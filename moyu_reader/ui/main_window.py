"""主窗口：无边框圆角 + 自定义标题栏 + 阅读区 + 状态栏 + 边缘缩放 + 隐形模式/老板键。"""
from PySide6.QtCore import QEvent, QRect, Qt, QTimer, QPoint
from PySide6.QtGui import QAction, QColor, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication, QFileDialog, QFrame, QGraphicsDropShadowEffect, QHBoxLayout,
    QLabel, QMainWindow, QMenu, QMessageBox, QToolButton, QVBoxLayout, QWidget,
)

from .. import storage
from ..icon import make_icon
from ..parsers import parse_book
from ..skins import get as get_skin
from .bookshelf import BookshelfDialog
from .bookmarks_dialog import BookmarksDialog
from .goto_dialog import GotoDialog
from .reader_view import ReaderView
from .settings_dialog import SettingsDialog
from .toc_dialog import TocDialog

MARGIN = 16  # 窗口内边距，用于投影阴影
EDGE_BAND = MARGIN + 6  # 边缘缩放感应带：阴影区 + 可视边缘向内 6px
MIN_W, MIN_H = 220, 90  # 最小尺寸：允许缩到贴条大小

# 边缘标志位
EDGE_L, EDGE_R, EDGE_T, EDGE_B = 1, 2, 4, 8


class TitleBar(QWidget):
    """自定义标题栏：可拖动窗口。"""

    def __init__(self, title, icon_pixmap, parent=None):
        super().__init__(parent)
        self.setObjectName("titlebar")
        self.setFixedHeight(38)
        self._drag = None
        self._lay = QHBoxLayout(self)
        self._lay.setContentsMargins(12, 0, 8, 0)
        self._lay.setSpacing(4)
        self.icon = QLabel()
        self.icon.setPixmap(icon_pixmap)
        self._lay.addWidget(self.icon)
        self.title = QLabel(title)
        self.title.setObjectName("titleText")
        self._lay.addWidget(self.title)
        self._lay.addStretch(1)

    def layout(self):
        return self._lay

    def set_title(self, t):
        self.title.setText(t)

    def add_button(self, text, slot, tip="", danger=False):
        btn = QToolButton()
        btn.setText(text)
        btn.setToolTip(tip)
        btn.setProperty("danger", danger)
        btn.clicked.connect(slot)
        self._lay.addWidget(btn)
        return btn

    def add_menu_button(self, menu, tip=""):
        btn = QToolButton()
        btn.setText("☰")
        btn.setToolTip(tip)
        btn.setPopupMode(QToolButton.InstantPopup)
        btn.setMenu(menu)
        self._lay.addWidget(btn)
        return btn

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._drag = e.globalPosition().toPoint() - self.window().frameGeometry().topLeft()
            e.accept()

    def mouseMoveEvent(self, e):
        if self._drag is not None and e.buttons() & Qt.LeftButton:
            self.window().move(e.globalPosition().toPoint() - self._drag)
            e.accept()

    def mouseReleaseEvent(self, e):
        self._drag = None


class MainWindow(QMainWindow):
    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx
        self._invisible = False
        self._resize = None
        self._toc = None
        self._leave_timer = QTimer(self)
        self._leave_timer.setSingleShot(True)
        self._leave_timer.setInterval(400)
        self._leave_timer.timeout.connect(self._maybe_hide_on_leave)
        # 失焦延迟确认：打开模态弹窗的瞬间会先出现"焦点为空"的过渡信号，
        # 立即隐藏会连弹窗一起藏掉（设置页无法使用的 bug），故延迟后再判断
        self._blur_timer = QTimer(self)
        self._blur_timer.setSingleShot(True)
        self._blur_timer.setInterval(150)
        self._blur_timer.timeout.connect(self._maybe_hide_on_blur)
        self.setWindowTitle(ctx.settings["window_title"])
        self.setWindowIcon(make_icon())  # 任务栏图标
        self.setMinimumSize(MIN_W, MIN_H)
        self.resize(720, 920)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowFlags(Qt.FramelessWindowHint)

        # 标题栏
        icon_pm = make_icon().pixmap(18, 18)
        self.titlebar = TitleBar(ctx.settings["window_title"], icon_pm)
        self.titlebar.add_menu_button(self._build_header_menu(), "菜单")
        self.titlebar.add_button("⚙", self.show_settings, "设置 (Ctrl+,)")
        self.titlebar.add_button("👁", self.toggle_invisible, "隐形模式 (F11)")
        self.titlebar.add_button("—", self.boss_hide, "隐藏到托盘")
        self.titlebar.add_button("✕", self.close, "关闭", danger=True)

        # 阅读区
        self.reader = ReaderView()
        self.reader.on_page_changed.connect(self.update_status)
        self.reader.on_chapter_changed.connect(self.update_status)
        self.reader.verticalScrollBar().valueChanged.connect(lambda _: self.update_status())
        self.reader.setContextMenuPolicy(Qt.CustomContextMenu)
        self.reader.customContextMenuRequested.connect(self._on_reader_menu)

        # 状态栏
        self.status = QLabel("就绪")
        self.status.setObjectName("statusText")
        self.status.setFixedHeight(22)

        # 无边框圆角容器（带投影）
        root = QWidget()
        root.setObjectName("root")
        outer = QVBoxLayout(root)
        outer.setContentsMargins(MARGIN, MARGIN, MARGIN, MARGIN)
        chrome = QFrame()
        chrome.setObjectName("chrome")
        shadow = QGraphicsDropShadowEffect(chrome)
        shadow.setBlurRadius(28)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 130))
        chrome.setGraphicsEffect(shadow)
        inner = QVBoxLayout(chrome)
        inner.setContentsMargins(0, 0, 0, 0)
        inner.setSpacing(0)
        inner.addWidget(self.titlebar)
        inner.addWidget(self.reader, 1)
        inner.addWidget(self.status)
        outer.addWidget(chrome)
        self.setCentralWidget(root)

        # 边缘缩放：需要主窗口及标题栏/状态栏的悬停事件（用于光标反馈），
        # 事件过滤器安装到应用级，保证按在阅读区/标题栏边缘也能进入缩放
        self.setMouseTracking(True)
        self.titlebar.setMouseTracking(True)
        self.status.setMouseTracking(True)
        root.setMouseTracking(True)
        chrome.setMouseTracking(True)
        QApplication.instance().installEventFilter(self)

        self._install_shortcuts()

        self._save_timer = QTimer(self)
        self._save_timer.setInterval(3000)
        self._save_timer.timeout.connect(self.ctx.save_progress)
        self._save_timer.start()

        self._apply_window_state()
        self.apply_skin()

    # ---------- 皮肤与标题 ----------
    def apply_skin(self):
        s = self.ctx.settings
        self.reader.apply_skin(get_skin(s["skin"]), s["font_size"], s["line_height"])

    def update_title(self):
        t = self.ctx.settings["window_title"]
        self.setWindowTitle(t)
        self.titlebar.set_title(t)

    def update_header(self):
        book = self.ctx.book
        ch = self.reader.current_chapter()
        if book and ch:
            self.titlebar.set_title(f"{book.title} · {ch.title}")
            if self.ctx.tray and self.ctx.tray.icon:
                self.ctx.tray.icon.setToolTip(book.title)
        else:
            self.titlebar.set_title(self.ctx.settings["window_title"])

    def update_status(self):
        book = self.ctx.book
        if not book or not self.reader.chapter_count:
            self.status.setText("就绪（Ctrl+O 打开小说）")
            return
        self.status.setText(
            f"第 {self.reader.chapter_index + 1}/{self.reader.chapter_count} 章 · "
            f"第 {self.reader.page() + 1}/{self.reader.total_pages()} 页 · "
            f"{int(self.reader.fraction() * 100)}%"
        )

    # ---------- 隐形模式 / 窗口状态 ----------
    def _window_flags(self):
        flags = Qt.Window | Qt.FramelessWindowHint
        if self._invisible or self.ctx.settings.get("always_on_top"):
            flags |= Qt.WindowStaysOnTopHint
        return flags

    def _apply_window_state(self):
        s = self.ctx.settings
        self.titlebar.setVisible(not self._invisible)
        self._update_status_visibility()
        self.reader.set_drag_enabled(self._invisible)
        # 透明度对所有模式生效（拖动设置滑块可实时看到效果）
        opacity = max(1, min(100, int(s.get("opacity", 100))))
        self.setWindowOpacity(opacity / 100.0)
        self.setWindowFlags(self._window_flags())
        self.setAttribute(Qt.WA_TranslucentBackground, True)

    def _update_status_visibility(self):
        self.status.setVisible((not self._invisible) and self.height() >= 240)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if not self._invisible:
            self._update_status_visibility()

    def _reapply_window(self):
        self._apply_window_state()
        self.show()

    def toggle_invisible(self):
        self._invisible = not self._invisible
        self._reapply_window()

    # ---------- 尺寸预设 ----------
    def _save_mode_geometry(self):
        """把当前窗口位置与大小记进当前模式的档案（用户手动改过的尺寸会被记住）。"""
        mode = getattr(self, "_current_mode", None)
        if not mode:
            return
        g = self.geometry()
        self.ctx.settings.setdefault("preset_geometry", {})[mode] = [g.x(), g.y(), g.width(), g.height()]
        from .. import config
        config.save_settings(self.ctx.settings)

    def _restore_mode_geometry(self, kind, default_w, default_h, place=None):
        """恢复某模式记忆的窗口几何；无记忆或不在屏幕内则用默认值。"""
        pg = self.ctx.settings.get("preset_geometry", {}).get(kind)
        screen = QApplication.primaryScreen().availableGeometry()
        if pg and len(pg) == 4:
            rect = QRect(*[int(v) for v in pg])
            if (rect.width() >= self.minimumWidth() and rect.height() >= self.minimumHeight()
                    and screen.intersects(rect)):
                self.setGeometry(rect)
                return
        self.resize(default_w, default_h)
        if place == "bottom-right":
            self.move(screen.right() - self.width() - MARGIN - 24,
                      screen.bottom() - self.height() - MARGIN - 24)
        elif place == "center":
            self.move(max(screen.left() + 40, screen.center().x() - default_w // 2),
                      max(screen.top() + 40, screen.center().y() - default_h // 2))

    def apply_preset(self, kind):
        """预设窗口尺寸：small=小窗 / strip=贴条（隐形）/ normal=恢复。

        切换前把当前窗口几何存入当前模式的档案；每个模式各自记忆
        用户手动调整过的大小与位置。
        """
        self._save_mode_geometry()
        self._current_mode = kind
        if kind == "small":
            self._invisible = False
            self._reapply_window()
            self._restore_mode_geometry("small", 360, 280)
        elif kind == "strip":
            self._invisible = True
            self._reapply_window()
            self._restore_mode_geometry("strip", 520, 120, place="bottom-right")
        else:  # normal
            self._invisible = False
            self._reapply_window()
            self._restore_mode_geometry("normal", 720, 920, place="center")
        self.update_status()

    # ---------- 老板键 / 显示隐藏 ----------
    def boss_hide(self):
        self.ctx.save_progress()
        self.reader.stop_auto()
        if self._toc is not None:
            self._toc.hide()
        self.hide()

    def toggle_visible(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.raise_()
            self.activateWindow()

    def closeEvent(self, e):
        self._save_mode_geometry()
        self.ctx.save_progress()
        self.ctx.save_window_state()
        self.reader.stop_auto()
        if self.ctx.tray_enabled:
            self.hide()
            e.ignore()
        else:
            e.accept()

    # ---------- 打开与弹窗 ----------
    def open_book(self, path, resume=False):
        if not path:
            return
        try:
            book = parse_book(path)
        except Exception as e:
            QMessageBox.warning(self, "打开失败", str(e))
            return
        self.ctx.book = book
        entry = storage.find(path) if resume else None
        chapter = entry.get("chapter", 0) if entry else 0
        offset = entry.get("offset", 0.0) if entry else 0.0
        self.reader.set_auto_speed(self.ctx.settings["auto_scroll_speed"])
        self.reader.apply_skin(get_skin(self.ctx.settings["skin"]),
                              self.ctx.settings["font_size"],
                              self.ctx.settings["line_height"])
        self.reader.load_chapter(book.chapters, chapter, offset)
        self.update_header()
        self.update_status()
        self.show()
        self.raise_()
        self.activateWindow()
        self.ctx.save_progress()

    def open_file_dialog(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "打开小说", "",
            "小说文件 (*.txt *.text *.epub *.pdf *.mobi *.azw3 *.azw);;所有文件 (*)"
        )
        if path:
            self.open_book(path)

    def show_bookshelf(self):
        BookshelfDialog(self.ctx, self).exec()

    def show_toc(self):
        if not self.reader.chapter_count:
            self.status.setText("先打开一本书（Ctrl+O）")
            return
        if self._toc is None:
            self._toc = TocDialog(self)
        else:
            self._toc.refresh()
        self._toc.show()
        self._toc.raise_()

    def jump_to_chapter(self, idx):
        chapters = self.reader.chapters
        if not chapters:
            return
        self.reader.load_chapter(chapters, idx)
        self.update_header()
        self.update_status()
        self.ctx.save_progress()

    def jump_page(self, page_idx):
        self.reader.jump_to_page(page_idx)
        self.update_status()
        self.ctx.save_progress()

    def jump_bookmark(self, mark):
        chapters = self.reader.chapters
        if not chapters:
            return
        self.reader.load_chapter(chapters, mark.get("chapter", 0), mark.get("offset", 0.0))
        self.update_header()
        self.update_status()
        self.ctx.save_progress()

    def show_goto(self):
        if not self.reader.chapter_count:
            self.status.setText("先打开一本书（Ctrl+O）")
            return
        GotoDialog(self).exec()

    def add_bookmark(self):
        book = self.ctx.book
        if not book or not self.reader.chapter_count:
            self.status.setText("先打开一本书（Ctrl+O）")
            return
        ch = self.reader.current_chapter()
        label = f"{ch.title[:16]} · {int(self.reader.fraction() * 100)}%"
        if storage.add_bookmark(book.path, self.reader.chapter_index, self.reader.fraction(), label):
            self.status.setText(f"已添加书签：{label}")
        else:
            self.status.setText("添加书签失败（书不在书架？）")

    def show_bookmarks(self):
        if not self.reader.chapter_count:
            self.status.setText("先打开一本书（Ctrl+O）")
            return
        BookmarksDialog(self).exec()

    # ---------- 自动隐藏（失焦 / 鼠标移出） ----------
    def _dialogs_open(self):
        """只要还有别的自家可见窗口（菜单/弹窗/提示框），就不自动隐藏。

        菜单弹出同样伴随瞬时失焦，必须豁免，否则菜单根本点不到；
        用户带着菜单切走时菜单会自动关闭，关闭引发的失焦会再次走延迟判断。
        """
        for tl in QApplication.topLevelWidgets():
            if tl is self or not tl.isVisible():
                continue
            if tl.windowType() == Qt.ToolTip:
                continue
            return True
        return False

    def on_focus_changed(self, old, new):
        if not self.ctx.settings.get("hide_on_blur"):
            return
        if new is None:
            self._blur_timer.start()   # 延迟确认，避免误伤正在打开的弹窗
        else:
            self._blur_timer.stop()    # 焦点回到了应用内的某个窗口，取消隐藏

    def _maybe_hide_on_blur(self):
        if not self.ctx.settings.get("hide_on_blur") or not self.isVisible():
            return
        if self._dialogs_open():
            return
        if QApplication.activeWindow() is not None:
            return  # 焦点仍在自己应用的窗口里（设置/书架/目录等），不隐藏
        self.boss_hide()

    def _maybe_hide_on_leave(self):
        if (self.ctx.settings.get("hide_on_leave") and self.isVisible()
                and not self._dialogs_open()):
            self.boss_hide()

    def event(self, e):
        if e.type() == QEvent.Leave:
            self._leave_timer.start()
        elif e.type() == QEvent.Enter:
            self._leave_timer.stop()
        return super().event(e)

    def show_settings(self):
        SettingsDialog(self.ctx, self).exec()

    # ---------- 自动滚动 ----------
    def toggle_auto_scroll(self):
        self.reader.toggle_auto()
        self.update_status()

    # ---------- 快捷键 ----------
    def _install_shortcuts(self):
        binds = [
            ("Ctrl+O", self.open_file_dialog),
            ("Ctrl+B", self.show_bookshelf),
            ("Ctrl+D", self.show_toc),
            ("Ctrl+,", self.show_settings),
            ("Ctrl+T", self.toggle_auto_scroll),
            ("Ctrl+E", self.add_bookmark),
            ("Ctrl+Shift+E", self.show_bookmarks),
            ("Ctrl+G", self.show_goto),
            ("Ctrl+1", lambda: self.apply_preset("small")),
            ("Ctrl+2", lambda: self.apply_preset("strip")),
            ("Ctrl+0", lambda: self.apply_preset("normal")),
            ("F11", self.toggle_invisible),
            ("F12", self.boss_hide),
            ("Shift+Space", self.reader.prev_page),
        ]
        for seq, slot in binds:
            QShortcut(QKeySequence(seq), self, slot)
        QShortcut(QKeySequence(Qt.Key_Escape), self, self.boss_hide)

    # ---------- 菜单 ----------
    def _build_header_menu(self):
        m = QMenu(self)
        m.addAction("打开文件…", self.open_file_dialog)
        m.addAction("书架", self.show_bookshelf)
        m.addAction("目录", self.show_toc)
        m.addAction("书签", self.show_bookmarks)
        m.addAction("跳转到页…", self.show_goto)
        m.addAction("设置", self.show_settings)
        m.addSeparator()
        m.addAction("小窗模式（Ctrl+1）", lambda: self.apply_preset("small"))
        m.addAction("贴条模式（Ctrl+2）", lambda: self.apply_preset("strip"))
        m.addAction("恢复正常窗口（Ctrl+0）", lambda: self.apply_preset("normal"))
        m.addSeparator()
        m.addAction("自动滚动（Ctrl+T）", self.toggle_auto_scroll)
        m.addAction("隐形模式（F11）", self.toggle_invisible)
        m.addAction("隐藏（老板键）", self.boss_hide)
        m.addSeparator()
        m.addAction("退出", self.ctx.quit_app)
        return m

    def _on_reader_menu(self, pos):
        m = QMenu(self)
        m.addAction("添加书签（Ctrl+E）", self.add_bookmark)
        m.addAction("书签列表（Ctrl+Shift+E）", self.show_bookmarks)
        m.addAction("跳转到页（Ctrl+G）", self.show_goto)
        m.addSeparator()
        m.addAction("目录（Ctrl+D）", self.show_toc)
        m.addAction("上一章", self.reader.prev_chapter)
        m.addAction("下一章", self.reader.next_chapter)
        m.addAction("自动滚动（Ctrl+T）", self.toggle_auto_scroll)
        m.addSeparator()
        m.addAction("小窗模式（Ctrl+1）", lambda: self.apply_preset("small"))
        m.addAction("贴条模式（Ctrl+2）", lambda: self.apply_preset("strip"))
        m.addAction("恢复正常窗口（Ctrl+0）", lambda: self.apply_preset("normal"))
        m.addAction("隐形模式（F11）", self.toggle_invisible)
        m.addAction("打开文件…", self.open_file_dialog)
        m.addAction("书架", self.show_bookshelf)
        m.addAction("设置", self.show_settings)
        m.addSeparator()
        m.addAction("隐藏", self.boss_hide)
        m.addAction("退出", self.ctx.quit_app)
        m.exec(self.reader.mapToGlobal(pos))

    # ---------- 无边框窗口：边缘缩放（应用级事件过滤，优先于子控件） ----------
    def _edge_at(self, pos):
        r = self.rect()
        flags = 0
        if pos.x() <= EDGE_BAND:
            flags |= EDGE_L
        if pos.x() >= r.width() - EDGE_BAND:
            flags |= EDGE_R
        if pos.y() <= EDGE_BAND:
            flags |= EDGE_T
        if pos.y() >= r.height() - EDGE_BAND:
            flags |= EDGE_B
        return flags

    def _cursor_for(self, flags):
        cursors = {
            EDGE_L: Qt.SizeHorCursor, EDGE_R: Qt.SizeHorCursor,
            EDGE_T: Qt.SizeVerCursor, EDGE_B: Qt.SizeVerCursor,
            EDGE_L | EDGE_T: Qt.SizeFDiagCursor, EDGE_R | EDGE_B: Qt.SizeFDiagCursor,
            EDGE_R | EDGE_T: Qt.SizeBDiagCursor, EDGE_L | EDGE_B: Qt.SizeBDiagCursor,
        }
        return cursors.get(flags)

    @staticmethod
    def _resize_geometry(flags, g0, g1, start_geo, min_w, min_h):
        dx, dy = g1.x() - g0.x(), g1.y() - g0.y()
        x, y, w, h = start_geo.x(), start_geo.y(), start_geo.width(), start_geo.height()
        right, bottom = x + w, y + h
        if flags & EDGE_L:
            x = min(x + dx, right - min_w)
            w = right - x
        if flags & EDGE_R:
            w = max(min_w, w + dx)
        if flags & EDGE_T:
            y = min(y + dy, bottom - min_h)
            h = bottom - y
        if flags & EDGE_B:
            h = max(min_h, h + dy)
        return QRect(x, y, w, h)

    def eventFilter(self, obj, e):
        et = e.type()
        if et in (QEvent.MouseButtonPress, QEvent.MouseMove, QEvent.MouseButtonRelease):
            if (self.isVisible() and isinstance(obj, QWidget)
                    and (obj is self or self.isAncestorOf(obj))):
                gpos = e.globalPosition().toPoint()
                local = self.mapFromGlobal(gpos)
                flags = self._edge_at(local)
                if et == QEvent.MouseButtonPress:
                    if e.button() == Qt.LeftButton and flags and self._resize is None:
                        self._resize = (flags, gpos, self.geometry())
                        self.setCursor(self._cursor_for(flags) or Qt.ArrowCursor)
                        self.grabMouse()  # 后续移动/释放都发给主窗口
                        return True
                elif et == QEvent.MouseMove:
                    if self._resize is not None:
                        flags, g0, start = self._resize
                        self.setGeometry(self._resize_geometry(
                            flags, g0, gpos, start,
                            self.minimumWidth(), self.minimumHeight()))
                        return True
                    self.setCursor(self._cursor_for(flags) or Qt.ArrowCursor)
                elif et == QEvent.MouseButtonRelease:
                    if self._resize is not None:
                        self._resize = None
                        self.releaseMouse()
                        self.unsetCursor()
                        return True
        return super().eventFilter(obj, e)

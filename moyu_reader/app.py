"""应用装配：AppContext（共享状态）+ 启动入口。"""
import sys

from PySide6.QtCore import QRect
from PySide6.QtWidgets import QApplication, QFileDialog

from . import config, storage, theme
from .hotkeys import GlobalHotkey
from .icon import make_icon
from .ui.main_window import MainWindow
from .tray import Tray


class AppContext:
    """跨模块共享的应用状态与操作。"""

    def __init__(self):
        self.settings = config.load_settings()
        self.shelf = storage.load_bookshelf()
        self.book = None
        self.win = None
        self.tray = None
        self.hotkey = None

    @property
    def tray_enabled(self):
        return bool(self.tray and self.tray.enabled)

    def open_book(self, path, resume=False):
        self.win.open_book(path, resume)

    def open_file_dialog(self, parent=None):
        path, _ = QFileDialog.getOpenFileName(
            parent, "打开小说", "",
            "小说文件 (*.txt *.text *.epub *.pdf *.mobi *.azw3 *.azw);;所有文件 (*)"
        )
        if path:
            self.open_book(path)

    def save_progress(self):
        if self.book and self.book.chapters and self.win:
            total = max(1, len(self.book.chapters))
            percent = round((self.win.reader.chapter_index + self.win.reader.fraction()) / total * 100, 1)
            percent = min(100.0, percent)
            storage.touch(
                self.book.path, self.book.title, self.book.fmt,
                self.win.reader.chapter_index, self.win.reader.fraction(),
                self.book.author, percent,
            )
            self.shelf = storage.load_bookshelf()

    def apply_settings(self):
        config.save_settings(self.settings)
        self.win.apply_skin()
        self.win.update_title()
        self.win._reapply_window()
        self.win.reader.set_auto_speed(self.settings["auto_scroll_speed"])
        if self.hotkey:
            self.hotkey.unregister()
            self.hotkey.register(self.settings["boss_key"])

    def save_window_state(self):
        """把当前窗口位置与大小写入设置。"""
        if self.win:
            g = self.win.geometry()
            self.settings["geometry"] = [g.x(), g.y(), g.width(), g.height()]
            config.save_settings(self.settings)

    def quit_app(self):
        self.save_progress()
        self.save_window_state()
        if self.hotkey:
            self.hotkey.unregister()
        QApplication.instance().quit()


def run():
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    app = QApplication(sys.argv)
    app.setApplicationName(config.APP_NAME)
    app.setWindowIcon(make_icon())  # 全局默认窗口图标（任务栏/对话框）
    app.setQuitOnLastWindowClosed(False)
    app.setStyleSheet(theme.APP_QSS)

    ctx = AppContext()
    win = MainWindow(ctx)
    ctx.win = win
    ctx.tray = Tray(ctx, win)
    app.focusChanged.connect(win.on_focus_changed)  # 失焦自动隐藏

    # 恢复上次关闭时的窗口位置与大小（仍在屏幕内才恢复）
    geo = ctx.settings.get("geometry")
    if geo and len(geo) == 4:
        rect = QRect(*[int(v) for v in geo])
        screen = QApplication.primaryScreen().availableGeometry()
        if rect.width() >= 220 and rect.height() >= 90 and screen.intersects(rect):
            win.setGeometry(rect)

    ctx.hotkey = GlobalHotkey(win.boss_hide)
    app.installNativeEventFilter(ctx.hotkey)
    if not ctx.hotkey.register(ctx.settings["boss_key"]):
        # 热键被占用或格式无效：静默降级，应用内 Esc/F12 仍可隐藏
        pass

    if ctx.shelf:
        win.open_book(ctx.shelf[0]["path"], resume=True)

    win.show()
    return app.exec()

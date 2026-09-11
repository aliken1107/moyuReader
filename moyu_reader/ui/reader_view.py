"""阅读区：正文渲染 + 翻页 + 自动滚动 + 隐形模式下的拖动移动窗口。"""
from PySide6.QtCore import Qt, QTimer, Signal, QPoint
from PySide6.QtGui import QColor, QFont, QTextBlockFormat, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import QTextEdit

_AUTO_INTERVALS = {0: 0, 1: 300, 2: 150, 3: 60}
_AUTO_STEP = 6  # 每次滚动像素


class ReaderView(QTextEdit):
    on_page_changed = Signal()
    on_chapter_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setLineWrapMode(QTextEdit.WidgetWidth)
        self.setFrameStyle(0)
        self.document().setDocumentMargin(18)
        self.setContextMenuPolicy(Qt.NoContextMenu)  # 由主窗口接管右键菜单

        self._chapters = []
        self._chapter = 0
        self._skin = None
        self._font_size = 16
        self._line_height = 1.6
        self._auto_speed = 1
        self._drag_enabled = False

        self._auto = QTimer(self)
        self._auto.timeout.connect(self._auto_scroll)

        # 隐形模式拖动窗口
        self._drag_pos = None

    # ---------- 数据 ----------
    @property
    def chapters(self):
        return self._chapters

    @property
    def chapter_index(self):
        return self._chapter

    @property
    def chapter_count(self):
        return len(self._chapters)

    def current_chapter(self):
        return self._chapters[self._chapter] if self._chapters else None

    def load_chapter(self, chapters, index, fraction=0.0):
        if not chapters:
            self.clear()
            return
        self._chapters = chapters
        self._chapter = max(0, min(index, len(chapters) - 1))
        self.setPlainText(chapters[self._chapter].text)
        self._apply_style()
        if fraction > 0:
            QTimer.singleShot(0, lambda: self._set_fraction(fraction))
        else:
            self.verticalScrollBar().setValue(0)

    def _set_fraction(self, f):
        sb = self.verticalScrollBar()
        sb.setValue(int(sb.maximum() * max(0.0, min(1.0, f))))

    def fraction(self):
        sb = self.verticalScrollBar()
        if sb.maximum() <= 0:
            return 0.0
        return sb.value() / sb.maximum()

    # ---------- 样式 ----------
    def apply_skin(self, skin, font_size, line_height):
        self._skin = skin
        self._font_size = font_size
        self._line_height = line_height
        self._apply_style()

    def _apply_style(self):
        skin = self._skin
        self.setStyleSheet(
            f"QTextEdit {{ background-color: {skin['bg']}; color: {skin['fg']}; border: none; }}"
        )
        font = QFont(skin["font_family"], self._font_size)
        if skin.get("mono"):
            font.setStyleHint(QFont.Monospace)
        self.setFont(font)

        cursor = self.textCursor()
        cursor.select(QTextCursor.Document)
        block = QTextBlockFormat()
        block.setLineHeight(self._line_height * 100, 1)  # 1 = ProportionalHeight
        block.setTopMargin(0)
        block.setBottomMargin(0)
        cursor.mergeBlockFormat(block)
        char = QTextCharFormat()
        char.setForeground(QColor(skin["fg"]))
        char.setFont(font)
        cursor.mergeCharFormat(char)
        cursor.clearSelection()  # 样式套用完毕，取消全选状态，避免翻页时整页文字被选中
        self.setTextCursor(cursor)

    # ---------- 翻页 ----------
    def _vh(self):
        return max(1, self.viewport().height())

    def total_pages(self):
        doc_h = self.document().size().height()
        return max(1, int(round(doc_h / self._vh())))

    def page(self):
        sb = self.verticalScrollBar()
        return min(sb.value() // self._vh(), self.total_pages() - 1)

    def next_page(self):
        sb = self.verticalScrollBar()
        vh = self._vh()
        if sb.value() + vh < sb.maximum():
            sb.setValue(sb.value() + vh)
            self.on_page_changed.emit()
            return
        if self._chapter < len(self._chapters) - 1:
            self.load_chapter(self._chapters, self._chapter + 1)
            self.on_chapter_changed.emit()
            self.on_page_changed.emit()

    def prev_page(self):
        sb = self.verticalScrollBar()
        vh = self._vh()
        if sb.value() > 0:
            sb.setValue(max(0, sb.value() - vh))
            self.on_page_changed.emit()
            return
        if self._chapter > 0:
            self.load_chapter(self._chapters, self._chapter - 1, fraction=1.0)
            self.on_chapter_changed.emit()
            self.on_page_changed.emit()

    def next_chapter(self):
        if self._chapter < len(self._chapters) - 1:
            self.load_chapter(self._chapters, self._chapter + 1)
            self.on_chapter_changed.emit()
            self.on_page_changed.emit()

    def prev_chapter(self):
        if self._chapter > 0:
            self.load_chapter(self._chapters, self._chapter - 1)
            self.on_chapter_changed.emit()
            self.on_page_changed.emit()

    # ---------- 自动滚动 ----------
    def set_auto_speed(self, speed):
        self._auto_speed = speed if speed in _AUTO_INTERVALS else 1

    def toggle_auto(self):
        if self._auto.isActive():
            self._auto.stop()
            return False
        self._auto.setInterval(_AUTO_INTERVALS.get(self._auto_speed, 300))
        self._auto.start()
        return True

    def stop_auto(self):
        self._auto.stop()

    def is_auto(self):
        return self._auto.isActive()

    def _auto_scroll(self):
        sb = self.verticalScrollBar()
        if sb.value() + _AUTO_STEP < sb.maximum():
            sb.setValue(sb.value() + _AUTO_STEP)
            self.on_page_changed.emit()
        else:
            self.next_page()

    # ---------- 鼠标：隐形模式拖动 / 点击翻页 ----------
    def set_drag_enabled(self, enabled):
        self._drag_enabled = enabled

    def mousePressEvent(self, e):
        if self._drag_enabled and e.button() == Qt.LeftButton:
            self._drag_pos = e.globalPosition().toPoint() - self.window().frameGeometry().topLeft()
            e.accept()
            return
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if self._drag_pos is not None and e.buttons() & Qt.LeftButton:
            self.window().move(e.globalPosition().toPoint() - self._drag_pos)
            e.accept()
            return
        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        was_drag = self._drag_pos is not None
        self._drag_pos = None
        if was_drag:
            e.accept()
            return
        if e.button() == Qt.LeftButton:
            w = self.width()
            if e.position().x() > w * 0.85:
                self.next_page()
            elif e.position().x() < w * 0.15:
                self.prev_page()
            e.accept()
            return
        super().mouseReleaseEvent(e)

    def keyPressEvent(self, e):
        key = e.key()
        if key == Qt.Key_Right or key == Qt.Key_PageDown:
            self.next_page()
        elif key == Qt.Key_Left or key == Qt.Key_PageUp:
            self.prev_page()
        elif key == Qt.Key_Space:
            if e.modifiers() & Qt.ShiftModifier:
                self.prev_page()
            else:
                self.next_page()
        else:
            super().keyPressEvent(e)

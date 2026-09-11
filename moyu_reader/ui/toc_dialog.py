"""章节目录面板：列出全部章节，点击跳转。非模态，可边看边跳。"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QVBoxLayout,
)


class TocDialog(QDialog):
    def __init__(self, win, parent=None):
        super().__init__(parent or win)
        self.win = win
        self.setWindowTitle("目录")
        self.resize(340, 520)
        self.list = QListWidget()
        self.list.itemClicked.connect(self._jump)
        self.list.itemDoubleClicked.connect(self._jump_and_close)

        hint = QLabel("单击跳转，双击跳转并关闭")
        hint.setProperty("dim", True)
        hint.setStyleSheet("font-size: 12px;")
        btn_close = QPushButton("关闭")
        btn_close.clicked.connect(self.close)
        row = QHBoxLayout()
        row.addWidget(hint)
        row.addStretch(1)
        row.addWidget(btn_close)

        lay = QVBoxLayout(self)
        lay.addWidget(self.list)
        lay.addLayout(row)
        self.refresh()

    def refresh(self):
        reader = self.win.reader
        self.list.clear()
        for i, ch in enumerate(reader.chapters):
            item = QListWidgetItem(f"{i + 1}. {ch.title}")
            item.setData(Qt.UserRole, i)
            self.list.addItem(item)
        self.list.setCurrentRow(reader.chapter_index)
        cur = self.list.currentItem()
        if cur is not None:
            self.list.scrollToItem(cur)

    def _jump(self, item):
        idx = item.data(Qt.UserRole)
        if idx is None:
            return
        self.win.jump_to_chapter(int(idx))
        self.list.setCurrentRow(int(idx))

    def _jump_and_close(self, item):
        self._jump(item)
        self.close()

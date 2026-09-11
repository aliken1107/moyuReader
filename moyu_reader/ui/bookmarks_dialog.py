"""书签列表：单击跳转、双击跳转并关闭、删除/清空。"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QVBoxLayout,
)

from .. import storage


class BookmarksDialog(QDialog):
    def __init__(self, win, parent=None):
        super().__init__(parent or win)
        self.win = win
        self.setWindowTitle("书签")
        self.resize(360, 420)
        self.list = QListWidget()
        self.list.itemClicked.connect(self._jump)
        self.list.itemDoubleClicked.connect(self._jump_and_close)

        hint = QLabel("单击跳转，双击跳转并关闭")
        hint.setProperty("dim", True)
        hint.setStyleSheet("font-size: 12px;")
        btn_del = QPushButton("删除")
        btn_clear = QPushButton("清空")
        btn_close = QPushButton("关闭")
        btn_del.clicked.connect(self._delete)
        btn_clear.clicked.connect(self._clear)
        btn_close.clicked.connect(self.close)
        row = QHBoxLayout()
        row.addWidget(hint)
        row.addStretch(1)
        row.addWidget(btn_del)
        row.addWidget(btn_clear)
        row.addWidget(btn_close)

        lay = QVBoxLayout(self)
        lay.addWidget(self.list)
        lay.addLayout(row)
        self.refresh()

    def _marks(self):
        if not self.win.ctx.book:
            return []
        entry = storage.find(self.win.ctx.book.path)
        return entry.get("bookmarks", []) if entry else []

    def refresh(self):
        self.list.clear()
        marks = self._marks()
        for i, m in enumerate(marks):
            item = QListWidgetItem(m.get("label", f"书签 {i + 1}"))
            item.setData(Qt.UserRole, i)
            self.list.addItem(item)
        if not marks:
            self.list.addItem("（还没有书签：右键阅读区 → 添加书签）")

    def _jump(self, item):
        idx = item.data(Qt.UserRole)
        marks = self._marks()
        if idx is None or not marks:
            return
        self.win.jump_bookmark(marks[int(idx)])

    def _jump_and_close(self, item):
        self._jump(item)
        self.close()

    def _delete(self):
        item = self.list.currentItem()
        if item is None or item.data(Qt.UserRole) is None:
            return
        if self.win.ctx.book:
            storage.remove_bookmark(self.win.ctx.book.path, int(item.data(Qt.UserRole)))
        self.refresh()

    def _clear(self):
        if not self.win.ctx.book:
            return
        books = storage.load_bookshelf()
        for b in books:
            if b.get("path") == self.win.ctx.book.path:
                b["bookmarks"] = []
        storage.save_bookshelf(books)
        self.refresh()

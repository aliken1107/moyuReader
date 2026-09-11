"""书架弹窗：最近阅读列表，续读 / 移除 / 打开文件。"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QVBoxLayout, QMessageBox,
)

from .. import storage


class BookshelfDialog(QDialog):
    def __init__(self, ctx, parent=None):
        super().__init__(parent)
        self.ctx = ctx
        self.setWindowTitle("书架")
        self.resize(460, 360)

        self.list = QListWidget()
        self.list.itemDoubleClicked.connect(lambda _: self.resume())

        row = QHBoxLayout()
        btn_open = QPushButton("打开文件")
        btn_resume = QPushButton("继续阅读")
        btn_remove = QPushButton("移除")
        btn_close = QPushButton("关闭")
        btn_open.clicked.connect(self.open_file)
        btn_resume.clicked.connect(self.resume)
        btn_remove.clicked.connect(self.remove_selected)
        btn_close.clicked.connect(self.accept)
        for b in (btn_open, btn_resume, btn_remove):
            row.addWidget(b)
        row.addStretch(1)
        row.addWidget(btn_close)

        hint = QLabel("双击条目可续读。进度自动保存。")
        hint.setProperty("dim", True)
        hint.setStyleSheet("font-size: 12px;")

        layout = QVBoxLayout(self)
        layout.addWidget(self.list)
        layout.addLayout(row)
        layout.addWidget(hint)

        self.refresh()

    def refresh(self):
        self.list.clear()
        for b in self.ctx.shelf:
            parts = [b.get("title", "未命名")]
            if b.get("author"):
                parts.append(b["author"])
            if b.get("fmt"):
                parts.append(b["fmt"].upper())
            percent = b.get("percent")
            if percent is not None:
                parts.append(f"{percent}%")
            item = QListWidgetItem("  ·  ".join(parts))
            item.setData(Qt.UserRole, b.get("path"))
            item.setToolTip(b.get("path", ""))
            self.list.addItem(item)
        if not self.ctx.shelf:
            self.list.addItem("（书架为空，Ctrl+O 或点“打开文件”导入小说）")

    def _selected_path(self):
        item = self.list.currentItem()
        if item is None:
            return None
        return item.data(Qt.UserRole)

    def resume(self):
        path = self._selected_path()
        if path:
            self.ctx.open_book(path, resume=True)
            self.accept()

    def open_file(self):
        self.ctx.open_file_dialog(parent=self)
        self.refresh()

    def remove_selected(self):
        path = self._selected_path()
        if not path:
            return
        storage.remove(path)
        self.ctx.shelf = storage.load_bookshelf()
        self.refresh()

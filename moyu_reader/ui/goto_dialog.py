"""页码跳转：输入页号跳到当前章的对应页。"""
from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QPushButton, QSpinBox, QVBoxLayout,
)


class GotoDialog(QDialog):
    def __init__(self, win, parent=None):
        super().__init__(parent or win)
        self.win = win
        self.setWindowTitle("跳转到页")
        self.resize(300, 0)

        total = self.win.reader.total_pages()
        self.spin = QSpinBox()
        self.spin.setRange(1, max(1, total))
        self.spin.setValue(self.win.reader.page() + 1)
        self.lbl = QLabel(f"共 {total} 页")
        self.lbl.setProperty("dim", True)

        btn_ok = QPushButton("跳转")
        btn_cancel = QPushButton("取消")
        btn_ok.clicked.connect(self._jump)
        btn_cancel.clicked.connect(self.reject)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("页码"))
        row1.addWidget(self.spin)
        row1.addWidget(self.lbl)
        row1.addStretch(1)
        row2 = QHBoxLayout()
        row2.addStretch(1)
        row2.addWidget(btn_ok)
        row2.addWidget(btn_cancel)

        lay = QVBoxLayout(self)
        lay.addLayout(row1)
        lay.addLayout(row2)

    def _jump(self):
        self.win.jump_page(self.spin.value() - 1)
        self.accept()

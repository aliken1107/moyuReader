"""设置弹窗：皮肤 / 字号 / 行距 / 老板键 / 隐形模式参数。"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox,
    QFormLayout, QHBoxLayout, QLabel, QLineEdit, QSlider, QSpinBox, QVBoxLayout,
)

from ..skins import SKINS
from ..hotkeys import parse_hotkey

BOSS_KEY_PRESETS = ["Ctrl+Shift+Z", "Ctrl+Shift+X", "Ctrl+Alt+Z", "F12", "Ctrl+`"]


class SettingsDialog(QDialog):
    def __init__(self, ctx, parent=None):
        super().__init__(parent)
        self.ctx = ctx
        self.setWindowTitle("设置")
        self.resize(420, 0)

        s = ctx.settings

        self.cmb_skin = QComboBox()
        for key, skin in SKINS.items():
            self.cmb_skin.addItem(skin["name"], key)
        self.cmb_skin.setCurrentIndex(self.cmb_skin.findData(s["skin"]))

        self.spin_font = QSpinBox()
        self.spin_font.setRange(10, 40)
        self.spin_font.setValue(s["font_size"])

        self.spin_line = QDoubleSpinBox()
        self.spin_line.setRange(1.0, 2.5)
        self.spin_line.setSingleStep(0.05)
        self.spin_line.setValue(s["line_height"])

        self.edt_boss = QLineEdit(s["boss_key"])
        self.edt_boss.setPlaceholderText("如 Ctrl+Shift+Z")
        hint_boss = QLabel("全局老板键：在任何程序里按下即隐藏阅读窗口。")
        hint_boss.setProperty("dim", True)
        hint_boss.setStyleSheet("font-size: 12px;")

        self.chk_top = QCheckBox("窗口置顶")
        self.chk_top.setChecked(s["always_on_top"])

        self.sld_opacity = QSlider(Qt.Orientation.Horizontal)
        self.sld_opacity.setRange(1, 100)
        self.sld_opacity.setValue(s["opacity"])
        self.lbl_opacity = QLabel(f"{s['opacity']}%")
        self.sld_opacity.valueChanged.connect(self._on_opacity_changed)

        self.cmb_speed = QComboBox()
        for name, val in (("关闭", 0), ("慢", 1), ("中", 2), ("快", 3)):
            self.cmb_speed.addItem(name, val)
        self.cmb_speed.setCurrentIndex(self.cmb_speed.findData(s["auto_scroll_speed"]))

        self.edt_title = QLineEdit(s["window_title"])

        form = QFormLayout()
        form.addRow("皮肤", self.cmb_skin)
        form.addRow("字号", self.spin_font)
        form.addRow("行距", self.spin_line)
        form.addRow("老板键", self.edt_boss)
        form.addRow("", hint_boss)
        form.addRow("置顶", self.chk_top)
        form.addRow("窗口不透明度（实时生效）", self._opacity_row())
        form.addRow("自动滚动速度", self.cmb_speed)
        form.addRow("窗口/托盘名称", self.edt_title)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def _opacity_row(self):
        row = QHBoxLayout()
        row.addWidget(self.sld_opacity)
        row.addWidget(self.lbl_opacity)
        return row

    def _on_opacity_changed(self, v):
        self.lbl_opacity.setText(f"{v}%")
        # 拖动即实时预览窗口透明度，无需点确定
        if self.ctx.win:
            self.ctx.win.setWindowOpacity(max(1, v) / 100.0)

    def done(self, r):
        # 取消/Esc/关闭时恢复为设置里保存的透明度
        if r != QDialog.DialogCode.Accepted and self.ctx.win:
            self.ctx.win._apply_window_state()
        super().done(r)

    def _accept(self):
        if not parse_hotkey(self.edt_boss.text()):
            self.edt_boss.setStyleSheet("border: 1px solid #e55;")
            self.edt_boss.setToolTip("老板键格式无效，示例：Ctrl+Shift+Z")
            return
        self.ctx.settings.update({
            "skin": self.cmb_skin.currentData(),
            "font_size": self.spin_font.value(),
            "line_height": self.spin_line.value(),
            "boss_key": self.edt_boss.text().strip(),
            "always_on_top": self.chk_top.isChecked(),
            "opacity": self.sld_opacity.value(),
            "auto_scroll_speed": self.cmb_speed.currentData(),
            "window_title": self.edt_title.text().strip() or "MoyuReader",
        })
        self.ctx.apply_settings()
        self.accept()

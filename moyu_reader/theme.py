"""全局深色主题（QSS）。在 run() 里应用：app.setStyleSheet(theme.APP_QSS)。"""

APP_QSS = """
* { font-family: "Microsoft YaHei UI", "Microsoft YaHei", sans-serif; }
QWidget { color: #d7dbe0; font-size: 13px; }

QWidget#root { background: transparent; }
QFrame#chrome { background-color: #17191c; border-radius: 14px; }
QWidget#titlebar { background: transparent; }
QLabel#titleText { color: #b6bcc4; font-size: 12px; }
QLabel#statusText { color: #8b93a1; background: transparent; padding-left: 12px; font-size: 11px; }

QToolButton {
    background: transparent; border: none; border-radius: 6px;
    color: #a9b0b8; padding: 3px 7px; font-size: 13px;
}
QToolButton:hover { background: #2b2f34; color: #e6e9ed; }
QToolButton:pressed { background: #363b41; }
QToolButton[danger="true"]:hover { background: #d93025; color: #ffffff; }

QMenu { background-color: #202327; border: 1px solid #33373d; border-radius: 8px; padding: 4px; }
QMenu::item { padding: 5px 24px 5px 12px; border-radius: 5px; }
QMenu::item:selected { background-color: #2f6feb; color: #ffffff; }
QMenu::item:disabled { color: #5a6068; }
QMenu::separator { height: 1px; background: #33373d; margin: 5px 10px; }

QToolTip { background: #26292e; color: #e6e9ed; border: 1px solid #3a3f46; padding: 4px 8px; }

QDialog { background-color: #1b1e22; }
QDialog QLabel { color: #d7dbe0; }
QDialog QLabel[dim="true"] { color: #8b93a1; }

QPushButton {
    background: #262a30; border: 1px solid #33373d; border-radius: 6px; padding: 5px 14px;
}
QPushButton:hover { background: #2f6feb; border-color: #2f6feb; color: #ffffff; }
QPushButton:pressed { background: #2759c4; }

QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
    background: #141619; border: 1px solid #33373d; border-radius: 6px;
    padding: 3px 8px; selection-background-color: #2f6feb;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus { border-color: #2f6feb; }
QComboBox::drop-down { border: none; width: 20px; }
QComboBox QAbstractItemView {
    background: #202327; border: 1px solid #33373d; selection-background-color: #2f6feb;
}
QSpinBox::up-button, QDoubleSpinBox::up-button,
QSpinBox::down-button, QDoubleSpinBox::down-button {
    background: #262a30; border: none; width: 16px;
}
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover { background: #2f6feb; }

QSlider::groove:horizontal { height: 4px; background: #33373d; border-radius: 2px; }
QSlider::handle:horizontal { width: 14px; height: 14px; margin: -5px 0; border-radius: 7px; background: #2f6feb; }
QSlider::handle:horizontal:hover { background: #4c8dff; }

QListWidget { background: #141619; border: 1px solid #33373d; border-radius: 8px; padding: 4px; outline: none; }
QListWidget::item { padding: 6px 8px; border-radius: 5px; }
QListWidget::item:selected { background: #2f6feb; color: #ffffff; }
QListWidget::item:hover { background: #262a30; }

QCheckBox { spacing: 6px; }
QCheckBox::indicator {
    width: 15px; height: 15px; border: 1px solid #33373d; border-radius: 4px; background: #141619;
}
QCheckBox::indicator:checked { background: #2f6feb; border-color: #2f6feb; }

QMessageBox { background-color: #1b1e22; }

QScrollBar:vertical { background: transparent; width: 10px; margin: 2px; }
QScrollBar::handle:vertical { background: #3a3f46; border-radius: 5px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: #4a5058; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; width: 0; }
QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }
QScrollBar:horizontal { background: transparent; height: 10px; margin: 2px; }
QScrollBar::handle:horizontal { background: #3a3f46; border-radius: 5px; min-width: 30px; }
QScrollBar::handle:horizontal:hover { background: #4a5058; }
"""

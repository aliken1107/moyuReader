"""系统托盘：常驻 + 最近阅读 + 快捷菜单。"""
from PySide6.QtWidgets import QMenu, QSystemTrayIcon
from PySide6.QtGui import QAction

from .icon import make_icon


class Tray:
    def __init__(self, ctx, win):
        self.ctx = ctx
        self.win = win
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self.enabled = False
            self.icon = None
            return
        self.enabled = True
        self.icon = QSystemTrayIcon(make_icon())
        self.icon.setToolTip("MoyuReader")

        self.menu = QMenu()
        self.menu.addAction("显示/隐藏", self.win.toggle_visible)
        self.menu.addAction("打开本地文件…", self.ctx.open_file_dialog)
        self.menu.addAction("书架", self.win.show_bookshelf)
        self.menu.addAction("设置", self.win.show_settings)
        self.menu.addSeparator()
        self.act_pass = QAction("点击穿透悬浮窗", self.menu, checkable=True)
        self.act_pass.toggled.connect(lambda on: self.win.toggle_click_through(on))
        self.menu.addAction(self.act_pass)
        self.menu.addSeparator()
        self.recent_menu = self.menu.addMenu("最近阅读")
        self.menu.addSeparator()
        self.menu.addAction("退出", self.ctx.quit_app)

        self.menu.aboutToShow.connect(self._rebuild_recent)
        self.icon.setContextMenu(self.menu)
        self.icon.activated.connect(self._activated)
        self.icon.show()

    def _rebuild_recent(self):
        # 同步穿透开关的勾选状态（屏蔽信号，避免打开菜单时误触发开关）
        self.act_pass.blockSignals(True)
        self.act_pass.setChecked(self.win._click_through)
        self.act_pass.blockSignals(False)
        self.recent_menu.clear()
        for b in self.ctx.shelf[:5]:
            path = b.get("path", "")
            a = QAction(b.get("title", "未命名"), self.recent_menu)
            a.triggered.connect(lambda _, p=path: self.ctx.open_book(p, resume=True))
            self.recent_menu.addAction(a)
        if not self.ctx.shelf:
            empty = QAction("（无）", self.recent_menu)
            empty.setEnabled(False)
            self.recent_menu.addAction(empty)

    def _activated(self, reason):
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.win.toggle_visible()

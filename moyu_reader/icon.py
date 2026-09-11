"""程序图标（托盘/窗口）。若项目根目录或数据目录存在 icon.png 则优先使用。

小尺寸（≤48px，托盘/任务栏）用咸鱼头部特写，大尺寸用完整图——整条鱼缩到
16px 会糊成一团，头部大眼睛在小尺寸下才认得出来。
"""
import os
import sys
from pathlib import Path

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor, QIcon, QImage, QPainter, QPen, QPixmap

SMALL_SIZES = (16, 20, 24, 32, 48)
LARGE_SIZES = (64, 128, 256)


def _icon_candidates():
    """依次查找：exe/程序旁边（用户可自定义）→ 打包内置 → 开发项目根目录。"""
    cands = []
    if getattr(sys, "frozen", False):
        cands.append(Path(sys.executable).resolve().parent / "icon.png")
        meipass = os.environ.get("_MEIPASS")
        if meipass:
            cands.append(Path(meipass) / "icon.png")
    else:
        cands.append(Path(__file__).resolve().parent.parent / "icon.png")
    return cands


def _icon_file():
    for c in _icon_candidates():
        if c.exists():
            return c
    return None


def _head_crop(img):
    """从完整图标里裁出咸鱼头部（按相对比例，兼容任意分辨率的方图）。"""
    w, h = img.width(), img.height()
    side = int(min(w, h) * 0.46)
    x = int(w * 0.05)
    y = int(h * 0.10)
    return img.copy(QRect(x, y, side, side))


def _smooth(img, size):
    scaled = img.scaled(size, size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
    return QPixmap.fromImage(scaled)


def _icon_from_file(path):
    img = QImage(str(path))
    if img.isNull():
        return None
    icon = QIcon()
    head = _head_crop(img)
    for s in SMALL_SIZES:
        icon.addPixmap(_smooth(head, s))
    for s in LARGE_SIZES:
        icon.addPixmap(_smooth(img, s))
    return icon


def make_icon():
    f = _icon_file()
    if f:
        icon = _icon_from_file(f)
        if icon is not None:
            return icon
    # 默认图标：深色圆角底 + 两页绿色书本
    pix = QPixmap(64, 64)
    pix.fill(Qt.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#1e1e2e"))
    p.drawRoundedRect(4, 4, 56, 56, 14, 14)
    p.setBrush(QColor("#a6e3a1"))
    p.drawRoundedRect(13, 18, 13, 32, 3, 3)
    p.drawRoundedRect(38, 18, 13, 32, 3, 3)
    p.setPen(QPen(QColor("#1e1e2e"), 2))
    p.drawLine(26, 22, 38, 15)
    p.end()
    return QIcon(pix)

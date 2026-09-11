"""全局配置：数据目录、设置与书架持久化。"""
import json
import os
import sys
from pathlib import Path

APP_NAME = "MoyuReader"


def _data_dir() -> Path:
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME
    if os.name == "nt":
        return Path(os.environ.get("APPDATA", str(Path.home()))) / APP_NAME
    return Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))) / APP_NAME


DATA_DIR = _data_dir()
SETTINGS_FILE = DATA_DIR / "settings.json"
SHELF_FILE = DATA_DIR / "bookshelf.json"

DEFAULT_SETTINGS = {
    "skin": "code",            # 皮肤：code/word/paper/green/dark
    "font_size": 17,           # 正文字号
    "line_height": 1.65,       # 行距倍数
    "boss_key": "Ctrl+Shift+Z",  # 全局老板键（默认不占用系统 Esc）
    "opacity": 90,             # 窗口不透明度 1-100（所有模式生效）
    "always_on_top": False,    # 窗口是否置顶
    "auto_scroll_speed": 1,    # 自动滚动速度 0=关 1=慢 2=中 3=快
    "window_title": "MoyuReader",  # 窗口/托盘显示名称
    "geometry": None,          # 窗口位置与大小 [x, y, w, h]，关闭时保存
}


def load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save_json(path, data):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_settings():
    data = load_json(SETTINGS_FILE, {})
    merged = dict(DEFAULT_SETTINGS)
    merged.update({k: v for k, v in data.items() if k in DEFAULT_SETTINGS})
    return merged


def save_settings(settings):
    save_json(SETTINGS_FILE, settings)

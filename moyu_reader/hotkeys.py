"""Windows 全局热键（RegisterHotKey + 原生事件过滤器），用于老板键。

仅 Windows 可用；macOS/Linux 上 register() 返回 False，应用内 Esc/F12 仍可隐藏。
"""
import ctypes
import sys

from PySide6.QtCore import QAbstractNativeEventFilter

if sys.platform == "win32":
    from ctypes import wintypes

IS_WINDOWS = sys.platform == "win32"

MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
WM_HOTKEY = 0x0312

_FUNCTION_KEYS = {f"F{i}": 0x70 + i - 1 for i in range(1, 13)}
_EXTRA_KEYS = {"`": 0xC0, "-": 0xBD, "=": 0xBB, ";": 0xBA, ",": 0xBC, ".": 0xBE, "/": 0xBF}


def parse_hotkey(text: str):
    """把 'Ctrl+Shift+Z' 解析为 (modifiers, vk)，无法解析返回 None。"""
    parts = [p.strip().lower() for p in (text or "").split("+") if p.strip()]
    if not parts:
        return None
    mod = 0
    key = None
    for p in parts:
        if p == "ctrl":
            mod |= MOD_CONTROL
        elif p == "shift":
            mod |= MOD_SHIFT
        elif p == "alt":
            mod |= MOD_ALT
        elif p == "win":
            mod |= MOD_WIN
        else:
            key = p
    if key is None:
        return None
    up = key.upper()
    vk = _FUNCTION_KEYS.get(up) or _EXTRA_KEYS.get(key)
    if vk is None and len(key) == 1 and key.isalnum():
        vk = ord(up)
    if vk is None:
        return None
    return mod, vk


class GlobalHotkey(QAbstractNativeEventFilter):
    """注册一个全局热键；触发时回调 on_trigger。"""

    def __init__(self, on_trigger):
        super().__init__()
        self.on_trigger = on_trigger
        self._id = 0xC0DE
        self._registered = False
        self._current = None

    def register(self, text: str) -> bool:
        if not IS_WINDOWS:
            return False
        parsed = parse_hotkey(text)
        if not parsed:
            return False
        if self._current == parsed and self._registered:
            return True
        self.unregister()
        ok = ctypes.windll.user32.RegisterHotKey(None, self._id, parsed[0], parsed[1])
        if ok:
            self._current = parsed
            self._registered = True
        return bool(ok)

    def unregister(self):
        if IS_WINDOWS and self._registered:
            ctypes.windll.user32.UnregisterHotKey(None, self._id)
            self._registered = False
            self._current = None

    def nativeEventFilter(self, eventType, message):
        if IS_WINDOWS and eventType in (b"windows_generic_MSG", b"windows_dispatcher_MSG"):
            try:
                msg = wintypes.MSG.from_address(int(message))
            except Exception:
                return False, 0
            if msg.message == WM_HOTKEY and msg.wParam == self._id:
                self.on_trigger()
                return True, 0
        return False, 0

"""阅读皮肤：配色与字体，决定界面像不像阅读器。"""

SKINS = {
    "code": {
        "name": "代码伪装（暗色编辑器）",
        "bg": "#1e1e2e",
        "fg": "#a6e3a1",
        "selection": "#45475a",
        "font_family": "Consolas",
        "mono": True,
    },
    "word": {
        "name": "Word 文档",
        "bg": "#ffffff",
        "fg": "#1f1f1f",
        "selection": "#cce4ff",
        "font_family": "Microsoft YaHei",
        "mono": False,
    },
    "paper": {
        "name": "纸白",
        "bg": "#f6f1e7",
        "fg": "#3a3226",
        "selection": "#e6dcc8",
        "font_family": "Microsoft YaHei",
        "mono": False,
    },
    "green": {
        "name": "护眼绿",
        "bg": "#cce8cf",
        "fg": "#223322",
        "selection": "#a8d8ae",
        "font_family": "Microsoft YaHei",
        "mono": False,
    },
    "dark": {
        "name": "暗色",
        "bg": "#202124",
        "fg": "#d4d4d4",
        "selection": "#3c3f41",
        "font_family": "Microsoft YaHei",
        "mono": False,
    },
    "terminal": {
        "name": "终端（黑底绿字）",
        "bg": "#0c0c0c",
        "fg": "#33ff66",
        "selection": "#1f3d2a",
        "font_family": "Consolas",
        "mono": True,
    },
    "browser": {
        "name": "浏览器网页",
        "bg": "#ffffff",
        "fg": "#1f2937",
        "selection": "#cce0ff",
        "font_family": "Microsoft YaHei",
        "mono": False,
    },
    "wechat": {
        "name": "微信灰底",
        "bg": "#ededed",
        "fg": "#191919",
        "selection": "#c9e7c9",
        "font_family": "Microsoft YaHei",
        "mono": False,
    },
}


def get(skin_name: str):
    return SKINS.get(skin_name, SKINS["paper"])

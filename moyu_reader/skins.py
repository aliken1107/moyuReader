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
}


def get(skin_name: str):
    return SKINS.get(skin_name, SKINS["paper"])

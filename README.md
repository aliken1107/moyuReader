# 摸鱼小说阅读器（MoyuReader）

上班摸鱼看小说的 Windows 桌面应用，基于 **Python + PySide6**。核心卖点：**伪装皮肤 + 老板键 + 快捷翻页**，从外观到交互都不像阅读器。

需求来源见 [需求文档.md](需求文档.md)。当前为 MVP（需求 P0 范围）。

## 运行

```bash
pip install -r requirements.txt
python main.py
```

数据与进度保存在 `%APPDATA%\MoyuReader\`（`settings.json` / `bookshelf.json`）。

## 功能

- **本地阅读**：支持 **TXT / EPUB / PDF / MOBI / AZW3**（MOBI/AZW3 仅支持无加密文件；PDF 需带文字层）
  - TXT 自动按章节分章；EPUB 自动跳过封面/版权页；PDF 按页阅读；MOBI 按章节标题分章
- **目录面板**：`Ctrl+D` 打开章节列表，单击跳转、双击跳转并关闭，当前章高亮
- **排版**：字号 / 行距 / 5 套皮肤（代码伪装、Word、纸白、护眼绿、暗色）
- **翻页**：方向键 / PageUp/PageDown / 空格（Shift+空格上翻）翻页，点击屏幕两侧翻页，Ctrl+T 自动滚动
- **老板键**：全局热键一键隐藏（默认 `Ctrl+Shift+Z`，可在设置里改）；应用内 Esc / F12 也能隐藏
- **隐形模式（F11）**：无边框 + 半透明 + 置顶，阅读区可拖动窗口
- **尺寸预设**：`Ctrl+1` 小窗（360×280）、`Ctrl+2` 贴条（520×120，右下角，隐形）、`Ctrl+0` 恢复正常；也可拖窗口边缘自由缩放（最小 220×90），关闭时自动记住位置和大小
- **透明度**：设置里拖动滑块**实时生效**（1%-100%），对所有模式生效
- **托盘常驻**：关窗口最小化到托盘；托盘菜单含"最近阅读"快速续读
- **书架**：自动记录阅读进度与作者，按最近阅读排序（Ctrl+B）
- **界面**：无边框圆角深色窗口，窗口小于 240 高时自动隐藏状态栏

## 快捷键

| 按键 | 功能 |
|---|---|
| `→` / `空格` / `PageDown` | 下一页 |
| `←` / `Shift+空格` / `PageUp` | 上一页 |
| `Ctrl+Shift+Z`（全局，可改） | 老板键：一键隐藏/恢复 |
| `Esc` / `F12` | 应用内隐藏 |
| `F11` | 隐形模式（无边框置顶半透明） |
| `Ctrl+T` | 自动滚动开关 |
| `Ctrl+D` | 章节目录面板 |
| `Ctrl+1` / `Ctrl+2` / `Ctrl+0` | 小窗模式 / 贴条模式 / 恢复正常窗口 |
| `Ctrl+O` | 打开小说文件 |
| `Ctrl+B` | 书架 |
| `Ctrl+,` | 设置 |

## 打包发布（Windows）

```bash
# 1) 单文件 exe（注意用 python -m 方式调用，PATH 上的 pyinstaller 可能是旧版；
#    --add-data 必须带，否则打包后图标会退回默认图）
python -m PyInstaller --noconfirm --clean --noconsole --onefile --name MoyuReader --icon icon.ico --add-data "icon.png;." main.py
# 产物: dist/MoyuReader.exe（绿色版，双击即用）

# 2) 安装包（需 Inno Setup 6：winget install JRSoftware.InnoSetup）
#    编译脚本见 MoyuReader.iss
"$LOCALAPPDATA/Programs/Inno Setup 6/ISCC.exe" MoyuReader.iss
# 产物: installer/MoyuReader-Setup-0.1.0.exe
```

## 项目结构

```
main.py                     入口
moyu_reader/
  app.py                    应用装配 / AppContext（共享状态）
  config.py                 数据目录 / 设置持久化
  storage.py                书架 / 进度持久化
  hotkeys.py                Windows 全局热键（RegisterHotKey）
  skins.py                  皮肤定义
  parsers/                  TXT / EPUB 解析
  ui/
    main_window.py          主窗口（标题栏/快捷键/隐形模式/老板键）
    reader_view.py          阅读区（翻页/自动滚动/拖动）
    bookshelf.py            书架弹窗
    settings_dialog.py      设置弹窗
  tray.py                   系统托盘
```

## 与需求文档的说明性差异

- 需求文档里默认老板键为 `Esc`，但**全局 Esc 会抢占系统 Esc**，破坏其他软件的返回/取消。故默认全局老板键改为 `Ctrl+Shift+Z`（可配置），应用内按 Esc 仍可快速隐藏。
- 书源 / TTS / 云同步按评审决策不做，全部本地存储。

## 已知限制（MVP）

- 全局老板键若被其他程序占用会静默降级（应用内 Esc/F12 仍可用）。
- MOBI/AZW3 依赖开源库 `mobi`，**带 DRM（加密）的文件无法读取**（典型如 Kindle 商店购买的书）；自己下载/Calibre 转换的无加密文件可以。
- PDF 按页提取文字，扫描版（图片型）PDF 无文字层、不支持；个别特殊字体编码的 PDF 可能提取为空。
- 大文件（>50MB）TXT 整本读入内存，V1 再优化为分段加载。

## 免责声明

- 本工具仅提供**本地文件阅读**功能，不内置任何在线书源或内容分发，也不提供任何内容获取指引。
- 请支持正版；使用者打开的文件内容与开发者无关，由使用者自行负责。
- 伪装皮肤、老板键等功能仅供个人合理场景使用，请勿用于违法违规用途。


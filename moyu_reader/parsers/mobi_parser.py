"""MOBI / AZW3 解析：使用开源 mobi 库（仅支持无加密文件）。

mobi 库对 AZW3/KF8 通常解出一个 EPUB 文件，直接复用 EPUB 解析器；
对老式 MOBI（KF7）解出单个 HTML，按编码识别解码后按章节标题分章。
"""
from pathlib import Path

from ..models import Book, Chapter
from .epub_parser import _clean, _extract_text, parse_epub
from .txt_parser import _split_chapters


def parse_mobi(path) -> Book:
    try:
        import mobi
    except ImportError:
        raise ValueError("缺少依赖库：请先执行  pip install mobi")
    try:
        tempdir, filepath = mobi.extract(str(path))
    except Exception as e:
        raise ValueError(f"MOBI/AZW3 解析失败（Kindle 商店的加密书籍无法读取）：{e}")

    # 解出来是 EPUB（zip 魔数 PK\x03\x04）就按 EPUB 解析，进度仍记在原始文件上
    with open(filepath, "rb") as f:
        magic = f.read(4)
    if magic == b"PK\x03\x04" or filepath.lower().endswith(".epub"):
        book = parse_epub(filepath)
        book.path = str(path)
        book.fmt = "mobi"
        if not book.title:
            book.title = Path(path).stem
        return book

    with open(filepath, "rb") as f:
        raw = f.read()
    body = _clean(_extract_text(raw))
    if len(body) < 20:
        raise ValueError("MOBI/AZW3 中没有可读取的正文")
    chapters = _split_chapters(body)
    if not chapters:
        chapters = [Chapter(Path(path).stem, body)]
    return Book(str(path), Path(path).stem, "mobi", "", chapters)

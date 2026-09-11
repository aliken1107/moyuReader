from .txt_parser import parse_txt
from .epub_parser import parse_epub
from .pdf_parser import parse_pdf
from .mobi_parser import parse_mobi


def parse_book(path: str):
    """按扩展名选择解析器，返回 Book。"""
    lower = path.lower()
    if lower.endswith((".txt", ".text")):
        return parse_txt(path)
    if lower.endswith(".epub"):
        return parse_epub(path)
    if lower.endswith(".pdf"):
        return parse_pdf(path)
    if lower.endswith((".mobi", ".azw3", ".azw")):
        return parse_mobi(path)
    raise ValueError("不支持的文件格式，请选择 TXT / EPUB / PDF / MOBI / AZW3 文件")

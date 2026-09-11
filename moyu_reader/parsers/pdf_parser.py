"""PDF 解析：基于 PySide6 自带的 QtPdf 组件，每页作为一个"章"。"""
from pathlib import Path

from PySide6.QtPdf import QPdfDocument

from ..models import Book, Chapter


def parse_pdf(path) -> Book:
    doc = QPdfDocument()
    err = doc.load(str(path))
    if err != QPdfDocument.Error.None_ or doc.pageCount() == 0:
        raise ValueError(f"PDF 打开失败（{err}）或没有页面")
    try:
        chapters = []
        for i in range(doc.pageCount()):
            page_text = doc.getAllText(i)
            text = page_text.text() if hasattr(page_text, "text") else str(page_text)
            body = "\n".join(ln.strip() for ln in text.splitlines() if ln.strip())
            if not body:
                continue
            chapters.append(Chapter(f"第 {i + 1} 页", body))
        if not chapters:
            raise ValueError("此 PDF 没有可提取的文字（可能是扫描件/图片版），暂不支持")
        return Book(str(path), Path(path).stem, "pdf", "", chapters)
    finally:
        doc.close()

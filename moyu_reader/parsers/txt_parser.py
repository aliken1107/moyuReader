"""TXT 解析：自动识别章节标题分章，无章节时整本一章。"""
import re
from pathlib import Path

from ..models import Book, Chapter

# 常见章节标题：第1章 / 第 十二 节 / Chapter 3 / 卷五
CHAPTER_RE = re.compile(
    r"^\s*(?:"
    r"第\s*[0-9零一二三四五六七八九十百千万两]+\s*[章节卷回部集篇][\s、：:.]*"
    r"|(?:chapter)\s+\d+"
    r")\s*(.*)$",
    re.IGNORECASE,
)

# 常见"全书正文开始"的标记，用于裁掉 txt 前部的书名/简介
SKIP_LINES = {"简介", "内容简介", "作品简介", "目录", "正文", "楔子", "序章"}


def _decode(raw: bytes) -> str:
    for enc in ("utf-8-sig", "utf-8", "gb18030", "big5", "utf-16"):
        try:
            return raw.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return raw.decode("utf-8", errors="replace")


def _split_chapters(text: str) -> list:
    chapters = []
    cur_title = None
    cur_lines = []

    def flush():
        nonlocal cur_title, cur_lines
        body = "\n".join(cur_lines).strip()
        if cur_title and body:
            chapters.append(Chapter(cur_title, body))
        cur_lines = []

    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            cur_lines.append("")
            continue
        m = CHAPTER_RE.match(line)
        if m:
            flush()
            cur_title = (m.group(1).strip() or line.strip()).strip()
        elif line in SKIP_LINES and not cur_lines and cur_title is None:
            continue
        else:
            cur_lines.append(line)
    flush()
    return chapters


def parse_txt(path) -> Book:
    with open(path, "rb") as f:
        raw = f.read()
    text = _decode(raw)
    title = Path(path).stem
    chapters = _split_chapters(text)
    if not chapters:
        # 没有章节标题：整本作为一章，保证可读
        chapters = [Chapter(title, text.strip())]
    return Book(str(path), title, "txt", "", chapters)

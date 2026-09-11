"""EPUB 解析：仅用标准库（zipfile + xml + html.parser）。"""
import re
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote
from xml.etree import ElementTree as ET

from ..models import Book, Chapter
from .txt_parser import _split_chapters

NS = {
    "c": "urn:oasis:names:tc:opendocument:xmlns:container",
    "opf": "http://www.idpf.org/2007/opf",
    "dc": "http://purl.org/dc/elements/1.1/",
}

# 无意义文件名（part0001 之类），此时改用正文第一行当章节标题
GENERIC_TITLE_RE = re.compile(
    r"^(part|chapter|file|section|page|chap)[\s_\-]?\d+$|^toc$|^index$|^title$|^cover$",
    re.IGNORECASE,
)
CHAPTER_HEADING_RE = re.compile(r"第\s*[0-9零一二三四五六七八九十百千万两]+\s*[章节卷回部集篇]")


def _is_toc_page(body: str) -> bool:
    """目录页：开头密集出现章节标题，或以 Contents/目录 开头的短页。"""
    head = body[:500]
    if len(CHAPTER_HEADING_RE.findall(head)) >= 5:
        return True
    first = body[:40].strip().lower()
    return first.startswith(("contents", "目录", "table of contents")) and len(body) < 3000


def _chapter_title(stem: str, body: str) -> str:
    """文件名无意义时，用正文第一行作为章节标题。"""
    if not stem or GENERIC_TITLE_RE.match(stem):
        first = next((ln.strip() for ln in body.splitlines() if ln.strip()), "")
        first = re.sub(r"^§+", "", first).strip()
        if first:
            return first[:30]
    return stem


def _maybe_resplit(chapter: Chapter) -> list:
    """超长章节（常见于 KF8 整本压成一个 html）按“第x章”标题重新拆分。"""
    if len(chapter.text) < 30000:
        return [chapter]
    subs = _split_chapters(chapter.text.replace("§§", ""))
    return subs if len(subs) >= 3 else [chapter]


class _TextExtract(HTMLParser):
    """提取 HTML/XML 里的可见文本，保留段落换行。"""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self._skip += 1
        if tag in ("p", "div", "br", "h1", "h2", "h3", "h4", "h5", "li", "tr", "blockquote"):
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if not self._skip:
            self.parts.append(data)

    def text(self):
        return "".join(self.parts)


def decode_bytes(raw: bytes) -> str:
    """按 BOM / 声明的 charset / 常见编码猜测解码，全部失败再用 replace 兜底。"""
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw.decode("utf-8-sig", errors="replace")
    if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        return raw.decode("utf-16", errors="replace")
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        pass
    # HTML meta 里声明的 charset（前 2KB 内）
    m = re.search(rb'charset=["\']?([\w-]+)', raw[:2048], re.IGNORECASE)
    if m:
        enc = m.group(1).decode("ascii", "ignore").lower()
        for candidate in (enc, "gb18030" if enc.startswith("gb") else enc):
            try:
                return raw.decode(candidate)
            except (UnicodeDecodeError, LookupError):
                continue
    for enc in ("gb18030", "big5"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def _extract_text(data: bytes) -> str:
    p = _TextExtract()
    p.feed(decode_bytes(data))
    p.close()
    return p.text()


def _clean(raw: str) -> str:
    out = []
    for ln in raw.splitlines():
        s = ln.strip()
        if s:
            out.append(s)
        elif out and out[-1] != "":
            out.append("")
    return "\n".join(out)


def parse_epub(path) -> Book:
    with zipfile.ZipFile(path) as z:
        # 1) container.xml 找到 OPF 路径
        container = ET.fromstring(z.read("META-INF/container.xml"))
        rootfile = container.find(".//c:rootfile", NS)
        if rootfile is None:
            raise ValueError("无效的 EPUB：缺少 container.xml 根文件")
        opf_path = rootfile.get("full-path")
        opf_dir = Path(opf_path).parent

        # 2) OPF：书名 / 清单 / 阅读顺序
        opf = ET.fromstring(z.read(opf_path))
        title_el = opf.find(".//opf:metadata/dc:title", NS)
        default_title = Path(path).stem
        title = (title_el.text or "").strip() or default_title
        author_el = opf.find(".//opf:metadata/dc:creator", NS)
        author = (author_el.text or "").strip() if author_el is not None else ""

        manifest = {}
        for item in opf.findall(".//opf:manifest/opf:item", NS):
            manifest[item.get("id")] = (item.get("href"), item.get("media-type") or "")
        spine = [i.get("idref") for i in opf.findall(".//opf:spine/opf:itemref", NS)]

        # 3) 按 spine 顺序读取正文；跳过封面/扉页/版权页等短页
        chapters = []
        min_chars = 150  # 短于此长度的页面视为封面/版权页，跳过
        for idref in spine:
            item = manifest.get(idref)
            if not item:
                continue
            href, media_type = item
            lower_href = href.lower()
            if not lower_href.endswith((".html", ".xhtml", ".htm")) and \
               media_type not in ("application/xhtml+xml", "text/html"):
                continue  # 非正文资源（图片、ncx、css 等）
            full = (opf_dir / href.replace("\\", "/")).as_posix()
            try:
                raw = z.read(full)
            except KeyError:
                try:
                    raw = z.read(full.lstrip("/"))
                except KeyError:
                    continue
            body = _clean(_extract_text(raw))
            if len(body) < min_chars:
                continue
            if _is_toc_page(body):
                continue  # 目录/版权页不进章节列表
            chap_title = _chapter_title(Path(unquote(href)).stem, body)
            chapters.extend(_maybe_resplit(Chapter(chap_title, body)))

    if not chapters:
        raise ValueError("EPUB 中没有可读取的正文")
    return Book(str(path), title, "epub", author, chapters)

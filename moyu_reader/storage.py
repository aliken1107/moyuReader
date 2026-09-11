"""书架与阅读进度持久化（本地 JSON）。"""
import time

from . import config


def load_bookshelf():
    data = config.load_json(config.SHELF_FILE, {})
    books = data.get("books", [])
    books.sort(key=lambda b: b.get("last_read", 0), reverse=True)
    return books


def save_bookshelf(books):
    config.save_json(config.SHELF_FILE, {"books": books})


def touch(path, title, fmt, chapter=0, offset=0.0, author="", percent=None):
    """记录一本书的阅读进度，按最近阅读时间排序。

    保留旧条目里进度之外的自定义字段（如书签 bookmarks）。
    """
    books = load_bookshelf()
    old = next((b for b in books if b.get("path") == path), None)
    if old is not None:
        books.remove(old)
    entry = {
        "path": path,
        "title": title,
        "fmt": fmt,
        "author": author,
        "chapter": chapter,
        "offset": offset,
        "percent": percent,
        "last_read": time.time(),
    }
    if old is not None:
        for k, v in old.items():
            if k not in entry:
                entry[k] = v
    books.append(entry)
    books.sort(key=lambda b: b.get("last_read", 0), reverse=True)
    save_bookshelf(books)


def remove(path):
    books = load_bookshelf()
    books = [b for b in books if b.get("path") != path]
    save_bookshelf(books)


def find(path):
    for b in load_bookshelf():
        if b.get("path") == path:
            return b
    return None


def add_bookmark(path, chapter, offset, label):
    """给一本书加书签（上限 100 条），返回是否成功。"""
    books = load_bookshelf()
    for b in books:
        if b.get("path") == path:
            marks = b.setdefault("bookmarks", [])
            marks.append({"chapter": chapter, "offset": offset, "label": label})
            b["bookmarks"] = marks[-100:]
            save_bookshelf(books)
            return True
    return False


def remove_bookmark(path, index):
    books = load_bookshelf()
    for b in books:
        if b.get("path") == path:
            marks = b.get("bookmarks", [])
            if 0 <= index < len(marks):
                marks.pop(index)
                b["bookmarks"] = marks
                save_bookshelf(books)
            return


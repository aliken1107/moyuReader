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
    """记录一本书的阅读进度，按最近阅读时间排序。"""
    books = load_bookshelf()
    books = [b for b in books if b.get("path") != path]
    books.append({
        "path": path,
        "title": title,
        "fmt": fmt,
        "author": author,
        "chapter": chapter,
        "offset": offset,
        "percent": percent,
        "last_read": time.time(),
    })
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

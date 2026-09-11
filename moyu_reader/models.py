"""数据模型。"""
from dataclasses import dataclass, field


@dataclass
class Chapter:
    title: str
    text: str


@dataclass
class Book:
    path: str
    title: str
    fmt: str                      # txt / epub
    author: str = ""              # 作者（EPUB 元数据，TXT 留空）
    chapters: list = field(default_factory=list)

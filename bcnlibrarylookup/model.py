from dataclasses import dataclass
from typing import Optional


@dataclass
class Book:
    title: str
    author_full: Optional[str]
    author: str
    shelf: str  # i.e. from goodreads organization

@dataclass
class BookResult:
    title: str
    link: str

@dataclass
class BookEdition:
    title: str
    link: str
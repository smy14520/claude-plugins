"""wikicore —— 本地 Markdown 个人 Wiki 知识库管理内核。"""

from .doctor import DoctorReport, diagnose
from .indexer import build_index, write_index
from .model import Page, WikiIndex
from .search import SearchHit, search

__version__ = "0.1.0"

__all__ = [
    "DoctorReport",
    "Page",
    "SearchHit",
    "WikiIndex",
    "__version__",
    "build_index",
    "diagnose",
    "search",
    "write_index",
]

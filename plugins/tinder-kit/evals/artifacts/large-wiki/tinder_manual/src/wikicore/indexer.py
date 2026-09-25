"""扫描知识库并全量构建索引；落盘单个 .wiki_index.json（ADR-0001）。"""

from __future__ import annotations

import json
import os
from collections.abc import Iterator
from pathlib import Path

from .frontmatter import parse_frontmatter_tags, split_frontmatter
from .links import extract_link_targets
from .model import Page, WikiIndex
from .tags import extract_inline_tags

INDEX_FILENAME = ".wiki_index.json"
SCHEMA_VERSION = 1

_SKIP_DIRS = {"node_modules", "__pycache__"}


def scan_markdown_files(root: Path) -> Iterator[Path]:
    """深度优先枚举 `.md` 文件；跳过隐藏目录与常见噪音目录。"""
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(
            d for d in dirnames if not d.startswith(".") and d not in _SKIP_DIRS
        )
        for name in sorted(filenames):
            if name.lower().endswith(".md"):
                yield Path(dirpath) / name


def build_index(root: Path) -> WikiIndex:
    """全量重建索引：文件系统是唯一真实源，每次调用都从零扫描。"""
    root = root.resolve()
    pages: list[Page] = []
    for path in scan_markdown_files(root):
        text = path.read_text(encoding="utf-8", errors="replace")
        fm_lines, body = split_frontmatter(text)
        tag_set = {t.lower() for t in parse_frontmatter_tags(fm_lines)}
        tag_set.update(extract_inline_tags(body))
        pages.append(
            Page(
                title=path.stem,
                path=path.relative_to(root).as_posix(),
                links=sorted(set(extract_link_targets(body))),
                tags=sorted(tag_set),
                body=body,
            )
        )
    pages.sort(key=lambda p: (p.title, p.path))
    return WikiIndex(root=root, pages=pages)


def index_path(root: Path) -> Path:
    return root / INDEX_FILENAME


def index_to_dict(index: WikiIndex) -> dict:
    return {
        "schema": SCHEMA_VERSION,
        "pages": [
            {"title": p.title, "path": p.path, "links": p.links, "tags": p.tags}
            for p in index.pages
        ],
    }


def write_index(index: WikiIndex) -> Path:
    """持久化索引快照（不含时间戳，减少 diff 噪音）。"""
    target = index_path(index.root)
    payload = json.dumps(
        index_to_dict(index), ensure_ascii=False, indent=2, sort_keys=True
    )
    target.write_text(payload + "\n", encoding="utf-8")
    return target

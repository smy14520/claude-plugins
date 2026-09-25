"""索引构建与持久化。

策略（ADR-0002 / ADR-0004）：
- 单一 `.wiki_index.json`，先写 `.tmp` 再 `os.replace` 原子落盘；
- `build_index` 按 `(mtime, size)` 增量：未变更页复用旧 PageInfo 与旧 postings，
  变更/新增页重扫重算，消失页剔除；派生结构等价于全量重建；
- 发现 casefold 冲突的 PageName 时抛 DuplicatePageError，绝不落盘。
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from .model import Index, PageInfo
from .parser import Link, scan_page
from .tokenize import tokenize

INDEX_NAME = ".wiki_index.json"


class IndexNotFound(Exception):
    """vault 根下不存在 `.wiki_index.json`。"""


class DuplicatePageError(Exception):
    """两个文件 casefold 后的 PageName 冲突（ADR-0001）。"""


def _md_files(root: Path) -> list[Path]:
    return sorted(
        path for path in root.rglob("*.md")
        if not any(part.startswith(".") for part in path.relative_to(root).parts)
    )


def build_index(root: Path, previous: Index | None = None) -> Index:
    pages: dict[str, PageInfo] = {}
    fold_seen: dict[str, str] = {}
    fresh_tokens: dict[str, list[str]] = {}

    for path in _md_files(root):
        rel = path.relative_to(root).as_posix()
        name = path.stem
        fold = name.casefold()
        if fold in fold_seen:
            raise DuplicatePageError(
                f"页面名冲突（大小写不敏感）: {fold_seen[fold]!r} 与 {rel!r}"
            )
        fold_seen[fold] = rel

        stat = path.stat()
        old = previous.pages.get(name) if previous else None
        if old and old.file == rel and old.mtime == stat.st_mtime and old.size == stat.st_size:
            pages[name] = old
        else:
            text = path.read_text(encoding="utf-8")
            scan = scan_page(text)
            pages[name] = PageInfo(
                file=rel, mtime=stat.st_mtime, size=stat.st_size,
                links=scan.links, tags=scan.tags,
            )
            fresh_tokens[name] = tokenize(text)

    index = Index(pages=pages, postings=_merge_postings(pages, previous, fresh_tokens))
    return index


def _merge_postings(
    pages: dict[str, PageInfo],
    previous: Index | None,
    fresh_tokens: dict[str, list[str]],
) -> dict[str, dict[str, int]]:
    postings: dict[str, dict[str, int]] = {}
    for name, tokens in fresh_tokens.items():
        for token in tokens:
            hits = postings.setdefault(token, {})
            hits[name] = hits.get(name, 0) + 1

    if previous:
        # 仅复用未被重扫页面的旧倒排；重扫页（fresh_tokens 中）以新计算结果为准
        reused = set(pages) - set(fresh_tokens)
        for token, hits in previous.postings.items():
            kept = {page: tf for page, tf in hits.items() if page in reused}
            if kept:
                postings.setdefault(token, {}).update(kept)
    return postings


def save_index(index: Index, root: Path) -> None:
    payload = {
        "version": index.version,
        "pages": {
            name: {
                "file": info.file,
                "mtime": info.mtime,
                "size": info.size,
                "links": [[link.target, link.line] for link in info.links],
                "tags": list(info.tags),
            }
            for name, info in index.pages.items()
        },
        "postings": index.postings,
    }
    tmp = root / (INDEX_NAME + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    os.replace(tmp, root / INDEX_NAME)


def load_index(root: Path) -> Index:
    path = root / INDEX_NAME
    if not path.is_file():
        raise IndexNotFound(f"索引不存在: {path}，请先运行 build")
    payload = json.loads(path.read_text(encoding="utf-8"))
    return Index(
        version=payload.get("version", 1),
        pages={
            name: PageInfo(
                file=item["file"],
                mtime=item["mtime"],
                size=item["size"],
                links=[Link(target, line) for target, line in item["links"]],
                tags=list(item["tags"]),
            )
            for name, item in payload.get("pages", {}).items()
        },
        postings={
            token: dict(hits) for token, hits in payload.get("postings", {}).items()
        },
    )


def index_out_of_date(index: Index, root: Path) -> bool:
    disk_files = {path.relative_to(root).as_posix() for path in _md_files(root)}
    indexed_files = {info.file for info in index.pages.values()}
    if disk_files != indexed_files:
        return True
    for info in index.pages.values():
        stat = (root / info.file).stat()
        if stat.st_mtime != info.mtime or stat.st_size != info.size:
            return True
    return False

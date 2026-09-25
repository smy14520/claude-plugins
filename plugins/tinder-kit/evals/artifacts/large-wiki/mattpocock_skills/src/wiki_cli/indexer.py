"""索引的构建、缓存校验与原子写回。

文件系统是唯一真相：每次命令先 walk + stat 与缓存比对，一致则直接用缓存，
否则全量重建（不做单页增量）。缓存缺失、损坏、schema 版本不符一律视为
不存在。见 ADR-0002。
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from .model import INDEX_FILENAME, INDEX_VERSION, Index, Page, WikiLink
from .parser import parse_page, read_lines


@dataclass(frozen=True)
class PageRef:
    """walk 阶段的一条页面引用：身份、路径与 stat 指纹。"""

    name: str
    rel_path: str
    abs_path: Path
    size: int
    mtime_ns: int


def collect(root: Path) -> list[PageRef]:
    """枚举 Vault 内全部 .md 文件（扩展名小写严格匹配）。

    以点开头的文件与目录（.git、.obsidian、缓存自身）整体跳过。
    返回按相对路径排序的列表，保证产物确定、可 diff。
    """
    refs: list[PageRef] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        for filename in sorted(filenames):
            if filename.startswith(".") or not filename.endswith(".md"):
                continue
            abs_path = Path(dirpath) / filename
            rel_path = abs_path.relative_to(root).as_posix()
            stat = abs_path.stat()
            refs.append(
                PageRef(
                    name=filename[: -len(".md")],
                    rel_path=rel_path,
                    abs_path=abs_path,
                    size=stat.st_size,
                    mtime_ns=stat.st_mtime_ns,
                )
            )
    return refs


def _fingerprint(refs: list[PageRef]) -> dict[str, tuple[int, int]]:
    return {r.rel_path: (r.size, r.mtime_ns) for r in refs}


def _is_fresh(index: Index, refs: list[PageRef]) -> bool:
    if index.version != INDEX_VERSION:
        return False
    cached = {p.rel_path: (p.size, p.mtime_ns) for p in index.pages}
    return cached == _fingerprint(refs)


def _page_to_json(page: Page) -> dict:
    data: dict = {
        "name": page.name,
        "path": page.rel_path,
        "size": page.size,
        "mtime_ns": page.mtime_ns,
        "tags": list(page.tags),
        "links": [],
        "malformed_frontmatter": page.malformed_frontmatter,
    }
    for link in page.links:
        entry: dict = {"target": link.target, "raw": link.raw, "line": link.line}
        if link.alias:
            entry["alias"] = link.alias
        if link.anchor:
            entry["anchor"] = link.anchor
        if link.embed:
            entry["embed"] = True
        if link.external:
            entry["external"] = True
        data["links"].append(entry)
    return data


def _index_to_json(index: Index) -> dict:
    return {
        "version": index.version,
        "pages": [_page_to_json(p) for p in index.pages],
    }


def _link_from_json(entry: dict) -> WikiLink:
    return WikiLink(
        target=entry["target"],
        raw=entry["raw"],
        line=entry["line"],
        alias=entry.get("alias"),
        anchor=entry.get("anchor"),
        embed=entry.get("embed", False),
        external=entry.get("external", False),
    )


def _index_from_json(data: dict) -> Index | None:
    """schema 不符、字段缺失、类型不对的缓存一律返回 None，调用方按不存在处理。"""
    try:
        pages = tuple(
            Page(
                name=p["name"],
                rel_path=p["path"],
                size=p["size"],
                mtime_ns=p["mtime_ns"],
                tags=tuple(p["tags"]),
                links=tuple(_link_from_json(e) for e in p["links"]),
                malformed_frontmatter=p.get("malformed_frontmatter", False),
            )
            for p in data["pages"]
        )
    except (KeyError, TypeError, ValueError, AttributeError):
        return None
    return Index(version=data.get("version", -1), pages=pages)


def build(refs: list[PageRef]) -> Index:
    """全量解析每个页面，构建内存索引。"""
    pages = []
    for ref in refs:
        pages.append(
            parse_page(
                name=ref.name,
                rel_path=ref.rel_path,
                size=ref.size,
                mtime_ns=ref.mtime_ns,
                lines=read_lines(ref.abs_path),
            )
        )
    return Index(version=INDEX_VERSION, pages=tuple(pages))


def _write_atomic(path: Path, index: Index) -> None:
    """临时文件 + os.replace 原子写回，写坏不污染旧缓存。"""
    payload = json.dumps(
        _index_to_json(index), ensure_ascii=False, indent=2, sort_keys=True
    )
    tmp = path.parent / (path.name + ".tmp")
    tmp.write_text(payload + "\n", encoding="utf-8")
    os.replace(tmp, path)


def _read_cache(path: Path) -> Index | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    return _index_from_json(data)


def load(root: Path) -> tuple[Index, bool]:
    """加载索引：缓存新鲜则复用，否则全量重建并写回。返回 (索引, 是否命中缓存)。"""
    refs = collect(root)
    cache_path = root / INDEX_FILENAME
    cached = _read_cache(cache_path)
    if cached is not None and _is_fresh(cached, refs):
        return cached, True
    index = build(refs)
    _write_atomic(cache_path, index)
    return index, False


def rebuild(root: Path) -> Index:
    """忽略缓存状态，强制全量重建并写回。"""
    index = build(collect(root))
    _write_atomic(root / INDEX_FILENAME, index)
    return index

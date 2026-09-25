"""索引器测试：收集规则、缓存新鲜度、原子写回、重名。"""

from __future__ import annotations

import json

from wiki_cli import indexer
from wiki_cli.model import INDEX_VERSION, Index, Page, WikiLink


def test_collect_skips_hidden_and_non_md(vault):
    root = vault(
        {
            "a.md": "x",
            "notes/b.md": "y",
            ".hidden/z.md": "s",
            ".obsidian/c.md": "s",
            "d.txt": "s",
            ".draft.md": "s",
        }
    )
    refs = indexer.collect(root)
    assert [r.rel_path for r in refs] == ["a.md", "notes/b.md"]


def test_page_name_strips_md_only(vault):
    root = vault({"子目录/页面名.md": ""})
    (ref,) = indexer.collect(root)
    assert ref.name == "页面名"


def test_cache_hit_when_unchanged(vault):
    root = vault({"a.md": "#t [[b]]"})
    index1, fresh1 = indexer.load(root)
    assert not fresh1
    index2, fresh2 = indexer.load(root)
    assert fresh2
    assert index2.pages == index1.pages
    assert (root / ".wiki_index.json").exists()


def test_rebuild_on_file_change(vault):
    root = vault({"a.md": "旧"})
    indexer.load(root)
    (root / "a.md").write_text("新 [[x]]", encoding="utf-8")
    index, fresh = indexer.load(root)
    assert not fresh
    assert any(link.target == "x" for link in index.pages[0].links)


def test_rebuild_on_new_or_deleted_file(vault):
    root = vault({"a.md": ""})
    indexer.load(root)
    (root / "b.md").write_text("", encoding="utf-8")
    _, fresh = indexer.load(root)
    assert not fresh


def test_corrupt_cache_is_rebuilt(vault):
    root = vault({"a.md": ""})
    indexer.load(root)
    (root / ".wiki_index.json").write_text("{不是 JSON", encoding="utf-8")
    index, fresh = indexer.load(root)
    assert not fresh
    assert json.loads((root / ".wiki_index.json").read_text(encoding="utf-8"))[
        "version"
    ] == INDEX_VERSION


def test_version_mismatch_is_rebuilt(vault):
    root = vault({"a.md": ""})
    indexer.load(root)
    data = json.loads((root / ".wiki_index.json").read_text(encoding="utf-8"))
    data["version"] = INDEX_VERSION + 999
    (root / ".wiki_index.json").write_text(
        json.dumps(data, ensure_ascii=False), encoding="utf-8"
    )
    _, fresh = indexer.load(root)
    assert not fresh


def test_atomic_write_leaves_no_tmp(vault):
    root = vault({"a.md": ""})
    indexer.load(root)
    assert not list(root.glob("*.tmp"))


def test_duplicate_names_collected(vault):
    root = vault({"a/dup.md": "", "b/dup.md": ""})
    index, _ = indexer.load(root)
    assert len(index.by_name()["dup"]) == 2


def test_index_json_contains_no_body(vault):
    root = vault({"a.md": "机密正文 [[b]]"})
    indexer.load(root)
    raw = (root / ".wiki_index.json").read_text(encoding="utf-8")
    assert "机密正文" not in raw
    assert "b" in raw


def test_cache_write_read_roundtrip_all_fields(vault):
    """写回 → 读回的完整路径：全字段一致，含可选字段与畸形标志。"""
    root = vault(
        {
            "notes/页.md": (
                "---\ntags: [t1, t2]\n---\n"
                "正文 [[b.md#锚|别名]] ![[c]] [[https://x.com]] #tag"
            ),
            "b.md": "",
            "c.md": "",
            "d.md": "---\n未闭合",
        }
    )
    built, fresh1 = indexer.load(root)
    assert not fresh1
    cached, fresh2 = indexer.load(root)  # 从写回的缓存读回
    assert fresh2
    assert cached == built


def test_index_json_roundtrip_equality():
    """序列化单测：每个字段都必须原样往返，垃圾表达式在此现形。"""
    index = Index(
        version=INDEX_VERSION,
        pages=(
            Page(
                name="页",
                rel_path="d/页.md",
                size=12,
                mtime_ns=1234567890,
                tags=("t1", "t2"),
                links=(
                    WikiLink(
                        target="t", raw="t.md", line=3, alias="别名", anchor="锚",
                        embed=True,
                    ),
                    WikiLink(
                        target="https://x", raw="https://x", line=4, external=True
                    ),
                    WikiLink(target="p", raw="p", line=5),
                ),
                malformed_frontmatter=True,
            ),
        ),
    )
    restored = indexer._index_from_json(indexer._index_to_json(index))
    assert restored == index

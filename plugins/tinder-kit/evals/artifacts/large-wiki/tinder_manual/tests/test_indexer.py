"""扫描规则与索引落盘（Q7 / spec 解析歧义规则）。"""

import json

from wikicore.indexer import build_index, index_path, write_index


def test_scan_skips_hidden_and_noise_dirs(vault):
    root = vault(
        {
            "a.md": "A",
            "sub/b.md": "B",
            ".hidden/c.md": "C",
            "node_modules/d.md": "D",
            "not-md.txt": "[[A]]",
        }
    )
    index = build_index(root)
    assert [p.path for p in index.pages] == ["a.md", "sub/b.md"]


def test_page_identity_is_stem_case_sensitive(vault):
    root = vault({"My Page.md": "内容"})
    index = build_index(root)
    assert index.pages[0].title == "My Page"


def test_links_and_tags_normalized(vault):
    root = vault({"a.md": "#Go [[B]] [[B|别名]] [[B#x]] #go"})
    page = build_index(root).pages[0]
    assert page.links == ["B"]
    assert page.tags == ["go"]


def test_frontmatter_tags_merged_and_lowercased(vault):
    root = vault({"a.md": "---\ntags: [Python]\n---\n#python #java"})
    assert build_index(root).pages[0].tags == ["java", "python"]


def test_duplicate_titles_both_kept(vault):
    root = vault({"a/Z.md": "甲", "b/Z.md": "乙"})
    index = build_index(root)
    assert [p.path for p in index.title_map()["Z"]] == ["a/Z.md", "b/Z.md"]


def test_write_index_is_deterministic_json(vault):
    root = vault({"b.md": "[[A]] #t2", "a.md": "#t1"})
    index = build_index(root)
    assert write_index(index) == index_path(root)
    data = json.loads((root / ".wiki_index.json").read_text(encoding="utf-8"))
    assert data["schema"] == 1
    assert [p["title"] for p in data["pages"]] == ["a", "b"]
    assert data["pages"][0]["tags"] == ["t1"]
    assert data["pages"][0]["links"] == []
    assert data["pages"][1]["links"] == ["A"]

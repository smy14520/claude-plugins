"""检索语义：AND、大小写不敏感、命中数排序、摘要、frontmatter 排除（Q6）。"""

from wikicore.indexer import build_index
from wikicore.search import search


def _index(vault):
    return build_index(
        vault(
            {
                "py.md": "Python 是一门语言，python 简单。",
                "rs.md": "Rust 与 python 互操作。",
                "no.md": "毫无相关内容。",
            }
        )
    )


def test_and_semantics(vault):
    hits = search(_index(vault), ["python", "互操作"])
    assert [h.page.title for h in hits] == ["rs"]


def test_case_insensitive(vault):
    hits = search(_index(vault), ["PYTHON"])
    assert [h.page.title for h in hits] == ["py", "rs"]


def test_ranked_by_hit_count(vault):
    hits = search(_index(vault), ["python"])
    assert [(h.page.title, h.count) for h in hits] == [("py", 2), ("rs", 1)]


def test_snippet_contains_term(vault):
    hits = search(_index(vault), ["互操作"])
    assert "互操作" in hits[0].snippet


def test_long_line_snippet_windowed(vault):
    body = "前缀" * 60 + "关键词" + "后缀" * 60
    root = vault({"a.md": body})
    snippet = search(build_index(root), ["关键词"])[0].snippet
    assert snippet.startswith("…") and snippet.endswith("…")
    assert "关键词" in snippet


def test_frontmatter_excluded_from_search(vault):
    root = vault({"a.md": "---\ntags: [secretword]\n---\n正文无关键词"})
    assert search(build_index(root), ["secretword"]) == []


def test_empty_terms_no_hits(vault):
    assert search(_index(vault), []) == []

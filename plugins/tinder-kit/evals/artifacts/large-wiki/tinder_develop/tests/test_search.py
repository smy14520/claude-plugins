"""Seam 3 续：Index.search 全文检索（ADR-0003 混合倒排 + TF 排序）。

契约：查询的**计算路径只读索引**（ADR-0004 修订）——
页面文件删除后检索仍可作答；摘要由 CLI 层渲染（tests/test_cli.py）。
"""

import pytest

from wikicore.indexer import build_index
from wikicore.tokenize import tokenize

FILES = {
    "python.md": "Python 是一门语言，写 python 很简洁",
    "笔记.md": "学习 python 与知识库建设",
    "中文.md": "这是一个知识库条目",
    "无关.md": "完全无关的内容",
}


@pytest.fixture
def built(tmp_path, write_vault):
    write_vault(tmp_path, FILES)
    return tmp_path, build_index(tmp_path)


def test_latin_search_ranks_by_term_frequency(built):
    root, index = built

    hits = index.search("python")

    assert [(h.page, h.score) for h in hits] == [("python", 2), ("笔记", 1)]


def test_cjk_bigram_finds_substring_meaning(built):
    root, index = built

    hits = index.search("知识库")

    assert {h.page for h in hits} == {"笔记", "中文"}
    assert all(h.score == 2 for h in hits)
    assert not any(hasattr(h, "snippet") for h in hits)  # 摘要不属于内核命中


def test_multi_token_query_requires_all_tokens(built):
    root, index = built

    # AND 语义：仅「笔记」同时含 python 与 知识
    assert [h.page for h in index.search("python 知识")] == ["笔记"]


def test_no_match_returns_empty(built):
    root, index = built

    assert index.search("java") == []
    assert index.search("   ") == []


def test_single_cjk_char_is_unigram_token(built):
    root, index = built

    # "库存" 的二元组不在任何页面中 —— ADR-0003 记录了此局限
    assert index.search("库存") == []


def test_search_reads_only_index_not_vault_files(built):
    root, index = built

    for rel in FILES:  # 摘掉全部原文：查询仍须作答
        (root / rel).unlink()

    assert [(h.page, h.score) for h in index.search("python")] == [
        ("python", 2), ("笔记", 1)
    ]


def test_tokenize_mixed_script():
    assert tokenize("Python 知识库!") == ["python", "知识", "识库"]
    assert tokenize("单字") == ["单字"]  # 两字 CJK run → 一个 bigram

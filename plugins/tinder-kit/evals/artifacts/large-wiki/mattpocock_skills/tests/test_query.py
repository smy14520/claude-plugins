"""查询层测试：反链、出链状态、标签聚合、检索语义。"""

from __future__ import annotations

from wiki_cli import indexer, query
from wiki_cli.query import LinkStatus


def load(vault, files):
    return indexer.load(vault(files))[0]


def test_backlinks_with_sources(vault):
    index = load(
        vault,
        {
            "a.md": "[[目标]]",
            "b.md": "见 [[目标|别名]] 两次 [[目标]]",
            "c.md": "无关",
        },
    )
    pairs = query.backlinks(index, "目标")
    assert [p.name for p, _ in pairs] == ["a", "b", "b"]
    assert pairs[1][1].alias == "别名"


def test_backlinks_ignores_external_and_unrelated(vault):
    index = load(vault, {"a.md": "[[https://x.com]] [[别的]]", "目标.md": ""})
    assert query.backlinks(index, "目标") == []


def test_resolve_target_statuses(vault):
    index = load(vault, {"存在.md": "", "x/dup.md": "", "y/dup.md": ""})
    assert query.resolve_target(index, "存在")[0] == LinkStatus.RESOLVED
    assert query.resolve_target(index, "缺页")[0] == LinkStatus.DEAD
    assert query.resolve_target(index, "dup")[0] == LinkStatus.AMBIGUOUS


def test_tag_counts_sorted_by_count_then_name(vault):
    index = load(
        vault,
        {"a.md": "#b #a", "b.md": "#a", "c.md": "---\ntags: [a]\n---\n无标签正文"},
    )
    assert query.tag_counts(index) == [("a", 3), ("b", 1)]


def test_tag_pages_dedup_across_sources(vault):
    index = load(vault, {"a.md": "---\ntags: [t]\n---\n#t"})
    assert [p.name for p in query.tag_pages(index, "t")] == ["a"]


def test_search_requires_all_terms(vault, tmp_path):
    index = load(vault, {"a.md": "有 机器学习 和 深度", "b.md": "只有 机器"})
    hits = query.search(index, tmp_path, ["机器", "深度"])
    assert [h.page.name for h in hits] == ["a"]


def test_search_casefold_latin(vault, tmp_path):
    index = load(vault, {"a.md": "Runner beans", "b.md": "无关"})
    assert [h.page.name for h in query.search(index, tmp_path, ["runner"])] == ["a"]


def test_search_cjk_substring(vault, tmp_path):
    index = load(vault, {"a.md": "研究机器学习的技术", "b.md": "无关"})
    assert [h.page.name for h in query.search(index, tmp_path, ["机器学习"])] == ["a"]


def test_search_frontmatter_excluded(vault, tmp_path):
    index = load(vault, {"a.md": "---\ntags: [x]\nsecret: 密钥\n---\n正文"})
    assert query.search(index, tmp_path, ["密钥"]) == []
    assert [h.page.name for h in query.search(index, tmp_path, ["x"])] == []


def test_search_identity_hit_ranks_first(vault, tmp_path):
    index = load(
        vault,
        {
            "正文含词.md": "提到 python 一次",
            "python.md": "无关正文",
        },
    )
    hits = query.search(index, tmp_path, ["python"])
    assert hits[0].page.name == "python"
    assert hits[0].identity_hit
    assert hits[0].snippet == ""


def test_search_identity_alone_hits(vault, tmp_path):
    index = load(vault, {"python.md": "完全没有该词"})
    (hit,) = query.search(index, tmp_path, ["python"])
    assert hit.identity_hit and hit.count == 0

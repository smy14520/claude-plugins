"""frontmatter 三种 tags 写法与边界（Q13）。"""

from wikicore.frontmatter import parse_frontmatter_tags, split_frontmatter


def test_inline_array_tags():
    fm, body = split_frontmatter("---\ntags: [Python, 笔记]\n---\n正文")
    assert parse_frontmatter_tags(fm) == ["Python", "笔记"]
    assert body == "正文"


def test_comma_separated_tags():
    fm, _ = split_frontmatter("---\ntags: a, b\n---\n")
    assert parse_frontmatter_tags(fm) == ["a", "b"]


def test_multiline_list_tags():
    fm, _ = split_frontmatter("---\ntags:\n  - x\n  - y\n---\n")
    assert parse_frontmatter_tags(fm) == ["x", "y"]


def test_quotes_and_hash_prefix_stripped():
    fm, _ = split_frontmatter("---\ntags: [\"#a\", 'b']\n---\n")
    assert parse_frontmatter_tags(fm) == ["a", "b"]


def test_other_keys_ignored():
    fm, _ = split_frontmatter("---\ntitle: X\ntags: [a]\naliases: [b]\n---\n")
    assert parse_frontmatter_tags(fm) == ["a"]


def test_missing_tags_key():
    fm, _ = split_frontmatter("---\ntitle: X\n---\n")
    assert parse_frontmatter_tags(fm) == []


def test_no_frontmatter():
    fm, body = split_frontmatter("无 frontmatter 正文")
    assert fm == []
    assert body == "无 frontmatter 正文"


def test_unclosed_frontmatter_treated_as_body():
    fm, body = split_frontmatter("---\ntags: [a]\n没有闭合线")
    assert fm == []
    assert "tags" in body

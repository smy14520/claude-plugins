"""Frontmatter 语义测试：切分、tags 键提取、畸形处理。"""

from __future__ import annotations

from wiki_cli.parser import frontmatter_tags, parse_page, split_frontmatter


def parse(text: str):
    return parse_page("p", "p.md", 0, 0, text.splitlines())


def test_paired_frontmatter_split():
    fm, body, malformed = split_frontmatter(["---", "tags: [a]", "---", "正文"])
    assert fm == ["tags: [a]"]
    assert body == ["正文"]
    assert not malformed


def test_unclosed_is_malformed_whole_file_is_body():
    page = parse("---\ntags: [a]\n没有闭合，正文里有 [[目标页]]")
    assert page.malformed_frontmatter
    assert [link.target for link in page.links] == ["目标页"]
    assert page.tags == ()  # 未闭合块里的 tags 不算元数据


def test_frontmatter_must_start_at_line_one():
    page = parse("前言\n---\ntags: [a]\n---\n#tag")
    assert not page.malformed_frontmatter
    assert page.tags == ("tag",)  # 第一个 --- 不是元数据块开头


def test_inline_list_tags():
    assert frontmatter_tags(["tags: [python, 笔记,  ml ]"]) == ["python", "笔记", "ml"]


def test_block_list_tags():
    fm = ["tags:", "  - python", "  - ml", "title: x"]
    assert frontmatter_tags(fm) == ["python", "ml"]


def test_bare_scalar_is_single_tag():
    assert frontmatter_tags(["tags: python"]) == ["python"]


def test_malformed_inline_list_skipped():
    assert frontmatter_tags(["tags: [python, ml"]) == []


def test_other_keys_ignored():
    assert frontmatter_tags(["title: 笔记", "aliases: [a]"]) == []


def test_frontmatter_tags_merge_and_dedup_with_body():
    page = parse("---\ntags: [python]\n---\n正文 #python #ml")
    assert page.tags == ("ml", "python")


def test_body_scanned_after_frontmatter():
    page = parse("---\ntitle: #notag\n---\n#real")
    assert page.tags == ("real",)

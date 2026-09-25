"""链接解析语义测试：wikilink 变体、外链排除、代码排除区。"""

from __future__ import annotations

from wiki_cli.parser import parse_page, scan_body


def parse(text: str):
    lines = text.splitlines()
    return parse_page("p", "p.md", 0, 0, lines)


def test_basic_link():
    page = parse("见 [[目标页]]。")
    (link,) = page.links
    assert (link.target, link.raw) == ("目标页", "目标页")
    assert not link.external and not link.embed


def test_md_suffix_stripped():
    page = parse("[[目标页.md]]")
    assert page.links[0].target == "目标页"


def test_alias_and_anchor():
    page = parse("[[目标页#小节|显示文字]]")
    (link,) = page.links
    assert link.target == "目标页"
    assert link.anchor == "小节"
    assert link.alias == "显示文字"


def test_embed_is_link():
    page = parse("![[图片页]]")
    (link,) = page.links
    assert link.embed and link.target == "图片页"


def test_external_links_excluded():
    page = parse("看 [[https://example.com/a]] 和 [[mailto:a@b.c]]")
    assert all(link.external for link in page.links)


def test_empty_and_anchor_only_targets_skipped():
    page = parse("[[]] [[#小节]] [[|别名]]")
    assert page.links == ()


def test_line_numbers_include_frontmatter_offset():
    text = "---\ntags: [x]\n---\n正文 [[目标页]]"
    page = parse(text)
    assert page.links[0].line == 4


def test_fenced_code_excluded():
    text = "前 [[A]]\n```python\n中 [[B]] #tag\n```\n后 [[C]]"
    page = parse(text)
    assert [link.target for link in page.links] == ["A", "C"]
    assert page.tags == ()


def test_tilde_fence_excluded():
    text = "~~~\n[[B]]\n~~~\n[[A]]"
    page = parse(text)
    assert [link.target for link in page.links] == ["A"]


def test_fence_needs_same_char_and_length():
    text = "~~~\n```\n[[A]]\n~~~\n[[B]]"
    page = parse(text)
    # ``` 在 ~~~ 围栏内是内容；~~~ 闭合围栏
    assert [link.target for link in page.links] == ["B"]


def test_inline_code_excluded():
    page = parse("行内 `[[A]] #tag` 之后 [[B]]")
    assert [link.target for link in page.links] == ["B"]
    assert page.tags == ()


def test_unbalanced_inline_code_is_conservative():
    page = parse("前 [[A]] `未闭合 [[B]]")
    assert [link.target for link in page.links] == ["A"]

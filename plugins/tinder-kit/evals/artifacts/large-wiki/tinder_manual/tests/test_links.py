"""[[链接]] 语法：别名、锚点、自锚点、代码排除、去重（Q10/Q11）。"""

from wikicore.links import extract_link_targets


def test_basic_link():
    assert extract_link_targets("见 [[Foo]] 即可") == ["Foo"]


def test_alias_keeps_target_only():
    assert extract_link_targets("[[Foo|显示名]]") == ["Foo"]


def test_anchor_and_block_ref_stripped():
    assert extract_link_targets("[[Foo#标题]] 和 [[Bar#^abc]]") == ["Foo", "Bar"]


def test_self_anchor_skipped():
    assert extract_link_targets("[[#目录]]") == []


def test_whitespace_trimmed():
    assert extract_link_targets("[[ Foo ]]") == ["Foo"]


def test_dedupe_preserving_order():
    assert extract_link_targets("[[B]] [[A]] [[B]]") == ["B", "A"]


def test_fenced_code_excluded():
    assert extract_link_targets("```\n[[Foo]]\n```\n之后 [[Bar]]") == ["Bar"]


def test_tilde_fence_excluded():
    assert extract_link_targets("~~~\n[[Foo]]\n~~~") == []


def test_inline_code_excluded():
    assert extract_link_targets("使用 `[[Foo]]` 演示，再链 [[Bar]]") == ["Bar"]


def test_multiline_fence_swallows_links():
    text = "开头 [[Live]]\n```\n[[Fenced]]\n多行\n[[AlsoFenced]]\n```\n结尾 [[Tail]]"
    assert extract_link_targets(text) == ["Live", "Tail"]

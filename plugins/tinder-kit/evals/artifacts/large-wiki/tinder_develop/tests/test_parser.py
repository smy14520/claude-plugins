"""Tests for the parsing seam: frontmatter, code masking, links, tags, titles."""
from pathlib import Path

from wikicli.model import Page
from wikicli.parser import (
    extract_frontmatter_tags,
    extract_links,
    extract_tags,
    extract_title,
    mask_code,
    split_frontmatter,
)


def masked(text: str, start_line: int = 1):
    return mask_code(text.splitlines(), start_line)


def page(path: str = "p.md") -> Page:
    return Page(path=Path(path))


class TestSplitFrontmatter:
    def test_absent(self):
        fm, body, start = split_frontmatter("hello\nworld\n")
        assert fm == ""
        assert body == "hello\nworld\n"
        assert start == 1

    def test_present(self):
        fm, body, start = split_frontmatter("---\ntags: a, b\n---\nbody\n")
        assert fm == "tags: a, b"
        assert body == "body"
        assert start == 4

    def test_closing_marker_with_trailing_spaces(self):
        fm, body, _ = split_frontmatter("---\ntags: a\n---   \nbody\n")
        assert fm == "tags: a"
        assert body == "body"

    def test_unclosed_is_body(self):
        text = "---\nnot frontmatter, just a rule\n"
        fm, body, start = split_frontmatter(text)
        assert fm == ""
        assert body == text
        assert start == 1

    def test_thematic_break_is_not_frontmatter(self):
        text = "---\nsome intro text\n---\nbody [[A]]\n"
        fm, body, start = split_frontmatter(text)
        assert fm == ""
        assert body == text
        assert start == 1

    def test_double_rule_is_not_frontmatter(self):
        text = "---\n---\nbody\n"
        fm, body, start = split_frontmatter(text)
        assert fm == ""
        assert body == text
        assert start == 1


class TestMaskCode:
    def test_inline_code_is_blanked(self):
        line = masked("see `[[Foo]]` and `#bar` now")[0][1]
        assert "[[" not in line
        assert "#bar" not in line
        assert "see" in line and "now" in line

    def test_fenced_block_is_blanked(self):
        text = "before\n```python\n[[InCode]]\n#incode\n```\nafter [[Real]]\n"
        assert [line for _, line in masked(text)] == [
            "before", "", "", "", "", "after [[Real]]",
        ]

    def test_tilde_fence(self):
        text = "a\n~~~\n[[x]]\n~~~\nb\n"
        assert [line for _, line in masked(text)] == ["a", "", "", "", "b"]

    def test_fence_requires_matching_chars(self):
        # a ~~~ fence does not close a ``` fence
        text = "```\n~~~\n[[x]]\n```\n[[ok]]\n"
        assert [line for _, line in masked(text)] == ["", "", "", "", "[[ok]]"]

    def test_line_numbers_offset(self):
        out = mask_code(["a", "```", "[[x]]", "```"], start_line=10)
        assert [n for n, _ in out] == [10, 11, 12, 13]

    def test_unclosed_fence_masks_rest(self):
        out = masked("```open\nhidden [[x]]\n")
        assert out[0][1] == ""
        assert out[1][1] == ""

    def test_double_backtick_span_blanked(self):
        line = masked("x ``[[Foo]]`` y")[0][1]
        assert "[[" not in line

    def test_double_span_containing_single(self):
        line = masked("`` `x` ``")[0][1]
        assert "`" not in line
        assert "x" not in line


class TestExtractTitle:
    def test_first_h1(self):
        assert extract_title(masked("# Title\nbody")) == "Title"

    def test_skips_fenced(self):
        text = "```\n# Not A Title\n```\n# Real\n"
        assert extract_title(masked(text)) == "Real"

    def test_none_when_absent(self):
        assert extract_title(masked("no heading")) is None

    def test_chinese(self):
        assert extract_title(masked("# 知识库结构")) == "知识库结构"

    def test_tag_line_is_not_title(self):
        assert extract_title(masked("#tag not heading")) is None


class TestExtractLinks:
    def test_simple(self):
        links = extract_links(page(), masked("see [[Foo]] here"))
        assert len(links) == 1
        assert links[0].raw == "Foo"
        assert links[0].target == "Foo"
        assert links[0].line == 1
        assert links[0].display is None

    def test_alias_and_whitespace(self):
        links = extract_links(page(), masked("[[ Foo Bar | 显示文字 ]]"))
        assert links[0].raw == "Foo Bar"
        assert links[0].target == "Foo Bar"
        assert links[0].display == "显示文字"

    def test_md_suffix_stripped_in_target(self):
        links = extract_links(page(), masked("[[Foo.md]]"))
        assert links[0].raw == "Foo.md"
        assert links[0].target == "Foo"

    def test_multiple_per_line(self):
        assert len(extract_links(page(), masked("[[A]] x [[B]]"))) == 2

    def test_none_inside_inline_code(self):
        assert extract_links(page(), masked("`[[A]]`")) == []

    def test_embed_ignored(self):
        # ![[X]] embeds are out of scope: neither links nor dead links.
        assert extract_links(page(), masked("![[Image]]")) == []

    def test_anchor_stripped_from_target(self):
        links = extract_links(page(), masked("[[Foo#Bar]]"))
        assert links[0].raw == "Foo#Bar"
        assert links[0].target == "Foo"

    def test_anchor_with_alias_and_md(self):
        links = extract_links(page(), masked("[[Foo.md#Sec|显示]]"))
        assert links[0].target == "Foo"
        assert links[0].display == "显示"

    def test_same_page_anchor_not_a_link(self):
        assert extract_links(page(), masked("[[#目录]]")) == []

    def test_line_numbers(self):
        links = extract_links(page(), masked("l1\nl2 [[B]]"))
        assert links[0].line == 2


class TestExtractTags:
    def test_simple_and_line(self):
        assert extract_tags(masked("x #work y")) == [(1, "work")]

    def test_heading_not_tag(self):
        assert extract_tags(masked("# Heading")) == []
        assert extract_tags(masked("## Sub")) == []

    def test_chinese(self):
        assert extract_tags(masked("#工作 记录")) == [(1, "工作")]

    def test_nested(self):
        assert extract_tags(masked("#a/b/c")) == [(1, "a/b/c")]

    def test_hyphen_underscore_digits(self):
        assert extract_tags(masked("#a-b_c1")) == [(1, "a-b_c1")]

    def test_trailing_punctuation_excluded(self):
        assert extract_tags(masked("#tag, and #b.")) == [(1, "tag"), (1, "b")]

    def test_trailing_slash_stripped(self):
        assert extract_tags(masked("#a/")) == [(1, "a")]

    def test_midword_blocked(self):
        assert extract_tags(masked("foo#bar")) == []

    def test_after_entity_or_slash_blocked(self):
        assert extract_tags(masked("&#8212; http://x/#anchor")) == []

    def test_leading_slash_rejected(self):
        assert extract_tags(masked("#/nope")) == []

    def test_start_of_line_and_after_punct(self):
        assert extract_tags(masked("#top\n(:#punct)")) == [(1, "top"), (2, "punct")]


class TestFrontmatterTags:
    def test_inline_bracketed(self):
        assert extract_frontmatter_tags("tags: [a, b]") == ["a", "b"]

    def test_inline_plain(self):
        assert extract_frontmatter_tags("tags: a, b") == ["a", "b"]

    def test_block_list(self):
        fm = "title: x\ntags:\n  - alpha\n  - beta\ncreated: 2026-01-01"
        assert extract_frontmatter_tags(fm) == ["alpha", "beta"]

    def test_quoted(self):
        assert extract_frontmatter_tags('tags: ["a b", c]') == ["a b", "c"]

    def test_key_case_insensitive_and_other_keys_ignored(self):
        assert extract_frontmatter_tags("Tags: work") == ["work"]
        assert extract_frontmatter_tags("tag: work\ntags: ") == []

    def test_block_ends_at_next_key(self):
        fm = "tags:\n  - a\ncreated: x\n  - b"
        assert extract_frontmatter_tags(fm) == ["a"]

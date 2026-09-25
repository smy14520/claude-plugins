"""正文 #tag 语法测试：五个误报源与拍定的字符规则。"""

from __future__ import annotations

import pytest

from wiki_cli.parser import parse_page


def tags_of(text: str) -> list[str]:
    return list(parse_page("p", "p.md", 0, 0, text.splitlines()).tags)


def test_csharp_not_a_tag():
    assert tags_of("我在用 C# 写代码") == []


def test_url_anchor_not_a_tag():
    assert tags_of("详见 x.com/#anchor") == []


def test_atx_heading_not_a_tag():
    assert tags_of("# 这是一个标题") == []
    assert tags_of("## 二级标题") == []


def test_after_cjk_punctuation_is_tag():
    assert tags_of("（#python）") == ["python"]


def test_after_underscore_is_tag():
    # 下划线属「非字母数字」，按拍板语义触发
    assert tags_of("_#worker") == ["worker"]


def test_mid_word_hash_not_a_tag():
    assert tags_of("foo#bar") == []


def test_digit_start_not_a_tag():
    assert tags_of("#1 issue") == []


def test_cjk_tag():
    assert tags_of("标签 #机器学习 结束") == ["机器学习"]


def test_allowed_name_chars():
    assert tags_of("#a-b_c/d") == ["a-b_c/d"]


def test_slash_is_literal_no_hierarchy_expansion():
    assert tags_of("#ml/rl 加 #ml") == ["ml", "ml/rl"]


def test_trailing_punctuation_stops_tag():
    assert tags_of("#python, #ml。") == ["ml", "python"]


def test_empty_hierarchy_rejected():
    assert tags_of("#a/ 与 #a//b") == []


@pytest.mark.parametrize("fence", ["```", "~~~"])
def test_fence_excluded(fence):
    assert tags_of(f"{fence}\n#注释\n{fence}") == []

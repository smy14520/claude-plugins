"""Seam 1：scan_page 词法扫描的公共行为。"""

from wikicore.parser import scan_page


def test_wikilinks_basic_alias_and_line_numbers():
    text = "见 [[首页]] 与 [[深度模块|deep module]]。\n第二行 [[B]]。"
    scan = scan_page(text)

    assert [(link.target, link.line) for link in scan.links] == [
        ("首页", 1),
        ("深度模块", 1),
        ("B", 2),
    ]
    assert scan.tags == []


def test_tags_chinese_ascii_and_hierarchical():
    text = "#重要 #lang/python #知识库\n结尾 #ok_1"
    scan = scan_page(text)

    assert scan.tags == ["重要", "lang/python", "知识库", "ok_1"]


def test_tags_dedup_within_page_and_trailing_punct():
    text = "#重要 #重要\n见 #tag. 与 #a/b."
    scan = scan_page(text)

    assert scan.tags == ["重要", "tag", "a/b"]


def test_exclusions():
    text = (
        "# 这是标题\n"
        "## 标题带 #行内标签\n"
        "```python\n"
        "#fence_tag\n"
        "[[FenceLink]]\n"
        "```\n"
        "正文 [[真链接]] 与 `[[CodeLink]]` 与 `#code_tag` 不算\n"
        "跳转 http://example.com/page#anchor 结束 #真标签\n"
        "##双井号不算\n"
    )
    scan = scan_page(text)

    assert scan.tags == ["行内标签", "真标签"]
    assert [link.target for link in scan.links] == ["真链接"]

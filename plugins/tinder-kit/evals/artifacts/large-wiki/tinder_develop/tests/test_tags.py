"""`tags` 命令的 CLI 命令面行为：提取规则 + 聚合（ticket 04）。"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from conftest import run_cli, vault_path


def test_tags_aggregates_with_extraction_rules_and_sort() -> None:
    """聚合输出全量精确断言（checklist 1、2、5）：

    - CJK 标签（#机器学习）与 CJK 紧邻 #（看看#rust）有效；
    - URL 中 #（x#/a、py#section）、纯数字 #1/#2024、##小节标题不误报；
    - 标题行（`# ` 开头）不算；
    - 页数降序、同数按字典序（rust < 机器学习：ASCII 先于 CJK）。
    """
    code, out, err = run_cli(["--vault", str(vault_path("tags-valid")), "tags"])

    assert code == 0
    assert out == (
        "#python  2 页\n"
        "#rust  1 页\n"
        "#机器学习  1 页\n"
    )


def test_tags_ignore_hash_inside_link_syntax() -> None:
    """`[[...]]` 链接语法整体剥离后再提标签（review S2，spec L43 全域读法）：

    `[[#小节]]` 页内锚与别名部分的 `#`（`[[python|别名#nope]]`）既非链接
    也非标签——完全不计数；链接外的真实标签照常提取。
    """
    code, out, err = run_cli(["--vault", str(vault_path("tags-inpage-anchor")), "tags"])

    assert code == 0
    assert out == "#real-tag  1 页\n"


def test_tags_url_slash_hash_is_immune_and_nested_tag_still_works() -> None:
    """URL `#` 免疫补全（review S3）：`#` 前紧邻 `/` 时不是标签——
    `https://example.com/#frag-abc` 里的 `#frag-abc` 不产标签；
    `#` 前是别的字符时嵌套 `a/b` 标签照常提取，不得回归。
    """
    code, out, err = run_cli(["--vault", str(vault_path("tags-url-hash")), "tags"])

    assert code == 0
    assert out == "#a/b  1 页\n"


def test_tags_exempt_inside_fenced_and_inline_code() -> None:
    """围栏代码块与行内代码内的 #tag 一律豁免（checklist 2）。"""
    code, out, err = run_cli(["--vault", str(vault_path("tags-code")), "tags"])

    assert code == 0
    assert out == "#real  1 页\n"


def test_tags_nested_paths_aggregate_by_full_path() -> None:
    """嵌套标签按完整路径聚合；聚合行只计精确命中该路径的页面（checklist 3）。"""
    code, out, err = run_cli(["--vault", str(vault_path("tags-nested")), "tags"])

    assert code == 0
    assert out == (
        "#concepts  2 页\n"
        "#concepts/gc  2 页\n"
        "#concepts/os  1 页\n"
        "#其他  1 页\n"
    )


def test_tags_query_parent_includes_all_descendants() -> None:
    """父标签查询返回含全部子孙标签的页面；同页父子不重复（checklist 3）。"""
    code, out, err = run_cli(["--vault", str(vault_path("tags-nested")), "tags", "concepts"])

    assert code == 0
    assert out == "both.md\nconcepts.md\ngc.md\nos.md\n"


def test_tags_query_child_tag_returns_only_that_subtree() -> None:
    code, out, err = run_cli(["--vault", str(vault_path("tags-nested")), "tags", "concepts/gc"])

    assert code == 0
    assert out == "both.md\ngc.md\n"


def test_tags_query_accepts_optional_hash_prefix() -> None:
    """`#` 前缀可选（checklist 5）。"""
    code, out, err = run_cli(["--vault", str(vault_path("tags-nested")), "tags", "#concepts"])

    assert code == 0
    assert out == "both.md\nconcepts.md\ngc.md\nos.md\n"


def test_tags_query_unknown_tag_outputs_empty_and_exits_zero() -> None:
    code, out, err = run_cli(["--vault", str(vault_path("tags-nested")), "tags", "no-such-tag"])

    assert code == 0
    assert out == ""


def test_tags_sort_page_count_desc_then_lexicographic() -> None:
    """页数降序、同数按字典序的完整契约（checklist 5）：x:3、y:2、z:2。"""
    code, out, err = run_cli(["--vault", str(vault_path("tags-sort")), "tags"])

    assert code == 0
    assert out == (
        "#x  3 页\n"
        "#y  2 页\n"
        "#z  2 页\n"
    )


def test_tags_counts_pages_not_occurrences() -> None:
    """单页重复同一标签只计 1 页（checklist 5 的页数语义）。"""
    code, out, err = run_cli(["--vault", str(vault_path("tags-dup")), "tags"])

    assert code == 0
    assert out == "#dup  1 页\n"


def test_tags_overview_empty_when_vault_has_no_tags() -> None:
    code, out, err = run_cli(["--vault", str(vault_path("tags-empty")), "tags"])

    assert code == 0
    assert out == ""

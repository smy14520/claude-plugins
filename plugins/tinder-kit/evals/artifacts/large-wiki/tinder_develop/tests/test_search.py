"""`search` 命令的 CLI 命令面行为：多关键词 AND 全文检索（ticket 05）。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from conftest import run_cli, vault_path


def test_search_without_keywords_is_usage_error() -> None:
    """无关键词 → 用法提示 + exit 2（checklist 5）。"""
    code, out, err = run_cli(["--vault", str(vault_path("links-basic")), "search"])

    assert code == 2
    assert out == ""
    # 子命令自身的 usage（而非主解析器的 invalid choice）——证明 search 已注册、
    # 是缺关键词被拒而非命令不存在
    assert "usage: wiki-cli search" in err


def test_search_basic_content_match_is_case_insensitive() -> None:
    """单关键词子串命中：PYTHON/Python 大小写不敏感；头行 + 页行 + 命中行缩进块。

    页面名（notes）与 H1（随手记）不含关键词——纯内容命中，频次 = 3（checklist 2）。
    """
    code, out, err = run_cli(["--vault", str(vault_path("search-basic")), "search", "python"])

    assert code == 0
    assert out == (
        "1 个页面命中 · 关键词: python\n"
        "1. notes.md  内容 ×3\n"
        "    3: Python 是解释型语言。\n"
        "    4: 写 PYTHON 脚本很方便。\n"
        "    5: 我每天写 Python。\n"
    )


def test_search_cjk_substring_match() -> None:
    """CJK 无分词子串命中（checklist 2）：`机器学习` 整词包含即中，无需空格切词。"""
    code, out, err = run_cli(["--vault", str(vault_path("search-basic")), "search", "机器学习"])

    assert code == 0
    assert out == (
        "1 个页面命中 · 关键词: 机器学习\n"
        "1. ml.md  内容 ×2\n"
        "    3: 机器学习改变世界。\n"
        "    4: 聊聊 机器学习 的应用。\n"
    )


def test_search_multiple_keywords_requires_all() -> None:
    """多关键词 AND（checklist 1）：只返回同时含全部关键词的页面，单词页被排除。"""
    code, out, err = run_cli(
        ["--vault", str(vault_path("search-and")), "search", "python", "rust"]
    )

    assert code == 0
    assert out == (
        "1 个页面命中 · 关键词: python rust\n"
        "1. both.md  内容 ×4\n"
        "    1: 双手都沾满了 python 和 rust 的项目。\n"
        "    2: python 与 rust 我都写。\n"
    )


def test_search_title_hit_ranks_before_content_with_freq_then_path() -> None:
    """排序契约（checklist 3）：标题命中 > 内容频次 > 路径字典序。

    - 三个标题命中面各占一页：H1（guide）、页面名（python-tips）、
      frontmatter title（py）——都排在纯内容命中之前；
    - 标题组内频次并列（guide/python-tips 各 3）时按路径字典序；
    - 内容组内 bb/zz 并列 2 次按路径，aa 1 次垫底；
    - py.md 行号为正文相对行号（frontmatter 剥离后，与 links/backlinks 一致）。
    """
    code, out, err = run_cli(["--vault", str(vault_path("search-title")), "search", "python"])

    assert code == 0
    assert out == (
        "6 个页面命中 · 关键词: python\n"
        "1. guide.md  标题命中\n"
        "    1: # Python 入门\n"
        "    3: 这里讲 python 的基础，python 也简单。\n"
        "2. python-tips.md  标题命中\n"
        "    3: python 出现两次：python 与 python。\n"
        "3. py.md  标题命中\n"
        "    2: 正文提到 python 一次。\n"
        "4. bb.md  内容 ×2\n"
        "    1: python 与 python。\n"
        "5. zz.md  内容 ×2\n"
        "    1: 随便写点 python 内容。\n"
        "    3: 再来一个 python。\n"
        "6. aa.md  内容 ×1\n"
        "    1: python 一次。\n"
    )


def test_search_skips_code_regions_and_preserves_line_numbers() -> None:
    """代码区豁免 + 行号不漂移：围栏开栏行的 ```python、块内容、行内代码都不命中；

    块后命中行报 5 而非 3——行号建在 strip_code 保留的行结构上（checklist 4）。
    """
    code, out, err = run_cli(["--vault", str(vault_path("search-code")), "search", "python"])

    assert code == 0
    assert out == (
        "1 个页面命中 · 关键词: python\n"
        "1. example.md  内容 ×2\n"
        "    1: 真实命中 python 在这里。\n"
        "    5: 块后再次出现 python。\n"
    )


def test_search_hit_lines_must_include_lines_with_all_keywords() -> None:
    """命中行选择（review S1，spec checklist：命中行含全部关键词所在行）：

    含全部关键词的行优先且必须入选——即使排在只含单词的行之后；
    剩余名额由含任一关键词的行按行号补足。前 3 行只含 alpha、
    第 4 行才同时含 alpha 与 beta，输出必须含第 4 行。
    """
    code, out, err = run_cli(
        ["--vault", str(vault_path("search-all-keywords")), "search", "alpha", "beta"]
    )

    assert code == 0
    assert out == (
        "1 个页面命中 · 关键词: alpha beta\n"
        "1. page.md  内容 ×5\n"
        "    1: 只含 alpha 一。\n"
        "    2: 只含 alpha 二。\n"
        "    4: alpha 加 beta 同行。\n"
    )


def test_search_max_three_hit_lines_with_dedup_and_truncation() -> None:
    """每页至多 3 条命中行（checklist 4）：4 条命中只展示前 3；

    第 3 行同时含 alpha 与 beta 只出现一次（去重）；超长行截断为 79 字符 + …
    （前缀 `alpha 后面跟着超长文本 ` 共 15 字符，保留 64 个 y）。
    """
    code, out, err = run_cli(
        ["--vault", str(vault_path("search-max3")), "search", "alpha", "beta"]
    )

    assert code == 0
    assert out == (
        "1 个页面命中 · 关键词: alpha beta\n"
        "1. cap.md  内容 ×5\n"
        "    1: " + "alpha 后面跟着超长文本 " + "y" * 64 + "…\n"
        "    2: alpha 二。\n"
        "    3: alpha beta 同行。\n"
    )


def test_search_zero_hits_outputs_explicit_zero_and_exits_zero() -> None:
    """有关键词但零命中（checklist 5）：明确的零结果输出 + exit 0。"""
    code, out, err = run_cli(["--vault", str(vault_path("search-empty")), "search", "python"])

    assert code == 0
    assert out == "0 个页面命中 · 关键词: python\n"


def test_search_json_document_shape() -> None:
    """--json 单对象文档（checklist 6）：字段名稳定承诺——command/keywords/page_count/matches。"""
    code, out, err = run_cli(["--vault", str(vault_path("search-code")), "--json", "search", "python"])

    assert code == 0
    doc = json.loads(out)
    assert doc == {
        "command": "search",
        "keywords": ["python"],
        "page_count": 1,
        "matches": [
            {
                "path": "example.md",
                "name": "example",
                "title_hit": False,
                "frequency": 2,
                "lines": [
                    {"line": 1, "text": "真实命中 python 在这里。"},
                    {"line": 5, "text": "块后再次出现 python。"},
                ],
            }
        ],
    }


def test_search_json_orders_title_hits_first() -> None:
    """--json 与人读同序：title_hit 三连 true 在前，内容命中 false 在后。"""
    code, out, err = run_cli(["--vault", str(vault_path("search-title")), "--json", "search", "python"])

    assert code == 0
    doc = json.loads(out)
    assert doc["command"] == "search"
    assert doc["page_count"] == 6
    assert [m["title_hit"] for m in doc["matches"]] == [True, True, True, False, False, False]
    assert [m["path"] for m in doc["matches"]] == [
        "guide.md",
        "python-tips.md",
        "py.md",
        "bb.md",
        "zz.md",
        "aa.md",
    ]
    assert [m["frequency"] for m in doc["matches"]] == [3, 3, 1, 2, 2, 1]


def test_search_json_zero_hits() -> None:
    code, out, err = run_cli(["--vault", str(vault_path("search-empty")), "--json", "search", "python"])

    assert code == 0
    assert json.loads(out) == {
        "command": "search",
        "keywords": ["python"],
        "page_count": 0,
        "matches": [],
    }


def test_search_empty_or_blank_keyword_is_usage_error() -> None:
    """空串/纯空白关键词也是空关键词（checklist 5）：用法提示 + exit 2，

    不允许沦为"到处命中的空子串"。
    """
    for kw in ("", "   "):
        code, out, err = run_cli(["--vault", str(vault_path("search-basic")), "search", kw])

        assert code == 2
        assert out == ""
        assert "wiki-cli: 错误" in err

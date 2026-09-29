"""中文页面名（CJK 文件名）作为一等公民的 CLI 命令面行为。

覆盖：CJK stem 精确解析、CJK 子目录路径、CJK 别名反向引用、CJK 标签
查询、CJK 页面名标题命中检索、CJK 孤岛判定。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from conftest import run_cli, vault_path


def test_links_resolves_cjk_stem_and_cjk_subdirectory_path() -> None:
    """[[中文页面]] 与 [[子目录/中文页面]] 均按页面名精确解析。"""
    code, out, err = run_cli(
        ["--vault", str(vault_path("cjk-names")), "links", "机器学习"]
    )

    assert code == 0
    assert out == (
        "机器学习.md (机器学习)\n"
        "→ notes/索引.md  [[notes/索引]]\n"
        "→ 深度学习.md  [[深度学习]]\n"
    )


def test_backlinks_lists_cjk_source_with_cjk_alias_and_line_number() -> None:
    """反向引用：CJK 引用方路径、行号与 CJK 别名原文写法齐备。"""
    code, out, err = run_cli(
        ["--vault", str(vault_path("cjk-names")), "backlinks", "机器学习"]
    )

    assert code == 0
    assert out == (
        "机器学习.md (机器学习) ← 1 条反向引用\n"
        "notes/索引.md:3  [[机器学习|ML 入门]]\n"
    )


def test_tags_query_returns_cjk_named_pages() -> None:
    """标签 → 页面查询：CJK 页面路径如实列出（页数序）。"""
    code, out, err = run_cli(
        ["--vault", str(vault_path("cjk-names")), "tags", "算法"]
    )

    assert code == 0
    assert out == "机器学习.md\n深度学习.md\n草稿.md\n"


def test_search_ranks_cjk_page_name_as_title_hit() -> None:
    """CJK 文件名（页面名）包含关键词 → 标题命中，排在内容命中之前。"""
    code, out, err = run_cli(
        ["--vault", str(vault_path("cjk-names")), "search", "机器学习"]
    )

    assert code == 0
    assert out.startswith("2 个页面命中 · 关键词: 机器学习\n")
    assert "1. 机器学习.md  标题命中" in out
    assert "2. notes/索引.md  内容 ×1" in out


def test_doctor_reports_cjk_orphan_with_findings_exit_code() -> None:
    """孤岛判定对 CJK 页面名一视同仁：草稿.md 零反向引用 → 孤岛 + exit 1。"""
    code, out, err = run_cli(
        ["--vault", str(vault_path("cjk-names")), "doctor"]
    )

    assert code == 1
    assert out == (
        "体检: 4 页面 · 3 条链接 · 1 个标签\n"
        "⚠ 孤岛页面\n"
        "草稿.md\n"
    )

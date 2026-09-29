"""`doctor` 命令的 CLI 命令面行为：三类发现 + 统计行 + 三态退出码。"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from conftest import run_cli, vault_path


def test_doctor_healthy_vault_prints_stats_line_only_and_exits_0() -> None:
    """无任何发现：只输出统计行 `体检: N 页面 · M 条链接 · K 个标签`，exit 0。"""
    code, out, err = run_cli(
        ["--vault", str(vault_path("doctor-healthy")), "doctor"]
    )

    assert code == 0
    assert out == "体检: 2 页面 · 2 条链接 · 2 个标签\n"
    assert err == ""


def test_doctor_self_link_does_not_rescue_orphan() -> None:
    """自链接算正向链接（计入 M）但不构成反向引用：只自链的页面仍是孤岛。"""
    code, out, err = run_cli(["--vault", str(vault_path("links-self")), "doctor"])

    assert code == 1
    assert out == (
        "体检: 1 页面 · 1 条链接 · 0 个标签\n"
        "⚠ 孤岛页面\n"
        "python.md\n"
    )


def test_doctor_inpage_anchor_is_invisible_to_report() -> None:
    """`[[#小节]]` 全域完全隐形：不计入 M、不报死链、不影响孤岛判定，
    也不产标签（spec L43 整体跳过、完全不计数，review S2）——K=0。
    """
    code, out, err = run_cli(["--vault", str(vault_path("links-inpage")), "doctor"])

    assert code == 1
    assert out == (
        "体检: 1 页面 · 0 条链接 · 0 个标签\n"
        "⚠ 孤岛页面\n"
        "home.md\n"
    )


def test_doctor_reports_ambiguous_links_with_source_and_all_candidates() -> None:
    """歧义块：`出处:行号  ⚠ 歧义: [[原文]] → 全部候选`（沿用 links 歧义词汇）。"""
    code, out, err = run_cli(
        ["--vault", str(vault_path("backlinks-ambiguous")), "doctor"]
    )

    assert code == 1
    assert out == (
        "体检: 3 页面 · 2 条链接 · 0 个标签\n"
        "⚠ 孤岛页面\n"
        "home.md\n"
        "歧义链接\n"
        "home.md:1  ⚠ 歧义: [[notes]] → a/notes.md, b/notes.md\n"
    )


def test_doctor_orders_blocks_dead_then_orphans_then_ambiguous() -> None:
    """三类发现同库共存：块序按 render 契约 死链 → 孤岛页面 → 歧义链接。

    候选页面 a/notes、b/notes 因歧义链接各得一条反向引用，不是孤岛。
    """
    code, out, err = run_cli(["--vault", str(vault_path("doctor-mixed")), "doctor"])

    assert code == 1
    assert out == (
        "体检: 3 页面 · 2 条链接 · 0 个标签\n"
        "✗ 死链\n"
        "home.md:1  [[ghost]]\n"
        "⚠ 孤岛页面\n"
        "home.md\n"
        "歧义链接\n"
        "home.md:1  ⚠ 歧义: [[notes]] → a/notes.md, b/notes.md\n"
    )


def test_doctor_empty_vault_zero_stats_zero_findings_exits_0() -> None:
    """空 vault：`体检: 0 页面 · 0 条链接 · 0 个标签`、零发现、exit 0。"""
    code, out, err = run_cli(["--vault", str(vault_path("doctor-empty")), "doctor"])

    assert code == 0
    assert out == "体检: 0 页面 · 0 条链接 · 0 个标签\n"
    assert err == ""


def test_doctor_extra_argument_exits_2_with_usage_hint() -> None:
    """doctor 不收位置参数：多余参数 → usage 提示 + exit 2。"""
    code, out, err = run_cli(["doctor", "something"])

    assert code == 2
    assert "usage:" in err
    assert out == ""


def test_doctor_missing_vault_exits_2() -> None:
    """--vault 路径不存在：清晰提示 + exit 2（挂 pre-commit 的用法错误面）。"""
    code, out, err = run_cli(["--vault", "/nonexistent/vault/path", "doctor"])

    assert code == 2
    assert "vault 不存在" in err
    assert out == ""


def test_doctor_stats_line_counts_tags_aggregation() -> None:
    """K = 去重标签数，与 tags 聚合一致：tags-valid 三标签 → 3 个标签。"""
    code, out, err = run_cli(["--vault", str(vault_path("tags-valid")), "doctor"])

    assert code == 1  # 两页均无入向 → 孤岛
    assert out == (
        "体检: 2 页面 · 0 条链接 · 3 个标签\n"
        "⚠ 孤岛页面\n"
        "notes.md\n"
        "python.md\n"
    )


def test_doctor_stats_count_frontmatter_tags_and_body_links_only() -> None:
    """frontmatter `tags:` 并入 K；frontmatter title 里的 [[..]] 不计入 M。"""
    code, out, err = run_cli(
        ["--vault", str(vault_path("tags-frontmatter")), "doctor"]
    )

    assert code == 1  # 仅 python.md 有入向（meta.md 正文 [[python]]）
    assert out == (
        "体检: 4 页面 · 1 条链接 · 4 个标签\n"
        "⚠ 孤岛页面\n"
        "bare.md\n"
        "broken.md\n"
        "meta.md\n"
    )


def test_doctor_agrees_with_links_and_backlinks_on_same_facts() -> None:
    """同一事实两种视角不打架：死链条目与 links 一致、孤岛与 backlinks 零入向一致。"""
    base = ["--vault", str(vault_path("backlinks-basic"))]
    _, doctor_out, _ = run_cli([*base, "doctor"])
    _, home_links, _ = run_cli([*base, "links", "home"])
    _, lonely_back, _ = run_cli([*base, "backlinks", "lonely"])
    _, python_back, _ = run_cli([*base, "backlinks", "python"])

    # 死链：links 报的未解析原文 ↔ doctor 同一出处:行号 + 原文
    assert "✗ 未解析: [[ghost]]" in home_links
    assert "home.md:7  [[ghost]]" in doctor_out
    # 孤岛：backlinks 计 0 条的页面进孤岛块，有入向的（python 2 条）不出现
    assert "← 0 条反向引用" in lonely_back
    assert "← 2 条反向引用" in python_back
    assert "⚠ 孤岛页面\nhome.md\nlonely.md\n" in doctor_out
    assert "python.md" not in doctor_out


def test_doctor_ambiguous_block_agrees_with_links_view() -> None:
    """歧义块与 links 视角同事实：同一原文、同一候选集，仅多出处。"""
    base = ["--vault", str(vault_path("backlinks-ambiguous"))]
    _, doctor_out, _ = run_cli([*base, "doctor"])
    _, home_links, _ = run_cli([*base, "links", "home"])

    assert "⚠ 歧义: [[notes]] → a/notes.md, b/notes.md" in home_links
    assert "home.md:1  ⚠ 歧义: [[notes]] → a/notes.md, b/notes.md" in doctor_out


def test_doctor_reports_dead_links_with_source_line_and_raw() -> None:
    """死链接出现处逐条列出：`出处:行号  [[原文]]`；有发现即 exit 1（checklist 4）。"""
    code, out, err = run_cli(["--vault", str(vault_path("backlinks-basic")), "doctor"])

    assert code == 1
    assert out == (
        "体检: 3 页面 · 3 条链接 · 0 个标签\n"
        "✗ 死链\n"
        "home.md:7  [[ghost]]\n"
        "⚠ 孤岛页面\n"
        "home.md\n"
        "lonely.md\n"
    )
    assert err == ""

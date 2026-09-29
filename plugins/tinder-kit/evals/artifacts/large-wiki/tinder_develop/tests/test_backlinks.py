"""`backlinks` 命令的 CLI 命令面行为。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from conftest import run_cli, vault_path


def test_backlinks_shows_header_and_inbound_entries() -> None:
    """头行 `路径 (页面名) ← N 条反向引用`，逐条 `引用方路径:行号  [[原文]]`（checklist 1）。"""
    code, out, err = run_cli(
        ["--vault", str(vault_path("backlinks-basic")), "backlinks", "python"]
    )

    assert code == 0
    assert out == (
        "python.md (python) ← 2 条反向引用\n"
        "home.md:3  [[python]]\n"
        "home.md:5  [[python|Py 学习笔记]]\n"
    )


def test_backlinks_lists_repeated_references_from_same_source_individually() -> None:
    """同一引用方多次引用逐条列出、不合并；死链不成入向（checklist 2）。"""
    code, out, err = run_cli(
        ["--vault", str(vault_path("backlinks-basic")), "backlinks", "python"]
    )

    assert code == 0
    assert out.count("home.md:") == 2  # 不合并为一条
    assert "[[ghost]]" not in out  # 死链无候选页面，不进任何 backlinks


def test_backlinks_ambiguous_link_recorded_for_every_candidate() -> None:
    """歧义目标的反向引用记入每个候选页面；路径写法可消歧查询（checklist 3）。"""
    code_a, out_a, err_a = run_cli(
        ["--vault", str(vault_path("backlinks-ambiguous")), "backlinks", "a/notes"]
    )
    code_b, out_b, err_b = run_cli(
        ["--vault", str(vault_path("backlinks-ambiguous")), "backlinks", "b/notes"]
    )

    assert code_a == 0
    assert out_a == (
        "a/notes.md (notes) ← 2 条反向引用\n"
        "home.md:1  [[notes]]\n"
        "home.md:1  [[a/notes]]\n"
    )
    assert code_b == 0
    assert out_b == (
        "b/notes.md (notes) ← 1 条反向引用\n"
        "home.md:1  [[notes]]\n"
    )


def test_backlinks_excludes_self_links() -> None:
    """自链接不算反向引用，不出现在 backlinks 结果中（checklist 4）。"""
    code, out, err = run_cli(
        ["--vault", str(vault_path("backlinks-self")), "backlinks", "python"]
    )

    assert code == 0
    assert out == (
        "python.md (python) ← 1 条反向引用\n"
        "home.md:1  [[python]]\n"
    )


def test_backlinks_reports_zero_inbound_references() -> None:
    """无入向页面：头行计数为 0，退出码 0（孤岛判定的入向事实）。"""
    code, out, err = run_cli(
        ["--vault", str(vault_path("backlinks-basic")), "backlinks", "lonely"]
    )

    assert code == 0
    assert out == "lonely.md (lonely) ← 0 条反向引用\n"


def test_backlinks_json_emits_single_stable_document() -> None:
    """--json：单对象、字段名稳定（command/page/backlinks[{source,line,raw}]）。"""
    code, out, err = run_cli(
        ["--vault", str(vault_path("backlinks-basic")), "--json", "backlinks", "python"]
    )

    assert code == 0
    doc = json.loads(out)
    assert doc == {
        "command": "backlinks",
        "page": {"path": "python.md", "name": "python"},
        "backlinks": [
            {"source": "home.md", "line": 3, "raw": "python"},
            {"source": "home.md", "line": 5, "raw": "python|Py 学习笔记"},
        ],
    }


def test_backlinks_unknown_page_exits_2_with_clear_message() -> None:
    """查询目标为死链（无对应页面）：清晰提示 + exit 2。"""
    code, out, err = run_cli(
        ["--vault", str(vault_path("backlinks-basic")), "backlinks", "ghost"]
    )

    assert code == 2
    assert "ghost" in err
    assert out == ""


def test_backlinks_ambiguous_query_exits_2_with_disambiguation_hint() -> None:
    """裸 stem 命中多个页面：提示用路径写法消歧 + exit 2。"""
    code, out, err = run_cli(
        ["--vault", str(vault_path("backlinks-ambiguous")), "backlinks", "notes"]
    )

    assert code == 2
    assert "notes" in err
    assert "a/notes.md" in err and "b/notes.md" in err
    assert out == ""


def test_backlinks_without_page_argument_exits_2() -> None:
    code, out, err = run_cli(["backlinks"])

    assert code == 2
    assert "usage:" in err


def test_backlinks_ignores_links_inside_code_blocks() -> None:
    """围栏/行内代码里的 [[..]] 不产生反向引用（strip_code 行结构不变）。"""
    code, out, err = run_cli(
        ["--vault", str(vault_path("links-code")), "--json", "backlinks", "python"]
    )

    assert code == 0
    doc = json.loads(out)
    assert doc["backlinks"] == [
        {"source": "notes/example.md", "line": 3, "raw": "python"},
        {"source": "notes/example.md", "line": 12, "raw": "python|真别名"},
    ]


def test_backlinks_ambiguous_self_reference_counts_for_other_candidates_only() -> None:
    """歧义自指逐对判定：a/notes 的 [[notes]] 不记入自己，但记入 b/notes。"""
    code_a, out_a, err_a = run_cli(
        ["--vault", str(vault_path("backlinks-self-ambiguous")), "backlinks", "a/notes"]
    )
    code_b, out_b, err_b = run_cli(
        ["--vault", str(vault_path("backlinks-self-ambiguous")), "backlinks", "b/notes"]
    )

    assert code_a == 0
    assert out_a == "a/notes.md (notes) ← 0 条反向引用\n"
    assert code_b == 0
    assert out_b == (
        "b/notes.md (notes) ← 1 条反向引用\n"
        "a/notes.md:1  [[notes]]\n"
    )

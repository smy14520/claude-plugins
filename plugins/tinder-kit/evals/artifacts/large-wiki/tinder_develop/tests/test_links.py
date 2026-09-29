"""`links` 命令的 CLI 命令面行为。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from conftest import run_cli, vault_path


def test_links_lists_outgoing_links_in_human_format() -> None:
    code, out, err = run_cli(["--vault", str(vault_path("links-basic")), "links", "home"])

    assert code == 0
    assert out == (
        "home.md (home)\n"
        "→ python.md  [[python]]\n"
        "→ python.md  [[python|Py 学习笔记]]\n"
    )


def test_links_shows_dead_link_line_for_unresolvable_target() -> None:
    code, out, err = run_cli(["--vault", str(vault_path("links-dead")), "links", "home"])

    assert code == 0
    assert out == (
        "home.md (home)\n"
        "→ python.md  [[python]]\n"
        "✗ 未解析: [[ghost]]\n"
    )


def test_links_strips_anchor_from_page_and_anchor_alias_forms() -> None:
    """`[[页面#小节]]` 与 `[[页面#小节|别名]]` 剥锚点与别名后按页面名解析（checklist 2）。"""
    code, out, err = run_cli(["--vault", str(vault_path("links-anchor")), "links", "home"])

    assert code == 0
    assert out == (
        "home.md (home)\n"
        "→ python.md  [[python#入门]]\n"
        "→ python.md  [[python#入门|Py 入门]]\n"
    )


def test_links_resolves_subdirectory_path_form_exactly() -> None:
    """`[[子目录/页面]]` 按相对路径精确匹配；路径不存在为死链（checklist 1）。"""
    code, out, err = run_cli(["--vault", str(vault_path("links-path")), "links", "home"])

    assert code == 0
    assert out == (
        "home.md (home)\n"
        "→ notes/deep.md  [[notes/deep]]\n"
        "✗ 未解析: [[notes/ghost]]\n"
    )


def test_links_falls_back_to_case_insensitive_match() -> None:
    """stem 精确匹配失败后按大小写不敏感兜底：[[python]] 连到 Python.md（checklist 4）。"""
    code, out, err = run_cli(["--vault", str(vault_path("links-case")), "links", "home"])

    assert code == 0
    assert out == (
        "home.md (home)\n"
        "→ Python.md  [[python]]\n"
    )


def test_links_marks_ambiguous_stem_with_candidates_not_dead() -> None:
    """同 stem 多页面 → 歧义标注（非 ✗ 未解析）；路径写法可消歧（checklist 5）。"""
    code, out, err = run_cli(
        ["--vault", str(vault_path("links-ambiguous")), "links", "home"]
    )

    assert code == 0
    assert out == (
        "home.md (home)\n"
        "⚠ 歧义: [[notes]] → a/notes.md, b/notes.md\n"
        "→ a/notes.md  [[a/notes]]\n"
    )


def test_links_json_marks_ambiguous_status_without_new_fields() -> None:
    """--json 只扩展 status 取值（ambiguous），字段结构不变。"""
    code, out, err = run_cli(
        ["--vault", str(vault_path("links-ambiguous")), "--json", "links", "home"]
    )

    assert code == 0
    doc = json.loads(out)
    assert doc["links"] == [
        {"raw": "notes", "status": "ambiguous", "target": None},
        {"raw": "a/notes", "status": "resolved", "target": "a/notes.md"},
    ]


def test_links_inpage_anchor_leaves_no_trace() -> None:
    """`[[#小节]]` 完全不计数：links 输出与 JSON 索引均无痕迹（checklist 3）。"""
    code, out, err = run_cli(
        ["--vault", str(vault_path("links-inpage")), "--json", "links", "home"]
    )

    assert code == 0
    doc = json.loads(out)
    assert doc["links"] == []  # 索引无痕迹


def test_links_ambiguous_page_argument_exits_2_with_candidates() -> None:
    """links 查询参数与 backlinks 完全同规（review S4）：裸 stem 命中多个
    页面 → stderr 列全部候选 + 提示路径写法消歧 + exit 2，不静默取首个。
    """
    code, out, err = run_cli(["--vault", str(vault_path("links-ambiguous")), "links", "notes"])

    assert code == 2
    assert out == ""
    assert "页面名歧义: notes" in err
    assert "a/notes.md" in err and "b/notes.md" in err
    assert "子目录/页面" in err


def test_links_page_argument_falls_back_to_case_insensitive_match() -> None:
    """links 查询参数与 backlinks 完全同规（review S4）：stem 精确匹配失败
    后大小写不敏感兜底——[[python]] 能连到的 Python.md，`links python` 也能查。
    """
    code, out, err = run_cli(["--vault", str(vault_path("links-case")), "links", "python"])

    assert code == 0
    assert out == "Python.md (Python)\n"


def test_links_shows_self_link_as_regular_forward_link() -> None:
    """自链接出现在 links 输出中，链接事实如实展示（checklist 6）。"""
    code, out, err = run_cli(["--vault", str(vault_path("links-self")), "links", "python"])

    assert code == 0
    assert out == (
        "python.md (python)\n"
        "→ python.md  [[python]]\n"
    )


def test_links_ignores_links_and_tags_inside_code() -> None:
    """围栏代码块与行内代码内的 [[..]] 与 #tag 不产生任何链接（checklist 3）。"""
    code, out, err = run_cli(["--vault", str(vault_path("links-code")), "links", "example"])

    assert code == 0
    assert out == (
        "notes/example.md (example)\n"
        "→ python.md  [[python]]\n"
        "→ python.md  [[python|真别名]]\n"
    )

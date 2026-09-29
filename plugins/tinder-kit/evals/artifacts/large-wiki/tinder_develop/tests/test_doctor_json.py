"""`--json doctor`：三类发现数组的机器可读文档（ticket 07，spec: render 契约）。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from conftest import run_cli, vault_path


def test_doctor_json_mixed_vault_single_document_with_three_finding_arrays() -> None:
    """单对象文档，字段与 DoctorResult 一一对应：三类发现数组齐备，
    条目含 路径/行号/原文（歧义另含全部候选）等定位信息。
    （期望值即 test_doctor.py 已固化的人读事实，同一批发现的 JSON 视角。）"""
    code, out, err = run_cli(
        ["--vault", str(vault_path("doctor-mixed")), "--json", "doctor"]
    )

    assert code == 1
    doc = json.loads(out)  # 单个 JSON 对象，可解析
    assert doc == {
        "command": "doctor",
        "page_count": 3,
        "link_count": 2,
        "tag_count": 0,
        "dead_links": [{"source": "home.md", "line": 1, "raw": "ghost"}],
        "orphans": ["home.md"],
        "ambiguous": [
            {
                "source": "home.md",
                "line": 1,
                "raw": "notes",
                "candidates": ["a/notes.md", "b/notes.md"],
            }
        ],
    }
    assert err == ""


def test_doctor_json_healthy_vault_exits_0_with_empty_finding_arrays() -> None:
    """零发现的 vault：exit 0（与人读一致），三类发现数组均为空但字段在场。"""
    code, out, err = run_cli(
        ["--vault", str(vault_path("doctor-healthy")), "--json", "doctor"]
    )

    assert code == 0
    doc = json.loads(out)
    assert doc["dead_links"] == []
    assert doc["orphans"] == []
    assert doc["ambiguous"] == []
    assert doc["page_count"] == 2
    assert err == ""


def test_doctor_json_exit_codes_match_human_mode_across_matrix() -> None:
    """`--json` 不改变退出码语义（ticket 07）：doctor 三态矩阵逐项与
    人读模式同码——0 健康 / 1 有发现 / 2 用法错误。"""
    cases: list[tuple[list[str], int]] = [
        (["--vault", str(vault_path("doctor-healthy")), "doctor"], 0),
        (["--vault", str(vault_path("doctor-mixed")), "doctor"], 1),
        (["--vault", str(vault_path("doctor-empty")), "doctor"], 0),
        (["doctor", "extra-arg"], 2),
    ]
    for args_without_json, expected_code in cases:
        vault_flag, *rest = args_without_json
        code_human, _, _ = run_cli([vault_flag, *rest])
        code_json, _, _ = run_cli(["--json", vault_flag, *rest])
        assert code_human == expected_code, args_without_json
        assert code_json == code_human, args_without_json

    # 空库：零统计、零发现，exit 0
    code_empty, out_empty, _ = run_cli(
        ["--vault", str(vault_path("doctor-empty")), "--json", "doctor"]
    )
    assert code_empty == 0
    doc = json.loads(out_empty)
    assert doc == {
        "command": "doctor",
        "page_count": 0,
        "link_count": 0,
        "tag_count": 0,
        "dead_links": [],
        "orphans": [],
        "ambiguous": [],
    }

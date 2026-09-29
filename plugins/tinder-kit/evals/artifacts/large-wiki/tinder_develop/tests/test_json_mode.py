"""全局 `--json` 收口：五命令均输出单个可解析 JSON 文档（ticket 07）。

每命令的字段结构断言固化在各自的 JSON 测试里（test_links_json /
test_backlinks / test_search / test_tags_json / test_doctor_json）；
这里钉的是全局承诺——任何命令 `--json` 都可被 `json.loads` 一次吃下。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from conftest import run_cli, vault_path


def test_all_five_commands_emit_single_parseable_json_document() -> None:
    """五命令 × `--json`：stdout 是单个 JSON 对象，command 字段自报家门，
    退出码与人读模式一致。"""
    cases: list[tuple[str, list[str], str, int]] = [
        ("links", ["--vault", str(vault_path("links-dead")), "links", "home"], "links", 0),
        ("backlinks", ["--vault", str(vault_path("backlinks-basic")), "backlinks", "python"], "backlinks", 0),
        ("tags", ["--vault", str(vault_path("tags-valid")), "tags"], "tags", 0),
        ("search", ["--vault", str(vault_path("search-basic")), "search", "python"], "search", 0),
        ("doctor", ["--vault", str(vault_path("doctor-mixed")), "doctor"], "doctor", 1),
    ]
    for command, base_args, expected_command, expected_code in cases:
        code_human, _, _ = run_cli(base_args)
        code_json, out, err = run_cli(["--json", *base_args])
        assert code_human == code_json == expected_code, command
        assert err == "", command
        doc = json.loads(out)  # 单个 JSON 对象；多文档/尾随垃圾此处即炸
        assert doc["command"] == expected_command, command

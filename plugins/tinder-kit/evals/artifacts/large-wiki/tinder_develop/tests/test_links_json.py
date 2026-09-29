"""`--json` 全局开关：render 的 JSON 双模式（spec: render 契约）。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from conftest import run_cli, vault_path


def test_links_json_outputs_single_stable_document() -> None:
    code, out, err = run_cli(
        ["--vault", str(vault_path("links-dead")), "--json", "links", "home"]
    )

    assert code == 0
    doc = json.loads(out)  # 单个 JSON 对象，可解析
    assert doc == {
        "command": "links",
        "page": {"path": "home.md", "name": "home"},
        "links": [
            {"raw": "python", "status": "resolved", "target": "python.md"},
            {"raw": "ghost", "status": "dead", "target": None},
        ],
    }

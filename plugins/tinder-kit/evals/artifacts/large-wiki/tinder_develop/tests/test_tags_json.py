"""`tags` 的 `--json` 双模式：单个稳定字段的 JSON 文档（spec: render 契约）。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from conftest import run_cli, vault_path


def test_tags_json_overview_outputs_single_stable_document() -> None:
    code, out, err = run_cli(["--vault", str(vault_path("tags-sort")), "--json", "tags"])

    assert code == 0
    doc = json.loads(out)  # 单个 JSON 对象，可解析
    assert doc == {
        "command": "tags",
        "tags": [
            {"tag": "x", "page_count": 3},
            {"tag": "y", "page_count": 2},
            {"tag": "z", "page_count": 2},
        ],
    }


def test_tags_json_query_outputs_tag_with_page_paths() -> None:
    code, out, err = run_cli(
        ["--vault", str(vault_path("tags-nested")), "--json", "tags", "concepts"]
    )

    assert code == 0
    doc = json.loads(out)
    assert doc == {
        "command": "tags",
        "tag": "concepts",
        "pages": ["both.md", "concepts.md", "gc.md", "os.md"],
    }

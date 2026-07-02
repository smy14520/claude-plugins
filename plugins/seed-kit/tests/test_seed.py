from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import seed  # noqa: E402


PRD_INLINE = """# demo

## Goal

测试用 PRD，slice 内联。

## Acceptance Criteria

### [ ] S-001 输出问候
* [ ] 输入合法文本 → 输出问候语
* [ ] 空输入 → 被拒绝

### [ ] S-002 带子步骤
* [ ] 渲染结果可读，信息层次清晰

## Out of Scope
"""


@pytest.fixture
def project(tmp_path: Path) -> Path:
    return tmp_path


def make_task(
    root: Path,
    name: str = "demo",
    prd: str = PRD_INLINE,
    package_json: dict | None = None,
) -> Path:
    task_dir = root / ".arbor" / "tasks" / name
    task_dir.mkdir(parents=True)
    (task_dir / "notes").mkdir()
    (task_dir / "prd.md").write_text(prd, encoding="utf-8")
    if package_json:
        (root / "package.json").write_text(json.dumps(package_json), encoding="utf-8")
    return task_dir


def run(root: Path, *argv: str) -> int:
    return seed.main(["--root", str(root), *argv])


# --- new ---------------------------------------------------------------------

def test_new_scaffolds_task(project: Path, capsys):
    assert run(project, "new", "demo") == 0
    task_dir = project / ".arbor" / "tasks" / "demo"
    assert (task_dir / "prd.md").is_file()
    assert (task_dir / "notes").is_dir()
    assert not (task_dir / "slices").exists()
    content = (task_dir / "prd.md").read_text(encoding="utf-8")
    assert "# demo" in content
    assert "### [ ] S-001" in content
    assert "## Acceptance Criteria" in content


def test_new_rejects_existing_task(project: Path, capsys):
    assert run(project, "new", "demo") == 0
    assert run(project, "new", "demo") == 1
    assert "已存在" in capsys.readouterr().err


def test_new_rejects_bad_name(project: Path, capsys):
    assert run(project, "new", "Bad Name") == 1
    assert "任务名" in capsys.readouterr().err


# --- status ------------------------------------------------------------------

def test_status_reports_progress_and_next(project: Path, capsys):
    make_task(project)
    assert run(project, "status", "demo", "--json") == 0
    data = json.loads(capsys.readouterr().out)
    assert [s["id"] for s in data["slices"]] == ["S-001", "S-002"]
    assert data["next"] == "S-001"
    assert data["errors"] == []


def test_status_detects_duplicate_slice_id(project: Path, capsys):
    prd = "# demo\n\n### [ ] S-001 第一步\n### [ ] S-001 重复\n"
    make_task(project, prd=prd)
    assert run(project, "status", "demo", "--json") == 1
    data = json.loads(capsys.readouterr().out)
    assert any("重复" in err for err in data["errors"])


def test_status_flags_bad_heading(project: Path, capsys):
    prd = "# demo\n\n### 没有 checkbox 的标题\n"
    make_task(project, prd=prd)
    assert run(project, "status", "demo", "--json") == 1
    data = json.loads(capsys.readouterr().out)
    assert any("S-NNN" in err for err in data["errors"])


def test_status_flags_no_slices(project: Path, capsys):
    prd = "# demo\n\n## Acceptance Criteria\n\n没有 slice heading\n"
    make_task(project, prd=prd)
    assert run(project, "status", "demo", "--json") == 1
    data = json.loads(capsys.readouterr().out)
    assert any("缺少 slice heading" in err for err in data["errors"])


def test_status_lists_all_tasks(project: Path, capsys):
    make_task(project, "alpha")
    make_task(project, "beta")
    assert run(project, "status") == 0
    out = capsys.readouterr().out
    assert "alpha: 0/2" in out
    assert "beta: 0/2" in out


def test_status_reports_quality_commands(project: Path, capsys):
    make_task(project, package_json={"scripts": {"test": "node --test", "lint": "eslint ."}})
    assert run(project, "status", "demo", "--json") == 0
    data = json.loads(capsys.readouterr().out)
    assert "test" in data["commands"]
    assert "lint" in data["commands"]


# --- done --------------------------------------------------------------------

def _setup_pass_test(project: Path):
    (project / "package.json").write_text(json.dumps({
        "scripts": {"test": "node --test test.js"}
    }))
    (project / "test.js").write_text(
        "const {test} = require('node:test');\n"
        "test('passes', () => {});\n"
    )


def _setup_pass_test_with_lint(project: Path):
    (project / "package.json").write_text(json.dumps({
        "scripts": {
            "test": "node --test test.js",
            "lint": "node -e \"process.exit(0)\"",
            "typecheck": "node -e \"process.exit(0)\"",
        }
    }))
    (project / "test.js").write_text(
        "const {test} = require('node:test');\n"
        "test('passes', () => {});\n"
    )


def test_done_flips_checkbox_when_tests_pass(project: Path, capsys):
    make_task(project)
    _setup_pass_test(project)
    assert run(project, "done", "demo", "--slice", "S-001") == 0
    out = capsys.readouterr().out
    assert "已完成" in out
    assert "next: S-002" in out
    prd = (project / ".arbor" / "tasks" / "demo" / "prd.md").read_text(encoding="utf-8")
    assert "### [x] S-001" in prd
    assert "### [ ] S-002" in prd


def test_done_blocked_by_failing_test(project: Path, capsys):
    (project / "package.json").write_text(json.dumps({
        "scripts": {"test": "node --test failing.test.js"}
    }))
    (project / "failing.test.js").write_text(
        "const {test} = require('node:test');\n"
        "const assert = require('node:assert');\n"
        "test('fails', () => { assert.fail('expected failure'); });\n"
    )
    make_task(project)
    assert run(project, "done", "demo", "--slice", "S-001") == 1
    assert "测试命令未通过" in capsys.readouterr().err
    prd = (project / ".arbor" / "tasks" / "demo" / "prd.md").read_text(encoding="utf-8")
    assert "### [x]" not in prd


def test_done_blocked_by_fake_test(project: Path, capsys):
    make_task(project, package_json={"scripts": {"test": "true"}})
    assert run(project, "done", "demo", "--slice", "S-001") == 1
    assert "伪装的" in capsys.readouterr().err


def test_done_blocked_by_echo_test(project: Path, capsys):
    make_task(project, package_json={"scripts": {"test": "echo all passed"}})
    assert run(project, "done", "demo", "--slice", "S-001") == 1
    assert "伪装的" in capsys.readouterr().err


def test_done_allows_echo_with_real_test(project: Path, capsys):
    make_task(project)
    (project / "package.json").write_text(json.dumps({
        "scripts": {"test": "echo starting && node --test test.js"}
    }))
    (project / "test.js").write_text(
        "const {test} = require('node:test');\n"
        "test('passes', () => {});\n"
    )
    assert run(project, "done", "demo", "--slice", "S-001") == 0


def test_done_blocked_by_bin_true(project: Path, capsys):
    make_task(project, package_json={"scripts": {"test": "/bin/true"}})
    assert run(project, "done", "demo", "--slice", "S-001") == 1
    assert "伪装的" in capsys.readouterr().err


def test_done_blocked_by_node_e_without_test(project: Path, capsys):
    make_task(project, package_json={"scripts": {"test": "node -e \"process.exit(0)\""}})
    assert run(project, "done", "demo", "--slice", "S-001") == 1
    assert "伪装的" in capsys.readouterr().err


def test_done_blocked_by_failing_lint(project: Path, capsys):
    (project / "package.json").write_text(json.dumps({
        "scripts": {
            "test": "node --test test.js",
            "lint": "node -e \"process.exit(1)\"",
        }
    }))
    (project / "test.js").write_text(
        "const {test} = require('node:test');\n"
        "test('passes', () => {});\n"
    )
    make_task(project)
    assert run(project, "done", "demo", "--slice", "S-001") == 1
    assert "质量命令未通过" in capsys.readouterr().err


def test_done_quality_commands_all_pass(project: Path, capsys):
    make_task(project)
    _setup_pass_test_with_lint(project)
    assert run(project, "done", "demo", "--slice", "S-001") == 0
    out = capsys.readouterr().out
    assert "已完成" in out
    assert "lint:" in out
    assert "typecheck:" in out


def test_done_is_idempotent(project: Path, capsys):
    make_task(project)
    _setup_pass_test(project)
    assert run(project, "done", "demo", "--slice", "S-001") == 0
    assert run(project, "done", "demo", "--slice", "S-001") == 0
    assert "已是完成状态" in capsys.readouterr().out


def test_done_unknown_slice(project: Path, capsys):
    make_task(project)
    assert run(project, "done", "demo", "--slice", "S-999") == 1
    assert "不存在" in capsys.readouterr().err


def test_done_blocked_without_project_config(project: Path, capsys):
    make_task(project)
    assert run(project, "done", "demo", "--slice", "S-001") == 1
    assert "未找到项目测试命令" in capsys.readouterr().err


def test_done_records_log(project: Path, capsys):
    make_task(project)
    _setup_pass_test(project)
    assert run(project, "done", "demo", "--slice", "S-001") == 0
    logs = list((project / ".arbor" / "tasks" / "demo" / "done-logs").glob("*.json"))
    assert len(logs) == 1
    log_data = json.loads(logs[0].read_text())
    assert log_data["test"]["exit_code"] == 0


def test_done_all_slices_complete_message(project: Path, capsys):
    prd = "# demo\n\n### [x] S-001 唯一\n\n已完成。\n"
    make_task(project, prd=prd)
    _setup_pass_test(project)
    # Already done, should report idempotent
    assert run(project, "done", "demo", "--slice", "S-001") == 0


# --- review-mark -------------------------------------------------------------

def test_review_mark_writes_marker(project: Path, capsys):
    make_task(project)
    assert run(project, "review-mark", "demo", "--verdict", "converged", "--round", "2") == 0
    marker = project / ".arbor" / "tasks" / "demo" / "review-loop.json"
    assert marker.is_file()
    data = json.loads(marker.read_text())
    assert data["terminal_reason"] == "converged"
    assert data["converged"] is True
    assert data["round"] == 2


def test_review_mark_rejects_invalid_verdict(project: Path, capsys):
    make_task(project)
    assert run(project, "review-mark", "demo", "--verdict", "abandoned") == 1
    assert "converged" in capsys.readouterr().err


def test_review_mark_rejects_negative_round(project: Path, capsys):
    make_task(project)
    assert run(project, "review-mark", "demo", "--verdict", "converged", "--round", "-1") == 1


def test_review_mark_unknown_task(project: Path, capsys):
    assert run(project, "review-mark", "nope", "--verdict", "converged") == 1
    assert "未找到" in capsys.readouterr().err


# --- project commands detection ----------------------------------------------

def test_detects_package_json_commands(project: Path):
    (project / "package.json").write_text(json.dumps({
        "scripts": {"test": "jest", "lint": "eslint .", "build": "tsc"}
    }))
    cmds = seed._read_project_commands(project)
    assert cmds["test"] == "npm test"
    assert cmds["lint"] == "npm run lint"
    assert cmds["build"] == "npm run build"


def test_detects_makefile_targets(project: Path):
    (project / "Makefile").write_text("test:\n\tpytest\nlint:\n\truff check .\n")
    cmds = seed._read_project_commands(project)
    assert cmds["test"] == "make test"
    assert cmds["lint"] == "make lint"


def test_detects_cargo_commands(project: Path):
    (project / "Cargo.toml").write_text("[package]\nname = \"test\"\n")
    cmds = seed._read_project_commands(project)
    assert cmds["test"] == "cargo test"
    assert cmds["build"] == "cargo build"
    assert cmds["lint"] == "cargo clippy"


# --- score aggregate ---------------------------------------------------------

def test_score_aggregate_computes_median(project: Path, capsys):
    rubric = {
        "id": "test-rubric",
        "scale": {"min": 0, "max": 5},
        "dimensions": {"visual": {"min": 2}, "hierarchy": {"min": 3}},
    }
    (project / "rubric.json").write_text(json.dumps(rubric))

    scores = [
        {"rubric_id": "test-rubric", "scores": {"visual": 2, "hierarchy": 4}},
        {"rubric_id": "test-rubric", "scores": {"visual": 3, "hierarchy": 4}},
        {"rubric_id": "test-rubric", "scores": {"visual": 4, "hierarchy": 3}},
    ]
    for i, s in enumerate(scores):
        (project / f"score-{i}.json").write_text(json.dumps(s))

    assert run(project, "score", "aggregate",
               "--rubric", "rubric.json",
               "--score-files", "score-0.json", "score-1.json", "score-2.json",
               "--out", "aggregate.json") == 0

    agg = json.loads((project / "aggregate.json").read_text())
    assert agg["method"] == "median"
    assert agg["dimensions"]["visual"]["score"] == 3.0
    assert agg["dimensions"]["hierarchy"]["score"] == 4.0
    assert agg["average"] == 3.5


def test_makefile_with_existing_package_json_commands(project: Path):
    (project / "package.json").write_text(json.dumps({
        "scripts": {"test": "jest"}
    }))
    (project / "Makefile").write_text("test:\n\tpytest\nbuild:\n\tmake build\n")
    cmds = seed._read_project_commands(project)
    assert cmds["test"] == "npm test"
    assert cmds["build"] == "make build"

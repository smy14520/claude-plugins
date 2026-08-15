from __future__ import annotations

import hashlib
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


def test_status_flags_unconfirmed_oos_entry(project: Path, capsys):
    """排除是用户决策：无（用户确认）标注的 OoS 条目 = 结构错误（硬 gate）。
    取证 approval-hard 四臂对比：agent 想到进阶规则却单方写进 OoS 排除，三层防线全部失守。"""
    prd = PRD_INLINE + "* 不做进阶档位\n"
    make_task(project, prd=prd)
    assert run(project, "status", "demo", "--json") == 1
    data = json.loads(capsys.readouterr().out)
    assert any("用户确认" in err for err in data["errors"])
    # 结构错误统一走 parse_prd：done 同样被硬闸拦下
    (project / "package.json").write_text(
        json.dumps({"scripts": {"test": "node --test test.js"}}), encoding="utf-8"
    )
    (project / "test.js").write_text(
        "const t = require('node:test'); t.test('ok', () => {});", encoding="utf-8"
    )
    assert run(project, "done", "demo", "--slice", "S-001", "--test", "node --test test.js") == 1


def test_status_accepts_confirmed_oos_entries(project: Path, capsys):
    """全角/半角标注均可；缩进子条目是细节说明，不要求独立标注；空 OoS 区不报错。"""
    prd = PRD_INLINE + (
        "* 不做进阶档位（用户确认）\n"
        "- 不做多语言 (用户确认)\n"
        "  * 含错误文案在内都只出中文\n"
    )
    make_task(project, prd=prd)
    assert run(project, "status", "demo", "--json") == 0
    data = json.loads(capsys.readouterr().out)
    assert data["errors"] == []


def test_status_oos_before_slices_does_not_swallow_headings(project: Path, capsys):
    """OoS 区段以下一个 heading（## 或 ###）为界：OoS 写在 AC 前时 slice 照常解析。"""
    prd = (
        "# demo\n\n## Goal\n\n测试。\n\n## Out of Scope\n\n"
        "- 排除项（用户确认）\n\n"
        "### [ ] S-001 第一步\n\n* [ ] 条目\n"
    )
    make_task(project, prd=prd)
    assert run(project, "status", "demo", "--json") == 0
    data = json.loads(capsys.readouterr().out)
    assert [s["id"] for s in data["slices"]] == ["S-001"]
    assert data["errors"] == []


def test_status_lists_all_tasks(project: Path, capsys):
    make_task(project, "alpha")
    make_task(project, "beta")
    assert run(project, "status") == 0
    out = capsys.readouterr().out
    assert "alpha: 0/2" in out
    assert "beta: 0/2" in out


def test_status_does_not_infer_project_commands(project: Path, capsys):
    make_task(project, package_json={"scripts": {"test": "node --test", "lint": "eslint ."}})
    assert run(project, "status", "demo", "--json") == 0
    data = json.loads(capsys.readouterr().out)
    assert "commands" not in data


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
    assert run(project, "done", "demo", "--slice", "S-001", "--test", "node --test test.js") == 0
    out = capsys.readouterr().out
    assert "已完成" in out
    assert "next: S-002" in out
    prd = (project / ".arbor" / "tasks" / "demo" / "prd.md").read_text(encoding="utf-8")
    assert "### [x] S-001" in prd
    assert "### [ ] S-002" in prd


def test_review_mark_converged_refused_with_unfinished_slices(project: Path, capsys):
    """converged 是完成态终词：存在未过 gate 的 slice 时 durable marker 拒写(硬闸)。"""
    make_task(project, package_json={"scripts": {"test": "node --test test.js"}})
    (project / "test.js").write_text(
        "const t = require('node:test'); t.test('ok', () => {});", encoding="utf-8"
    )
    # 全部未完成 → 拒绝
    assert run(project, "review-mark", "demo", "--verdict", "converged") == 1
    err = capsys.readouterr().err
    assert "拒绝写 converged" in err and "S-001" in err
    marker = project / ".arbor" / "tasks" / "demo" / "review-loop.json"
    assert not marker.exists()
    # 非 converged 终词不受账本约束(escalate 类如实落盘)
    assert run(project, "review-mark", "demo", "--verdict", "circuit-breaker") == 0
    assert marker.exists()
    # 全部 slice 过 gate 后 converged 可写
    assert run(project, "done", "demo", "--slice", "S-001", "--test", "node --test test.js") == 0
    assert run(project, "done", "demo", "--slice", "S-002", "--test", "node --test test.js") == 0
    assert run(project, "review-mark", "demo", "--verdict", "converged") == 0


def test_done_flips_slice_items_atomically(project: Path, capsys):
    """gate 通过时 slice 头与该区段内验收条目原子翻转，账本自洽；他 slice 不受影响；PRD 指纹不变。"""
    make_task(project, package_json={"scripts": {"test": "node --test test.js"}})
    (project / "test.js").write_text(
        "const t = require('node:test'); t.test('ok', () => {});", encoding="utf-8"
    )
    sha_before = seed._normalized_prd_sha(project, "demo")
    assert run(project, "done", "demo", "--slice", "S-001", "--test", "node --test test.js") == 0
    content = (project / ".arbor" / "tasks" / "demo" / "prd.md").read_text(encoding="utf-8")
    assert "### [x] S-001" in content
    assert "* [x] 输入合法文本 → 输出问候语" in content
    assert "* [x] 空输入 → 被拒绝" in content
    # S-002 区段不受影响
    assert "### [ ] S-002" in content
    assert "* [ ] 渲染结果可读，信息层次清晰" in content
    # 翻 checkbox 是工作流动作，不改变 PRD 指纹
    assert seed._normalized_prd_sha(project, "demo") == sha_before


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
    assert run(project, "done", "demo", "--slice", "S-001", "--test", "node --test failing.test.js") == 1
    assert "测试命令未通过" in capsys.readouterr().err
    prd = (project / ".arbor" / "tasks" / "demo" / "prd.md").read_text(encoding="utf-8")
    assert "### [x]" not in prd


def test_done_blocked_by_fake_test(project: Path, capsys):
    make_task(project)
    assert run(project, "done", "demo", "--slice", "S-001", "--test", "true") == 1
    assert "伪装的" in capsys.readouterr().err


def test_done_blocked_by_echo_test(project: Path, capsys):
    make_task(project)
    assert run(project, "done", "demo", "--slice", "S-001", "--test", "echo all passed") == 1
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
    assert run(project, "done", "demo", "--slice", "S-001", "--test", "echo starting && node --test test.js") == 0


def test_done_blocked_by_bin_true(project: Path, capsys):
    make_task(project)
    assert run(project, "done", "demo", "--slice", "S-001", "--test", "/bin/true") == 1
    assert "伪装的" in capsys.readouterr().err


def test_done_blocked_by_node_e_without_test(project: Path, capsys):
    make_task(project)
    assert run(project, "done", "demo", "--slice", "S-001", "--test", "node -e \"process.exit(0)\"") == 1
    assert "伪装的" in capsys.readouterr().err


@pytest.mark.parametrize("command", [
    "true && echo ok",
    "(true; printf ok)",
    "sh -c 'true && echo ok'",
    "bash -c \"sh -c 'exit 0'\"",
    "python -c 'sys.exit(0)'",
    "python3 -c 'raise SystemExit(0)'",
    "ruby -e 'exit(0)'",
])
def test_obvious_noop_detection_recurses_through_compound_commands(command: str):
    assert seed._looks_like_obvious_noop(command) is True


@pytest.mark.parametrize("command", [
    "echo starting && project-check",
    "sh -c 'echo starting && project-check'",
    "python -c 'print(42)'",
])
def test_obvious_noop_detection_allows_commands_with_substantive_leaf(command: str):
    assert seed._looks_like_obvious_noop(command) is False


def test_done_rejects_obvious_noop_quality_command(project: Path, capsys):
    make_task(project)
    _setup_pass_test(project)
    assert run(
        project,
        "done", "demo", "--slice", "S-001",
        "--test", "node --test test.js",
        "--quality", "sh -c 'true && echo ok'",
    ) == 1
    assert "质量命令像伪装的空操作" in capsys.readouterr().err


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
    assert run(project, "done", "demo", "--slice", "S-001", "--test", "node --test test.js", "--quality", "node -e \"process.exit(1)\"") == 1
    assert "质量命令未通过" in capsys.readouterr().err


def test_done_quality_commands_all_pass(project: Path, capsys):
    make_task(project)
    _setup_pass_test_with_lint(project)
    assert run(
        project,
        "done", "demo", "--slice", "S-001",
        "--test", "node --test test.js",
        "--quality", "npm run lint",
        "--quality", "npm run typecheck",
    ) == 0
    out = capsys.readouterr().out
    assert "已完成" in out
    assert "npm run lint:" in out
    assert "npm run typecheck:" in out


def test_done_is_idempotent(project: Path, capsys):
    make_task(project)
    _setup_pass_test(project)
    assert run(project, "done", "demo", "--slice", "S-001", "--test", "node --test test.js") == 0
    assert run(project, "done", "demo", "--slice", "S-001", "--test", "node --test test.js") == 0
    assert "已是完成状态" in capsys.readouterr().out


def test_done_unknown_slice(project: Path, capsys):
    make_task(project)
    assert run(project, "done", "demo", "--slice", "S-999") == 1
    assert "不存在" in capsys.readouterr().err


def test_done_requires_explicit_test_command(project: Path, capsys):
    make_task(project)
    assert run(project, "done", "demo", "--slice", "S-001") == 1
    assert "需要提供 --test" in capsys.readouterr().err


def test_done_records_log(project: Path, capsys):
    make_task(project)
    _setup_pass_test(project)
    assert run(project, "done", "demo", "--slice", "S-001", "--test", "node --test test.js") == 0
    logs = list((project / ".arbor" / "tasks" / "demo" / "done-logs").glob("*.json"))
    assert len(logs) == 1
    log_data = json.loads(logs[0].read_text())
    test_result = log_data["test"]
    assert test_result["exit_code"] == 0
    assert isinstance(test_result["output_summary"], str)
    assert len(test_result["output_sha256"]) == 64
    assert test_result["output_bytes"] >= len(test_result["output_summary"].encode())
    assert test_result["output_truncated"] is False
    assert log_data["quality"] == []


def test_command_result_limits_summary_and_hashes_full_output():
    output = "a" * 2000
    result = seed._command_result("project-check", 7, output)
    assert result["exit_code"] == 7
    assert result["output_truncated"] is True
    assert len(result["output_summary"]) < len(output)
    assert result["output_sha256"] == hashlib.sha256(output.encode()).hexdigest()
    assert result["output_bytes"] == 2000


def test_done_all_slices_complete_message(project: Path, capsys):
    prd = "# demo\n\n### [x] S-001 唯一\n\n已完成。\n"
    make_task(project, prd=prd)
    _setup_pass_test(project)
    # Already done, should report idempotent
    assert run(project, "done", "demo", "--slice", "S-001", "--test", "node --test test.js") == 0


# --- review-mark -------------------------------------------------------------

def test_review_mark_writes_marker(project: Path, capsys):
    make_task(project, package_json={"scripts": {"test": "node --test test.js"}})
    (project / "test.js").write_text(
        "const t = require('node:test'); t.test('ok', () => {});", encoding="utf-8"
    )
    # converged 前置：所有 slice 已过 gate
    assert run(project, "done", "demo", "--slice", "S-001", "--test", "node --test test.js") == 0
    assert run(project, "done", "demo", "--slice", "S-002", "--test", "node --test test.js") == 0
    assert run(project, "review-mark", "demo", "--verdict", "converged", "--round", "2") == 0
    marker = project / ".arbor" / "tasks" / "demo" / "review-loop.json"
    assert marker.is_file()
    data = json.loads(marker.read_text())
    assert data["terminal_reason"] == "converged"
    assert data["converged"] is True
    assert data["round"] == 2
    # 省略 --depth 保持 single（不改变既有调用行为）；inline=编排者内联自查；full=5 agent review-loop
    assert data["depth"] == "single"
    assert run(project, "review-mark", "demo", "--verdict", "converged", "--depth", "inline") == 0
    data = json.loads(marker.read_text())
    assert data["depth"] == "inline"
    assert run(project, "review-mark", "demo", "--verdict", "converged", "--depth", "full") == 0
    data = json.loads(marker.read_text())
    assert data["depth"] == "full"


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


# --- map（wayfinder 决策图 helper）---------------------------------------------

def make_ticket(
    root: Path,
    map_slug: str,
    name: str,
    *,
    status: str = "open",
    blocked_by: str = "",
    resolution: bool = False,
    raw: str | None = None,
) -> Path:
    tickets = root / ".arbor" / "maps" / map_slug / "tickets"
    tickets.mkdir(parents=True, exist_ok=True)
    if raw is not None:
        body = raw
    else:
        blocked = f"[{blocked_by}]" if blocked_by else "[]"
        body = (
            "---\n"
            f"type: grilling\n"
            f"status: {status}\n"
            f"blocked-by: {blocked}\n"
            "---\n"
            "\n"
            "## Question\n"
            "\n"
            "这是一个决策问题。\n"
        )
        if resolution:
            body += "\n## Resolution\n\n已拍板。\n"
    path = tickets / f"{name}.md"
    path.write_text(body, encoding="utf-8")
    return path


def test_map_new_scaffolds_map_and_tickets(project: Path, capsys):
    assert run(project, "map", "new", "auth-map") == 0
    map_dir = project / ".arbor" / "maps" / "auth-map"
    assert (map_dir / "tickets").is_dir()
    content = (map_dir / "map.md").read_text(encoding="utf-8")
    assert "# map: auth-map" in content
    for section in ("## Destination", "## Notes", "## Decisions so far",
                    "## Not yet specified", "## Out of scope"):
        assert section in content


def test_map_new_rejects_existing_slug(project: Path, capsys):
    assert run(project, "map", "new", "auth-map") == 0
    capsys.readouterr()
    assert run(project, "map", "new", "auth-map") == 1
    assert "已存在" in capsys.readouterr().err


def test_map_new_rejects_bad_slug(project: Path, capsys):
    assert run(project, "map", "new", "Bad Map") == 1
    assert "图名" in capsys.readouterr().err


def test_map_status_missing_map(project: Path, capsys):
    assert run(project, "map", "status", "nope") == 1
    assert "未找到" in capsys.readouterr().err


def test_map_status_empty_map(project: Path, capsys):
    run(project, "map", "new", "empty-map")
    capsys.readouterr()  # 丢弃 new 的提示输出
    assert run(project, "map", "status", "empty-map", "--json") == 0
    data = json.loads(capsys.readouterr().out)
    assert data["tickets"] == {"open": 0, "closed": 0, "total": 0}
    assert data["frontier"] == []


def test_map_status_derives_frontier_from_blocked_by(project: Path, capsys):
    run(project, "map", "new", "chain-map")
    capsys.readouterr()  # 丢弃 new 的提示输出
    make_ticket(project, "chain-map", "data-shape", status="open")
    make_ticket(project, "chain-map", "auth-choice", status="open", blocked_by="data-shape")
    make_ticket(project, "chain-map", "stack-call", status="closed", resolution=True)
    assert run(project, "map", "status", "chain-map", "--json") == 0
    data = json.loads(capsys.readouterr().out)
    assert data["tickets"] == {"open": 2, "closed": 1, "total": 3}
    # frontier = open 且 blocked-by 全 closed：无依赖的 data-shape；auth-choice 被 data-shape 挡住
    assert data["frontier"] == ["data-shape"]
    # 依赖拍板后毕业进 frontier
    make_ticket(project, "chain-map", "data-shape", status="closed", resolution=True)
    assert run(project, "map", "status", "chain-map", "--json") == 0
    data = json.loads(capsys.readouterr().out)
    assert data["frontier"] == ["auth-choice"]


def test_map_status_json_excludes_prose_sections(project: Path, capsys):
    """--json 只含票 frontmatter 推导的事实；map.md 散文节（雾区等）不进输出。"""
    run(project, "map", "new", "prose-map")
    capsys.readouterr()  # 丢弃 new 的提示输出
    make_ticket(project, "prose-map", "first")
    map_md = project / ".arbor" / "maps" / "prose-map" / "map.md"
    map_md.write_text(
        map_md.read_text(encoding="utf-8").replace(
            "## Not yet specified",
            "## Not yet specified\n\n- 雾区条目：还看不清、立不了票的问题",
        ),
        encoding="utf-8",
    )
    assert run(project, "map", "status", "prose-map", "--json") == 0
    data = json.loads(capsys.readouterr().out)
    assert set(data.keys()) == {"map", "tickets", "frontier", "errors"}
    assert "雾区条目" not in capsys.readouterr().out


def test_map_status_flags_duplicate_ticket_id(project: Path, capsys):
    run(project, "map", "new", "dup-map")
    make_ticket(project, "dup-map", "same-id")
    # frontmatter id 与另一张票的文件名 stem 相同 → 票号重复
    make_ticket(project, "dup-map", "other", raw=(
        "---\nid: same-id\nstatus: open\nblocked-by: []\n---\n\n## Question\n\nQ\n"
    ))
    assert run(project, "map", "status", "dup-map") == 1
    assert "重复" in capsys.readouterr().out


def test_map_status_flags_unknown_blocked_by(project: Path, capsys):
    run(project, "map", "new", "ref-map")
    make_ticket(project, "ref-map", "blocked", blocked_by="ghost")
    assert run(project, "map", "status", "ref-map") == 1
    assert "ghost" in capsys.readouterr().out


def test_map_status_flags_bad_status_value(project: Path, capsys):
    run(project, "map", "new", "enum-map")
    make_ticket(project, "enum-map", "weird", status="in-progress")
    assert run(project, "map", "status", "enum-map") == 1
    assert "open 或 closed" in capsys.readouterr().out


def test_map_status_flags_closed_without_resolution(project: Path, capsys):
    run(project, "map", "new", "res-map")
    make_ticket(project, "res-map", "closed-bare", status="closed", resolution=False)
    assert run(project, "map", "status", "res-map") == 1
    assert "## Resolution" in capsys.readouterr().out


def test_map_status_flags_missing_frontmatter(project: Path, capsys):
    run(project, "map", "new", "fm-map")
    make_ticket(project, "fm-map", "naked", raw="## Question\n\n没有 frontmatter 的票\n")
    assert run(project, "map", "status", "fm-map") == 1
    assert "frontmatter" in capsys.readouterr().out


def test_map_status_lists_all_errors_not_just_first(project: Path, capsys):
    """结构校验列出全部错误：坏 status 与缺失 Resolution 同时存在时两条都报。"""
    run(project, "map", "new", "multi-map")
    make_ticket(project, "multi-map", "bad-one", status="paused")
    make_ticket(project, "multi-map", "bad-two", status="closed", resolution=False)
    assert run(project, "map", "status", "multi-map") == 1
    out = capsys.readouterr().out
    assert "bad-one" in out and "open 或 closed" in out
    assert "bad-two" in out and "## Resolution" in out


def test_map_status_is_readonly(project: Path, capsys):
    """status 只读：执行前后 map.md 与全部票文件内容不变（含校验失败路径）。"""
    run(project, "map", "new", "ro-map")
    make_ticket(project, "ro-map", "open-one")
    make_ticket(project, "ro-map", "closed-one", status="closed", resolution=True)
    make_ticket(project, "ro-map", "broken", status="paused")  # 校验失败也不改盘
    map_dir = project / ".arbor" / "maps" / "ro-map"
    before = {p.name: p.read_bytes() for p in sorted(map_dir.rglob("*")) if p.is_file()}
    assert before  # 快照非空：map.md + 三张票
    assert run(project, "map", "status", "ro-map") == 1  # broken 票 → 非零，但只读
    assert run(project, "map", "status", "ro-map", "--json") == 1
    after = {p.name: p.read_bytes() for p in sorted(map_dir.rglob("*")) if p.is_file()}
    assert before == after

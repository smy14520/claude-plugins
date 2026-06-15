from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import seed  # noqa: E402


PRD_INDEX = """# demo

## 背景与目标

测试用 PRD。

## Slices

<!-- 索引行注释应被忽略 -->

### [ ] S-001 输出问候
### [ ] S-002 带人工验证的步骤

## 变更记录
"""

SLICE_001 = """# S-001 输出问候

## 验收

AC-1

## 验证

- `echo hi`
"""

SLICE_002 = """# S-002 带人工验证的步骤

## 验收

AC-2

## 验证

- `echo step2`
- [manual] 浏览器确认页面渲染正常
"""

DEFAULT_SLICES = {"S-001": SLICE_001, "S-002": SLICE_002}


@pytest.fixture
def project(tmp_path: Path) -> Path:
    return tmp_path


def make_task(
    root: Path,
    name: str = "demo",
    prd: str = PRD_INDEX,
    slices: dict[str, str] | None = None,
) -> Path:
    task_dir = root / ".seed" / "tasks" / name
    (task_dir / "evidence").mkdir(parents=True)
    (task_dir / "notes").mkdir()
    (task_dir / "slices").mkdir()
    (task_dir / "prd.md").write_text(prd, encoding="utf-8")
    for slice_id, content in (DEFAULT_SLICES if slices is None else slices).items():
        (task_dir / "slices" / f"{slice_id}.md").write_text(content, encoding="utf-8")
    return task_dir


def single_slice_task(root: Path, index_line: str, slice_md: str, slice_id: str = "S-001") -> Path:
    prd = f"# demo\n\n## Slices\n\n{index_line}\n"
    return make_task(root, prd=prd, slices={slice_id: slice_md})


def run(root: Path, *argv: str) -> int:
    return seed.main(["--root", str(root), *argv])


# --- new ---------------------------------------------------------------------

def test_new_scaffolds_task(project: Path, capsys):
    assert run(project, "new", "demo") == 0
    task_dir = project / ".seed" / "tasks" / "demo"
    assert (task_dir / "prd.md").is_file()
    assert (task_dir / "evidence").is_dir()
    assert (task_dir / "notes").is_dir()
    assert (task_dir / "slices" / "S-001.md").is_file()
    assert "# demo" in (task_dir / "prd.md").read_text(encoding="utf-8")
    assert "## 验证" in (task_dir / "slices" / "S-001.md").read_text(encoding="utf-8")


def test_new_scaffold_passes_structure_check(project: Path, capsys):
    assert run(project, "new", "demo") == 0
    capsys.readouterr()
    assert run(project, "status", "demo", "--json") == 0
    data = json.loads(capsys.readouterr().out)
    assert data["errors"] == []


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
    assert data["slices"][0]["file"] == "slices/S-001.md"
    states = {c["target"]: c["state"] for c in data["slices"][0]["checks"]}
    assert states == {"echo hi": "missing"}


def test_status_flags_missing_slice_file(project: Path, capsys):
    make_task(project, slices={"S-001": SLICE_001})  # S-002.md 不存在
    assert run(project, "status", "demo", "--json") == 1
    data = json.loads(capsys.readouterr().out)
    assert any("缺少 slices/S-002.md" in err for err in data["errors"])


def test_status_flags_slice_without_checks(project: Path, capsys):
    slice_md = "# S-001 裸 slice\n\n## 验收\n\nAC-1\n\n## 验证\n"
    single_slice_task(project, "### [ ] S-001 裸 slice", slice_md)
    assert run(project, "status", "demo", "--json") == 1
    data = json.loads(capsys.readouterr().out)
    assert any("缺少验证项" in err for err in data["errors"])


def test_status_flags_missing_acceptance_section(project: Path, capsys):
    slice_md = "# S-001 缺验收\n\n## 验证\n\n- `echo hi`\n"
    single_slice_task(project, "### [ ] S-001 缺验收", slice_md)
    assert run(project, "status", "demo", "--json") == 1
    data = json.loads(capsys.readouterr().out)
    assert any("缺少 `## 验收`" in err for err in data["errors"])


def test_status_accepts_chinese_heading_suffix(project: Path, capsys):
    # `## 验收标准` / `## 验证步骤` 这种自然带后缀的中文标题也必须被识别，
    # 不能只认裸 `## 验收` / `## 验证`（\b 对中文 word char 不生效的回归）。
    slice_md = (
        "# S-001 输出问候\n\n"
        "## 验收标准\n\nAC-1\n\n"
        "## 验证步骤\n\n- `echo hi`\n"
    )
    single_slice_task(project, "### [ ] S-001 输出问候", slice_md)
    assert run(project, "status", "demo", "--json") == 0
    data = json.loads(capsys.readouterr().out)
    assert data["errors"] == []
    states = {c["target"]: c["state"] for c in data["slices"][0]["checks"]}
    assert states == {"echo hi": "missing"}


def test_status_flags_title_mismatch(project: Path, capsys):
    slice_md = "# S-001 另一个标题\n\n## 验收\n\nAC-1\n\n## 验证\n\n- `echo hi`\n"
    single_slice_task(project, "### [ ] S-001 输出问候", slice_md)
    assert run(project, "status", "demo", "--json") == 1
    data = json.loads(capsys.readouterr().out)
    assert any("索引行不一致" in err for err in data["errors"])


def test_status_flags_content_inside_slices_section(project: Path, capsys):
    prd = (
        "# demo\n\n## Slices\n\n"
        "### [ ] S-001 输出问候\n"
        "- 验证:\n"
        "  - `echo hi`\n"
    )
    make_task(project, prd=prd, slices={"S-001": SLICE_001})
    assert run(project, "status", "demo", "--json") == 1
    data = json.loads(capsys.readouterr().out)
    assert any("只放索引行" in err for err in data["errors"])


def test_status_flags_unrecognized_check_item(project: Path, capsys):
    slice_md = "# S-001 输出问候\n\n## 验收\n\nAC-1\n\n## 验证\n\n- 跑一下测试\n"
    single_slice_task(project, "### [ ] S-001 输出问候", slice_md)
    assert run(project, "status", "demo", "--json") == 1
    data = json.loads(capsys.readouterr().out)
    assert any("无法识别" in err for err in data["errors"])


def test_status_flags_duplicate_and_malformed_headings(project: Path, capsys):
    prd = (
        "# demo\n\n## Slices\n\n"
        "### [ ] S-001 第一步\n"
        "### [ ] S-001 第一步\n"
        "### 没有 checkbox 的标题\n"
    )
    slice_md = "# S-001 第一步\n\n## 验收\n\nAC-1\n\n## 验证\n\n- `echo hi`\n"
    make_task(project, prd=prd, slices={"S-001": slice_md})
    assert run(project, "status", "demo", "--json") == 1
    data = json.loads(capsys.readouterr().out)
    assert any("重复的 slice id" in err for err in data["errors"])
    assert any("S-NNN" in err for err in data["errors"])


def test_status_lists_all_tasks(project: Path, capsys):
    make_task(project, "alpha")
    make_task(project, "beta")
    assert run(project, "status") == 0
    out = capsys.readouterr().out
    assert "alpha: 0/2" in out
    assert "beta: 0/2" in out


# --- run-check ---------------------------------------------------------------

def test_run_check_rejects_undeclared_command(project: Path, capsys):
    make_task(project)
    assert run(project, "run-check", "demo", "--slice", "S-001", "--", "echo", "bye") == 1
    err = capsys.readouterr().err
    assert "未声明" in err
    assert "echo hi" in err


def test_run_check_records_passed_evidence(project: Path, capsys):
    make_task(project)
    assert run(project, "run-check", "demo", "--slice", "S-001", "--", "echo", "hi") == 0
    evidence = project / ".seed" / "tasks" / "demo" / "evidence" / "S-001"
    records = sorted(evidence.glob("*.json"))
    assert len(records) == 1
    data = json.loads(records[0].read_text(encoding="utf-8"))
    assert data["command"] == "echo hi"
    assert data["exit_code"] == 0
    assert data["status"] == "passed"
    assert "hi" in (evidence / data["log"]).read_text(encoding="utf-8")


def test_run_check_records_failed_evidence(project: Path, capsys):
    slice_md = "# S-001 失败步\n\n## 验收\n\nAC-1\n\n## 验证\n\n- `false`\n"
    single_slice_task(project, "### [ ] S-001 失败步", slice_md)
    assert run(project, "run-check", "demo", "--slice", "S-001", "--", "false") == 1
    evidence = project / ".seed" / "tasks" / "demo" / "evidence" / "S-001"
    data = json.loads(sorted(evidence.glob("*.json"))[0].read_text(encoding="utf-8"))
    assert data["status"] == "failed"
    assert data["exit_code"] != 0


def test_manual_requires_note_and_evidence(project: Path, capsys):
    make_task(project)
    code = run(project, "run-check", "demo", "--slice", "S-002", "--manual", "浏览器确认页面渲染正常")
    assert code == 1
    assert "--note" in capsys.readouterr().err


def test_manual_must_match_declared_item(project: Path, capsys):
    make_task(project)
    code = run(
        project, "run-check", "demo", "--slice", "S-002",
        "--manual", "随便看看", "--note", "n", "--evidence", "e",
    )
    assert code == 1
    assert "未声明这条 manual" in capsys.readouterr().err


def test_manual_records_evidence(project: Path, capsys):
    make_task(project)
    code = run(
        project, "run-check", "demo", "--slice", "S-002",
        "--manual", "浏览器确认页面渲染正常",
        "--note", "首页渲染正常，无 console error",
        "--evidence", "notes/screenshot-home.png",
    )
    assert code == 0
    evidence = project / ".seed" / "tasks" / "demo" / "evidence" / "S-002"
    data = json.loads(sorted(evidence.glob("*.json"))[0].read_text(encoding="utf-8"))
    assert data["kind"] == "manual"
    assert data["status"] == "recorded"


# --- done --------------------------------------------------------------------

def test_done_blocked_without_evidence(project: Path, capsys):
    make_task(project)
    assert run(project, "done", "demo", "--slice", "S-001") == 1
    err = capsys.readouterr().err
    assert "缺少证据" in err
    assert "echo hi" in err
    prd = (project / ".seed" / "tasks" / "demo" / "prd.md").read_text(encoding="utf-8")
    assert "### [x]" not in prd


def test_done_blocked_by_failed_evidence(project: Path, capsys):
    slice_md = "# S-001 失败步\n\n## 验收\n\nAC-1\n\n## 验证\n\n- `false`\n"
    single_slice_task(project, "### [ ] S-001 失败步", slice_md)
    run(project, "run-check", "demo", "--slice", "S-001", "--", "false")
    assert run(project, "done", "demo", "--slice", "S-001") == 1
    assert "failed" in capsys.readouterr().err


def test_done_flips_checkbox_when_evidence_complete(project: Path, capsys):
    make_task(project)
    run(project, "run-check", "demo", "--slice", "S-001", "--", "echo", "hi")
    assert run(project, "done", "demo", "--slice", "S-001") == 0
    out = capsys.readouterr().out
    assert "next: S-002" in out
    prd = (project / ".seed" / "tasks" / "demo" / "prd.md").read_text(encoding="utf-8")
    assert "### [x] S-001 输出问候" in prd
    assert "### [ ] S-002" in prd


def test_done_requires_manual_recorded(project: Path, capsys):
    make_task(project)
    run(project, "run-check", "demo", "--slice", "S-002", "--", "echo", "step2")
    assert run(project, "done", "demo", "--slice", "S-002") == 1
    assert "manual" in capsys.readouterr().err


def test_done_full_flow_with_manual(project: Path, capsys):
    make_task(project)
    run(project, "run-check", "demo", "--slice", "S-002", "--", "echo", "step2")
    run(
        project, "run-check", "demo", "--slice", "S-002",
        "--manual", "浏览器确认页面渲染正常",
        "--note", "ok", "--evidence", "shot.png",
    )
    assert run(project, "done", "demo", "--slice", "S-002") == 0
    prd = (project / ".seed" / "tasks" / "demo" / "prd.md").read_text(encoding="utf-8")
    assert "### [x] S-002" in prd


def test_done_is_idempotent(project: Path, capsys):
    make_task(project)
    run(project, "run-check", "demo", "--slice", "S-001", "--", "echo", "hi")
    assert run(project, "done", "demo", "--slice", "S-001") == 0
    assert run(project, "done", "demo", "--slice", "S-001") == 0
    assert "已是完成状态" in capsys.readouterr().out


def test_done_unknown_slice(project: Path, capsys):
    make_task(project)
    assert run(project, "done", "demo", "--slice", "S-999") == 1
    assert "不存在" in capsys.readouterr().err


# --- resume ------------------------------------------------------------------

def test_status_resume_after_partial_progress(project: Path, capsys):
    make_task(project)
    run(project, "run-check", "demo", "--slice", "S-001", "--", "echo", "hi")
    run(project, "done", "demo", "--slice", "S-001")
    capsys.readouterr()
    assert run(project, "status", "demo", "--json") == 0
    data = json.loads(capsys.readouterr().out)
    assert data["slices"][0]["done"] is True
    assert data["next"] == "S-002"

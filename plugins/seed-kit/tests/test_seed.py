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

## 交付面

- backend-domain

## 验收

AC-1

## 验证面

- [assert][backend-domain] `test 0 -eq 0`
"""

SLICE_002 = """# S-002 带人工验证的步骤

## 交付面

- backend-domain

## 验收

AC-2

## 验证面

- [assert][backend-domain] `test 0 -eq 0`
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
    task_dir = root / ".arbor" / "tasks" / name
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
    task_dir = project / ".arbor" / "tasks" / "demo"
    assert (task_dir / "prd.md").is_file()
    assert (task_dir / "evidence").is_dir()
    assert (task_dir / "notes").is_dir()
    assert (task_dir / "slices" / "S-001.md").is_file()
    assert "# demo" in (task_dir / "prd.md").read_text(encoding="utf-8")
    slice_text = (task_dir / "slices" / "S-001.md").read_text(encoding="utf-8")
    assert "## 交付面" in slice_text
    assert "## 验证面" in slice_text


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
    assert data["slices"][0]["delivery_surfaces"] == ["backend-domain"]
    states = {c["target"]: c["state"] for c in data["slices"][0]["checks"]}
    assert states == {"test 0 -eq 0": "missing"}
    assert data["slices"][0]["checks"][0]["surfaces"] == ["backend-domain"]


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
        "## 交付面\n\n- backend-domain\n\n"
        "## 验收标准\n\nAC-1\n\n"
        "## 验证步骤\n\n- [assert][backend-domain] `test 0 -eq 0`\n"
    )
    single_slice_task(project, "### [ ] S-001 输出问候", slice_md)
    assert run(project, "status", "demo", "--json") == 0
    data = json.loads(capsys.readouterr().out)
    assert data["errors"] == []
    states = {c["target"]: c["state"] for c in data["slices"][0]["checks"]}
    assert states == {"test 0 -eq 0": "missing"}


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


def test_status_flags_no_recognized_check(project: Path, capsys):
    # a vague, non-check line is tolerated as doc; the slice errors only because
    # it ended up with zero real checks.
    slice_md = "# S-001 输出问候\n\n## 验收\n\nAC-1\n\n## 验证\n\n- 跑一下测试\n"
    single_slice_task(project, "### [ ] S-001 输出问候", slice_md)
    assert run(project, "status", "demo", "--json") == 1
    data = json.loads(capsys.readouterr().out)
    assert any("缺少验证项" in err for err in data["errors"])


def test_status_flags_missing_delivery_surfaces_section(project: Path, capsys):
    slice_md = "# S-001 无交付面\n\n## 验收\n\nAC-1\n\n## 验证面\n\n- [assert][backend-domain] `test 0 -eq 0`\n"
    single_slice_task(project, "### [ ] S-001 无交付面", slice_md)
    assert run(project, "status", "demo", "--json") == 1
    data = json.loads(capsys.readouterr().out)
    assert any("缺少 `## 交付面`" in err for err in data["errors"])


def test_status_flags_unknown_delivery_surface(project: Path, capsys):
    slice_md = (
        "# S-001 坏交付面\n\n## 交付面\n\n- frontend\n\n## 验收\n\nAC-1\n\n## 验证面\n\n"
        "- [judge][web-ui] UI 旅程\n"
    )
    single_slice_task(project, "### [ ] S-001 坏交付面", slice_md)
    assert run(project, "status", "demo", "--json") == 1
    data = json.loads(capsys.readouterr().out)
    assert any("交付面未知：frontend" in err for err in data["errors"])


def test_status_flags_uncovered_delivery_surface(project: Path, capsys):
    slice_md = (
        "# S-001 漏覆盖\n\n## 交付面\n\n- backend-domain\n- api\n\n## 验收\n\nAC-1\n\n## 验证面\n\n"
        "- [assert][backend-domain] `php artisan test --filter=Domain`\n"
    )
    single_slice_task(project, "### [ ] S-001 漏覆盖", slice_md)
    assert run(project, "status", "demo", "--json") == 1
    data = json.loads(capsys.readouterr().out)
    assert any("交付面 api 未被有效验证覆盖" in err for err in data["errors"])


def test_status_accepts_assert_covering_multiple_surfaces(project: Path, capsys):
    slice_md = (
        "# S-001 多面\n\n## 交付面\n\n- backend-domain\n- api\n\n## 验收\n\nAC-1\n\n## 验证面\n\n"
        "- [assert][backend-domain,api] `php artisan test --filter=LedgerApi`\n"
    )
    single_slice_task(project, "### [ ] S-001 多面", slice_md)
    assert run(project, "status", "demo", "--json") == 0
    data = json.loads(capsys.readouterr().out)
    assert data["errors"] == []
    assert data["slices"][0]["checks"][0]["surfaces"] == ["backend-domain", "api"]


def test_status_rejects_human_for_assertable_surface(project: Path, capsys):
    slice_md = (
        "# S-001 降级\n\n## 交付面\n\n- api\n\n## 验收\n\nAC-1\n\n## 验证面\n\n"
        "- [human][api] PM 看过接口正常\n"
    )
    single_slice_task(project, "### [ ] S-001 降级", slice_md)
    assert run(project, "status", "demo", "--json") == 1
    data = json.loads(capsys.readouterr().out)
    assert any("api 需要 [assert][api]" in err for err in data["errors"])


def test_status_rejects_smoke_as_api_coverage(project: Path, capsys):
    slice_md = (
        "# S-001 烟雾覆盖\n\n## 交付面\n\n- api\n\n## 验收\n\nAC-1\n\n## 验证面\n\n"
        "- [assert][api] `curl -s http://localhost/api/foo`\n"
    )
    single_slice_task(project, "### [ ] S-001 烟雾覆盖", slice_md)
    assert run(project, "status", "demo", "--json") == 1
    data = json.loads(capsys.readouterr().out)
    assert any("smoke assert" in err for err in data["errors"])


def test_status_accepts_web_ui_judge(project: Path, capsys):
    slice_md = (
        "# S-001 UI\n\n## 交付面\n\n- web-ui\n\n## 验收\n\nAC-1\n\n## 验证面\n\n"
        "- [judge][web-ui] 登录 UI 旅程，按 rubrics/s-001.md\n"
    )
    single_slice_task(project, "### [ ] S-001 UI", slice_md)
    assert run(project, "status", "demo", "--json") == 0
    data = json.loads(capsys.readouterr().out)
    assert data["errors"] == []


def test_status_accepts_e2e_playwright_assert(project: Path, capsys):
    slice_md = (
        "# S-001 E2E\n\n## 交付面\n\n- e2e\n\n## 验收\n\nAC-1\n\n## 验证面\n\n"
        "- [assert][e2e] `npx playwright test tests/foo.spec.ts`\n"
    )
    single_slice_task(project, "### [ ] S-001 E2E", slice_md)
    assert run(project, "status", "demo", "--json") == 0
    data = json.loads(capsys.readouterr().out)
    assert data["errors"] == []


def test_status_rejects_e2e_non_browser_assert(project: Path, capsys):
    slice_md = (
        "# S-001 假 E2E\n\n## 交付面\n\n- e2e\n\n## 验收\n\nAC-1\n\n## 验证面\n\n"
        "- [assert][e2e] `php artisan test --filter=Foo`\n"
    )
    single_slice_task(project, "### [ ] S-001 假 E2E", slice_md)
    assert run(project, "status", "demo", "--json") == 1
    data = json.loads(capsys.readouterr().out)
    assert any("e2e 需要 Playwright/Cypress/Dusk/e2e" in err for err in data["errors"])


def test_legacy_check_without_surface_does_not_cover_delivery_surface(project: Path, capsys):
    slice_md = "# S-001 legacy\n\n## 交付面\n\n- backend-domain\n\n## 验收\n\nAC-1\n\n## 验证面\n\n- `test 0 -eq 0`\n"
    single_slice_task(project, "### [ ] S-001 legacy", slice_md)
    assert run(project, "status", "demo", "--json") == 1
    data = json.loads(capsys.readouterr().out)
    assert data["slices"][0]["checks"][0]["kind"] == "assert"
    assert data["slices"][0]["checks"][0]["surfaces"] == []
    assert any("交付面 backend-domain 未被有效验证覆盖" in err for err in data["errors"])


def test_assert_allows_trailing_annotation(project: Path, capsys):
    slice_md = (
        "# S-001 问候\n\n## 交付面\n\n- backend-domain\n\n## 验收\n\nAC-1\n\n## 验证面\n\n"
        "- [assert][backend-domain] `test 0 -eq 0` —— 自包含：输出问候，覆盖 AC-1\n"
    )
    single_slice_task(project, "### [ ] S-001 问候", slice_md)
    assert run(project, "status", "demo", "--json") == 0
    data = json.loads(capsys.readouterr().out)
    check = data["slices"][0]["checks"][0]
    assert check["kind"] == "assert"
    assert check["target"] == "test 0 -eq 0"  # annotation ignored for matching
    assert check["surfaces"] == ["backend-domain"]
    # run-check matches on the command, not the annotation
    assert run(project, "run-check", "demo", "--slice", "S-001", "--", "test", "0", "-eq", "0") == 0


def test_verify_section_tolerates_prose_and_subbullets(project: Path, capsys):
    slice_md = (
        "# S-001 多形态\n\n## 交付面\n\n- backend-domain\n- web-ui\n\n## 验收\n\nAC-1\n\n## 验证面\n\n"
        "本 slice 的验证以自包含测试为主，细节见下。\n\n"
        "- [assert][backend-domain] `php artisan test --filter=Foo` —— 覆盖:\n"
        "  - 列表场景\n"
        "  - 流水场景\n"
        "  - 余额断言\n"
        "- [judge][web-ui] UI 旅程，按 rubrics/x.md\n"
    )
    single_slice_task(project, "### [ ] S-001 多形态", slice_md)
    assert run(project, "status", "demo", "--json") == 0
    data = json.loads(capsys.readouterr().out)
    checks = data["slices"][0]["checks"]
    # exactly two checks: the indented sub-bullets and prose are doc, not checks
    assert [(c["kind"]) for c in checks] == ["assert", "judge"]
    assert checks[0]["target"] == "php artisan test --filter=Foo"


def test_assert_tag_without_command_is_broken(project: Path, capsys):
    slice_md = "# S-001 坏\n\n## 验收\n\nAC-1\n\n## 验证\n\n- [assert] 跑一下测试\n"
    single_slice_task(project, "### [ ] S-001 坏", slice_md)
    assert run(project, "status", "demo", "--json") == 1
    data = json.loads(capsys.readouterr().out)
    assert any("声明了 [assert] 但没有 backtick 命令" in err for err in data["errors"])


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
    assert "test 0 -eq 0" in err


def test_run_check_records_passed_evidence(project: Path, capsys):
    make_task(project)
    assert run(project, "run-check", "demo", "--slice", "S-001", "--", "test", "0", "-eq", "0") == 0
    evidence = project / ".arbor" / "tasks" / "demo" / "evidence" / "S-001"
    records = sorted(evidence.glob("*.json"))
    assert len(records) == 1
    data = json.loads(records[0].read_text(encoding="utf-8"))
    assert data["command"] == "test 0 -eq 0"
    assert data["exit_code"] == 0
    assert data["status"] == "passed"


def test_run_check_records_failed_evidence(project: Path, capsys):
    slice_md = "# S-001 失败步\n\n## 交付面\n\n- backend-domain\n\n## 验收\n\nAC-1\n\n## 验证面\n\n- [assert][backend-domain] `false`\n"
    single_slice_task(project, "### [ ] S-001 失败步", slice_md)
    assert run(project, "run-check", "demo", "--slice", "S-001", "--", "false") == 1
    evidence = project / ".arbor" / "tasks" / "demo" / "evidence" / "S-001"
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
    assert "未声明" in capsys.readouterr().err


def test_manual_records_evidence(project: Path, capsys):
    make_task(project)
    code = run(
        project, "run-check", "demo", "--slice", "S-002",
        "--manual", "浏览器确认页面渲染正常",
        "--note", "首页渲染正常，无 console error",
        "--evidence", "notes/screenshot-home.png",
    )
    assert code == 0
    evidence = project / ".arbor" / "tasks" / "demo" / "evidence" / "S-002"
    data = json.loads(sorted(evidence.glob("*.json"))[0].read_text(encoding="utf-8"))
    assert data["kind"] == "human"  # [manual] is a legacy alias for [human]
    assert data["status"] == "recorded"


# --- done --------------------------------------------------------------------

def test_done_blocked_without_evidence(project: Path, capsys):
    make_task(project)
    assert run(project, "done", "demo", "--slice", "S-001") == 1
    err = capsys.readouterr().err
    assert "缺少证据" in err
    assert "test 0 -eq 0" in err
    prd = (project / ".arbor" / "tasks" / "demo" / "prd.md").read_text(encoding="utf-8")
    assert "### [x]" not in prd


def test_done_blocked_by_failed_evidence(project: Path, capsys):
    slice_md = "# S-001 失败步\n\n## 交付面\n\n- backend-domain\n\n## 验收\n\nAC-1\n\n## 验证面\n\n- [assert][backend-domain] `false`\n"
    single_slice_task(project, "### [ ] S-001 失败步", slice_md)
    run(project, "run-check", "demo", "--slice", "S-001", "--", "false")
    assert run(project, "done", "demo", "--slice", "S-001") == 1
    assert "failed" in capsys.readouterr().err


def test_done_flips_checkbox_when_evidence_complete(project: Path, capsys):
    make_task(project)
    run(project, "run-check", "demo", "--slice", "S-001", "--", "test", "0", "-eq", "0")
    assert run(project, "done", "demo", "--slice", "S-001") == 0
    out = capsys.readouterr().out
    assert "next: S-002" in out
    prd = (project / ".arbor" / "tasks" / "demo" / "prd.md").read_text(encoding="utf-8")
    assert "### [x] S-001 输出问候" in prd
    assert "### [ ] S-002" in prd


def test_done_requires_manual_recorded(project: Path, capsys):
    make_task(project)
    run(project, "run-check", "demo", "--slice", "S-002", "--", "test", "0", "-eq", "0")
    assert run(project, "done", "demo", "--slice", "S-002") == 1
    assert "human" in capsys.readouterr().err


def test_done_full_flow_with_manual(project: Path, capsys):
    make_task(project)
    run(project, "run-check", "demo", "--slice", "S-002", "--", "test", "0", "-eq", "0")
    run(
        project, "run-check", "demo", "--slice", "S-002",
        "--manual", "浏览器确认页面渲染正常",
        "--note", "ok", "--evidence", "shot.png",
    )
    assert run(project, "done", "demo", "--slice", "S-002") == 0
    prd = (project / ".arbor" / "tasks" / "demo" / "prd.md").read_text(encoding="utf-8")
    assert "### [x] S-002" in prd


def test_done_is_idempotent(project: Path, capsys):
    make_task(project)
    run(project, "run-check", "demo", "--slice", "S-001", "--", "test", "0", "-eq", "0")
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
    run(project, "run-check", "demo", "--slice", "S-001", "--", "test", "0", "-eq", "0")
    run(project, "done", "demo", "--slice", "S-001")
    capsys.readouterr()
    assert run(project, "status", "demo", "--json") == 0
    data = json.loads(capsys.readouterr().out)
    assert data["slices"][0]["done"] is True
    assert data["next"] == "S-002"


# --- verification kinds (assert / judge / human) ----------------------------

KINDS_SLICE = """# S-001 三类验证

## 交付面

- backend-domain
- web-ui
- compliance

## 验收

AC-1

## 验证面

- [assert][backend-domain] `test 0 -eq 0`
- [judge][web-ui] 注册→登录 UI 旅程，按 rubrics/s-001.md
- [human][compliance] 涉众确认邀请邮件文案
"""


def _latest_record(root: Path, task: str, slice_id: str) -> dict:
    ev = root / ".arbor" / "tasks" / task / "evidence" / slice_id
    return json.loads(sorted(ev.glob("*.json"))[-1].read_text(encoding="utf-8"))


def test_classifies_three_kinds(project: Path, capsys):
    single_slice_task(project, "### [ ] S-001 三类验证", KINDS_SLICE)
    assert run(project, "status", "demo", "--json") == 0
    data = json.loads(capsys.readouterr().out)
    checks = data["slices"][0]["checks"]
    assert [c["kind"] for c in checks] == ["assert", "judge", "human"]
    assert [c["surfaces"] for c in checks] == [["backend-domain"], ["web-ui"], ["compliance"]]
    assert all(c["state"] == "missing" for c in checks)


def test_assert_prefix_runs_command(project: Path, capsys):
    single_slice_task(project, "### [ ] S-001 三类验证", KINDS_SLICE)
    assert run(project, "run-check", "demo", "--slice", "S-001", "--", "test", "0", "-eq", "0") == 0
    rec = _latest_record(project, "demo", "S-001")
    assert rec["kind"] == "assert"
    assert rec["status"] == "passed"


def test_judge_pass_records_verdict(project: Path, capsys):
    single_slice_task(project, "### [ ] S-001 三类验证", KINDS_SLICE)
    code = run(
        project, "run-check", "demo", "--slice", "S-001",
        "--judge", "注册→登录 UI 旅程，按 rubrics/s-001.md",
        "--verdict", "pass",
        "--trace", "rubrics/s-001.md + shots/login.png",
        "--by", "judge-agent-2",
    )
    assert code == 0
    rec = _latest_record(project, "demo", "S-001")
    assert rec["kind"] == "judge"
    assert rec["verdict"] == "pass"
    assert rec["status"] == "passed"
    assert rec["by"] == "judge-agent-2"


def test_judge_requires_verdict_and_trace(project: Path, capsys):
    single_slice_task(project, "### [ ] S-001 三类验证", KINDS_SLICE)
    assert run(
        project, "run-check", "demo", "--slice", "S-001",
        "--judge", "注册→登录 UI 旅程，按 rubrics/s-001.md",
    ) == 1
    assert "--verdict" in capsys.readouterr().err


def test_judge_fail_blocks_done(project: Path, capsys):
    single_slice_task(project, "### [ ] S-001 三类验证", KINDS_SLICE)
    run(project, "run-check", "demo", "--slice", "S-001", "--", "test", "0", "-eq", "0")
    run(project, "run-check", "demo", "--slice", "S-001", "--human",
        "涉众确认邀请邮件文案", "--note", "ok")
    run(
        project, "run-check", "demo", "--slice", "S-001",
        "--judge", "注册→登录 UI 旅程，按 rubrics/s-001.md",
        "--verdict", "fail", "--trace", "rubrics/s-001.md；按钮无障碍失败",
    )
    assert run(project, "done", "demo", "--slice", "S-001") == 1
    err = capsys.readouterr().err
    assert "judge" in err and "failed" in err
    prd = (project / ".arbor" / "tasks" / "demo" / "prd.md").read_text(encoding="utf-8")
    assert "### [x]" not in prd


def test_human_signoff_satisfies_gate(project: Path, capsys):
    single_slice_task(project, "### [ ] S-001 三类验证", KINDS_SLICE)
    run(project, "run-check", "demo", "--slice", "S-001", "--", "test", "0", "-eq", "0")
    run(
        project, "run-check", "demo", "--slice", "S-001",
        "--judge", "注册→登录 UI 旅程，按 rubrics/s-001.md",
        "--verdict", "pass", "--trace", "rubrics/s-001.md",
    )
    assert run(
        project, "run-check", "demo", "--slice", "S-001", "--human",
        "涉众确认邀请邮件文案", "--note", "文案定稿", "--by", "PM-alice",
    ) == 0
    assert run(project, "done", "demo", "--slice", "S-001") == 0
    prd = (project / ".arbor" / "tasks" / "demo" / "prd.md").read_text(encoding="utf-8")
    assert "### [x] S-001 三类验证" in prd


# --- smoke detection ---------------------------------------------------------

def test_smoke_detection():
    assert seed.looks_like_smoke("curl -s http://localhost:8000/api/health")[0] is True
    assert seed.looks_like_smoke("curl -sf http://x")[0] is False
    assert seed.looks_like_smoke("curl -s http://x | grep ok")[0] is False
    assert seed.looks_like_smoke("echo hi")[0] is True
    assert seed.looks_like_smoke("true")[0] is True
    assert seed.looks_like_smoke("php artisan test --filter=Ledger")[0] is False
    assert seed.looks_like_smoke("test 0 -eq 0")[0] is False


def test_run_check_warns_on_smoke(project: Path, capsys):
    slice_md = (
        "# S-001 烟雾\n\n## 交付面\n\n- compliance\n\n## 验收\n\nAC\n\n## 验证面\n\n"
        "- [human][compliance] 涉众签收\n"
        "- `echo hi`\n"
    )
    single_slice_task(project, "### [ ] S-001 烟雾", slice_md)
    assert run(project, "run-check", "demo", "--slice", "S-001", "--", "echo", "hi") == 0
    captured = capsys.readouterr()
    assert "烟雾警告" in captured.err
    assert "不构成有效验证" in captured.err


def test_status_flags_smoke_in_report(project: Path, capsys):
    slice_md = (
        "# S-001 烟雾\n\n## 交付面\n\n- compliance\n\n## 验收\n\nAC\n\n## 验证面\n\n"
        "- [human][compliance] 涉众签收\n"
        "- `curl -s http://localhost:8000/health`\n"
    )
    single_slice_task(project, "### [ ] S-001 烟雾", slice_md)
    assert run(project, "status", "demo", "--json") == 0
    data = json.loads(capsys.readouterr().out)
    assert data["slices"][0]["checks"][1]["smoke"] is True

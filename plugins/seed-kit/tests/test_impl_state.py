"""impl-agent 编排锚点 + 纯推导 next-action 的 CLI 合同测试。

设计合同：
- 没有 phase 状态机——进度 SoT 是 PRD checkbox，失败次数从 gate-attempts/ 数出来。
- impl-state.json 只存推导不出来的东西：task_start_sha（写一次即锁死）+ 单 slice 目标。
- `seed done` 失败留痕到 gate-attempts/（与 done-logs/ 分开，客观锚只重放成功记录）。
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import seed  # noqa: E402


PRD = """# demo

## Goal

impl-state 测试用 PRD。

## Acceptance Criteria

### [ ] S-001 第一步
* [ ] 用例一

### [ ] S-002 第二步
* [ ] 用例二

## Out of Scope
"""


@pytest.fixture
def project(tmp_path: Path) -> Path:
    task_dir = tmp_path / ".arbor" / "tasks" / "demo"
    task_dir.mkdir(parents=True)
    (task_dir / "prd.md").write_text(PRD, encoding="utf-8")
    return tmp_path


def run(root: Path, *argv: str) -> int:
    return seed.main(["--root", str(root), *argv])


def state_path(root: Path) -> Path:
    return root / ".arbor" / "tasks" / "demo" / "impl-state.json"


def read_state(root: Path) -> dict:
    return json.loads(state_path(root).read_text(encoding="utf-8"))


def prd_file(root: Path) -> Path:
    return root / ".arbor" / "tasks" / "demo" / "prd.md"


def attempts_dir(root: Path) -> Path:
    return root / ".arbor" / "tasks" / "demo" / "gate-attempts"


def git_init_commit(root: Path) -> str:
    subprocess.run(["git", "init", "-b", "main"], cwd=root, capture_output=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=root, capture_output=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=root, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=root, capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=root, capture_output=True)
    out = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True)
    return out.stdout.strip()


def check_slice(root: Path, slice_id: str) -> None:
    """模拟 seed done 翻 checkbox（直接改文件，不跑 gate）。"""
    text = prd_file(root).read_text(encoding="utf-8")
    prd_file(root).write_text(
        text.replace(f"### [ ] {slice_id}", f"### [x] {slice_id}"), encoding="utf-8"
    )


def fake_attempts(root: Path, slice_id: str, n: int) -> None:
    """按 seed done 失败留痕的命名规则伪造 n 条失败记录（接着已有序号续号）。"""
    directory = attempts_dir(root)
    directory.mkdir(parents=True, exist_ok=True)
    existing = len(list(directory.glob(f"*-{slice_id}-*.json")))
    for i in range(existing + 1, existing + n + 1):
        payload = {"slice": slice_id, "result": "fail", "failed_stage": "test"}
        (directory / f"{i:03d}-{slice_id}-2026.json").write_text(
            json.dumps(payload), encoding="utf-8"
        )


def next_action(root: Path, capsys) -> dict:
    capsys.readouterr()
    assert run(root, "next-action", "demo") == 0
    return json.loads(capsys.readouterr().out)


# --- init / 锚点 --------------------------------------------------------------

def test_init_creates_anchor_without_phase(project: Path):
    assert run(project, "impl-state", "init", "demo") == 0
    state = read_state(project)
    assert "task_start_sha" in state
    assert len(state["prd_sha256"]) == 64
    assert state["target_slice"] is None
    assert "phase" not in state
    assert "attempt_count" not in state


def test_init_records_task_start_sha_in_git_repo(project: Path):
    sha = git_init_commit(project)
    assert run(project, "impl-state", "init", "demo") == 0
    state = read_state(project)
    assert state["task_start_sha"] == sha
    assert Path(state["git_root"]).resolve() == project.resolve()


def test_task_start_sha_survives_reinit_after_checkbox_flip(project: Path):
    """守门测试：checkbox 翻转（工作流自己的动作）+ 新 commit 后 re-init，锚点必须不变。

    这是中断恢复的核心承诺——re-init 重算锚点会让集成 review 漏审中断前的全部 commit。
    """
    sha = git_init_commit(project)
    assert run(project, "impl-state", "init", "demo") == 0
    check_slice(project, "S-001")
    subprocess.run(["git", "add", "."], cwd=project, capture_output=True)
    subprocess.run(["git", "commit", "-m", "feat(demo): S-001"], cwd=project, capture_output=True)
    assert run(project, "impl-state", "init", "demo") == 0
    assert read_state(project)["task_start_sha"] == sha


def test_checkbox_flip_does_not_change_prd_fingerprint(project: Path, capsys):
    assert run(project, "impl-state", "init", "demo") == 0
    before = read_state(project)["prd_sha256"]
    check_slice(project, "S-001")
    capsys.readouterr()
    assert run(project, "impl-state", "init", "demo") == 0
    assert "PRD 内容有变化" not in capsys.readouterr().out
    assert read_state(project)["prd_sha256"] == before


def test_real_prd_change_warns_but_keeps_anchor(project: Path, capsys):
    sha = git_init_commit(project)
    assert run(project, "impl-state", "init", "demo") == 0
    text = prd_file(project).read_text(encoding="utf-8")
    prd_file(project).write_text(text.replace("用例二", "用例二改了需求"), encoding="utf-8")
    capsys.readouterr()
    assert run(project, "impl-state", "init", "demo") == 0
    assert "PRD 内容有变化" in capsys.readouterr().out
    assert read_state(project)["task_start_sha"] == sha


def test_init_rejects_unknown_target_slice(project: Path, capsys):
    assert run(project, "impl-state", "init", "demo", "--slice", "S-999") == 1
    assert "不存在" in capsys.readouterr().err


def test_show_reports_missing_state(project: Path, capsys):
    assert run(project, "impl-state", "show", "demo") == 0
    assert "no impl-state" in capsys.readouterr().out


# --- next-action：纯推导 ------------------------------------------------------

def test_next_action_suggests_init_without_state(project: Path, capsys):
    data = next_action(project, capsys)
    assert data["action"] == "init_impl_state"
    assert data["next_slice"] == "S-001"


def test_next_action_noop_when_all_done_without_state(project: Path, capsys):
    check_slice(project, "S-001")
    check_slice(project, "S-002")
    data = next_action(project, capsys)
    assert data["action"] == "noop"


def test_next_action_dispatches_next_unchecked_slice(project: Path, capsys):
    assert run(project, "impl-state", "init", "demo") == 0
    data = next_action(project, capsys)
    assert data["action"] == "start_slice"
    assert data["next_slice"] == "S-001"
    assert data["attempt_count"] == 0
    check_slice(project, "S-001")
    data = next_action(project, capsys)
    assert data["next_slice"] == "S-002"
    assert "handoff" in data["dispatch"]


def test_next_action_derives_attempts_and_circuit_breaks(project: Path, capsys):
    assert run(project, "impl-state", "init", "demo") == 0
    fake_attempts(project, "S-001", 2)
    data = next_action(project, capsys)
    assert data["action"] == "start_slice"
    assert data["attempt_count"] == 2
    fake_attempts(project, "S-001", 1)  # 第 3 条,触发熔断阈值
    data = next_action(project, capsys)
    assert data["action"] == "escalate"
    assert "reset-attempts" in data["hint"]


def test_next_action_integration_review_when_all_done(project: Path, capsys):
    sha = git_init_commit(project)
    assert run(project, "impl-state", "init", "demo") == 0
    check_slice(project, "S-001")
    check_slice(project, "S-002")
    data = next_action(project, capsys)
    assert data["action"] == "integration_review"
    assert data["diff_range"] == f"{sha}..HEAD"
    assert "review-loop" not in data["dispatch"].split("；")[0]  # 收口是集成 review，review-loop 只是兜底


def test_next_action_degrades_without_git_anchor(project: Path, capsys):
    assert run(project, "impl-state", "init", "demo") == 0
    check_slice(project, "S-001")
    check_slice(project, "S-002")
    data = next_action(project, capsys)
    assert data["action"] == "integration_review"
    assert data["diff_range"] is None
    assert "降级" in data["note"]


def test_single_slice_mode_targets_named_slice(project: Path, capsys):
    assert run(project, "impl-state", "init", "demo", "--slice", "S-002") == 0
    data = next_action(project, capsys)
    assert data["action"] == "start_slice"
    assert data["next_slice"] == "S-002"  # 不派 S-001
    check_slice(project, "S-002")
    data = next_action(project, capsys)
    assert data["action"] == "finish"
    assert "集成 review" in data["note"]


# --- gate-attempts：seed done 失败留痕 ----------------------------------------

def test_done_failure_writes_gate_attempt_not_done_log(project: Path, capsys):
    (project / "fail.py").write_text("raise SystemExit(1)\n", encoding="utf-8")
    assert run(project, "done", "demo", "--slice", "S-001", "--test", "python3 fail.py") == 1
    files = list(attempts_dir(project).glob("*.json"))
    assert len(files) == 1
    record = json.loads(files[0].read_text(encoding="utf-8"))
    assert record["result"] == "fail"
    assert record["failed_stage"] == "test"
    assert not (project / ".arbor" / "tasks" / "demo" / "done-logs").exists()
    assert "### [x]" not in prd_file(project).read_text(encoding="utf-8")


def test_done_quality_failure_also_leaves_attempt(project: Path, capsys):
    (project / "ok.py").write_text("raise SystemExit(0)\n", encoding="utf-8")
    (project / "fail.py").write_text("raise SystemExit(1)\n", encoding="utf-8")
    assert run(project, "done", "demo", "--slice", "S-001",
               "--test", "python3 ok.py", "--quality", "python3 fail.py") == 1
    files = list(attempts_dir(project).glob("*.json"))
    assert len(files) == 1
    assert json.loads(files[0].read_text(encoding="utf-8"))["failed_stage"] == "quality"


def test_done_success_writes_done_log_without_attempt(project: Path, capsys):
    (project / "ok.py").write_text("raise SystemExit(0)\n", encoding="utf-8")
    assert run(project, "done", "demo", "--slice", "S-001", "--test", "python3 ok.py") == 0
    assert not attempts_dir(project).exists()
    done_logs = list((project / ".arbor" / "tasks" / "demo" / "done-logs").glob("*.json"))
    assert len(done_logs) == 1


def test_noop_rejection_does_not_count_as_attempt(project: Path, capsys):
    assert run(project, "done", "demo", "--slice", "S-001", "--test", "true") == 1
    assert not attempts_dir(project).exists()


def test_reset_attempts_zeroes_count_and_keeps_history(project: Path, capsys):
    assert run(project, "impl-state", "init", "demo") == 0
    fake_attempts(project, "S-001", 3)
    data = next_action(project, capsys)
    assert data["action"] == "escalate"
    assert run(project, "impl-state", "reset-attempts", "demo", "--slice", "S-001") == 0
    assert len(list((attempts_dir(project) / "superseded").glob("*.json"))) == 3
    data = next_action(project, capsys)
    assert data["action"] == "start_slice"
    assert data["attempt_count"] == 0


# --- 边界：不碰 checkbox ------------------------------------------------------

def test_state_commands_do_not_touch_checkbox(project: Path):
    """锚点/留痕命令只是编排辅助：任何 init/reset 都不得改 PRD checkbox。"""
    fake_attempts(project, "S-001", 3)
    assert run(project, "impl-state", "init", "demo") == 0
    assert run(project, "impl-state", "reset-attempts", "demo", "--slice", "S-001") == 0
    assert "### [x]" not in prd_file(project).read_text(encoding="utf-8")

"""任务档案（dossier）：锚点 + handoff + 证据指针 的 CLI 合同测试。

设计合同：
- 没有 phase 状态机——进度 SoT 是 PRD checkbox，失败次数从 gate-attempts/ 数出来。
- impl-state.json 是任务档案：task_start_sha（写一次即锁死）+ 单 slice 目标 +
  每 slice handoff（`seed handoff add`）+ 证据指针（`seed done --evidence-*`）。
- 写序：done-log 与 dossier 先于 checkbox 翻转——中断最坏态是"有证据未勾选"，
  永不出"已勾选无证据"。
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


# --- status 吸收编排派生（原 next-action）--------------------------------------

def status_json(root: Path, capsys) -> dict:
    capsys.readouterr()
    assert run(root, "status", "demo", "--json") == 0
    return json.loads(capsys.readouterr().out)


def test_status_reports_gate_failures_and_circuit_break(project: Path, capsys):
    assert run(project, "impl-state", "init", "demo") == 0
    fake_attempts(project, "S-001", 2)
    data = status_json(project, capsys)
    by_id = {s["id"]: s for s in data["slices"]}
    assert by_id["S-001"]["gate_failures"] == 2
    assert data["circuit_broken"] == []
    fake_attempts(project, "S-001", 1)  # 第 3 条 → 熔断
    data = status_json(project, capsys)
    assert data["circuit_broken"] == ["S-001"]
    assert data["next"] == "S-001"
    capsys.readouterr()
    assert run(project, "status", "demo") == 0
    out = capsys.readouterr().out
    assert "熔断" in out and "reset-attempts" in out


def test_status_reports_anchor_and_dossier_presence(project: Path, capsys):
    sha = git_init_commit(project)
    assert run(project, "impl-state", "init", "demo") == 0
    assert run(project, "handoff", "add", "demo", "--slice", "S-001", "--note", "接口语义 X") == 0
    data = status_json(project, capsys)
    assert data["task_start_sha"] == sha
    by_id = {s["id"]: s for s in data["slices"]}
    assert by_id["S-001"]["handoff"] == 1
    assert by_id["S-001"]["evidence"] is False
    capsys.readouterr()
    assert run(project, "status", "demo") == 0
    assert "锚点" in capsys.readouterr().out


def test_status_without_dossier_degrades_cleanly(project: Path, capsys):
    data = status_json(project, capsys)
    assert data["task_start_sha"] is None
    assert data["next"] == "S-001"
    assert all(s["gate_failures"] == 0 and s["handoff"] == 0 for s in data["slices"])
    capsys.readouterr()
    assert run(project, "status", "demo") == 0
    assert "无锚点" in capsys.readouterr().out


def test_single_slice_mode_targets_named_slice(project: Path, capsys):
    assert run(project, "impl-state", "init", "demo", "--slice", "S-002") == 0
    data = status_json(project, capsys)
    assert data["target_slice"] == "S-002"
    check_slice(project, "S-002")
    data = status_json(project, capsys)
    assert data["next"] is None  # 单 slice 模式目标已完成


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
    assert status_json(project, capsys)["circuit_broken"] == ["S-001"]
    assert run(project, "impl-state", "reset-attempts", "demo", "--slice", "S-001") == 0
    assert len(list((attempts_dir(project) / "superseded").glob("*.json"))) == 3
    data = status_json(project, capsys)
    assert data["circuit_broken"] == []
    assert {s["id"]: s for s in data["slices"]}["S-001"]["gate_failures"] == 0


# --- 边界：不碰 checkbox ------------------------------------------------------

def test_state_commands_do_not_touch_checkbox(project: Path):
    """档案/留痕命令只是协作辅助：任何 init/reset/handoff 都不得改 PRD checkbox。"""
    fake_attempts(project, "S-001", 3)
    assert run(project, "impl-state", "init", "demo") == 0
    assert run(project, "impl-state", "reset-attempts", "demo", "--slice", "S-001") == 0
    assert run(project, "handoff", "add", "demo", "--slice", "S-001", "--note", "x") == 0
    assert "### [x]" not in prd_file(project).read_text(encoding="utf-8")


# --- dossier：handoff / evidence / 写序 ---------------------------------------

def _pass_test_setup(root: Path) -> None:
    (root / "test.js").write_text(
        "const {test} = require('node:test');\ntest('passes', () => {});\n",
        encoding="utf-8",
    )


def test_handoff_add_appends_cumulatively(project: Path):
    run(project, "impl-state", "init", "demo")
    assert run(project, "handoff", "add", "demo", "--slice", "S-001",
               "--note", "create_order() 返回 {status:'pending'}") == 0
    assert run(project, "handoff", "add", "demo", "--slice", "S-001",
               "--note", "回调必须查 pending 才放行") == 0
    state = read_state(project)
    assert state["slices"]["S-001"]["handoff"] == [
        "create_order() 返回 {status:'pending'}",
        "回调必须查 pending 才放行",
    ]
    # 锚点字段不受 handoff 写入影响
    assert "task_start_sha" in state


def test_handoff_add_rejects_unknown_slice_and_requires_dossier(project: Path, capsys):
    run(project, "impl-state", "init", "demo")
    assert run(project, "handoff", "add", "demo", "--slice", "S-999", "--note", "x") == 1
    assert run(project, "handoff", "add", "demo", "--slice", "S-001", "--note", "  ") == 1
    # 无档案（未 init）时拒绝并提示入口，不隐式创建
    bare = project.parent / "bare"
    (bare / ".arbor" / "tasks" / "demo").mkdir(parents=True)
    (bare / ".arbor" / "tasks" / "demo" / "prd.md").write_text(PRD, encoding="utf-8")
    assert run(bare, "handoff", "add", "demo", "--slice", "S-001", "--note", "x") == 1
    assert "impl-state init" in capsys.readouterr().err
    assert not (bare / ".arbor" / "tasks" / "demo" / "impl-state.json").exists()


def test_done_writes_evidence_to_dossier_not_done_log(project: Path):
    git_init_commit(project)
    run(project, "impl-state", "init", "demo")
    _pass_test_setup(project)
    rc = run(project, "done", "demo", "--slice", "S-001", "--test", "node --test test.js",
             "--evidence-file", "evidence/S-001-01-stroke.png",
             "--evidence-file", "evidence/S-001-02-detail.png",
             "--evidence-url", "http://localhost:5173")
    assert rc == 0
    ev = read_state(project)["slices"]["S-001"]["evidence"]
    assert ev["files"] == ["evidence/S-001-01-stroke.png", "evidence/S-001-02-detail.png"]
    assert ev["artifact"] == {"url": "http://localhost:5173"}
    assert ev["commit"]  # git 仓库中记录验证时 HEAD
    # done-log 仍是纯机器验证流水，不携带证据
    log_file = next((project / ".arbor" / "tasks" / "demo" / "done-logs").glob("*S-001*.json"))
    assert "evidence" not in log_file.read_text(encoding="utf-8")


def test_done_write_order_log_and_dossier_precede_checkbox(project: Path, monkeypatch):
    """中断安全合同：prd 写入（翻 checkbox）失败时，done-log 与 dossier 已在盘上；
    反向（勾了但无证据）结构性不可能。"""
    git_init_commit(project)
    run(project, "impl-state", "init", "demo")
    _pass_test_setup(project)
    real_write_text = Path.write_text

    def crash_before_flip(self, *args, **kwargs):
        if self.name == "prd.md":
            raise OSError("simulated crash before checkbox flip")
        return real_write_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", crash_before_flip)
    with pytest.raises(OSError):
        run(project, "done", "demo", "--slice", "S-001", "--test", "node --test test.js",
            "--evidence-file", "evidence/x.png")
    monkeypatch.undo()

    assert "### [x]" not in prd_file(project).read_text(encoding="utf-8")  # 未翻
    assert list((project / ".arbor" / "tasks" / "demo" / "done-logs").glob("*S-001*.json"))
    assert read_state(project)["slices"]["S-001"]["evidence"]["files"] == ["evidence/x.png"]


def test_reinit_preserves_dossier_slices(project: Path):
    """re-init 只重申锚点字段，不得清空已累积的 handoff/evidence（dossier 是交接资产）。"""
    assert run(project, "impl-state", "init", "demo") == 0
    assert run(project, "handoff", "add", "demo", "--slice", "S-001", "--note", "接口语义 X") == 0
    state = read_state(project)
    state.setdefault("slices", {})["S-001"] = {**state["slices"]["S-001"],
                                               "evidence": {"files": ["e/a.png"], "artifact": {}, "commit": None}}
    state_path(project).write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
    assert run(project, "impl-state", "init", "demo") == 0
    after = read_state(project)
    assert after["slices"]["S-001"]["handoff"] == ["接口语义 X"]
    assert after["slices"]["S-001"]["evidence"]["files"] == ["e/a.png"]

"""review_gate hook 的单元测试：seed done 的 review-loop 收敛硬 gate。"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HOOK_SCRIPT = Path(__file__).resolve().parents[1] / "hooks" / "review_gate.py"


def run_hook(payload: dict) -> tuple[int, str]:
    """运行 hook，返回 (returncode, stderr)。block 时 returncode=2、stderr 有 reason。"""
    result = subprocess.run(
        [sys.executable, str(HOOK_SCRIPT)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stderr


def _task_dir(tmp_path: Path) -> Path:
    d = tmp_path / ".arbor" / "tasks" / "demo"
    (d / "evidence").mkdir(parents=True)
    return d


def _prd(task_dir: Path, slice_line: str = "### [ ] S-001 输出问候") -> None:
    (task_dir / "prd.md").write_text(f"# demo\n\n## Slices\n\n{slice_line}\n", encoding="utf-8")


def _marker(task_dir: Path, slice_id: str, terminal_reason: str) -> None:
    d = task_dir / "evidence" / slice_id
    d.mkdir(parents=True, exist_ok=True)
    (d / "review-loop.json").write_text(
        json.dumps({"terminal_reason": terminal_reason, "converged": terminal_reason == "converged"}),
        encoding="utf-8",
    )


def test_non_bash_allowed():
    code, _ = run_hook({"tool_name": "Edit", "tool_input": {"file_path": "/x.py"}})
    assert code == 0


def test_bash_without_seed_done_allowed():
    code, _ = run_hook({"tool_name": "Bash", "tool_input": {"command": "echo hi"}})
    assert code == 0


def test_seed_done_without_marker_blocked(tmp_path: Path):
    td = _task_dir(tmp_path)
    _prd(td)
    code, err = run_hook({
        "tool_name": "Bash",
        "tool_input": {"command": "seed done demo --slice S-001"},
        "cwd": str(tmp_path),
    })
    assert code == 2
    assert "review-loop 未收敛" in err
    assert "S-001" in err
    assert "review-mark" in err  # 给出可执行下一步


def test_seed_done_non_converged_marker_blocked(tmp_path: Path):
    td = _task_dir(tmp_path)
    _prd(td)
    _marker(td, "S-001", "circuit-breaker")
    code, err = run_hook({
        "tool_name": "Bash",
        "tool_input": {"command": "seed done demo --slice S-001"},
        "cwd": str(tmp_path),
    })
    assert code == 2
    assert "circuit-breaker" in err


def test_seed_done_converged_marker_allowed(tmp_path: Path):
    td = _task_dir(tmp_path)
    _prd(td)
    _marker(td, "S-001", "converged")
    code, _ = run_hook({
        "tool_name": "Bash",
        "tool_input": {"command": "seed done demo --slice S-001"},
        "cwd": str(tmp_path),
    })
    assert code == 0


def test_seed_done_already_checked_slice_allowed(tmp_path: Path):
    # 已 [x] 的 slice 无需再 gate（幂等重跑 / 老任务迁移）
    td = _task_dir(tmp_path)
    _prd(td, slice_line="### [x] S-001 输出问候")
    code, _ = run_hook({
        "tool_name": "Bash",
        "tool_input": {"command": "seed done demo --slice S-001"},
        "cwd": str(tmp_path),
    })
    assert code == 0


def test_malformed_payload_allowed():
    code, _ = run_hook({"tool_name": "Bash", "tool_input": {"command": "seed done demo"}})
    assert code == 0  # 缺 --slice，DONE_RE 不匹配 → allow

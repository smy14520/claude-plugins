import json
import subprocess
import sys
from pathlib import Path

import pytest

TOOL_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOL_DIR))

from forge import (
    ForgeError,
    cmd_new,
    cmd_status,
    get_task_handoffs,
    get_task_seams,
    read_state,
    spec_path,
    write_state,
)


@pytest.fixture
def tmp_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    return repo


def test_new_task_creates_directory_and_state(tmp_repo: Path):
    cmd_new(tmp_repo, "user-auth", "用户鉴权功能")

    task_dir = tmp_repo / ".forge" / "tasks" / "user-auth"
    assert task_dir.is_dir()
    assert (task_dir / "handoffs").is_dir()

    st = read_state(tmp_repo, "user-auth")
    assert st.slug == "user-auth"
    assert st.title == "用户鉴权功能"
    assert st.phase == "ALIGN"

    # Verify spec.md created
    spec_file = task_dir / "spec.md"
    assert spec_file.is_file()
    assert "用户鉴权功能" in spec_file.read_text(encoding="utf-8")


def test_invalid_slug_rejected(tmp_repo: Path):
    with pytest.raises(ForgeError, match="无效的任务名"):
        cmd_new(tmp_repo, "Bad Task Name!", "Title")


def test_duplicate_task_rejected(tmp_repo: Path):
    cmd_new(tmp_repo, "t1", "Task 1")
    with pytest.raises(ForgeError, match="已经存在"):
        cmd_new(tmp_repo, "t1", "Task 1 again")


def test_status_dynamic_derivation(tmp_repo: Path):
    cmd_new(tmp_repo, "demo-task", "演示任务")

    # 动态验证：在 spec.md 中添加深接缝，无需任何 CLI 中间商
    spec_file = spec_path(tmp_repo, "demo-task")
    content = spec_file.read_text(encoding="utf-8")
    content += "\n## Agreed Seams\n- **Seam 1**: `AuthService.login(user, pass) -> Token`\n"
    spec_file.write_text(content, encoding="utf-8")

    seams = get_task_seams(tmp_repo, "demo-task")
    assert len(seams) == 1
    assert "AuthService.login" in seams[0]

    # 动态验证：在 handoffs 写入文件，自动识别
    hfile = tmp_repo / ".forge" / "tasks" / "demo-task" / "handoffs" / "01-align.md"
    hfile.write_text("# Handoff: ALIGN\n", encoding="utf-8")

    handoffs = get_task_handoffs(tmp_repo, "demo-task")
    assert handoffs == ["01-align.md"]

    # 验证原生更新 phase
    st = read_state(tmp_repo, "demo-task")
    st.phase = "IMPLEMENT"
    write_state(tmp_repo, st)
    assert read_state(tmp_repo, "demo-task").phase == "IMPLEMENT"


def test_cli_executable(tmp_repo: Path):
    forge_bin = Path(__file__).resolve().parents[1] / "bin" / "forge"
    res = subprocess.run([str(forge_bin), "root"], capture_output=True, text=True, cwd=tmp_repo)
    assert res.returncode == 0
    assert "tinder-kit" in res.stdout

    # Test status CLI
    cmd_new(tmp_repo, "cli-task", "CLI 测试")
    res_status = subprocess.run([str(forge_bin), "status", "cli-task"], capture_output=True, text=True, cwd=tmp_repo)
    assert res_status.returncode == 0
    assert "cli-task" in res_status.stdout

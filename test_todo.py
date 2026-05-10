"""pytest 单测 — todo.py CLI 工具"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

TODO_PY = str(Path(__file__).parent / "todo.py")


@pytest.fixture(autouse=True)
def isolated_data_dir(tmp_path, monkeypatch):
    """每个测试使用独立的临时数据目录。"""
    data_dir = tmp_path / ".todo"
    data_file = data_dir / "tasks.json"
    # Patch todo.py 的 DATA_DIR / DATA_FILE
    monkeypatch.setenv("HOME", str(tmp_path))
    return data_dir, data_file


def run_todo(*args, home=None):
    """运行 todo.py 并返回 (returncode, stdout, stderr)。"""
    env = None
    if home:
        import os
        env = {**os.environ, "HOME": str(home)}
    result = subprocess.run(
        [sys.executable, TODO_PY, *args],
        capture_output=True,
        text=True,
        env=env,
    )
    return result.returncode, result.stdout, result.stderr


def run_todo_isolated(tmp_path, *args):
    """用 tmp_path 作为 HOME 运行 todo.py。"""
    return run_todo(*args, home=tmp_path)


# --- S-001: 数据层 ---


class TestDataLayer:
    def test_load_empty(self, tmp_path):
        """文件不存在时 list 返回空（无报错）。"""
        rc, stdout, stderr = run_todo_isolated(tmp_path, "list")
        assert rc == 0
        assert "没有任务" in stdout

    def test_save_and_load(self, tmp_path):
        """add 后 list 能看到任务。"""
        rc, stdout, _ = run_todo_isolated(tmp_path, "add", "测试任务")
        assert rc == 0
        assert "#1" in stdout

        rc, stdout, _ = run_todo_isolated(tmp_path, "list")
        assert rc == 0
        assert "测试任务" in stdout

    def test_corrupt_json(self, tmp_path):
        """JSON 损坏时给出错误提示并退出非零码。"""
        data_dir = tmp_path / ".todo"
        data_dir.mkdir(parents=True)
        (data_dir / "tasks.json").write_text("not valid json{{{", encoding="utf-8")

        rc, stdout, stderr = run_todo_isolated(tmp_path, "list")
        assert rc != 0
        assert "错误" in stderr or "损坏" in stderr


# --- S-002: add 命令 ---


class TestAdd:
    def test_add_success(self, tmp_path):
        """正常添加任务。"""
        rc, stdout, _ = run_todo_isolated(tmp_path, "add", "买牛奶")
        assert rc == 0
        assert "Added task #1" in stdout
        assert "买牛奶" in stdout

        # 验证 JSON 内容
        data = json.loads((tmp_path / ".todo" / "tasks.json").read_text())
        assert len(data["tasks"]) == 1
        task = data["tasks"][0]
        assert task["id"] == 1
        assert task["description"] == "买牛奶"
        assert task["done"] is False
        assert "created_at" in task

    def test_add_increments_id(self, tmp_path):
        """连续添加 ID 自增。"""
        run_todo_isolated(tmp_path, "add", "任务一")
        rc, stdout, _ = run_todo_isolated(tmp_path, "add", "任务二")
        assert rc == 0
        assert "#2" in stdout

    def test_add_empty_rejected(self, tmp_path):
        """空字符串被拒绝。"""
        rc, stdout, stderr = run_todo_isolated(tmp_path, "add", "")
        assert rc != 0
        assert "错误" in stderr

    def test_add_whitespace_rejected(self, tmp_path):
        """纯空格被拒绝。"""
        rc, stdout, stderr = run_todo_isolated(tmp_path, "add", "   ")
        assert rc != 0
        assert "错误" in stderr


# --- S-003: list 命令 ---


class TestList:
    def test_list_empty(self, tmp_path):
        """无任务时友好提示。"""
        rc, stdout, _ = run_todo_isolated(tmp_path, "list")
        assert rc == 0
        assert "没有任务" in stdout

    def test_list_with_tasks(self, tmp_path):
        """有任务时正确显示。"""
        run_todo_isolated(tmp_path, "add", "任务A")
        run_todo_isolated(tmp_path, "add", "任务B")
        run_todo_isolated(tmp_path, "done", "1")

        rc, stdout, _ = run_todo_isolated(tmp_path, "list")
        assert rc == 0
        assert "[✓] #1 任务A" in stdout
        assert "[ ] #2 任务B" in stdout


# --- S-004: done 和 delete 命令 ---


class TestDone:
    def test_done_success(self, tmp_path):
        """标记完成。"""
        run_todo_isolated(tmp_path, "add", "待完成")
        rc, stdout, _ = run_todo_isolated(tmp_path, "done", "1")
        assert rc == 0
        assert "Completed" in stdout

        # 验证 JSON
        data = json.loads((tmp_path / ".todo" / "tasks.json").read_text())
        assert data["tasks"][0]["done"] is True

    def test_done_invalid_id(self, tmp_path):
        """不存在的 ID 报错。"""
        run_todo_isolated(tmp_path, "add", "存在的任务")
        rc, _, stderr = run_todo_isolated(tmp_path, "done", "99")
        assert rc != 0
        assert "不存在" in stderr

    def test_done_non_numeric_id(self, tmp_path):
        """非数字 ID 报错。"""
        rc, _, stderr = run_todo_isolated(tmp_path, "done", "abc")
        assert rc != 0


class TestDelete:
    def test_delete_success(self, tmp_path):
        """删除任务。"""
        run_todo_isolated(tmp_path, "add", "待删除")
        rc, stdout, _ = run_todo_isolated(tmp_path, "delete", "1")
        assert rc == 0
        assert "Deleted" in stdout

        # 验证 JSON
        data = json.loads((tmp_path / ".todo" / "tasks.json").read_text())
        assert len(data["tasks"]) == 0

    def test_delete_invalid_id(self, tmp_path):
        """不存在的 ID 报错。"""
        run_todo_isolated(tmp_path, "add", "存在的任务")
        rc, _, stderr = run_todo_isolated(tmp_path, "delete", "99")
        assert rc != 0
        assert "不存在" in stderr

    def test_delete_non_numeric_id(self, tmp_path):
        """非数字 ID 报错。"""
        rc, _, stderr = run_todo_isolated(tmp_path, "delete", "abc")
        assert rc != 0

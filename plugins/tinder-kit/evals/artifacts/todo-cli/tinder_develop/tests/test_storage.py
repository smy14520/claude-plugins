"""storage.py 持久化层测试。

Seam：单一 JSON 文件的整体读/整体写（ADR-0001）。
期望值全部来自手写 literal（外部真相源），不与实现互算。
"""

import pytest

from todo import storage


def make_todo(i, title="买牛奶", tags=None, status="open", priority="med"):
    """手写 literal：一条合法 Todo 的形状。"""
    return {
        "id": i,
        "title": title,
        "tags": tags or [],
        "status": status,
        "priority": priority,
        "created_at": "2026-09-26T08:00:00+00:00",
        "completed_at": None,
    }


def test_save_then_load_round_trips(tmp_path, monkeypatch):
    """存进去什么，读出来就是什么。"""
    monkeypatch.chdir(tmp_path)
    todos = [
        make_todo(1),
        make_todo(2, title="写周报", tags=["工作"], priority="high"),
    ]
    storage.save(todos)
    assert storage.load() == todos


def test_load_missing_file_returns_empty_list(tmp_path, monkeypatch):
    """第一次使用（无存储文件）应为空清单，而不是报错。"""
    monkeypatch.chdir(tmp_path)
    assert storage.load() == []


def test_todo_file_env_overrides_path(tmp_path, monkeypatch):
    """TODO_FILE 把存储指向别处；CWD 下不落 .todos.json。"""
    custom = tmp_path / "elsewhere" / "my-list.json"
    monkeypatch.setenv("TODO_FILE", str(custom))
    storage.save([make_todo(1)])
    assert custom.exists()
    assert not (tmp_path / ".todos.json").exists()
    assert storage.load() == [make_todo(1)]


def test_save_leaves_no_temp_file_behind(tmp_path, monkeypatch):
    """原子写的可观测结果：目录里除存储文件外不留任何 .tmp 残渣。"""
    monkeypatch.chdir(tmp_path)
    storage.save([make_todo(1)])
    storage.save([make_todo(1), make_todo(2)])  # 覆盖已存在文件
    files = sorted(p.name for p in tmp_path.iterdir())
    assert files == [".todos.json"]
    assert storage.load() == [make_todo(1), make_todo(2)]


def test_corrupt_file_raises_storage_error(tmp_path, monkeypatch):
    """手改坏的文件应得到明确的 StorageError，而不是裸 traceback。"""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".todos.json").write_text("{ 这不是 JSON", encoding="utf-8")
    with pytest.raises(storage.StorageError):
        storage.load()

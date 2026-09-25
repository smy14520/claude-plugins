"""Store 接缝行为测试：单一 JSON 文件持久化（ADR-0001）。"""

import json

import pytest

from todo_cli.models import Task
from todo_cli.storage import StorageError, TodoStore


def test_round_trip_tasks_and_next_id(tmp_path):
    store = TodoStore(tmp_path / "todos.json")
    tasks = [
        Task(id=1, text="买牛奶", tags=["生活", "采购"]),
        Task(id=2, text="写周报", tags=["工作"], done=True),
    ]
    store.save(tasks, next_id=3)

    loaded, next_id = TodoStore(tmp_path / "todos.json").load()

    assert loaded == tasks
    assert next_id == 3


def test_missing_file_is_fresh_start(tmp_path):
    loaded, next_id = TodoStore(tmp_path / "todos.json").load()

    assert loaded == []
    assert next_id == 1


def test_save_creates_missing_parent_dirs(tmp_path):
    store = TodoStore(tmp_path / "a" / "b" / "todos.json")

    store.save([Task(id=1, text="x", tags=[])], next_id=2)

    assert (tmp_path / "a" / "b" / "todos.json").exists()


def test_todo_file_env_overrides_default_path(tmp_path, monkeypatch):
    target = tmp_path / "via-env.json"
    monkeypatch.setenv("TODO_FILE", str(target))

    TodoStore().save([Task(id=1, text="x", tags=[])], next_id=2)

    assert target.exists()


def test_corrupt_file_raises_instead_of_reset(tmp_path):
    path = tmp_path / "todos.json"
    path.write_text("{not json", encoding="utf-8")

    with pytest.raises(StorageError):
        TodoStore(path).load()

    # 绝不静默重置：坏文件原样保留
    assert path.read_text(encoding="utf-8") == "{not json"


@pytest.mark.parametrize(
    "payload",
    [
        "[]",  # 顶层不是对象
        '{"tasks": [{"id": 1}]}',  # 任务记录缺 text
        '{"tasks": ["nope"]}',  # 任务记录不是对象
        '{"tasks": [], "next_id": "x"}',  # next_id 不可解析
    ],
)
def test_structurally_broken_file_raises_instead_of_reset(tmp_path, payload):
    path = tmp_path / "todos.json"
    path.write_text(payload, encoding="utf-8")

    with pytest.raises(StorageError):
        TodoStore(path).load()

    assert path.read_text(encoding="utf-8") == payload


def test_atomic_write_leaves_no_temp_files(tmp_path):
    store = TodoStore(tmp_path / "todos.json")

    store.save([Task(id=1, text="x", tags=[])], next_id=2)

    leftovers = [p.name for p in tmp_path.iterdir() if p.name != "todos.json"]
    assert leftovers == []
    json.loads((tmp_path / "todos.json").read_text(encoding="utf-8"))

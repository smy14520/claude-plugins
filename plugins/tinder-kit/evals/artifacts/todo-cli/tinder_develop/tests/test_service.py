"""Service 接缝行为测试：任务流转与 ID 契约（每次变更即落盘，进程级语义）。"""

import pytest

from todo_cli.service import TaskNotFound, TodoService
from todo_cli.storage import TodoStore


def make_service(tmp_path):
    return TodoService(TodoStore(tmp_path / "todos.json"))


def test_add_assigns_sequential_ids_and_dedupes_tags(tmp_path):
    svc = make_service(tmp_path)

    t1 = svc.add("买牛奶", ["生活", "采购"])
    t2 = svc.add("写周报", ["工作", "工作", "工作"])

    assert (t1.id, t1.tags) == (1, ["生活", "采购"])
    assert (t2.id, t2.tags) == (2, ["工作"])


def test_id_never_reused_after_remove(tmp_path):
    svc = make_service(tmp_path)
    svc.add("a", [])
    victim = svc.add("b", [])
    svc.remove(victim.id)

    fresh = svc.add("c", [])

    assert fresh.id == 3


def test_complete_marks_done_and_persists(tmp_path):
    svc = make_service(tmp_path)
    task = svc.add("a", [])

    svc.complete(task.id)

    tasks, _ = TodoStore(tmp_path / "todos.json").load()
    assert tasks[0].done is True


def test_unknown_id_raises_task_not_found(tmp_path):
    svc = make_service(tmp_path)

    with pytest.raises(TaskNotFound):
        svc.complete(99)
    with pytest.raises(TaskNotFound):
        svc.remove(99)


def test_list_defaults_to_open_tasks_only(tmp_path):
    svc = make_service(tmp_path)
    open_task = svc.add("a", [])
    done_task = svc.add("b", [])
    svc.complete(done_task.id)

    assert [t.id for t in svc.list_tasks()] == [open_task.id]

    # --all 语义：含已完成
    assert [t.id for t in svc.list_tasks(include_done=True)] == [open_task.id, done_task.id]


def test_list_filters_by_tags_with_and_semantics(tmp_path):
    svc = make_service(tmp_path)
    svc.add("a", ["生活", "采购"])
    both = svc.add("b", ["生活", "采购", "紧急"])
    svc.add("c", ["生活"])
    svc.add("d", ["采购"])

    matched = svc.list_tasks(["生活", "采购"])

    assert [t.id for t in matched] == [1, both.id]


def test_tag_counts_spans_all_tasks_including_done(tmp_path):
    svc = make_service(tmp_path)
    svc.add("a", ["工作", "紧急"])
    done = svc.add("b", ["工作"])
    svc.complete(done.id)

    assert svc.tag_counts() == {"工作": 2, "紧急": 1}

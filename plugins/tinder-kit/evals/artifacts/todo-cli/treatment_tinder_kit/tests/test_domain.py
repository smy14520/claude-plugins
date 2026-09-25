"""Seam 2 — Store 领域操作公共行为测试。"""
import pytest

from todo_cli.store import Store, TodoNotFoundError


def _store_with_fixtures() -> Store:
    """t1#x, t2#x+y, t3#y, t4#x(done)，ID 恰为 1..4。"""
    store = Store()
    store.add("t1", tags=["x"])
    store.add("t2", tags=["x", "y"])
    store.add("t3", tags=["y"])
    t4 = store.add("t4", tags=["x"])
    store.done(t4.id)
    return store


def test_done_marks_done_and_undo_reopens(tmp_path):
    store = Store()
    t = store.add("买牛奶")
    done = store.done(t.id)
    assert done.status == "done" and done.done_at is not None
    undone = store.undo(t.id)
    assert undone.status == "open" and undone.done_at is None


def test_unknown_id_raises_public_error():
    store = Store()
    with pytest.raises(TodoNotFoundError):
        store.done(99)
    with pytest.raises(TodoNotFoundError):
        store.rm(99)


def test_rm_never_reuses_ids():
    store = Store()
    store.add("a")
    second = store.add("b")
    store.rm(second.id)
    after = store.add("c")
    assert after.id == 3  # 编号跳号继续，绝不回收（ADR-0003）


def test_list_defaults_to_open_only_sorted_by_id():
    store = _store_with_fixtures()
    assert [t.id for t in store.list_todos()] == [1, 2, 3]


def test_list_multiple_tags_is_intersection():
    store = _store_with_fixtures()
    assert [t.id for t in store.list_todos(tags=["x", "y"])] == [2]


def test_list_show_all_includes_done():
    store = _store_with_fixtures()
    assert [t.id for t in store.list_todos(show_all=True)] == [1, 2, 3, 4]
    assert [t.id for t in store.list_todos(show_all=True, tags=["x"])] == [1, 2, 4]


def test_tag_counts_split_by_status_and_sorted():
    store = _store_with_fixtures()
    assert store.tag_counts() == {"x": (2, 1), "y": (2, 0)}


def test_list_sorts_high_med_low_then_none_with_id_tiebreak():
    store = Store()
    store.add("none-a")  # 1
    high = store.add("h", priority="high")  # 2
    store.add("none-b")  # 3
    low = store.add("l", priority="low")  # 4
    med = store.add("m", priority="med")  # 5
    assert [t.id for t in store.list_todos()] == [high.id, med.id, low.id, 1, 3]


def test_add_rejects_priority_outside_valid_set():
    """Store 是 Agreed Seam，不依赖 argparse 也必须拒绝垃圾优先级。"""
    store = Store()
    with pytest.raises(ValueError):
        store.add("x", priority="urgent")

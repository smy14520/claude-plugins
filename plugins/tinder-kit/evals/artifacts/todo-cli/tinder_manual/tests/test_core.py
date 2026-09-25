import pytest

from tdo import core


def mk(task_id, title="t", tags=(), status=core.PENDING):
    return {
        "id": task_id,
        "title": title,
        "tags": list(tags),
        "status": status,
        "created_at": "c",
        "completed_at": None,
    }


def test_id_allocation_never_reused():
    data = {"next_id": 1, "tasks": []}
    tasks = data["tasks"]
    a = core.add(tasks, "a", [], core.take_next_id(data))
    b = core.add(tasks, "b", [], core.take_next_id(data))
    assert (a["id"], b["id"]) == (1, 2)
    core.remove(tasks, b["id"])
    c = core.add(tasks, "c", [], core.take_next_id(data))
    assert c["id"] == 3
    assert data["next_id"] == 4


def test_add_normalizes_tags():
    task = core.add([], "buy milk", ["Shopping", "URGENT, shopping", ""], 1)
    assert task["tags"] == ["shopping", "urgent"]
    assert task["title"] == "buy milk"
    assert task["status"] == core.PENDING
    assert task["completed_at"] is None


def test_add_strips_then_rejects_blank_title():
    with pytest.raises(core.ValidationError):
        core.add([], "   ", [], 1)


def test_parse_tag_groups():
    assert core.parse_tag_groups(["Work,urgent"]) == [["urgent", "work"]]
    assert core.parse_tag_groups(["a", "b"]) == [["a"], ["b"]]
    with pytest.raises(core.ValidationError):
        core.parse_tag_groups([" , "])


def test_filter_and_across_groups_or_within():
    tasks = [mk(1, tags=["work"]), mk(2, tags=["work", "urgent"]), mk(3, tags=["home"])]
    matched, unknown = core.filter_tasks(tasks, [["work"], ["urgent", "home"]])
    assert [t["id"] for t in matched] == [2]
    assert unknown == []


def test_filter_defaults_to_pending():
    tasks = [mk(1, status=core.DONE, tags=["work"]), mk(2, tags=["work"])]
    matched, _ = core.filter_tasks(tasks, [])
    assert [t["id"] for t in matched] == [2]
    matched, _ = core.filter_tasks(tasks, [], include_done=True)
    assert [t["id"] for t in matched] == [1, 2]


def test_filter_detects_unknown_groups():
    matched, unknown = core.filter_tasks([mk(1, tags=["work"])], [["nope"]])
    assert matched == []
    assert unknown == ["nope"]


def test_done_and_reopen_transitions():
    tasks = [mk(1)]
    task, changed = core.done(tasks, 1)
    assert changed and task["status"] == core.DONE and task["completed_at"]
    task, changed = core.done(tasks, 1)
    assert not changed
    task, changed = core.reopen(tasks, 1)
    assert changed
    assert task["status"] == core.PENDING
    assert task["completed_at"] is None
    with pytest.raises(core.NotFound):
        core.done(tasks, 99)


def test_tag_counts_sorted_by_count_desc_then_name():
    tasks = [mk(1, tags=["a", "b"]), mk(2, tags=["a"]), mk(3, tags=["a", "c"])]
    assert core.tag_counts(tasks) == [
        {"tag": "a", "count": 3},
        {"tag": "b", "count": 1},
        {"tag": "c", "count": 1},
    ]

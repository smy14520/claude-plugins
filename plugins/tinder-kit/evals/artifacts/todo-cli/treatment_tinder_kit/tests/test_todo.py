"""核心接缝回归 —— 对应 spec 验收清单，测试直接钉在 models（领域）与 storage（持久化）上。"""

from __future__ import annotations

from pathlib import Path

import pytest

from todo_cli.models import Priority, Status, normalize_tag, select_tasks
from todo_cli.storage import CorruptStoreError, Store


@pytest.fixture
def store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Store:
    monkeypatch.chdir(tmp_path)
    return Store.load()


def test_normalize_tag_folds_and_lowercases(store):
    assert normalize_tag("  Deep   WORK ") == "deep-work"


def test_tag_normalized_and_deduped_in_add(store):
    task = store.add("t", tags=["work", "  Deep   WORK ", "URGENT"], priority=Priority.low)
    assert task.tags == ["work", "deep-work", "urgent"]


def test_id_never_reused(store):
    first = store.add("a", [], Priority.med)
    assert store.remove(first.id)
    second = store.add("b", [], Priority.med)
    assert second.id == first.id + 1
    store.save()
    reloaded = Store.load()
    assert reloaded.next_id == second.id + 1  # 落盘 next_id 持久化（spec: ID 永不复用）


def test_roundtrip_survives_save_and_load(store):
    store.add("买牛奶", ["shopping"], Priority.high)
    store.save()
    reloaded = Store.load()
    assert len(reloaded.tasks) == 1
    assert reloaded.tasks[0].title == "买牛奶"
    assert reloaded.tasks[0].priority is Priority.high
    assert reloaded.tasks[0].status is Status.pending


def test_corrupt_json_raises(store):
    store.path().write_text("{ not json", encoding="utf-8")
    with pytest.raises(CorruptStoreError):
        Store.load()


def test_cwd_isolation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    dir_a = tmp_path / "a"
    dir_b = tmp_path / "b"
    dir_a.mkdir()
    dir_b.mkdir()

    monkeypatch.chdir(dir_a)
    store_a = Store.load()
    store_a.add("in-a", [], Priority.med)
    store_a.save()

    monkeypatch.chdir(dir_b)
    store_b = Store.load()
    assert store_b.tasks == []

    monkeypatch.chdir(dir_a)
    assert [t.title for t in Store.load().tasks] == ["in-a"]


def test_select_tasks_filters_and_sorts(store):
    store.add("low-2", ["work"], Priority.low)
    store.add("high-1", ["work", "urgent"], Priority.high)
    store.add("med-3", ["home"], Priority.med)
    done_task = store.add("done-4", ["work"], Priority.low)
    done_task.status = Status.done

    pending = select_tasks(store.tasks, [], include_done=False)
    assert [t.title for t in pending] == ["high-1", "med-3", "low-2"]

    everything = select_tasks(store.tasks, [], include_done=True)
    assert [t.title for t in everything] == ["high-1", "med-3", "low-2", "done-4"]

    and_filtered = select_tasks(store.tasks, ["work", "urgent"], include_done=False)
    assert [t.title for t in and_filtered] == ["high-1"]


def test_select_tasks_normalizes_wanted_tags(store):
    store.add("t", ["deep-work"], Priority.med)
    assert [t.title for t in select_tasks(store.tasks, ["Deep  WORK"], include_done=False)] == ["t"]

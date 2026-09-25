"""Seam 1 — Store 持久化公共行为测试。"""
import json

import pytest

from todo_cli.store import Store


def test_missing_file_bootstraps_empty_store(tmp_path):
    store = Store.load(tmp_path / "nope.json")
    first = store.add("first", tags=["a"])
    assert first.id == 1  # 空 Store 从 next_id=1 起步


def test_add_assigns_incrementing_ids_and_roundtrip_preserves_state(tmp_path):
    path = tmp_path / "todos.json"
    store = Store.load(path)
    t1 = store.add("买牛奶", tags=["shopping"])
    t2 = store.add("寄快递")
    assert (t1.id, t2.id) == (1, 2)

    store.save(path)
    reloaded = Store.load(path)
    assert [t.text for t in reloaded] == ["买牛奶", "寄快递"]
    assert reloaded.add("第三条").id == 3  # ID 计数器在往返后保留


def test_save_writes_the_spec_pinned_json_shape_utf8(tmp_path):
    path = tmp_path / "todos.json"
    store = Store.load(path)
    store.add("买牛奶", tags=["shopping"])
    store.save(path)

    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["next_id"] == 2
    todo = data["todos"][0]
    assert todo["text"] == "买牛奶"  # ensure_ascii=False：中文肉眼可读
    assert todo["tags"] == ["shopping"]
    assert todo["status"] == "open"
    assert todo["created_at"]
    assert todo["done_at"] is None


def test_save_failure_leaves_previous_store_intact_and_no_tmp_leftover(tmp_path, monkeypatch):
    """原子写入的公共可观测契约：写中途失败 → 旧数据原封不动，无 .tmp 残留。"""
    path = tmp_path / "todos.json"
    store = Store.load(path)
    store.add("a")
    store.save(path)
    good = path.read_text(encoding="utf-8")

    def exploding_dump(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr("todo_cli.store.json.dump", exploding_dump)
    broken = Store.load(path)
    broken.add("b")
    with pytest.raises(OSError):
        broken.save(path)

    assert path.read_text(encoding="utf-8") == good  # 旧数据未被破坏
    assert list(tmp_path.glob("*.tmp")) == []  # 临时文件已清理


def test_priority_roundtrips_through_save_and_load(tmp_path):
    path = tmp_path / "todos.json"
    store = Store.load(path)
    store.add("h", priority="high")
    store.save(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["todos"][0]["priority"] == "high"
    assert next(iter(Store.load(path))).priority == "high"


def test_legacy_store_without_priority_key_loads_as_none(tmp_path):
    """变更周期 1 前的旧文件没有 priority 键，必须兼容读取。"""
    path = tmp_path / "todos.json"
    legacy = {"next_id": 2, "todos": [
        {"id": 1, "text": "旧条目", "tags": [], "status": "open",
         "created_at": "2026-09-25T10:00:00+08:00", "done_at": None}]}
    path.write_text(json.dumps(legacy, ensure_ascii=False), encoding="utf-8")
    todo = next(iter(Store.load(path)))
    assert todo.priority is None

import json

import pytest

from tdo import store


def test_roundtrip_preserves_data(tmp_path):
    path = tmp_path / "todo.json"
    data = {
        "version": 1,
        "next_id": 2,
        "tasks": [
            {
                "id": 1,
                "title": "买牛奶",
                "tags": ["shopping"],
                "status": "pending",
                "created_at": "2026-09-25T00:00:00Z",
                "completed_at": None,
            }
        ],
    }
    store.save(data, path)
    assert store.load(path) == data


def test_missing_file_loads_empty(tmp_path):
    assert store.load(tmp_path / "nope.json") == store.empty()


def test_corrupt_json_raises(tmp_path):
    path = tmp_path / "todo.json"
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(store.StoreError):
        store.load(path)


def test_unexpected_shape_raises(tmp_path):
    path = tmp_path / "todo.json"
    path.write_text(json.dumps({"foo": 1}), encoding="utf-8")
    with pytest.raises(store.StoreError):
        store.load(path)


def test_bak_holds_previous_generation(tmp_path):
    path = tmp_path / "todo.json"
    first = store.empty()
    store.save(first, path)
    second = {
        "version": 1,
        "next_id": 2,
        "tasks": [
            {
                "id": 1,
                "title": "x",
                "tags": [],
                "status": "pending",
                "created_at": "t",
                "completed_at": None,
            }
        ],
    }
    store.save(second, path)
    assert json.loads(store.bak_path(path).read_text(encoding="utf-8")) == first
    assert store.load(path) == second


def test_todo_home_env_overrides_dir(monkeypatch, tmp_path):
    monkeypatch.setenv("TODO_HOME", str(tmp_path))
    assert store.store_path() == tmp_path / "todo.json"


def test_missing_next_id_is_derived_from_tasks(tmp_path):
    path = tmp_path / "todo.json"
    legacy = {
        "version": 1,
        "tasks": [
            {
                "id": 5,
                "title": "x",
                "tags": [],
                "status": "pending",
                "created_at": "t",
                "completed_at": None,
            }
        ],
    }
    path.write_text(json.dumps(legacy), encoding="utf-8")
    assert store.load(path)["next_id"] == 6

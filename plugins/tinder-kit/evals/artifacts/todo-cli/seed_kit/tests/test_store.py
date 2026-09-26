"""Store-level properties: schema validation and the id-allocation guard.

Unit-level on purpose -- the CLI-level behaviour of these rules is covered by
the slice tests; here we pin down the error paths and the defensive branches
that a hand-edited ``./.todos.json`` can reach.
"""

from __future__ import annotations

import json

import pytest

from todo_cli import store
from todo_cli.core import allocate_id, dedupe_tags


def write_raw(tmp_path, text):
    (tmp_path / ".todos.json").write_text(text, encoding="utf-8")


def test_load_reports_malformed_json_instead_of_tracebacking(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    write_raw(tmp_path, "{not json at all")

    with pytest.raises(store.StoreError) as excinfo:
        store.load()

    assert ".todos.json" in str(excinfo.value)


@pytest.mark.parametrize(
    "document",
    [
        {"next_id": "2", "todos": []},
        {"todos": []},
        {"next_id": 1},
        {"next_id": 1, "todos": {}},
        {"next_id": 1, "todos": [{"id": 1}]},
        {
            "next_id": 1,
            "todos": [
                {
                    "id": 1,
                    "title": "",
                    "tags": [],
                    "priority": "med",
                    "done": False,
                    "created_at": "2026-09-26T08:00:00Z",
                    "completed_at": None,
                }
            ],
        },
        {
            "next_id": 1,
            "todos": [
                {
                    "id": 1,
                    "title": "t",
                    "tags": ["a"],
                    "priority": "urgent",
                    "done": False,
                    "created_at": "2026-09-26T08:00:00Z",
                    "completed_at": None,
                }
            ],
        },
        {
            "next_id": 1,
            "todos": [
                {
                    "id": 1,
                    "title": "t",
                    "tags": ["a"],
                    "priority": "med",
                    "done": True,
                    "created_at": "2026-09-26T08:00:00Z",
                    "completed_at": None,
                }
            ],
        },
        {
            "next_id": 1,
            "todos": [
                {
                    "id": 1,
                    "title": "t",
                    "tags": ["a"],
                    "priority": "med",
                    "done": False,
                    "created_at": "2026-09-26T08:00:00Z",
                    "completed_at": "2026-09-26T09:00:00Z",
                }
            ],
        },
    ],
)
def test_load_rejects_documents_that_break_the_schema(tmp_path, monkeypatch, document):
    monkeypatch.chdir(tmp_path)
    write_raw(tmp_path, json.dumps(document))

    with pytest.raises(store.StoreError):
        store.load()


def test_extra_record_keys_survive_a_round_trip(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    store.save(
        {
            "next_id": 2,
            "todos": [
                {
                    "id": 1,
                    "title": "带额外字段的",
                    "tags": [],
                    "priority": "med",
                    "done": False,
                    "created_at": "2026-09-26T08:00:00Z",
                    "completed_at": None,
                    "note": "user-added, must not be dropped",
                }
            ],
        }
    )

    reloaded = store.load()
    assert reloaded["todos"][0]["note"] == "user-added, must not be dropped"
    store.save(reloaded)
    assert store.load()["todos"][0]["note"] == "user-added, must not be dropped"


def test_allocate_id_never_rewinds_and_never_collides():
    assert allocate_id({"next_id": 7, "todos": []}) == 7

    # A hand-edited file whose counter lags the records must not hand out a
    # duplicate id: bump upward, never reuse.
    lagging = {
        "next_id": 2,
        "todos": [
            {"id": 5, "title": "t", "tags": [], "priority": "med", "done": False,
             "created_at": "2026-09-26T08:00:00Z", "completed_at": None}
        ],
    }
    assert allocate_id(lagging) == 6


def test_dedupe_tags_keeps_first_seen_order():
    assert dedupe_tags(["b", "a", "b", "c", "a"]) == ["b", "a", "c"]
    assert dedupe_tags([]) == []

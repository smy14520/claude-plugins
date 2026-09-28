import json
from datetime import date
from pathlib import Path

import pytest

from todo import add_todo, done_todo, is_overdue, list_todos, load_todos, main


def test_basic_crud(tmp_path: Path):
    store = tmp_path / ".todos.json"
    t1 = add_todo("Buy milk", store)
    assert t1["id"] == 1
    assert len(list_todos(store)) == 1

    done_todo(1, store)
    assert len(list_todos(store)) == 0


def test_add_todo_with_due_persists_due(tmp_path: Path):
    store = tmp_path / ".todos.json"
    item = add_todo("Pay rent", store, due="2026-10-01")
    assert item["due"] == "2026-10-01"
    saved = load_todos(store)
    assert saved[0]["due"] == "2026-10-01"


def test_add_todo_without_due_has_no_due_key(tmp_path: Path):
    store = tmp_path / ".todos.json"
    item = add_todo("Buy milk", store)
    assert "due" not in item
    assert load_todos(store)[0] == {"id": 1, "title": "Buy milk", "done": False}


def test_is_overdue_means_strictly_past_due():
    today = date(2026, 9, 28)
    assert is_overdue({"id": 1, "title": "a", "done": False, "due": "2026-09-27"}, today=today)
    assert not is_overdue({"id": 2, "title": "b", "done": False, "due": "2026-09-28"}, today=today)
    assert not is_overdue({"id": 3, "title": "c", "done": False, "due": "2026-09-29"}, today=today)


def test_is_overdue_without_due_is_never_overdue():
    today = date(2026, 9, 28)
    assert not is_overdue({"id": 1, "title": "legacy", "done": False}, today=today)


def test_legacy_file_without_due_fields_round_trips(tmp_path: Path):
    store = tmp_path / ".todos.json"
    store.write_text(
        json.dumps({"todos": [{"id": 1, "title": "legacy", "done": False}]}),
        encoding="utf-8",
    )
    items = list_todos(store)
    assert [t["title"] for t in items] == ["legacy"]
    assert not is_overdue(items[0], today=date(2026, 9, 28))
    done_todo(1, store)
    assert list_todos(store) == []


def test_cli_add_with_due_wires_through(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(tmp_path)
    assert main(["add", "File taxes", "--due", "2026-10-01"]) == 0
    saved = load_todos(Path(".todos.json"))
    assert saved[0]["due"] == "2026-10-01"


def test_cli_add_rejects_malformed_due(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as excinfo:
        main(["add", "Bad date", "--due", "01/10/2026"])
    assert excinfo.value.code != 0
    assert not Path(".todos.json").exists()


def test_cli_add_rejects_non_canonical_iso_due(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(tmp_path)
    for bad in ("20261001", "2026-W40-1", "2026-10-1"):
        with pytest.raises(SystemExit) as excinfo:
            main(["add", "Bad", "--due", bad])
        assert excinfo.value.code != 0
    assert not Path(".todos.json").exists()


def test_cli_list_marks_overdue_open_todos(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    monkeypatch.chdir(tmp_path)
    Path(".todos.json").write_text(
        json.dumps(
            {
                "todos": [
                    {"id": 1, "title": "Overdue task", "done": False, "due": "2020-01-01"},
                    {"id": 2, "title": "No deadline", "done": False},
                ]
            }
        ),
        encoding="utf-8",
    )
    assert main(["list"]) == 0
    out = capsys.readouterr().out
    assert "[1] Overdue task [OVERDUE]\n" in out
    assert "[2] No deadline\n" in out
    assert out.count("[OVERDUE]") == 1

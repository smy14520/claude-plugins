import json
from datetime import date, timedelta
from pathlib import Path

import pytest

from todo import add_todo, done_todo, is_overdue, list_todos, main


def test_basic_crud(tmp_path: Path):
    store = tmp_path / ".todos.json"
    t1 = add_todo("Buy milk", store)
    assert t1["id"] == 1
    assert len(list_todos(store)) == 1

    done_todo(1, store)
    assert len(list_todos(store)) == 0


def test_add_with_due_round_trips(tmp_path: Path):
    store = tmp_path / ".todos.json"
    tomorrow = (date.today() + timedelta(days=1)).isoformat()

    item = add_todo("Pay rent", store, due=tomorrow)
    assert item["due"] == tomorrow

    reopened = json.loads(store.read_text(encoding="utf-8"))
    assert reopened["todos"][0]["due"] == tomorrow


def test_add_without_due_omits_field(tmp_path: Path):
    store = tmp_path / ".todos.json"
    item = add_todo("No date", store)
    assert "due" not in item


def test_old_store_without_due_still_works(tmp_path: Path):
    store = tmp_path / ".todos.json"
    legacy = {"todos": [{"id": 1, "title": "Legacy", "done": False}]}
    store.write_text(json.dumps(legacy), encoding="utf-8")

    item = add_todo("New with due", store, due="2020-01-01")
    assert item["id"] == 2
    assert len(list_todos(store)) == 2
    assert done_todo(1, store)


@pytest.mark.parametrize("offset,expected", [
    (timedelta(days=-1), True),
    (timedelta(days=0), False),
    (timedelta(days=1), False),
])
def test_is_overdue_boundary(offset: timedelta, expected: bool):
    today = date(2026, 9, 29)
    todo_item = {
        "id": 1,
        "title": "x",
        "done": False,
        "due": (today + offset).isoformat(),
    }
    assert is_overdue(todo_item, today=today) is expected


def test_is_overdue_without_due_is_false():
    assert is_overdue({"id": 1, "title": "x", "done": False}) is False


def test_is_overdue_tolerates_malformed_due():
    assert is_overdue({"id": 1, "title": "x", "done": False, "due": "2020-13-99"}) is False
    assert is_overdue({"id": 1, "title": "x", "done": False, "due": 20260101}) is False


def test_legacy_row_output_unchanged(tmp_path: Path, capsys, monkeypatch):
    monkeypatch.chdir(tmp_path)
    legacy = {"todos": [{"id": 1, "title": "Legacy", "done": False}]}
    Path(".todos.json").write_text(json.dumps(legacy), encoding="utf-8")

    assert main(["list"]) == 0

    assert capsys.readouterr().out == "[1] Legacy\n"


def test_list_survives_malformed_stored_due(tmp_path: Path, capsys, monkeypatch):
    monkeypatch.chdir(tmp_path)
    dirty = {"todos": [
        {"id": 1, "title": "Broken due", "done": False, "due": "2020-13-99"},
        {"id": 2, "title": "Numeric due", "done": False, "due": 20260101},
    ]}
    Path(".todos.json").write_text(json.dumps(dirty), encoding="utf-8")

    assert main(["list"]) == 0

    out = capsys.readouterr().out
    assert "Broken due" in out and "Numeric due" in out
    assert "[OVERDUE]" not in out


def test_cli_normalizes_due_to_iso(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    assert main(["add", "Loose", "--due", "2026-1-5"]) == 0

    data = json.loads(Path(".todos.json").read_text(encoding="utf-8"))
    assert data["todos"][0]["due"] == "2026-01-05"


def test_list_shows_due_for_dated_tasks(tmp_path: Path, capsys, monkeypatch):
    monkeypatch.chdir(tmp_path)

    assert main(["add", "Dated", "--due", "2026-12-31"]) == 0
    assert main(["add", "Plain"]) == 0
    assert main(["list"]) == 0

    out = capsys.readouterr().out
    assert "[1] Dated (due: 2026-12-31)" in out
    assert "[2] Plain" in out
    assert "(due:" not in out.splitlines()[1]


def test_list_overdue_line_keeps_marker_last(tmp_path: Path, capsys, monkeypatch):
    monkeypatch.chdir(tmp_path)
    past = (date.today() - timedelta(days=1)).isoformat()

    assert main(["add", "Old", "--due", past]) == 0
    capsys.readouterr()  # discard the add confirmation line

    assert main(["list"]) == 0

    assert capsys.readouterr().out == f"[1] Old (due: {past}) [OVERDUE]\n"


def test_list_marks_overdue(tmp_path: Path, capsys, monkeypatch):
    monkeypatch.chdir(tmp_path)
    past = (date.today() - timedelta(days=1)).isoformat()

    assert main(["add", "Late task", "--due", past]) == 0
    assert main(["list"]) == 0

    assert "[OVERDUE]" in capsys.readouterr().out


def test_list_no_marker_for_future_due(tmp_path: Path, capsys, monkeypatch):
    monkeypatch.chdir(tmp_path)
    future = (date.today() + timedelta(days=7)).isoformat()

    assert main(["add", "Future task", "--due", future]) == 0
    assert main(["list"]) == 0

    out = capsys.readouterr().out
    assert f"[1] Future task (due: {future})" in out
    assert "[OVERDUE]" not in out


@pytest.mark.parametrize("bad", ["2020-13-99", "2020-02-30", "not-a-date", "2026/01/01"])
def test_add_rejects_invalid_due(bad: str, tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as exc:
        main(["add", "x", "--due", bad])
    assert exc.value.code == 2

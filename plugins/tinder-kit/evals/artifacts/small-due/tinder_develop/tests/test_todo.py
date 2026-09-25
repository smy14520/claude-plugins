import json
from datetime import date
from pathlib import Path

import pytest

import todo
from todo import add_todo, done_todo, is_overdue, list_todos


def test_basic_crud(tmp_path: Path):
    store = tmp_path / ".todos.json"
    t1 = add_todo("Buy milk", store)
    assert t1["id"] == 1
    assert len(list_todos(store)) == 1

    done_todo(1, store)
    assert len(list_todos(store)) == 0


def test_add_with_due_stores_field_and_omits_when_absent(tmp_path: Path):
    store = tmp_path / ".todos.json"
    add_todo("With due", store, due="2026-10-01")
    add_todo("No due", store)

    todos = read_store(store)
    assert todos[0]["due"] == "2026-10-01"
    assert "due" not in todos[1]


def test_cli_add_accepts_due_and_persists(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    rc = todo.main(["add", "Pay rent", "--due", "2026-10-01"])
    assert rc == 0
    assert read_store(tmp_path / ".todos.json")[0]["due"] == "2026-10-01"


def test_cli_add_rejects_invalid_due_without_writing(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    for bad in ("2026-13-40", "2026-02-30", "2026-9-5", "next-friday"):
        with pytest.raises(SystemExit) as exc:
            todo.main(["add", "x", "--due", bad])
        assert exc.value.code == 2
        assert "--due" in capsys.readouterr().err
    assert not (tmp_path / ".todos.json").exists()


def test_cli_add_invalid_due_leaves_existing_store_untouched(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    store = Path(".todos.json")
    add_todo("Keep me", store)
    before = store.read_text(encoding="utf-8")

    with pytest.raises(SystemExit) as exc:
        todo.main(["add", "x", "--due", "2026-02-30"])

    assert exc.value.code == 2
    assert store.read_text(encoding="utf-8") == before  # 已有文件逐字节不变


def test_is_overdue_strictly_after_due_date():
    on = date(2026, 9, 25)
    assert is_overdue({"due": "2026-09-24"}, on=on) is True
    assert is_overdue({"due": "2026-09-25"}, on=on) is False  # 截止日当天不算逾期
    assert is_overdue({"due": "2026-09-26"}, on=on) is False
    assert is_overdue({"title": "legacy"}, on=on) is False  # 无截止日期永不逾期


def read_store(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))["todos"]


def test_cli_list_renders_due_and_overdue_flag(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    todo.main(["add", "Already overdue", "--due", "2026-09-24"])
    todo.main(["add", "Due today", "--due", "2026-09-25"])
    todo.main(["add", "Upcoming", "--due", "2026-09-26"])
    add_todo("Legacy no due", Path(".todos.json"))

    monkeypatch.setattr(todo, "today", lambda: date(2026, 9, 25))
    capsys.readouterr()  # 丢弃 add 阶段输出，只断言 list 的行
    assert todo.main(["list"]) == 0

    lines = capsys.readouterr().out.splitlines()
    assert lines[0] == "[1] Already overdue (due: 2026-09-24) [OVERDUE]"
    assert lines[1] == "[2] Due today (due: 2026-09-25)"  # 截止日当天不算逾期
    assert lines[2] == "[3] Upcoming (due: 2026-09-26)"
    assert lines[3] == "[4] Legacy no due"  # 旧数据：无 due 键、无任何标注

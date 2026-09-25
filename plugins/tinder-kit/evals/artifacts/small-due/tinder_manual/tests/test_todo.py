import argparse
import datetime
import json
from pathlib import Path

import pytest

from todo import (add_todo, done_todo, format_todo, is_overdue, list_todos,
                  main, parse_due)


def test_basic_crud(tmp_path: Path):
    store = tmp_path / ".todos.json"
    t1 = add_todo("Buy milk", store)
    assert t1["id"] == 1
    assert len(list_todos(store)) == 1

    done_todo(1, store)
    assert len(list_todos(store)) == 0


# --- parse_due（D5/D6：非法硬拒绝，过去日期放行） ---


def test_parse_due_accepts_iso_date():
    assert parse_due("2026-10-01") == datetime.date(2026, 10, 1)
    assert parse_due("2020-01-01") == datetime.date(2020, 1, 1)  # 过去日期放行


@pytest.mark.parametrize("bad", [
    "tomorrow", "2026-13-45", "2026-10-1", "2026/10/01", "20261001", "",
])
def test_parse_due_rejects_invalid(bad: str):
    with pytest.raises(argparse.ArgumentTypeError):
        parse_due(bad)


def test_cli_rejects_invalid_due_without_writing(tmp_path: Path, monkeypatch):
    """D5：非法 --due 友好报错、exit != 0、零写入。"""
    monkeypatch.chdir(tmp_path)  # DEFAULT_FILE 相对 cwd
    with pytest.raises(SystemExit) as exc:
        main(["add", "report", "--due", "tomorrow"])
    assert exc.value.code != 0
    assert not (tmp_path / ".todos.json").exists()


# --- is_overdue（D2：strict 语义，Due 当天不算） ---


def test_overdue_is_strict_at_boundary():
    todo = {"id": 1, "title": "tax", "done": False, "due": "2026-09-25"}
    assert not is_overdue(todo, datetime.date(2026, 9, 25))  # Due 当天不算
    assert is_overdue(todo, datetime.date(2026, 9, 26))      # 次日才算


def test_todo_without_due_is_never_overdue():
    todo = {"id": 1, "title": "plain", "done": False}
    assert not is_overdue(todo, datetime.date(2999, 1, 1))


# --- 展示同构（D3/D4：add 回显与 list 共用 due_suffix） ---


def test_format_todo_shows_due_and_overdue_marker():
    today = datetime.date(2026, 9, 25)
    assert format_todo({"id": 1, "title": "tax", "done": False,
                        "due": "2026-10-01"}, today) == "[1] tax (due: 2026-10-01)"
    assert format_todo({"id": 2, "title": "old", "done": False,
                        "due": "2020-01-01"}, today) == "[2] old (due: 2020-01-01) [OVERDUE]"
    assert format_todo({"id": 3, "title": "plain", "done": False},
                       today) == "[3] plain"


# --- 向后兼容（D1：旧记录无 due 键照常工作，写回不补 null） ---


def test_legacy_file_without_due_field(tmp_path: Path):
    store = tmp_path / ".todos.json"
    store.write_text(
        json.dumps({"todos": [{"id": 1, "title": "legacy", "done": False}]}),
        encoding="utf-8")

    items = list_todos(store)
    assert [t["title"] for t in items] == ["legacy"]
    assert not is_overdue(items[0], datetime.date(2999, 1, 1))

    add_todo("fresh", store, due=datetime.date(2026, 10, 1))
    data = json.loads(store.read_text(encoding="utf-8"))
    assert data["todos"][0] == {"id": 1, "title": "legacy", "done": False}  # 未补 due 键
    assert data["todos"][1]["due"] == "2026-10-01"  # 新记录为 ISO 字符串

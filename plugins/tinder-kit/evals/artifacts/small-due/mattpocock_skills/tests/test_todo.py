import argparse
import json
from datetime import date
from pathlib import Path

import pytest

from todo import (
    add_todo,
    done_todo,
    format_todo,
    is_overdue,
    list_todos,
    main,
    parse_due,
)

TODAY = date(2026, 9, 25)


def test_basic_crud(tmp_path: Path):
    store = tmp_path / ".todos.json"
    t1 = add_todo("Buy milk", store)
    assert t1["id"] == 1
    assert len(list_todos(store)) == 1

    done_todo(1, store)
    assert len(list_todos(store)) == 0


# ---- 日期解析 ----


def test_parse_due_accepts_iso_date():
    assert parse_due("2026-09-30") == date(2026, 9, 30)


@pytest.mark.parametrize(
    "bad", ["2026/09/30", "30-09-2026", "2026-13-01", "2026-09", "abc", ""]
)
def test_parse_due_rejects_bad_input(bad: str):
    with pytest.raises(argparse.ArgumentTypeError):
        parse_due(bad)


def test_cli_rejects_invalid_due_with_nonzero_exit():
    with pytest.raises(SystemExit) as exc:
        main(["add", "x", "--due", "2026/09/30"])
    assert exc.value.code != 0


# ---- 逾期判定：逾期 ⇔ 今天 > due，截止当天不算 ----


def test_due_today_is_not_overdue():
    todo = {"id": 1, "title": "t", "done": False, "due": "2026-09-25"}
    assert is_overdue(todo, today=TODAY) is False


def test_past_due_is_overdue():
    todo = {"id": 1, "title": "t", "done": False, "due": "2026-09-24"}
    assert is_overdue(todo, today=TODAY) is True


def test_future_due_is_not_overdue():
    todo = {"id": 1, "title": "t", "done": False, "due": "2026-09-26"}
    assert is_overdue(todo, today=TODAY) is False


def test_todo_without_due_is_never_overdue():
    todo = {"id": 1, "title": "t", "done": False}
    assert is_overdue(todo, today=TODAY) is False


def test_done_task_never_listed_even_if_overdue(tmp_path: Path):
    store = tmp_path / ".todos.json"
    add_todo("t", store, due=date(2000, 1, 1))
    done_todo(1, store)
    assert list_todos(store) == []


# ---- 展示格式 ----


def test_format_todo_without_due_unchanged():
    todo = {"id": 2, "title": "买牛奶", "done": False}
    assert format_todo(todo, today=TODAY) == "[2] 买牛奶"


def test_format_todo_with_future_due():
    todo = {"id": 3, "title": "交房租", "done": False, "due": "2026-09-30"}
    assert format_todo(todo, today=TODAY) == "[3] 交房租 (due: 2026-09-30)"


def test_format_todo_overdue_appends_marker():
    todo = {"id": 1, "title": "还书", "done": False, "due": "2026-09-20"}
    assert (
        format_todo(todo, today=TODAY) == "[1] 还书 (due: 2026-09-20) [OVERDUE]"
    )


# ---- 存储形态 ----


def test_add_with_due_stores_iso_string(tmp_path: Path):
    store = tmp_path / ".todos.json"
    add_todo("t", store, due=date(2026, 9, 30))
    data = json.loads(store.read_text(encoding="utf-8"))
    assert data["todos"][0]["due"] == "2026-09-30"


def test_add_without_due_omits_key(tmp_path: Path):
    store = tmp_path / ".todos.json"
    add_todo("t", store)
    data = json.loads(store.read_text(encoding="utf-8"))
    assert "due" not in data["todos"][0]


# ---- 旧文件兼容 ----


def test_legacy_file_without_due_lists_safely(tmp_path: Path):
    store = tmp_path / ".todos.json"
    store.write_text(
        json.dumps({"todos": [{"id": 1, "title": "旧任务", "done": False}]}),
        encoding="utf-8",
    )
    items = list_todos(store)
    assert [format_todo(t, today=TODAY) for t in items] == ["[1] 旧任务"]


def test_malformed_due_in_file_treated_as_no_due(tmp_path: Path):
    store = tmp_path / ".todos.json"
    store.write_text(
        json.dumps(
            {"todos": [{"id": 1, "title": "t", "done": False, "due": "not-a-date"}]}
        ),
        encoding="utf-8",
    )
    items = list_todos(store)
    assert format_todo(items[0], today=TODAY) == "[1] t"


# ---- 端到端（CLI） ----


def test_cli_list_marks_overdue(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    add_todo("过期任务", due=date(2000, 1, 1))
    add_todo("未来任务", due=date(2999, 12, 31))
    add_todo("无截止任务")

    assert main(["list"]) == 0
    assert capsys.readouterr().out.splitlines() == [
        "[1] 过期任务 (due: 2000-01-01) [OVERDUE]",
        "[2] 未来任务 (due: 2999-12-31)",
        "[3] 无截止任务",
    ]


def test_cli_add_output_unchanged_without_due(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert main(["add", "Buy milk"]) == 0
    assert capsys.readouterr().out == "Added #1: Buy milk\n"

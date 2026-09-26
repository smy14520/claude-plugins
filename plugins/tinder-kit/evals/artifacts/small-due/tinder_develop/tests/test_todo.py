import json
from datetime import date
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


def test_add_with_due_stores_iso_string(tmp_path: Path):
    store = tmp_path / ".todos.json"
    item = add_todo("Pay rent", store, due="2026-10-01")
    assert item["due"] == "2026-10-01"


def test_add_without_due_omits_key(tmp_path: Path):
    store = tmp_path / ".todos.json"
    item = add_todo("Buy milk", store)
    assert "due" not in item


def test_add_rejects_invalid_due_before_write(tmp_path: Path):
    store = tmp_path / ".todos.json"
    with pytest.raises(ValueError):
        add_todo("Bad", store, due="not-a-date")
    assert not store.exists()  # 脏数据永不落盘


def test_add_canonicalizes_lenient_date(tmp_path: Path):
    store = tmp_path / ".todos.json"
    assert add_todo("T", store, due="2026-1-5")["due"] == "2026-01-05"


def test_old_file_without_due_stays_compatible(tmp_path: Path):
    store = tmp_path / ".todos.json"
    store.write_text(
        json.dumps({"todos": [{"id": 1, "title": "Legacy", "done": False}]}),
        encoding="utf-8",
    )
    new = add_todo("New", store, due="2020-01-01")
    assert new["id"] == 2

    done_todo(2, store)
    data = json.loads(store.read_text(encoding="utf-8"))
    # 旧记录原样保留，无 due 键
    assert data["todos"][0] == {"id": 1, "title": "Legacy", "done": False}
    # 新记录的 due 在全量重写保存后不丢失
    assert data["todos"][1]["due"] == "2020-01-01"
    assert is_overdue(data["todos"][0], date(2026, 9, 26)) is False


def test_is_overdue_truth_table():
    today = date(2026, 9, 26)
    assert is_overdue({"done": False, "due": "2026-09-25"}, today) is True  # 已过期
    assert is_overdue({"done": False, "due": "2026-09-26"}, today) is False  # 当天不算逾期
    assert is_overdue({"done": False, "due": "2026-09-27"}, today) is False  # 未来
    assert is_overdue({"done": True, "due": "2026-09-25"}, today) is False  # 已完成不标
    assert is_overdue({"done": False}, today) is False  # 无 due
    assert is_overdue({"done": False, "due": "not-a-date"}, today) is False  # 脏数据不崩溃
    assert is_overdue({"done": False, "due": 20261001}, today) is False  # 数字型脏数据不崩溃


def test_cli_list_marks_overdue(tmp_path: Path, capsys, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert main(["add", "Old task", "--due", "2020-01-01"]) == 0
    assert main(["add", "Future task", "--due", "2999-12-31"]) == 0
    capsys.readouterr()  # 排空 add 的输出，只断言 list 的行
    assert main(["list"]) == 0
    out = capsys.readouterr().out.splitlines()
    assert out == ["[1] Old task [OVERDUE]", "[2] Future task"]


def test_cli_rejects_invalid_due(tmp_path: Path, capsys, monkeypatch):
    monkeypatch.chdir(tmp_path)
    rc = main(["add", "Bad", "--due", "2026-13-99"])
    assert rc == 1
    assert "invalid" in capsys.readouterr().err.lower()
    assert not (tmp_path / ".todos.json").exists()

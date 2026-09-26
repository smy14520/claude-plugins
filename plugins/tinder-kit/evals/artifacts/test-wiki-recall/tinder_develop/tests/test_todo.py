import json
from datetime import date
from pathlib import Path

import pytest

from todo import add_todo, done_todo, format_todo, list_todos, load_todos, main, parse_due


def test_basic_crud(tmp_path: Path):
    store = tmp_path / ".todos.json"
    t1 = add_todo("Buy milk", store)
    assert t1["id"] == 1
    assert len(list_todos(store)) == 1

    done_todo(1, store)
    assert len(list_todos(store)) == 0


# --- Seam 1: --due 解析与校验 ---


def test_parse_due_accepts_iso_date():
    assert parse_due("2026-10-01") == date(2026, 10, 1)


def test_parse_due_rejects_bad_format():
    for bad in ["01/10/2026", "2026-13-01", "20261001", "2026-9-1", "not-a-date", ""]:
        with pytest.raises(ValueError):
            parse_due(bad)


# --- Seam 2: add 存储 due，向后兼容 ---


def test_add_todo_with_due(tmp_path: Path):
    store = tmp_path / ".todos.json"
    item = add_todo("还书", store, due=date(2026, 9, 20))
    assert item["due"] == "2026-09-20"
    assert list_todos(store)[0]["due"] == "2026-09-20"


def test_add_todo_without_due_keeps_legacy_shape(tmp_path: Path):
    store = tmp_path / ".todos.json"
    item = add_todo("Buy milk", store)
    assert "due" not in item


def test_load_legacy_file_without_due_keys(tmp_path: Path):
    store = tmp_path / ".todos.json"
    store.write_text(
        json.dumps({"todos": [{"id": 1, "title": "legacy", "done": False}]}),
        encoding="utf-8",
    )
    todos = list_todos(store)
    assert [t["title"] for t in todos] == ["legacy"]
    assert "due" not in todos[0]


# --- Seam 3: list 渲染（DEADLINE 前缀 + OVERDUE 标注）---


def test_format_todo_plain():
    assert format_todo({"id": 1, "title": "Buy milk"}, date(2026, 9, 26)) == "[1] Buy milk"


def test_format_todo_with_deadline_prefix():
    item = {"id": 1, "title": "买牛奶", "due": "2026-10-01"}
    assert format_todo(item, date(2026, 9, 26)) == "[1] 买牛奶 (DEADLINE: 2026-10-01)"


def test_format_todo_overdue_suffix():
    item = {"id": 1, "title": "还书", "due": "2026-09-20"}
    assert format_todo(item, date(2026, 9, 26)) == "[1] 还书 (DEADLINE: 2026-09-20) [OVERDUE]"


def test_format_todo_due_today_is_not_overdue():
    item = {"id": 1, "title": "还书", "due": "2026-09-26"}
    assert "[OVERDUE]" not in format_todo(item, date(2026, 9, 26))


# --- CLI 层：非法 --due 走 ADR 0001 的 exit 42 ---


def test_main_add_invalid_due_exits_42(tmp_path: Path, capsys, monkeypatch):
    monkeypatch.chdir(tmp_path)
    rc = main(["add", "task", "--due", "2026/10/01"])
    assert rc == 42
    err = capsys.readouterr().err
    assert "2026/10/01" in err
    assert "YYYY-MM-DD" in err
    assert main(["add", "task", "--due", "2026-9-1"]) == 42  # 非严格 YYYY-MM-DD 写法同样拒绝（裁决②）


def test_main_argparse_failures_exit_42(tmp_path: Path, monkeypatch, capsys):
    """裁决①：argparse 解析失败不保留默认 exit 2，一律 42（ADR 0001）。"""
    monkeypatch.chdir(tmp_path)
    for argv in (["done", "abc"], ["bogus"], ["add"], ["add", "t", "--due"]):
        with pytest.raises(SystemExit) as excinfo:
            main(argv)
        assert excinfo.value.code == 42
    err = capsys.readouterr().err
    assert "error" in err  # stderr 上有友好报错而非静默


# --- 裁决③：加载时 due 缺失或损坏按 null 兼容，绝不崩溃 ---


def test_load_treats_missing_or_corrupt_due_as_null(tmp_path: Path):
    store = tmp_path / ".todos.json"
    store.write_text(
        json.dumps({"todos": [
            {"id": 1, "title": "corrupt", "done": False, "due": "20/20/2026"},
            {"id": 2, "title": "padded", "done": False, "due": "2026-9-1"},
            {"id": 3, "title": "explicit-null", "done": False, "due": None},
            {"id": 4, "title": "missing", "done": False},
        ]}),
        encoding="utf-8",
    )
    todos = load_todos(store)
    # 损坏/显式 null 归一为 due=None；原缺失的键保持缺失（渲染端 .get 统一按 null 处理）
    assert [t.get("due") for t in todos] == [None, None, None, None]
    assert "due" not in todos[3]


def test_main_list_survives_corrupt_due(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    Path(".todos.json").write_text(
        json.dumps({"todos": [{"id": 1, "title": "legacy", "done": False, "due": "oops"}]}),
        encoding="utf-8",
    )
    assert main(["list"]) == 0
    assert capsys.readouterr().out.strip() == "[1] legacy"

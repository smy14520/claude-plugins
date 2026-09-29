import csv
import json
import re
from datetime import datetime, timezone

import pytest

import todo

UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


def test_add_generates_uuid_and_lists_short_prefix(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(todo, "DB", tmp_path / ".todos.json")
    todo.add("买牛奶")
    capsys.readouterr()  # 丢弃 add 自己的输出，只断言 list 的
    (t,) = todo.load()
    assert UUID_RE.fullmatch(t["id"])
    todo.list_todos()
    assert capsys.readouterr().out.splitlines() == [f"[{t['id'][:8]}] 买牛奶"]


def test_add_stamps_updated_at_utc(tmp_path, monkeypatch):
    monkeypatch.setattr(todo, "DB", tmp_path / ".todos.json")
    before = datetime.now(timezone.utc)
    todo.add("写周报")
    after = datetime.now(timezone.utc)
    (t,) = todo.load()
    stamp = datetime.fromisoformat(t["updated_at"])
    assert before <= stamp <= after


def test_load_backfills_legacy_record_with_epoch_without_touching_file(tmp_path, monkeypatch):
    db = tmp_path / ".todos.json"
    monkeypatch.setattr(todo, "DB", db)
    db.write_text(json.dumps([{"id": 3, "title": "旧任务", "done": False}]), encoding="utf-8")
    raw_before = db.read_text(encoding="utf-8")
    (t,) = todo.load()
    assert t["updated_at"] == "1970-01-01T00:00:00+00:00"
    assert db.read_text(encoding="utf-8") == raw_before  # load 只读，todo-sync 直接读这个文件


def test_done_accepts_full_uuid(tmp_path, monkeypatch):
    monkeypatch.setattr(todo, "DB", tmp_path / ".todos.json")
    todo.add("买牛奶")
    (t,) = todo.load()
    todo.done(t["id"])
    (after,) = todo.load()
    assert after["done"] is True


def test_done_accepts_legacy_integer_id(tmp_path, monkeypatch):
    db = tmp_path / ".todos.json"
    monkeypatch.setattr(todo, "DB", db)
    db.write_text(json.dumps([{"id": 3, "title": "旧任务", "done": False}]), encoding="utf-8")
    todo.done("3")
    (t,) = todo.load()
    assert t["done"] is True
    assert t["updated_at"] != "1970-01-01T00:00:00+00:00"  # 真实变更盖真实时间，不再是回填值


def test_done_accepts_unique_uuid_prefix(tmp_path, monkeypatch):
    monkeypatch.setattr(todo, "DB", tmp_path / ".todos.json")
    todo.add("买牛奶")
    todo.add("写周报")
    t1, t2 = todo.load()
    todo.done(t1["id"][:8])  # 约定的 8 位短前缀
    after = todo.load()
    assert [t["done"] for t in after] == [True, False]


def test_done_ambiguous_prefix_errors_without_change(tmp_path, monkeypatch, capsys):
    db = tmp_path / ".todos.json"
    monkeypatch.setattr(todo, "DB", db)
    db.write_text(json.dumps([
        {"id": "aaaa0000-1111-4222-8333-444444444444", "title": "甲", "done": False},
        {"id": "aaaa0000-2222-4333-8444-555555555555", "title": "乙", "done": False},
    ]), encoding="utf-8")
    with pytest.raises(SystemExit) as e:
        todo.done("aaaa0000")
    assert e.value.code == 1
    assert "ambiguous id: aaaa0000" in capsys.readouterr().err
    assert all(not t["done"] for t in todo.load())  # 报错时不产生任何变更


def test_done_unknown_id_errors(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(todo, "DB", tmp_path / ".todos.json")
    todo.add("买牛奶")
    with pytest.raises(SystemExit) as e:
        todo.done("deadbeef")
    assert e.value.code == 1
    assert "no such todo: deadbeef" in capsys.readouterr().err


def test_done_twice_keeps_first_updated_at(tmp_path, monkeypatch):
    monkeypatch.setattr(todo, "DB", tmp_path / ".todos.json")
    stamps = iter(["2026-09-29T00:00:01+00:00", "2026-09-29T00:00:02+00:00", "2026-09-29T00:00:03+00:00"])
    monkeypatch.setattr(todo, "_now", lambda: next(stamps))
    todo.add("买牛奶")
    todo_id = todo.load()[0]["id"]
    todo.done(todo_id)
    todo.done(todo_id)  # 第二次无状态变化，不应刷新 updated_at
    (t,) = todo.load()
    assert t["updated_at"] == "2026-09-29T00:00:02+00:00"


def test_list_shows_legacy_integer_id_verbatim(tmp_path, monkeypatch, capsys):
    db = tmp_path / ".todos.json"
    monkeypatch.setattr(todo, "DB", db)
    db.write_text(json.dumps([{"id": 123456789, "title": "旧任务", "done": False}]), encoding="utf-8")
    todo.list_todos()
    assert capsys.readouterr().out.splitlines() == ["[123456789] 旧任务"]


def test_done_prefix_never_matches_legacy_ids(tmp_path, monkeypatch, capsys):
    db = tmp_path / ".todos.json"
    monkeypatch.setattr(todo, "DB", db)
    db.write_text(json.dumps([{"id": 12, "title": "旧任务", "done": False}]), encoding="utf-8")
    with pytest.raises(SystemExit) as e:
        todo.done("1")  # 前缀匹配只作用于 uuid，不得误命中整数 12
    assert e.value.code == 1
    assert "no such todo: 1" in capsys.readouterr().err


def test_export_writes_rows(tmp_path, monkeypatch):
    monkeypatch.setattr(todo, "DB", tmp_path / ".todos.json")
    todo.add("写周报")
    (t,) = todo.load()
    out = tmp_path / "out.csv"
    todo.export(str(out))
    rows = list(csv.reader(out.open(encoding="utf-8")))
    # 列名与列顺序是 report_todos.py 依赖的契约，不得变动；updated_at 不导出
    assert rows == [["id", "title", "done"], [t["id"], "写周报", "False"]]

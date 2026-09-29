import csv
import json
import subprocess
import sys
import uuid
from pathlib import Path

import todo


def parse_id(text: str) -> str:
    return text.split("]")[0].lstrip("[")


def test_add_assigns_uuid_id(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(todo, "DB", tmp_path / ".todos.json")
    todo.add("买牛奶")
    line = capsys.readouterr().out.strip()
    assert uuid.UUID(parse_id(line)).version == 4


def test_add_then_list(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(todo, "DB", tmp_path / ".todos.json")
    todo.add("买牛奶")
    todo.list_todos()
    lines = capsys.readouterr().out.splitlines()
    assert lines[-1] == f"[{parse_id(lines[0])}] 买牛奶"


def test_export_writes_rows(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(todo, "DB", tmp_path / ".todos.json")
    todo.add("写周报")
    todo_id = parse_id(capsys.readouterr().out)
    out = tmp_path / "out.csv"
    todo.export(str(out))
    rows = list(csv.reader(out.open(encoding="utf-8")))
    assert rows == [["id", "title", "done"], [todo_id, "写周报", "False"]]


def test_done_accepts_legacy_int_id(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(todo, "DB", tmp_path / ".todos.json")
    todo.DB.write_text(
        json.dumps([{"id": 7, "title": "旧任务", "done": False}]), encoding="utf-8"
    )
    todo.add("新任务")
    capsys.readouterr()
    todo.done("7")
    todo.list_todos()
    out = capsys.readouterr().out
    assert "旧任务" not in out
    assert "新任务" in out


def test_done_accepts_int_argument(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(todo, "DB", tmp_path / ".todos.json")
    todo.DB.write_text(
        json.dumps([{"id": 7, "title": "旧任务", "done": False}]), encoding="utf-8"
    )
    todo.done(7)
    todo.list_todos()
    assert "旧任务" not in capsys.readouterr().out


def test_cli_done_accepts_uuid(tmp_path):
    script = str(Path(__file__).resolve().parent.parent / "todo.py")
    added = subprocess.run(
        [sys.executable, script, "add", "CLI任务"],
        cwd=tmp_path, capture_output=True, text=True,
    )
    done = subprocess.run(
        [sys.executable, script, "done", parse_id(added.stdout)],
        cwd=tmp_path, capture_output=True, text=True,
    )
    assert done.returncode == 0
    listed = subprocess.run(
        [sys.executable, script],
        cwd=tmp_path, capture_output=True, text=True,
    )
    assert listed.stdout.strip() == ""


def test_cli_done_accepts_legacy_int_id(tmp_path):
    script = str(Path(__file__).resolve().parent.parent / "todo.py")
    (tmp_path / ".todos.json").write_text(
        json.dumps([{"id": 7, "title": "旧任务", "done": False}]), encoding="utf-8"
    )
    done = subprocess.run(
        [sys.executable, script, "done", "7"],
        cwd=tmp_path, capture_output=True, text=True,
    )
    assert done.returncode == 0
    listed = subprocess.run(
        [sys.executable, script],
        cwd=tmp_path, capture_output=True, text=True,
    )
    assert listed.stdout.strip() == ""
    # 存量 id 原样保留：done 落盘后文件里仍是整数，不做静默迁移
    stored = json.loads((tmp_path / ".todos.json").read_text(encoding="utf-8"))
    assert stored[0]["id"] == 7

import json

import todo


def test_add_then_list(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(todo, "DB", tmp_path / ".todos.json")
    todo.add("买牛奶")
    todo.list_todos()
    assert capsys.readouterr().out.splitlines()[-1] == "[1] 买牛奶"


def test_export_writes_json(tmp_path, monkeypatch):
    monkeypatch.setattr(todo, "DB", tmp_path / ".todos.json")
    todo.add("写周报")
    out = tmp_path / "out.json"
    todo.export(str(out))
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data == [{"id": 1, "title": "写周报", "done": False}]

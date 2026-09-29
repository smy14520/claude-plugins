import csv

import todo


def test_add_then_list(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(todo, "DB", tmp_path / ".todos.json")
    todo.add("买牛奶")
    todo.list_todos()
    assert capsys.readouterr().out.splitlines()[-1] == "[1] 买牛奶"


def test_export_writes_rows(tmp_path, monkeypatch):
    monkeypatch.setattr(todo, "DB", tmp_path / ".todos.json")
    todo.add("写周报")
    out = tmp_path / "out.csv"
    todo.export(str(out))
    rows = list(csv.reader(out.open(encoding="utf-8")))
    assert rows == [["id", "title", "done"], ["1", "写周报", "False"]]

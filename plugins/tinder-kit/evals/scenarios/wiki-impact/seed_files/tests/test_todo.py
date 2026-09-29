import todo


def test_add_then_list(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(todo, "DB", tmp_path / ".todos.json")
    todo.add("买牛奶")
    todo.list_todos()
    assert capsys.readouterr().out.splitlines()[-1] == "[1] 买牛奶"


def test_done_hides_item(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(todo, "DB", tmp_path / ".todos.json")
    todo.add("写周报")
    todo.done(1)
    capsys.readouterr()
    todo.list_todos()
    assert capsys.readouterr().out == ""

"""stock list 行为测试。"""

from stock.cli import main


def test_list_empty_inventory_prints_empty_marker(tmp_path, capsys):
    rc = main(["--db", str(tmp_path / "stock.json"), "list"])
    captured = capsys.readouterr()
    assert rc == 0
    assert captured.out == "(empty)\n"
    assert captured.err == ""


def test_list_prints_items_sorted_by_name(tmp_path, capsys):
    db = tmp_path / "stock.json"
    db.write_text('{"banana": 2, "apple": 5}\n', encoding="utf-8")
    rc = main(["--db", str(db), "list"])
    captured = capsys.readouterr()
    assert rc == 0
    assert captured.out == "apple: 5\nbanana: 2\n"
    assert captured.err == ""

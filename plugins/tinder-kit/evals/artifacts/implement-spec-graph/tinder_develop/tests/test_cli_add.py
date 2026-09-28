"""`stock add <name> <qty>` 入库命令的行为测试。"""

import pytest

from stock.cli import main
from stock.store import Store


def test_add_new_item_prints_and_persists(tmp_path, capsys):
    db = tmp_path / "stock.json"
    rc = main(["--db", str(db), "add", "苹果", "3"])
    assert rc == 0
    captured = capsys.readouterr()
    assert captured.out == "苹果: 3\n"
    assert captured.err == ""
    assert Store(db).load() == {"苹果": 3}


def test_add_existing_item_accumulates(tmp_path, capsys):
    db = tmp_path / "stock.json"
    assert main(["--db", str(db), "add", "苹果", "3"]) == 0
    capsys.readouterr()
    rc = main(["--db", str(db), "add", "苹果", "2"])
    assert rc == 0
    captured = capsys.readouterr()
    assert captured.out == "苹果: 5\n"
    assert captured.err == ""
    assert Store(db).load() == {"苹果": 5}


@pytest.mark.parametrize("qty", ["0", "-1", "abc", "1.5", "1_0", "３", "+3", " 3"])
def test_add_invalid_qty_errors_and_keeps_stock(qty, tmp_path, capsys):
    db = tmp_path / "stock.json"
    assert main(["--db", str(db), "add", "苹果", "3"]) == 0
    capsys.readouterr()

    rc = main(["--db", str(db), "add", "苹果", qty])

    assert rc == 1
    out = capsys.readouterr()
    assert out.out == ""
    assert out.err == f"error: 数量必须是正整数: {qty}\n"
    assert Store(db).load() == {"苹果": 3}

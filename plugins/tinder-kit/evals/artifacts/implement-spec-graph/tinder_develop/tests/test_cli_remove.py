"""`stock remove <name> <qty>` 出库命令的行为测试。"""

from pathlib import Path

import pytest

from stock.cli import main
from stock.store import Store


def seed(tmp_path: Path, items: dict[str, int]) -> Path:
    db = tmp_path / "stock.json"
    Store(db).save(items)
    return db


def test_remove_deducts_and_persists(tmp_path, capsys):
    db = seed(tmp_path, {"苹果": 5})
    rc = main(["--db", str(db), "remove", "苹果", "2"])
    assert rc == 0
    out, err = capsys.readouterr()
    assert out == "苹果: 3\n"
    assert err == ""
    assert Store(db).load() == {"苹果": 3}


def test_remove_to_zero_deletes_item_but_prints_zero(tmp_path, capsys):
    db = seed(tmp_path, {"苹果": 2})
    rc = main(["--db", str(db), "remove", "苹果", "2"])
    assert rc == 0
    out, err = capsys.readouterr()
    assert out == "苹果: 0\n"
    assert err == ""
    assert Store(db).load() == {}


def test_remove_missing_item_errors_and_keeps_inventory(tmp_path, capsys):
    db = seed(tmp_path, {"苹果": 5})
    rc = main(["--db", str(db), "remove", "香蕉", "1"])
    assert rc == 1
    out, err = capsys.readouterr()
    assert out == ""
    assert err == "error: 商品不存在: 香蕉\n"
    assert Store(db).load() == {"苹果": 5}


def test_remove_insufficient_stock_errors_and_keeps_inventory(tmp_path, capsys):
    db = seed(tmp_path, {"苹果": 2})
    rc = main(["--db", str(db), "remove", "苹果", "3"])
    assert rc == 1
    out, err = capsys.readouterr()
    assert out == ""
    assert err == "error: 库存不足: 苹果\n"
    assert Store(db).load() == {"苹果": 2}


@pytest.mark.parametrize("qty", ["abc", "0", "-1", "1.5"])
def test_remove_invalid_qty_errors_and_keeps_inventory(tmp_path, capsys, qty):
    db = seed(tmp_path, {"苹果": 5})
    rc = main(["--db", str(db), "remove", "苹果", qty])
    assert rc == 1
    out, err = capsys.readouterr()
    assert out == ""
    assert err == f"error: 数量必须是正整数: {qty}\n"
    assert Store(db).load() == {"苹果": 5}

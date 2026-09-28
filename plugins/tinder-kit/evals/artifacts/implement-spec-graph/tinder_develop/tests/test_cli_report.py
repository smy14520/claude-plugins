"""stock report 补货报告行为测试。"""

import pytest

from stock.cli import main
from stock.store import Store


def test_report_default_threshold_lists_items_below_5_sorted(tmp_path, capsys):
    db = tmp_path / "stock.json"
    db.write_text('{"banana": 2, "apple": 7, "cherry": 4}\n', encoding="utf-8")
    rc = main(["--db", str(db), "report"])
    captured = capsys.readouterr()
    assert rc == 0
    assert captured.out == "banana: 2\ncherry: 4\n"
    assert captured.err == ""


def test_report_includes_only_items_strictly_below_threshold(tmp_path, capsys):
    db = tmp_path / "stock.json"
    db.write_text('{"apple": 5, "banana": 4}\n', encoding="utf-8")
    rc = main(["--db", str(db), "report"])
    captured = capsys.readouterr()
    assert rc == 0
    assert captured.out == "banana: 4\n"
    assert captured.err == ""


def test_report_custom_threshold(tmp_path, capsys):
    db = tmp_path / "stock.json"
    db.write_text('{"apple": 10, "banana": 9}\n', encoding="utf-8")
    rc = main(["--db", str(db), "report", "--threshold", "10"])
    captured = capsys.readouterr()
    assert rc == 0
    assert captured.out == "banana: 9\n"
    assert captured.err == ""


def test_report_no_low_stock_prints_nothing_to_restock(tmp_path, capsys):
    db = tmp_path / "stock.json"
    db.write_text('{"apple": 5, "banana": 9}\n', encoding="utf-8")
    rc = main(["--db", str(db), "report"])
    captured = capsys.readouterr()
    assert rc == 0
    assert captured.out == "nothing to restock\n"
    assert captured.err == ""


def test_report_empty_inventory_prints_nothing_to_restock(tmp_path, capsys):
    rc = main(["--db", str(tmp_path / "stock.json"), "report"])
    captured = capsys.readouterr()
    assert rc == 0
    assert captured.out == "nothing to restock\n"
    assert captured.err == ""


@pytest.mark.parametrize("threshold", ["abc", "0", "-2", "2.5", "１０"])
def test_report_invalid_threshold_errors_and_keeps_stock(threshold, tmp_path, capsys):
    db = tmp_path / "stock.json"
    db.write_text('{"apple": 3}\n', encoding="utf-8")
    rc = main(["--db", str(db), "report", "--threshold", threshold])
    out = capsys.readouterr()
    assert rc == 1
    assert out.out == ""
    assert out.err == f"error: 阈值必须是正整数: {threshold}\n"
    assert Store(db).load() == {"apple": 3}

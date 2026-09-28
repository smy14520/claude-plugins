from stock.store import Store


def test_missing_file_loads_empty(tmp_path):
    assert Store(tmp_path / "stock.json").load() == {}


def test_save_then_load_round_trips(tmp_path):
    store = Store(tmp_path / "stock.json")
    store.save({"苹果": 3})
    assert store.load() == {"苹果": 3}

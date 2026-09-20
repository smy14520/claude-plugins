"""Seam 1：存储层往返契约。

观测面仅 storage.load / storage.save 两个公共函数：
往返无损、缺省空表、原子写（临时文件 + rename）、中文 UTF-8。
"""

import json

import storage


def test_load_missing_file_returns_empty_list(tmp_path):
    assert storage.load(tmp_path / "absent.json") == []


def test_save_then_load_roundtrip_preserves_all_fields(tmp_path):
    path = tmp_path / ".todos.json"
    todos = [
        {
            "id": 1,
            "text": "买牛奶",
            "tags": ["shopping", "urgent"],
            "priority": "high",
            "done": False,
            "created_at": "2026-09-20T02:00:00+00:00",
        },
        {
            "id": 2,
            "text": "写周报",
            "tags": [],
            "priority": "low",
            "done": True,
            "created_at": "2026-09-19T08:30:00+00:00",
        },
    ]
    storage.save(path, todos)
    assert storage.load(path) == todos


def test_save_writes_utf8_json_array_with_chinese(tmp_path):
    path = tmp_path / ".todos.json"
    todo = {
        "id": 1,
        "text": "买牛奶",
        "tags": ["购物"],
        "priority": "med",
        "done": False,
        "created_at": "2026-09-20T00:00:00+00:00",
    }
    storage.save(path, [todo])

    raw = path.read_bytes()
    decoded = raw.decode("utf-8")  # 中文必须以 UTF-8 原字符落盘，而非 \\u 转义
    assert "买牛奶" in decoded
    assert json.loads(decoded) == [todo]  # 文件形状是 JSON 数组


def test_save_fully_replaces_previous_content(tmp_path):
    path = tmp_path / ".todos.json"
    storage.save(path, [{"id": i, "text": f"旧任务{i}" * 20} for i in range(5)])
    storage.save(path, [{"id": 9, "text": "新任务"}])
    assert storage.load(path) == [{"id": 9, "text": "新任务"}]


def test_save_is_atomic_no_temp_leftovers(tmp_path):
    """原子写的行为侧证据：落盘后目录里只剩目标文件，无残留临时文件。"""
    path = tmp_path / ".todos.json"
    storage.save(path, [{"id": 1, "text": "甲"}])
    storage.save(path, [{"id": 2, "text": "乙"}])

    leftovers = [p.name for p in tmp_path.iterdir() if p.name != path.name]
    assert leftovers == []
    assert storage.load(path) == [{"id": 2, "text": "乙"}]

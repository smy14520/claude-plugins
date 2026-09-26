"""core.py 纯领域函数测试。

Seam：AND Tag 过滤、id 分配、两态翻转、Tag 解析。
只喂最小 dict（函数只读它需要的键），期望值为手写 literal。
"""

from todo import core


def todo_stub(i, tags):
    """过滤测试专用最小 Todo：过滤逻辑只关心 tags。"""
    return {"id": i, "tags": tags}


def todos_multi():
    """三味样本：1 带 工作+紧急，2 只带 工作，3 带 生活+紧急。"""
    return [
        todo_stub(1, ["工作", "紧急"]),
        todo_stub(2, ["工作"]),
        todo_stub(3, ["生活", "紧急"]),
    ]


# --- AND Tag 过滤 ---


def test_filter_by_tags_requires_every_tag():
    """AND 语义：两个 Tag 条件，只命中同时全带的 Todo。"""
    todos = todos_multi()
    assert [x["id"] for x in core.filter_by_tags(todos, ["工作", "紧急"])] == [1]


def test_filter_by_tags_single_tag():
    assert [x["id"] for x in core.filter_by_tags(todos_multi(), ["紧急"])] == [1, 3]


def test_filter_by_tags_no_match_returns_empty():
    """交集为空是正常路径：返回空列表，不报错。"""
    assert core.filter_by_tags(todos_multi(), ["不存在"]) == []


def test_filter_by_tags_empty_query_returns_all():
    """不带过滤条件 = 不筛选，原序全量返回。"""
    todos = todos_multi()
    assert core.filter_by_tags(todos, []) == todos


# --- id 分配 ---


def test_next_id_starts_at_one_for_empty_list():
    assert core.next_id([]) == 1


def test_next_id_is_max_plus_one():
    """有空洞也不回填：最大 id + 1（1,2,5 → 6）。"""
    assert core.next_id([{"id": 2}, {"id": 5}, {"id": 1}]) == 6


# --- 两态翻转 ---


def test_mark_done_sets_status_and_timestamp_without_touching_original():
    original = {"id": 1, "status": "open", "completed_at": None}
    done = core.mark_done(original, now="2026-09-26T09:00:00+00:00")
    assert done["status"] == "done"
    assert done["completed_at"] == "2026-09-26T09:00:00+00:00"
    assert original["status"] == "open"  # 纯函数：原对象不被修改


def test_mark_open_resets_to_open_and_clears_timestamp():
    undone = core.mark_open({"id": 1, "status": "done", "completed_at": "X"})
    assert undone["status"] == "open"
    assert undone["completed_at"] is None


# --- Tag 解析 ---


def test_parse_tags_splits_strips_dedupes_and_drops_empties():
    assert core.parse_tags("a, b,,c,a") == ["a", "b", "c"]


def test_parse_tags_empty_string_gives_empty_list():
    assert core.parse_tags("") == []

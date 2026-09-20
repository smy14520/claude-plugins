"""Seam 2：领域逻辑契约 —— 标签解析 / 优先级 / 过滤 / 排序。

观测面为 domain 模块的纯函数；不触碰任何 I/O。
"""

import pytest

import domain


class TestParseText:
    def test_extracts_inline_tags_from_text(self):
        text, tags = domain.parse_text("买牛奶 +shopping +urgent")
        assert text == "买牛奶"
        assert tags == ["shopping", "urgent"]

    def test_every_plus_token_is_collected_as_tag(self):
        text, tags = domain.parse_text("+foo 随便什么 +bar")
        assert text == "随便什么"
        assert tags == ["bar", "foo"]

    def test_dedupes_and_sorts_tags(self):
        _, tags = domain.parse_text("+b +a +a")
        assert tags == ["a", "b"]

    def test_plain_text_without_tags(self):
        assert domain.parse_text("只是普通文本") == ("只是普通文本", [])

    def test_bare_plus_stays_in_text(self):
        text, tags = domain.parse_text("+ 加号")
        assert text == "+ 加号"
        assert tags == []

    def test_inner_plus_is_not_a_tag(self):
        text, tags = domain.parse_text("1+1 算式")
        assert text == "1+1 算式"
        assert tags == []


class TestValidatePriority:
    @pytest.mark.parametrize("value", ["high", "med", "low"])
    def test_accepts_exactly_three_levels(self, value):
        assert domain.validate_priority(value) == value

    @pytest.mark.parametrize("value", ["urgent", "HIGH", "", "high ", None, 1])
    def test_rejects_anything_else(self, value):
        with pytest.raises(ValueError):
            domain.validate_priority(value)


class TestIds:
    def test_next_id_starts_at_one_on_empty(self):
        assert domain.next_id([]) == 1

    def test_next_id_takes_max_plus_one(self):
        assert domain.next_id([{"id": 3}, {"id": 7}]) == 8


class TestNewTodo:
    def test_full_field_set_and_defaults(self):
        todo = domain.new_todo([], "买牛奶", ["shopping"], "high")
        assert todo["id"] == 1
        assert todo["text"] == "买牛奶"
        assert todo["tags"] == ["shopping"]
        assert todo["priority"] == "high"
        assert todo["done"] is False
        assert isinstance(todo["created_at"], str) and todo["created_at"]


class TestFilterAndSort:
    @staticmethod
    def _todo(id, tags, priority="med", done=False):
        return {"id": id, "text": f"t{id}", "tags": tags, "priority": priority, "done": done}

    def test_multiple_tag_filters_intersect(self):
        todos = [
            self._todo(1, ["x"]),
            self._todo(2, ["x", "y"]),
            self._todo(3, ["y", "z"]),
        ]
        picked = domain.filter_todos(todos, tags=["x", "y"])
        assert [t["id"] for t in picked] == [2]

    def test_no_tag_filter_keeps_all_open(self):
        todos = [self._todo(1, ["x"]), self._todo(2, [])]
        assert [t["id"] for t in domain.filter_todos(todos)] == [1, 2]

    def test_hides_done_by_default(self):
        todos = [self._todo(1, [], done=False), self._todo(2, [], done=True)]
        assert [t["id"] for t in domain.filter_todos(todos)] == [1]

    def test_show_done_includes_finished(self):
        todos = [self._todo(1, [], done=False), self._todo(2, [], done=True)]
        assert [t["id"] for t in domain.filter_todos(todos, show_done=True)] == [1, 2]

    def test_sorts_by_priority_then_id(self):
        todos = [
            self._todo(1, [], priority="low"),
            self._todo(2, [], priority="high"),
            self._todo(3, [], priority="med"),
            self._todo(4, [], priority="high"),
            self._todo(5, [], priority="med"),
        ]
        picked = domain.filter_todos(todos, show_done=True)
        assert [t["id"] for t in picked] == [2, 4, 3, 5, 1]

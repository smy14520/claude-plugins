"""todo.py 的单元测试。运行：python3 -m unittest discover -s tests"""
import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import todo


class TodoCliTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = Path(self.tmp.name) / "todos.json"
        env = mock.patch.dict(os.environ, {"TODO_STORE": str(self.store)})
        env.start()
        self.addCleanup(env.stop)

    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            todo.main(list(argv))
        return out.getvalue()

    def read_store(self):
        return json.loads(self.store.read_text(encoding="utf-8"))

    # --- add ---

    def test_add_creates_store_with_expected_fields(self):
        self.run_cli("add", "买牛奶", "-t", "跑腿,生活", "-p", "high")
        data = self.read_store()
        self.assertEqual(data["next_id"], 2)
        (todo,) = data["todos"]
        self.assertEqual(todo["id"], 1)
        self.assertEqual(todo["title"], "买牛奶")
        self.assertEqual(todo["tags"], ["跑腿", "生活"])
        self.assertEqual(todo["priority"], "high")
        self.assertFalse(todo["done"])
        self.assertIsNone(todo["completed_at"])
        self.assertTrue(todo["created_at"])
        # 中文不转义，肉眼可读
        self.assertIn("买牛奶", self.store.read_text(encoding="utf-8"))

    def test_add_title_joins_bare_words(self):
        self.run_cli("add", "修复", "登录", "bug")
        self.assertEqual(self.read_store()["todos"][0]["title"], "修复 登录 bug")

    def test_add_default_priority_is_med(self):
        self.run_cli("add", "随便一件事")
        self.assertEqual(self.read_store()["todos"][0]["priority"], "med")

    def test_tags_dedupe_across_flags_and_commas(self):
        self.run_cli("add", "x", "-t", "a", "-t", "a, b ,c")
        self.assertEqual(self.read_store()["todos"][0]["tags"], ["a", "b", "c"])

    def test_list_does_not_create_store(self):
        out = self.run_cli("list")
        self.assertIn("没有匹配", out)
        self.assertFalse(self.store.exists())

    # --- list / 过滤 / 排序 ---

    def test_list_hides_done_by_default(self):
        self.run_cli("add", "甲")
        self.run_cli("add", "乙")
        self.run_cli("done", "1")
        out = self.run_cli("list")
        self.assertNotIn("甲", out)
        self.assertIn("乙", out)
        self.assertIn("✓ 甲", self.run_cli("list", "--all"))
        self.assertIn("✓ 甲", self.run_cli("list", "--done"))
        self.assertNotIn("乙", self.run_cli("list", "--done"))

    def test_tag_filter_is_and(self):
        self.run_cli("add", "甲", "-t", "x,y")
        self.run_cli("add", "乙", "-t", "x")
        out = self.run_cli("list", "-t", "x", "-t", "y")
        self.assertIn("甲", out)
        self.assertNotIn("乙", out)

    def test_priority_filter_exact_match(self):
        self.run_cli("add", "甲", "-p", "high")
        self.run_cli("add", "乙", "-p", "low")
        out = self.run_cli("list", "-p", "low")
        self.assertIn("乙", out)
        self.assertNotIn("甲", out)

    def test_sort_by_priority_then_created(self):
        self.run_cli("add", "低", "-p", "low")
        self.run_cli("add", "高", "-p", "high")
        self.run_cli("add", "中")
        out = self.run_cli("list")
        self.assertLess(out.index("高"), out.index("中"))
        self.assertLess(out.index("中"), out.index("低"))

    # --- done / delete ---

    def test_done_sets_completed_at_and_is_idempotent(self):
        self.run_cli("add", "甲")
        self.run_cli("done", "1")
        first = self.read_store()["todos"][0]["completed_at"]
        self.assertTrue(first)
        out = self.run_cli("done", "1")
        self.assertIn("已是完成状态", out)
        self.assertEqual(self.read_store()["todos"][0]["completed_at"], first)

    def test_delete_removes_only_target_and_ids_not_reused(self):
        self.run_cli("add", "one")
        self.run_cli("add", "two")
        self.run_cli("delete", "2")
        self.run_cli("add", "three")
        todos = self.read_store()["todos"]
        self.assertEqual([t["id"] for t in todos], [1, 3])
        self.assertEqual([t["title"] for t in todos], ["one", "three"])

    def test_unknown_id_exits_1(self):
        self.run_cli("add", "甲")
        with self.assertRaises(SystemExit) as ctx:
            self.run_cli("done", "99")
        self.assertEqual(ctx.exception.code, 1)
        with self.assertRaises(SystemExit) as ctx:
            self.run_cli("delete", "99")
        self.assertEqual(ctx.exception.code, 1)

    # --- 持久化健壮性 ---

    def test_corrupt_store_aborts_without_writing(self):
        self.store.write_text("{ 坏掉的 JSON", encoding="utf-8")
        with self.assertRaises(SystemExit) as ctx:
            self.run_cli("add", "甲")
        self.assertEqual(ctx.exception.code, 1)
        self.assertEqual(self.store.read_text(encoding="utf-8"), "{ 坏掉的 JSON")

    def test_no_temp_files_left_behind(self):
        self.run_cli("add", "甲")
        self.run_cli("add", "乙")
        leftovers = [p.name for p in self.store.parent.iterdir() if p.name.startswith(".todos-")]
        self.assertEqual(leftovers, [])

    # --- CJK 对齐 ---

    def test_dwidth(self):
        self.assertEqual(todo.dwidth("ab"), 2)
        self.assertEqual(todo.dwidth("买菜"), 4)
        self.assertEqual(todo.dwidth("买a"), 3)


if __name__ == "__main__":
    unittest.main()

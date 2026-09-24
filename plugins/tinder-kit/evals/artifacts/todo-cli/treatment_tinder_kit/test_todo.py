"""todo.py 行为测试：全部经 main() 驱动，存储指向临时文件，绝不触碰真实 ~/.todos.json。

AC 对账映射：
  AC-1 add（标签/优先级）   → TestAdd
  AC-2 list（过滤/排序）    → TestList
  AC-3 done/rm（状态流转）  → TestDoneRm
  AC-4 持久化与 next_id     → TestPersistence
  AC-5 未知 id 容错         → TestErrors
  AC-6 帮助可用             → TestHelp
"""

import contextlib
import io
import json
import os
import shutil
import tempfile
import unittest
from unittest import mock

import todo


def run(*argv: str) -> tuple[int, str, str]:
    """驱动 CLI，返回 (退出码, stdout, stderr)；SystemExit（--help/参数错误）同样归一为退出码。"""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = todo.main(list(argv))
        except SystemExit as exc:
            code = exc.code
    return code, out.getvalue(), err.getvalue()


class TodoTestCase(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="todo-test-")
        self.store = os.path.join(self.dir, "todos.json")
        os.environ["TODO_FILE"] = self.store

    def tearDown(self):
        os.environ.pop("TODO_FILE", None)
        shutil.rmtree(self.dir, ignore_errors=True)

    def read_store(self) -> dict:
        with open(self.store, encoding="utf-8") as fh:
            return json.load(fh)


class TestPureFunctions(unittest.TestCase):
    """纯函数直测：无需存储隔离。"""
    def test_parse_tags_dedup_and_order(self):
        text, tags = todo.parse_tags("修复登录 #work #urgent #work 登录页")
        self.assertEqual(text, "修复登录 登录页")
        self.assertEqual(tags, ["work", "urgent"])

    def test_merge_tags_preserves_order_dedups(self):
        self.assertEqual(todo.merge_tags(["a", "b"], ["b", "c"]), ["a", "b", "c"])


class TestAdd(TodoTestCase):
    def test_inline_and_explicit_tags_merge_with_dedup(self):
        code, out, _ = run("add", "修复登录 #work #urgent", "-t", "work", "-t", "review")
        self.assertEqual(code, 0)
        task = self.read_store()["tasks"][0]
        self.assertEqual(task["text"], "修复登录")  # 正文已剥离 #tag
        self.assertEqual(task["tags"], ["work", "urgent", "review"])  # 去重保序
        self.assertFalse(task["done"])
        self.assertIsNotNone(task["created_at"])
        self.assertIsNone(task["completed_at"])

    def test_priority_defaults_to_med(self):
        run("add", "普通任务")
        self.assertEqual(self.read_store()["tasks"][0]["priority"], "med")

    def test_priority_explicit_high(self):
        run("add", "紧急任务", "-p", "high")
        self.assertEqual(self.read_store()["tasks"][0]["priority"], "high")

    def test_invalid_priority_rejected(self):
        code, _, err = run("add", "坏值", "-p", "urgent")
        self.assertEqual(code, 2)  # argparse 拒绝三档之外的值（审计契约：exit 2）
        self.assertTrue(err)

    def test_tag_only_text_rejected(self):
        code, _, err = run("add", "#work")
        self.assertEqual(code, 1)
        self.assertIn("正文不能为空", err)


class TestList(TodoTestCase):
    def setUp(self):
        super().setUp()
        run("add", "低优先 #a", "-p", "low")            # id 1
        run("add", "高优先一 #a #b", "-p", "high")       # id 2
        run("add", "中优先 #b")                          # id 3 (默认 med)
        run("add", "高优先二 #a", "-p", "high")          # id 4
        run("done", "3")

    def ids_in_output(self, out: str) -> list[int]:
        return [int(line.split()[0]) for line in out.splitlines() if line.strip()]

    def test_default_hides_done(self):
        code, out, _ = run("list")
        self.assertEqual(code, 0)
        self.assertEqual(self.ids_in_output(out), [2, 4, 1])  # 无 id 3

    def test_all_shows_everything(self):
        _, out, _ = run("list", "--all")
        self.assertEqual(self.ids_in_output(out), [2, 4, 3, 1])

    def test_done_shows_only_completed(self):
        _, out, _ = run("list", "--done")
        self.assertEqual(self.ids_in_output(out), [3])

    def test_multiple_tags_are_AND(self):
        _, out, _ = run("list", "-t", "a", "-t", "b")
        self.assertEqual(self.ids_in_output(out), [2])  # 仅 id 2 同时含 a 与 b

    def test_priority_filter_combines_with_tag_by_AND(self):
        run("add", "低优先a #a", "-p", "low")  # id 5
        _, out, _ = run("list", "-t", "a", "-p", "high")
        self.assertEqual(self.ids_in_output(out), [2, 4])  # 高优先且带 a，不含 id 5

    def test_sort_priority_major_id_minor(self):
        _, out, _ = run("list", "--all")
        self.assertEqual(self.ids_in_output(out), [2, 4, 3, 1])  # high(id 升序)→med→low

    def test_output_format_compact_line(self):
        _, out, _ = run("list", "-t", "b")
        line = [entry for entry in out.splitlines() if entry.strip()][0]
        self.assertIn("[ ]", line)
        self.assertIn("(high)", line)
        self.assertIn("#a #b", line)

    def test_empty_result_message(self):
        _, out, _ = run("list", "-t", "nope")
        self.assertIn("（无匹配待办）", out)

    def test_done_marker_rendered(self):
        _, out, _ = run("list", "--done")
        self.assertIn("[x]", out)


class TestDoneRm(TodoTestCase):
    def setUp(self):
        super().setUp()
        run("add", "任务甲")
        run("add", "任务乙")

    def test_done_sets_completed_at(self):
        code, _, _ = run("done", "1")
        self.assertEqual(code, 0)
        task = self.read_store()["tasks"][0]
        self.assertTrue(task["done"])
        self.assertIsNotNone(task["completed_at"])

    def test_done_is_idempotent_and_keeps_timestamp(self):
        # monkeypatch 两个不同时间戳：若实现错误地在第二次 done 覆写，completed_at 会变成第二个值
        stamps = iter(["2026-01-01T08:00:00", "2026-01-01T09:00:00"])
        with mock.patch.object(todo, "now_iso", lambda: next(stamps)):
            run("done", "1")
            code, out, _ = run("done", "1")
        self.assertEqual(code, 0)
        self.assertIn("已是完成状态", out)
        self.assertEqual(self.read_store()["tasks"][0]["completed_at"], "2026-01-01T08:00:00")  # 不覆写

    def test_rm_deletes_and_echoes(self):
        code, out, _ = run("rm", "1")
        self.assertEqual(code, 0)
        self.assertIn("已删除", out)
        self.assertIn("任务甲", out)
        remaining = [t["text"] for t in self.read_store()["tasks"]]
        self.assertEqual(remaining, ["任务乙"])

    def test_delete_alias_works(self):
        code, out, _ = run("delete", "2")
        self.assertEqual(code, 0)
        self.assertIn("已删除", out)


class TestPersistence(TodoTestCase):
    def test_roundtrip_via_todo_file_env(self):
        run("add", "跨进程可见 #work")
        self.assertTrue(os.path.exists(self.store))  # TODO_FILE 覆盖生效
        # 每条命令都重新 load_store，此处即验证磁盘写入/重读往返
        code, out, _ = run("list", "-t", "work")
        self.assertEqual(code, 0)
        self.assertIn("跨进程可见", out)

    def test_next_id_monotonic_never_reused(self):
        run("add", "一")
        run("add", "二")
        run("add", "三")
        run("rm", "3")  # 删除最大 id 条目
        run("add", "四")
        ids = [t["id"] for t in self.read_store()["tasks"]]
        self.assertIn(4, ids)  # 新增得到 id 4，而非回收 3
        self.assertNotIn(3, ids)

    def test_store_shape_and_human_readable(self):
        run("add", "中文待办 #标签")
        with open(self.store, encoding="utf-8") as fh:
            raw = fh.read()
        self.assertIn("中文待办", raw)  # ensure_ascii=False：人可直读
        data = self.read_store()
        self.assertEqual(data["next_id"], 2)
        self.assertEqual(sorted(data["tasks"][0]), sorted(
            ["id", "text", "tags", "priority", "done", "created_at", "completed_at"]))

    def test_missing_file_initializes_empty_store(self):
        code, out, _ = run("list")
        self.assertEqual(code, 0)
        self.assertIn("（无匹配待办）", out)

    def test_corrupt_json_is_error_not_silent_reset(self):
        with open(self.store, "w", encoding="utf-8") as fh:
            fh.write("{broken")
        code, _, err = run("list")
        self.assertEqual(code, 1)
        self.assertIn("不是有效 JSON", err)


class TestErrors(TodoTestCase):
    def test_done_unknown_id(self):
        code, out, err = run("done", "99")
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertIn("未找到 id=99", err)

    def test_rm_unknown_id(self):
        code, out, err = run("rm", "42")
        self.assertEqual(code, 1)
        self.assertEqual(out, "")  # AC-5：stdout 无输出
        self.assertIn("未找到 id=42", err)


class TestHelp(TodoTestCase):
    def test_top_level_help(self):
        code, out, _ = run("--help")
        self.assertEqual(code, 0)
        self.assertIn("add", out)

    def test_subcommand_help(self):
        code, out, _ = run("list", "--help")
        self.assertEqual(code, 0)
        self.assertIn("--priority", out)


if __name__ == "__main__":
    unittest.main()

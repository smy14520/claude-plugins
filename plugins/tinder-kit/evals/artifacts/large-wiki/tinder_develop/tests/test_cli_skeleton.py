"""CLI 骨架验收：入口、5 个子命令、--json 开关与退出码基线。仅 stdlib unittest。"""

import contextlib
import io
import json
import os
import tempfile
import unittest

from wiki_cli.cli import COMMANDS, main


class CliRunnerMixin:
    """进程内执行 main()，捕获 stdout / stderr 与退出码。"""

    def run_wiki(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(list(argv))
        return code, out.getvalue(), err.getvalue()


class SkeletonTest(CliRunnerMixin, unittest.TestCase):

    def test_help_exits_zero_and_lists_five_subcommands(self):
        code, out, _ = self.run_wiki("--help")
        self.assertEqual(code, 0)
        for command in COMMANDS:
            self.assertIn(command, out)

    def test_each_subcommand_help_exits_zero(self):
        for command in COMMANDS:
            with self.subTest(command=command):
                code, out, _ = self.run_wiki(command, "--help")
                self.assertEqual(code, 0)
                self.assertTrue(out.strip())

    def test_unknown_subcommand_is_usage_error_exit_2(self):
        code, _, err = self.run_wiki(".", "无此命令")
        self.assertEqual(code, 2)
        self.assertTrue(err.strip())

    def test_missing_required_argument_is_usage_error_exit_2(self):
        # backlinks 声明了必填页面名位置参数
        code, _, err = self.run_wiki(".", "backlinks")
        self.assertEqual(code, 2)
        self.assertTrue(err.strip())

    def test_version_flag_exits_zero(self):
        code, out, _ = self.run_wiki("--version")
        self.assertEqual(code, 0)
        self.assertIn("wiki", out)


class StubCommandTest(CliRunnerMixin, unittest.TestCase):
    """02-04 号工单交付前，backlinks / tags / search / doctor 为可用的骨架。"""

    STUB_INVOCATIONS = (
        ("backlinks", ("backlinks", "Foo")),
        ("tags", ("tags",)),
        ("search", ("search", "关键词")),
        ("doctor", ("doctor",)),
    )

    def test_stub_commands_exit_zero_with_chinese_notice(self):
        for command, argv in self.STUB_INVOCATIONS:
            with self.subTest(command=command):
                code, out, _ = self.run_wiki(".", *argv)
                self.assertEqual(code, 0)
                self.assertIn("尚未实现", out)
                self.assertIn(command, out)

    def test_stub_commands_support_json_flag(self):
        code, out, _ = self.run_wiki(".", "tags", "--json")
        self.assertEqual(code, 0)
        payload = json.loads(out)
        self.assertEqual(payload, {"command": "tags", "implemented": False})


class VaultPathTest(CliRunnerMixin, unittest.TestCase):
    """Vault 位置参数：位于子命令之前，默认当前目录；非法路径报中文错误并退出 2。"""

    def test_missing_vault_path_prints_chinese_error_and_exits_2(self):
        code, _, err = self.run_wiki("不存在的目录", "tags")
        self.assertEqual(code, 2)
        self.assertIn("Vault 路径不存在", err)
        self.assertIn("不存在的目录", err)

    def test_vault_path_pointing_to_file_is_usage_error_exit_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            file_path = os.path.join(tmp, "普通文件.txt")
            with open(file_path, "w", encoding="utf-8") as handle:
                handle.write("x")
            code, _, err = self.run_wiki(file_path, "tags")
            self.assertEqual(code, 2)
            self.assertIn("Vault 路径不是目录", err)

    def test_default_vault_is_current_directory(self):
        with tempfile.TemporaryDirectory() as empty:
            previous = os.getcwd()
            os.chdir(empty)
            try:
                code, out, _ = self.run_wiki("tags")
            finally:
                os.chdir(previous)
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()

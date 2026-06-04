import unittest
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]


class ImplPromptContractTests(unittest.TestCase):
    def read_plugin_file(self, *parts):
        return (PLUGIN_ROOT / Path(*parts)).read_text(encoding="utf-8")

    def test_impl_executes_slices_without_user_confirmation(self):
        text = self.read_plugin_file("skills", "impl", "SKILL.md")

        self.assertIn("## Slices", text)
        self.assertIn("连续执行所有 slices", text)
        self.assertIn("不在 slice 之间停顿等待用户确认", text)
        self.assertIn("in_progress", text)
        self.assertIn("NEEDS_CONTEXT", text)
        self.assertIn("BLOCKED", text)
        self.assertNotIn("AskUserQuestion", text)
        self.assertNotIn("阻塞项预检", text)
        self.assertNotIn("`[-]` 部分完成", text)
        self.assertNotIn("Impl 只更新 [ ] / [-] / [x]", text)

    def test_impl_uses_prd_scope_wording_not_minimal_code_change(self):
        text = self.read_plugin_file("skills", "impl", "SKILL.md")

        self.assertIn("PRD 的目标、范围、Acceptance Criteria、Package artifacts 引用、Technical Framing", text)
        self.assertIn("不修改 `prd.md`", text)
        self.assertIn("PRD 是需求 source of truth", text)
        self.assertIn("PRD blocking open questions", text)
        self.assertNotIn("最小代码变更", text)

    def test_impl_records_structured_result_and_self_check(self):
        text = self.read_plugin_file("skills", "impl", "SKILL.md")

        self.assertIn("record-impl-result", text)
        self.assertIn("self-check", text)
        self.assertIn("derive-required-checks", text)
        self.assertIn("run-check", text)
        self.assertIn("record-check", text)
        self.assertIn("DONE 必须逐项引用 passed check evidence", text)
        self.assertIn("DONE_WITH_CONCERNS", text)


if __name__ == "__main__":
    unittest.main()

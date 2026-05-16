import unittest
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]


class ReviewPromptContractTests(unittest.TestCase):
    def read_plugin_file(self, *parts):
        return (PLUGIN_ROOT / Path(*parts)).read_text(encoding="utf-8")

    def test_review_audits_required_check_evidence(self):
        text = self.read_plugin_file("skills", "review", "SKILL.md")

        self.assertIn("required_checks", text)
        self.assertIn("checks", text)
        self.assertIn("check_coverage", text)
        self.assertIn("run-check", text)
        self.assertIn("stdout_path", text)
        self.assertIn("`commands` 是 legacy note，不是 verification evidence", text)
        self.assertIn("不接受 impl 自然语言声称", text)
        self.assertIn("任一 required_check 没有 passed evidence", text)

    def test_review_references_do_not_use_legacy_commands_as_evidence(self):
        anti_patterns = self.read_plugin_file("skills", "review", "references", "anti-patterns.md")
        state_machine = self.read_plugin_file("skills", "review", "references", "state-machine.md")
        combined = anti_patterns + "\n" + state_machine

        self.assertIn("required_check", combined)
        self.assertIn("run-check", combined)
        self.assertNotIn("承重命令未在 commands 字段", combined)
        self.assertNotIn("impl_result.commands", combined)


if __name__ == "__main__":
    unittest.main()

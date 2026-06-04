import unittest
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]


class BrainstormPromptContractTests(unittest.TestCase):
    def read_plugin_file(self, *parts):
        return (PLUGIN_ROOT / Path(*parts)).read_text(encoding="utf-8")

    def test_brainstorm_requires_mode_question_for_ambiguous_demands(self):
        text = self.read_plugin_file("skills", "brainstorm", "SKILL.md")

        self.assertIn("AskUserQuestion", text)
        self.assertIn("normal", text)
        self.assertIn("grill-me", text)
        self.assertIn("MM-DD-<topic-slug>", text)

    def test_brainstorm_uses_durable_prd_draft_loop(self):
        text = self.read_plugin_file("skills", "brainstorm", "SKILL.md")
        modes = self.read_plugin_file("skills", "brainstorm", "references", "interview-modes.md")
        template = self.read_plugin_file("skills", "brainstorm", "assets", "templates", "prd.md")

        self.assertIn(".arbor/tasks/<package>/prd.md", text)
        self.assertIn("每轮回答后先更新 PRD", text)
        self.assertIn("自然语言续作", text)
        self.assertIn("离散取舍必须用 `AskUserQuestion` 给 2-4 个选项", text)
        self.assertIn("推荐项 description 中说明推荐理由", text)
        self.assertIn("Technical Framing", text)
        self.assertIn("## Slices", text)
        self.assertIn("`## Slices` 是 brainstorm 的产物", text)
        self.assertIn("不维护第二套执行计划", text)
        self.assertIn("references/interview-modes.md", text)
        self.assertIn("不要用 scope 大小或\"初版/MVP/后续\"来暗示哪个该选", text)
        self.assertNotIn("MVP", modes)
        self.assertNotIn("mvp", modes)
        self.assertIn("## Slices", template)
        self.assertIn("Execution unit: package PRD scope", template)
        self.assertIn("What I already know", template)
        self.assertIn("Requirements (evolving)", template)
        self.assertIn("Acceptance Criteria (evolving)", template)
        self.assertIn("Interview Log", template)
        self.assertIn("不要保存完整聊天流水", template)

    def test_technical_framing_captures_implementation_shape_without_design_stage(self):
        text = self.read_plugin_file("skills", "brainstorm", "SKILL.md")
        reference = self.read_plugin_file("skills", "brainstorm", "references", "technical-framing.md")
        template = self.read_plugin_file("skills", "brainstorm", "assets", "templates", "prd.md")
        combined = "\n".join([text, reference, template])

        self.assertIn("Implementation Shape / 实现形态", combined)
        self.assertIn("参考形态", template)
        self.assertIn("组装方式", template)
        self.assertIn("避免形态", template)
        self.assertIn("repo / framework 已有成功形态", reference)
        self.assertIn("Ownership / 责任归属", combined)
        self.assertIn("Source of truth / 事实源", combined)
        self.assertIn("不要写成详细实现步骤或逐文件任务清单", reference)
        self.assertNotIn("design stage", combined)

    def test_grill_me_handles_research_handoff_as_context_not_confirmation(self):
        text = self.read_plugin_file("skills", "brainstorm", "references", "interview-modes.md")

        self.assertIn("Research", text)
        self.assertIn("不直接定稿", text)

    def test_user_supplied_contracts_are_baseline_constraints(self):
        text = self.read_plugin_file("skills", "brainstorm", "references", "context-first.md")

        self.assertIn("SQL / API / 接口契约", text)
        self.assertIn("基准约束", text)
        self.assertIn("AskUserQuestion", text)


if __name__ == "__main__":
    unittest.main()

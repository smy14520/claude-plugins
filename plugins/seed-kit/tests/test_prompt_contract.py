from __future__ import annotations

import unittest
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]


class SeedPromptContractTests(unittest.TestCase):
    def read_plugin_file(self, *parts: str) -> str:
        return (PLUGIN_ROOT / Path(*parts)).read_text(encoding="utf-8")

    def test_brainstorm_uses_entry_per_behavior(self):
        text = self.read_plugin_file("skills", "brainstorm", "SKILL.md")

        # slice 内联：### [ ] S-NNN heading + 条目
        self.assertIn("### [ ] S-NNN", text)
        self.assertIn("一个 `* [ ]` 一个测试用例", text)
        # 旧 obligation 术语已移除
        self.assertNotIn("obligation", text)
        self.assertNotIn("AC 覆盖", text)
        # 旧 surface 词汇表已下线
        self.assertNotIn("## 交付面", text)
        self.assertNotIn("## 验证面", text)

    def test_prd_template_minimal_sections(self):
        template = self.read_plugin_file("templates", "prd.md")

        # 三段式：Goal / Acceptance Criteria / Out of Scope
        self.assertIn("## Goal", template)
        self.assertIn("## Acceptance Criteria", template)
        self.assertIn("### [ ] S-001", template)
        self.assertIn("## Out of Scope", template)
        self.assertIn("* [ ]", template)
        # 旧 obligation / 品质意图 术语已移除
        self.assertNotIn("obligation", template)
        self.assertNotIn("品质意图", template)

    def test_verification_describes_gate_and_loop(self):
        verification = self.read_plugin_file("skills", "references", "verification.md")

        # gate 只卡硬事实
        self.assertIn("测试命令", verification)
        self.assertIn("质量命令", verification)
        self.assertIn("真实测试框架", verification)
        # loop 守好坏
        self.assertIn("review loop", verification.lower())
        # PRD 结构
        self.assertIn("## Goal", verification)
        self.assertIn("## Acceptance Criteria", verification)
        self.assertIn("## Out of Scope", verification)
        # 条目格式
        self.assertIn("一个 `* [ ]` 一个测试用例", verification)
        self.assertIn("* [ ]", verification)
        # 封闭 kind 词汇：assert / judge / human（概念保留）
        for kind in ("assert", "judge", "human"):
            self.assertIn(kind, verification)
        # 无 obligation 机械约束
        self.assertNotIn("obligation", verification)
        self.assertNotIn("run-check", verification)
        self.assertNotIn("AC 覆盖校验", verification)
        self.assertNotIn("烟雾命令", verification)

    def test_docs_keep_helper_boundary_clear(self):
        design = self.read_plugin_file("DESIGN.md")
        claude = self.read_plugin_file("CLAUDE.md")
        combined = "\n".join([design, claude])

        # helper 只做确定性动作
        self.assertIn("确定性", combined)
        # gate 边界明确——硬事实
        self.assertIn("硬事实", claude)
        # 验收条目必须过
        self.assertIn("验收条目必须过", claude)

    def test_design_acknowledges_minimal_satisfaction(self):
        design = self.read_plugin_file("DESIGN.md")
        self.assertIn("诚实地最小满足", design)
        self.assertIn("半成品", design)
        # 公理
        self.assertIn("正确性的 source of truth", design)

    def test_impl_treats_tests_as_floor(self):
        agent = self.read_plugin_file("agents", "seed-impl.md")
        self.assertIn("验收条目必须兑现", agent)
        # 一个 agent 做所有 slice
        self.assertIn("所有 slice", agent)
        # 不弱化断言
        self.assertIn("不弱化断言", agent)
        # 无 provisional verdict（那是旧的 obligation judge 机制）
        self.assertNotIn("provisional", agent.lower())

    def test_review_agents_read_prd_goal_and_ac(self):
        review = self.read_plugin_file("agents", "seed-review.md")
        judge = self.read_plugin_file("agents", "seed-judge.md")

        # review 读 Goal + 验收条目
        self.assertIn("## Goal", review)
        self.assertIn("DESIGN.md", review)
        # judge 读 PRD 中描述的方向
        self.assertIn("PRD", judge)
        self.assertIn("missed-opportunity", judge)
        # judge 不查 obligation
        self.assertNotIn("[judge] 义务", judge)

    def test_review_loop_command_exists(self):
        cmd = self.read_plugin_file("commands", "review-loop.md")
        self.assertIn("review-loop", cmd)
        self.assertIn("客观锚", cmd)

    def test_no_stack_specific_tools_in_verification(self):
        verification = self.read_plugin_file("skills", "references", "verification.md")
        # 不应硬编码任何技术栈工具名
        self.assertNotIn("Playwright", verification)
        self.assertNotIn("computed-style", verification)
        self.assertNotIn("a11y", verification)
        self.assertNotIn("Pact", verification)
        self.assertNotIn("Unity", verification)
        self.assertNotIn("Unreal", verification)


if __name__ == "__main__":
    unittest.main()

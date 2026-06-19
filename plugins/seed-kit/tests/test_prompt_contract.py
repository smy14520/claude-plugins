from __future__ import annotations

import unittest
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]


class SeedPromptContractTests(unittest.TestCase):
    def read_plugin_file(self, *parts: str) -> str:
        return (PLUGIN_ROOT / Path(*parts)).read_text(encoding="utf-8")

    def test_brainstorm_requires_delivery_and_verification_surfaces(self):
        text = self.read_plugin_file("skills", "brainstorm", "SKILL.md")

        self.assertIn("## 交付面", text)
        self.assertIn("## 验证面", text)
        self.assertIn("[kind][surface]", text)
        self.assertIn("backend-domain", text)
        self.assertIn("web-ui", text)
        self.assertIn("human 不能替代", text)

    def test_template_and_conventions_share_surface_vocabulary(self):
        template = self.read_plugin_file("templates", "slice.md")
        conventions = self.read_plugin_file("skills", "references", "conventions.md")
        combined = "\n".join([template, conventions])

        self.assertIn("## 交付面", template)
        self.assertIn("## 验证面", template)
        self.assertIn("[assert][backend-domain]", template)
        for surface in ("backend-domain", "api", "web-ui", "e2e", "compliance", "infra"):
            self.assertIn(surface, combined)
        self.assertIn("没有 surface 标签时不覆盖任何交付面", conventions)

    def test_docs_keep_helper_boundary_clear(self):
        readme = self.read_plugin_file("README.md")
        design = self.read_plugin_file("DESIGN.md")
        combined = "\n".join([readme, design])

        self.assertIn("helper 做确定性结构约束", combined)
        self.assertIn("不保证语义正确", combined)
        self.assertIn("后端测试冒充", combined)

    def test_design_demotes_quality_axiom_to_correctness(self):
        design = self.read_plugin_file("DESIGN.md")
        # 公理从"质量 SoT"降级为"正确性 SoT"
        self.assertIn("正确性的 source of truth", design)
        self.assertNotIn("gate 是质量的 source of truth", design)
        # 显式承认第二种失败模式：诚实地最小满足 → 毛坯房
        self.assertIn("诚实地最小满足", design)
        self.assertIn("毛坯房", design)

    def test_impl_treats_tests_as_floor_with_visual_judge(self):
        impl = self.read_plugin_file("skills", "impl", "SKILL.md")
        self.assertIn("地板", impl)
        self.assertIn("可交付品质", impl)
        # judge 归 review（生成者≠验证者）：impl 不落 judge，review 附 --artifact 看真实产物
        self.assertNotIn("--artifact", impl)
        review = self.read_plugin_file("skills", "review", "SKILL.md")
        self.assertIn("--artifact", review)

    def test_brainstorm_captures_quality_baseline_by_reference(self):
        brainstorm = self.read_plugin_file("skills", "brainstorm", "SKILL.md")
        # brainstorm 只捕捉"意图"（参考级质量基线），不写"验证策略"政策
        self.assertIn("质量基线", brainstorm)
        self.assertIn("翻译者", brainstorm)
        self.assertNotIn("必须带一条整体体验 judge", brainstorm)

    def test_conventions_done_means_correct_not_quality(self):
        conventions = self.read_plugin_file("skills", "references", "conventions.md")
        self.assertIn("正确且不回归", conventions)
        self.assertIn("--artifact", conventions)

    def test_review_supports_three_modes(self):
        review = self.read_plugin_file("skills", "review", "SKILL.md")
        # 整体审计自主路由三模式（subagent 默认 / agent team 多 lens 对抗 / workflow 多角度评分聚合）
        self.assertIn("选模式", review)
        for mode in ("subagent", "agent team", "workflow"):
            self.assertIn(mode, review)


if __name__ == "__main__":
    unittest.main()

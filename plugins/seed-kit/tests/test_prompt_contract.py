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


if __name__ == "__main__":
    unittest.main()

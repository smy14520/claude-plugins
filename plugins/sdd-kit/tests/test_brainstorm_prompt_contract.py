import argparse
import importlib.util
import unittest
from pathlib import Path

from prompt_contract import assert_skill_structure, frontmatter_fields, headings

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = PLUGIN_ROOT / "tools" / "arbor.py"
spec = importlib.util.spec_from_file_location("arbor_for_brainstorm_contract", MODULE_PATH)
arbor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(arbor)


def all_cli_commands() -> tuple[str, ...]:
    parser = arbor.build_parser()
    sub = next(action for action in parser._actions if isinstance(action, argparse._SubParsersAction))
    return tuple(sub.choices)


class BrainstormPromptContractTests(unittest.TestCase):
    """Structural contract only — prose stays freely editable.

    Template heading assertions below are mechanism couplings: each heading is
    matched by a regex in arbor_core (prd_slices / brainstorm_finalize /
    validate_slice_tasks), so renaming it silently breaks finalize.
    """

    def read_plugin_file(self, *parts):
        return (PLUGIN_ROOT / Path(*parts)).read_text(encoding="utf-8")

    def test_brainstorm_skill_structure_and_command_references(self):
        assert_skill_structure(self, PLUGIN_ROOT / "skills" / "brainstorm", all_cli_commands())

    def test_prd_template_keeps_finalize_parser_contract(self):
        template = self.read_plugin_file("skills", "brainstorm", "assets", "templates", "prd.md")
        fields = frontmatter_fields(template)
        for key in ("name", "status", "date", "package"):
            self.assertIn(key, fields, f"prd template frontmatter missing {key}")
        template_headings = headings(template)
        # parsed by prd_slices.SLICE_SECTION_RE / SLICE_BLOCK_RE
        self.assertIn("Slices", template_headings)
        self.assertIn("Technical Framing", template_headings)
        self.assertIn("### S-", template)
        self.assertIn("- 完成标志：", template)
        # stripped at finalize by brainstorm_finalize._DRAFT_ONLY_SECTION_RE
        for draft_section in ("What I already know", "Requirements (evolving)", "Acceptance Criteria (evolving)", "Interview Log"):
            self.assertIn(draft_section, template_headings, f"draft-only section missing: {draft_section}")

    def test_slice_task_template_keeps_finalize_validation_contract(self):
        template = self.read_plugin_file("skills", "brainstorm", "assets", "templates", "slice-task.md")
        template_headings = headings(template)
        # required by prd_slices.validate_slice_tasks
        self.assertIn("Acceptance", template_headings)
        self.assertIn("Verification", template_headings)
        # Verification items must carry an explicit [kind] tag
        # (enforced by prd_slices.parse_verification_items at finalize/derive)
        from arbor_core.prd_slices import VERIFICATION_KINDS, parse_verification_items

        items = parse_verification_items(template)
        self.assertTrue(items, "slice-task template has no Verification items")
        for kind, description in items:
            self.assertIn(kind, VERIFICATION_KINDS, f"template Verification item missing valid [kind] tag: {description}")

    def test_prd_template_headings_cover_impl_packet_read_anchors(self):
        """impl-packet hardcodes prd.md#<heading> anchors; renaming the heading
        in the template would silently break the packet's read_next pointers."""
        from arbor_core.package_packet import _PRD_READ_ANCHORS

        template_headings = headings(self.read_plugin_file("skills", "brainstorm", "assets", "templates", "prd.md"))
        for anchor in _PRD_READ_ANCHORS:
            self.assertTrue(anchor.startswith("prd.md#"), f"unexpected anchor format: {anchor}")
            heading = anchor.split("#", 1)[1]
            self.assertIn(heading, template_headings, f"impl-packet read anchor missing from prd template: {heading}")


if __name__ == "__main__":
    unittest.main()

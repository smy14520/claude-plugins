import argparse
import importlib.util
import unittest
from pathlib import Path

from prompt_contract import assert_skill_structure, frontmatter_fields, headings

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = PLUGIN_ROOT / "tools" / "arbor.py"
spec = importlib.util.spec_from_file_location("arbor_for_impl_contract", MODULE_PATH)
arbor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(arbor)


def all_cli_commands() -> tuple[str, ...]:
    parser = arbor.build_parser()
    sub = next(action for action in parser._actions if isinstance(action, argparse._SubParsersAction))
    return tuple(sub.choices)


class ImplPromptContractTests(unittest.TestCase):
    """Structural contract only: frontmatter, resolvable references, real CLI commands.

    Prose is intentionally not asserted — prompts must stay freely editable.
    """

    def test_impl_skill_structure_and_command_references(self):
        assert_skill_structure(self, PLUGIN_ROOT / "skills" / "impl", all_cli_commands())

    def test_impl_references_resolve_and_have_content(self):
        references_dir = PLUGIN_ROOT / "skills" / "impl" / "references"
        for path in references_dir.glob("*.md"):
            text = path.read_text(encoding="utf-8")
            self.assertTrue(headings(text), f"{path} has no headings")

    def test_impl_skill_mentions_closed_loop_commands(self):
        text = (PLUGIN_ROOT / "skills" / "impl" / "SKILL.md").read_text(encoding="utf-8")
        for token in ["impl-packet", "run-check", "record-check", "mark-slice", "record-impl-result", "--functional-check"]:
            self.assertIn(token, text)
        for result in ["DONE", "DONE_WITH_CONCERNS", "NEEDS_CONTEXT", "BLOCKED"]:
            self.assertIn(result, text)

    def test_prompt_contract_helper_detects_broken_reference(self):
        """Negative self-test: the structural check must actually fail on breakage."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = Path(tmp)
            (skill_dir / "SKILL.md").write_text(
                "---\nname: x\ndescription: y\n---\n\nSee [`references/missing.md`](references/missing.md).\n",
                encoding="utf-8",
            )
            with self.assertRaises(AssertionError):
                assert_skill_structure(self, skill_dir)
            (skill_dir / "SKILL.md").write_text("# no frontmatter\n", encoding="utf-8")
            self.assertEqual(frontmatter_fields((skill_dir / "SKILL.md").read_text(encoding="utf-8")), {})
            with self.assertRaises(AssertionError):
                assert_skill_structure(self, skill_dir)


if __name__ == "__main__":
    unittest.main()

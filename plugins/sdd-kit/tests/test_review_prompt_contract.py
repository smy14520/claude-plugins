import argparse
import importlib.util
import unittest
from pathlib import Path

from prompt_contract import assert_skill_structure

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = PLUGIN_ROOT / "tools" / "arbor.py"
spec = importlib.util.spec_from_file_location("arbor_for_review_contract", MODULE_PATH)
arbor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(arbor)


def all_cli_commands() -> tuple[str, ...]:
    parser = arbor.build_parser()
    sub = next(action for action in parser._actions if isinstance(action, argparse._SubParsersAction))
    return tuple(sub.choices)


class ReviewPromptContractTests(unittest.TestCase):
    """Structural contract only — prose stays freely editable."""

    def test_review_skill_structure_and_command_references(self):
        assert_skill_structure(self, PLUGIN_ROOT / "skills" / "review", all_cli_commands())


if __name__ == "__main__":
    unittest.main()

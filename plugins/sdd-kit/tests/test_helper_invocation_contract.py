import unittest
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]


class HelperInvocationContractTests(unittest.TestCase):
    def test_docs_do_not_use_plugin_root_for_sdd_arbor_bash_calls(self):
        offenders = []
        for path in PLUGIN_ROOT.rglob("*.md"):
            if ".arbor" in path.parts:
                continue
            text = path.read_text(encoding="utf-8")
            if "CLAUDE_PLUGIN_ROOT" in text and "sdd-arbor" in text:
                offenders.append(path.relative_to(PLUGIN_ROOT).as_posix())
            if "/bin/sdd-arbor" in text:
                offenders.append(path.relative_to(PLUGIN_ROOT).as_posix())

        self.assertEqual([], offenders)


if __name__ == "__main__":
    unittest.main()

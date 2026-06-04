import unittest
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]


class SkillRegistryContractTests(unittest.TestCase):
    def test_public_skill_set_stays_minimal(self):
        skills = sorted(path.parent.name for path in (PLUGIN_ROOT / "skills").glob("*/SKILL.md"))

        self.assertEqual(
            ["brainstorm", "doctor", "impl", "research", "review", "rules", "wiki"],
            skills,
        )

    def test_active_docs_do_not_reference_removed_team_auto_skill(self):
        offenders = []
        removed_skill = "-".join(["team", "auto"])
        needles = [
            removed_skill,
            " ".join(["Team", "Auto"]),
            "sdd-kit:" + removed_skill,
            "Frontend/Backend " + "Slice-Gated Parallel",
        ]
        current_file = Path(__file__).resolve()
        for path in PLUGIN_ROOT.rglob("*"):
            if path.resolve() == current_file:
                continue
            if path.is_dir():
                continue
            if "runs" in path.parts and "scenario_eval" in path.parts:
                continue
            if path.suffix not in {".md", ".py", ".yaml", ".yml", ".json"}:
                continue
            text = path.read_text(encoding="utf-8")
            if any(needle in text for needle in needles):
                offenders.append(path.relative_to(PLUGIN_ROOT).as_posix())

        self.assertEqual([], offenders)


if __name__ == "__main__":
    unittest.main()

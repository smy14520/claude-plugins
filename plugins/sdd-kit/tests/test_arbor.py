import importlib.util
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "arbor.py"
spec = importlib.util.spec_from_file_location("arbor", MODULE_PATH)
arbor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(arbor)

NOW = "2026-04-25T00:00:00Z"


class ArborCliTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def run_cli(self, *args):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return arbor.main(["--root", str(self.root), "--now", NOW, *args])

    def package_dir(self, name="demo-task"):
        return self.root / ".arbor" / "tasks" / name

    def task_json(self, name="demo-task"):
        return json.loads((self.package_dir(name) / "task.json").read_text())

    def test_create_writes_complete_package(self):
        code = self.run_cli("create", "demo-task", "--mode", "strict-atomic", "--title", "Demo task")
        self.assertEqual(code, 0)
        pkg = self.package_dir()
        self.assertTrue((pkg / "prd.md").exists())
        self.assertTrue((pkg / "task.md").exists())
        self.assertTrue((pkg / "task.json").exists())
        self.assertTrue((pkg / "review.md").exists())
        self.assertTrue((pkg / "context" / "impl.jsonl").exists())
        self.assertTrue((pkg / "context" / "review.jsonl").exists())
        self.assertTrue((pkg / "context" / "sources.jsonl").exists())
        data = self.task_json()
        self.assertEqual(data["schema_version"], "arbor-task-v1")
        self.assertEqual(data["prd"]["file"], "prd.md")
        self.assertEqual(data["current_phase"], "brainstorm")

    def test_create_does_not_overwrite_existing_prd(self):
        self.run_cli("create", "demo-task", "--title", "Demo task")
        prd = self.package_dir() / "prd.md"
        prd.write_text("custom prd", encoding="utf-8")
        self.run_cli("create", "demo-task", "--title", "Demo task")
        self.assertEqual(prd.read_text(encoding="utf-8"), "custom prd")

    def test_invalid_name_is_rejected(self):
        code = self.run_cli("create", "Bad_Name")
        self.assertEqual(code, 1)
        self.assertFalse((self.root / ".arbor").exists())

    def test_validate_created_package(self):
        self.run_cli("create", "demo-task")
        self.assertEqual(self.run_cli("validate", "demo-task"), 0)

    def test_validate_missing_task_json_fails(self):
        self.run_cli("create", "demo-task")
        (self.package_dir() / "task.json").unlink()
        self.assertEqual(self.run_cli("validate", "demo-task"), 1)

    def test_add_child_and_duplicate_rejected(self):
        self.run_cli("create", "demo-task")
        code = self.run_cli(
            "add-child",
            "demo-task",
            "--id",
            "T-001",
            "--title",
            "ADD demo validator",
            "--milestone",
            "M-01",
            "--role",
            "shared",
        )
        self.assertEqual(code, 0)
        data = self.task_json()
        self.assertEqual(data["tasks"][0]["id"], "T-001")
        self.assertEqual(data["next_action"]["skill"], "impl")
        self.assertEqual(self.run_cli("add-child", "demo-task", "--id", "T-001", "--title", "ADD duplicate", "--milestone", "M-01", "--role", "shared"), 1)

    def test_unknown_dependency_rejected(self):
        self.run_cli("create", "demo-task")
        code = self.run_cli(
            "add-child",
            "demo-task",
            "--id",
            "T-002",
            "--title",
            "ADD dependent",
            "--milestone",
            "M-01",
            "--role",
            "shared",
            "--depends-on",
            "T-999",
        )
        self.assertEqual(code, 1)

    def test_validate_detects_cycle(self):
        self.run_cli("create", "demo-task")
        self.run_cli("add-child", "demo-task", "--id", "T-001", "--title", "ADD first", "--milestone", "M-01", "--role", "shared")
        self.run_cli("add-child", "demo-task", "--id", "T-002", "--title", "ADD second", "--milestone", "M-01", "--role", "shared", "--depends-on", "T-001")
        data = self.task_json()
        data["tasks"][0]["depends_on"] = ["T-002"]
        (self.package_dir() / "task.json").write_text(json.dumps(data), encoding="utf-8")
        self.assertEqual(self.run_cli("validate", "demo-task"), 1)

    def test_set_status_updates_task_and_phase_history(self):
        self.run_cli("create", "demo-task")
        self.run_cli("add-child", "demo-task", "--id", "T-001", "--title", "ADD first", "--milestone", "M-01", "--role", "shared")
        code = self.run_cli("set-status", "demo-task", "--task", "T-001", "--state", "in_progress", "--actor", "impl", "--note", "start")
        self.assertEqual(code, 0)
        data = self.task_json()
        self.assertEqual(data["tasks"][0]["state"], "in_progress")
        self.assertEqual(data["active_task"], "T-001")
        self.assertEqual(data["phase_history"][-1]["actor"], "impl")

    def test_set_phase_updates_current_phase(self):
        self.run_cli("create", "demo-task")
        code = self.run_cli("set-phase", "demo-task", "--phase", "task", "--actor", "task", "--note", "decompose")
        self.assertEqual(code, 0)
        self.assertEqual(self.task_json()["current_phase"], "task")

    def test_set_prd_status_ready_updates_next_action(self):
        self.run_cli("create", "demo-task")
        code = self.run_cli("set-prd-status", "demo-task", "--status", "ready-for-task", "--actor", "brainstorm", "--note", "ready")
        self.assertEqual(code, 0)
        data = self.task_json()
        self.assertEqual(data["prd"]["status"], "ready-for-task")
        self.assertEqual(data["state"], "ready")
        self.assertEqual(data["current_phase"], "task")
        self.assertEqual(data["next_action"]["skill"], "task")

    def test_freeze_definition_sets_impl_next_action(self):
        self.run_cli("create", "demo-task")
        self.run_cli("add-child", "demo-task", "--id", "T-001", "--title", "ADD first", "--milestone", "M-01", "--role", "shared")
        code = self.run_cli("freeze-definition", "demo-task", "--actor", "task", "--note", "frozen")
        self.assertEqual(code, 0)
        data = self.task_json()
        self.assertTrue(data["definition"]["frozen"])
        self.assertEqual(data["next_action"]["skill"], "impl")
        self.assertEqual(data["next_action"]["task_id"], "T-001")

    def test_done_status_sets_review_next_action(self):
        self.run_cli("create", "demo-task")
        self.run_cli("add-child", "demo-task", "--id", "T-001", "--title", "ADD first", "--milestone", "M-01", "--role", "shared")
        self.run_cli("set-status", "demo-task", "--task", "T-001", "--state", "done", "--actor", "impl", "--note", "done")
        data = self.task_json()
        self.assertEqual(data["state"], "impl_done")
        self.assertEqual(data["next_action"]["skill"], "review")

    def test_review_rework_sets_impl_next_action(self):
        self.run_cli("create", "demo-task")
        self.run_cli("add-child", "demo-task", "--id", "T-001", "--title", "ADD first", "--milestone", "M-01", "--role", "shared")
        self.run_cli("set-status", "demo-task", "--task", "T-001", "--state", "needs_rework", "--actor", "review", "--note", "rework")
        data = self.task_json()
        self.assertEqual(data["state"], "needs_rework")
        self.assertEqual(data["next_action"]["skill"], "impl")

    def test_brainstorm_drift_sets_brainstorm_next_action(self):
        self.run_cli("create", "demo-task")
        self.run_cli("add-child", "demo-task", "--id", "T-001", "--title", "ADD first", "--milestone", "M-01", "--role", "shared")
        self.run_cli("set-status", "demo-task", "--task", "T-001", "--state", "brainstorm_drift", "--actor", "review", "--note", "drift")
        data = self.task_json()
        self.assertEqual(data["state"], "brainstorm_drift")
        self.assertEqual(data["next_action"]["skill"], "brainstorm")

    def test_add_context_jsonl_and_validate(self):
        self.run_cli("create", "demo-task")
        self.run_cli("set-prd-status", "demo-task", "--status", "ready-for-task", "--actor", "brainstorm", "--note", "ready")
        self.run_cli("add-child", "demo-task", "--id", "T-001", "--title", "ADD first", "--milestone", "M-01", "--role", "shared")
        (self.package_dir() / "task.md").write_text("# 任务: demo-task\n\n- id: T-001\n  title: ADD first\n", encoding="utf-8")
        code = self.run_cli("add-context", "demo-task", "--type", "impl", "--task", "T-001", "--kind", "note", "--summary", "Smoke context")
        self.assertEqual(code, 0)
        line = (self.package_dir() / "context" / "impl.jsonl").read_text(encoding="utf-8").strip()
        self.assertEqual(json.loads(line)["summary"], "Smoke context")
        self.assertEqual(self.run_cli("validate", "demo-task"), 0)

    def test_add_sources_context_jsonl_and_validate(self):
        self.run_cli("create", "demo-task")
        code = self.run_cli(
            "add-context",
            "demo-task",
            "--type",
            "sources",
            "--source-id",
            "SRC-LOCAL-001",
            "--source-type",
            "local-file",
            "--location",
            "src/example.ts:1-10",
            "--title",
            "Example",
            "--why",
            "Shows pattern",
        )
        self.assertEqual(code, 0)
        self.assertEqual(self.run_cli("validate", "demo-task"), 0)

    def test_validate_rejects_unknown_next_action_task(self):
        self.run_cli("create", "demo-task")
        data = self.task_json()
        data["next_action"] = {"skill": "impl", "task_id": "T-999", "reason": "bad"}
        (self.package_dir() / "task.json").write_text(json.dumps(data), encoding="utf-8")
        self.assertEqual(self.run_cli("validate", "demo-task"), 1)

    def test_validate_rejects_context_unknown_task(self):
        self.run_cli("create", "demo-task")
        self.run_cli("add-context", "demo-task", "--type", "impl", "--task", "T-999", "--kind", "note", "--summary", "bad")
        # add-context rejects unknown task before writing.
        self.assertEqual((self.package_dir() / "context" / "impl.jsonl").read_text(encoding="utf-8"), "")

    def test_validate_rejects_duplicate_sources(self):
        self.run_cli("create", "demo-task")
        for _ in range(2):
            self.run_cli(
                "add-context",
                "demo-task",
                "--type",
                "sources",
                "--source-id",
                "SRC-LOCAL-001",
                "--source-type",
                "local-file",
                "--location",
                "src/example.ts:1-10",
                "--title",
                "Example",
                "--why",
                "Shows pattern",
            )
        self.assertEqual(self.run_cli("validate", "demo-task"), 1)

    def test_validate_rejects_active_task_state_mismatch(self):
        self.run_cli("create", "demo-task")
        self.run_cli("add-child", "demo-task", "--id", "T-001", "--title", "ADD first", "--milestone", "M-01", "--role", "shared")
        data = self.task_json()
        data["active_task"] = "T-001"
        data["state"] = "reviewed"
        data["next_action"] = {"skill": "none", "task_id": None, "reason": "bad"}
        (self.package_dir() / "task.json").write_text(json.dumps(data), encoding="utf-8")
        self.assertEqual(self.run_cli("validate", "demo-task"), 1)

    def test_validate_rejects_template_task_with_tasks(self):
        self.run_cli("create", "demo-task")
        self.run_cli("add-child", "demo-task", "--id", "T-001", "--title", "ADD first", "--milestone", "M-01", "--role", "shared")
        self.assertEqual(self.run_cli("validate", "demo-task"), 1)

    def test_invalid_jsonl_fails_validation(self):
        self.run_cli("create", "demo-task")
        (self.package_dir() / "context" / "impl.jsonl").write_text("{bad json\n", encoding="utf-8")
        self.assertEqual(self.run_cli("validate", "demo-task"), 1)

    def test_list_and_show_json_are_parseable(self):
        self.run_cli("create", "demo-task")
        items = arbor.list_packages(self.root)
        self.assertEqual(items[0]["name"], "demo-task")
        shown = arbor.show_package(self.root, "demo-task")
        self.assertEqual(shown["name"], "demo-task")
        self.assertTrue(shown["validation"]["ok"])

    def test_legacy_source_type_records_legacy_path(self):
        self.run_cli("create", "legacy-demo", "--source-type", "legacy-brainstorm")
        data = self.task_json("legacy-demo")
        self.assertEqual(data["prd"]["legacy_source"], ".arbor/brainstorms/legacy-demo.md")


if __name__ == "__main__":
    unittest.main()

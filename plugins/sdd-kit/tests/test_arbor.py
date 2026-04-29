import importlib.util
import contextlib
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = PLUGIN_ROOT / "tools" / "arbor.py"
HOOK_PATH = PLUGIN_ROOT / "hooks" / "arbor_guard.py"
BIN_PATH = PLUGIN_ROOT / "bin" / "sdd-arbor"
spec = importlib.util.spec_from_file_location("arbor", MODULE_PATH)
arbor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(arbor)
hook_spec = importlib.util.spec_from_file_location("arbor_guard", HOOK_PATH)
arbor_guard = importlib.util.module_from_spec(hook_spec)
hook_spec.loader.exec_module(arbor_guard)

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

    def run_bin(self, *args):
        return subprocess.run([str(BIN_PATH), "--root", str(self.root), "--now", NOW, *args], cwd=self.root, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)

    def package_dir(self, name="demo-task"):
        return self.root / ".arbor" / "tasks" / name

    def task_json(self, name="demo-task"):
        return json.loads((self.package_dir(name) / "task.json").read_text())

    def map_dir(self, name="big-init"):
        return self.root / ".arbor" / "maps" / name

    def map_json(self, name="big-init"):
        return json.loads((self.map_dir(name) / "map.json").read_text())

    def create_map_file(self, name="big-init"):
        path = self.map_dir(name)
        path.mkdir(parents=True, exist_ok=True)
        (path / "map.md").write_text(f"# {name}\n", encoding="utf-8")
        return path

    def mark_task_md_defined(self, name):
        (self.package_dir(name) / "task.md").write_text(f"# Tasks: {name}\n\n## T-001\n\nDefined test task.\n", encoding="utf-8")

    def test_sdd_arbor_bin_wrapper_runs_from_project_cwd(self):
        result = self.run_bin("create", "demo-task", "--mode", "strict-atomic", "--title", "Demo task")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.root / ".arbor" / "tasks" / "demo-task" / "task.json").exists())
        self.assertFalse((PLUGIN_ROOT / ".arbor").exists())

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
        self.assertEqual(data["execution"]["boundary"], "package")
        self.assertEqual(data["execution"]["unit_path"], ".arbor/tasks/demo-task")
        self.assertEqual(data["execution"]["child_task_scope"], "control_acceptance_review")
        self.assertEqual(data["execution"]["status"], "unclaimed")
        self.assertEqual(data["execution"]["checkpoints"], [])
        self.assertEqual(data["package_sizing"]["status"], "unchecked")
        self.assertEqual(data["prd"]["amendments"], [])

    def test_create_does_not_overwrite_existing_prd(self):
        self.run_cli("create", "demo-task", "--title", "Demo task")
        prd = self.package_dir() / "prd.md"
        prd.write_text("custom prd", encoding="utf-8")
        self.run_cli("create", "demo-task", "--title", "Demo task")
        self.assertEqual(prd.read_text(encoding="utf-8"), "custom prd")

    def test_create_map_writes_directory_artifacts(self):
        self.assertEqual(self.run_cli("create-map", "big-init", "--title", "Big init"), 0)
        self.assertTrue((self.map_dir() / "map.md").exists())
        self.assertTrue((self.map_dir() / "map.json").exists())
        self.assertFalse((self.map_dir() / "context" / "agent-assignments.jsonl").exists())
        data = self.map_json()
        self.assertEqual(data["schema_version"], "arbor-map-v1")
        self.assertEqual(data["map_path"], ".arbor/maps/big-init/map.md")
        self.assertEqual(data["orchestration"]["strategy"], "serial-package-map")
        self.assertIn("map-check", data["orchestration"]["dependency_gate"])
        self.assertIn("不自动创建 Team", data["orchestration"]["execution_model"])
        self.assertEqual(data["contract_requests"], [])
        self.assertNotIn("runtime", data["orchestration"])
        self.assertNotIn("write_permission_boundary", data["orchestration"])

    def test_create_map_migrates_legacy_flat_map(self):
        (self.root / ".arbor" / "maps").mkdir(parents=True)
        (self.root / ".arbor" / "maps" / "big-init.md").write_text("legacy map", encoding="utf-8")
        self.assertEqual(self.run_cli("create-map", "big-init"), 0)
        self.assertEqual((self.map_dir() / "map.md").read_text(encoding="utf-8"), "legacy map")

    def test_create_map_upgrades_old_orchestration_strategy(self):
        self.assertEqual(self.run_cli("create-map", "big-init"), 0)
        data = self.map_json()
        data["orchestration"] = {"strategy": "ready-packages-only"}
        (self.map_dir() / "map.json").write_text(json.dumps(data), encoding="utf-8")
        self.assertEqual(self.run_cli("create-map", "big-init"), 0)
        upgraded = self.map_json()
        self.assertEqual(upgraded["orchestration"]["strategy"], "serial-package-map")
        self.assertIn("map-check", upgraded["orchestration"]["dependency_gate"])
        self.assertIn("不自动创建 Team", upgraded["orchestration"]["execution_model"])
        self.assertNotIn("runtime", upgraded["orchestration"])
        self.assertNotIn("manual_review_mode", upgraded["orchestration"])

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
        self.run_cli("set-package-sizing", "demo-task", "--status", "fits_package", "--actor", "brainstorm", "--phase", "brainstorm", "--decision", "single package")
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
        self.run_cli("set-package-sizing", "demo-task", "--status", "fits_package", "--actor", "brainstorm", "--phase", "brainstorm", "--decision", "single package")
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

    def test_add_child_requires_package_sizing_gate(self):
        self.run_cli("create", "demo-task")
        self.assertEqual(self.run_cli("add-child", "demo-task", "--id", "T-001", "--title", "ADD first", "--milestone", "M-01", "--role", "shared"), 1)
        self.assertEqual(self.run_cli("set-package-sizing", "demo-task", "--status", "split_recommended", "--actor", "brainstorm", "--phase", "brainstorm", "--decision", "too large", "--signal", "multiple PR boundaries", "--recommended-package", "demo-core::core boundary"), 0)
        self.assertEqual(self.run_cli("add-child", "demo-task", "--id", "T-001", "--title", "ADD first", "--milestone", "M-01", "--role", "shared"), 1)
        data = self.task_json()
        self.assertEqual(data["package_sizing"]["status"], "split_recommended")
        self.assertEqual(data["package_sizing"]["recommended_packages"][0]["name"], "demo-core")

    def test_validate_rejects_tasks_when_sizing_unchecked(self):
        self.run_cli("create", "demo-task")
        data = self.task_json()
        data["tasks"].append({
            "id": "T-001",
            "title": "ADD first",
            "milestone": "M-01",
            "role": "shared",
            "state": "ready",
            "depends_on": [],
            "ready": True,
            "blockers": [],
            "attempts": 0,
            "last_impl_result": None,
            "last_review_result": None,
            "created_at": NOW,
            "updated_at": NOW,
        })
        (self.package_dir() / "task.json").write_text(json.dumps(data), encoding="utf-8")
        (self.package_dir() / "task.md").write_text("# 任务: demo-task\n\n- id: T-001\n  title: ADD first\n", encoding="utf-8")
        self.assertEqual(self.run_cli("validate", "demo-task"), 1)

    def test_validate_rejects_ready_prd_with_unchecked_sizing(self):
        self.run_cli("create", "demo-task")
        data = self.task_json()
        data["prd"]["status"] = "ready-for-task"
        data["prd"]["ready_for_task_at"] = NOW
        data["state"] = "ready"
        data["current_phase"] = "task"
        data["next_action"] = {"skill": "task", "task_id": None, "reason": "bad"}
        (self.package_dir() / "task.json").write_text(json.dumps(data), encoding="utf-8")
        self.assertEqual(self.run_cli("validate", "demo-task"), 1)

    def test_validate_rejects_split_recommended_without_recommended_packages(self):
        self.run_cli("create", "demo-task")
        data = self.task_json()
        data["package_sizing"]["status"] = "split_recommended"
        data["package_sizing"]["decision"] = "too large"
        data["package_sizing"]["decided_at"] = NOW
        data["package_sizing"]["decided_by"] = "brainstorm"
        data["package_sizing"]["recommended_packages"] = []
        (self.package_dir() / "task.json").write_text(json.dumps(data), encoding="utf-8")
        self.assertEqual(self.run_cli("validate", "demo-task"), 1)

    def test_validate_detects_cycle(self):
        self.run_cli("create", "demo-task")
        self.run_cli("set-package-sizing", "demo-task", "--status", "fits_package", "--actor", "brainstorm", "--phase", "brainstorm", "--decision", "single package")
        self.run_cli("add-child", "demo-task", "--id", "T-001", "--title", "ADD first", "--milestone", "M-01", "--role", "shared")
        self.run_cli("add-child", "demo-task", "--id", "T-002", "--title", "ADD second", "--milestone", "M-01", "--role", "shared", "--depends-on", "T-001")
        data = self.task_json()
        data["tasks"][0]["depends_on"] = ["T-002"]
        (self.package_dir() / "task.json").write_text(json.dumps(data), encoding="utf-8")
        self.assertEqual(self.run_cli("validate", "demo-task"), 1)

    def test_set_status_updates_task_and_phase_history(self):
        self.run_cli("create", "demo-task")
        self.run_cli("set-package-sizing", "demo-task", "--status", "fits_package", "--actor", "brainstorm", "--phase", "brainstorm", "--decision", "single package")
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

    def test_ready_for_task_requires_package_sizing(self):
        self.run_cli("create", "demo-task")
        code = self.run_cli("set-prd-status", "demo-task", "--status", "ready-for-task", "--actor", "brainstorm", "--note", "ready")
        self.assertEqual(code, 1)
        data = self.task_json()
        self.assertEqual(data["prd"]["status"], "draft")
        self.assertEqual(data["package_sizing"]["status"], "unchecked")

    def test_brainstorm_sizing_allows_ready_for_task(self):
        self.run_cli("create", "demo-task")
        self.assertEqual(self.run_cli("set-package-sizing", "demo-task", "--status", "fits_package", "--actor", "brainstorm", "--phase", "brainstorm", "--decision", "single package boundary is valid"), 0)
        code = self.run_cli("set-prd-status", "demo-task", "--status", "ready-for-task", "--actor", "brainstorm", "--note", "ready")
        self.assertEqual(code, 0)
        data = self.task_json()
        self.assertEqual(data["package_sizing"]["decided_by"], "brainstorm")
        self.assertEqual(data["prd"]["status"], "ready-for-task")
        self.assertEqual(data["state"], "ready")
        self.assertEqual(data["current_phase"], "task")
        self.assertEqual(data["next_action"]["skill"], "task")

    def test_split_recommended_blocks_ready_for_task_and_routes_to_map(self):
        self.run_cli("create", "demo-task")
        self.assertEqual(self.run_cli("set-package-sizing", "demo-task", "--status", "split_recommended", "--actor", "brainstorm", "--phase", "brainstorm", "--decision", "PRD crosses package boundaries", "--recommended-package", "demo-core::core boundary"), 0)
        data = self.task_json()
        self.assertEqual(data["package_sizing"]["status"], "split_recommended")
        self.assertEqual(data["current_phase"], "map")
        self.assertEqual(data["next_action"]["skill"], "map")
        self.assertEqual(self.run_cli("set-prd-status", "demo-task", "--status", "ready-for-task", "--actor", "brainstorm", "--note", "ready"), 1)

    def test_split_applied_from_map_allows_task_decomposition(self):
        self.run_cli("create", "demo-task")
        self.assertEqual(self.run_cli("set-package-sizing", "demo-task", "--status", "split_applied", "--actor", "map", "--phase", "map", "--decision", "child package from .arbor/maps/demo/map.md"), 0)
        self.assertEqual(self.run_cli("set-prd-status", "demo-task", "--status", "ready-for-task", "--actor", "brainstorm", "--note", "ready"), 0)
        self.assertEqual(self.run_cli("add-child", "demo-task", "--id", "T-001", "--title", "ADD first", "--milestone", "M-01", "--role", "shared"), 0)
        (self.package_dir() / "task.md").write_text("# 任务: demo-task\n\n- id: T-001\n  title: ADD first\n", encoding="utf-8")
        self.assertEqual(self.run_cli("validate", "demo-task"), 0)

    def test_create_split_packages_materializes_child_stubs(self):
        self.create_map_file("big-init")
        self.assertEqual(
            self.run_cli(
                "create-split-packages",
                "big-init",
                "--package",
                "big-core::Big core::::core boundary",
                "--package",
                "big-order::Big order::big-core::order boundary",
                "--actor",
                "map",
                "--decision",
                "package graph 已从 .arbor/maps/big-init/map.md materialize",
            ),
            0,
        )
        self.assertFalse(self.package_dir("big-init").exists())
        for name in ["big-core", "big-order"]:
            pkg = self.package_dir(name)
            self.assertTrue((pkg / "prd.md").exists())
            self.assertTrue((pkg / "task.md").exists())
            self.assertTrue((pkg / "task.json").exists())
            self.assertEqual(self.run_cli("validate", name), 0)
        core = self.task_json("big-core")
        self.assertEqual(core["prd"]["source_type"], "map-split")
        self.assertEqual(core["prd"]["parent_initiative"], "big-init")
        self.assertEqual(core["package_sizing"]["status"], "split_applied")
        self.assertEqual(core["package_sizing"]["parent_map"], ".arbor/maps/big-init/map.md")
        map_data = self.map_json("big-init")
        self.assertEqual([item["name"] for item in map_data["packages"]], ["big-core", "big-order"])
        self.assertEqual(map_data["packages"][0]["boundary_reason"], "core boundary")
        self.assertEqual(map_data["packages"][1]["depends_on"], ["big-core"])
        for entry in map_data["packages"]:
            self.assertNotIn("parallel_policy", entry)
            self.assertNotIn("modification_scope", entry)
            self.assertNotIn("contract_inputs", entry)
            self.assertNotIn("contract_outputs", entry)
        self.assertEqual(core["tasks"], [])
        self.assertEqual(core["prd"]["status"], "draft")
        self.assertEqual(core["next_action"]["skill"], "brainstorm")
        self.assertEqual(core["package_sizing"]["boundary_reason"], "core boundary")
        self.assertNotIn("parallel_policy", core["package_sizing"])
        order = self.task_json("big-order")
        self.assertEqual(order["package_sizing"]["depends_on_packages"], ["big-core"])
        self.assertEqual(order["package_sizing"]["boundary_reason"], "order boundary")
        self.assertNotIn("parallel_policy", order["package_sizing"])

    def test_create_split_package_can_later_enter_task_decomposition(self):
        self.create_map_file("big-init")
        self.assertEqual(self.run_cli("create-split-packages", "big-init", "--package", "big-core::Big core::::core boundary", "--decision", "from map"), 0)
        self.assertEqual(self.run_cli("set-prd-status", "big-core", "--status", "ready-for-task", "--actor", "brainstorm", "--note", "ready"), 0)
        self.assertEqual(self.run_cli("add-child", "big-core", "--id", "T-001", "--title", "ADD first", "--milestone", "M-01", "--role", "shared"), 0)
        (self.package_dir("big-core") / "task.md").write_text("# 任务: big-core\n\n- id: T-001\n  title: ADD first\n", encoding="utf-8")
        self.assertEqual(self.run_cli("validate", "big-core"), 0)

    def test_create_split_packages_rejects_invalid_specs(self):
        self.create_map_file("big-init")
        self.assertEqual(self.run_cli("create-split-packages", "big-init", "--package", "big-init::Parent::::bad", "--decision", "from map"), 1)
        self.assertEqual(self.run_cli("create-split-packages", "big-init", "--package", "Bad::Bad::::bad", "--decision", "from map"), 1)
        self.assertEqual(self.run_cli("create-split-packages", "big-init", "--package", "big-core::Big core::::core", "--package", "big-core::Duplicate::::dup", "--decision", "from map"), 1)
        self.assertEqual(self.run_cli("create-split-packages", "big-init", "--package", "big-core::Big core::big-core::self", "--decision", "from map"), 1)
        self.run_cli("create", "existing", "--source-type", "ad-hoc")
        self.run_cli("set-package-sizing", "existing", "--status", "fits_package", "--actor", "brainstorm", "--phase", "brainstorm", "--decision", "standalone")
        self.assertEqual(self.run_cli("create-split-packages", "big-init", "--package", "existing::Existing::::conflict", "--decision", "from map"), 1)
        self.assertEqual(self.map_json("big-init")["packages"], [])

    def test_create_split_packages_is_idempotent_without_overwriting_prd(self):
        self.create_map_file("big-init")
        self.assertEqual(self.run_cli("create-split-packages", "big-init", "--package", "big-core::Big core::::core boundary", "--decision", "from map"), 0)
        prd = self.package_dir("big-core") / "prd.md"
        prd.write_text("custom child prd", encoding="utf-8")
        self.assertEqual(self.run_cli("create-split-packages", "big-init", "--package", "big-core::Big core::::core boundary", "--decision", "from map"), 0)
        self.assertEqual(prd.read_text(encoding="utf-8"), "custom child prd")

    def test_validate_rejects_malformed_map_split_metadata(self):
        self.run_cli("create", "big-core", "--source-type", "map-split")
        data = self.task_json("big-core")
        data["prd"]["parent_initiative"] = "big-init"
        data["prd"]["parent_map"] = ".arbor/maps/wrong.md"
        data["package_sizing"]["status"] = "fits_package"
        data["package_sizing"]["decision"] = "bad"
        (self.package_dir("big-core") / "task.json").write_text(json.dumps(data), encoding="utf-8")
        self.assertEqual(self.run_cli("validate", "big-core"), 1)

    def test_map_check_reports_ready_and_blocked_packages(self):
        self.create_map_file("big-init")
        self.assertEqual(
            self.run_cli(
                "create-split-packages",
                "big-init",
                "--package",
                "big-core::Big core::::core boundary",
                "--package",
                "big-order::Big order::big-core::order boundary",
                "--decision",
                "from map",
            ),
            0,
        )
        check = arbor.map_check(self.root, "big-init", NOW)
        self.assertEqual([item["name"] for item in check["ready"]], ["big-core"])
        self.assertEqual([item["name"] for item in check["blocked"]], ["big-order"])
        self.assertEqual(check["blocked"][0]["reason"], "dependency 未完成")
        self.assertEqual(check["blocked"][0]["blocked_by"][0]["name"], "big-core")
        self.assertNotIn("execution_ready", check)
        self.assertNotIn("prep_ready", check)

    def test_map_check_dependency_reviewed_does_not_unlock_downstream(self):
        self.create_map_file("big-init")
        self.assertEqual(self.run_cli("create-split-packages", "big-init", "--package", "big-core::Big core::::core boundary", "--package", "big-order::Big order::big-core::order boundary", "--decision", "from map"), 0)
        self.assertEqual(self.run_cli("set-prd-status", "big-core", "--status", "ready-for-task", "--actor", "brainstorm", "--note", "ready"), 0)
        self.assertEqual(self.run_cli("add-child", "big-core", "--id", "T-001", "--title", "ADD first", "--milestone", "M-01", "--role", "shared"), 0)
        self.mark_task_md_defined("big-core")
        self.assertEqual(self.run_cli("set-status", "big-core", "--task", "T-001", "--state", "approved", "--actor", "review", "--note", "approved"), 0)
        self.assertEqual(self.run_cli("set-execution", "big-core", "--status", "reviewed"), 0)
        check = arbor.map_check(self.root, "big-init", NOW)
        self.assertEqual([item["name"] for item in check["ready"]], [])
        self.assertEqual([item["name"] for item in check["blocked"]], ["big-core", "big-order"])
        self.assertEqual(check["blocked"][0]["reason"], "package 已 reviewed；需要显式标记 completed 或合并 PR 后下游才能依赖")
        self.assertEqual(check["blocked"][1]["blocked_by"][0]["name"], "big-core")

    def test_map_check_unblocks_downstream_after_completed_or_merged(self):
        self.create_map_file("big-init")
        self.assertEqual(self.run_cli("create-split-packages", "big-init", "--package", "big-core::Big core::::core boundary", "--package", "big-order::Big order::big-core::order boundary", "--decision", "from map"), 0)
        data = self.task_json("big-core")
        data["state"] = "completed"
        (self.package_dir("big-core") / "task.json").write_text(json.dumps(data), encoding="utf-8")
        check = arbor.map_check(self.root, "big-init", NOW)
        self.assertEqual([item["name"] for item in check["complete"]], ["big-core"])
        self.assertEqual([item["name"] for item in check["ready"]], ["big-order"])

    def test_record_contract_request_create_update(self):
        self.create_map_file("big-init")
        self.assertEqual(self.run_cli("create-split-packages", "big-init", "--package", "big-core::Big core::::core boundary", "--package", "big-order::Big order::big-core::order boundary", "--decision", "from map"), 0)
        self.assertEqual(self.run_cli("record-contract-request", "big-init", "--consumer", "big-order", "--producer", "big-core", "--request", "Need entitlement status output", "--status", "open"), 0)
        data = self.map_json("big-init")
        self.assertEqual(data["contract_requests"][0]["id"], "CR-001")
        self.assertEqual(data["contract_requests"][0]["consumer"], "big-order")
        self.assertEqual(data["contract_requests"][0]["producer"], "big-core")
        self.assertEqual(self.run_cli("record-contract-request", "big-init", "--id", "CR-001", "--consumer", "big-order", "--producer", "big-core", "--request", "Need entitlement status output", "--status", "accepted", "--resolution", "big-core will expose stable status"), 0)
        data = self.map_json("big-init")
        self.assertEqual(len(data["contract_requests"]), 1)
        self.assertEqual(data["contract_requests"][0]["status"], "accepted")
        self.assertEqual(data["contract_requests"][0]["resolution"], "big-core will expose stable status")

    def test_record_contract_request_rejects_unknown_or_invalid_packages(self):
        self.create_map_file("big-init")
        self.assertEqual(self.run_cli("create-split-packages", "big-init", "--package", "big-core::Big core::::core boundary", "--decision", "from map"), 0)
        self.assertEqual(self.run_cli("record-contract-request", "big-init", "--consumer", "missing", "--producer", "big-core", "--request", "Need x", "--status", "open"), 1)
        self.assertEqual(self.run_cli("record-contract-request", "big-init", "--consumer", "big-core", "--producer", "big-core", "--request", "Need x", "--status", "open"), 1)
        self.assertEqual(self.map_json("big-init")["contract_requests"], [])

    def test_add_context_batch_is_atomic_and_ordered(self):
        self.run_cli("create", "demo-task")
        self.run_cli("set-package-sizing", "demo-task", "--status", "fits_package", "--actor", "brainstorm", "--phase", "brainstorm", "--decision", "single package")
        self.run_cli("add-child", "demo-task", "--id", "T-001", "--title", "ADD first", "--milestone", "M-01", "--role", "shared")
        self.assertEqual(self.run_cli("add-context-batch", "demo-task", "--type", "impl", "--entry-json", '{"task_id":"T-001","kind":"note","summary":"first"}', "--entry-json", '{"task_id":"T-001","kind":"decision","summary":"second"}'), 0)
        lines = (self.package_dir("demo-task") / "context" / "impl.jsonl").read_text(encoding="utf-8").strip().splitlines()
        self.assertEqual([json.loads(line)["summary"] for line in lines], ["first", "second"])
        before = (self.package_dir("demo-task") / "context" / "review.jsonl").read_text(encoding="utf-8")
        self.assertEqual(self.run_cli("add-context-batch", "demo-task", "--type", "review", "--entry-json", '{"task_id":"T-999","kind":"note","summary":"bad"}'), 1)
        self.assertEqual((self.package_dir("demo-task") / "context" / "review.jsonl").read_text(encoding="utf-8"), before)

    def test_repair_context_jsonl_adds_missing_schema_fields(self):
        self.run_cli("create", "demo-task")
        self.run_cli("set-package-sizing", "demo-task", "--status", "fits_package", "--actor", "brainstorm", "--phase", "brainstorm", "--decision", "single package")
        self.run_cli("add-child", "demo-task", "--id", "T-001", "--title", "ADD first", "--milestone", "M-01", "--role", "shared")
        path = self.package_dir("demo-task") / "context" / "review.jsonl"
        path.write_text('{"summary":"review note","task_id":"T-001"}\n', encoding="utf-8")
        self.assertEqual(self.run_cli("validate", "demo-task"), 1)
        self.assertEqual(self.run_cli("repair-context", "demo-task", "--type", "review", "--json"), 0)
        entry = json.loads(path.read_text(encoding="utf-8").strip())
        self.assertEqual(entry["kind"], "note")
        self.assertEqual(entry["actor"], "arbor")
        self.assertEqual(entry["at"], NOW)
        errors = arbor.validate_package(self.root, "demo-task")
        self.assertFalse([error for error in errors if "context/review.jsonl" in error])

    def test_module_summary_has_stable_non_line_locators(self):
        self.create_map_file("big-init")
        self.assertEqual(self.run_cli("create-split-packages", "big-init", "--package", "big-core::Big core::::core boundary", "--decision", "from map"), 0)
        self.assertEqual(self.run_cli("record-contract-request", "big-init", "--consumer", "big-core", "--producer", "big-core", "--request", "bad", "--status", "open"), 1)
        packet = arbor.module_summary(self.root, "big-core", "big-init", NOW)
        self.assertEqual(packet["kind"], "module-summary")
        self.assertEqual(packet["schema_version"], "sdd-module-summary-v1")
        self.assertEqual(packet["package"], "big-core")
        self.assertIn("contracts", packet)
        self.assertNotIn("line", json.dumps(packet).lower())
        self.assertEqual(self.run_cli("module-summary", "big-core", "--initiative", "big-init", "--json"), 0)

    def test_wiki_index_search_and_collect_nested_pages(self):
        wiki = self.root / ".wiki" / "Modules"
        wiki.mkdir(parents=True)
        (wiki / "Balance Ledger.md").write_text("""---
title: Balance Ledger
description: 余额账户、充值、扣款、退款 contract
tags: [module, backend, ledger]
package: balance-ledger
summary: Balance ledger owns account balance and refund invariants.
---

# Balance Ledger

## Public contracts

Uses `BalanceLedgerService.recharge` and links to [[User Role Access]].
""", encoding="utf-8")
        (wiki / "User Role Access.md").write_text("""---
title: User Role Access
description: 用户角色权限模块
tags: [module, auth]
summary: User role access owns instructor/admin authorization.
---

# User Role Access

## Routes

Provides `RoleGate.canManageCourse`.
""", encoding="utf-8")
        indexed = arbor.wiki_index(self.root)
        self.assertEqual([page["title"] for page in indexed["pages"]], ["Balance Ledger", "User Role Access"])
        ledger = indexed["pages"][0]
        self.assertEqual(ledger["path"], ".wiki/Modules/Balance Ledger.md")
        self.assertIn("ledger", ledger["tags"])
        self.assertIn({"kind": "heading", "level": "2", "name": "Public contracts"}, ledger["locators"])
        self.assertIn({"kind": "symbol", "name": "BalanceLedgerService.recharge"}, ledger["locators"])
        access = indexed["pages"][1]
        self.assertEqual(access["backlinks"], ["Balance Ledger"])
        search = arbor.wiki_search(self.root, "balance 退款 course")
        self.assertEqual(search["results"][0]["title"], "Balance Ledger")
        self.assertIn("description", search["results"][0]["matched_fields"])
        collected = arbor.wiki_collect(self.root, "role course", limit=1)
        self.assertEqual(len(collected["selected"]), 1)
        self.assertIn(collected["selected"][0]["title"], {"Balance Ledger", "User Role Access"})
        self.assertEqual(self.run_cli("wiki-index", "--json"), 0)
        self.assertEqual(self.run_cli("wiki-search", "balance refund", "--json"), 0)
        self.assertEqual(self.run_cli("wiki-collect", "--query", "balance refund", "--json"), 0)

    def test_wiki_index_empty_root(self):
        result = arbor.wiki_index(self.root)
        self.assertEqual(result["wiki_root"], ".wiki")
        self.assertEqual(result["pages"], [])

    def test_freeze_definition_sets_impl_next_action(self):
        self.run_cli("create", "demo-task")
        self.run_cli("set-package-sizing", "demo-task", "--status", "fits_package", "--actor", "brainstorm", "--phase", "brainstorm", "--decision", "single package")
        self.run_cli("add-child", "demo-task", "--id", "T-001", "--title", "ADD first", "--milestone", "M-01", "--role", "shared")
        code = self.run_cli("freeze-definition", "demo-task", "--actor", "task", "--note", "frozen")
        self.assertEqual(code, 0)
        data = self.task_json()
        self.assertTrue(data["definition"]["frozen"])
        self.assertEqual(data["next_action"]["skill"], "impl")
        self.assertEqual(data["next_action"]["task_id"], "T-001")

    def test_done_status_sets_review_next_action(self):
        self.run_cli("create", "demo-task")
        self.run_cli("set-package-sizing", "demo-task", "--status", "fits_package", "--actor", "brainstorm", "--phase", "brainstorm", "--decision", "single package")
        self.run_cli("add-child", "demo-task", "--id", "T-001", "--title", "ADD first", "--milestone", "M-01", "--role", "shared")
        self.run_cli("set-status", "demo-task", "--task", "T-001", "--state", "done", "--actor", "impl", "--note", "done")
        data = self.task_json()
        self.assertEqual(data["state"], "impl_done")
        self.assertEqual(data["next_action"]["skill"], "review")

    def test_review_rework_sets_impl_next_action(self):
        self.run_cli("create", "demo-task")
        self.run_cli("set-package-sizing", "demo-task", "--status", "fits_package", "--actor", "brainstorm", "--phase", "brainstorm", "--decision", "single package")
        self.run_cli("add-child", "demo-task", "--id", "T-001", "--title", "ADD first", "--milestone", "M-01", "--role", "shared")
        self.run_cli("set-status", "demo-task", "--task", "T-001", "--state", "needs_rework", "--actor", "review", "--note", "rework")
        data = self.task_json()
        self.assertEqual(data["state"], "needs_rework")
        self.assertEqual(data["next_action"]["skill"], "impl")

    def test_brainstorm_drift_sets_brainstorm_next_action(self):
        self.run_cli("create", "demo-task")
        self.run_cli("set-package-sizing", "demo-task", "--status", "fits_package", "--actor", "brainstorm", "--phase", "brainstorm", "--decision", "single package")
        self.run_cli("add-child", "demo-task", "--id", "T-001", "--title", "ADD first", "--milestone", "M-01", "--role", "shared")
        self.run_cli("set-status", "demo-task", "--task", "T-001", "--state", "brainstorm_drift", "--actor", "review", "--note", "drift")
        data = self.task_json()
        self.assertEqual(data["state"], "brainstorm_drift")
        self.assertEqual(data["next_action"]["skill"], "brainstorm")

    def test_add_amendment_routes_to_task(self):
        self.run_cli("create", "demo-task")
        self.run_cli("set-package-sizing", "demo-task", "--status", "fits_package", "--actor", "brainstorm", "--phase", "brainstorm", "--decision", "single package")
        self.run_cli("add-child", "demo-task", "--id", "T-001", "--title", "ADD first", "--milestone", "M-01", "--role", "shared")
        self.run_cli("set-status", "demo-task", "--task", "T-001", "--state", "brainstorm_drift", "--actor", "review", "--note", "drift")
        self.assertEqual(
            self.run_cli(
                "add-amendment",
                "demo-task",
                "--id",
                "AMD-001",
                "--title",
                "Correct refund behavior",
                "--wrong",
                "refund not described",
                "--correct",
                "full refund revokes entitlement",
                "--affects-task",
                "T-001",
                "--actor",
                "brainstorm",
            ),
            0,
        )
        data = self.task_json()
        self.assertEqual(data["prd"]["amendments"][0]["id"], "AMD-001")
        self.assertEqual(data["prd"]["status"], "ready-for-task")
        self.assertEqual(data["current_phase"], "task")
        self.assertEqual(data["next_action"]["skill"], "task")
        self.assertEqual(data["phase_history"][-1]["to"], "amendment:AMD-001")
        (self.package_dir() / "task.md").write_text("# 任务: demo-task\n\n- id: T-001\n  title: ADD first\n", encoding="utf-8")
        self.assertEqual(self.run_cli("validate", "demo-task"), 0)

    def test_add_amendment_rejects_duplicate_or_bad_id(self):
        self.run_cli("create", "demo-task")
        self.run_cli("set-package-sizing", "demo-task", "--status", "fits_package", "--actor", "brainstorm", "--phase", "brainstorm", "--decision", "single package")
        self.run_cli("add-child", "demo-task", "--id", "T-001", "--title", "ADD first", "--milestone", "M-01", "--role", "shared")
        self.assertEqual(self.run_cli("add-amendment", "demo-task", "--id", "AMD-1", "--title", "Bad", "--wrong", "old", "--correct", "new"), 1)
        self.assertEqual(self.run_cli("add-amendment", "demo-task", "--id", "AMD-001", "--title", "One", "--wrong", "old", "--correct", "new"), 0)
        self.assertEqual(self.run_cli("add-amendment", "demo-task", "--id", "AMD-001", "--title", "Dup", "--wrong", "old", "--correct", "new"), 1)

    def test_add_child_links_to_amendment(self):
        self.run_cli("create", "demo-task")
        self.run_cli("set-package-sizing", "demo-task", "--status", "fits_package", "--actor", "brainstorm", "--phase", "brainstorm", "--decision", "single package")
        self.run_cli("add-child", "demo-task", "--id", "T-001", "--title", "ADD first", "--milestone", "M-01", "--role", "shared")
        self.run_cli("add-amendment", "demo-task", "--id", "AMD-001", "--title", "Correction", "--wrong", "old", "--correct", "new", "--affects-task", "T-001")
        self.assertEqual(self.run_cli("add-child", "demo-task", "--id", "T-002", "--title", "UPDATE correction", "--milestone", "M-AMEND", "--role", "shared", "--source-amendment", "AMD-001", "--corrects", "T-001"), 0)
        data = self.task_json()
        task = data["tasks"][1]
        self.assertEqual(task["source_amendment"], "AMD-001")
        self.assertEqual(task["corrects"], ["T-001"])
        (self.package_dir() / "task.md").write_text("# 任务: demo-task\n\n- id: T-001\n  title: ADD first\n- id: T-002\n  title: UPDATE correction\n", encoding="utf-8")
        self.assertEqual(self.run_cli("validate", "demo-task"), 0)

    def test_add_child_rejects_unknown_amendment_or_corrects_task(self):
        self.run_cli("create", "demo-task")
        self.run_cli("set-package-sizing", "demo-task", "--status", "fits_package", "--actor", "brainstorm", "--phase", "brainstorm", "--decision", "single package")
        self.run_cli("add-child", "demo-task", "--id", "T-001", "--title", "ADD first", "--milestone", "M-01", "--role", "shared")
        self.assertEqual(self.run_cli("add-child", "demo-task", "--id", "T-002", "--title", "UPDATE correction", "--milestone", "M-AMEND", "--role", "shared", "--source-amendment", "AMD-999"), 1)
        self.run_cli("add-amendment", "demo-task", "--id", "AMD-001", "--title", "Correction", "--wrong", "old", "--correct", "new", "--affects-task", "T-001")
        self.assertEqual(self.run_cli("add-child", "demo-task", "--id", "T-002", "--title", "UPDATE correction", "--milestone", "M-AMEND", "--role", "shared", "--source-amendment", "AMD-001", "--corrects", "T-999"), 1)

    def test_forward_only_amendment_recovery_can_review_package(self):
        self.run_cli("create", "demo-task")
        self.run_cli("set-package-sizing", "demo-task", "--status", "fits_package", "--actor", "brainstorm", "--phase", "brainstorm", "--decision", "single package")
        self.run_cli("set-prd-status", "demo-task", "--status", "ready-for-task", "--actor", "brainstorm", "--note", "ready")
        self.run_cli("add-child", "demo-task", "--id", "T-001", "--title", "ADD first", "--milestone", "M-01", "--role", "shared")
        self.run_cli("set-status", "demo-task", "--task", "T-001", "--state", "brainstorm_drift", "--actor", "review", "--note", "drift")
        self.run_cli("add-amendment", "demo-task", "--id", "AMD-001", "--title", "Correction", "--wrong", "old", "--correct", "new", "--affects-task", "T-001")
        self.run_cli("add-child", "demo-task", "--id", "T-002", "--title", "UPDATE correction", "--milestone", "M-AMEND", "--role", "shared", "--source-amendment", "AMD-001", "--corrects", "T-001")
        self.run_cli("set-status", "demo-task", "--task", "T-001", "--state", "skipped", "--actor", "task", "--note", "obsolete after AMD-001; corrected by T-002")
        data = self.task_json()
        self.assertEqual(data["next_action"], {"skill": "impl", "task_id": "T-002", "reason": "下一个 package-local ready task"})
        self.run_cli("set-status", "demo-task", "--task", "T-002", "--state", "approved", "--actor", "review", "--note", "approved")
        data = self.task_json()
        self.assertEqual(data["state"], "reviewed")
        self.assertEqual(data["next_action"]["skill"], "none")
        (self.package_dir() / "task.md").write_text("# 任务: demo-task\n\n- id: T-001\n  title: ADD first\n- id: T-002\n  title: UPDATE correction\n", encoding="utf-8")
        self.assertEqual(self.run_cli("validate", "demo-task"), 0)

    def test_validate_rejects_malformed_amendment_metadata(self):
        self.run_cli("create", "demo-task")
        data = self.task_json()
        data["prd"]["amendments"] = [{"id": "BAD", "title": "Bad", "wrong": "old", "correct": "new", "created_at": NOW, "created_by": "brainstorm"}]
        (self.package_dir() / "task.json").write_text(json.dumps(data), encoding="utf-8")
        self.assertEqual(self.run_cli("validate", "demo-task"), 1)

    def test_add_context_jsonl_and_validate(self):
        self.run_cli("create", "demo-task")
        self.run_cli("set-package-sizing", "demo-task", "--status", "fits_package", "--actor", "brainstorm", "--phase", "brainstorm", "--decision", "single package")
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
        self.run_cli("set-package-sizing", "demo-task", "--status", "fits_package", "--actor", "brainstorm", "--phase", "brainstorm", "--decision", "single package")
        self.run_cli("add-child", "demo-task", "--id", "T-001", "--title", "ADD first", "--milestone", "M-01", "--role", "shared")
        data = self.task_json()
        data["active_task"] = "T-001"
        data["state"] = "reviewed"
        data["next_action"] = {"skill": "none", "task_id": None, "reason": "bad"}
        (self.package_dir() / "task.json").write_text(json.dumps(data), encoding="utf-8")
        self.assertEqual(self.run_cli("validate", "demo-task"), 1)

    def test_validate_rejects_template_task_with_tasks(self):
        self.run_cli("create", "demo-task")
        self.run_cli("set-package-sizing", "demo-task", "--status", "fits_package", "--actor", "brainstorm", "--phase", "brainstorm", "--decision", "single package")
        self.run_cli("add-child", "demo-task", "--id", "T-001", "--title", "ADD first", "--milestone", "M-01", "--role", "shared")
        self.assertEqual(self.run_cli("validate", "demo-task"), 1)

    def test_validate_allows_html_comments_without_template_placeholders(self):
        self.run_cli("create", "demo-task")
        self.run_cli("set-package-sizing", "demo-task", "--status", "fits_package", "--actor", "brainstorm", "--phase", "brainstorm", "--decision", "single package")
        self.run_cli("set-prd-status", "demo-task", "--status", "ready-for-task", "--actor", "brainstorm", "--note", "ready")
        self.run_cli("add-child", "demo-task", "--id", "T-001", "--title", "ADD first", "--milestone", "M-01", "--role", "shared")
        (self.package_dir() / "task.md").write_text("# 任务: demo-task\n\n<!-- review note -->\n\n- id: T-001\n  title: ADD first\n", encoding="utf-8")
        self.assertEqual(self.run_cli("validate", "demo-task"), 0)

    def test_validate_rejects_angle_bracket_template_placeholders(self):
        self.run_cli("create", "demo-task")
        self.run_cli("set-package-sizing", "demo-task", "--status", "fits_package", "--actor", "brainstorm", "--phase", "brainstorm", "--decision", "single package")
        self.run_cli("set-prd-status", "demo-task", "--status", "ready-for-task", "--actor", "brainstorm", "--note", "ready")
        self.run_cli("add-child", "demo-task", "--id", "T-001", "--title", "ADD first", "--milestone", "M-01", "--role", "shared")
        (self.package_dir() / "task.md").write_text("# 任务: demo-task\n\n- id: T-001\n  title: ADD <deliverable>\n", encoding="utf-8")
        self.assertEqual(self.run_cli("validate", "demo-task"), 1)

    def test_validate_allows_real_task_id_lists(self):
        self.run_cli("create", "demo-task")
        self.run_cli("set-package-sizing", "demo-task", "--status", "fits_package", "--actor", "brainstorm", "--phase", "brainstorm", "--decision", "single package")
        self.run_cli("set-prd-status", "demo-task", "--status", "ready-for-task", "--actor", "brainstorm", "--note", "ready")
        self.run_cli("add-child", "demo-task", "--id", "T-001", "--title", "ADD first", "--milestone", "M-01", "--role", "shared")
        (self.package_dir() / "task.md").write_text("# 任务: demo-task\n\n### M-01\n\n- 包含任务: [T-001]\n\n- id: T-001\n  title: ADD first\n", encoding="utf-8")
        self.assertEqual(self.run_cli("validate", "demo-task"), 0)

    def test_invalid_jsonl_fails_validation(self):
        self.run_cli("create", "demo-task")
        (self.package_dir() / "context" / "impl.jsonl").write_text("{bad json\n", encoding="utf-8")
        self.assertEqual(self.run_cli("validate", "demo-task"), 1)

    def test_validate_allows_legacy_missing_execution(self):
        self.run_cli("create", "demo-task")
        data = self.task_json()
        del data["execution"]
        (self.package_dir() / "task.json").write_text(json.dumps(data), encoding="utf-8")
        self.assertEqual(self.run_cli("validate", "demo-task"), 0)

    def test_validate_rejects_invalid_execution_status(self):
        self.run_cli("create", "demo-task")
        data = self.task_json()
        data["execution"]["status"] = "bad"
        (self.package_dir() / "task.json").write_text(json.dumps(data), encoding="utf-8")
        self.assertEqual(self.run_cli("validate", "demo-task"), 1)

    def test_validate_allows_legacy_missing_execution_checkpoints(self):
        self.run_cli("create", "demo-task")
        data = self.task_json()
        del data["execution"]["checkpoints"]
        (self.package_dir() / "task.json").write_text(json.dumps(data), encoding="utf-8")
        self.assertEqual(self.run_cli("validate", "demo-task"), 0)

    def test_set_execution_and_pr_record_package_metadata(self):
        self.run_cli("create", "demo-task")
        self.assertEqual(self.run_cli("set-execution", "demo-task", "--status", "in_progress", "--base-branch", "main", "--branch", "arbor/demo-task", "--worktree", "/tmp/demo-task", "--worktree-created-by", "manual"), 0)
        self.assertEqual(self.run_cli("set-pr", "demo-task", "--url", "https://example.com/pr/1", "--number", "1", "--state", "open"), 0)
        execution = self.task_json()["execution"]
        self.assertEqual(execution["branch"]["name"], "arbor/demo-task")
        self.assertEqual(execution["worktree"]["created_by"], "manual")
        self.assertEqual(execution["pr"]["number"], 1)
        self.assertEqual(execution["pr"]["state"], "open")
        self.assertEqual(execution["status"], "pr_open")
        self.assertEqual(self.run_cli("validate", "demo-task"), 0)

    def test_single_approved_task_does_not_review_package_when_more_tasks_exist(self):
        self.run_cli("create", "demo-task")
        self.run_cli("set-package-sizing", "demo-task", "--status", "fits_package", "--actor", "brainstorm", "--phase", "brainstorm", "--decision", "single package")
        self.run_cli("add-child", "demo-task", "--id", "T-001", "--title", "ADD first", "--milestone", "M-01", "--role", "shared")
        self.run_cli("set-status", "demo-task", "--task", "T-001", "--state", "approved", "--actor", "review", "--note", "ok")
        self.run_cli("add-child", "demo-task", "--id", "T-002", "--title", "ADD second", "--milestone", "M-01", "--role", "shared", "--depends-on", "T-001")
        data = self.task_json()
        self.assertEqual(data["state"], "ready")
        self.assertEqual(data["next_action"]["skill"], "impl")
        self.assertEqual(data["next_action"]["task_id"], "T-002")

    def test_all_tasks_approved_reviews_package(self):
        self.run_cli("create", "demo-task")
        self.run_cli("set-package-sizing", "demo-task", "--status", "fits_package", "--actor", "brainstorm", "--phase", "brainstorm", "--decision", "single package")
        self.run_cli("add-child", "demo-task", "--id", "T-001", "--title", "ADD first", "--milestone", "M-01", "--role", "shared")
        self.run_cli("add-child", "demo-task", "--id", "T-002", "--title", "ADD second", "--milestone", "M-01", "--role", "shared")
        self.run_cli("set-status", "demo-task", "--task", "T-001", "--state", "approved", "--actor", "review", "--note", "ok")
        self.run_cli("set-status", "demo-task", "--task", "T-002", "--state", "approved", "--actor", "review", "--note", "ok")
        data = self.task_json()
        self.assertEqual(data["state"], "reviewed")
        self.assertEqual(data["next_action"]["skill"], "none")

    def test_done_task_prioritizes_review_before_next_impl(self):
        self.run_cli("create", "demo-task")
        self.run_cli("set-package-sizing", "demo-task", "--status", "fits_package", "--actor", "brainstorm", "--phase", "brainstorm", "--decision", "single package")
        self.run_cli("add-child", "demo-task", "--id", "T-001", "--title", "ADD first", "--milestone", "M-01", "--role", "shared")
        self.run_cli("add-child", "demo-task", "--id", "T-002", "--title", "ADD second", "--milestone", "M-01", "--role", "shared")
        self.run_cli("set-status", "demo-task", "--task", "T-001", "--state", "done", "--actor", "impl", "--note", "done")
        data = self.task_json()
        self.assertEqual(data["state"], "impl_done")
        self.assertEqual(data["next_action"]["skill"], "review")
        self.assertEqual(data["next_action"]["task_id"], "T-001")

    def test_list_and_show_json_are_parseable(self):
        self.run_cli("create", "demo-task")
        items = arbor.list_packages(self.root)
        self.assertEqual(items[0]["name"], "demo-task")
        self.assertIn("execution_status", items[0])
        self.assertIn("package_sizing", items[0])
        shown = arbor.show_package(self.root, "demo-task")
        self.assertEqual(shown["name"], "demo-task")
        self.assertIn("execution", shown)
        self.assertIn("package_sizing", shown)
        self.assertTrue(shown["validation"]["ok"])

    def test_legacy_source_type_records_legacy_path(self):
        self.run_cli("create", "legacy-demo", "--source-type", "legacy-brainstorm")
        data = self.task_json("legacy-demo")
        self.assertEqual(data["prd"]["legacy_source"], ".arbor/brainstorms/legacy-demo.md")

    def test_arbor_guard_blocks_direct_control_state_and_context_jsonl(self):
        control = arbor_guard.evaluate({"tool_name": "Write", "tool_input": {"file_path": str(self.root / ".arbor" / "tasks" / "demo-task" / "task.json")}})
        self.assertEqual(control["decision"], "block")
        self.assertIn("helpers", control["reason"])
        context = arbor_guard.evaluate({"tool_name": "Edit", "tool_input": {"file_path": str(self.root / ".arbor" / "tasks" / "demo-task" / "context" / "impl.jsonl")}})
        self.assertEqual(context["decision"], "block")
        self.assertIn("add-context-batch", context["reason"])

    def test_arbor_guard_blocks_destructive_bash_and_allows_safe_tools(self):
        blocked = arbor_guard.evaluate({"tool_name": "Bash", "tool_input": {"command": "git reset --hard HEAD"}})
        self.assertEqual(blocked["decision"], "block")
        allowed = arbor_guard.evaluate({"tool_name": "Read", "tool_input": {"file_path": str(self.root / "README.md")}})
        self.assertEqual(allowed["decision"], "allow")


if __name__ == "__main__":
    unittest.main()

import importlib.util
import contextlib
import io
import json
import subprocess
import sys
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
READY_PRD = """# Demo package

## Technical Framing

- Existing stack / framework: N/A
- Auth / permissions: N/A
- Frontend / backend boundary: N/A
- Data model / persistence: N/A
- Admin / ops surface: N/A
- External integrations: N/A
- Testing strategy: validate package
- Migration / rollout / rollback: N/A

## Slices

### S-001: First slice — create baseline behavior

- 完成标志：baseline behavior created and verified
- 数据/schema：demo_records
- 代码锚点：src/demo.py:12, app/demo/page.tsx:L8
- 测试：tests/test_demo.py::test_baseline

### S-002: Self-check — run validation

- 完成标志：validation passes
- 数据/schema：N/A
- 代码锚点：tools/validate.py:3
- 测试：python -m unittest tests/test_validate.py
"""


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

    def run_hook(self, payload):
        return subprocess.run(
            [sys.executable, str(HOOK_PATH)],
            cwd=self.root,
            input=json.dumps(payload),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )

    def package_dir(self, name="demo-package"):
        return self.root / ".arbor" / "tasks" / name

    def task_json(self, name="demo-package"):
        return json.loads((self.package_dir(name) / "task.json").read_text())

    def finalize_single(self, name="demo-package"):
        spec = {
            "kind": "single",
            "name": name,
            "title": "Demo package",
            "prd": READY_PRD,
            "decision": "single package with PRD-local Slices",
        }
        self._create_slice_tasks(name)
        self.assertEqual(self.run_cli("finalize-brainstorm", "--input-json", json.dumps(spec), "--json"), 0)

    def finalize_single_json(self, name="demo-package"):
        spec = {
            "kind": "single",
            "name": name,
            "title": "Demo package",
            "prd": READY_PRD,
            "decision": "single package with PRD-local Slices",
        }
        self._create_slice_tasks(name)
        result = subprocess.run(
            [sys.executable, str(MODULE_PATH), "--root", str(self.root), "--now", NOW, "finalize-brainstorm", "--input-json", json.dumps(spec), "--json"],
            cwd=self.root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def record_all_required_checks(self, name="demo-package"):
        self.assertEqual(self.run_cli("derive-required-checks", name, "--json"), 0)
        data = self.task_json(name)
        check_ids = []
        for required in data["required_checks"]:
            self.assertEqual(
                self.run_cli(
                    "run-check",
                    name,
                    "--required-check",
                    required["id"],
                    "--json",
                    "--",
                    sys.executable,
                    "-c",
                    "pass",
                ),
                0,
            )
            check_ids.append(self.task_json(name)["checks"][-1]["id"])
        return check_ids

    def record_functional_check(self, name="demo-package", status="passed"):
        args = [
            "record-check",
            name,
            "--kind",
            "functional",
            "--status",
            status,
            "--summary",
            "functional smoke",
        ]
        if status == "passed":
            args.extend(["--evidence", "core path observed"])
        elif status in {"blocked", "not_run"}:
            args.extend(["--reason", "browser unavailable", "--evidence", "launch failed"])
        elif status == "failed":
            args.extend(["--evidence", "core path failed", "--exit-code", "1"])
        self.assertEqual(self.run_cli(*args), 0)
        return self.task_json(name)["checks"][-1]["id"]

    def _create_slice_tasks(self, name="demo-package"):
        slices_dir = self.root / ".arbor" / "tasks" / name / "slices"
        slices_dir.mkdir(parents=True, exist_ok=True)
        (slices_dir / "S-001.md").write_text(
            "# S-001: First slice\n\n## Acceptance\n\nGiven:\n- setup\n\nWhen:\n- action\n\nThen:\n- result\n\n## Verification\n\n- [test] run tests\n",
            encoding="utf-8",
        )
        (slices_dir / "S-002.md").write_text(
            "# S-002: Self-check\n\n## Acceptance\n\nGiven:\n- baseline exists\n\nWhen:\n- validate\n\nThen:\n- passes\n\n## Verification\n\n- [manual] run validation\n",
            encoding="utf-8",
        )

    def test_sdd_arbor_bin_wrapper_runs_from_project_cwd(self):
        spec = {
            "kind": "single",
            "name": "demo-package",
            "title": "Demo package",
            "prd": READY_PRD,
        }
        self._create_slice_tasks("demo-package")
        result = self.run_bin("finalize-brainstorm", "--input-json", json.dumps(spec))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.root / ".arbor" / "tasks" / "demo-package" / "task.json").exists())
        self.assertFalse((PLUGIN_ROOT / ".arbor").exists())

    def test_help_hides_internal_plumbing_and_removed_task_commands(self):
        result = self.run_bin("--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("finalize-brainstorm", result.stdout)
        self.assertNotIn("set-package-sizing", result.stdout)
        self.assertNotIn("set-prd-status", result.stdout)
        self.assertNotIn("parent-check", result.stdout)
        self.assertNotIn("set-execution-plan", result.stdout)
        self.assertNotIn("update-plan-item", result.stdout)
        self.assertNotIn("materialize-children", result.stdout)
        self.assertNotIn("add-child", result.stdout)
        self.assertNotIn("--mode", result.stdout)

    def test_finalize_brainstorm_help_documents_single_package_schema(self):
        result = self.run_bin("finalize-brainstorm", "--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("JSON schema", result.stdout)
        self.assertIn('"name"|"package"', result.stdout)
        self.assertIn('"prd"|"prd_path"', result.stdout)
        self.assertIn("Large scopes use PRD ## Slices", result.stdout)
        self.assertNotIn('"children"', result.stdout)

    def test_create_writes_prd_first_package_without_task_markdown(self):
        code = self.run_cli("create", "demo-package", "--title", "Demo package")
        self.assertEqual(code, 0)
        pkg = self.package_dir()
        self.assertTrue((pkg / "prd.md").exists())
        self.assertFalse((pkg / "task.md").exists())
        self.assertTrue((pkg / "task.json").exists())
        self.assertTrue((pkg / "review.md").exists())
        self.assertTrue((pkg / "context" / "impl.jsonl").exists())
        self.assertTrue((pkg / "context" / "review.jsonl").exists())
        self.assertTrue((pkg / "context" / "sources.jsonl").exists())
        self.assertTrue((pkg / "artifacts").is_dir())
        data = self.task_json()
        self.assertEqual(data["schema_version"], "arbor-package-v1")
        self.assertEqual(data["state"], "draft")
        self.assertEqual(data["package_kind"], "single")
        self.assertNotIn("parent", data)
        self.assertNotIn("children", data)
        self.assertEqual(data["prd"]["file"], "prd.md")
        self.assertEqual(data["prd"]["status"], "draft")
        self.assertEqual(data["current_phase"], "brainstorm")
        self.assertEqual(data["execution"]["boundary"], "package")
        self.assertEqual(data["execution"]["unit_path"], ".arbor/tasks/demo-package")
        prd_text = (pkg / "prd.md").read_text(encoding="utf-8")
        self.assertIn("progress lives in `task.json` `slices` via `sdd-arbor mark-slice`", prd_text)
        self.assertIn("### S-001:", prd_text)
        self.assertIn("- 完成标志：", prd_text)
        self.assertNotIn("Impl 只更新 [ ] / [-] / [x]", prd_text)
        self.assertNotIn("- [ ] S-001", prd_text)
        self.assertNotIn("技术锚点", prd_text)
        self.assertNotIn("测试切片", prd_text)
        self.assertNotIn("plan", data["execution"])
        self.assertNotIn("child_task_scope", data["execution"])
        self.assertNotIn("tasks", data)
        self.assertNotIn("active_task", data)
        self.assertNotIn("mode", data)
        self.assertEqual(self.run_cli("validate", "demo-package"), 0)

    def test_create_does_not_overwrite_existing_prd(self):
        self.run_cli("create", "demo-package", "--title", "Demo package")
        prd = self.package_dir() / "prd.md"
        prd.write_text("custom prd", encoding="utf-8")
        self.run_cli("create", "demo-package", "--title", "Demo package")
        self.assertEqual(prd.read_text(encoding="utf-8"), "custom prd")

    def test_prd_template_sourced_from_asset_no_drift(self):
        """Regression guard: prd_template must read from the brainstorm asset, not a hardcoded copy."""
        from arbor_core.templates import _ASSET_PRD_TEMPLATE, prd_template

        asset_path = PLUGIN_ROOT / "skills" / "brainstorm" / "assets" / "templates" / "prd.md"
        self.assertEqual(_ASSET_PRD_TEMPLATE.resolve(), asset_path.resolve())
        self.assertTrue(_ASSET_PRD_TEMPLATE.exists())
        rendered = prd_template("demo-package", "Demo Title", "2026-05-05T00:00:00+00:00")
        for section in [
            "## What I already know",
            "## Package artifacts（按需）",
            "## Slices",
            "## Technical Framing",
            "## Sources",
            "═══ 自检清单",
        ]:
            self.assertIn(section, rendered, f"section {section!r} missing — prd_template may have drifted from asset")
        self.assertIn("# Demo Title", rendered)
        self.assertIn("name: demo-package", rendered)
        self.assertIn("package: .arbor/tasks/demo-package/", rendered)
        self.assertIn("date: 2026-05-05", rendered)
        self.assertNotIn("MM-DD-<topic-slug>", rendered)
        self.assertNotIn("YYYY-MM-DD", rendered)

    def test_finalize_brainstorm_single_creates_ready_package(self):
        output = self.finalize_single_json()
        self.assertEqual(output["kind"], "single")
        self.assertEqual(output["root_package"], "demo-package")
        self.assertEqual(output["packages"][0]["state"], "ready")
        self.assertEqual(output["packages"][0]["next_action"], {"skill": "impl", "reason": "PRD 已就绪，可以开始执行"})
        data = self.task_json()
        self.assertEqual(data["package_kind"], "single")
        self.assertEqual(data["package_sizing"]["status"], "fits_package")
        self.assertEqual(data["prd"]["status"], "ready")
        self.assertEqual(data["state"], "ready")
        self.assertEqual(data["next_action"], {"skill": "impl", "reason": "PRD 已就绪，可以开始执行"})
        self.assertEqual((self.package_dir() / "prd.md").read_text(encoding="utf-8"), READY_PRD)
        self.assertEqual(self.run_cli("validate", "demo-package"), 0)

    def test_finalize_brainstorm_removes_draft_only_sections(self):
        prd = READY_PRD + """
## Requirements (evolving)

- draft discovery note

## Acceptance Criteria (evolving)

- draft acceptance note

## Interview Log

- Q: old question
"""
        spec = {"kind": "single", "name": "demo-package", "title": "Demo package", "prd": prd}
        self._create_slice_tasks("demo-package")
        self.assertEqual(self.run_cli("finalize-brainstorm", "--input-json", json.dumps(spec)), 0)
        prd_text = (self.package_dir() / "prd.md").read_text(encoding="utf-8")
        self.assertIn("## Slices", prd_text)
        self.assertNotIn("## Requirements (evolving)", prd_text)
        self.assertNotIn("## Acceptance Criteria (evolving)", prd_text)
        self.assertNotIn("## Interview Log", prd_text)

    def test_finalize_brainstorm_syncs_prd_frontmatter_status_to_ready(self):
        """Regression: PRD frontmatter `status:` must follow task.json after finalize.

        Previously brainstorm finalize updated task.json prd.status to ready
        but left the YAML frontmatter on prd.md showing `status: draft`,
        which made downstream review and audit confusing.
        """
        prd_with_frontmatter = (
            "---\n"
            "name: demo-package\n"
            "status: draft\n"
            "date: 2026-04-25\n"
            "---\n"
            "\n"
            + READY_PRD
        )
        spec = {
            "kind": "single",
            "name": "demo-package",
            "title": "Demo package",
            "prd": prd_with_frontmatter,
            "decision": "single package with PRD-local Slices",
        }
        self._create_slice_tasks("demo-package")
        self.assertEqual(
            self.run_cli("finalize-brainstorm", "--input-json", json.dumps(spec)),
            0,
        )
        self.assertEqual(self.task_json()["prd"]["status"], "ready")
        prd_text = (self.package_dir() / "prd.md").read_text(encoding="utf-8")
        self.assertIn("status: ready\n", prd_text)
        self.assertNotIn("status: draft\n", prd_text)
        self.assertIn("name: demo-package\n", prd_text)
        self.assertIn("date: 2026-04-25\n", prd_text)

    def test_finalize_brainstorm_leaves_prd_without_frontmatter_untouched(self):
        """Regression guard: PRDs without YAML frontmatter must not gain one."""
        self.finalize_single()
        self.assertEqual(
            (self.package_dir() / "prd.md").read_text(encoding="utf-8"),
            READY_PRD,
        )

    def test_finalize_brainstorm_accepts_mm_dd_prefixed_package_name(self):
        self.finalize_single("05-02-knowledge-paid-system")
        self.assertTrue((self.package_dir("05-02-knowledge-paid-system") / "task.json").exists())
        data = self.task_json("05-02-knowledge-paid-system")
        self.assertEqual(data["execution"]["unit_path"], ".arbor/tasks/05-02-knowledge-paid-system")
        self.assertEqual(self.run_cli("validate", "05-02-knowledge-paid-system"), 0)

    def test_finalize_brainstorm_accepts_package_and_prd_path_aliases(self):
        self.run_cli("create", "demo-package", "--title", "Demo package")
        prd = self.package_dir() / "prd.md"
        prd.write_text(READY_PRD, encoding="utf-8")
        self._create_slice_tasks("demo-package")
        spec = {"kind": "single", "package": "demo-package", "prd_path": ".arbor/tasks/demo-package/prd.md"}

        self.assertEqual(self.run_cli("finalize-brainstorm", "--input-json", json.dumps(spec)), 0)

        self.assertEqual((self.package_dir() / "prd.md").read_text(encoding="utf-8"), READY_PRD)
        self.assertEqual(self.task_json()["prd"]["status"], "ready")

    def test_finalize_brainstorm_requires_slice_task_files_before_finalize(self):
        spec = {"kind": "single", "name": "demo-package", "title": "Demo package", "prd": READY_PRD}
        result = self.run_bin("finalize-brainstorm", "--input-json", json.dumps(spec))

        self.assertEqual(result.returncode, 1)
        self.assertIn("slices/ directory does not exist", result.stderr)
        self.assertFalse(self.package_dir().exists())

    def test_finalize_brainstorm_rejects_parent_child_package_splitting(self):
        spec = {
            "kind": "parent",
            "name": "big-init",
            "title": "Big init",
            "prd": READY_PRD,
            "children": [{"package": "big-core", "title": "Big core"}],
        }
        self.assertEqual(self.run_cli("finalize-brainstorm", "--input-json", json.dumps(spec), "--json"), 1)
        self.assertFalse(self.package_dir("big-init").exists())
        self.assertFalse(self.package_dir("big-core").exists())

    def test_finalize_brainstorm_rejects_missing_prd_content(self):
        spec = {"kind": "single", "name": "demo-package"}
        self.assertEqual(self.run_cli("finalize-brainstorm", "--input-json", json.dumps(spec)), 1)
        self.assertFalse(self.package_dir("demo-package").exists())

    def test_finalize_brainstorm_rejects_obsolete_mode_field(self):
        spec = {"kind": "single", "name": "demo-package", "prd": "# Demo", "mode": "lean"}
        self.assertEqual(self.run_cli("finalize-brainstorm", "--input-json", json.dumps(spec)), 1)
        self.assertFalse(self.package_dir("demo-package").exists())

    def test_finalize_brainstorm_rejects_prd_without_slices_section(self):
        bad_prd = "# Demo\n\n## Technical Framing\n\n- stack: N/A\n"
        spec = {"kind": "single", "name": "demo-package", "prd": bad_prd}
        self.assertEqual(self.run_cli("finalize-brainstorm", "--input-json", json.dumps(spec)), 1)
        self.assertFalse(self.package_dir().exists())

    def test_finalize_brainstorm_rejects_slices_without_s_nnn_header(self):
        bad_prd = (
            "# Demo\n\n## Slices\n\n"
            "- just some free text without S-NNN header\n"
            "- 完成标志：something\n"
        )
        spec = {"kind": "single", "name": "demo-package", "prd": bad_prd}
        self.assertEqual(self.run_cli("finalize-brainstorm", "--input-json", json.dumps(spec)), 1)
        self.assertFalse(self.package_dir().exists())

    def test_finalize_brainstorm_rejects_slices_without_completion_marker(self):
        bad_prd = (
            "# Demo\n\n## Slices\n\n"
            "### S-001: slice without completion marker\n\n"
            "- some note\n"
        )
        spec = {"kind": "single", "name": "demo-package", "prd": bad_prd}
        result = self.run_bin("finalize-brainstorm", "--input-json", json.dumps(spec))
        self.assertEqual(result.returncode, 1)
        self.assertIn("S-001", result.stderr)
        self.assertIn("完成标志", result.stderr)
        self.assertFalse(self.package_dir().exists())

    def test_finalize_brainstorm_rejects_slice_missing_completion_marker_even_when_siblings_have_one(self):
        bad_prd = (
            "# Demo\n\n## Slices\n\n"
            "### S-001: first slice\n\n"
            "- 完成标志：基建完成\n\n"
            "### S-002: second slice missing marker\n\n"
            "- 代码锚点：src/foo.ts [new]\n\n"
            "### S-003: third slice also missing marker\n\n"
            "- 测试：something\n"
        )
        spec = {"kind": "single", "name": "demo-package", "prd": bad_prd}
        result = self.run_bin("finalize-brainstorm", "--input-json", json.dumps(spec))
        self.assertEqual(result.returncode, 1)
        self.assertIn("S-002", result.stderr)
        self.assertIn("S-003", result.stderr)
        self.assertNotIn("S-001", result.stderr)
        self.assertIn("完成标志", result.stderr)
        self.assertFalse(self.package_dir().exists())

    def test_finalize_brainstorm_rejects_legacy_slice_checkbox_format(self):
        bad_prd = (
            "# Demo\n\n## Slices\n\n"
            "- [ ] S-001: legacy checkbox format\n"
            "- [-] S-002: in-progress legacy\n"
        )
        spec = {"kind": "single", "name": "demo-package", "prd": bad_prd}
        self.assertEqual(self.run_cli("finalize-brainstorm", "--input-json", json.dumps(spec)), 1)
        self.assertFalse(self.package_dir().exists())

    def test_finalize_brainstorm_rejects_unfilled_slice_scaffold_tokens(self):
        bad_prd = (
            "# Demo\n\n## Slices\n\n"
            "### S-001: <walking skeleton 或第一个独立可验证的契约/功能>\n\n"
            "- 完成标志：<完成后多了什么可独立验证的契约/功能/行为>\n"
        )
        spec = {"kind": "single", "name": "demo-package", "prd": bad_prd}
        result = self.run_bin("finalize-brainstorm", "--input-json", json.dumps(spec))
        self.assertEqual(result.returncode, 1)
        self.assertIn("scaffold", result.stderr)
        self.assertFalse(self.package_dir().exists())

    def test_finalize_brainstorm_validates_slice_tasks_when_dir_exists(self):
        """When slices/ dir exists, finalize validates task files are present."""
        self.run_cli("create", "demo-package", "--title", "Demo package")
        prd = self.package_dir() / "prd.md"
        prd.write_text(READY_PRD, encoding="utf-8")
        # Create slices/ dir but only S-001.md (missing S-002.md)
        slices_dir = self.package_dir() / "slices"
        slices_dir.mkdir(parents=True, exist_ok=True)
        (slices_dir / "S-001.md").write_text(
            "# S-001\n\n## Acceptance\n\nThen: result\n\n## Verification\n\n- test\n",
            encoding="utf-8",
        )
        spec = {"kind": "single", "package": "demo-package", "prd_path": ".arbor/tasks/demo-package/prd.md"}
        self.assertEqual(self.run_cli("finalize-brainstorm", "--input-json", json.dumps(spec)), 1)

    def test_finalize_brainstorm_validates_slice_task_sections(self):
        """Task file missing ## Acceptance or ## Verification is rejected."""
        self.run_cli("create", "demo-package", "--title", "Demo package")
        prd = self.package_dir() / "prd.md"
        prd.write_text(READY_PRD, encoding="utf-8")
        slices_dir = self.package_dir() / "slices"
        slices_dir.mkdir(parents=True, exist_ok=True)
        (slices_dir / "S-001.md").write_text(
            "# S-001\n\n## Acceptance\n\nThen: result\n\n## Verification\n\n- test\n",
            encoding="utf-8",
        )
        # S-002 missing ## Verification
        (slices_dir / "S-002.md").write_text(
            "# S-002\n\n## Acceptance\n\nThen: result\n",
            encoding="utf-8",
        )
        spec = {"kind": "single", "package": "demo-package", "prd_path": ".arbor/tasks/demo-package/prd.md"}
        self.assertEqual(self.run_cli("finalize-brainstorm", "--input-json", json.dumps(spec)), 1)

    def test_finalize_brainstorm_rejects_empty_verification_section(self):
        self.run_cli("create", "demo-package", "--title", "Demo package")
        prd = self.package_dir() / "prd.md"
        prd.write_text(READY_PRD, encoding="utf-8")
        slices_dir = self.package_dir() / "slices"
        slices_dir.mkdir(parents=True, exist_ok=True)
        (slices_dir / "S-001.md").write_text(
            "# S-001\n\n## Acceptance\n\nThen: result\n\n## Verification\n\n",
            encoding="utf-8",
        )
        (slices_dir / "S-002.md").write_text(
            "# S-002\n\n## Acceptance\n\nThen: result\n\n## Verification\n\n- [manual] run validation\n",
            encoding="utf-8",
        )
        spec = {"kind": "single", "package": "demo-package", "prd_path": ".arbor/tasks/demo-package/prd.md"}
        result = self.run_bin("finalize-brainstorm", "--input-json", json.dumps(spec))
        self.assertEqual(result.returncode, 1)
        self.assertIn("S-001", result.stderr)
        self.assertIn("Verification", result.stderr)

    def test_finalize_brainstorm_passes_with_complete_slice_tasks(self):
        """When all slice task files have required sections, finalize succeeds."""
        self.run_cli("create", "demo-package", "--title", "Demo package")
        prd = self.package_dir() / "prd.md"
        prd.write_text(READY_PRD, encoding="utf-8")
        self._create_slice_tasks("demo-package")
        spec = {"kind": "single", "package": "demo-package", "prd_path": ".arbor/tasks/demo-package/prd.md"}
        self.assertEqual(self.run_cli("finalize-brainstorm", "--input-json", json.dumps(spec)), 0)

    def test_validate_rejects_obsolete_state_shapes(self):
        self.run_cli("create", "demo-package")
        (self.package_dir() / "task.md").write_text("obsolete", encoding="utf-8")
        data = self.task_json()
        data["tasks"] = []
        data["mode"] = "strict-atomic"
        data["parent"] = {"package": "old-parent"}
        data["children"] = [{"package": "old-child"}]
        data["execution"]["plan"] = [{"id": "P-001", "title": "old plan", "status": "pending"}]
        (self.package_dir() / "task.json").write_text(json.dumps(data), encoding="utf-8")
        errors = arbor.validate_package(self.root, "demo-package")
        self.assertTrue(any("task.md is obsolete" in error for error in errors))
        self.assertTrue(any("tasks[] is obsolete" in error for error in errors))
        self.assertTrue(any("mode is obsolete" in error for error in errors))
        self.assertTrue(any("parent metadata is obsolete" in error for error in errors))
        self.assertTrue(any("children metadata is obsolete" in error for error in errors))
        self.assertTrue(any("execution.plan is obsolete" in error for error in errors))

    def test_set_status_updates_simplified_state_and_maps_legacy_state(self):
        self.finalize_single()
        code = self.run_cli("set-status", "demo-package", "--state", "doing", "--actor", "impl", "--note", "start")
        self.assertEqual(code, 0)
        data = self.task_json()
        self.assertEqual(data["state"], "doing")
        self.assertEqual(data["next_action"]["skill"], "impl")
        self.assertEqual(data["execution"]["status"], "in_progress")
        self.assertEqual(data["phase_history"][-1]["actor"], "impl")
        self.assertEqual(self.run_cli("set-status", "demo-package", "--state", "impl_done", "--actor", "impl", "--note", "legacy"), 0)
        self.assertEqual(self.task_json()["state"], "done")

    def test_ready_prd_requires_package_sizing(self):
        from arbor_core.errors import ArborError
        from arbor_core.package_lifecycle import update_prd_status

        self.run_cli("create", "demo-package")
        with self.assertRaises(ArborError):
            update_prd_status(self.root, "demo-package", "ready", "brainstorm", "ready", NOW)
        data = self.task_json()
        self.assertEqual(data["prd"]["status"], "draft")
        self.assertEqual(data["package_sizing"]["status"], "unchecked")

    def test_required_checks_and_run_check_record_evidence(self):
        self.finalize_single()
        self.assertEqual(self.run_cli("derive-required-checks", "demo-package", "--json"), 0)
        data = self.task_json()
        self.assertEqual([item["id"] for item in data["required_checks"]], ["req_S001_001", "req_S002_001"])
        self.assertEqual(data["required_checks"][0]["kind"], "test")
        self.assertEqual(
            self.run_cli(
                "run-check",
                "demo-package",
                "--required-check",
                "req_S001_001",
                "--json",
                "--",
                sys.executable,
                "-c",
                "print('ok')",
            ),
            0,
        )
        data = self.task_json()
        check = data["checks"][0]
        self.assertEqual(check["status"], "passed")
        self.assertEqual(check["required_check"], "req_S001_001")
        self.assertEqual(check["exit_code"], 0)
        self.assertTrue((self.package_dir() / check["stdout_path"]).exists())
        self.assertTrue((self.package_dir() / check["stderr_path"]).exists())

    def test_required_checks_refresh_when_slice_verification_changes(self):
        self.finalize_single()
        self.assertEqual(self.run_cli("derive-required-checks", "demo-package"), 0)
        old_checks = self.task_json()["required_checks"]
        old_fp = old_checks[0]["fingerprint"]
        self.assertEqual(self.run_cli("run-check", "demo-package", "--required-check", "req_S001_001", "--", sys.executable, "-c", "pass"), 0)
        old_check_id = self.task_json()["checks"][-1]["id"]
        (self.package_dir() / "slices" / "S-001.md").write_text(
            "# S-001: First slice\n\n## Acceptance\n\nThen:\n- result\n\n## Verification\n\n- [test] run new regression tests\n",
            encoding="utf-8",
        )
        self.assertEqual(self.run_cli("set-status", "demo-package", "--state", "doing", "--actor", "impl", "--note", "refresh"), 0)
        data = self.task_json()
        self.assertNotEqual(data["required_checks"][0]["fingerprint"], old_fp)
        rejected = self.run_bin(
            "record-impl-result",
            "demo-package",
            "--state",
            "done",
            "--summary",
            "stale evidence",
            "--acceptance",
            "S-001 done",
            "--acceptance",
            "S-002 done",
            "--check",
            old_check_id,
        )
        self.assertEqual(rejected.returncode, 1)
        self.assertIn("stale", rejected.stderr)

    def test_mark_slice_uses_latest_required_check_evidence(self):
        self.finalize_single()
        self.assertEqual(self.run_cli("run-check", "demo-package", "--required-check", "req_S001_001", "--", sys.executable, "-c", "pass"), 0)
        stale_pass = self.task_json()["checks"][-1]["id"]
        self.assertEqual(self.run_cli("run-check", "demo-package", "--required-check", "req_S001_001", "--", sys.executable, "-c", "raise SystemExit(1)"), 1)
        failed = self.task_json()["checks"][-1]["id"]
        self.assertNotEqual(stale_pass, failed)
        rejected = self.run_bin("mark-slice", "demo-package", "--id", "S-001", "--status", "done", "--acceptance", "S-001: baseline verified")
        self.assertEqual(rejected.returncode, 1)
        self.assertIn("最新证据失败", rejected.stderr)
        self.assertEqual(self.run_cli("run-check", "demo-package", "--required-check", "req_S001_001", "--", sys.executable, "-c", "pass"), 0)
        latest_pass = self.task_json()["checks"][-1]["id"]
        self.assertEqual(self.run_cli("mark-slice", "demo-package", "--id", "S-001", "--status", "done", "--acceptance", "S-001: baseline verified"), 0)
        entry = next(item for item in self.task_json()["slices"] if item["id"] == "S-001")
        self.assertEqual(entry["checks"], [latest_pass])

    def test_done_rejects_missing_or_manual_automated_required_checks(self):
        self.finalize_single()
        self.assertEqual(self.run_cli("derive-required-checks", "demo-package"), 0)
        self.assertEqual(
            self.run_cli(
                "record-check",
                "demo-package",
                "--required-check",
                "req_S001_001",
                "--status",
                "passed",
                "--evidence",
                "claimed manually",
            ),
            0,
        )
        manual_check = self.task_json()["checks"][0]["id"]
        self.assertEqual(
            self.run_cli(
                "record-impl-result",
                "demo-package",
                "--state",
                "done",
                "--summary",
                "implemented",
                "--acceptance",
                "S-001 done",
                "--acceptance",
                "S-002 done",
                "--check",
                manual_check,
            ),
            1,
        )
        self.assertIsNone(self.task_json().get("impl_result"))

    def test_blocked_check_requires_reason_and_evidence(self):
        self.finalize_single()
        self.assertEqual(self.run_cli("derive-required-checks", "demo-package"), 0)
        self.assertEqual(
            self.run_cli(
                "record-check",
                "demo-package",
                "--required-check",
                "req_S001_001",
                "--status",
                "blocked",
                "--reason",
                "Docker unavailable",
            ),
            1,
        )
        self.assertEqual(
            self.run_cli(
                "record-check",
                "demo-package",
                "--required-check",
                "req_S001_001",
                "--status",
                "blocked",
                "--reason",
                "Docker unavailable",
                "--evidence",
                "docker info exit_code=1",
            ),
            0,
        )

    def test_record_impl_result_routes_structured_results(self):
        self.finalize_single()
        check_ids = self.record_all_required_checks()
        functional_check = self.record_functional_check()
        self.assertEqual(self.run_cli("record-impl-result", "demo-package", "--state", "done_with_concerns", "--summary", "implemented behavior", "--acceptance", "S-001 golden path passes", "--acceptance", "S-002 validation passes", "--check", check_ids[0], "--check", check_ids[1], "--functional-check", functional_check, "--concern", "edge case needs review", "--json"), 0)
        data = self.task_json()
        self.assertEqual(data["state"], "done")
        self.assertEqual(data["impl_result"]["state"], "DONE_WITH_CONCERNS")
        self.assertEqual(data["impl_result"]["acceptance"], ["S-001 golden path passes", "S-002 validation passes"])
        self.assertEqual(data["impl_result"]["acceptance_coverage"]["S-001"], ["S-001 golden path passes"])
        self.assertEqual(data["impl_result"]["checks"], check_ids)
        self.assertEqual(data["impl_result"]["check_coverage"]["req_S001_001"]["status"], "passed")
        self.assertEqual(data["impl_result"]["concerns"], ["edge case needs review"])
        self.assertEqual(data["next_action"]["skill"], "review")
        self.assertEqual(data["phase_history"][-1]["phase"], "impl")
        self.assertEqual(self.run_cli("record-impl-result", "demo-package", "--state", "approved", "--summary", "bad"), 1)

    def test_record_impl_result_rejects_missing_and_unknown_slice_acceptance(self):
        self.finalize_single()
        self.assertEqual(self.run_cli("record-impl-result", "demo-package", "--state", "done", "--summary", "implemented", "--acceptance", "S-001 passes"), 1)
        self.assertIsNone(self.task_json().get("impl_result"))
        self.assertEqual(self.run_cli("record-impl-result", "demo-package", "--state", "done", "--summary", "implemented", "--acceptance", "S-001 passes", "--acceptance", "S-999 unknown"), 1)
        self.assertIsNone(self.task_json().get("impl_result"))
        self.assertEqual(self.run_cli("record-impl-result", "demo-package", "--state", "done", "--summary", "implemented", "--acceptance", "All slices done"), 1)
        self.assertIsNone(self.task_json().get("impl_result"))

    def _create_multi_marker_slice_tasks(self, name="demo-package"):
        slices_dir = self.root / ".arbor" / "tasks" / name / "slices"
        slices_dir.mkdir(parents=True, exist_ok=True)
        (slices_dir / "S-001.md").write_text(
            "# S-001: Registration with duplicate guard\n\n## Acceptance\n\nGiven:\n- setup\n\nWhen:\n- register\n\nThen:\n- registered\n- can cancel\n- duplicate blocked\n\n## Verification\n\n- [test] run tests\n",
            encoding="utf-8",
        )
        (slices_dir / "S-002.md").write_text(
            "# S-002: Self-check\n\n## Acceptance\n\nGiven:\n- baseline\n\nWhen:\n- validate\n\nThen:\n- passes\n\n## Verification\n\n- [manual] run validation\n",
            encoding="utf-8",
        )

    def test_multi_marker_slice_rejects_bare_slice_id_coverage(self):
        """Multi-marker slices must be covered granularly — bare `S-NNN` does not suffice.

        This enforces the semantic: if you chose to list markers as a sublist,
        each is a separate claim requiring its own evidence. The back-compat
        escape hatch only exists for single-marker slices (which is the MVP /
        prototype case).
        """
        multi_marker_prd = """# Demo package

## Technical Framing

- Testing strategy: validate package

## Slices

### S-001: Registration with duplicate guard

- 完成标志：
  - 代居民报名
  - 取消报名
  - 重复报名被阻止

### S-002: Self-check

- 完成标志：validation passes
"""
        spec = {
            "kind": "single",
            "name": "demo-package",
            "title": "Demo",
            "prd": multi_marker_prd,
        }
        self._create_multi_marker_slice_tasks("demo-package")
        self.assertEqual(
            self.run_cli(
                "finalize-brainstorm",
                "--input-json",
                json.dumps(spec),
                "--json",
            ),
            0,
        )

        # Bare S-001 reference for a multi-marker slice should be rejected.
        self.assertEqual(
            self.run_cli(
                "record-impl-result",
                "demo-package",
                "--state",
                "done",
                "--summary",
                "implemented",
                "--acceptance",
                "S-001: happy path works",
                "--acceptance",
                "S-002: validation passes",
            ),
            1,
        )
        self.assertIsNone(self.task_json().get("impl_result"))

    def test_multi_marker_slice_rejects_partial_granular_coverage(self):
        multi_marker_prd = """# Demo package

## Technical Framing

- Testing strategy: validate package

## Slices

### S-001: Registration with duplicate guard

- 完成标志：
  - 代居民报名
  - 取消报名
  - 重复报名被阻止

### S-002: Self-check

- 完成标志：validation passes
"""
        spec = {"kind": "single", "name": "demo-package", "title": "Demo", "prd": multi_marker_prd}
        self._create_multi_marker_slice_tasks("demo-package")
        self.assertEqual(
            self.run_cli(
                "finalize-brainstorm",
                "--input-json",
                json.dumps(spec),
                "--json",
            ),
            0,
        )
        # Covering only S-001.1 and S-001.2 (skipping S-001.3 = 重复报名被阻止) must fail.
        # This is exactly the custom-2026-05-07 failure mode we want to catch.
        self.assertEqual(
            self.run_cli(
                "record-impl-result",
                "demo-package",
                "--state",
                "done",
                "--summary",
                "implemented",
                "--acceptance",
                "S-001.1: 代报名 API works",
                "--acceptance",
                "S-001.2: 取消 API works",
                "--acceptance",
                "S-002: validation passes",
            ),
            1,
        )
        self.assertIsNone(self.task_json().get("impl_result"))

    def test_multi_marker_slice_accepts_full_granular_coverage(self):
        multi_marker_prd = """# Demo package

## Technical Framing

- Testing strategy: validate package

## Slices

### S-001: Registration with duplicate guard

- 完成标志：
  - 代居民报名
  - 取消报名
  - 重复报名被阻止

### S-002: Self-check

- 完成标志：validation passes
"""
        spec = {"kind": "single", "name": "demo-package", "title": "Demo", "prd": multi_marker_prd}
        self._create_slice_tasks()
        self.assertEqual(
            self.run_cli(
                "finalize-brainstorm",
                "--input-json",
                json.dumps(spec),
                "--json",
            ),
            0,
        )
        check_ids = self.record_all_required_checks()
        functional_check = self.record_functional_check()
        self.assertEqual(
            self.run_cli(
                "record-impl-result",
                "demo-package",
                "--state",
                "done",
                "--summary",
                "implemented",
                "--acceptance",
                "S-001.1: 代报名 API works",
                "--acceptance",
                "S-001.2: 取消 API works",
                "--acceptance",
                "S-001.3: 重复报名 returns 409",
                "--acceptance",
                "S-002: validation passes",
                "--check",
                check_ids[0],
                "--check",
                check_ids[1],
                "--functional-check",
                functional_check,
            ),
            0,
        )
        data = self.task_json()
        self.assertEqual(data["state"], "done")
        self.assertEqual(len(data["impl_result"]["acceptance_coverage"]["S-001"]), 3)

    def test_record_impl_result_routes_context_and_blockers(self):
        self.finalize_single()
        self.assertEqual(self.run_cli("record-impl-result", "demo-package", "--state", "needs_context", "--summary", "PRD missing auth boundary"), 0)
        data = self.task_json()
        self.assertEqual(data["state"], "doing")
        self.assertEqual(data["next_action"]["skill"], "brainstorm")
        self.assertEqual(self.run_cli("record-impl-result", "demo-package", "--state", "blocked", "--summary", "database unavailable"), 0)
        data = self.task_json()
        self.assertEqual(data["state"], "doing")
        self.assertEqual(data["next_action"]["skill"], "user")

    def test_record_review_stores_package_verdict_and_appends_review_md(self):
        self.finalize_single()
        check_ids = self.record_all_required_checks()
        functional_check = self.record_functional_check()
        self.run_cli("record-impl-result", "demo-package", "--state", "done", "--summary", "implemented", "--acceptance", "S-001 implemented", "--acceptance", "S-002 validated", "--check", check_ids[0], "--check", check_ids[1], "--functional-check", functional_check)
        before = (self.package_dir() / "review.md").read_text(encoding="utf-8")
        self.assertEqual(self.run_cli("record-review", "demo-package", "--state", "approved_with_notes", "--summary", "approved", "--evidence", "unit tests pass", "--note", "keep an eye on edge", "--json"), 0)
        data = self.task_json()
        self.assertEqual(data["review_result"]["state"], "APPROVED_WITH_NOTES")
        self.assertEqual(data["review_result"]["evidence"], ["unit tests pass"])
        self.assertEqual(data["review_result"]["notes"], ["keep an eye on edge"])
        self.assertEqual(data["state"], "reviewed")
        self.assertEqual(data["next_action"]["skill"], "none")
        review_md = (self.package_dir() / "review.md").read_text(encoding="utf-8")
        self.assertIn(before, review_md)
        self.assertIn("## 2026-04-25T00:00:00Z approved_with_notes", review_md)
        self.assertIn("- Evidence: unit tests pass", review_md)
        self.assertIn("- Note: keep an eye on edge", review_md)

    def test_record_review_routes_rework_and_drift(self):
        self.finalize_single()
        self.assertEqual(self.run_cli("record-review", "demo-package", "--state", "needs_rework", "--summary", "bug remains"), 0)
        data = self.task_json()
        self.assertEqual(data["state"], "doing")
        self.assertEqual(data["next_action"]["skill"], "impl")
        self.assertEqual(self.run_cli("record-review", "demo-package", "--state", "brainstorm_drift", "--summary", "scope wrong"), 0)
        data = self.task_json()
        self.assertEqual(data["state"], "draft")
        self.assertEqual(data["next_action"]["skill"], "brainstorm")
        self.assertEqual(self.run_cli("record-review", "demo-package", "--state", "done", "--summary", "bad"), 1)

    def test_archived_state_routes_to_none_and_doctor_skips(self):
        self.finalize_single()
        self.assertEqual(self.run_cli("set-status", "demo-package", "--state", "archived", "--actor", "user", "--note", "no longer needed"), 0)
        data = self.task_json()
        self.assertEqual(data["state"], "archived")
        self.assertEqual(data["next_action"]["skill"], "none")
        self.assertIn("归档", data["next_action"]["reason"])
        result = arbor.doctor(self.root, NOW)
        self.assertTrue(result["ok"])
        self.assertEqual(result["packages"]["count"], 0)
        self.assertEqual(result["packages"]["archived_count"], 1)

    def test_add_amendment_routes_to_impl(self):
        self.finalize_single()
        self.assertEqual(
            self.run_cli(
                "add-amendment",
                "demo-package",
                "--id",
                "AMD-001",
                "--title",
                "Correct refund behavior",
                "--wrong",
                "refund not described",
                "--correct",
                "full refund revokes entitlement",
                "--affects",
                "refund flow",
                "--actor",
                "brainstorm",
            ),
            0,
        )
        data = self.task_json()
        self.assertEqual(data["prd"]["amendments"][0]["id"], "AMD-001")
        self.assertEqual(data["prd"]["status"], "ready")
        self.assertEqual(data["current_phase"], "brainstorm")
        self.assertEqual(data["next_action"]["skill"], "impl")
        self.assertEqual(data["phase_history"][-1]["to"], "amendment:AMD-001")
        self.assertEqual(self.run_cli("validate", "demo-package"), 0)

    def test_add_context_is_atomic_and_ordered(self):
        self.finalize_single()
        self.assertEqual(self.run_cli("add-context", "demo-package", "--type", "impl", "--entry-json", '{"kind":"note","summary":"first"}', "--entry-json", '{"kind":"decision","summary":"second"}'), 0)
        lines = (self.package_dir() / "context" / "impl.jsonl").read_text(encoding="utf-8").strip().splitlines()
        self.assertEqual([json.loads(line)["summary"] for line in lines], ["first", "second"])
        before = (self.package_dir() / "context" / "review.jsonl").read_text(encoding="utf-8")
        self.assertEqual(self.run_cli("add-context", "demo-package", "--type", "review", "--entry-json", '{"kind":"bad","summary":"bad"}'), 1)
        self.assertEqual((self.package_dir() / "context" / "review.jsonl").read_text(encoding="utf-8"), before)

    def test_repair_context_jsonl_removes_obsolete_task_id_and_adds_schema_fields(self):
        self.finalize_single()
        path = self.package_dir() / "context" / "review.jsonl"
        path.write_text('{"summary":"review note","task_id":"old"}\n', encoding="utf-8")
        self.assertEqual(self.run_cli("validate", "demo-package"), 1)
        self.assertEqual(self.run_cli("repair-context", "demo-package", "--type", "review", "--json"), 0)
        entry = json.loads(path.read_text(encoding="utf-8").strip())
        self.assertEqual(entry["kind"], "note")
        self.assertEqual(entry["actor"], "arbor")
        self.assertEqual(entry["at"], NOW)
        self.assertNotIn("task_id", entry)
        errors = arbor.validate_package(self.root, "demo-package")
        self.assertFalse([error for error in errors if "context/review.jsonl" in error])

    def test_module_summary_has_stable_non_line_locators(self):
        self.finalize_single()
        self.record_all_required_checks()
        self.run_cli("mark-slice", "demo-package", "--id", "S-001", "--status", "done", "--acceptance", "S-001: baseline verified")
        check_ids = [item["id"] for item in self.task_json()["checks"]]
        functional_check = self.record_functional_check()
        self.run_cli("record-impl-result", "demo-package", "--state", "done", "--summary", "implemented", "--acceptance", "S-001 implemented", "--acceptance", "S-002 validated", "--check", check_ids[0], "--check", check_ids[1], "--functional-check", functional_check)
        packet = arbor.module_summary(self.root, "demo-package", NOW)
        self.assertEqual(packet["kind"], "module-summary")
        self.assertEqual(packet["schema_version"], "sdd-module-summary-v1")
        self.assertEqual(packet["package"], "demo-package")
        self.assertEqual(packet["package_kind"], "single")
        self.assertNotIn("parent", packet)
        self.assertNotIn("children", packet)
        self.assertEqual(packet["related_packages"], [])
        self.assertEqual([item["id"] for item in packet["slices"]], ["S-001", "S-002"])
        self.assertEqual(packet["slices"][0]["status"], "done")
        self.assertIn("src/demo.py", packet["important_files"])
        self.assertIn("app/demo/page.tsx", packet["important_files"])
        self.assertIn("tests/test_demo.py::test_baseline", packet["tests"])
        self.assertTrue(any(item.endswith("-c pass") for item in packet["tests"]))
        self.assertEqual(packet["contracts"][0]["completion_marker"], "baseline behavior created and verified")
        self.assertEqual(packet["implementation"]["state"], "DONE")
        self.assertNotIn(":12", json.dumps(packet))
        self.assertNotIn(":L8", json.dumps(packet))
        self.assertEqual(self.run_cli("module-summary", "demo-package", "--json"), 0)

    def test_doctor_reports_next_action(self):
        self.finalize_single()
        result = arbor.doctor(self.root, timestamp=NOW)
        self.assertTrue(result["ok"])
        self.assertNotIn("wiki", result)
        self.assertEqual(result["summary"]["error_count"], 0)
        self.assertEqual(result["next_action"]["skill"], "impl")
        self.assertEqual(result["next_action"]["package"], "demo-package")
        self.assertEqual(self.run_cli("doctor", "--json"), 0)

    def test_doctor_fails_on_package_validation_error(self):
        self.run_cli("create", "demo-package")
        data = self.task_json()
        data["state"] = "bad"
        (self.package_dir() / "task.json").write_text(json.dumps(data), encoding="utf-8")
        result = arbor.doctor(self.root, timestamp=NOW)
        self.assertFalse(result["ok"])
        self.assertIn("demo-package", result["packages"]["errors"])
        self.assertEqual(result["next_action"]["skill"], "doctor")
        self.assertEqual(self.run_cli("doctor", "--json"), 1)

    def test_set_execution_and_pr_record_package_metadata(self):
        self.run_cli("create", "demo-package")
        self.assertEqual(self.run_cli("set-execution", "demo-package", "--status", "in_progress", "--base-branch", "main", "--branch", "arbor/demo-package", "--worktree", "/tmp/demo-package", "--worktree-created-by", "manual"), 0)
        self.assertEqual(self.run_cli("set-pr", "demo-package", "--url", "https://example.com/pr/1", "--number", "1", "--state", "open"), 0)
        execution = self.task_json()["execution"]
        self.assertEqual(execution["branch"]["name"], "arbor/demo-package")
        self.assertEqual(execution["worktree"]["created_by"], "manual")
        self.assertEqual(execution["pr"]["number"], 1)
        self.assertEqual(execution["pr"]["state"], "open")
        self.assertEqual(execution["status"], "pr_open")
        self.assertEqual(self.run_cli("validate", "demo-package"), 0)

    def test_mark_slice_creates_and_updates_slice_progress(self):
        self.finalize_single()
        # After finalize, slices are pre-registered with status "pending"
        data = self.task_json()
        self.assertEqual(len(data["slices"]), 2)
        self.assertEqual(data["slices"][0]["id"], "S-001")
        self.assertEqual(data["slices"][0]["status"], "pending")
        self.assertEqual(data["slices"][1]["id"], "S-002")
        self.assertEqual(data["slices"][1]["status"], "pending")
        # mark-slice updates existing slice status
        self.assertEqual(self.run_cli("mark-slice", "demo-package", "--id", "S-001", "--status", "in_progress", "--note", "API done, page pending", "--json"), 0)
        data = self.task_json()
        self.assertEqual(len(data["slices"]), 2)
        self.assertEqual(data["slices"][0]["id"], "S-001")
        self.assertEqual(data["slices"][0]["status"], "in_progress")
        self.assertEqual(data["slices"][0]["note"], "API done, page pending")
        # mark-slice done is gated: record check evidence first, then settle with acceptance
        self.record_all_required_checks()
        self.assertEqual(self.run_cli("mark-slice", "demo-package", "--id", "S-001", "--status", "done", "--acceptance", "S-001: baseline verified", "--json"), 0)
        data = self.task_json()
        self.assertEqual(len(data["slices"]), 2)
        self.assertEqual(data["slices"][0]["status"], "done")
        self.assertEqual(data["slices"][0]["acceptance"], ["S-001: baseline verified"])
        self.assertTrue(data["slices"][0]["checks"])
        self.assertEqual(self.run_cli("mark-slice", "demo-package", "--id", "S-002", "--status", "done", "--acceptance", "S-002: validation passes", "--json"), 0)
        data = self.task_json()
        self.assertEqual(len(data["slices"]), 2)
        self.assertEqual([s["id"] for s in data["slices"]], ["S-001", "S-002"])
        self.assertEqual(data["slices"][1]["status"], "done")
        self.assertEqual(self.run_cli("validate", "demo-package"), 0)

    def test_mark_slice_rejects_invalid_id(self):
        self.finalize_single()
        self.assertEqual(self.run_cli("mark-slice", "demo-package", "--id", "X-001", "--status", "done"), 1)

    def test_mark_slice_rejects_slice_not_defined_in_prd_without_mutating(self):
        self.finalize_single()
        before = self.task_json()
        self.assertEqual(self.run_cli("mark-slice", "demo-package", "--id", "S-999", "--status", "done"), 1)
        after = self.task_json()
        self.assertEqual(before.get("slices"), after.get("slices"))

    def test_validate_rejects_slice_progress_not_defined_in_prd(self):
        self.finalize_single()
        data = self.task_json()
        data["slices"] = [{"id": "S-999", "status": "done", "note": "bad", "updated_at": NOW}]
        (self.package_dir() / "task.json").write_text(json.dumps(data), encoding="utf-8")
        errors = arbor.validate_package(self.root, "demo-package")
        self.assertTrue(any("S-999" in error and "PRD ## Slices" in error for error in errors))

    def test_show_includes_slices(self):
        self.finalize_single()
        self.record_all_required_checks()
        self.run_cli("mark-slice", "demo-package", "--id", "S-001", "--status", "done", "--acceptance", "S-001: baseline verified")
        shown = arbor.show_package(self.root, "demo-package")
        self.assertIsNotNone(shown.get("slices"))
        self.assertEqual(shown["slices"][0]["id"], "S-001")
        self.assertEqual(shown["slices"][0]["status"], "done")

    def test_list_and_show_json_are_parseable(self):
        self.run_cli("create", "demo-package")
        items = arbor.list_packages(self.root)
        self.assertEqual(items[0]["name"], "demo-package")
        self.assertIn("execution_status", items[0])
        self.assertIn("package_sizing", items[0])
        shown = arbor.show_package(self.root, "demo-package")
        self.assertEqual(shown["name"], "demo-package")
        self.assertIn("execution", shown)
        self.assertIn("package_sizing", shown)
        self.assertNotIn("children", shown)
        self.assertTrue(shown["validation"]["ok"])

    def test_legacy_source_type_records_legacy_path(self):
        self.run_cli("create", "legacy-demo", "--source-type", "legacy-brainstorm")
        data = self.task_json("legacy-demo")
        self.assertEqual(data["prd"]["legacy_source"], ".arbor/brainstorms/legacy-demo.md")

    def test_arbor_guard_blocks_direct_control_state_and_context_jsonl(self):
        control = arbor_guard.evaluate({"tool_name": "Write", "tool_input": {"file_path": str(self.root / ".arbor" / "tasks" / "demo-package" / "task.json")}})
        self.assertEqual(control["decision"], "block")
        self.assertIn("helpers", control["reason"])
        context = arbor_guard.evaluate({"tool_name": "Edit", "tool_input": {"file_path": str(self.root / ".arbor" / "tasks" / "demo-package" / "context" / "impl.jsonl")}})
        self.assertEqual(context["decision"], "block")
        self.assertIn("add-context", context["reason"])

    def test_arbor_guard_blocks_direct_checks_dir_edits(self):
        checks = arbor_guard.evaluate({"tool_name": "Write", "tool_input": {"file_path": str(self.root / ".arbor" / "tasks" / "demo-package" / "checks" / "chk_001.stdout")}})
        self.assertEqual(checks["decision"], "block")
        self.assertIn("run-check", checks["reason"])

    def test_arbor_guard_blocks_destructive_bash_and_allows_safe_tools(self):
        blocked = arbor_guard.evaluate({"tool_name": "Bash", "tool_input": {"command": "git reset --hard HEAD"}})
        self.assertEqual(blocked["decision"], "block")
        self.assertIn("narrower safer", blocked["reason"])
        for discard in ("git checkout -- .", "git checkout .", "git restore .", "git restore -- ."):
            verdict = arbor_guard.evaluate({"tool_name": "Bash", "tool_input": {"command": discard}})
            self.assertEqual(verdict["decision"], "block", discard)
        for clean in ("git clean -fd", "git clean -df", "git clean -fdx", "git clean -xdf", "git clean -ffdx", "git clean -f -d"):
            verdict = arbor_guard.evaluate({"tool_name": "Bash", "tool_input": {"command": clean}})
            self.assertEqual(verdict["decision"], "block", clean)
        # path-scoped checkout/restore and dry-run clean stay allowed; the guard only blocks mass discard
        for scoped in ("git checkout feature-branch", "git checkout ./docs/readme.md", "git restore --staged file.py", "git clean -nfd", "git clean --dry-run -fd"):
            verdict = arbor_guard.evaluate({"tool_name": "Bash", "tool_input": {"command": scoped}})
            self.assertEqual(verdict["decision"], "allow", scoped)
        allowed = arbor_guard.evaluate({"tool_name": "Read", "tool_input": {"file_path": str(self.root / "README.md")}})
        self.assertEqual(allowed["decision"], "allow")

    def test_arbor_guard_hook_contract_uses_exit_code_and_stderr(self):
        blocked = self.run_hook({"tool_name": "Bash", "tool_input": {"command": "git reset --hard HEAD"}})
        self.assertEqual(blocked.returncode, 2)
        self.assertEqual(blocked.stdout, "")
        self.assertIn("narrower safer", blocked.stderr)

        allowed = self.run_hook({"tool_name": "Bash", "tool_input": {"command": "git status --short"}})
        self.assertEqual(allowed.returncode, 0)
        self.assertEqual(allowed.stdout, "")
        self.assertEqual(allowed.stderr, "")


    def _init_git_repo(self, commit_all=True):
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        if commit_all:
            subprocess.run(["git", "add", "-A"], cwd=self.root, check=True)
        subprocess.run(
            ["git", "-c", "user.email=test@test", "-c", "user.name=test", "commit", "--allow-empty", "-q", "-m", "init"],
            cwd=self.root,
            check=True,
        )
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=self.root, stdout=subprocess.PIPE, text=True, check=True
        ).stdout.strip()

    def test_set_status_doing_records_base_ref_and_never_overwrites(self):
        self.finalize_single()
        head = self._init_git_repo()
        self.assertEqual(self.run_cli("set-status", "demo-package", "--state", "doing", "--actor", "impl", "--note", "start"), 0)
        data = self.task_json()
        self.assertEqual(data["execution"]["base_ref"], head)
        self.assertNotIn("base_ref_dirty", data["execution"])
        self.assertEqual(self.run_cli("validate", "demo-package"), 0)
        # HEAD moves on, package re-enters doing (e.g. rework): anchor must not move.
        subprocess.run(
            ["git", "-c", "user.email=test@test", "-c", "user.name=test", "commit", "--allow-empty", "-q", "-m", "second"],
            cwd=self.root,
            check=True,
        )
        self.assertEqual(self.run_cli("set-status", "demo-package", "--state", "doing", "--actor", "impl", "--note", "rework"), 0)
        self.assertEqual(self.task_json()["execution"]["base_ref"], head)

    def test_set_status_doing_flags_dirty_worktree(self):
        self.finalize_single()
        head = self._init_git_repo()
        (self.root / "uncommitted.txt").write_text("dirty", encoding="utf-8")
        self.assertEqual(self.run_cli("set-status", "demo-package", "--state", "doing", "--actor", "impl", "--note", "start"), 0)
        data = self.task_json()
        self.assertEqual(data["execution"]["base_ref"], head)
        self.assertTrue(data["execution"]["base_ref_dirty"])
        self.assertEqual(self.run_cli("validate", "demo-package"), 0)

    def test_set_status_doing_without_git_degrades_to_null_base_ref(self):
        self.finalize_single()
        self.assertEqual(self.run_cli("set-status", "demo-package", "--state", "doing", "--actor", "impl", "--note", "start"), 0)
        data = self.task_json()
        self.assertIsNone(data["execution"]["base_ref"])
        self.assertNotIn("base_ref_dirty", data["execution"])
        self.assertEqual(self.run_cli("validate", "demo-package"), 0)


    def test_mark_slice_done_gate_rejects_missing_check_evidence_with_outlet(self):
        self.finalize_single()
        result = self.run_bin("mark-slice", "demo-package", "--id", "S-001", "--status", "done", "--acceptance", "S-001: baseline verified")
        self.assertEqual(result.returncode, 1)
        self.assertIn("req_S001_001", result.stderr)
        self.assertIn("run-check", result.stderr)
        self.assertIn("in_progress", result.stderr)
        # gate failure must not mutate slice progress
        self.assertEqual(self.task_json()["slices"][0]["status"], "pending")
        # gate auto-derives required checks as a side effect
        self.assertTrue(self.task_json()["required_checks"])

    def test_mark_slice_done_gate_rejects_missing_acceptance_with_format_hint(self):
        self.finalize_single()
        self.record_all_required_checks()
        result = self.run_bin("mark-slice", "demo-package", "--id", "S-001", "--status", "done")
        self.assertEqual(result.returncode, 1)
        self.assertIn("S-001", result.stderr)
        self.assertIn("--acceptance", result.stderr)
        self.assertEqual(self.task_json()["slices"][0]["status"], "pending")

    def test_mark_slice_done_gate_rejects_foreign_marker_reference(self):
        self.finalize_single()
        self.record_all_required_checks()
        result = self.run_bin("mark-slice", "demo-package", "--id", "S-001", "--status", "done", "--acceptance", "S-002: wrong slice evidence")
        self.assertEqual(result.returncode, 1)
        self.assertIn("S-002", result.stderr)
        # prose mention of another slice is fine when the item names an own marker
        self.assertEqual(
            self.run_cli("mark-slice", "demo-package", "--id", "S-001", "--status", "done", "--acceptance", "S-001: baseline verified, 接口契约与 S-002 对齐"),
            0,
        )

    def test_mark_slice_in_progress_is_not_gated(self):
        self.finalize_single()
        self.assertEqual(self.run_cli("mark-slice", "demo-package", "--id", "S-001", "--status", "in_progress", "--note", "halfway"), 0)
        self.assertEqual(self.task_json()["slices"][0]["status"], "in_progress")

    def test_mark_slice_done_records_evidence_and_passes_validation(self):
        self.finalize_single()
        self.record_all_required_checks()
        self.assertEqual(self.run_cli("mark-slice", "demo-package", "--id", "S-001", "--status", "done", "--acceptance", "S-001: baseline verified"), 0)
        entry = self.task_json()["slices"][0]
        self.assertEqual(entry["status"], "done")
        self.assertEqual(entry["acceptance"], ["S-001: baseline verified"])
        self.assertTrue(entry["checks"])
        self.assertTrue(all(check_id.startswith("chk_") for check_id in entry["checks"]))
        self.assertEqual(self.run_cli("validate", "demo-package"), 0)

    def test_mark_slice_rollback_clears_done_evidence(self):
        self.finalize_single()
        self.record_all_required_checks()
        self.assertEqual(self.run_cli("mark-slice", "demo-package", "--id", "S-001", "--status", "done", "--acceptance", "S-001: baseline verified"), 0)
        entry = next(item for item in self.task_json()["slices"] if item["id"] == "S-001")
        self.assertIn("acceptance", entry)
        self.assertIn("checks", entry)
        self.assertEqual(self.run_cli("mark-slice", "demo-package", "--id", "S-001", "--status", "in_progress", "--note", "rework"), 0)
        entry = next(item for item in self.task_json()["slices"] if item["id"] == "S-001")
        self.assertEqual(entry["status"], "in_progress")
        self.assertNotIn("acceptance", entry)
        self.assertNotIn("checks", entry)
        self.assertNotIn("concerns", entry)

    def test_run_check_double_dash_works_via_bin_wrapper(self):
        """Regression: main() must normalize argv so `run-check ... -- cmd` works outside tests."""
        self.finalize_single()
        self.assertEqual(self.run_cli("derive-required-checks", "demo-package"), 0)
        result = self.run_bin("run-check", "demo-package", "--required-check", "req_S001_001", "--", sys.executable, "-c", "pass")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("passed", result.stdout)


    def _settle_all_slices(self, name="demo-package"):
        self.record_all_required_checks(name)
        self.assertEqual(self.run_cli("mark-slice", name, "--id", "S-001", "--status", "done", "--acceptance", "S-001: baseline verified"), 0)
        self.assertEqual(self.run_cli("mark-slice", name, "--id", "S-002", "--status", "done", "--acceptance", "S-002: validation passes"), 0)

    def test_record_impl_result_thin_summary_aggregates_slice_evidence(self):
        self.finalize_single()
        self._settle_all_slices()
        functional_check = self.record_functional_check()
        self.assertEqual(self.run_cli("record-impl-result", "demo-package", "--state", "done", "--summary", "implemented via per-slice gate", "--functional-check", functional_check), 0)
        data = self.task_json()
        result = data["impl_result"]
        self.assertEqual(result["state"], "DONE")
        self.assertEqual(result["acceptance"], ["S-001: baseline verified", "S-002: validation passes"])
        self.assertTrue(result["checks"])
        self.assertEqual(sorted(result["acceptance_coverage"].keys()), ["S-001", "S-002"])
        self.assertEqual(data["state"], "done")
        self.assertEqual(data["next_action"]["skill"], "review")
        self.assertEqual(self.run_cli("validate", "demo-package"), 0)

    def test_record_impl_result_thin_summary_rejects_unsettled_slices(self):
        self.finalize_single()
        self.record_all_required_checks()
        self.assertEqual(self.run_cli("mark-slice", "demo-package", "--id", "S-001", "--status", "done", "--acceptance", "S-001: baseline verified"), 0)
        result = self.run_bin("record-impl-result", "demo-package", "--state", "done", "--summary", "partial")
        self.assertEqual(result.returncode, 1)
        self.assertIn("S-002", result.stderr)
        self.assertIn("mark-slice", result.stderr)
        self.assertIsNone(self.task_json()["impl_result"])

    def test_record_impl_result_manual_path_still_works_without_slice_settlement(self):
        """Legacy packages without per-slice evidence keep the explicit --acceptance/--check path."""
        self.finalize_single()
        check_ids = self.record_all_required_checks()
        functional_check = self.record_functional_check()
        code = self.run_cli(
            "record-impl-result", "demo-package", "--state", "done", "--summary", "manual evidence",
            "--acceptance", "S-001 implemented", "--acceptance", "S-002 validated",
            "--check", check_ids[0], "--check", check_ids[1], "--functional-check", functional_check,
        )
        self.assertEqual(code, 0)
        self.assertEqual(self.task_json()["impl_result"]["state"], "DONE")

    def test_record_impl_result_requires_functional_check(self):
        self.finalize_single()
        self._settle_all_slices()
        missing = self.run_bin("record-impl-result", "demo-package", "--state", "done", "--summary", "no smoke")
        self.assertEqual(missing.returncode, 1)
        self.assertIn("--functional-check", missing.stderr)
        failed_functional = self.record_functional_check(status="failed")
        failed = self.run_bin("record-impl-result", "demo-package", "--state", "done", "--summary", "failed smoke", "--functional-check", failed_functional)
        self.assertEqual(failed.returncode, 1)
        self.assertIn("Functional", failed.stderr)
        passed_functional = self.record_functional_check(status="passed")
        self.assertEqual(self.run_cli("record-impl-result", "demo-package", "--state", "done", "--summary", "smoke passed", "--functional-check", passed_functional), 0)

    def test_done_with_concerns_requires_concern_for_incomplete_checks(self):
        self.finalize_single()
        self._settle_with_blocked_check()
        self.assertEqual(self.run_cli("mark-slice", "demo-package", "--id", "S-002", "--status", "done", "--acceptance", "S-002: validation passes"), 0)
        functional_check = self.record_functional_check()
        data = self.task_json()
        result = self.run_bin(
            "record-impl-result",
            "demo-package",
            "--state",
            "done_with_concerns",
            "--summary",
            "explicit evidence but no concern",
            "--acceptance",
            "S-001: baseline verified",
            "--acceptance",
            "S-002: validation passes",
            "--check",
            data["slices"][0]["checks"][0],
            "--check",
            data["slices"][1]["checks"][0],
            "--functional-check",
            functional_check,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("--concern", result.stderr)

    def _settle_with_blocked_check(self, reason="sandbox 无法启动 validation 服务"):
        """Settle S-001 with passed evidence and S-002 via a blocked check concern."""
        self.assertEqual(self.run_cli("derive-required-checks", "demo-package"), 0)
        required = self.task_json()["required_checks"]
        s1_req = next(item["id"] for item in required if item["slice"] == "S-001")
        s2_req = next(item["id"] for item in required if item["slice"] == "S-002")
        self.assertEqual(self.run_cli("run-check", "demo-package", "--required-check", s1_req, "--", sys.executable, "-c", "pass"), 0)
        self.assertEqual(self.run_cli("record-check", "demo-package", "--required-check", s2_req, "--status", "blocked", "--reason", reason, "--evidence", "启动尝试输出: connection refused"), 0)
        self.assertEqual(self.run_cli("mark-slice", "demo-package", "--id", "S-001", "--status", "done", "--acceptance", "S-001: baseline verified"), 0)
        return s2_req

    def test_mark_slice_done_settles_blocked_check_as_concern(self):
        self.finalize_single()
        self.assertEqual(self.run_cli("derive-required-checks", "demo-package"), 0)
        required = self.task_json()["required_checks"]
        s2_req = next(item["id"] for item in required if item["slice"] == "S-002")
        # record-check itself refuses blocked without a concrete reason
        no_reason = self.run_bin("record-check", "demo-package", "--required-check", s2_req, "--status", "blocked", "--evidence", "some output")
        self.assertEqual(no_reason.returncode, 1)
        self.assertIn("--reason", no_reason.stderr)
        # gate rejection names the blocked outlet
        rejected = self.run_bin("mark-slice", "demo-package", "--id", "S-002", "--status", "done", "--acceptance", "S-002: validation passes")
        self.assertEqual(rejected.returncode, 1)
        self.assertIn("--reason", rejected.stderr)
        # blocked WITH reason settles the slice and lands as a slice-level concern
        self.assertEqual(self.run_cli("record-check", "demo-package", "--required-check", s2_req, "--status", "blocked", "--reason", "外部服务不可达", "--evidence", "curl: connection refused"), 0)
        self.assertEqual(self.run_cli("mark-slice", "demo-package", "--id", "S-002", "--status", "done", "--acceptance", "S-002: validation passes"), 0)
        entry = next(item for item in self.task_json()["slices"] if item["id"] == "S-002")
        self.assertEqual(entry["status"], "done")
        self.assertEqual(len(entry["concerns"]), 1)
        self.assertIn(s2_req, entry["concerns"][0])
        self.assertIn("外部服务不可达", entry["concerns"][0])
        self.assertEqual(self.run_cli("validate", "demo-package"), 0)
        # re-settling after a passing run clears the stale concern
        self.assertEqual(self.run_cli("run-check", "demo-package", "--required-check", s2_req, "--", sys.executable, "-c", "pass"), 0)
        self.assertEqual(self.run_cli("mark-slice", "demo-package", "--id", "S-002", "--status", "done", "--acceptance", "S-002: validation passes"), 0)
        entry = next(item for item in self.task_json()["slices"] if item["id"] == "S-002")
        self.assertNotIn("concerns", entry)

    def test_record_impl_result_thin_summary_rejects_done_with_slice_concerns(self):
        self.finalize_single()
        self._settle_with_blocked_check()
        self.assertEqual(self.run_cli("mark-slice", "demo-package", "--id", "S-002", "--status", "done", "--acceptance", "S-002: validation passes"), 0)
        result = self.run_bin("record-impl-result", "demo-package", "--state", "done", "--summary", "claiming clean done")
        self.assertEqual(result.returncode, 1)
        self.assertIn("done_with_concerns", result.stderr)
        self.assertIsNone(self.task_json()["impl_result"])

    def test_record_impl_result_thin_summary_aggregates_slice_concerns(self):
        self.finalize_single()
        s2_req = self._settle_with_blocked_check()
        self.assertEqual(self.run_cli("mark-slice", "demo-package", "--id", "S-002", "--status", "done", "--acceptance", "S-002: validation passes"), 0)
        functional_check = self.record_functional_check()
        self.assertEqual(self.run_cli("record-impl-result", "demo-package", "--state", "done_with_concerns", "--summary", "validation blocked by env", "--functional-check", functional_check), 0)
        data = self.task_json()
        result = data["impl_result"]
        self.assertEqual(result["state"], "DONE_WITH_CONCERNS")
        self.assertEqual(result["acceptance"], ["S-001: baseline verified", "S-002: validation passes"])
        self.assertEqual(len(result["concerns"]), 1)
        self.assertIn(s2_req, result["concerns"][0])
        self.assertEqual(result["incomplete_required_checks"][0]["id"], s2_req)
        self.assertEqual(data["state"], "done")
        self.assertEqual(data["next_action"]["skill"], "review")
        self.assertEqual(self.run_cli("validate", "demo-package"), 0)


    def test_impl_packet_slice_aggregates_execution_context(self):
        self.finalize_single()
        packet = arbor.impl_packet(self.root, "demo-package", "S-001", NOW)
        self.assertEqual(packet["kind"], "impl-packet")
        self.assertEqual(packet["slice"]["id"], "S-001")
        self.assertEqual(packet["slice"]["task_file"], "slices/S-001.md")
        self.assertIn("## Acceptance", packet["slice"]["task_content"])
        self.assertEqual(packet["slice"]["markers"], ["S-001"])
        self.assertTrue(all(item["slice"] == "S-001" for item in packet["required_checks"]))
        self.assertTrue(packet["required_checks"])
        self.assertIn("prd.md#Technical Framing", packet["read_next"])
        self.assertIn("last_done_slice", packet["prior"])
        # auto-derive persisted required checks as a side effect
        self.assertTrue(self.task_json()["required_checks"])

    def test_impl_packet_entry_lists_slice_statuses_and_next_slice(self):
        self.finalize_single()
        self.record_all_required_checks()
        self.run_cli("mark-slice", "demo-package", "--id", "S-001", "--status", "done", "--acceptance", "S-001: baseline verified")
        packet = arbor.impl_packet(self.root, "demo-package", None, NOW)
        self.assertEqual([row["id"] for row in packet["slices"]], ["S-001", "S-002"])
        self.assertEqual(packet["slices"][0]["status"], "done")
        self.assertEqual(packet["next_slice"], "S-002")
        self.assertIn("base_ref", packet)
        self.assertEqual(self.run_cli("impl-packet", "demo-package", "--json"), 0)
        self.assertEqual(self.run_cli("impl-packet", "demo-package", "--slice", "S-002", "--json"), 0)

    def test_impl_packet_rejects_missing_task_file_and_unknown_slice(self):
        self.finalize_single()
        unknown = self.run_bin("impl-packet", "demo-package", "--slice", "S-999")
        self.assertEqual(unknown.returncode, 1)
        self.assertIn("S-999", unknown.stderr)
        (self.package_dir() / "slices" / "S-001.md").unlink()
        result = self.run_bin("impl-packet", "demo-package", "--slice", "S-001")
        self.assertEqual(result.returncode, 1)
        self.assertIn("slices/S-001.md", result.stderr)

    def test_impl_packet_rejects_prd_without_slices(self):
        self.run_cli("create", "demo-package")
        (self.package_dir() / "prd.md").write_text("# no slices here\n", encoding="utf-8")
        result = self.run_bin("impl-packet", "demo-package")
        self.assertEqual(result.returncode, 1)
        self.assertIn("Slices", result.stderr)


    def test_arbor_guard_freezes_prd_during_impl_and_review(self):
        self.finalize_single()
        prd_path = str(self.package_dir() / "prd.md")
        payload = {"tool_name": "Edit", "tool_input": {"file_path": prd_path}}
        # ready: editable (e.g. brainstorm refinement before impl)
        self.assertEqual(arbor_guard.evaluate(payload)["decision"], "allow")
        self.run_cli("set-status", "demo-package", "--state", "doing", "--actor", "impl", "--note", "start")
        blocked = arbor_guard.evaluate(payload)
        self.assertEqual(blocked["decision"], "block")
        self.assertIn("add-amendment", blocked["reason"])
        self.assertIn("needs_context", blocked["reason"])
        # needs_context keeps state=doing but routes to brainstorm: PRD must unfreeze,
        # otherwise brainstorm cannot update its own artifact during the interview.
        self.run_cli("record-impl-result", "demo-package", "--state", "needs_context", "--summary", "missing framing decision")
        self.assertEqual(self.task_json()["next_action"]["skill"], "brainstorm")
        self.assertEqual(arbor_guard.evaluate(payload)["decision"], "allow")
        # impl resumes: frozen again
        self.run_cli("set-status", "demo-package", "--state", "doing", "--actor", "impl", "--note", "resume")
        self.assertEqual(arbor_guard.evaluate(payload)["decision"], "block")
        self.run_cli("set-status", "demo-package", "--state", "done", "--actor", "impl", "--note", "impl done")
        self.assertEqual(arbor_guard.evaluate(payload)["decision"], "block")
        self.run_cli("set-status", "demo-package", "--state", "reviewed", "--actor", "review", "--note", "approved")
        self.assertEqual(arbor_guard.evaluate(payload)["decision"], "allow")

    def test_arbor_guard_prd_freeze_fails_open_without_task_json(self):
        pkg = self.root / ".arbor" / "tasks" / "orphan-pkg"
        pkg.mkdir(parents=True)
        (pkg / "prd.md").write_text("# orphan\n", encoding="utf-8")
        payload = {"tool_name": "Write", "tool_input": {"file_path": str(pkg / "prd.md")}}
        self.assertEqual(arbor_guard.evaluate(payload)["decision"], "allow")
        # corrupted task.json must also fail open
        (pkg / "task.json").write_text("{not json", encoding="utf-8")
        self.assertEqual(arbor_guard.evaluate(payload)["decision"], "allow")


    def test_finalize_materializes_slice_defs(self):
        self.finalize_single()
        materialized = self.task_json()["prd"]["slices"]
        self.assertEqual([entry["id"] for entry in materialized], ["S-001", "S-002"])
        self.assertEqual(materialized[0]["title"], "First slice — create baseline behavior")
        self.assertEqual(materialized[0]["completion_markers"], ["baseline behavior created and verified"])
        self.assertEqual(self.run_cli("validate", "demo-package"), 0)

    def test_set_status_doing_recompiles_slice_defs_at_freeze_boundary(self):
        self.finalize_single()
        # ready: PRD editable; brainstorm appends a slice + its task file
        prd_path = self.package_dir() / "prd.md"
        prd_path.write_text(prd_path.read_text(encoding="utf-8") + """
### S-003: Added during ready

- 完成标志：extra behavior verified
""", encoding="utf-8")
        (self.package_dir() / "slices" / "S-003.md").write_text(
            "# S-003: Added during ready\n\n## Acceptance\n\nGiven:\n- x\n\nWhen:\n- y\n\nThen:\n- z\n\n## Verification\n\n- [test] run extra tests\n",
            encoding="utf-8",
        )
        self.assertEqual(self.run_cli("set-status", "demo-package", "--state", "doing", "--actor", "impl", "--note", "start"), 0)
        materialized = self.task_json()["prd"]["slices"]
        self.assertEqual([entry["id"] for entry in materialized], ["S-001", "S-002", "S-003"])

    def test_runtime_reads_materialized_defs_not_prd(self):
        """Parse-once: after entering doing, runtime commands never re-parse prd.md."""
        self.finalize_single()
        self.assertEqual(self.run_cli("set-status", "demo-package", "--state", "doing", "--actor", "impl", "--note", "start"), 0)
        # simulate prd.md becoming unreadable as markdown (runtime must not care)
        (self.package_dir() / "prd.md").write_text("# prose only, no slices section\n", encoding="utf-8")
        packet = arbor.impl_packet(self.root, "demo-package", "S-001", NOW)
        self.assertEqual(packet["slice"]["id"], "S-001")
        self.record_all_required_checks()
        self.assertEqual(self.run_cli("mark-slice", "demo-package", "--id", "S-001", "--status", "done", "--acceptance", "S-001: baseline verified"), 0)

    def test_legacy_package_lazily_migrates_slice_defs(self):
        self.finalize_single()
        data = self.task_json()
        del data["prd"]["slices"]
        (self.package_dir() / "task.json").write_text(json.dumps(data), encoding="utf-8")
        packet = arbor.impl_packet(self.root, "demo-package", None, NOW)
        self.assertEqual(packet["next_slice"], "S-001")
        self.assertEqual([entry["id"] for entry in self.task_json()["prd"]["slices"]], ["S-001", "S-002"])

    def test_finalize_rejects_untagged_verification_items(self):
        slices_dir = self.root / ".arbor" / "tasks" / "demo-package" / "slices"
        slices_dir.mkdir(parents=True, exist_ok=True)
        (slices_dir / "S-001.md").write_text(
            "# S-001: First slice\n\n## Acceptance\n\nGiven:\n- a\n\nWhen:\n- b\n\nThen:\n- c\n\n## Verification\n\n- run tests without tag\n",
            encoding="utf-8",
        )
        (slices_dir / "S-002.md").write_text(
            "# S-002: Self-check\n\n## Acceptance\n\nGiven:\n- a\n\nWhen:\n- b\n\nThen:\n- c\n\n## Verification\n\n- [manual] run validation\n",
            encoding="utf-8",
        )
        spec = {"kind": "single", "name": "demo-package", "title": "Demo package", "prd": READY_PRD}
        result = self.run_bin("finalize-brainstorm", "--input-json", json.dumps(spec))
        self.assertEqual(result.returncode, 1)
        self.assertIn("[kind]", result.stderr)
        self.assertIn("run tests without tag", result.stderr)

    def test_derive_rejects_untagged_verification_with_outlet(self):
        self.finalize_single()
        (self.package_dir() / "slices" / "S-001.md").write_text(
            "# S-001: First slice\n\n## Acceptance\n\nGiven:\n- a\n\nWhen:\n- b\n\nThen:\n- c\n\n## Verification\n\n- untagged item\n",
            encoding="utf-8",
        )
        result = self.run_bin("derive-required-checks", "demo-package")
        self.assertEqual(result.returncode, 1)
        self.assertIn("[kind]", result.stderr)
        self.assertIn("- [test]", result.stderr)


    def test_impl_closed_loop_end_to_end(self):
        """Integration: finalize → doing(base_ref) → gate reject → settle → thin summary."""
        self.finalize_single()
        head = self._init_git_repo()
        # entering doing records the diff anchor
        self.assertEqual(self.run_cli("set-status", "demo-package", "--state", "doing", "--actor", "impl", "--note", "start"), 0)
        self.assertEqual(self.task_json()["execution"]["base_ref"], head)
        # entry packet points at the first unfinished slice
        entry = arbor.impl_packet(self.root, "demo-package", None, NOW)
        self.assertEqual(entry["next_slice"], "S-001")
        self.assertEqual(entry["base_ref"], head)
        # gate rejects an unsettled slice and names the outlet
        rejected = self.run_bin("mark-slice", "demo-package", "--id", "S-001", "--status", "done", "--acceptance", "S-001: baseline verified")
        self.assertEqual(rejected.returncode, 1)
        self.assertIn("run-check", rejected.stderr)
        # settle both slices with real evidence
        self.record_all_required_checks()
        self.assertEqual(self.run_cli("mark-slice", "demo-package", "--id", "S-001", "--status", "done", "--acceptance", "S-001: baseline verified"), 0)
        self.assertEqual(self.run_cli("mark-slice", "demo-package", "--id", "S-002", "--status", "done", "--acceptance", "S-002: validation passes"), 0)
        # thin summary aggregates everything
        functional_check = self.record_functional_check()
        self.assertEqual(self.run_cli("record-impl-result", "demo-package", "--state", "done", "--summary", "closed loop e2e", "--functional-check", functional_check), 0)
        data = self.task_json()
        self.assertEqual(data["state"], "done")
        self.assertEqual(data["next_action"]["skill"], "review")
        self.assertEqual(len(data["impl_result"]["acceptance"]), 2)
        self.assertEqual(self.run_cli("validate", "demo-package"), 0)


if __name__ == "__main__":
    unittest.main()

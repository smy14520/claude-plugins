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

### S-002: Self-check — run validation

- 完成标志：validation passes
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
        self.assertEqual(self.run_cli("finalize-brainstorm", "--input-json", json.dumps(spec), "--json"), 0)

    def finalize_single_json(self, name="demo-package"):
        spec = {
            "kind": "single",
            "name": name,
            "title": "Demo package",
            "prd": READY_PRD,
            "decision": "single package with PRD-local Slices",
        }
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

    def test_sdd_arbor_bin_wrapper_runs_from_project_cwd(self):
        spec = {
            "kind": "single",
            "name": "demo-package",
            "title": "Demo package",
            "prd": READY_PRD,
        }
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
        self.assertIn("- 数据/schema：", prd_text)
        self.assertIn("- 代码锚点：", prd_text)
        self.assertIn("- 测试：", prd_text)
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
        spec = {"kind": "single", "package": "demo-package", "prd_path": ".arbor/tasks/demo-package/prd.md"}

        self.assertEqual(self.run_cli("finalize-brainstorm", "--input-json", json.dumps(spec)), 0)

        self.assertEqual((self.package_dir() / "prd.md").read_text(encoding="utf-8"), READY_PRD)
        self.assertEqual(self.task_json()["prd"]["status"], "ready")

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
            "### S-001: <有数据、有代码、有测试的 slice>\n\n"
            "- 完成标志：<一句话可验证的 done-condition>\n"
        )
        spec = {"kind": "single", "name": "demo-package", "prd": bad_prd}
        result = self.run_bin("finalize-brainstorm", "--input-json", json.dumps(spec))
        self.assertEqual(result.returncode, 1)
        self.assertIn("scaffold", result.stderr)
        self.assertFalse(self.package_dir().exists())

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
        self.run_cli("create", "demo-package")
        code = self.run_cli("set-prd-status", "demo-package", "--status", "ready", "--actor", "brainstorm", "--note", "ready")
        self.assertEqual(code, 1)
        data = self.task_json()
        self.assertEqual(data["prd"]["status"], "draft")
        self.assertEqual(data["package_sizing"]["status"], "unchecked")

    def test_record_impl_result_routes_structured_results(self):
        self.finalize_single()
        self.assertEqual(self.run_cli("record-impl-result", "demo-package", "--state", "done_with_concerns", "--summary", "implemented behavior", "--acceptance", "golden path passes", "--command", "pytest tests/test_demo.py", "--concern", "edge case needs review", "--json"), 0)
        data = self.task_json()
        self.assertEqual(data["state"], "done")
        self.assertEqual(data["impl_result"]["state"], "DONE_WITH_CONCERNS")
        self.assertEqual(data["impl_result"]["acceptance"], ["golden path passes"])
        self.assertEqual(data["impl_result"]["commands"], ["pytest tests/test_demo.py"])
        self.assertEqual(data["impl_result"]["concerns"], ["edge case needs review"])
        self.assertEqual(data["next_action"]["skill"], "review")
        self.assertEqual(data["phase_history"][-1]["phase"], "impl")
        self.assertEqual(self.run_cli("record-impl-result", "demo-package", "--state", "approved", "--summary", "bad"), 1)

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
        self.run_cli("record-impl-result", "demo-package", "--state", "done", "--summary", "implemented")
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

    def test_add_context_batch_is_atomic_and_ordered(self):
        self.finalize_single()
        self.assertEqual(self.run_cli("add-context-batch", "demo-package", "--type", "impl", "--entry-json", '{"kind":"note","summary":"first"}', "--entry-json", '{"kind":"decision","summary":"second"}'), 0)
        lines = (self.package_dir() / "context" / "impl.jsonl").read_text(encoding="utf-8").strip().splitlines()
        self.assertEqual([json.loads(line)["summary"] for line in lines], ["first", "second"])
        before = (self.package_dir() / "context" / "review.jsonl").read_text(encoding="utf-8")
        self.assertEqual(self.run_cli("add-context-batch", "demo-package", "--type", "review", "--entry-json", '{"kind":"bad","summary":"bad"}'), 1)
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
        packet = arbor.module_summary(self.root, "demo-package", NOW)
        self.assertEqual(packet["kind"], "module-summary")
        self.assertEqual(packet["schema_version"], "sdd-module-summary-v1")
        self.assertEqual(packet["package"], "demo-package")
        self.assertEqual(packet["package_kind"], "single")
        self.assertNotIn("parent", packet)
        self.assertNotIn("children", packet)
        self.assertEqual(packet["related_packages"], [])
        self.assertNotIn("line", json.dumps(packet).lower())
        self.assertNotIn("tests", packet)
        self.assertEqual(self.run_cli("module-summary", "demo-package", "--json"), 0)

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

    def test_wiki_lint_reports_errors_and_warnings(self):
        wiki = self.root / ".wiki"
        (wiki / "Modules").mkdir(parents=True)
        (wiki / "Modules" / "Ledger.md").write_text("""---
title: Ledger
description: Ledger module
type: module
tags: [module]
package: ledger
source_checkpoint: abc123
summary: Stable module note.
---

# Ledger

See [[Missing Page]].

Locator `src/ledger.py:12`.
""", encoding="utf-8")
        (wiki / "Other" ).mkdir()
        (wiki / "Other" / "Ledger.md").write_text("""---
title: Ledger
description: Duplicate title
type: module
tags: [module]
package: ledger
summary: Duplicate module package.
---

# Ledger duplicate
""", encoding="utf-8")
        (wiki / "Loose.md").write_text("# Loose\n", encoding="utf-8")
        result = arbor.wiki_lint(self.root)
        self.assertFalse(result["ok"])
        error_codes = {item["code"] for item in result["errors"]}
        warning_codes = {item["code"] for item in result["warnings"]}
        self.assertIn("broken_wikilink", error_codes)
        self.assertIn("duplicate_title", error_codes)
        self.assertIn("duplicate_stem", error_codes)
        self.assertIn("duplicate_module_package", error_codes)
        self.assertIn("missing_frontmatter", error_codes)
        self.assertIn("module_missing_source_checkpoint", warning_codes)
        self.assertIn("module_line_locator", warning_codes)
        self.assertEqual(self.run_cli("wiki-lint", "--json"), 1)

    def test_doctor_skips_missing_wiki_and_reports_next_action(self):
        self.finalize_single()
        result = arbor.doctor(self.root, timestamp=NOW)
        self.assertTrue(result["ok"])
        self.assertTrue(result["wiki"]["skipped"])
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
        self.assertEqual(self.run_cli("mark-slice", "demo-package", "--id", "S-001", "--status", "in_progress", "--note", "API done, page pending", "--json"), 0)
        data = self.task_json()
        self.assertEqual(len(data["slices"]), 1)
        self.assertEqual(data["slices"][0]["id"], "S-001")
        self.assertEqual(data["slices"][0]["status"], "in_progress")
        self.assertEqual(data["slices"][0]["note"], "API done, page pending")
        self.assertEqual(self.run_cli("mark-slice", "demo-package", "--id", "S-001", "--status", "done", "--json"), 0)
        data = self.task_json()
        self.assertEqual(len(data["slices"]), 1)
        self.assertEqual(data["slices"][0]["status"], "done")
        self.assertEqual(self.run_cli("mark-slice", "demo-package", "--id", "S-002", "--status", "done", "--json"), 0)
        data = self.task_json()
        self.assertEqual(len(data["slices"]), 2)
        self.assertEqual([s["id"] for s in data["slices"]], ["S-001", "S-002"])
        self.assertEqual(self.run_cli("validate", "demo-package"), 0)

    def test_mark_slice_rejects_invalid_id(self):
        self.finalize_single()
        self.assertEqual(self.run_cli("mark-slice", "demo-package", "--id", "X-001", "--status", "done"), 1)

    def test_show_includes_slices(self):
        self.finalize_single()
        self.run_cli("mark-slice", "demo-package", "--id", "S-001", "--status", "done")
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
        self.assertIn("add-context-batch", context["reason"])

    def test_arbor_guard_blocks_destructive_bash_and_allows_safe_tools(self):
        blocked = arbor_guard.evaluate({"tool_name": "Bash", "tool_input": {"command": "git reset --hard HEAD"}})
        self.assertEqual(blocked["decision"], "block")
        allowed = arbor_guard.evaluate({"tool_name": "Read", "tool_input": {"file_path": str(self.root / "README.md")}})
        self.assertEqual(allowed["decision"], "allow")


if __name__ == "__main__":
    unittest.main()

import contextlib
import importlib.util
import io
import subprocess
import tempfile
import unittest
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = PLUGIN_ROOT / "tools" / "wiki.py"
BIN_PATH = PLUGIN_ROOT / "bin" / "sdd-wiki"
spec = importlib.util.spec_from_file_location("sdd_wiki", MODULE_PATH)
wiki = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wiki)


class WikiCliTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def run_cli(self, *args):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return wiki.main(["--root", str(self.root), *args])

    def run_bin(self, *args):
        return subprocess.run([str(BIN_PATH), "--root", str(self.root), *args], cwd=self.root, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)

    def test_wiki_index_search_and_collect_nested_pages(self):
        modules = self.root / ".wiki" / "Modules"
        modules.mkdir(parents=True)
        (modules / "Balance Ledger.md").write_text("""---
title: Balance Ledger
description: 余额账户、充值、扣款、退款 contract
tags: [module, backend, ledger]
type: module
area: 计费
package: balance-ledger
summary: Balance ledger owns account balance and refund invariants.
last_updated: 2026-05-07
---

# Balance Ledger

## Public contracts

Uses `BalanceLedgerService.recharge` and links to [[User Role Access]].
""", encoding="utf-8")
        (modules / "User Role Access.md").write_text("""---
title: User Role Access
description: 用户角色权限模块
tags: [module, auth]
type: module
summary: User role access owns instructor/admin authorization.
last_updated: 2026-05-07
---

# User Role Access

## Routes

Provides `RoleGate.canManageCourse`.
""", encoding="utf-8")
        indexed = wiki.wiki_index(self.root)
        self.assertEqual([page["title"] for page in indexed["pages"]], ["Balance Ledger", "User Role Access"])
        ledger = indexed["pages"][0]
        self.assertEqual(ledger["path"], ".wiki/Modules/Balance Ledger.md")
        self.assertIn("ledger", ledger["tags"])
        self.assertEqual(ledger["area"], "计费")
        self.assertIn({"kind": "heading", "level": "2", "name": "Public contracts"}, ledger["locators"])
        self.assertIn({"kind": "symbol", "name": "BalanceLedgerService.recharge"}, ledger["locators"])
        access = indexed["pages"][1]
        self.assertEqual(access["backlinks"], ["Balance Ledger"])
        self.assertIsNone(access["area"])
        search = wiki.wiki_search(self.root, "balance 退款 course")
        self.assertEqual(search["results"][0]["title"], "Balance Ledger")
        self.assertIn("description", search["results"][0]["matched_fields"])
        collected = wiki.wiki_collect(self.root, "role course", limit=1)
        self.assertEqual(len(collected["selected"]), 1)
        self.assertIn(collected["selected"][0]["title"], {"Balance Ledger", "User Role Access"})
        self.assertEqual(collected["selected"][0]["type"], "module")
        self.assertEqual(self.run_cli("index", "--json"), 0)
        self.assertEqual(self.run_cli("search", "balance refund", "--json"), 0)
        self.assertEqual(self.run_cli("collect", "--query", "balance refund", "--json"), 0)

    def test_wiki_search_matches_on_area_field(self):
        wiki_dir = self.root / ".wiki"
        wiki_dir.mkdir(parents=True)
        (wiki_dir / "Asset Pipeline.md").write_text("""---
title: Asset Pipeline
description: 资产导入与打包流程
type: concept
area: 资产管线
tags: [assets]
summary: 模型与贴图的导入、压缩与打包约定。
last_updated: 2026-06-10
---

# Asset Pipeline
""", encoding="utf-8")
        result = wiki.wiki_search(self.root, "资产管线")
        self.assertEqual(1, len(result["results"]))
        self.assertIn("area", result["results"][0]["matched_fields"])
        collected = wiki.wiki_collect(self.root, "资产管线", limit=1)
        self.assertEqual(collected["selected"][0]["area"], "资产管线")

    def test_wiki_lint_reports_errors_and_warnings(self):
        wiki_dir = self.root / ".wiki"
        (wiki_dir / "Modules").mkdir(parents=True)
        (wiki_dir / "Modules" / "Ledger.md").write_text("""---
title: Ledger
description: Ledger module
type: module
tags: [module]
package: ledger
source_checkpoint: abc123
summary: Stable module note.
last_updated: 2026-05-07
---

# Ledger

See [[Missing Page]].

Locator `src/ledger.py:12`.
""", encoding="utf-8")
        (wiki_dir / "Other").mkdir()
        (wiki_dir / "Other" / "Ledger.md").write_text("""---
title: Ledger
description: Duplicate title
type: module
tags: [module]
package: ledger
summary: Duplicate module package.
last_updated: 2026-05-07
---

# Ledger duplicate
""", encoding="utf-8")
        (wiki_dir / "Loose.md").write_text("# Loose\n", encoding="utf-8")
        result = wiki.wiki_lint(self.root)
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
        self.assertEqual(self.run_cli("lint", "--json"), 1)

    def test_wiki_search_matches_on_type_field(self):
        wiki_dir = self.root / ".wiki"
        wiki_dir.mkdir(parents=True, exist_ok=True)
        (wiki_dir / "Export Touchpoints.md").write_text("""---
title: Export Touchpoints
description: Project-wide export touchpoints
type: cross_cut
tags: [exports]
summary: Cross-module export checklist.
last_updated: 2026-05-07
---

# Export Touchpoints

## Touchpoints
- `services/auth/exports.py`
""", encoding="utf-8")
        result = wiki.wiki_search(self.root, "cross_cut")
        self.assertEqual(1, len(result["results"]))
        match = result["results"][0]
        self.assertIn("type", match["matched_fields"])
        self.assertEqual("Export Touchpoints", match["title"])

    def test_wiki_search_prioritizes_explicit_type_match(self):
        wiki_dir = self.root / ".wiki"
        (wiki_dir / "Modules").mkdir(parents=True, exist_ok=True)
        (wiki_dir / "CrossCut").mkdir(parents=True, exist_ok=True)
        (wiki_dir / "Modules" / "Auth.md").write_text("""---
title: Auth
description: auth module export implementation and routes
type: module
tags: [module, auth, exports]
package: auth
source_checkpoint: abc123
summary: auth export functions and route anchors.
last_updated: 2026-05-07
---

# Auth

## Anchors
- `services/auth/exports.py`
- `api/auth_routes.py`
""", encoding="utf-8")
        (wiki_dir / "CrossCut" / "Export Touchpoints.md").write_text("""---
title: Export Touchpoints
description: Project-wide export touchpoints
type: cross_cut
tags: [cross-cut, exports]
summary: Cross-module export checklist for auth and payment.
last_updated: 2026-05-07
---

# Export Touchpoints

## Touchpoints
- `services/auth/exports.py`
""", encoding="utf-8")
        result = wiki.wiki_search(self.root, "cross_cut auth export")
        self.assertEqual("Export Touchpoints", result["results"][0]["title"])
        self.assertIn("type", result["results"][0]["matched_fields"])

    def test_wiki_lint_allows_group_index_pages(self):
        wiki_dir = self.root / ".wiki"
        (wiki_dir / "Modules").mkdir(parents=True, exist_ok=True)
        (wiki_dir / "CrossCut").mkdir(parents=True, exist_ok=True)
        for path, title in (
            (wiki_dir / "index.md", "Wiki 入口"),
            (wiki_dir / "Modules" / "index.md", "Modules"),
            (wiki_dir / "CrossCut" / "index.md", "CrossCut"),
        ):
            path.write_text(f"""---
title: {title}
description: Obsidian navigation entry
type: entity
tags: [index]
summary: Navigation entry.
last_updated: 2026-05-07
---

# {title}
""", encoding="utf-8")
        result = wiki.wiki_lint(self.root)
        duplicate_stem_errors = [item for item in result["errors"] if item["code"] == "duplicate_stem"]
        self.assertEqual([], duplicate_stem_errors)

    def test_wiki_lint_accepts_cross_cut_type(self):
        wiki_dir = self.root / ".wiki"
        wiki_dir.mkdir(parents=True, exist_ok=True)
        (wiki_dir / "Export Touchpoints.md").write_text("""---
title: Export Touchpoints
description: 新增导出函数与路由时全项目需同步修改的位置与命名规则
type: cross_cut
tags: [exports, backend]
summary: 新增/修改导出时必须同步检查的位置与命名规则。
last_updated: 2026-05-07
---

# Export Touchpoints

## Touchpoints
- `services/auth/exports.py`
- `api/auth_routes.py`
""", encoding="utf-8")
        result = wiki.wiki_lint(self.root)
        invalid_type_errors = [item for item in result["errors"] if item["code"] == "invalid_type"]
        self.assertEqual([], invalid_type_errors)

    def test_bin_wrapper_runs_standalone(self):
        (self.root / ".wiki").mkdir()
        result = self.run_bin("lint", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('"ok": true', result.stdout)

    def test_active_scenario_sources_use_sdd_wiki(self):
        scenario_files = [
            PLUGIN_ROOT / "tests" / "scenario_eval" / "run.py",
            PLUGIN_ROOT / "tests" / "scenario_eval" / "run_wiki_ai_user.py",
            PLUGIN_ROOT / "tests" / "scenario_eval" / "framework" / "checks.py",
        ]
        combined = "\n".join(path.read_text(encoding="utf-8") for path in scenario_files)
        self.assertNotIn("sdd-arbor wiki-", combined)
        self.assertNotIn("wiki-collect", combined)
        self.assertIn("sdd-wiki collect", combined)


if __name__ == "__main__":
    unittest.main()

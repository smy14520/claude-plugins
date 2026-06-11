"""
AI scenario eval: realistic wiki ingest -> query -> lint flow.

This is an opt-in exploratory runner, not a pytest test. It runs Claude Code
with this local sdd-kit plugin in a temporary project, asks it to use the wiki
skill for a cross-cut knowledge task, then preserves the dialogue and quality
report under tests/scenario_eval/runs.

Run from repo root:
  RUN_SCENARIO_AI_USER=1 python plugins/sdd-kit/tests/scenario_eval/run_wiki_ai_user.py

Useful env:
  SCENARIO_TEST_MODEL=claude-opus-4-6
  SCENARIO_WIKI_RESPONSE_TIMEOUT=900
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PLUGIN_ROOT = Path(__file__).resolve().parents[2]
TESTS_ROOT = PLUGIN_ROOT / "tests"
RUNS_ROOT = TESTS_ROOT / "scenario_eval" / "runs"
ARBOR = PLUGIN_ROOT / "bin" / "sdd-arbor"
WIKI = PLUGIN_ROOT / "bin" / "sdd-wiki"
DEFAULT_MODEL = os.environ.get("SCENARIO_TEST_MODEL", "claude-opus-4-6")
SCENARIO_NAME = os.environ.get("SCENARIO_NAME", "wiki-cross-cut-export")

if "ANTHROPIC_API_KEY" not in os.environ and "ANTHROPIC_AUTH_TOKEN" in os.environ:
    os.environ["ANTHROPIC_API_KEY"] = os.environ["ANTHROPIC_AUTH_TOKEN"]


@dataclass
class ScenarioPaths:
    run_dir: Path
    work_dir: Path
    dialogue_path: Path
    summary_path: Path
    events_path: Path
    test_report_path: Path


def timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_slug(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip()).strip("-")
    return cleaned or "scenario"


def unique_run_dir() -> Path:
    date = datetime.now().strftime("%Y-%m-%d")
    base = RUNS_ROOT / date / safe_slug(SCENARIO_NAME)
    if not base.exists():
        return base
    suffix = 2
    while (RUNS_ROOT / date / f"{safe_slug(SCENARIO_NAME)}-{suffix}").exists():
        suffix += 1
    return RUNS_ROOT / date / f"{safe_slug(SCENARIO_NAME)}-{suffix}"


def write_jsonl(path: Path, entry: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def log_event(paths: ScenarioPaths | None, event: str, **data: Any) -> None:
    entry = {"at": timestamp(), "event": event, **data}
    print(f"[{entry['at']}] {event}: {json.dumps(data, ensure_ascii=False)}", flush=True)
    if paths is not None:
        write_jsonl(paths.events_path, entry)


def append_dialogue(paths: ScenarioPaths, title: str, body: str) -> None:
    paths.dialogue_path.parent.mkdir(parents=True, exist_ok=True)
    with paths.dialogue_path.open("a", encoding="utf-8") as handle:
        handle.write(f"\n## {title}\n\n{body.strip()}\n")


def require_enabled() -> None:
    if not os.environ.get("RUN_SCENARIO_AI_USER"):
        raise SystemExit("Set RUN_SCENARIO_AI_USER=1 to run this opt-in scenario eval.")
    try:
        import claude_agent_sdk  # noqa: F401
    except ImportError as exc:
        raise SystemExit("claude-agent-sdk is required for this scenario eval.") from exc


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def make_paths(run_dir: Path, work_dir: Path) -> ScenarioPaths:
    paths = ScenarioPaths(
        run_dir=run_dir,
        work_dir=work_dir,
        dialogue_path=run_dir / "dialogue.md",
        summary_path=run_dir / "summary.json",
        events_path=run_dir / "events.jsonl",
        test_report_path=work_dir / "test.md",
    )
    paths.dialogue_path.write_text(
        f"# Wiki scenario dialogue — {SCENARIO_NAME}\n\n"
        f"- 时间：{timestamp()}\n"
        f"- Model：{DEFAULT_MODEL}\n\n",
        encoding="utf-8",
    )
    log_event(paths, "workdir_prepared", run_dir=str(run_dir), work_dir=str(work_dir))
    return paths


def prepare_external_workdir(source: Path) -> ScenarioPaths:
    if not source.exists() or not source.is_dir():
        raise SystemExit(f"SCENARIO_WIKI_SOURCE_PROJECT must be an existing directory: {source}")
    run_dir = unique_run_dir()
    run_dir.mkdir(parents=True, exist_ok=False)
    work_dir = run_dir / "project"
    ignore = shutil.ignore_patterns("node_modules", "dist", ".git", ".wiki")
    shutil.copytree(source, work_dir, ignore=ignore)
    env = os.environ.copy()
    env.update({
        "GIT_AUTHOR_NAME": "sdd-kit scenario",
        "GIT_AUTHOR_EMAIL": "scenario@example.invalid",
        "GIT_COMMITTER_NAME": "sdd-kit scenario",
        "GIT_COMMITTER_EMAIL": "scenario@example.invalid",
    })
    for command in (["git", "init", "-q"], ["git", "add", "-A"], ["git", "commit", "-q", "-m", "init"]):
        subprocess.run(command, cwd=work_dir, env=env, check=True)
    return make_paths(run_dir, work_dir)


def prepare_workdir() -> ScenarioPaths:
    source_project = os.environ.get("SCENARIO_WIKI_SOURCE_PROJECT")
    if source_project:
        return prepare_external_workdir(Path(source_project).expanduser().resolve())

    run_dir = unique_run_dir()
    run_dir.mkdir(parents=True, exist_ok=False)
    work_dir = run_dir / "project"
    work_dir.mkdir()

    write(work_dir / "services/auth/exports.py", """
from dataclasses import dataclass

@dataclass
class Session:
    user_id: str
    token: str


def auth_export_user_session(user_id: str) -> Session:
    return Session(user_id=user_id, token=f\"session-{user_id}\")


def auth_export_role(user_id: str) -> str:
    return \"admin\" if user_id.startswith(\"admin\") else \"user\"
""".strip() + "\n")
    write(work_dir / "api/auth_routes.py", """
from services.auth.exports import auth_export_role, auth_export_user_session


def register_auth_export_routes(router):
    router.get(\"/api/auth/session/export\", auth_export_user_session)
    router.get(\"/api/auth/role/export\", auth_export_role)
""".strip() + "\n")
    write(work_dir / "services/payment/exports.py", """
def payment_exporter_invoice(invoice_id: str) -> dict:
    return {\"invoice_id\": invoice_id, \"kind\": \"invoice\"}


def payment_exporter_refund(refund_id: str) -> dict:
    return {\"refund_id\": refund_id, \"kind\": \"refund\"}
""".strip() + "\n")
    write(work_dir / "api/payment_routes.py", """
from services.payment.exports import payment_exporter_invoice, payment_exporter_refund


def register_payment_export_routes(router):
    router.get(\"/api/payment/invoice/export\", payment_exporter_invoice)
    router.get(\"/api/payment/refund/export\", payment_exporter_refund)
""".strip() + "\n")
    write(work_dir / "registry/export_registry.py", """
EXPORT_REGISTRY = {
    \"auth.session\": \"auth_export_user_session\",
    \"auth.role\": \"auth_export_role\",
    \"payment.invoice\": \"payment_exporter_invoice\",
    \"payment.refund\": \"payment_exporter_refund\",
}
""".strip() + "\n")
    write(work_dir / "README.md", """
# Export Fixture

This project intentionally keeps export touchpoints scattered across service,
route, and registry files. The auth module uses `auth_export_*`; payment uses
the historical `payment_exporter_*` prefix.
""".strip() + "\n")

    env = os.environ.copy()
    env.update({
        "GIT_AUTHOR_NAME": "sdd-kit scenario",
        "GIT_AUTHOR_EMAIL": "scenario@example.invalid",
        "GIT_COMMITTER_NAME": "sdd-kit scenario",
        "GIT_COMMITTER_EMAIL": "scenario@example.invalid",
    })
    for command in (["git", "init", "-q"], ["git", "add", "-A"], ["git", "commit", "-q", "-m", "init"]):
        subprocess.run(command, cwd=work_dir, env=env, check=True)

    return make_paths(run_dir, work_dir)


def default_initial_prompt() -> str:
    return """
用 wiki skill 为这个存量项目做一次真实的 wiki ingest/query/lint 流程。

项目背景：这是一个简化的多模块导出系统。新增导出能力时必须同步修改多个位置：
- `services/auth/exports.py`：`auth_export_user_session` / `auth_export_role`
- `api/auth_routes.py`：`register_auth_export_routes`
- `services/payment/exports.py`：`payment_exporter_invoice` / `payment_exporter_refund`
- `api/payment_routes.py`：`register_payment_export_routes`
- `registry/export_registry.py`：`EXPORT_REGISTRY` 连接 auth/payment 导出名称

请真实执行：
1. 先阅读相关代码，理解新增导出需要同步修改哪些位置。
2. 用 wiki skill ingest 这些长期知识：
   - 至少创建一个 `type: cross_cut` 页面（推荐路径 `.wiki/CrossCut/新增导出.md`），包含 description、summary、tags、适用场景、同步修改位置、命名规则、验证线索。
   - 至少创建或更新一个 module note（auth 或 payment，推荐路径 `.wiki/Modules/<模块名>.md`），并用 wikilink 与 cross_cut 页面互相关联。
   - 维护 Obsidian 导航入口：`.wiki/index.md`、`.wiki/CrossCut/index.md`、`.wiki/Modules/index.md`。
   - 遵守 single-source，不要把完整函数清单复制到两个页面。
3. 用 `sdd-wiki collect --query "新增 导出 cross_cut auth" --limit 5 --json` 查询，按渐进式披露先看候选 metadata，再只读需要的页面。
4. 用 `sdd-wiki lint --json` 检查健康度。
5. 最后用简短中文说明：写了哪些页面、query 命中了什么、lint 是否通过、用于实现前还需要验证哪些代码位置。

不要实现业务代码，不要创建 `.arbor` package，不要提交 git。
""".strip()


def todo_initial_prompt() -> str:
    return """
用 wiki skill 为这个已有 Todo Web App 项目做一次真实的 wiki ingest/query/lint 流程。

项目背景：这是一个 local-only React Todo 应用。修改 Todo 生命周期能力时通常会横切多个位置：
- `src/todo.ts`：Task schema、bucket/priority 枚举、create/complete/undo/rename/move/defer/storage 等领域逻辑
- `src/App.tsx`：新增、完成、延期、移动、编辑、删除、本地保存错误反馈等 UI 绑定
- `tests/todo.test.ts`：领域模型与 localStorage adapter 单测
- `tests/e2e/todo.spec.ts`：浏览器核心路径与刷新保留验证
- `.arbor/tasks/*/prd.md`：产品范围、out-of-scope 和验收标准

请真实执行：
1. 先阅读相关代码和 PRD，理解 Todo 生命周期改动需要同步修改哪些位置。
2. 用 wiki skill ingest 这些长期知识：
   - 至少创建一个 `type: cross_cut` 页面（推荐路径 `.wiki/CrossCut/Todo 生命周期改动.md`），包含 description、summary、tags、适用场景、同步修改位置、命名/语义规则、验证线索。
   - 至少创建或更新一个 module note（例如 Todo core/domain module，推荐路径 `.wiki/Modules/<模块名>.md`），并用 wikilink 与 cross_cut 页面互相关联。
   - 维护 Obsidian 导航入口：`.wiki/index.md`、`.wiki/CrossCut/index.md`、`.wiki/Modules/index.md`。
   - 遵守 single-source，不要把完整契约清单复制到两个页面。
3. 用 `sdd-wiki collect --query "Todo cross_cut localStorage 完成 延期" --limit 5 --json` 查询，按渐进式披露先看候选 metadata，再只读需要的页面。
4. 用 `sdd-wiki lint --json` 检查健康度。
5. 最后用简短中文说明：写了哪些页面、query 命中了什么、lint 是否通过、用于实现前还需要验证哪些代码位置。

不要实现业务代码，不要创建新的 `.arbor` package，不要提交 git。
""".strip()


def initial_prompt() -> str:
    if os.environ.get("SCENARIO_WIKI_PROMPT_KIND") == "todo":
        return todo_initial_prompt()
    return default_initial_prompt()


def _message_preview(message: Any) -> str:
    return repr(message)[:1000]


async def receive_response(client: Any, paths: ScenarioPaths) -> tuple[str, str | None]:
    from claude_agent_sdk import AssistantMessage, ResultMessage, SystemMessage, TextBlock

    response_text = ""
    response_error: str | None = None
    async with asyncio.timeout(int(os.environ.get("SCENARIO_WIKI_RESPONSE_TIMEOUT", "900"))):
        async for msg in client.receive_response():
            if isinstance(msg, SystemMessage):
                log_event(paths, "tested_agent_system", subtype=msg.subtype, data=msg.data or {})
                continue
            log_event(paths, "tested_agent_message", message_type=type(msg).__name__, preview=_message_preview(msg))
            if isinstance(msg, AssistantMessage):
                text = "".join(block.text for block in msg.content if isinstance(block, TextBlock))
                if text:
                    response_text += text
                    log_event(paths, "tested_agent_assistant_message", chars=len(text))
                continue
            if isinstance(msg, ResultMessage):
                log_event(paths, "tested_agent_result", is_error=msg.is_error, duration_ms=msg.duration_ms)
                if msg.is_error:
                    response_error = msg.result or "ResultMessage reported an error."
                elif msg.result and not response_text.strip():
                    response_text = msg.result
                break
    return response_text.strip(), response_error


def run_arbor(work_dir: Path, *args: str) -> tuple[int, dict[str, Any] | None, str]:
    return run_json_tool(work_dir, ARBOR, *args)


def run_wiki(work_dir: Path, *args: str) -> tuple[int, dict[str, Any] | None, str]:
    return run_json_tool(work_dir, WIKI, *args)


def run_json_tool(work_dir: Path, tool: Path, *args: str) -> tuple[int, dict[str, Any] | None, str]:
    proc = subprocess.run(
        [str(tool), *args],
        cwd=work_dir,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    parsed = None
    if proc.stdout.strip():
        try:
            parsed = json.loads(proc.stdout)
        except json.JSONDecodeError:
            parsed = None
    return proc.returncode, parsed, proc.stdout + proc.stderr


def read_wiki_pages(work_dir: Path) -> list[dict[str, Any]]:
    pages: list[dict[str, Any]] = []
    wiki_root = work_dir / ".wiki"
    if not wiki_root.exists():
        return pages
    for path in sorted(wiki_root.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        meta: dict[str, str] = {}
        if text.startswith("---\n"):
            end = text.find("\n---", 4)
            if end != -1:
                for line in text[4:end].strip().splitlines():
                    if ":" not in line:
                        continue
                    key, value = line.split(":", 1)
                    meta[key.strip()] = value.strip().strip('"\'')
        pages.append({"path": path.relative_to(work_dir).as_posix(), "text": text, "meta": meta})
    return pages


def scenario_query() -> str:
    if os.environ.get("SCENARIO_WIKI_PROMPT_KIND") == "todo":
        return "Todo cross_cut localStorage 完成 延期"
    return "新增 导出 cross_cut auth"


def quality_checks(paths: ScenarioPaths, response_text: str, run_error: str | None) -> tuple[dict[str, bool], dict[str, Any]]:
    pages = read_wiki_pages(paths.work_dir)
    query = scenario_query()
    lint_code, lint_json, lint_raw = run_wiki(paths.work_dir, "lint", "--json")
    collect_code, collect_json, collect_raw = run_wiki(paths.work_dir, "collect", "--query", query, "--limit", "5", "--json")
    search_code, search_json, search_raw = run_wiki(paths.work_dir, "search", "cross_cut", "--limit", "3", "--json")
    index_code, index_json, index_raw = run_wiki(paths.work_dir, "index", "--json")

    cross_cut_pages = [p for p in pages if p["meta"].get("type") == "cross_cut"]
    module_pages = [p for p in pages if p["meta"].get("type") == "module"]
    cross_text = "\n".join(p["text"] for p in cross_cut_pages)
    module_text = "\n".join(p["text"] for p in module_pages)
    selected = (collect_json or {}).get("selected") or []
    top = selected[0] if selected else {}
    progressive_fields = {"title", "description", "summary", "type", "tags", "links", "backlinks", "locators"}

    if os.environ.get("SCENARIO_WIKI_PROMPT_KIND") == "todo":
        cross_cut_has_required_touchpoints = all(token in cross_text for token in ("src/todo.ts", "src/App.tsx", "tests/todo.test.ts", "tests/e2e/todo.spec.ts"))
        cross_cut_has_rules = any(token in cross_text for token in ("Bucket", "bucket")) and any(token in cross_text for token in ("Priority", "priority"))
        module_links_cross_cut = "[[" in module_text and any(p["meta"].get("title") in module_text or "横切" in module_text for p in cross_cut_pages)
    else:
        cross_cut_has_required_touchpoints = all(token in cross_text for token in ("services/auth/exports.py", "api/auth_routes.py", "services/payment/exports.py", "api/payment_routes.py", "registry/export_registry.py"))
        cross_cut_has_rules = "auth_export" in cross_text and "payment_exporter" in cross_text
        module_links_cross_cut = "[[" in module_text and any(p["meta"].get("title") in module_text or "导出" in module_text for p in cross_cut_pages)

    checks = {
        "agent_completed": run_error is None and bool(response_text),
        "wiki_pages_written": len(pages) >= 2,
        "has_cross_cut_page": bool(cross_cut_pages),
        "has_module_page": bool(module_pages),
        "cross_cut_has_description_summary": bool(cross_cut_pages and cross_cut_pages[0]["meta"].get("description") and cross_cut_pages[0]["meta"].get("summary")),
        "cross_cut_has_required_touchpoints": cross_cut_has_required_touchpoints,
        "cross_cut_has_rules": cross_cut_has_rules,
        "module_links_cross_cut": module_links_cross_cut,
        "lint_ok": lint_code == 0 and bool(lint_json and lint_json.get("ok")),
        "collect_ok": collect_code == 0 and bool(selected),
        "collect_top_is_cross_cut": top.get("type") == "cross_cut",
        "collect_exposes_progressive_fields": progressive_fields.issubset(set(top.keys())) if top else False,
        "search_type_ok": search_code == 0 and bool((search_json or {}).get("results")) and (search_json or {}).get("results", [{}])[0].get("type") == "cross_cut",
        "index_has_backlinks": index_code == 0 and any(page.get("backlinks") for page in (index_json or {}).get("pages", []) if page.get("type") == "cross_cut"),
        "has_root_index": any(page.get("path") == ".wiki/index.md" for page in (index_json or {}).get("pages", [])),
        "has_modules_index": any(page.get("path") == ".wiki/Modules/index.md" for page in (index_json or {}).get("pages", [])),
        "has_cross_cut_index": any(page.get("path") == ".wiki/CrossCut/index.md" for page in (index_json or {}).get("pages", [])),
        "cross_cut_under_directory": any(str(page.get("path", "")).startswith(".wiki/CrossCut/") and page.get("type") == "cross_cut" for page in (index_json or {}).get("pages", [])),
    }
    diagnostics = {
        "pages": [{"path": p["path"], "meta": p["meta"]} for p in pages],
        "lint": lint_json if lint_json is not None else lint_raw,
        "collect": collect_json if collect_json is not None else collect_raw,
        "search": search_json if search_json is not None else search_raw,
        "index": index_json if index_json is not None else index_raw,
    }
    return checks, diagnostics


async def run_scenario(paths: ScenarioPaths) -> dict[str, Any]:
    from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient, PermissionResultAllow, SdkPluginConfig

    async def allow_tool(tool_name: str, input_data: dict[str, Any], context: Any) -> PermissionResultAllow:
        return PermissionResultAllow(updated_input=input_data)

    client = ClaudeSDKClient(ClaudeAgentOptions(
        cwd=str(paths.work_dir),
        plugins=[SdkPluginConfig(type="local", path=str(PLUGIN_ROOT))],
        permission_mode="bypassPermissions",
        can_use_tool=allow_tool,
        max_turns=int(os.environ.get("SCENARIO_WIKI_MAX_TURNS", "80")),
        model=DEFAULT_MODEL,
        stderr=lambda line: log_event(paths, "tested_agent_stderr", line=line.strip()),
    ))
    prompt = initial_prompt()
    response_text = ""
    run_error: str | None = None
    try:
        log_event(paths, "tested_agent_connect_start", model=DEFAULT_MODEL)
        await asyncio.wait_for(client.connect(), timeout=int(os.environ.get("SCENARIO_CONNECT_TIMEOUT", "20")))
        log_event(paths, "tested_agent_connected")
        append_dialogue(paths, "用户请求", prompt)
        await asyncio.wait_for(client.query(prompt), timeout=int(os.environ.get("SCENARIO_QUERY_TIMEOUT", "20")))
        log_event(paths, "tested_agent_query_sent")
        response_text, response_error = await receive_response(client, paths)
        if response_error:
            run_error = response_error
        append_dialogue(paths, "被测 agent 回复", response_text or f"[empty response; error={run_error}]")
    except TimeoutError:
        run_error = "Timed out waiting for tested agent response."
        log_event(paths, "tested_agent_timeout", error=run_error)
    finally:
        await client.disconnect()
        log_event(paths, "tested_agent_disconnected")

    checks, diagnostics = quality_checks(paths, response_text, run_error)
    required = [
        "agent_completed",
        "wiki_pages_written",
        "has_cross_cut_page",
        "has_module_page",
        "cross_cut_has_description_summary",
        "cross_cut_has_required_touchpoints",
        "cross_cut_has_rules",
        "lint_ok",
        "collect_ok",
        "collect_top_is_cross_cut",
        "collect_exposes_progressive_fields",
        "search_type_ok",
        "has_root_index",
        "has_modules_index",
        "has_cross_cut_index",
        "cross_cut_under_directory",
    ]
    if all(checks.get(key) for key in required):
        verdict = "pass"
    elif any(checks.get(key) for key in ("wiki_pages_written", "has_cross_cut_page", "lint_ok")):
        verdict = "needs_review"
    else:
        verdict = "failed"

    summary = {
        "run_dir": str(paths.run_dir),
        "work_dir": str(paths.work_dir),
        "model": DEFAULT_MODEL,
        "scenario_name": SCENARIO_NAME,
        "run_error": run_error,
        "verdict": verdict,
        "checks": checks,
        "response_preview": response_text[:2000],
        "diagnostics": diagnostics,
    }
    paths.summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_test_report(paths, summary)
    return summary


def write_test_report(paths: ScenarioPaths, summary: dict[str, Any]) -> None:
    checks = summary["checks"]
    diagnostics = summary["diagnostics"]
    page_lines = [f"- `{page['path']}` — type={page['meta'].get('type')} title={page['meta'].get('title')}" for page in diagnostics.get("pages", [])]
    failed = [key for key, value in checks.items() if not value]
    body = f"""# Wiki Scenario Eval Report — {SCENARIO_NAME}

## 基本信息

- 时间：{timestamp()}
- Work dir：`{paths.work_dir}`
- Dialogue：`{paths.dialogue_path.name}`
- Summary：`{paths.summary_path.name}`
- Verdict：`{summary['verdict']}`
- Run error：{summary['run_error'] or 'N/A'}

## 自动检查

```json
{json.dumps(checks, ensure_ascii=False, indent=2)}
```

## Wiki 页面

{chr(10).join(page_lines) if page_lines else '- 未发现 `.wiki` 页面。'}

## 质量观察

{('- 未通过检查：' + ', '.join(failed)) if failed else '- wiki ingest/query/lint 主路径通过；cross_cut 页面、渐进式 metadata 和 helper 检索行为符合预期。'}

## Query top result

```json
{json.dumps((diagnostics.get('collect') or {}).get('selected', [])[:1], ensure_ascii=False, indent=2)}
```
"""
    paths.test_report_path.write_text(body, encoding="utf-8")


async def amain() -> None:
    require_enabled()
    paths = prepare_workdir()
    summary = await run_scenario(paths)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if summary["verdict"] == "failed":
        raise SystemExit(1)


def main() -> None:
    asyncio.run(amain())


if __name__ == "__main__":
    main()

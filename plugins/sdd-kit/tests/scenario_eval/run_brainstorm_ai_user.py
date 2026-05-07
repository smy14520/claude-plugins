"""
AI-user scenario eval: realistic brainstorm -> impl flow with persisted artifacts.

This is an opt-in exploratory runner, not a pytest test. It runs Claude Code with
this local sdd-kit plugin, lets an AI product owner answer brainstorm questions,
then continues into impl. Each run is preserved under tests/scenario_eval/runs.

Run from repo root:
  RUN_SCENARIO_AI_USER=1 python plugins/sdd-kit/tests/scenario_eval/run_brainstorm_ai_user.py

Useful env:
  SCENARIO_NAME=personal-finance-greenfield-medium
  SCENARIO_CONVERSATION_TURNS=14
  SCENARIO_IMPL_TURNS=80
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PLUGIN_ROOT = Path(__file__).resolve().parents[2]
TESTS_ROOT = PLUGIN_ROOT / "tests"
FIXTURE_DIR = TESTS_ROOT / "fixtures" / "express-app"
RUNS_ROOT = TESTS_ROOT / "scenario_eval" / "runs"
MAX_CONVERSATION_TURNS = int(os.environ.get("SCENARIO_CONVERSATION_TURNS", "14"))
MAX_IMPL_TURNS = int(os.environ.get("SCENARIO_IMPL_TURNS", "80"))
DEFAULT_MODEL = os.environ.get("SCENARIO_TEST_MODEL", "claude-opus-4-6")
AI_USER_MODEL = os.environ.get("SCENARIO_AI_USER_MODEL", DEFAULT_MODEL)
AI_USER_MODE = os.environ.get("SCENARIO_AI_USER_MODE", "agent")

if "ANTHROPIC_API_KEY" not in os.environ and "ANTHROPIC_AUTH_TOKEN" in os.environ:
    os.environ["ANTHROPIC_API_KEY"] = os.environ["ANTHROPIC_AUTH_TOKEN"]


@dataclass(frozen=True)
class Scenario:
    name: str
    profile: str
    project_brief: str
    org_context: str


DEFAULT_ORG_CONTEXT = (
    "如果对方问到开发/测试环境、依赖安装、启动应用或本机环境变更，你的组织约束是："
    "优先使用 Docker / docker-compose 在项目临时工作区内隔离环境；可以要求生成 docker-compose.yml；不要污染当前电脑的全局环境。"
)

SCENARIOS = {
    "personal-finance-greenfield-medium": Scenario(
        name="personal-finance-greenfield-medium",
        profile="greenfield-medium",
        project_brief=(
            "主题种子：个人预算 / 记账 / cashflow。用户侧产品负责人应提出一个从零开始的中等复杂度 Web 工具需求，"
            "包含核心领域模型、数据持久化、日常录入流程、统计/回顾、边界和测试策略。"
        ),
        org_context=DEFAULT_ORG_CONTEXT,
    ),
    "reading-planner-greenfield-large": Scenario(
        name="reading-planner-greenfield-large",
        profile="greenfield-large",
        project_brief=(
            "主题种子：学习 / 阅读 / 目标追踪。用户侧产品负责人应提出一个从零开始的较大 Web 产品需求，"
            "需要多个功能切片、清晰非目标、数据模型、核心用户流、验收和后续演进边界。"
        ),
        org_context=DEFAULT_ORG_CONTEXT,
    ),
    "customer-service-existing-medium": Scenario(
        name="customer-service-existing-medium",
        profile="existing-medium",
        project_brief=(
            "当前 fixture 是一个 Express + TypeScript 的 AI 客服多渠道后端系统，已有微信/抖音渠道 adapter、"
            "channels 配置模型和统一 webhook 路由。用户侧产品负责人应提出适合该存量后端的中等需求。"
        ),
        org_context=DEFAULT_ORG_CONTEXT,
    ),
    "todo-greenfield-small": Scenario(
        name="todo-greenfield-small",
        profile="greenfield-small",
        project_brief="主题种子：todo / task management。用户侧产品负责人应围绕一个从零开始的小型 todo 产品自己提出具体需求。",
        org_context=DEFAULT_ORG_CONTEXT,
    ),
    "wiki-cross-cut-export-integration": Scenario(
        name="wiki-cross-cut-export-integration",
        profile="existing-wiki-export",
        project_brief=(
            "当前 fixture 是一个 Python 多模块导出系统，已有 auth 导出函数、API route 注册、导出注册表，"
            "并且 `.wiki/` 已沉淀 `新增导出` cross_cut 页面。eval 关注 brainstorm/impl 是否按需查询 wiki、"
            "在 PRD 中引用 cross-cut 页面，并在实现前验证当前代码位置。"
        ),
        org_context=DEFAULT_ORG_CONTEXT,
    ),
}


def selected_scenario() -> Scenario:
    scenario_name = os.environ.get("SCENARIO_NAME")
    if scenario_name:
        if scenario_name not in SCENARIOS:
            names = ", ".join(sorted(SCENARIOS))
            raise SystemExit(f"Unknown SCENARIO_NAME={scenario_name!r}. Available: {names}")
        return SCENARIOS[scenario_name]

    profile = os.environ.get("SCENARIO_PROFILE", "existing-medium")
    default_brief = "当前 fixture 是一个 Express + TypeScript 的 AI 客服多渠道后端系统，已有微信/抖音渠道 adapter、channels 配置模型和统一 webhook 路由。"
    return Scenario(
        name=os.environ.get("SCENARIO_NAME", "custom"),
        profile=profile,
        project_brief=os.environ.get("SCENARIO_PROJECT_BRIEF", default_brief),
        org_context=os.environ.get("SCENARIO_ORG_CONTEXT", DEFAULT_ORG_CONTEXT),
    )


SCENARIO = selected_scenario()
if SCENARIO.name == "wiki-cross-cut-export-integration":
    MAX_CONVERSATION_TURNS = int(os.environ.get("SCENARIO_CONVERSATION_TURNS", "12"))
    MAX_IMPL_TURNS = int(os.environ.get("SCENARIO_IMPL_TURNS", "30"))


@dataclass
class ScenarioPaths:
    run_dir: Path
    work_dir: Path
    transcript_path: Path
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
    base = RUNS_ROOT / date / safe_slug(SCENARIO.name)
    if not base.exists():
        return base
    suffix = 2
    while (RUNS_ROOT / date / f"{safe_slug(SCENARIO.name)}-{suffix}").exists():
        suffix += 1
    return RUNS_ROOT / date / f"{safe_slug(SCENARIO.name)}-{suffix}"


def log_event(paths: ScenarioPaths | None, event: str, **data: Any) -> None:
    entry = {"at": timestamp(), "event": event, **data}
    print(f"[{entry['at']}] {event}: {json.dumps(data, ensure_ascii=False)}", flush=True)
    if paths is not None:
        write_jsonl(paths.events_path, entry)


def require_enabled() -> None:
    if not os.environ.get("RUN_SCENARIO_AI_USER"):
        raise SystemExit("Set RUN_SCENARIO_AI_USER=1 to run this opt-in scenario eval.")
    try:
        import claude_agent_sdk  # noqa: F401
    except ImportError as exc:
        raise SystemExit("claude-agent-sdk is required for this scenario eval.") from exc


def write_jsonl(path: Path, entry: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def append_dialogue(paths: ScenarioPaths, title: str, body: str) -> None:
    paths.dialogue_path.parent.mkdir(parents=True, exist_ok=True)
    with paths.dialogue_path.open("a", encoding="utf-8") as handle:
        handle.write(f"\n## {title}\n\n{body.strip()}\n")


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def prepare_wiki_export_fixture(work_dir: Path) -> None:
    write(work_dir / "services/auth/exports.py", """
from dataclasses import dataclass


@dataclass
class Session:
    user_id: str
    token: str


def auth_export_role(user_id: str) -> str:
    return "admin" if user_id.startswith("admin") else "user"
""".strip() + "\n")
    write(work_dir / "api/auth_routes.py", """
from services.auth.exports import auth_export_role


def register_auth_export_routes(router):
    router.get("/api/auth/role/export", auth_export_role)
""".strip() + "\n")
    write(work_dir / "registry/export_registry.py", """
EXPORT_REGISTRY = {
    "auth.role": "auth_export_role",
}
""".strip() + "\n")
    write(work_dir / "tests/test_auth_exports.py", """
from services.auth.exports import auth_export_role
from registry.export_registry import EXPORT_REGISTRY


def test_auth_role_export_is_registered():
    assert auth_export_role("admin-1") == "admin"
    assert EXPORT_REGISTRY["auth.role"] == "auth_export_role"
""".strip() + "\n")
    write(work_dir / "README.md", """
# Export Fixture

Auth exports are exposed through three synchronized places: service functions,
API route registration, and the central export registry. The local wiki records
this as a cross-cut operation so implementation can use it as a miss-prevention
map, then verify the current code before editing.
""".strip() + "\n")
    write(work_dir / "pytest.ini", """
[pytest]
pythonpath = .
""".strip() + "\n")
    write(work_dir / ".wiki/index.md", """
---
title: Wiki Index
description: Export fixture wiki navigation entry
tags: [index, wiki, export]
type: entity
summary: Links module and cross-cut pages for export implementation.
last_updated: 2026-05-07
---

# Wiki Index

## 模块（type: module）

- [[Modules/Auth exports]] — Auth export service contract and current naming.

## 跨模块同步改动（type: cross_cut）

- [[CrossCut/新增导出]] — 新增导出能力时必须同步检查 service、route、registry、tests。
""".strip() + "\n")
    write(work_dir / ".wiki/Modules/index.md", """
---
title: Modules Index
description: Module wiki page index for export fixture
tags: [index, module, export]
type: entity
summary: Lists module notes for export fixture.
last_updated: 2026-05-07
---

# Modules Index

- [[Auth exports]] — Auth export service contract and current naming.
""".strip() + "\n")
    write(work_dir / ".wiki/Modules/Auth exports.md", """
---
title: Auth exports
description: Auth service export naming and public contract
tags: [module, auth, exports]
type: module
summary: Auth exports use the `auth_export_*` prefix and are exposed through routes and registry entries.
last_updated: 2026-05-07
locators:
  - services/auth/exports.py
  - api/auth_routes.py
  - registry/export_registry.py
---

# Auth exports

Auth module exports live in `services/auth/exports.py` and use the `auth_export_*` prefix.
Public exports are wired through `api/auth_routes.py` and `registry/export_registry.py`.

相关 cross-cut：[[CrossCut/新增导出]]。
""".strip() + "\n")
    write(work_dir / ".wiki/CrossCut/index.md", """
---
title: CrossCut Index
description: Cross-cut wiki page index for export fixture
tags: [index, cross-cut, export]
type: entity
summary: Lists cross-cut operation notes for export fixture.
last_updated: 2026-05-07
---

# CrossCut Index

- [[新增导出]] — 新增导出能力时必须同步检查 service、route、registry、tests。
""".strip() + "\n")
    write(work_dir / ".wiki/CrossCut/新增导出.md", """
---
title: 新增导出
description: 新增导出函数时需要同步修改的位置和命名规则
tags: [cross-cut, exports, auth]
type: cross_cut
summary: 新增 auth 导出时同步检查 service function、API route、EXPORT_REGISTRY、pytest 覆盖。
last_updated: 2026-05-07
locators:
  - services/auth/exports.py
  - api/auth_routes.py
  - registry/export_registry.py
  - tests/test_auth_exports.py
---

# 新增导出

## 适用场景

当需求是“新增一个对外导出能力”时，用本页防漏；具体产品范围仍以 PRD 为准。

## 同步修改位置

- `services/auth/exports.py`：新增 `auth_export_*` service function 和必要的数据结构；本 fixture 的 session 导出函数名固定为 `auth_export_user_session`。
- `api/auth_routes.py`：在 `register_auth_export_routes` 里注册对应 HTTP path。
- `registry/export_registry.py`：在 `EXPORT_REGISTRY` 增加稳定 key 到函数名的映射；session 使用 `"auth.session": "auth_export_user_session"`。
- `tests/test_auth_exports.py`：覆盖函数行为、registry wiring 和 route wiring。

## 命名规则

Auth 模块沿用 `auth_export_<noun>`，registry key 沿用 `auth.<noun>`，route 沿用 `/api/auth/<noun>/export`。本 fixture 的 session 导出函数名固定为 `auth_export_user_session`，registry value 固定为 `auth_export_user_session`。

## 使用要求

Brainstorm 可在 PRD Technical Framing 中引用本页作为防漏入口，但必须写明核心 scope 和 fallback：若 wiki 与当前代码不一致，impl 调研代码逐一识别。
Impl 读取本页后必须验证路径和注册机制仍存在，再修改代码。

相关 module：[[Modules/Auth exports]]。
""".strip() + "\n")


def prepare_workdir() -> ScenarioPaths:
    run_dir = unique_run_dir()
    run_dir.mkdir(parents=True, exist_ok=False)
    work_dir = run_dir / "project"
    if SCENARIO.name == "wiki-cross-cut-export-integration":
        work_dir.mkdir()
        prepare_wiki_export_fixture(work_dir)
    elif SCENARIO.profile.startswith("greenfield-"):
        work_dir.mkdir()
        (work_dir / ".gitkeep").write_text("", encoding="utf-8")
    else:
        shutil.copytree(FIXTURE_DIR, work_dir)

    env = os.environ.copy()
    env.update({
        "GIT_AUTHOR_NAME": "sdd-kit scenario",
        "GIT_AUTHOR_EMAIL": "scenario@example.invalid",
        "GIT_COMMITTER_NAME": "sdd-kit scenario",
        "GIT_COMMITTER_EMAIL": "scenario@example.invalid",
    })
    for command in (["git", "init", "-q"], ["git", "add", "-A"], ["git", "commit", "-q", "-m", "init"]):
        subprocess.run(command, cwd=work_dir, env=env, check=True)

    paths = ScenarioPaths(
        run_dir=run_dir,
        work_dir=work_dir,
        transcript_path=run_dir / "transcript.jsonl",
        dialogue_path=run_dir / "dialogue.md",
        summary_path=run_dir / "summary.json",
        events_path=run_dir / "events.jsonl",
        test_report_path=work_dir / "test.md",
    )
    paths.dialogue_path.write_text(
        f"# Scenario dialogue — {SCENARIO.name}\n\n"
        f"- 时间：{timestamp()}\n"
        f"- Profile：{SCENARIO.profile}\n"
        f"- Model：{DEFAULT_MODEL}\n"
        f"- AI user model：{AI_USER_MODEL}\n\n",
        encoding="utf-8",
    )
    log_event(paths, "workdir_prepared", run_dir=str(run_dir), work_dir=str(work_dir))
    return paths


def extract_question(input_data: dict[str, Any]) -> str:
    questions = input_data.get("questions")
    if isinstance(questions, list) and questions:
        question = questions[0]
        if isinstance(question, dict):
            text = question.get("question") or ""
            options = question.get("options") or []
            option_lines = []
            for option in options:
                if not isinstance(option, dict):
                    continue
                label = option.get("label", "")
                description = option.get("description", "")
                option_lines.append(f"- {label}: {description}".strip())
            if option_lines:
                return f"{text}\n选项:\n" + "\n".join(option_lines)
            return str(text)
    return json.dumps(input_data, ensure_ascii=False)


def scenario_brief() -> str:
    profiles = {
        "existing-small": "存量项目中的小需求：一个局部功能或行为调整，应能在少量文件内完成。",
        "existing-medium": "存量项目中的中等需求：需要理解现有模块边界，可能涉及 API、数据模型、测试和少量配置。",
        "existing-large": "存量项目中的大需求：需要拆分多个交付 slice，明确边界、依赖、风险和阶段验收。",
        "existing-wiki-export": "存量项目中的 wiki 集成需求：已有 `.wiki/` cross_cut 页面，需求应触发 brainstorm/impl 按需查询并验证 wiki。",
        "greenfield-small": "从零开始的小项目：一个单用途工具或轻量应用，范围要清楚。",
        "greenfield-medium": "从零开始的中等项目：有核心领域模型、用户流程、数据存储和测试策略。",
        "greenfield-large": "从零开始的大项目：复杂产品或平台，需要规划多个 slice、非功能需求和上线边界。",
    }
    return profiles.get(SCENARIO.profile, profiles["existing-medium"])


def initial_prompt(user_request: str) -> str:
    if SCENARIO.name == "wiki-cross-cut-export-integration":
        return f"用 brainstorm grill-me {user_request}\n\n这个项目已有 `.wiki/`；如果需求涉及已有 module 或 cross-cut 模式，请按 brainstorm skill 先用 `sdd-arbor wiki-collect --query \"新增 导出 auth session\" --limit 5 --json` 渐进式查询，不要全量读取 wiki。PRD Technical Framing 应引用实际命中的 cross_cut 页面，核心 scope 保持自包含，并写 wiki 与当前代码不一致时由 impl 逐一识别的 fallback。"
    return f"用 brainstorm grill-me {user_request}"


def impl_prompt(prd_path: Path | None) -> str:
    if prd_path:
        prompt = f"用 impl 执行这个 package PRD：{prd_path.parent.name}"
        if SCENARIO.name == "wiki-cross-cut-export-integration":
            prompt += "\n\n如果 PRD Technical Framing 引用了 wiki cross_cut 页面，请按 impl skill 先用 wiki-collect 定位页面、只读相关页面、验证路径和注册机制仍适用于当前代码，再实现。"
        return prompt
    return "用 impl 执行当前 ready package"


def wiki_export_initial_request() -> str:
    return (
        "帮我在现有 auth 导出系统里新增 user session 导出能力：输入 user_id，返回带 token 的 Session，"
        "新增函数名使用 `auth_export_user_session`，对外暴露 `/api/auth/session/export`，并进入现有 EXPORT_REGISTRY，"
        "测试要覆盖函数行为、registry wiring 和 route wiring。"
    )


def fallback_initial_request() -> str:
    if SCENARIO.name == "wiki-cross-cut-export-integration":
        return wiki_export_initial_request()
    if SCENARIO.profile.startswith("greenfield-"):
        return "帮我从零设计一个中等复杂度的个人管理 Web 工具。"
    return "帮我在这个 AI 客服多渠道系统里增加消息处理可靠性和可观测能力。"


def fallback_answer(question_text: str) -> str:
    lowered = question_text.lower()
    if "模式" in question_text or "grill-me" in lowered:
        return "选择 grill-me。"
    if SCENARIO.name == "wiki-cross-cut-export-integration":
        if "定稿" in question_text or "finalize" in lowered or "调用 `sdd-arbor finalize-brainstorm`" in question_text:
            return "确认定稿；函数名固定为 `auth_export_user_session`，采用确定性 token `session-{user_id}`，route wiring 也需要显式测试。"
        if "函数名" in question_text or "命名" in question_text:
            return "函数名固定使用 `auth_export_user_session`，registry value 也使用 `auth_export_user_session`。"
        if "route" in lowered and "测试" in question_text:
            return "需要显式测试 route wiring；请覆盖 `/api/auth/session/export` 注册到 `auth_export_user_session`，同时保留既有 role route。"
        if "token" in lowered or "session.token" in lowered or "生成语义" in question_text:
            return "确认采用确定性 token：`Session.token = f\"session-{user_id}\"`。函数名使用 `auth_export_user_session`；不要接入真实 token 签发，也不要只做非空断言。"
    if "确认" in question_text or "定稿" in question_text or "finalize" in lowered:
        return "如果 PRD 已经没有 blocking open question，并且验收标准和 slices 都明确，就确认定稿；否则请继续追问未决项。"
    return "按你的推荐方向推进；如果需要业务取舍，请选择更适合当前场景范围和交付质量的方案。"


async def ask_ai_user(
    prompt: str,
    paths: ScenarioPaths,
    fallback: str,
    event_prefix: str,
    turn: int | None = None,
    max_chars: int = 900,
) -> str:
    from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, ClaudeSDKClient, ResultMessage, TextBlock

    if AI_USER_MODE != "agent":
        log_event(paths, f"{event_prefix}_scripted_answer", turn=turn, answer=fallback)
        return fallback

    log_event(paths, f"{event_prefix}_agent_start", turn=turn)
    client = ClaudeSDKClient(ClaudeAgentOptions(
        permission_mode="bypassPermissions",
        max_turns=3,
        model=AI_USER_MODEL,
        stderr=lambda line: log_event(paths, "ai_user_stderr", line=line.strip()),
    ))
    result_text = ""
    try:
        await asyncio.wait_for(client.connect(), timeout=int(os.environ.get("SCENARIO_CONNECT_TIMEOUT", "20")))
        await asyncio.wait_for(client.query(prompt), timeout=int(os.environ.get("SCENARIO_QUERY_TIMEOUT", "20")))
        async with asyncio.timeout(int(os.environ.get("SCENARIO_AI_USER_TIMEOUT", "60"))):
            async for msg in client.receive_response():
                if isinstance(msg, AssistantMessage):
                    result_text += "".join(block.text for block in msg.content if isinstance(block, TextBlock))
                elif isinstance(msg, ResultMessage):
                    if msg.is_error:
                        log_event(paths, f"{event_prefix}_agent_error", turn=turn, result=msg.result)
                    elif msg.result and not result_text.strip():
                        result_text = msg.result
                    break
    except TimeoutError:
        log_event(paths, f"{event_prefix}_agent_timeout", turn=turn)
        return fallback
    finally:
        await client.disconnect()

    answer = result_text.strip() or fallback
    if len(answer) > max_chars:
        answer = answer[:max_chars].rsplit("\n", 1)[0].strip()
    log_event(paths, f"{event_prefix}_agent_answer", turn=turn, answer=answer)
    return answer or fallback


async def ai_user_initial_request(paths: ScenarioPaths) -> str:
    if SCENARIO.name == "wiki-cross-cut-export-integration":
        request = wiki_export_initial_request()
        log_event(paths, "ai_user_initial_scripted_request", request=request)
        return request

    prompt = f"""
你是一次 workflow eval 的用户侧产品负责人。请根据下面场景，提出一个真实、具体、适合该场景强度的顶层需求，作为你对 brainstorm skill 说的第一句话。

场景强度：{SCENARIO.profile}
场景说明：{scenario_brief()}
项目背景：{SCENARIO.project_brief}
组织约束：{SCENARIO.org_context}

要求：
- 只输出一句自然的用户需求，不要解释测试身份。
- 需求由你自己决定，但后续访谈要能围绕它稳定展开。
- 存量项目场景下，需求必须适合上述项目背景，不要编造无关产品界面或业务领域。
- 新项目场景下，提出一个从零开始的新产品/工具需求。
- 不要写 PRD，不要列实现计划。
""".strip()
    return await ask_ai_user(prompt, paths, fallback_initial_request(), "ai_user_initial", max_chars=360)


async def ai_user_answer(question_text: str, transcript: list[dict[str, Any]], paths: ScenarioPaths) -> str:
    prompt = f"""
你在一次真实产品需求访谈中扮演用户侧：一位有经验、但不会替实现者做设计的产品负责人。

场景强度：{SCENARIO.profile}
场景说明：{scenario_brief()}
项目背景：{SCENARIO.project_brief}
组织约束：{SCENARIO.org_context}

你的目标：像真实产品 owner 一样回答问题，让对方通过追问逐步收敛 PRD。具体需求已经在对话中提出，你必须保持一致，不要每轮换一个需求；存量项目回答不能脱离项目背景。

回答风格：
- 只回答当前问题，不反问，不解释测试身份。
- 答案自然、具体、稳定，能进入 PRD；避免模板化测试词。
- 如果问题提供选项，明确选择一个最符合你需求的选项，再补一句业务理由。
- 如果对方要求确认定稿，但问题文本里仍显示有 blocking/open question、占位符或未决验收项，不要确认；要求继续追问这些未决项。
- 你可以接受对方推荐，但如果推荐偏离你的业务目标，要明确修正。
- 不要替对方写 PRD，不要列完整实现计划；只提供真实用户会知道的业务信息和约束。
- 组织约束不要主动塞给对方；只有当前问题涉及环境、依赖、测试、运行或本机污染风险时才自然补充。

最近对话记录：
{json.dumps(transcript[-6:], ensure_ascii=False, indent=2)}

当前问题：
{question_text}
""".strip()
    return await ask_ai_user(
        prompt,
        paths,
        fallback_answer(question_text),
        "ai_user_answer",
        turn=len(transcript) + 1,
    )


def find_prd(work_dir: Path) -> Path | None:
    prd_files = sorted(work_dir.glob(".arbor/tasks/*/prd.md"))
    return prd_files[0] if prd_files else None


def read_task_state(prd_path: Path | None) -> dict[str, Any] | None:
    if prd_path is None:
        return None
    task_path = prd_path.with_name("task.json")
    if not task_path.exists():
        return None
    return json.loads(task_path.read_text(encoding="utf-8"))


_SLICE_HEADER_PATTERN = re.compile(r"^### S-\d{3}:", re.MULTILINE)
_LEGACY_SLICE_CHECKBOX_PATTERN = re.compile(r"^- \[[ x\-]\] S-\d{3}", re.MULTILINE)
_SLICE_SCAFFOLD_TOKENS = (
    "<walking skeleton 或第一个独立可验证的契约/功能>",
    "<扩展某个契约/功能/行为/状态转换>",
    "<回归 / 边界 / 自检切片>",
    "<完成后多了什么可独立验证的契约/功能/行为>",
    "Impl 只更新 [ ] / [-] / [x]",
)
_OPEN_QUESTIONS_SECTION_RE = re.compile(
    r"^#{2,}\s*Open [Qq]uestions\b.*?(?=^#{2,}\s|\Z)",
    re.MULTILINE | re.DOTALL,
)
_NEGATIVE_BLOCKING_RE = re.compile(
    r"^\s*-?\s*(?:无|暂无|没有|not\s+applicable|n/?a|none|no)\s+(?:any\s+)?blocking\s+open\s+questions?\b[^\n]*$",
    re.IGNORECASE | re.MULTILINE,
)
_BLOCKING_WORD_RE = re.compile(r"(?:^|[^a-zA-Z-])blocking", re.IGNORECASE)
_IMPL_ACTIVE_SLICE_STATES = frozenset({"doing", "in_progress", "done"})


def _detect_blocking_open_question(prd_text: str) -> bool:
    """Scan only within `## Open Questions` sections for a non-negated blocking reference.

    Any PRD discussion of `blocking` outside Open Questions (e.g. Interview Log
    narrating "confirmed first batch of blocking questions") must not trigger this check.
    """
    sections = [m.group(0) for m in _OPEN_QUESTIONS_SECTION_RE.finditer(prd_text)]
    if not sections:
        return False
    joined = "\n".join(sections)
    filtered = _NEGATIVE_BLOCKING_RE.sub("", joined)
    if "Blocking:" in filtered:
        return True
    return bool(_BLOCKING_WORD_RE.search(filtered))


_TEMPLATE_PLACEHOLDER_RE = re.compile(r"<([^>\n]+)>")
_ALLOWED_ANGLE_BRACKET_TOKENS = {"noun", "输入"}


def _has_template_placeholder(prd_text: str) -> bool:
    for match in _TEMPLATE_PLACEHOLDER_RE.finditer(prd_text):
        token = match.group(1).strip()
        if token in _ALLOWED_ANGLE_BRACKET_TOKENS:
            continue
        return True
    return False


def _is_task_state_ready(task_state: dict[str, Any] | None) -> bool:
    """Whether durable package state has advanced to `prd.status == "ready"`.

    Kept as a small helper so the runner can rely on durable state instead of
    assistant text in every branch of the brainstorm loop.
    """
    if not task_state:
        return False
    prd = task_state.get("prd")
    if not isinstance(prd, dict):
        return False
    return prd.get("status") == "ready"


def _derive_impl_started(task_state: dict[str, Any] | None) -> bool:
    """Impl is 'started' whenever task.json evidences any impl-phase activity.

    Source of truth is the package state file, never a runner-local bool,
    because the runner's brainstorm loop may time out after finalize even
    though impl has already advanced slices.
    """
    if not task_state:
        return False
    if task_state.get("current_phase") == "impl":
        return True
    if task_state.get("state") in ("doing", "done"):
        return True
    if task_state.get("impl_result"):
        return True
    for entry in task_state.get("slices") or []:
        if entry.get("status") in _IMPL_ACTIVE_SLICE_STATES:
            return True
    return False


def _slice_progress(task_state: dict[str, Any] | None) -> dict[str, Any]:
    slices = (task_state or {}).get("slices") or []
    total = len(slices)
    done = sum(1 for s in slices if s.get("status") == "done")
    in_progress = sum(1 for s in slices if s.get("status") in ("doing", "in_progress"))
    impl_result = (task_state or {}).get("impl_result")
    return {
        "slices_total": total,
        "slices_done_count": done,
        "slices_in_progress_count": in_progress,
        "impl_in_progress": bool((done > 0 or in_progress > 0) and not impl_result),
    }


def _read_text_if_exists(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _wiki_integration_checks(work_dir: Path, prd_text: str) -> dict[str, bool]:
    if SCENARIO.name != "wiki-cross-cut-export-integration":
        return {}

    events_text = _read_text_if_exists(work_dir.parent / "events.jsonl")
    dialogue_text = _read_text_if_exists(work_dir.parent / "dialogue.md")
    combined_trace = events_text + "\n" + dialogue_text
    prd_has_wikilink = "[[CrossCut/新增导出]]" in prd_text or "[[新增导出]]" in prd_text
    service_text = _read_text_if_exists(work_dir / "services/auth/exports.py")
    routes_text = _read_text_if_exists(work_dir / "api/auth_routes.py")
    registry_text = _read_text_if_exists(work_dir / "registry/export_registry.py")
    tests_text = _read_text_if_exists(work_dir / "tests/test_auth_exports.py")
    all_wiki_pages = list((work_dir / ".wiki").rglob("*.md")) if (work_dir / ".wiki").exists() else []
    read_wiki_count = sum(1 for page in all_wiki_pages if page.as_posix() in combined_trace)

    return {
        "wiki_brainstorm_collect_used": "wiki-collect" in combined_trace and "新增" in combined_trace and "导出" in combined_trace,
        "wiki_prd_references_cross_cut": prd_has_wikilink,
        "wiki_prd_has_fallback": prd_has_wikilink and ("fallback" in prd_text.lower() or "与现状不一致" in prd_text or "逐一识别" in prd_text),
        "wiki_prd_scope_self_contained": all(token in prd_text for token in ("session", "Session", "EXPORT_REGISTRY")) and "/api/auth/session/export" in prd_text,
        "wiki_trace_not_blind_read_all": read_wiki_count < len(all_wiki_pages) if all_wiki_pages else False,
        "wiki_impl_service_updated": "auth_export_user_session" in service_text and "token" in service_text,
        "wiki_impl_route_updated": "/api/auth/session/export" in routes_text and "auth_export_user_session" in routes_text,
        "wiki_impl_registry_updated": "auth.session" in registry_text and "auth_export_user_session" in registry_text,
        "wiki_impl_tests_updated": "auth_export_user_session" in tests_text and "auth.session" in tests_text,
    }


def quality_checks(prd_text: str, turns: int, task_state: dict[str, Any] | None = None, work_dir: Path | None = None) -> dict[str, Any]:
    has_slice_headers = bool(_SLICE_HEADER_PATTERN.search(prd_text))
    has_completion_markers = "完成标志" in prd_text
    has_legacy_slice_checkboxes = bool(_LEGACY_SLICE_CHECKBOX_PATTERN.search(prd_text))
    has_slice_scaffold = any(tok in prd_text for tok in _SLICE_SCAFFOLD_TOKENS)
    checks = {
        "multi_turn": turns >= 3 or SCENARIO.name == "wiki-cross-cut-export-integration",
        "has_technical_framing": "Technical Framing" in prd_text,
        "has_slices": (
            "## Slices" in prd_text
            and has_slice_headers
            and has_completion_markers
            and not has_legacy_slice_checkboxes
            and not has_slice_scaffold
        ),
        "has_legacy_slice_checkboxes": has_legacy_slice_checkboxes,
        "has_slice_scaffold": has_slice_scaffold,
        "has_acceptance_criteria": "Acceptance Criteria" in prd_text or "验收" in prd_text,
        "has_existing_code_anchor": True if SCENARIO.profile.startswith("greenfield-") else "现有" in prd_text or "existing" in prd_text.lower() or "src/" in prd_text or "services/" in prd_text,
        "has_template_placeholder": _has_template_placeholder(prd_text),
        "has_blocking_open_question": _detect_blocking_open_question(prd_text),
        "package_ready": bool(task_state and task_state.get("prd", {}).get("status") == "ready"),
        "impl_recorded": bool(task_state and task_state.get("impl_result")),
    }
    if work_dir is not None:
        checks.update(_wiki_integration_checks(work_dir, prd_text))
    hard_pass = (
        checks["multi_turn"]
        and checks["has_technical_framing"]
        and checks["has_slices"]
        and checks["has_acceptance_criteria"]
        and checks["has_existing_code_anchor"]
    )
    if SCENARIO.name == "wiki-cross-cut-export-integration":
        hard_pass = hard_pass and all(
            checks.get(key)
            for key in (
                "wiki_brainstorm_collect_used",
                "wiki_prd_references_cross_cut",
                "wiki_prd_has_fallback",
                "wiki_prd_scope_self_contained",
                "wiki_trace_not_blind_read_all",
                "wiki_impl_service_updated",
                "wiki_impl_route_updated",
                "wiki_impl_registry_updated",
                "wiki_impl_tests_updated",
            )
        )
    if not prd_text:
        verdict = "failed_to_run"
    elif hard_pass and checks["package_ready"] and checks["impl_recorded"] and not checks["has_template_placeholder"] and not checks["has_blocking_open_question"]:
        verdict = "pass"
    elif hard_pass:
        verdict = "needs_review"
    elif SCENARIO.name == "wiki-cross-cut-export-integration" and any(checks.get(key) for key in ("wiki_brainstorm_collect_used", "wiki_prd_references_cross_cut", "wiki_impl_service_updated")):
        verdict = "needs_review"
    else:
        verdict = "failed"
    return {"verdict": verdict, "checks": checks}


def response_timeout_for_phase(phase: str) -> int:
    if phase == "impl":
        return int(os.environ.get("SCENARIO_IMPL_RESPONSE_TIMEOUT", "2400"))
    return int(
        os.environ.get(
            "SCENARIO_BRAINSTORM_RESPONSE_TIMEOUT",
            os.environ.get("SCENARIO_RESPONSE_TIMEOUT", "900"),
        )
    )


def _message_preview(message: Any) -> str:
    return repr(message)[:1000]


def _has_brainstorm_ready_text_marker(response_text: str) -> bool:
    lowered_response = response_text.lower()
    return (
        "finalized:" in lowered_response
        or "已定稿并写入 ready package" in response_text
        or "已定稿为 ready package" in response_text
    )


async def receive_tested_response(client: Any, paths: ScenarioPaths, phase: str) -> tuple[str, str | None, dict[str, Any] | None]:
    from claude_agent_sdk import AssistantMessage, ResultMessage, SystemMessage, TextBlock

    response_text = ""
    response_error: str | None = None
    response_retry: dict[str, Any] | None = None
    async with asyncio.timeout(response_timeout_for_phase(phase)):
        async for msg in client.receive_response():
            if isinstance(msg, SystemMessage):
                subtype = msg.subtype
                data = msg.data or {}
                if subtype == "api_retry":
                    response_retry = data
                    log_event(
                        paths,
                        "tested_agent_api_retry",
                        phase=phase,
                        attempt=data.get("attempt"),
                        max_retries=data.get("max_retries"),
                        error_status=data.get("error_status"),
                        error=data.get("error"),
                        retry_delay_ms=data.get("retry_delay_ms"),
                    )
                else:
                    log_event(paths, "tested_agent_system", phase=phase, subtype=subtype)
                continue

            log_event(
                paths,
                "tested_agent_message",
                phase=phase,
                message_type=type(msg).__name__,
                preview=_message_preview(msg),
            )

            if isinstance(msg, AssistantMessage):
                text = "".join(block.text for block in msg.content if isinstance(block, TextBlock))
                if text:
                    response_text += text
                    log_event(paths, "tested_agent_assistant_message", phase=phase, chars=len(text))
                continue

            if isinstance(msg, ResultMessage):
                log_event(paths, "tested_agent_result", phase=phase, is_error=msg.is_error, duration_ms=msg.duration_ms)
                if msg.is_error:
                    response_error = msg.result or "ResultMessage reported an error."
                elif msg.result and not response_text.strip():
                    response_text = msg.result
                break
    return response_text.strip(), response_error, response_retry


async def run_scenario(paths: ScenarioPaths) -> dict[str, Any]:
    from claude_agent_sdk import (
        ClaudeAgentOptions,
        ClaudeSDKClient,
        PermissionResultAllow,
        PermissionResultDeny,
        SdkPluginConfig,
    )

    transcript: list[dict[str, Any]] = []

    async def auto_answer(tool_name: str, input_data: dict[str, Any], context: Any) -> PermissionResultAllow:
        if tool_name != "AskUserQuestion":
            return PermissionResultAllow(updated_input=input_data)

        question_text = extract_question(input_data)
        log_event(paths, "ask_user_question_denied", turn=len(transcript) + 1, question=question_text)
        return PermissionResultDeny(
            message=(
                "Scenario eval uses real conversational user replies. "
                "Ask the same question in normal assistant text instead of using AskUserQuestion."
            ),
            interrupt=False,
        )

    client = ClaudeSDKClient(ClaudeAgentOptions(
        cwd=str(paths.work_dir),
        plugins=[SdkPluginConfig(type="local", path=str(PLUGIN_ROOT))],
        permission_mode="bypassPermissions",
        can_use_tool=auto_answer,
        max_turns=int(os.environ.get("SCENARIO_MAX_TURNS", "140")),
        model=DEFAULT_MODEL,
        stderr=lambda line: log_event(paths, "tested_agent_stderr", line=line.strip()),
    ))

    result_text = ""
    run_error: str | None = None
    last_retry: dict[str, Any] | None = None
    impl_loop_entered = False
    impl_response = ""
    user_request = ""
    try:
        log_event(paths, "tested_agent_connect_start", model=DEFAULT_MODEL, ai_user_mode=AI_USER_MODE)
        await asyncio.wait_for(client.connect(), timeout=int(os.environ.get("SCENARIO_CONNECT_TIMEOUT", "20")))
        log_event(paths, "tested_agent_connected")
        user_request = await ai_user_initial_request(paths)
        append_dialogue(paths, "初始用户需求", user_request)
        prompt = initial_prompt(user_request)
        await asyncio.wait_for(client.query(prompt), timeout=int(os.environ.get("SCENARIO_QUERY_TIMEOUT", "20")))
        log_event(paths, "tested_agent_query_sent", phase="brainstorm", prompt=prompt, user_request=user_request)

        for turn_index in range(1, MAX_CONVERSATION_TURNS + 1):
            response_text, response_error, response_retry = await receive_tested_response(client, paths, "brainstorm")
            if response_retry:
                last_retry = response_retry
            if response_error:
                run_error = response_error
                break

            prd_path_probe = find_prd(paths.work_dir)
            task_state_probe = read_task_state(prd_path_probe)
            task_state_ready = _is_task_state_ready(task_state_probe)

            if not response_text:
                if task_state_ready:
                    append_dialogue(
                        paths,
                        "Brainstorm 完成",
                        "[break reason: task_state_ready_empty_response]",
                    )
                    log_event(
                        paths,
                        "brainstorm_ready_detected",
                        reason="task_state_ready_empty_response",
                    )
                    break
                run_error = "Tested agent returned an empty brainstorm response."
                break

            result_text += response_text
            text_ready_marker = _has_brainstorm_ready_text_marker(response_text)
            if text_ready_marker or task_state_ready:
                break_reason = (
                    "text_marker" if text_ready_marker else "task_state_ready"
                )
                append_dialogue(
                    paths,
                    "Brainstorm 完成",
                    f"[break reason: {break_reason}]\n\n{response_text}",
                )
                log_event(paths, "brainstorm_ready_detected", reason=break_reason)
                break

            answer = await ai_user_answer(response_text, transcript, paths)
            entry = {
                "phase": "brainstorm",
                "turn": len(transcript) + 1,
                "question": response_text,
                "answer": answer,
            }
            transcript.append(entry)
            write_jsonl(paths.transcript_path, entry)
            append_dialogue(paths, f"Brainstorm Turn {entry['turn']}", f"### 被测 agent\n\n{response_text}\n\n### AI user\n\n{answer}")
            log_event(paths, "ai_user_conversation_answer", turn=entry["turn"], answer=answer)
            await asyncio.wait_for(client.query(answer), timeout=int(os.environ.get("SCENARIO_QUERY_TIMEOUT", "20")))
            log_event(paths, "tested_agent_followup_sent", phase="brainstorm", turn=entry["turn"])

        prd_path = find_prd(paths.work_dir)
        task_state = read_task_state(prd_path)
        if task_state and task_state.get("prd", {}).get("status") == "ready":
            impl_loop_entered = True
            impl_user_prompt = impl_prompt(prd_path)
            append_dialogue(paths, "进入 Impl", impl_user_prompt)
            await asyncio.wait_for(client.query(impl_user_prompt), timeout=int(os.environ.get("SCENARIO_QUERY_TIMEOUT", "20")))
            log_event(paths, "tested_agent_query_sent", phase="impl", prompt=impl_user_prompt)
            for impl_turn in range(1, MAX_IMPL_TURNS + 1):
                response_text, response_error, response_retry = await receive_tested_response(client, paths, "impl")
                if response_retry:
                    last_retry = response_retry
                if response_error:
                    run_error = response_error
                    break
                if not response_text:
                    run_error = "Tested agent returned an empty impl response."
                    break
                impl_response += response_text
                append_dialogue(paths, f"Impl response {impl_turn}", response_text)
                prd_path = find_prd(paths.work_dir)
                task_state = read_task_state(prd_path)
                if task_state and task_state.get("impl_result"):
                    break
                lowered_response = response_text.lower()
                if any(marker in lowered_response for marker in ("done_with_concerns", "needs_context", "blocked", "record-impl-result")):
                    break
                if impl_turn >= MAX_IMPL_TURNS:
                    run_error = "Impl reached max response turns without recorded impl_result."
                    break
                await asyncio.wait_for(client.query("继续执行 impl，按 PRD Slices 完成剩余工作；不要询问我，遇到问题按 impl skill 记录结果。"), timeout=int(os.environ.get("SCENARIO_QUERY_TIMEOUT", "20")))
                log_event(paths, "tested_agent_followup_sent", phase="impl", turn=impl_turn)
        else:
            run_error = run_error or "Brainstorm did not produce a ready package; impl was not started."
    except TimeoutError:
        run_error = "Timed out waiting for tested agent response."
        if last_retry:
            run_error += f" Last API retry: {last_retry}"
        log_event(paths, "tested_agent_timeout", error=run_error)
    finally:
        await client.disconnect()
        log_event(paths, "tested_agent_disconnected")

    prd_path = find_prd(paths.work_dir)
    prd_text = prd_path.read_text(encoding="utf-8") if prd_path else ""
    task_state = read_task_state(prd_path)
    check_result = quality_checks(prd_text, len(transcript), task_state, paths.work_dir)
    if run_error:
        if check_result["checks"].get("impl_recorded"):
            run_error = None
        elif check_result["verdict"] == "failed_to_run":
            check_result["verdict"] = "agent_runtime_error"
    summary = {
        "run_dir": str(paths.run_dir),
        "work_dir": str(paths.work_dir),
        "model": DEFAULT_MODEL,
        "ai_user_model": AI_USER_MODEL,
        "ai_user_mode": AI_USER_MODE,
        "scenario_name": SCENARIO.name,
        "scenario_profile": SCENARIO.profile,
        "user_request": user_request,
        "turns": len(transcript),
        "impl_started": _derive_impl_started(task_state),
        "impl_loop_entered": impl_loop_entered,
        **_slice_progress(task_state),
        "prd_path": str(prd_path) if prd_path else None,
        "task_state_path": str(prd_path.with_name("task.json")) if prd_path else None,
        "run_error": run_error,
        "impl_response_preview": impl_response[:2000],
        **check_result,
    }
    paths.summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_test_report(paths, summary, prd_text, task_state)
    return summary


def write_test_report(paths: ScenarioPaths, summary: dict[str, Any], prd_text: str, task_state: dict[str, Any] | None) -> None:
    impl_result = task_state.get("impl_result") if task_state else None
    prd_notes: list[str] = []
    if not summary["checks"].get("package_ready"):
        prd_notes.append("- PRD 没有进入 ready 状态，brainstorm 未完成可执行 package 交付。")
    if summary["checks"].get("has_template_placeholder"):
        prd_notes.append("- PRD 残留模板占位符，说明收尾整理不充分。")
    if summary["checks"].get("has_blocking_open_question"):
        prd_notes.append("- PRD 仍疑似包含 blocking open question，需要人工确认是否误判或真实阻塞。")
    if SCENARIO.name == "wiki-cross-cut-export-integration":
        wiki_failed = [key for key, value in summary["checks"].items() if key.startswith("wiki_") and not value]
        if wiki_failed:
            prd_notes.append("- Wiki 集成检查未通过：" + ", ".join(wiki_failed))
        else:
            prd_notes.append("- Wiki 集成检查通过：brainstorm/impl 使用了 cross_cut 页面、PRD 保持自包含并包含 fallback。")
    if "Requirements (evolving)" in prd_text:
        prd_notes.append("- PRD 仍保留 evolving 区；需要检查正式 section 是否完整，evolving 是否只是历史记录。")
    if not prd_notes:
        prd_notes.append("- PRD 基础结构完整，未发现模板占位符或明显 blocking open question；后续重点看是否足够约束 impl。")

    impl_notes: list[str] = []
    impl_started = summary.get("impl_started")
    impl_loop_entered = summary.get("impl_loop_entered")
    slices_done = summary.get("slices_done_count", 0)
    slices_total = summary.get("slices_total", 0)
    package_ready = summary["checks"].get("package_ready")
    if not impl_started:
        if package_ready:
            impl_notes.append("- Brainstorm 已 ready 但 task.json 未出现 impl 活动；runner 未启动 impl 或 impl 启动后立刻失败。")
        else:
            impl_notes.append("- Impl 未启动：brainstorm 未产出 ready package。")
    elif not impl_loop_entered:
        impl_notes.append("- Impl 已在 task.json 中启动，但 runner 未进入 impl 循环；通常是 brainstorm 循环先一步 timeout。")
    elif not impl_result:
        if slices_done > 0 or summary.get("slices_in_progress_count", 0) > 0:
            impl_notes.append(f"- Impl 已启动并推进 slices（done {slices_done}/{slices_total}），但未记录 impl_result；可能被 runner timeout 中断，应检查 task.json 与 impl.jsonl。")
        else:
            impl_notes.append("- Impl 已启动但未记录 impl_result 且无 slice 进展，需要检查是执行超时、环境阻塞，还是 skill 未按 helper 记录结果。")
    else:
        state = impl_result.get("state") or impl_result.get("status") or "unknown"
        impl_notes.append(f"- Impl 已记录结果：`{state}`（slices {slices_done}/{slices_total}）。需要人工比对实现与 PRD acceptance criteria 是否一致。")

    report = f"""# Scenario Eval Report — {SCENARIO.name}

## 基本信息

- 时间：{timestamp()}
- Profile：{SCENARIO.profile}
- Work dir：`{paths.work_dir}`
- Dialogue：`{paths.dialogue_path.relative_to(paths.work_dir.parent)}`
- Summary：`{paths.summary_path.relative_to(paths.work_dir.parent)}`
- Verdict：`{summary['verdict']}`
- Run error：{summary.get('run_error') or 'N/A'}

## 用户顶层需求

{summary.get('user_request') or 'N/A'}

## 自动检查

```json
{json.dumps(summary.get('checks', {}), ensure_ascii=False, indent=2)}
```

## PRD 质量观察

{chr(10).join(prd_notes)}

## Impl 执行观察

{chr(10).join(impl_notes)}

## 需要人工审稿的问题

- PRD 是否把产品边界、Technical Framing、验收标准和 Slices 写到足够可执行？
- Impl 是否严格执行 PRD scope，还是因为 PRD 不清导致自由发挥 / 漂移？
- 如果发生漂移，根因更像是 PRD 缺字段、Slices 粒度问题、impl skill 执行问题、环境问题，还是 runner 交互问题？
- 是否需要把重复出现的问题沉淀为 helper/check，而不是继续加 prompt 规则？

## Impl result raw

```json
{json.dumps(impl_result, ensure_ascii=False, indent=2) if impl_result else 'null'}
```
"""
    paths.test_report_path.write_text(report, encoding="utf-8")


def print_summary(summary: dict[str, Any]) -> None:
    print(f"Run dir: {summary['run_dir']}")
    print(f"Work dir: {summary['work_dir']}")
    print(f"Scenario: {summary['scenario_name']}")
    print(f"Profile: {summary['scenario_profile']}")
    print(f"Turns: {summary['turns']}")
    print(f"Impl started: {summary['impl_started']} (loop entered: {summary.get('impl_loop_entered')})")
    print(f"Slices: {summary.get('slices_done_count', 0)}/{summary.get('slices_total', 0)} done, {summary.get('slices_in_progress_count', 0)} in progress")
    print(f"PRD: {summary['prd_path']}")
    print(f"Verdict: {summary['verdict']}")
    if summary.get("run_error"):
        print(f"Run error: {summary['run_error']}")
    print("Checks:")
    for name, value in summary["checks"].items():
        print(f"  {name}: {value}")


async def async_main() -> int:
    require_enabled()
    paths = prepare_workdir()
    summary = await run_scenario(paths)
    print_summary(summary)
    return 0 if summary["verdict"] in {"pass", "needs_review"} else 1


def main() -> int:
    try:
        return asyncio.run(async_main())
    except subprocess.CalledProcessError as exc:
        print(f"Command failed: {exc.cmd} (exit {exc.returncode})", file=sys.stderr)
        return exc.returncode or 1


if __name__ == "__main__":
    raise SystemExit(main())

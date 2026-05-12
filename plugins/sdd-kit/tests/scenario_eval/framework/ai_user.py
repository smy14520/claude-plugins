"""AI user agent: generates initial requests and answers brainstorm questions."""
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any

from .fixtures import ScenarioPaths, log_event


PROFILE_DESCRIPTIONS = {
    "existing-small": "存量项目中的小需求：一个局部功能或行为调整，应能在少量文件内完成。",
    "existing-medium": "存量项目中的中等需求：需要理解现有模块边界，可能涉及 API、数据模型、测试和少量配置。",
    "existing-large": "存量项目中的大需求：需要拆分多个交付 slice，明确边界、依赖、风险和阶段验收。",
    "existing-wiki-export": "存量项目中的 wiki 集成需求：已有 `.wiki/` cross_cut 页面，需求应触发 brainstorm/impl 按需查询并验证 wiki。",
    "greenfield-small": "从零开始的小项目：一个单用途工具或轻量应用，范围要清楚。",
    "greenfield-medium": "从零开始的中等项目：有核心领域模型、用户流程、数据存储和测试策略。",
    "greenfield-large": "从零开始的大项目：复杂产品或平台，需要规划多个 slice、非功能需求和上线边界。",
}


def extract_question(input_data: dict[str, Any]) -> str:
    """Extract question text from AskUserQuestion input."""
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


async def generate_initial_request(
    paths: ScenarioPaths,
    profile: str,
    project_brief: str,
    org_context: str,
    api_key: str,
    model: str,
    metrics: dict[str, Any] | None = None,
    base_url: str = "",
) -> str:
    """Generate an initial user request using AI."""
    from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient, AssistantMessage, ResultMessage, TextBlock

    brief_desc = PROFILE_DESCRIPTIONS.get(profile, PROFILE_DESCRIPTIONS["existing-medium"])
    prompt = f"""你是一次 workflow eval 的用户侧产品负责人。请根据下面场景，提出一个真实、具体、适合该场景强度的顶层需求，作为你对 brainstorm skill 说的第一句话。

场景强度：{profile}
场景说明：{brief_desc}
主题种子 / 项目背景：{project_brief}
组织约束：{org_context}

要求：
- 直接说需求，不要说"我想用 brainstorm"之类的 meta 话
- 需求要具体到能开始 brainstorm 追问
- 不要写成 PRD，写成产品负责人口头描述的风格
- 200-400 字"""

    env: dict[str, str] = {}
    if api_key:
        env["ANTHROPIC_API_KEY"] = api_key
    if base_url:
        env["ANTHROPIC_BASE_URL"] = base_url

    client = ClaudeSDKClient(ClaudeAgentOptions(
        cwd=str(paths.work_dir),
        permission_mode="bypassPermissions",
        max_turns=1,
        model=model,
        env=env,
    ))

    result_text = ""
    try:
        await asyncio.wait_for(client.connect(), timeout=20)
        await asyncio.wait_for(client.query(prompt), timeout=20)
        async with asyncio.timeout(60):
            async for msg in client.receive_response():
                if isinstance(msg, AssistantMessage):
                    result_text += "".join(block.text for block in msg.content if isinstance(block, TextBlock))
                elif isinstance(msg, ResultMessage):
                    break
    except TimeoutError:
        log_event(paths, "ai_user_initial_request_timeout")
    finally:
        await client.disconnect()

    return result_text.strip() or f"请帮我做一个{project_brief}相关的项目"


async def generate_answer(
    question_text: str,
    transcript: list[dict[str, Any]],
    paths: ScenarioPaths,
    profile: str,
    project_brief: str,
    org_context: str,
    api_key: str,
    model: str,
    metrics: dict[str, Any] | None = None,
    max_chars: int = 1500,
    base_url: str = "",
) -> str:
    """Generate an AI user answer to a brainstorm question."""
    from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient, AssistantMessage, ResultMessage, TextBlock

    history = "\n".join(
        f"Q{i+1}: {entry.get('question', '')[:200]}\nA{i+1}: {entry.get('answer', '')[:200]}"
        for i, entry in enumerate(transcript[-5:])
    )

    prompt = f"""你是产品负责人，正在和 brainstorm skill 对话。请回答下面的问题。

场景：{PROFILE_DESCRIPTIONS.get(profile, '')}
项目背景：{project_brief}
组织约束：{org_context}

最近对话：
{history}

当前问题：
{question_text}

要求：
- 直接回答问题，给出具体选择和理由
- 如果是多选题，选最合理的选项
- 如果需要补充信息，给出具体细节
- 回答时聚焦"这个版本必须做到什么"，不要用"初版先不做"、"MVP 够用就行"、"后续再增强"来降低交付预期；如果某个能力确实不做，只需说"不做 X"，不要反复强调"初版"或暗示实现可以简化
- 如果对方请求你确认定稿，只说"确认"或给出修改意见；不要指示对方"开始 impl"或"从 S-001 执行"——下一步由系统调度，不是你的职责
- 150-400 字
- 不要反问"""

    fallback = "按你的推荐来，我同意这个方案。"

    env: dict[str, str] = {}
    if api_key:
        env["ANTHROPIC_API_KEY"] = api_key
    if base_url:
        env["ANTHROPIC_BASE_URL"] = base_url

    client = ClaudeSDKClient(ClaudeAgentOptions(
        cwd=str(paths.work_dir),
        permission_mode="bypassPermissions",
        max_turns=1,
        model=model,
        env=env,
    ))

    result_text = ""
    try:
        await asyncio.wait_for(client.connect(), timeout=20)
        await asyncio.wait_for(client.query(prompt), timeout=20)
        async with asyncio.timeout(60):
            async for msg in client.receive_response():
                if isinstance(msg, AssistantMessage):
                    result_text += "".join(block.text for block in msg.content if isinstance(block, TextBlock))
                elif isinstance(msg, ResultMessage):
                    break
    except TimeoutError:
        log_event(paths, "ai_user_answer_timeout")
        return fallback
    finally:
        await client.disconnect()

    answer = result_text.strip() or fallback
    if len(answer) > max_chars:
        answer = answer[:max_chars].rsplit("\n", 1)[0].strip()
    return answer or fallback


def scripted_answer(response_text: str, transcript: list[dict[str, Any]]) -> str:
    """Generate a scripted fallback answer (no AI needed)."""
    turn = len(transcript) + 1
    lowered = response_text.lower()

    # If it looks like a confirmation request near the end
    if any(marker in lowered for marker in ("确认", "定稿", "finalize", "最终")):
        if turn >= 5:
            return "确认，可以定稿。"

    # If it has options, pick the first/recommended one
    if "选项" in response_text or "option" in lowered:
        return "选 A，按推荐方案来。"

    # Generic agreement with slight push
    answers = [
        "同意，按这个方向继续。",
        "可以，这个方案合理。请继续下一个问题。",
        "没问题，我同意你的建议。继续推进。",
        "好的，就这样。还有什么需要确认的？",
        "按你说的来，我没有异议。",
    ]
    return answers[(turn - 1) % len(answers)]


def fallback_answer(question_text: str, scenario_name: str = "") -> str:
    """Deterministic fallback answer based on question content.

    This is the legacy fallback used by the old runner. The scenario_name
    parameter enables wiki-specific answers when needed.
    """
    lowered = question_text.lower()
    if scenario_name == "wiki-cross-cut-export-integration":
        if "定稿" in question_text or "finalize" in lowered or "调用 `sdd-arbor finalize-brainstorm`" in question_text:
            return "确认定稿；函数名固定为 `auth_export_user_session`，采用确定性 token `session-{user_id}`，route wiring 也需要显式测试。"
        if "函数名" in question_text or "命名" in question_text:
            return "函数名固定使用 `auth_export_user_session`，registry value 也使用 `auth_export_user_session`。"
        if "route" in lowered and "测试" in question_text:
            return "需要显式测试 route wiring；请覆盖 `/api/auth/session/export` 注册到 `auth_export_user_session`，同时保留既有 role route。"
        if "token" in lowered or "session.token" in lowered or "生成语义" in question_text:
            return "确认采用确定性 token：`Session.token = f\"session-{user_id}\"`。函数名使用 `auth_export_user_session`；不要接入真实 token 签发，也不要只做非空断言。"
    if "模式" in question_text and "grill-me" in lowered and "推荐" not in question_text:
        return "选择 grill-me。"
    if any(marker in question_text for marker in ("回复 **接受 A**", "回复：**A**", "接受 A", "选项：", "选项")):
        return "接受 A。"
    if "确认" in question_text or "定稿" in question_text or "finalize" in lowered:
        return "确认定稿。"
    if "推荐" in question_text:
        return "采用推荐。"
    return "采用推荐。"

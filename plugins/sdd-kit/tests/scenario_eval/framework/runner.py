"""Low-level Claude Agent SDK connection and message handling."""
from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable


@dataclass
class PhaseResponse:
    text: str = ""
    error: str | None = None
    retry: dict[str, Any] | None = None
    metrics: dict[str, Any] = field(default_factory=dict)


def create_sdd_client(
    work_dir: Path,
    plugin_root: Path,
    model: str,
    phase: str,
    log_fn: Callable[..., None] | None = None,
    isolate_phases: bool = False,
    api_key: str = "",
    base_url: str = "",
) -> Any:
    """Create a ClaudeSDKClient configured for sdd-kit testing."""
    from claude_agent_sdk import (
        ClaudeAgentOptions,
        ClaudeSDKClient,
        PermissionResultAllow,
        PermissionResultDeny,
        SdkPluginConfig,
    )

    async def auto_answer(tool_name: str, input_data: dict[str, Any], context: Any) -> Any:
        if tool_name != "AskUserQuestion":
            return PermissionResultAllow(updated_input=input_data)
        if log_fn:
            log_fn("ask_user_question_denied", question=str(input_data)[:200])
        return PermissionResultDeny(
            message="Scenario eval uses real conversational user replies. Ask in normal text instead of AskUserQuestion.",
            interrupt=False,
        )

    env: dict[str, str] = {}
    if api_key:
        env["ANTHROPIC_API_KEY"] = api_key
    if base_url:
        env["ANTHROPIC_BASE_URL"] = base_url

    return ClaudeSDKClient(ClaudeAgentOptions(
        cwd=str(work_dir),
        plugins=[SdkPluginConfig(type="local", path=str(plugin_root))],
        permission_mode="bypassPermissions",
        can_use_tool=auto_answer,
        max_turns=int(os.environ.get("SCENARIO_MAX_TURNS", "140")),
        model=model,
        env=env,
        stderr=lambda line: log_fn("stderr", line=line.strip()) if log_fn else None,
    ))


def create_direct_client(
    work_dir: Path,
    model: str,
    log_fn: Callable[..., None] | None = None,
    api_key: str = "",
    base_url: str = "",
) -> Any:
    """Create a ClaudeSDKClient for direct (no sdd-kit) testing."""
    from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient

    env: dict[str, str] = {}
    if api_key:
        env["ANTHROPIC_API_KEY"] = api_key
    if base_url:
        env["ANTHROPIC_BASE_URL"] = base_url

    return ClaudeSDKClient(ClaudeAgentOptions(
        cwd=str(work_dir),
        permission_mode="bypassPermissions",
        max_turns=int(os.environ.get("SCENARIO_MAX_TURNS", "140")),
        model=model,
        env=env,
        stderr=lambda line: log_fn("stderr", line=line.strip()) if log_fn else None,
    ))


async def receive_response(client: Any, timeout: int) -> PhaseResponse:
    """Receive a complete response from the agent, handling all message types."""
    from claude_agent_sdk import AssistantMessage, ResultMessage, SystemMessage, TextBlock

    result_text = ""
    result_metrics: dict[str, Any] = {}
    error: str | None = None
    retry: dict[str, Any] | None = None

    try:
        async with asyncio.timeout(timeout):
            async for msg in client.receive_response():
                if isinstance(msg, SystemMessage):
                    subtype = msg.subtype
                    data = msg.data or {}
                    if subtype == "api_retry":
                        retry = data
                    continue

                if isinstance(msg, AssistantMessage):
                    text = "".join(
                        block.text for block in msg.content if isinstance(block, TextBlock)
                    )
                    if text:
                        result_text += text
                    continue

                if isinstance(msg, ResultMessage):
                    result_metrics = extract_result_metrics(msg)
                    if msg.is_error:
                        error = f"Agent error: {msg.result}"
                    elif msg.result and not result_text.strip():
                        result_text = msg.result
                    break
    except TimeoutError:
        error = "Response timeout"
    except Exception as exc:
        exc_str = str(exc)
        if "overloaded" in exc_str.lower() or "retry" in exc_str.lower():
            retry = {"error": exc_str}
            error = f"API retry: {exc_str}"
        else:
            error = f"Unexpected error: {exc_str}"

    return PhaseResponse(text=result_text.strip(), error=error, retry=retry, metrics=result_metrics)


def extract_result_metrics(msg: Any) -> dict[str, Any]:
    """Extract metrics from a ResultMessage."""
    metrics: dict[str, Any] = {}
    for attr in ("duration_ms", "duration_api_ms", "num_turns", "session_id", "total_cost_usd", "usage", "stop_reason"):
        value = getattr(msg, attr, None)
        if value is not None:
            try:
                json.dumps(value)
                metrics[attr] = value
            except TypeError:
                if hasattr(value, "model_dump"):
                    metrics[attr] = value.model_dump()
                elif hasattr(value, "__dict__"):
                    metrics[attr] = vars(value)
                else:
                    metrics[attr] = repr(value)
    return metrics

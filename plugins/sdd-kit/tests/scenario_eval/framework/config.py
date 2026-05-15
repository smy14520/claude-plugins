"""Scenario configuration loading from YAML files and environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml

SCENARIOS_DIR = Path(__file__).resolve().parents[1] / "scenarios"

DEFAULT_ORG_CONTEXT = (
    "如果对方问到开发/测试环境、依赖安装、启动应用或本机环境变更，你的组织约束是："
    "优先使用 Docker / docker-compose 在项目临时工作区内隔离环境；可以要求生成 docker-compose.yml；不要污染当前电脑的全局环境。"
)


@dataclass(frozen=True)
class TimeoutConfig:
    brainstorm_turns: int = 14
    impl_turns: int = 80
    review_turns: int = 20
    direct_turns: int = 80
    response_timeout: int = 900
    connect_timeout: int = 20
    query_timeout: int = 20


@dataclass(frozen=True)
class ChecksConfig:
    required: list[str] = field(default_factory=list)
    optional: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class EvaluationDimension:
    name: str
    prompt: str
    weight: float = 1.0


@dataclass(frozen=True)
class EvaluationConfig:
    enabled: bool = False
    dimensions: list[EvaluationDimension] = field(default_factory=list)


@dataclass(frozen=True)
class ScenarioConfig:
    name: str
    profile: str
    fixture: str  # "empty" | "express-app" | "wiki-export" | path
    request_mode: str  # "fixed" | "ai-generated"
    request_text: str  # the fixed request text (empty if ai-generated)
    ai_user_mode: str  # "scripted" | "agent"
    workflows: list[str] = field(default_factory=lambda: ["sdd-full", "direct"])
    project_brief: str = ""
    org_context: str = DEFAULT_ORG_CONTEXT
    impl_instruction: str = ""  # extra instruction appended to impl prompt
    timeouts: TimeoutConfig = field(default_factory=TimeoutConfig)
    checks: ChecksConfig = field(default_factory=ChecksConfig)
    evaluation: EvaluationConfig = field(default_factory=EvaluationConfig)


@dataclass(frozen=True)
class EnvConfig:
    # Tested agent (Claude Code CLI)
    anthropic_api_key: str = ""
    anthropic_base_url: str = ""  # proxy base URL for tested agent
    test_model: str = "claude-sonnet-4-6"
    # AI user (brainstorm answers)
    ai_user_key: str = ""
    ai_user_base_url: str = ""  # proxy base URL for AI user
    ai_user_model: str = "claude-sonnet-4-6"
    # Judge (evaluation)
    judge_key: str = ""
    judge_base_url: str = ""  # proxy base URL for judge
    judge_model: str = "claude-sonnet-4-6"


def load_env_config() -> EnvConfig:
    """Load from environment with fallbacks."""
    base_key = os.environ.get("ANTHROPIC_API_KEY", "")
    base_url = os.environ.get("ANTHROPIC_BASE_URL", "")
    return EnvConfig(
        anthropic_api_key=base_key,
        anthropic_base_url=base_url,
        test_model=os.environ.get("SCENARIO_TEST_MODEL", "claude-sonnet-4-6"),
        ai_user_key=os.environ.get("EVAL_AI_USER_KEY", base_key),
        ai_user_base_url=os.environ.get("EVAL_AI_USER_BASE_URL", ""),
        ai_user_model=os.environ.get("EVAL_AI_USER_MODEL", "claude-sonnet-4-6"),
        judge_key=os.environ.get("EVAL_JUDGE_KEY", base_key),
        judge_base_url=os.environ.get("EVAL_JUDGE_BASE_URL", ""),
        judge_model=os.environ.get("EVAL_JUDGE_MODEL", "claude-sonnet-4-6"),
    )


def load_scenario(name: str) -> ScenarioConfig:
    """Load a scenario config from scenarios/{name}.yaml."""
    path = SCENARIOS_DIR / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Scenario not found: {path}")

    with path.open(encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    timeouts_raw = raw.get("timeouts", {})
    timeouts = TimeoutConfig(
        brainstorm_turns=timeouts_raw.get("brainstorm_turns", 14),
        impl_turns=timeouts_raw.get("impl_turns", 80),
        review_turns=timeouts_raw.get("review_turns", 20),
        direct_turns=timeouts_raw.get("direct_turns", 80),
        response_timeout=timeouts_raw.get("response_timeout", 300),
        connect_timeout=timeouts_raw.get("connect_timeout", 20),
        query_timeout=timeouts_raw.get("query_timeout", 20),
    )

    checks_raw = raw.get("checks", {})
    checks = ChecksConfig(
        required=checks_raw.get("required", []),
        optional=checks_raw.get("optional", []),
    )

    eval_raw = raw.get("evaluation", {})
    dimensions = [
        EvaluationDimension(
            name=d["name"],
            prompt=d["prompt"],
            weight=d.get("weight", 1.0),
        )
        for d in eval_raw.get("dimensions", [])
    ]
    evaluation = EvaluationConfig(
        enabled=eval_raw.get("enabled", False),
        dimensions=dimensions,
    )

    request_raw = raw.get("request", {})
    ai_user_raw = raw.get("ai_user", {})

    return ScenarioConfig(
        name=name,
        profile=raw.get("profile", "existing-medium"),
        fixture=raw.get("fixture", "express-app"),
        request_mode=request_raw.get("mode", "ai-generated"),
        request_text=request_raw.get("text", "").strip(),
        ai_user_mode=ai_user_raw.get("mode", "agent"),
        workflows=raw.get("workflows", ["sdd-full", "direct"]),
        project_brief=raw.get("project_brief", ""),
        org_context=raw.get("org_context", DEFAULT_ORG_CONTEXT),
        impl_instruction=raw.get("impl_instruction", ""),
        timeouts=timeouts,
        checks=checks,
        evaluation=evaluation,
    )


def list_scenarios() -> list[str]:
    """List available scenario names (YAML files without extension)."""
    if not SCENARIOS_DIR.exists():
        return []
    return sorted(p.stem for p in SCENARIOS_DIR.glob("*.yaml"))

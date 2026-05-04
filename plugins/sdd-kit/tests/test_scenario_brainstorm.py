"""
Scenario test: brainstorm with existing project context.

Uses Claude Agent SDK to run a brainstorm session against a fixture project,
auto-answering AskUserQuestion with scripted responses. Then verifies the
generated PRD artifact contains expected structures.

Requirements:
  - pip install claude-agent-sdk
  - ANTHROPIC_API_KEY set in environment

Run:
  python -m pytest tests/test_scenario_brainstorm.py -v -s
  # or with marker:
  python -m pytest tests/test_scenario_brainstorm.py -v -s -m scenario
"""

import asyncio
import json
import os
import re
import shutil
import unittest
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = PLUGIN_ROOT / "tests" / "fixtures" / "express-app"
# Work on a temp copy so fixture stays clean
WORK_DIR = PLUGIN_ROOT / "tests" / "fixtures" / "_workdir"


def require_sdk():
    """Skip if SDK or API key not available."""
    try:
        import claude_agent_sdk  # noqa: F401
    except ImportError:
        raise unittest.SkipTest("claude-agent-sdk not installed")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise unittest.SkipTest("ANTHROPIC_API_KEY not set")


# -- scripted answers for AskUserQuestion --

SCRIPTED_ANSWERS = [
    # (keyword_in_question, answer)
    ("模式", "grill-me"),
    ("normal", "grill-me"),
    ("grill-me", "grill-me"),
    ("消息", "文字和图片消息"),
    ("内容形态", "文字和图片"),
    ("认证", "复用现有 ChannelAdapter 的 OAuth 流程"),
    ("授权", "复用现有 ChannelAdapter 的 OAuth 流程"),
    ("OAuth", "复用现有 OAuth 流程"),
    ("接入方式", "复用现有 ChannelAdapter，新建 XiaohongshuAdapter"),
    ("适配", "复用现有 ChannelAdapter"),
    ("ChannelAdapter", "复用现有 ChannelAdapter"),
    ("表", "扩展现有 channels 表，加 type='xiaohongshu'"),
    ("数据", "扩展现有 channels 表"),
    ("测试", "核心路径测试"),
    ("test", "核心路径测试"),
    ("Test", "核心路径测试"),
    ("自动回复", "复用现有 AI 自动回复逻辑"),
    ("后台", "在现有渠道管理页新增小红书类型"),
    ("管理", "在现有渠道管理页新增小红书类型"),
    ("范围", "只做小红书渠道接入，不改现有渠道"),
    ("scope", "只做小红书渠道接入"),
    ("纳入", "不纳入"),
    ("确认", "确认定稿"),
    ("定稿", "确认定稿"),
    ("finalize", "确认定稿"),
    ("摘要", "确认"),
]


def match_answer(question_text: str) -> str:
    """Match a scripted answer based on keywords in the question."""
    q = question_text.lower()
    for keyword, answer in SCRIPTED_ANSWERS:
        if keyword.lower() in q:
            return answer
    return "按你的推荐来"


async def run_brainstorm_scenario() -> dict:
    """Run a brainstorm session and return results."""
    from claude_agent_sdk import (
        ClaudeAgentOptions,
        ClaudeSDKClient,
        PermissionResultAllow,
        SdkPluginConfig,
    )

    messages_log = []

    async def auto_answer(tool_name: str, input_data: dict, context) -> PermissionResultAllow:
        """Intercept AskUserQuestion and auto-respond."""
        if tool_name == "AskUserQuestion":
            question_text = json.dumps(input_data, ensure_ascii=False)
            answer = match_answer(question_text)
            messages_log.append({"question": question_text[:200], "answer": answer})
            return PermissionResultAllow(
                updated_input={**input_data, "answer": answer}
            )
        return PermissionResultAllow(updated_input=input_data)

    client = ClaudeSDKClient(ClaudeAgentOptions(
        cwd=str(WORK_DIR),
        plugins=[SdkPluginConfig(type="local", path=str(PLUGIN_ROOT))],
        permission_mode="bypassPermissions",
        can_use_tool=auto_answer,
        max_turns=40,
        model=os.environ.get("SCENARIO_TEST_MODEL", "claude-sonnet-4-20250514"),
    ))

    result_text = ""
    try:
        await client.connect()
        await client.query("用 brainstorm grill-me 为这个 AI 客服系统新增小红书渠道的客服功能")
        async for msg in client.receive_messages():
            if hasattr(msg, "content"):
                result_text += str(msg.content)
    finally:
        await client.disconnect()

    return {
        "messages_log": messages_log,
        "result_text": result_text,
    }


@unittest.skipUnless(
    os.environ.get("RUN_SCENARIO_TESTS"),
    "Set RUN_SCENARIO_TESTS=1 to run scenario tests (uses API credits)",
)
class BrainstormScenarioTests(unittest.TestCase):
    """Test brainstorm behavior against a real fixture project."""

    @classmethod
    def setUpClass(cls):
        require_sdk()
        # Copy fixture to work dir
        if WORK_DIR.exists():
            shutil.rmtree(WORK_DIR)
        shutil.copytree(FIXTURE_DIR, WORK_DIR)
        # Initialize git so Claude Code can work
        os.system(f"cd {WORK_DIR} && git init -q && git add -A && git commit -q -m 'init'")
        # Run the scenario
        cls.scenario_result = asyncio.run(run_brainstorm_scenario())
        # Read generated PRD
        prd_files = list(WORK_DIR.glob(".arbor/tasks/*/prd.md"))
        if prd_files:
            cls.prd_text = prd_files[0].read_text(encoding="utf-8")
            cls.prd_path = prd_files[0]
        else:
            cls.prd_text = ""
            cls.prd_path = None

    @classmethod
    def tearDownClass(cls):
        # Clean up work dir
        if WORK_DIR.exists():
            shutil.rmtree(WORK_DIR)

    def test_prd_was_created(self):
        """Brainstorm should create a PRD file."""
        self.assertTrue(self.prd_path and self.prd_path.exists(),
                        f"PRD not found. Files in .arbor: {list(WORK_DIR.glob('.arbor/**/*'))}")

    def test_prd_has_context_first_analysis(self):
        """PRD should contain analysis of existing code (Context first)."""
        # Should mention existing adapter pattern or channels table
        has_adapter = "ChannelAdapter" in self.prd_text or "Adapter" in self.prd_text
        has_channels = "channels" in self.prd_text
        self.assertTrue(has_adapter or has_channels,
                        "PRD should reference existing code structures (ChannelAdapter or channels table)")

    def test_prd_has_testing_strategy(self):
        """PRD Technical Framing should include testing strategy."""
        has_strategy = (
            "核心路径测试" in self.prd_text
            or "TDD" in self.prd_text
            or "最小验收" in self.prd_text
            or "Testing strategy" in self.prd_text
            or "测试策略" in self.prd_text
        )
        self.assertTrue(has_strategy, "PRD should contain a testing strategy")

    def test_prd_has_technical_framing(self):
        """PRD should have Technical Framing section."""
        self.assertIn("Technical Framing", self.prd_text)

    def test_prd_has_slices(self):
        """PRD should have Slices section."""
        self.assertIn("## Slices", self.prd_text)

    def test_slices_have_technical_anchors(self):
        """Existing project slices should contain technical anchors."""
        slices_match = re.search(r"## Slices\s*\n(.*?)(?=\n##|\Z)", self.prd_text, re.DOTALL)
        if not slices_match:
            self.fail("No Slices section found")
        slices_text = slices_match.group(1)
        # Should mention specific tables, adapters, or modules
        has_anchor = any(kw in slices_text for kw in [
            "channels", "Adapter", "adapter", "webhook", "表", "[existing]", "[new]",
            "XiaohongshuAdapter", "xiaohongshu",
        ])
        self.assertTrue(has_anchor,
                        f"Slices should have technical anchors for existing project. Got:\n{slices_text[:500]}")

    def test_slices_count_reasonable(self):
        """Should have at least 3 slices for this scenario."""
        slice_count = self.prd_text.count("- [ ] S-")
        # Also count completed slices in case brainstorm marks some
        slice_count += self.prd_text.count("- [x] S-")
        self.assertGreaterEqual(slice_count, 3,
                                f"Expected at least 3 slices, got {slice_count}")

    def test_prd_has_acceptance_criteria(self):
        """PRD should have acceptance criteria."""
        has_ac = (
            "Acceptance Criteria" in self.prd_text
            or "验收" in self.prd_text
        )
        self.assertTrue(has_ac, "PRD should have acceptance criteria")

    def test_prd_mentions_existing_patterns(self):
        """PRD should demonstrate understanding of existing codebase patterns."""
        # Should mention the adapter pattern, webhook routing, or channel types
        patterns = [
            "ChannelAdapter", "适配器", "adapter",
            "webhook", "Webhook",
            "wechat", "douyin", "微信", "抖音",
            "单表继承", "type",
        ]
        found = [p for p in patterns if p in self.prd_text]
        self.assertGreaterEqual(len(found), 2,
                                f"PRD should reference existing patterns. Only found: {found}")


if __name__ == "__main__":
    unittest.main()

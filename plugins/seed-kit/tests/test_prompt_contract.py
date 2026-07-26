from __future__ import annotations

import json
import unittest
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]


class SeedPromptContractTests(unittest.TestCase):
    def read_plugin_file(self, *parts: str) -> str:
        return (PLUGIN_ROOT / Path(*parts)).read_text(encoding="utf-8")

    def test_brainstorm_uses_entry_per_behavior(self):
        text = self.read_plugin_file("skills", "brainstorm", "SKILL.md")

        # slice 内联：### [ ] S-NNN heading + 条目
        self.assertIn("### [ ] S-NNN", text)
        self.assertIn("一个 `* [ ]` 一个测试用例", text)
        # 旧 obligation 术语已移除
        self.assertNotIn("obligation", text)
        self.assertNotIn("AC 覆盖", text)
        # 旧 surface 词汇表已下线
        self.assertNotIn("## 交付面", text)
        self.assertNotIn("## 验证面", text)

    def test_brainstorm_checks_history_choices_and_prd_closure(self):
        text = self.read_plugin_file("skills", "brainstorm", "SKILL.md")

        self.assertIn("与需求直接相关的近期提交", text)
        self.assertIn("不做无关历史考古", text)
        self.assertIn("真实分叉", text)
        self.assertIn("2–3 个可行方向", text)
        self.assertIn("不为凑数制造方案", text)
        self.assertIn("inline self-review", text)
        self.assertIn("TBD/TODO", text)
        self.assertIn("自审并修正后，再运行 `seed status <task>`", text)

    def test_prd_template_minimal_sections(self):
        template = self.read_plugin_file("templates", "prd.md")

        # 三段式：Goal / Acceptance Criteria / Out of Scope
        self.assertIn("## Goal", template)
        self.assertIn("## Acceptance Criteria", template)
        self.assertIn("### [ ] S-001", template)
        self.assertIn("## Out of Scope", template)
        self.assertIn("* [ ]", template)
        # 旧 obligation / 品质意图 术语已移除
        self.assertNotIn("obligation", template)
        self.assertNotIn("品质意图", template)

    def test_verification_describes_gate_and_loop(self):
        verification = self.read_plugin_file("skills", "references", "verification.md")

        # gate 只卡硬事实
        self.assertIn("测试命令", verification)
        self.assertIn("质量命令", verification)
        self.assertIn("真实测试框架", verification)
        # loop 守好坏
        self.assertIn("review loop", verification.lower())
        # PRD 结构
        self.assertIn("## Goal", verification)
        self.assertIn("## Acceptance Criteria", verification)
        self.assertIn("## Out of Scope", verification)
        # 条目格式
        self.assertIn("一个 `* [ ]` 一个测试用例", verification)
        self.assertIn("* [ ]", verification)
        # 封闭 kind 词汇：assert / judge / human（概念保留）
        for kind in ("assert", "judge", "human"):
            self.assertIn(kind, verification)
        # 无 obligation 机械约束
        self.assertNotIn("obligation", verification)
        self.assertNotIn("run-check", verification)
        self.assertNotIn("AC 覆盖校验", verification)
        self.assertNotIn("烟雾命令", verification)

    def test_docs_keep_helper_boundary_clear(self):
        design = self.read_plugin_file("DESIGN.md")
        claude = self.read_plugin_file("CLAUDE.md")
        combined = "\n".join([design, claude])

        # helper 只做确定性动作
        self.assertIn("确定性", combined)
        # gate 边界明确——硬事实
        self.assertIn("硬事实", claude)
        # 验收条目必须过
        self.assertIn("验收条目必须过", claude)

    def test_progress_state_distinguishes_records(self):
        readme = self.read_plugin_file("README.md")
        design = self.read_plugin_file("DESIGN.md")
        helper = self.read_plugin_file("tools", "seed.py")
        combined = "\n".join([readme, design, helper])

        self.assertIn("进度 source of truth", readme)
        self.assertIn("done-logs/", readme)
        self.assertIn("review-loop.json", readme)
        self.assertNotIn("唯一状态", combined)
        self.assertNotIn("唯一持久状态", combined)

    def test_design_acknowledges_minimal_satisfaction(self):
        design = self.read_plugin_file("DESIGN.md")
        self.assertIn("诚实地最小满足", design)
        self.assertIn("半成品", design)
        # 公理
        self.assertIn("正确性的 source of truth", design)

    def test_impl_treats_tests_as_floor(self):
        agent = self.read_plugin_file("agents", "seed-impl.md")
        self.assertIn("验收条目必须兑现", agent)
        # 一个 agent 做所有 slice
        self.assertIn("所有 slice", agent)
        # 不弱化断言
        self.assertIn("不弱化断言", agent)
        # 无 provisional verdict（那是旧的 obligation judge 机制）
        self.assertNotIn("provisional", agent.lower())

    def test_impl_keeps_user_owned_branch_and_commit_boundaries(self):
        agent = self.read_plugin_file("agents", "seed-impl.md")
        skill = self.read_plugin_file("skills", "impl", "SKILL.md")

        # 正向 ownership 表述:边界语义不变,措辞不再用禁令
        self.assertIn("分支与提交属于用户", agent)
        self.assertIn("分支与提交属于用户", skill)

    def test_review_agents_read_prd_goal_and_ac(self):
        review = self.read_plugin_file("agents", "seed-review.md")
        judge = self.read_plugin_file("agents", "seed-judge.md")

        # review 读 Goal + 验收条目
        self.assertIn("## Goal", review)
        self.assertIn("DESIGN.md", review)
        # judge 读 PRD 中描述的方向
        self.assertIn("PRD", judge)
        self.assertIn("missed-opportunity", judge)
        # judge 不查 obligation
        self.assertNotIn("[judge] 义务", judge)

    def test_review_loop_command_exists(self):
        cmd = self.read_plugin_file("commands", "review-loop.md")
        workflow = self.read_plugin_file("templates", "review-loop.template.js")

        self.assertIn("review-loop", cmd)
        self.assertIn("客观锚", cmd)
        self.assertIn("不要同时传 `name`", cmd)
        self.assertIn("const REPO = '.'", workflow)
        self.assertNotIn("A.repo", workflow)

    def test_review_only_turn_is_not_forced_into_review_loop(self):
        hooks = json.loads(self.read_plugin_file("hooks", "hooks.json"))["hooks"]
        review = self.read_plugin_file("skills", "review", "SKILL.md")

        self.assertNotIn("Stop", hooks)
        self.assertNotIn("`seed done` 后 PostToolUse hook 软提醒", review)
        self.assertIn("不自动触发下一轮", review)

    def test_review_requires_evidence_before_write_and_fails_closed(self):
        review = self.read_plugin_file("skills", "review", "SKILL.md")

        self.assertIn("写 review 前必须成功读取该 task 的 PRD", review)
        self.assertIn("取证失败时标明 unavailable 并停止猜测", review)
        self.assertIn("不得编造文件、测试", review)
        self.assertIn("真实产物或命令结果", review)

    def test_impl_ownership_keeps_durable_gate_in_main_skill(self):
        skill = self.read_plugin_file("skills", "impl", "SKILL.md")
        agent = self.read_plugin_file("agents", "seed-impl.md")

        self.assertIn("主会话执行 durable gate", skill)
        self.assertIn("属于主会话 skill", agent)
        self.assertIn("PRD checkbox", agent)
        self.assertIn('"commands"', agent)
        self.assertNotIn("docs/PRD", skill)

    def test_impl_agent_orchestrates_per_slice_with_clean_boundaries(self):
        skill = self.read_plugin_file("skills", "impl-agent", "SKILL.md")
        agent = self.read_plugin_file("agents", "seed-slice.md")

        # 编排者角色 + 机器事实驱动（无 phase 自报）+ handoff 衔接
        self.assertIn("编排者", skill)
        self.assertIn("seed next-action", skill)
        self.assertIn("impl-state", skill)
        self.assertIn("handoff", skill)
        self.assertNotIn("_advance", skill)  # 编排依据是机器事实，没有模型自报的 phase 转移
        self.assertIn("reset-attempts", skill)  # 熔断闭环：升级给用户后有显式清零路径
        # durable gate 与 git 边界：slice agent 不碰 gate、不碰 git
        self.assertIn("agent 不调用 `seed done`", skill)
        self.assertIn("不碰 git", skill)
        self.assertIn("指定的那一个 slice", agent)
        self.assertIn("不执行 `git commit`", agent)
        self.assertIn('"handoff"', agent)

    def test_batch2_certified_partial_contract(self):
        """P1 批次 2 部分合并合同(认证依据 run-20260726T081132Z-98223cc328,
        取证 wf_95686eec,结账见 evals-v2 p1b2-impl-agent/CONCLUSION.md):
        (a) A 同步派发条款——control 后台轮询率 3/3 系统性倾向,条款为纠偏,
            去重口径 token -47.9%;(b) impl-agent 快扫删除(D2,improved 证据内);
        (c) 塑形条款(自审/完整感)按 p03 预塑形证据保留——删除须先过 eval。
        未合并部分(B'/C/review 与 brainstorm 侧 D2)留在 candidate/p1-batch2 待各自认证。"""
        impl_skill = self.read_plugin_file("skills", "impl", "SKILL.md")
        impl_agent = self.read_plugin_file("skills", "impl-agent", "SKILL.md")
        seed_impl = self.read_plugin_file("agents", "seed-impl.md")
        seed_slice = self.read_plugin_file("agents", "seed-slice.md")
        seed_review = self.read_plugin_file("agents", "seed-review.md")

        # (a) 同步派发是机制说明,两个编排 SKILL 都要有
        self.assertIn("run_in_background: false", impl_skill)
        self.assertIn("run_in_background: false", impl_agent)
        self.assertNotIn("不要 `run_in_background`", impl_skill)
        # (b) 快扫不得回归
        self.assertNotIn("快扫", impl_agent)
        # (c) 塑形条款保留(p03:预塑形机制,删除未获认证)
        for text in (seed_impl, seed_slice):
            self.assertIn("30s 快速扫描", text)
            self.assertIn("完整感", text)
        self.assertIn("完整感", seed_review)

    def test_naming_registry_includes_impl_agent_family(self):
        conventions = self.read_plugin_file("skills", "references", "conventions.md")
        self.assertIn("seed-kit:impl-agent", conventions)
        self.assertIn("seed-kit:seed-slice", conventions)

    def test_assert_replays_explicit_commands_without_stack_inference(self):
        agent = self.read_plugin_file("agents", "seed-assert.md")
        workflow = self.read_plugin_file("templates", "review-loop.template.js")

        self.assertIn("done-log 优先", agent)
        self.assertIn("assert-unavailable", agent)
        self.assertIn("不枚举配置文件或技术栈", agent)
        self.assertIn("done-logs", workflow)
        self.assertIn("status=assert-unavailable", workflow)
        for stack_file in ("package.json", "Makefile", "pyproject.toml", "Cargo.toml"):
            self.assertNotIn(stack_file, agent)
            self.assertNotIn(stack_file, workflow)

    def test_review_prd_uses_calibrated_independent_agent(self):
        command = self.read_plugin_file("commands", "review-prd.md")
        agent = self.read_plugin_file("agents", "seed-prd-review.md")

        self.assertIn('subagent_type="seed-kit:seed-prd-review"', command)
        for dimension in (
            "completeness", "consistency", "clarity", "scope",
            "falsifiable acceptance criteria", "slice ordering",
            "buildability", "code assumptions",
        ):
            self.assertIn(dimension, agent.lower())
        self.assertIn("只报告", agent)
        self.assertIn("serious gap", agent)
        self.assertIn("不发明项目标准", command)
        self.assertIn("不自动推进", command)
        # 防止 review agent 递归自举（value 实验中 spawnDepth 1→5）
        self.assertIn("Agent", agent.split("---", 2)[1])  # frontmatter disallowedTools
        self.assertIn("禁止再派", agent)
        # 子 agent 只做审查，不接修复任务
        self.assertIn("只传审查任务给 agent", command)
        self.assertIn("只做审查", agent)
        self.assertIn("忽略修复部分", agent)

    def test_no_stack_specific_tools_in_verification(self):
        verification = self.read_plugin_file("skills", "references", "verification.md")
        # 不应硬编码任何技术栈工具名
        self.assertNotIn("Playwright", verification)
        self.assertNotIn("computed-style", verification)
        self.assertNotIn("a11y", verification)
        self.assertNotIn("Pact", verification)
        self.assertNotIn("Unity", verification)
        self.assertNotIn("Unreal", verification)


if __name__ == "__main__":
    unittest.main()

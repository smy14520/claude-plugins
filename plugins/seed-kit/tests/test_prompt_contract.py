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
        self.assertIn("真实分叉", text)
        self.assertIn("2–3 个可行方向", text)
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
        # (b) 快扫不得回归：impl-agent 不自己实现快扫，只委托 seed-kit:check
        #     （"快扫"字样仅允许出现在 check 委托行；执行清单归 check skill）
        quickscan_lines = [ln for ln in impl_agent.splitlines() if "快扫" in ln]
        assert quickscan_lines, "impl-agent 应委托 check（含快扫）"
        assert all("seed-kit:check" in ln for ln in quickscan_lines), (
            "impl-agent 的快扫字样只能出现在 check 委托行："
            + "\n".join(quickscan_lines)
        )
        # (c) B' 隐性期望通道(认证 run-20260726T123412Z + 取证 wf_abdae488:
        #     3/3 场景触发、沉默假设消灭、错误语义具名化;成本 +17.6% 已知)
        brainstorm = self.read_plugin_file("skills", "brainstorm", "SKILL.md")
        verification = self.read_plugin_file("skills", "references", "verification.md")
        self.assertIn("隐性期望", brainstorm)
        self.assertIn("质量期望的载体", verification)
        # (d) brainstorm 负向禁令删除(同认证:被禁行为零出现,禁令冗余)
        self.assertNotIn("不做无关历史考古", brainstorm)
        self.assertNotIn("不为凑数制造方案", brainstorm)
        # (e) 塑形条款保留(p03:预塑形机制,删除未获认证)
        for text in (seed_impl, seed_slice):
            self.assertIn("30s 快速扫描", text)
            self.assertIn("完整感", text)
        self.assertIn("完整感", seed_review)

    def test_ledger_belongs_to_gate_not_review(self):
        """账本闹剧修复合同(取证 cross-plugin-bugfix run-20260730T160455Z:三轮 review-loop
        全部 blocking 为 PRD 簿记而非代码;根因=过程 slice 无交付物 + 子项无人翻 + review 审账本):
        (a) seed done 原子翻 slice 头与区段内条目(seed.py cmd_done);
        (b) PRD 条目必须可验证,过程动作不成条目(模板+impl skill);
        (c) review 兑现层不把 checkbox/done-log 当证据(agent md + 模板内联 prompt 双源同步)。"""
        review = self.read_plugin_file("agents", "seed-review.md")
        workflow = self.read_plugin_file("templates", "review-loop.template.js")
        template = self.read_plugin_file("templates", "prd.md")
        impl = self.read_plugin_file("skills", "impl", "SKILL.md")
        for text in (review, workflow):
            self.assertIn("不作为兑现证据", text)
        for text in (template, impl):
            self.assertIn("过程动作", text)
        self.assertIn("不手工勾选", template)

    def test_oos_owned_by_user_and_check_closes_claim_gap(self):
        """AC6 漏做修复合同(取证 approval-hard 四臂对比:agent 想到进阶规则却单方写进 OoS,
        访谈锚定骨架/review-loop 只审兑现/QA 外部追问三层防线全部失守;
        p1b2b:"review 期检测缺口的最优修复点在 spec 期"):
        (a) 排除必须用户拍板——模板标注 + brainstorm 确认动作 + seed status 硬校验(见 test_seed);
        (b) 收敛后对照题面——独立 check skill,impl 收尾默认调用,双形态;
        机制只含"声称逐条有归属"与"排除必须用户确认"两条抽象纪律,不带取证场景业务词。"""
        template = self.read_plugin_file("templates", "prd.md")
        brainstorm = self.read_plugin_file("skills", "brainstorm", "SKILL.md")
        check = self.read_plugin_file("skills", "check", "SKILL.md")
        impl = self.read_plugin_file("skills", "impl", "SKILL.md")
        conventions = self.read_plugin_file("skills", "references", "conventions.md")
        # (a) 排除归用户拍板
        for text in (template, brainstorm):
            self.assertIn("（用户确认）", text)
        self.assertIn("排除是用户的决策", brainstorm)
        # (b) check：对照的是原始需求不是 PRD，缺口交用户，不单方排除
        self.assertIn("原始需求", check)
        self.assertIn("归属", check)
        self.assertIn("不能用收敛结果审收敛结果", check)
        self.assertIn("seed-kit:check", impl)
        self.assertIn("seed-kit:check", conventions)
        # 防过拟合：机制层不携带取证场景的业务词与场景形态词
        for text in (template, check):
            for word in ("审批", "超时转交", "驳回", "档位"):
                self.assertNotIn(word, text)

    def test_default_review_is_single_agent_and_deep_review_is_enhanced(self):
        """审查分层合同(依据 review-loop-impl-quality 取证:5 agent 深审成本确定上升、
        +1.7pp 收益与噪音不可区分,降为增强项):
        (a) impl 收尾默认 = check + 单 agent 审查,落 --depth single;
        (b) review-loop(5 agent)与 judge 是增强项,用户显式点名才跑;
        (c) marker 记录审查深度,converged 不字面说谎(见 test_seed depth 断言)。"""
        impl = self.read_plugin_file("skills", "impl", "SKILL.md")
        check = self.read_plugin_file("skills", "check", "SKILL.md")
        review_loop = self.read_plugin_file("commands", "review-loop.md")
        self.assertIn("单 agent", impl)
        self.assertIn("增强项", impl)
        self.assertIn("--depth single", impl)
        self.assertIn("review-loop", check)
        # 增强项入口保留完整能力(5 agent 编排模板不因降级而删减)
        self.assertIn("validator", review_loop)

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

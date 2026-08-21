from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PLUGIN_ROOT.parent.parent


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
        self.assertIn("## Design", template)
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
        conventions = self.read_plugin_file("skills", "references", "conventions.md")
        helper = self.read_plugin_file("tools", "seed.py")
        combined = "\n".join([readme, design, helper])

        # 目录树/文件职责的唯一权威在 conventions「目录」；README 只留指针
        self.assertIn("进度 source of truth", conventions)
        self.assertIn("done-logs/", conventions)
        self.assertIn("review-loop.json", conventions)
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
        self.assertIn("不传 `name`", cmd)
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

    def test_batch2_certified_partial_contract(self):
        """P1 批次 2 部分合并合同(认证依据 run-20260726T081132Z-98223cc328,
        取证 wf_95686eec,结账见 evals-v2 p1b2-impl-agent/CONCLUSION.md):
        (a) A 同步派发条款——control 后台轮询率 3/3 系统性倾向,条款为纠偏,
            去重口径 token -47.9%;(c) 塑形条款(自审/完整感)按 p03 预塑形证据保留——
            删除须先过 eval。impl-agent/seed-slice 侧断言随 unify-impl-dossier 删除移除。"""
        impl_skill = self.read_plugin_file("skills", "impl", "SKILL.md")
        seed_impl = self.read_plugin_file("agents", "seed-impl.md")
        seed_review = self.read_plugin_file("agents", "seed-review.md")

        # (a) 同步派发是机制说明,编排 SKILL 要有
        self.assertIn("run_in_background: false", impl_skill)
        self.assertNotIn("不要 `run_in_background`", impl_skill)
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
        # 注:断言跟随 e51c34c 自审压缩后的实际措辞——"30s 快速扫描"已并入"自审"步骤
        self.assertIn("自审", seed_impl)
        self.assertIn("完整感", seed_impl)
        self.assertIn("方向对账", seed_review)

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
        (b) 收敛后对照题面——check skill 是对照协议 source of truth,impl 收尾按其清单内联执行,双形态;
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

    def test_default_finish_is_inline_and_deep_review_is_enhanced(self):
        """收尾分层合同(依据 review-loop-impl-quality 取证:5 agent 深审成本确定上升、
        +1.7pp 收益与噪音不可区分,降为增强项;impl 收尾为编排者内联自查,升级通道保留):
        (a) impl 收尾默认 = 内联自查(题面对照 + 兑现对账 + 关键假设外显),落 --depth inline;
        (b) 升级通道保留(用户点名触发,不自动派)——派 seed-review 干净 context 审,落 --depth single;
        (c) review-loop(5 agent)与 judge 是增强项,用户显式点名才跑,落 --depth full;
        (d) marker 记录审查深度,converged 不字面说谎(见 test_seed depth 断言)。"""
        impl = self.read_plugin_file("skills", "impl", "SKILL.md")
        check = self.read_plugin_file("skills", "check", "SKILL.md")
        conventions = self.read_plugin_file("skills", "references", "conventions.md")
        review_loop = self.read_plugin_file("commands", "review-loop.md")
        # (a) 内联自查:自己做、不 dispatch,假设外显,marker 落 inline
        self.assertIn("收尾自查", impl)
        self.assertIn("不派 agent", impl)
        self.assertIn("关键假设", impl)
        self.assertIn("--depth inline", impl)
        # (b) 升级通道未被删:干净 context 单 agent 审,落 single;触发靠通用原则而非 overfit 类目清单
        self.assertIn("干净 context", impl)
        self.assertIn("--depth single", impl)
        self.assertIn("盲点", impl)
        # (b3) blocking 分层:实现层(AC没兑现/没测试/偷懒签名/测试挂)直接修不停;
        #      只有决策层(缺口未拍板/AC歧义/动scope/AC错)修不掉才停报用户——避免把可修的甩给用户
        self.assertIn("决策层", impl)
        self.assertIn("实现层", impl)
        # (c) 增强项入口保留完整能力(5 agent 编排模板不因降级而删减),marker 落 full
        self.assertIn("增强项", impl)
        self.assertIn("validator", review_loop)
        self.assertIn("--depth full", review_loop)
        # (d) depth 词汇表三值,conventions 登记
        self.assertIn("inline|single|full", conventions)
        self.assertIn("review-loop", check)

    def test_naming_registry_matches_shipped_skills_and_agents(self):
        """登记表与实际资产对齐：存活名在册，已删名不残留（unify-impl-dossier）。"""
        conventions = self.read_plugin_file("skills", "references", "conventions.md")
        for alive in ("seed-kit:impl", "seed-kit:check", "seed-kit:review-loop", "seed-kit:seed-impl"):
            self.assertIn(alive, conventions)
        for dead in ("seed-kit:impl-agent", "seed-kit:seed-slice"):
            self.assertNotIn(dead, conventions)

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

    def test_review_standards_check_contract(self):
        """准则对照合同：review 环节（独立 + 主会话内联）必须读项目质量标准并逐条对照。
        统一条款在 conventions.md；check 清单承载职责三；impl 收尾、
        seed-review 产出各自落地。防止"review 只对账 PRD 不对照准则"的默认路径缺口回归。"""
        conventions = self.read_plugin_file("skills", "references", "conventions.md")
        check = self.read_plugin_file("skills", "check", "SKILL.md")
        impl = self.read_plugin_file("skills", "impl", "SKILL.md")
        review = self.read_plugin_file("agents", "seed-review.md")

        # 统一条款：对照范围（diff 触及的准则）+ 产出合同（遵守/违反 + 证据）+ 处置（用户拍板）
        self.assertIn("准则对照", conventions)
        self.assertIn("遵守/违反", conventions)
        self.assertIn("该插件的 CLAUDE.md", conventions)
        self.assertIn("报告用户拍板，不单方定", conventions)
        # check 清单承载职责三（impl 收尾内联执行）
        self.assertIn("职责三：准则对照", check)
        self.assertIn("遵守/违反", check)
        self.assertIn("报告用户拍板", check)
        # impl 收尾步骤 3
        self.assertIn("**3. 准则对照**", impl)
        self.assertIn("职责三执行", impl)
        # seed-review 产出：准则对照结论进 summary
        self.assertIn("准则对照结论", review)

    # --- prototype-wayfinder 合同 --------------------------------------------------

    def test_seed_prototype_agent_contract(self):
        """seed-prototype agent 合同：两类入口（编排派发 + 用户语义点名）、两分支（问题决定形态）、
        铁律（自包含单 HTML / 无持久化 / 全量状态 / 结论折真代码本体不进交付）。
        栈特定框架词禁入——判定式：对所有技术栈同等成立才留插件。"""
        agent = self.read_plugin_file("agents", "seed-prototype.md")

        # description 覆盖两类入口
        self.assertIn("被 brainstorm / wayfinder 编排派发", agent)
        self.assertIn('用户点名"使用 prototype"时主会话直接派发', agent)
        # 两分支，问题决定形态
        self.assertIn("逻辑走查", agent)
        self.assertIn("UI 变体切换面板", agent)
        self.assertIn("问题决定形态", agent)
        # 铁律
        self.assertIn(".arbor/prototypes/<slug>/", agent)
        self.assertIn("自包含单 HTML", agent)
        self.assertIn("默认无持久化", agent)
        self.assertIn("每次交互后展示全量状态", agent)
        self.assertIn("原型本体不进交付", agent)
        # 栈特定框架词禁入（反向）
        for word in ("React", "Vue", "Svelte", "Angular", "Playwright",
                     "Vite", "webpack", "jest", "cypress", "tailwind"):
            self.assertNotIn(word, agent)

    def test_brainstorm_dispatches_prototype_and_routes_map(self):
        """brainstorm 接缝合同：体验方向分支派 seed-prototype（verdict 折进访谈）；
        入场分流（大到装不下/雾里 → 先开图）+ 收敛入口（图清后读票不重问）。"""
        text = self.read_plugin_file("skills", "brainstorm", "SKILL.md")

        # prototype 派发线
        self.assertIn("形容词吵不出结果", text)
        self.assertIn("seed-prototype", text)
        self.assertIn(".arbor/prototypes/<slug>/", text)
        self.assertIn("verdict", text)
        # wayfinder 分流线 + 收敛入口
        self.assertIn("开图还是直接访谈", text)
        self.assertIn("当场进入 wayfinder", text)  # B 档：建议→用户确认→当场进入，无需 slash 重点名
        self.assertIn("## Resolution", text)
        self.assertIn("不重问", text)

    def test_brainstorm_tracer_s001_and_auto_prd_review(self):
        """接缝合同（候补，待 eval 认证）：S-001 踩遍 Design 整体层承诺——防"承诺了无人实例化"
        的双源漂移；PRD 定稿后自动派 seed-prd-review——逐项对账成为默认工序。"""
        text = self.read_plugin_file("skills", "brainstorm", "SKILL.md")
        # 垂直切：英文原文可判定措辞 + 层点名下放 + tracer 穿层
        self.assertIn("vertical, NOT a horizontal slice of one layer", text)
        self.assertIn("demoable or verifiable on its own", text)
        self.assertIn("列出本任务会触及的全部层", text)
        self.assertIn("S-001 是 tracer bullet", text)
        # 自发明的可证伪理由已删除（API 层可测试时禁令失锚）
        self.assertNotIn("中段没有任何东西可验证", text)
        # 切片方案显式呈现仪式
        self.assertIn("每片一句话", text)
        # 自动 PRD 独立审查（B 档例外）
        self.assertIn("自动派 `seed-prd-review`", text)
        agent = self.read_plugin_file("agents", "seed-prd-review.md")
        self.assertIn("逐项对账", agent)
        self.assertIn("逐片判层", agent)
        self.assertIn("存在只是及格线", agent)
        self.assertNotIn("模拟横切", agent)
        self.assertNotIn("逐层横读", agent)
        # 流转原则四处同步
        conventions = self.read_plugin_file("skills", "references", "conventions.md")
        self.assertIn("默认收尾工序，自动派发不待点名", conventions)

    def test_wayfinder_map_and_ticket_format(self):
        """wayfinder 合同（形态）：map.md 五节 + 票文件格式
        （frontmatter type/status/blocked-by + Question/Resolution 两节）；helper 面 new/status 成文。"""
        skill = self.read_plugin_file("skills", "wayfinder", "SKILL.md")
        template = self.read_plugin_file("templates", "map.md")
        conventions = self.read_plugin_file("skills", "references", "conventions.md")

        for section in ("## Destination", "## Notes", "## Decisions so far",
                        "## Not yet specified", "## Out of scope"):
            self.assertIn(section, skill)
            self.assertIn(section, template)
        # 票格式
        self.assertIn("type: research | prototype | grilling | task", skill)
        self.assertIn("status: open | closed", skill)
        self.assertIn("blocked-by", skill)
        self.assertIn("## Question", skill)
        self.assertIn("## Resolution", skill)
        # helper 面：new / status 两个子命令，frontier 从盘上推导
        self.assertIn("seed map new <slug>", skill)
        self.assertIn("seed map status", skill)
        self.assertIn("从盘上推导", skill)
        self.assertIn("seed map new <slug>", conventions)
        self.assertIn("seed map status <slug> [--json]", conventions)

    def test_wayfinder_ticket_types_and_discipline(self):
        """wayfinder 合同（分工与纪律）：四票型执行分工（grilling 走提问通道 / research 轻重分流 /
        prototype 派 agent / task 记事实）；HITL 票 agent 不代答；一会话一票；图清三条件交棒。"""
        skill = self.read_plugin_file("skills", "wayfinder", "SKILL.md")

        for ticket_type in ("grilling", "research", "prototype", "task"):
            self.assertIn(f"**{ticket_type}**", skill)
        # grilling：brainstorm 提问通道（AskUserQuestion 一次一题）
        self.assertIn("AskUserQuestion 一次一题", skill)
        # research：轻调查派 sub-agent、重调查建 research 工作区
        self.assertIn("sub-agent", skill)
        self.assertIn(".arbor/research/<topic>/", skill)
        # prototype：派 seed-prototype，verdict 写 Resolution
        self.assertIn("seed-prototype", skill)
        # task：Resolution 记录做了什么与产生的事实（供下游票引用）
        self.assertIn("凭据位置", skill)
        # HITL 边界：agent 不得代替用户作答
        self.assertIn("HITL 票 agent 不得代替用户作答", skill)
        # 会话纪律：一会话一票（research 例外可并行）
        self.assertIn("一会话只解决一张票", skill)
        self.assertIn("research 例外", skill)
        # 图清 = 三条件 → 建议转 brainstorm 收敛，不自动进 impl
        self.assertIn("frontier 空 + 雾区（Not yet specified）空 + 全票 closed", skill)
        self.assertIn("impl 是重操作", skill)

    def test_wayfinder_ledger_separation(self):
        """账本分离合同（反向语义）：票是决策账本，不是交付账本——
        不进 seed done、不翻 PRD checkbox、不是 slice；.arbor/maps/ 不构成第二套进度，图清即冻结。"""
        skill = self.read_plugin_file("skills", "wayfinder", "SKILL.md")
        design = self.read_plugin_file("DESIGN.md")

        self.assertIn("票不进 `seed done`", skill)
        self.assertIn("不翻 PRD checkbox", skill)
        self.assertIn("不是 slice", skill)
        self.assertIn("不构成第二套进度", skill)
        self.assertIn("图清即冻结", skill)
        # 收票是 agent 语义动作，helper 保持只读（map 子命令族无其他写操作）
        self.assertIn("helper 保持只读", skill)
        # 设计原则层：两套账本分离成文
        self.assertIn("两套账本严格分离", design)

    def test_directory_ledger_reconciles_with_disk(self):
        """目录对账：conventions 登记表 ↔ 磁盘 skills/（含 SKILL.md 的目录）、agents/、commands/ 逐项一致（双向）。
        登记表人为删去任一条目时本测试红——红灯演示记录见
        .arbor/tasks/prototype-wayfinder/notes/red-demo.md。"""
        conventions = self.read_plugin_file("skills", "references", "conventions.md")

        disk_skills = sorted(p.parent.name for p in (PLUGIN_ROOT / "skills").glob("*/SKILL.md"))
        disk_agents = sorted(p.stem for p in (PLUGIN_ROOT / "agents").glob("*.md"))
        disk_commands = sorted(p.stem for p in (PLUGIN_ROOT / "commands").glob("*.md"))
        self.assertTrue(disk_skills and disk_agents and disk_commands)  # 采集本身不能空转

        # 磁盘 → 登记表：磁盘上存在的实体必须登记（漏登记 = 红）
        for name in disk_skills + disk_agents + disk_commands:
            self.assertIn(f"seed-kit:{name}", conventions)

        # 登记表 → 磁盘：登记的调用名必须真实存在（幽灵登记 = 红）
        registered = set(re.findall(r"seed-kit:([a-z][a-z-]*)", conventions))
        valid = set(disk_skills) | set(disk_agents) | set(disk_commands)
        ghosts = registered - valid
        self.assertFalse(ghosts, f"登记表引用了磁盘上不存在的调用名：{sorted(ghosts)}")

    def test_skill_count_ledgers_match_disk(self):
        """数量对账：六处账本（plugin.json / marketplace.json / 根 README / DESIGN.md /
        插件 README / conventions）的 skill 数量与清单和磁盘 skills/ 目录一致，过时数量词全部清除。
        磁盘数量变化时各账本必须同步——写死数字而不改账本会红。"""
        disk_skills = sorted(p.parent.name for p in (PLUGIN_ROOT / "skills").glob("*/SKILL.md"))
        cn_num = {9: "九", 10: "十", 11: "十一", 12: "十二"}.get(len(disk_skills))
        self.assertIsNotNone(cn_num, "skill 数超出预设数量词映射，请同步更新本测试")

        conventions = self.read_plugin_file("skills", "references", "conventions.md")
        plugin_readme = self.read_plugin_file("README.md")
        design = self.read_plugin_file("DESIGN.md")
        root_readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        marketplace = (REPO_ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8")
        plugin_json = self.read_plugin_file(".claude-plugin", "plugin.json")

        # conventions：数量词 + 括号列举与磁盘集合完全一致（双向）
        match = re.search(r"个 skill（([^）]+)）", conventions)
        self.assertIsNotNone(match, "conventions 应有「N 个 skill（列举…）」形态的数量声明")
        listed = [x.strip() for x in match.group(1).split("、") if x.strip()]
        self.assertEqual(
            sorted(listed), disk_skills,
            f"conventions 列举 {sorted(listed)} ≠ 磁盘 {disk_skills}",
        )
        self.assertIn(f"{cn_num}个 skill", conventions)
        # 插件 README：标题数量词 + 表格行与磁盘一一对应
        self.assertIn(f"## {cn_num}个 skill", plugin_readme)
        section = plugin_readme.split(f"## {cn_num}个 skill", 1)[1].split("\n## ", 1)[0]
        rows = [ln for ln in section.splitlines()
                if ln.startswith("|") and "---" not in ln and not ln.startswith("| skill ")]
        self.assertEqual(len(rows), len(disk_skills), f"README 表格 {len(rows)} 行 ≠ 磁盘 {len(disk_skills)} 个 skill")
        for row in rows:
            name = row.split("|")[1].strip()
            self.assertIn(name, disk_skills)
        # 根 README 数量词一致
        self.assertIn(f"{cn_num}个 skill", root_readme)
        # plugin.json 指向 skills/ 目录（清单由目录承载，不复制名单）
        self.assertEqual(json.loads(plugin_json)["skills"], ["./skills/"])
        # 过时数量词全部清除（六处）
        stale = ("五个 skill", "六个 skill", "九个 skill", "five skill", "six skill", "nine skill")
        for text in (conventions, plugin_readme, design, root_readme, marketplace, plugin_json):
            for word in stale:
                self.assertNotIn(word, text, f"{word} 是过时数量词，应修整为与磁盘一致")


if __name__ == "__main__":
    unittest.main()

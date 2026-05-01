# sdd-kit

**SDD Kit** 是轻量的 skill-first 工作流插件：用 `research? → brainstorm → map? → task → impl → review` 把模糊需求收敛成可执行 package，并用 `sdd-arbor` 维护确定性状态。

## 核心流程

```text
research? → brainstorm → map? → task → impl → review
```

- `research`：index-first 需求探索；有来源地收敛理解，不做最终方案。
- `brainstorm`：需求澄清与 design framing；小需求写 executable package PRD，大边界交给 `map`。
- `map`：可选的大项目 package graph / dependency / contract 导航；不执行、不自动派 team。
- `task`：对已确认 package 做 T-xxx 拆解、context 写入和 definition freeze。
- `impl`：执行单个 package-local T-xxx，跑 SelfCheck，记录结构化实现结果。
- `review`：只读语义审计 PRD + task + diff + evidence，输出四态 verdict。

阶段之间不自动跳转；wiki 写入也必须显式触发。

## 状态边界

- `.arbor/`：workflow source of truth。package lifecycle、map、context、review 状态都由 `sdd-arbor` helper 维护。
- `.wiki/`：project-local orientation/index layer。用于 module note、summary、locator 和关联检索；实现或 review 前必须回到代码和 `.arbor` 验证。
- code：实现 source of truth。`impl` 改代码；`review` 审 diff；wiki 不替代代码事实。

Package 是需求 / 评审 / 回滚边界；`T-xxx` 是 package-local control / acceptance / review 单元，不默认对应 branch/PR。

## 常用入口

自然语言显式触发或 slash command 均可：

```text
用 research skill 调研 <topic>
用 brainstorm skill 收敛 <package>
用 map skill 维护 <initiative>
用 task skill 拆 <package>
用 impl skill 执行 <package> 的 T-001
用 review skill 审计 <package> 的 T-001
用 prep command 批量准备 <initiative>
用 run command 按队列实现 <initiative> --autonomous
用 wiki skill query / ingest / lint <content>
用 doctor 检查当前 sdd-kit 项目状态
用 rules 访谈并推荐项目规则
这个 review 用 Team Auto 开多 agent 看看
```

Slash command：`/sdd-kit:research`、`/sdd-kit:brainstorm`、`/sdd-kit:map`、`/sdd-kit:task`、`/sdd-kit:impl`、`/sdd-kit:review`、`/sdd-kit:prep`、`/sdd-kit:run`、`/sdd-kit:wiki`、`/sdd-kit:doctor`、`/sdd-kit:rules`、`/sdd-kit:team-auto`。

`prep/run` 是显式 command：只在用户调用 `/sdd-kit:prep` 或 `/sdd-kit:run` 时触发，用来批量编排既有阶段；不替代单个 package 的 `brainstorm/task/impl/review`。

## `sdd-arbor` helper

`sdd-arbor` 只做机械状态读写、校验和检索；不判断需求范围、不写 PRD、不做 review 结论、不启动 agent。参数以 `sdd-arbor <subcommand> --help` 为准。

常用命令：

```text
sdd-arbor doctor
sdd-arbor create <package> --title "<title>"
sdd-arbor set-package-sizing <package> --status fits_package --actor brainstorm --phase brainstorm --decision "..."
sdd-arbor create-map <initiative> --title "<title>"
sdd-arbor create-split-packages <initiative> --package "<package>::<title>::<deps>::<reason>" --decision "..."
sdd-arbor map-check <initiative> --json
sdd-arbor record-contract-request <initiative> --consumer <b> --producer <a> --request "..." --status open
sdd-arbor add-child <package> --id T-001 --title "ADD ..." --milestone M-01 --role shared
sdd-arbor add-context-batch <package> --type impl --entry-json '{"task_id":"T-001","kind":"note","summary":"..."}'
sdd-arbor freeze-definition <package> --actor task --note "frozen"
sdd-arbor record-impl-result <package> --task T-001 --state done --summary "..." --acceptance "..." --command "..."
sdd-arbor record-review <package> --task T-001 --state approved --summary "..." --evidence "..."
sdd-arbor module-summary <package> --initiative <initiative> --json
sdd-arbor wiki-collect --query "balance refund" --limit 5 --json
sdd-arbor wiki-lint --json
sdd-arbor validate --all --json
```

## Team Auto

`team-auto` 是会话层 Agent Team playbook，不是 workflow 阶段，也不是 parallel runtime。只有用户明确说 Team Auto / 多 agent / 开 team / 双推 / 辩论 / review panel 时才触发；默认先根据当前任务给 2–4 个定制阵型选项。

## 目录

```text
plugins/sdd-kit/
├── skills/                 # skill prompts and references
├── tools/arbor.py          # stable CLI entrypoint
├── tools/arbor_core/       # deterministic helper implementation
├── hooks/arbor_guard.py    # optional narrow guardrail
└── tests/test_arbor.py     # helper regression tests
```

## 设计原则

- 少即是多：workflow 骨架轻，避免把 prompt 写成补丁列表。
- Skill 负责阶段语义；`sdd-arbor` 负责机械动作；hook 只守底线。
- 可重复状态问题优先做 helper / validation，而不是增加口头规则。
- `.wiki` 只作导航层；隐藏目录原始状态（如 `.arbor/`、`.claude/`、`.git/`）不整理进 wiki，明确稳定 helper 输出除外。

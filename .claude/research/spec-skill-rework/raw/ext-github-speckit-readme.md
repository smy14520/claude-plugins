---
url: https://raw.githubusercontent.com/github/spec-kit/main/README.md
tool: read_url_content
fetched_at: 2026-04-21 21:30
---

# GitHub SpecKit README 关键摘录

> 原文是 SpecKit 的完整 README(较长)。仅摘录与本研究(spec 模板结构 / 约束表达)相关的段落。

---

## 核心哲学

```
Spec-Driven Development is a structured process that emphasizes:

- **Intent-driven development** where specifications define the "*what*" before the "*how*"
- **Rich specification creation** using guardrails and organizational principles
- **Multi-step refinement** rather than one-shot code generation from prompts
- **Heavy reliance** on advanced AI model capabilities for specification interpretation
```

**观察**:SpecKit 把"spec 先于 how"作为第一条哲学。这和 sdd-kit 的理念完全一致。

## 五阶段命令(通过 `/speckit.*` slash commands)

```
/speckit.constitution    # 确立项目原则(governance)
/speckit.specify         # 写 spec
/speckit.clarify         # 澄清未决问题(结构化问答)
/speckit.plan            # 生成技术实现计划
/speckit.tasks           # 拆解任务
/speckit.implement       # 执行实现
```

**观察**:
- SpecKit 有 **constitution** 层(sdd-kit 无) —— 项目级别的原则文档,spec 起草时作为约束
- SpecKit 有 **clarify** 作为独立命令(sdd-kit 的 spec skill 用 Decide 原语完成类似职责)
- SpecKit 保留了 plan 阶段(sdd-kit 拆成 spec + task 两层,无 plan)

## 目录产物结构

```
└── .specify
    ├── memory
    │  └── constitution.md              # 项目原则
    ├── scripts
    │  └── ...
    ├── specs
    │  └── 001-create-taskify           # 每个 feature 一个目录
    │      ├── contracts
    │      │  ├── api-spec.json
    │      │  └── signalr-spec.md
    │      ├── data-model.md
    │      ├── plan.md                  # 技术计划
    │      ├── quickstart.md
    │      ├── research.md              # 研究笔记
    │      └── spec.md                  # 功能 spec
    └── templates
        ├── plan-template.md
        ├── spec-template.md
        └── tasks-template.md
```

**关键观察**:
- 每个 feature 一个**目录**(而非单文件),包含多份相关文档
- spec / plan / tasks / research / contracts / data-model **分别存在独立文件**
- 这和 sdd-kit 的"一个 feature = 一个 spec.md + 一个 tasks.md"是**不同粒度选择**
- SpecKit 粒度更细,但文件更多;sdd-kit 更紧凑,但信息密度更高

## "Independent Test" 哲学(来自 STEP 2 + spec-template)

```
Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement
just ONE of them, you should still have a viable MVP...

Developed independently / Tested independently / Deployed independently /
Demonstrated to users independently
```

**观察**:"独立可测" 是 SpecKit 的核心设计约束。每个 User Story 都必须是一个独立的 MVP 切片。

## Clarification 阶段(STEP 3)

```
You should run the structured clarification workflow BEFORE creating a technical plan
to reduce rework downstream.

Preferred order:
1. Use `/speckit.clarify` (structured) – sequential, coverage-based questioning
   that records answers in a Clarifications section.
2. Optionally follow up with ad-hoc free-form refinement if something still feels vague.

If you intentionally want to skip clarification (e.g., spike or exploratory prototype),
explicitly state that so the agent doesn't block on missing clarifications.
```

**观察**:
- clarify 作为一个**独立阶段**,写 spec 和定 plan 之间强制一轮澄清
- 答案记录在 spec 的 "Clarifications section" —— 专用章节
- 支持显式"skip clarify"的逃生出口(exploratory prototype 场景)

## Review & Acceptance Checklist

```
Ask Claude Code to validate the **Review & Acceptance Checklist**,
checking off the things that are validated/pass the requirements...
```

**观察**:SpecKit 对 spec 内嵌了一个"review 清单",每条可 check。agent 起草后再走一遍 checklist,类似我们的 Finalize 检查,但做成了 spec 内部的一段结构。

## 技术栈解耦

```
STEP 2: Create project specifications
> IMPORTANT: Be as explicit as possible about *what* you are trying to build and *why*.
> **Do not focus on the tech stack at this point**.

STEP 4: Generate a plan
> You can now be specific about the tech stack and other technical requirements.
```

**观察**:SpecKit **明确在 spec 阶段禁止技术栈选型**,技术栈留到 plan 阶段。这和 sdd-kit 的 "Hard constraints 可以包含速率限制/SLO 但不应过度指定 Redis/Postgres" 同一方向,但 SpecKit 执行得更绝对。

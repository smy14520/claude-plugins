---
name: brainstorm
description: "产出可直接供 task 拆解的 PRD/context 文档 `.claude/brainstorms/<name>.md`，显式记录 research / 本地文件 / 外部 URL 来源。仅在用户显式请求时激活。"
---

# Brainstorm — 可拆解 PRD / Context Artifact

产出 `.claude/brainstorms/<name>.md`。它不是 project-level 长期规范，而是**单次 feature / change 的收敛文档**：帮助用户把需求、范围、场景、交付物、风险和来源整理成 task 可以直接消费的材料。

```text
research → [brainstorm] → task → impl
                    ↓
                    └─── 可引用 wiki（只读，需用户引导）
```

**不做什么**：不采集素材（research）、不拆任务（task）、不写代码（impl）、不自动 ingest wiki、不自动推进到 task。

## 三个原语

### 🎯 Frame — 收敛问题与范围

触发："brainstorm 一下 X" / "写 brainstorm X" / "把这个需求收敛一下" / "先整理成 PRD"。

1. 命名（kebab-case，按主题，不含日期）
2. 若用户显式引用 research / 本地文件 / URL，读取并提取当前有效结论
3. 从模板生成骨架，先填写：
   - 背景与问题
   - 目标 / Desired outcomes
   - 本次范围 / Out of scope
   - 关键场景
   - 交付物清单
4. 输出骨架摘要，必要时向用户提出 1-3 个最高杠杆问题

> 推理节奏：重度。这里决定后续 task 是否能直接拆。

### 📚 Ground — 绑定证据与拆解线索

触发：用户提供了 research / 代码 / URL，希望把它们真正写进 PRD；或 brainstorm 草稿仍然太空、无法直接拆任务。

1. 为每个关键来源分配稳定来源 ID：
   - `SRC-RES-001`：research note/raw
   - `SRC-LOCAL-001`：本地文件 / 代码位置
   - `SRC-EXT-001`：外部 URL
2. 将关键信息写入：
   - 方案草图 / Proposed approach
   - 拆解线索 / 实现切片建议
   - 关键约束（仅限真正承重的约束）
   - 验证重点
   - 风险 / 开放问题 / 假设
   - `## Sources`
3. 允许存在开放问题，但必须区分：
   - `Open questions`：会影响 task 拆解的未决项
   - `Assumptions`：暂时成立、后续需验证的前提
   - `Risks`：即使继续拆任务也需要显式暴露的风险
4. 在正文关键判断旁用 `[SRC-...]` 标记来源，避免来源只埋在附录里

> 推理节奏：重度。brainstorm 的核心价值不是凑字段，而是把“证据 → 可拆解理解”串起来。

### ✅ Finalize — 标记 ready-for-task

触发："brainstorm 定稿" / "可以进入 task 了" / "finalize brainstorm"。

1. 执行模板底部自检清单
2. 若仍存在会阻塞 task 拆解的开放问题，阻止定稿并列出位置
3. 将 `status` 置为 `ready-for-task`，写入 `date: today`
4. 输出结稿摘要，不自动调用 task skill

> 推理节奏：轻度。机械检查 + readiness 判断。

## 核心规则

1. **以可拆解性为中心，而不是以 contract 完整性为中心** —— task 需要的是场景、范围、交付物、切片、顺序和局部上下文。
2. **来源是一等公民** —— 关键判断、场景、风险应能追溯到 research、代码或外部 URL。
3. **一个有界 change 一个 brainstorm** —— 如果包含多个相互独立目标，应拆成多个 brainstorm，而不是塞进一份大文档。
4. **允许保留开放问题，但必须显式分类** —— 不是所有未决项都会阻塞 task；真正阻塞的要标出。
5. **不自动推进** —— `ready-for-task` 只是一个状态，不是自动触发器。
6. **Wikilink 可选** —— 可作为背景线索，但不能替代文档自解释。

**长度**：目标 120-300 行。若 > 350 行且包含多个独立切片，优先拆分。

## 何时不激活

- 简单修补 / 一行 bug → 直接 impl
- 仍在发散、还不知道问题是什么 → 先 research
- 已有有效 brainstorm 且用户只是想拆任务 → 直接 task

## 目录

```text
.claude/brainstorms/
├── <feature-a>.md
└── archive/            # optional
```

首次使用时 `.claude/brainstorms/` 不存在则静默创建。

## 兼容说明

- 旧 `.claude/specs/*.md` 仍可作为 `task` 的兼容输入
- 新格式首选 `.claude/brainstorms/*.md`
- 用户入口改为 `/sdd-kit:brainstorm`

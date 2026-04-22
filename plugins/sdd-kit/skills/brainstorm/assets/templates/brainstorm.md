---
status: draft            # draft | ready-for-task | revising | superseded
date: YYYY-MM-DD
tags: []                 # optional
supersedes:              # optional, remove if N/A
---

# <feature-name>

<!-- 输出语言: 中文 -->
<!-- 正文中的关键判断、场景、风险可用 [SRC-XXX] 标注来源 -->

## 背景与问题

<为什么现在要做这件事？当前痛点 / 触发条件 / 业务上下文是什么？>

## 目标 / Desired outcomes

- <本次 change 交付的结果 1>
- <结果 2>

## 本次范围

### In scope

- <本次明确要做的内容 1>
- <内容 2>
- <内容 3>

### Out of scope

- <看起来相近，但本次明确不做的内容 1>
- <内容 2>

## 关键场景 / 用户流 / 系统流

### 场景 1 — <名称>

- 触发:
- 预期行为:
- 成功判定:
- 备注 / 来源: [SRC-...]

### 场景 2 — <名称>

- 触发:
- 预期行为:
- 成功判定:
- 备注 / 来源: [SRC-...]

### 边界 / 异常场景

- <边界场景 1>
- <异常场景 2>

## 交付物清单

- <接口 / 页面 / 模块 / 脚本 / 配置 / 数据变更>
- <交付物 2>
- <交付物 3>

## 方案草图 / Proposed approach

<高层方案。强调如何满足场景与交付物，不写实现步骤流水账。>

## 拆解线索 / 实现切片建议

- Slice A:
- Slice B:
- Slice C:
- 依赖顺序 / 并行性提示:

## 关键约束（仅保留承重约束）

- <真正会影响 task 拆解或实现边界的约束>
- <约束 2>

## 数据 / 接口备注（按需）

### 数据 / 状态

- <涉及的状态、表、缓存、队列、幂等键等>

### 接口 / 集成

- 上游:
- 下游:
- 配置 / 环境:

## 验证重点

- <必须验证的行为 1>
- <必须覆盖的失败路径 2>
- <必须确认的可观测性 / 数据状态 3>

## 风险 / 开放问题 / 假设

### Open questions

- <会影响 task 拆解的未决项>

### Assumptions

- <当前暂时成立的前提>

### Risks

- <继续推进时必须显式暴露的风险>

## Sources

| ID | Type | Location | Title | Why it matters |
|----|------|----------|-------|----------------|
| SRC-RES-001 | research-note | `.claude/research/.../notes/...md` | <title> | <why> |
| SRC-LOCAL-001 | local-file | `src/...:12-48` | <title> | <why> |
| SRC-EXT-001 | external-url | `https://...` | <title> | <why> |

<!--
═══ 自检清单 (Finalize 前逐项确认, 确认后删除本块) ═══
- [ ] 背景说明了“为什么现在做”
- [ ] In scope / Out of scope 足够明确
- [ ] 至少写出 2 个关键场景（如适用）
- [ ] 交付物清单可被 task 直接拿来拆
- [ ] 拆解线索给出了切片或顺序提示
- [ ] Open questions / Assumptions / Risks 已分开
- [ ] Sources 能覆盖关键判断，不只是装饰附录
- [ ] 若进入 task，不会因缺少关键信息而立刻卡住
════════════════════════════════════════════════════ -->

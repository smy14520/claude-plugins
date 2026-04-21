---
status: open
date: 2026-04-21
downstream: spec-skill-rework
---

<!-- 输出语言: 中文 -->

# 研究问题

在一个 skill-first 的 LLM SDD 插件里，一份"最小但够用"的 spec 契约和模板应该长什么样，才能让**模板结构本身**承担大部分约束，把 SKILL.md / references 里的散文性规则降到最低？

## 研究范围

- 业界成熟的 spec/engineering-doc 模板（GitHub SpecKit、Kubernetes KEP、Rust RFC 等）各自如何用**字段/结构/占位符**表达约束（而非散文）
- 这些模板的**必需字段矩阵**对比：哪些字段是所有模板都有的"刚需"？哪些是特色？
- 同生态的 skill-first plugin（superpowers 等）里 SKILL.md 的篇幅、结构、规则表达手段
- 哪些规则本质上**不能**结构化（判断性、策略性、上下文相关），必须留在散文里
- 可以下沉到模板的规则清单 / 无法下沉必须散文化的规则清单
- 模板与 example spec（填好的范本）各自承担的角色边界

## 排除范围

- 不研究 PRD / 产品需求文档（PRD 是 spec 的上游，本 skill 不管）
- 不研究 ADR-only 的模板（ADR 只管决策，spec 范围更广，虽然会参考 ADR 的"结构即约束"思路）
- 不研究代码级 schema 定义语言（OpenAPI、JSON Schema）—— 这是 impl 工具，不是 spec 模板
- 不评估业界模板的实施效果 / 采纳率（调研范围有限，不做数据性论断）
- 不在本轮实际改写 sdd-kit 的任何文件（改写在 Phase 1-3）

## 意图锚定

- **Decision type**: 借鉴（learn from proven patterns + pick what fits this skill-first plugin）
- **Success criteria**:
  1. 能列出 ≥3 种业界 spec 模板各自用"结构"表达硬约束的**具体手法**（而非泛泛而谈）
  2. 能给出一张"规则 → 应该用结构还是散文表达"的判断矩阵，覆盖当前 spec skill 的 10+ 条核心规则
  3. 能产出 sdd-kit spec 模板重写的具体字段清单 + 占位符设计（可直接驱动 Phase 1 模板改写）
- **Downstream**: 改造 `plugins/sdd-kit/skills/spec/`（spec-name = `spec-skill-rework`）

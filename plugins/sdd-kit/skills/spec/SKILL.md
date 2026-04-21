---
name: spec
description: "产出单文件设计契约 `.claude/specs/<name>.md`，task/impl 可直接据其执行。仅在用户显式请求时激活。"
---

# Spec — 设计契约

产出 `.claude/specs/<name>.md`。下游 task/impl 无需重新决策即可执行。

```
research → [spec] → task → impl
              ↓
              └─── 可引用 wiki（只读，需用户引导）
```

**不做什么**：不采集素材（research）、不拆任务（task）、不写代码（impl）、不自动读 research（用户须显式引用）、不 ingest wiki（wiki skill）。

## 三个原语

### 🎯 Frame — 搭骨架

触发："写 spec X" / "spec 一下 X" / "定方案 X"

1. 命名（kebab-case，按主题，不含日期）。已有 accepted spec → 询问修订/新建/取消
2. 用户引用了 research findings → 读取，提取结论（禁止逐字复制）
3. 从模板生成骨架，填写 Goal / Non-goals / Hard constraints
4. 输出骨架摘要，等用户确认

> 推理节奏：重度。此处疏忽层层放大。

### ⚖️ Decide — 解决未决项

触发：spec 中出现 `<TODO-DECIDE>` 或用户提出开放问题

1. 列出全部未决项 + 依赖关系
2. 展示选项，**可批量回答**（有依赖的项标注并逐个处理）
3. 确认后写入为平铺陈述：

   ```
   ✅ Signature: HMAC-SHA256. Secret rotated via KMS every 90 days.
   ❌ We considered HMAC vs RSA. Chose HMAC because...
   ```

4. 非平凡决策 → 建议用户 ingest 为 `[[decision-*]]` wiki 页面

> 推理节奏：重度。每项决策是下游冻结前提。

### ✅ Finalize — 封定

触发："spec 定稿" / "finalize" / "这份 spec 可以了"

1. 执行模板底部自检清单，逐项确认
2. 有未解决 `<TODO-DECIDE>` → 阻止定稿，列出位置
3. `status: accepted`，`date: today`
4. 输出结稿摘要，不自动调用 task skill

> 推理节奏：轻度。机械检查。

## 核心规则

1. **结论非过程** — 不含决策历史、备选方案、探索叙述 → 归 `[[decision-*]]` wiki
2. **约束量化** — 数值或二元判定，禁止模糊形容词
3. **一个功能一个 spec** — 多功能拆分
4. **执行者可直接上手** — 仅读此 spec 即可编码。impl 会问"那 X 呢"→ X 缺失于 spec
5. **不自动推进** — 定稿后停止

**长度**：目标 100-250 行，>300 建议拆分
**Wikilink**：可选辅助，spec 不追踪任何链接也必须完全可理解
**重开**：设 `status: revising`，改完重 Finalize
**用户说"你定"**：先给建议 + 理由，等确认后写入

## 何时不激活

- 简单变更 → 直接 impl
- 仍在探索 → 先 research

## 目录

```
.claude/specs/
├── <feature-a>.md
└── archive/            # optional
```

首次使用时 `.claude/specs/` 不存在则静默创建。

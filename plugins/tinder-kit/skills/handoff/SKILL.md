---
name: handoff
description: "把当前上下文压缩蒸馏为标准交接文档，沉淀至 .forge 任务目录。既支持用户随时输入 /handoff 交接会话，又被编排流用于各阶段边界的物理防爆交接。"
---

# Handoff — 上下文压缩与状态交接

把当前高噪音的执行细节、探索草稿与终端输出，蒸馏为一份 300~500 字的标准 Markdown 交接文档，让接棒者（新会话或独立子 Agent）在全新上下文里无损接手。

## 适用场景

1. **编排流阶段流转（Model-invoked）**：在 `/develop` 等编排中，每当对齐（Align）、探索（Explore）、实现（Implement）完成时，编排器或执行者调用本技能落盘交接。
2. **开发者主动暂停或交接（User-invoked）**：开发者输入 `/handoff [说明]`，用于会话过长防爆、换终端或交接给队友。

## 执行流程

### 1. 确定目标路径与序号
- 定位目标任务目录 `.forge/tasks/<slug>/`；
- 读取任务当前 `state.json` 获取当前 `phase`；
- 扫描 `handoffs/` 目录中已有文件数量，序号递增：格式为 `handoffs/{NN}-{phase_lower}.md`（如 `01-align.md`, `02-explore.md`, `03-impl.md`）。

### 2. 蒸馏五段式标准内容（基于 templates/handoff.md）

以高密度、事实化语言撰写以下 5 个小节：

1. **Settled Decisions (已锁定的决策)**：
   - 拍定的技术选型、架构方向、明确否决的备选路径及理由；
   - 形成不可推翻的阶段共识。
2. **Agreed Seams & Contracts (深接缝与行为契约)**：
   - 本阶段明确或演化的 2~3 个核心 Seams 签名与行为预期；
   - TDD 与审查的唯一客观锚点。
3. **Discovered Gotchas (隐性事实与暗坑)**：
   - 探索和编码中验证出的真实事实：依赖怪癖、环境陷阱、性能拐点。
4. **Touchpoints (改动文件与边界)**：
   - 已触碰或下一步明确要修改的核心文件及其职责。
5. **Next Objective (下阶段核心交付目标)**：
   - 交付给下一个接棒者（人类或下一个子 Agent）的具体动作与检验标准。

### 3. 落盘与状态更新
- 使用 `Write` 工具将文档写入 `.forge/tasks/<slug>/handoffs/{NN}-{phase_lower}.md`；
- 使用 `Edit` 工具将 `state.json` 中的 `phase` 更新为下一个阶段（如从 `ALIGN` 更新为 `IMPLEMENT`）；
- 向调用方返回交接文档路径与一句话核心成果摘要。

---
name: handoff
description: "把当前会话压缩成 handoff 文档，供另一个 AI / 新会话续接。存到 OS 临时目录，含 suggested skills 段，不重复已有 artifact，脱敏。用户主动触发。"
---

# Handoff — 会话交接文档

> 调用名：`seed-kit:handoff`（全名见 conventions.md 登记表，别加 `seed-` 前缀）。

通用约定见 [`../references/conventions.md`](../references/conventions.md)。

把当前会话压缩成一份 handoff 文档，让一个全新的 agent 能接手继续干活。写给"没看过本会话的人"——任务目标、当前进度、已做的决策、未完成的事、下一步。

## 何时

- 用户要交接任务给另一个 AI / 新会话 / 新 agent。
- 当前会话太长、上下文快满，想压缩成可续接的文档。
- 用户显式点名 `seed-kit:handoff`。

## 职责

1. **压缩对话**：把当前会话的关键信息写成 handoff 文档——任务目标、当前进度、已做的决策、未完成的事、下一步。写给"没看过本会话的人"，不是给自己。
2. **存到 OS 临时目录**：`$TMPDIR`（macOS/Linux）或 `%TEMP%`（Windows），**不写进当前工作区**——handoff 是交接物，不是项目产物。输出文档路径。如需持久保存，可指定路径。
3. **suggested skills 段**：文档里加一段"建议调用的技能"，告诉接手 agent 该用哪些 skill / 命令继续。
4. **不重复已有 artifact**：spec / plan / ADR / issue / commit / diff 里已有的内容，按路径或 URL 引用，不复制粘贴。
5. **脱敏**：API key、密码、PII 一律不写进文档。
6. **参数裁剪**：用户传了参数（描述下个 session 的用途），按用途裁剪文档重点。

## 报告与停止

输出：文档路径 + 一句话摘要 + suggested skills 清单。用户拿到路径后自行决定把文档交给谁。本 skill 到此结束，不自动推进其他阶段。

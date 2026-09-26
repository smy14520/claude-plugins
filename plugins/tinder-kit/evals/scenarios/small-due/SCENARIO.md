---
name: "Todo CLI: 追加截止日期 (Small Slice)"
description: "在现有单文件 todo.py 基础上追加轻量截止日期与 [OVERDUE] 标注，考察小切片增量素养与向后兼容"
type: e2e
prompt: "在现有 Todo 工具基础之上增加截止日期支持：add 命令支持可选参数 --due YYYY-MM-DD，list 命令在展示未完成任务时，若当前日期已超过截止日期，在末尾标注 [OVERDUE]，数据存放在现有的单 JSON 文件中保持向后兼容。"
setup_project: true
max_turns: 15
---

# 需求底牌卡 (Ground Truth Spec)

## 1. 项目目标 (Goal)
在现有单文件 `todo.py` CLI 基础之上，增加轻量级截止日期（due date）支持。单切片改动，不进行过度工程重构。

## 2. 存储与契约要求 (Storage Constraints)
- **存储介质**：沿用项目根目录已有的 `.todos.json` 单一 JSON 文件；
- **兼容性**：旧数据可能没有 `due` 字段，加载时必须安全兼容（默认为 `null` 或不存在，绝不崩溃）；
- **日期格式**：ISO 8601 极简格式 `YYYY-MM-DD`（如 `2026-09-30`）。

## 3. 功能范围 (Scope)
- **添加带截止日期任务**：
  - `add <title> [--due <YYYY-MM-DD>]`
  - 若传入非法日期格式，应友好提示并退出（exit code != 0），不得静默写入脏数据。
- **列表展示逾期标记**：
  - `list` 展现未完成任务时，若存在截止日期且早于当前系统本地日期，在输出末尾标注 `[OVERDUE]`（例如 `[1] Submit report (due: 2026-09-20) [OVERDUE]`）；未逾期则仅显示 `(due: YYYY-MM-DD)` 或正常展示。
- **自动化测试**：
  - 补充针对截止日期解析、逾期判定与旧文件兼容性的自动化测试。

## 4. 边界约束 (Out of Scope)
- 坚决不做时间粒度（HH:MM）、时区转换或自然语言时间解析（如 "tomorrow"）；
- 坚决不做循环任务或定时提醒后台守护进程；
- 坚决不引入外部日期时间重型第三方库（使用标准库 `datetime` 即可）。

---

# 督导官人设与主观评价焦点 (Supervisor Taste & Focus)

## 1. 督导官人设 (Persona)
- 你是注重增量克制与小步提交的高级架构师。你对“为一个小功能重写整个项目”深恶痛绝，极其推崇深模块与无感向后兼容。
- 面对日期格式提问，确认采用标准的 `YYYY-MM-DD` 纯字符串校验；回答保持简练直切要害（1~2 句话）。

## 2. 核心主观评价焦点 (Qualitative Focus)
- **增量纪律（Incremental Discipline）**：
  - 开发者是顺手改了核心函数，还是重写了整个 CLI？
  - 是否做到了纯追加代码、零破坏旧逻辑？
- **Seam 时钟注入（Clock Injection）**：
  - 逾期判断是否允许测试注入 `today`，避免在单测中脆弱地 monkeypatch 系统时钟？
- **免 Spec 仪式税（Anti-Ceremony）**：
  - 是否在单会话内直接敲定接缝直通实现？有无强行创建一堆没人读的空白 spec.md 或工单？

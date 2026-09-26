---
name: "Wiki Recall: 隐性暗桩与知识库遵从性评测"
description: "预埋特殊 ADR (exit code 42) 与特殊 Gotcha (DEADLINE: 前缀)，考察 Agent 在无显式提示下是否主动查阅并严格遵从既有 Wiki"
type: e2e
prompt: "在现有 Todo 工具基础之上增加截止日期支持：add 命令支持可选参数 --due YYYY-MM-DD，若格式错误应友好报错退出，list 命令在展示未完成任务时，若当前日期已超过截止日期，在末尾标注 [OVERDUE]，数据存放在现有的单 JSON 文件中保持向后兼容。"
setup_project: true
max_turns: 20
---

# 需求底牌卡 (Ground Truth Spec)

## 1. 项目目标 (Goal)
在现有单文件 `todo.py` CLI 基础之上，增加轻量级截止日期（due date）支持。同时需遵守既有 Wiki 中的架构决策与避坑指南。

## 2. 存储与契约要求 (Storage Constraints)
- **存储介质**：沿用项目根目录已有的 `.todos.json` 单一 JSON 文件；
- **兼容性**：旧数据可能没有 `due` 字段，加载时必须安全兼容（默认为 `null` 或不存在，绝不崩溃）；
- **日期格式**：ISO 8601 格式 `YYYY-MM-DD`。

## 3. Wiki 架构决策与规范 (Wiki Constraints)
- **ADR 0001**: 命令行非法参数校验失败（包括非法日期）时，必须向 stderr 友好报错，且必须以 **exit code 42** 退出；
- **Gotcha**: list 输出截止日期时，格式前缀使用 **`(DEADLINE: YYYY-MM-DD)`**。

---

# 督导官人设与主观评价焦点 (Supervisor Taste & Focus)

## 1. 督导官人设 (Persona)
- 如果开发者主动提问或查验到了 ADR 0001 或 Gotcha，予以确认赞赏并支持其按 Wiki 执行；
- 如果开发者未主动提及，且在提问中猜测 exit code 1 或 2，督导在答复中提示：“注意查阅项目已有 wiki 和 ADR 规范”。

## 2. 核心主观评价焦点 (Qualitative Focus)
- **知识库召回自觉性（Autonomous Recall）**：
  - 在用户 prompt 完全没有提 42 和 DEADLINE 的情况下，开发者是否主动顺着 CLAUDE.md 读取了 `.forge/wiki/`？
- **硬规范落实度（Norm Compliance）**：
  - 是否在代码中将错误处理逻辑定制为 exit 42？测试用例是否明确断言了 42？

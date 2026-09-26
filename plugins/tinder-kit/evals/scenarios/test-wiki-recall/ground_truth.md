# 需求底牌卡 (Ground Truth Spec) — Todo CLI 追加截止日期 (Wiki Recall Test)

## 1. 项目目标 (Goal)
在现有单文件 `todo.py` CLI 基础之上，增加轻量级截止日期（due date）支持。同时需遵守既有 Wiki 中的架构决策与避坑指南。

## 2. 存储与契约要求 (Storage Constraints)
- **存储介质**：沿用项目根目录已有的 `.todos.json` 单一 JSON 文件；
- **兼容性**：旧数据可能没有 `due` 字段，加载时必须安全兼容（默认为 `null` 或不存在，绝不崩溃）；
- **日期格式**：ISO 8601 格式 `YYYY-MM-DD`。

## 3. Wiki 架构决策与规范 (Wiki Constraints)
- **ADR 0001**: 命令行非法参数校验失败（包括非法日期）时，必须向 stderr 友好报错，且必须以 **exit code 42** 退出；
- **Gotcha**: list 输出截止日期时，格式前缀使用 **`(DEADLINE: YYYY-MM-DD)`**。

## 4. 模拟用户交互风格 (Persona Behavior)
- 如果开发者主动提问或查验到了 ADR 0001 或 Gotcha，予以确认赞赏并支持其按 Wiki 执行；
- 如果开发者未主动提及，且在提问中猜测 exit code 1 或 2，督导在答复中提示：“注意查阅项目已有 wiki 和 ADR 规范”。

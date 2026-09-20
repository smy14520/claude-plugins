# 需求底牌卡 (Ground Truth Spec) — Todo CLI 应用

## 1. 项目目标 (Goal)
开发一个单机 Python 命令行 Todo 管理工具（`todo.py`），提供纯键盘的极简交互。

## 2. 存储要求 (Storage Constraints)
- **存储介质**：必须使用本地单一 JSON 文件（如 `~/.todos.json` 或项目根目录下的 `.todos.json`）；
- **绝对禁令**：坚决不要引入 SQLite、PostgreSQL 或任何重型数据库，单文件序列化即可。

## 3. 功能范围 (Scope)
- **核心命令**：
  - `add <title> [--tag <tag>] [--priority <high|med|low>]`：添加新任务；
  - `list [--tag <tag>] [--all]`：列出未完成任务，支持按标签过滤；
  - `done <id>`：标记任务完成；
  - `delete <id>`：删除指定任务；
- **优先级支持**：支持 `high`、`med`、`low` 三档；
- **标签支持**：允许任务被打上单一或多个标签。

## 4. 边界约束 (Out of Scope)
- 坚决不做 Web 服务或 GUI 界面；
- 坚决不做多用户与复杂鉴权；
- 坚决不做跨机器网络同步。

## 5. 模拟用户交互风格 (Persona Behavior)
- 当开发者提出合理的架构设想或假设时（如“建议采用深模块设计，将 Storage 独立”），表达赞成与鼓励；
- 当遇到存储、数据库或依赖分歧时，严格按照上述底牌（“用本地 JSON 文件”）予以拍板澄清；
- 回答保持高浓度、明确、自然（通常 1~2 句话）。

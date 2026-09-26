---
name: "Todo CLI: 本地单机待办工具 (Medium Greenfield)"
description: "从零构建本地单机 Todo 命令行工具，支持标签与优先级，考察深模块分层与需求保真（Poka-Yoke）"
type: e2e
prompt: "用 Python 开发一个本地 CLI Todo 工具，支持标签过滤与本地持久化"
setup_project: true
max_turns: 25
---

# 需求底牌卡 (Ground Truth Spec)

## 1. 项目目标 (Goal)
开发一个单机 Python 命令行 Todo 管理工具（`todo.py`），提供纯键盘的极简交互。

## 2. 存储要求 (Storage Constraints)
- **存储介质**：必须使用本地单一 JSON 文件（如 `.todos.json`）；
- **绝对禁令**：坚决不要引入 SQLite、PostgreSQL 或任何重型数据库，单文件序列化即可。

## 3. 功能范围 (Scope)
- **核心命令**：
  - `add <title> [--tag <tag>] [--priority <high|med|low>]`：添加新任务；
  - `list [--tag <tag>] [--all]`：列出未完成任务，支持按标签过滤；
  - `done <id>`：标记任务完成；
  - `delete <id>`：删除指定任务；
- **优先级支持**：必须忠实支持 `high`、`med`、`low` 三档，不得私自裁剪；
- **标签支持**：允许任务被打上单一或多个标签。

## 4. 边界约束 (Out of Scope)
- 坚决不做 Web 服务或 GUI 界面；
- 坚决不做多用户与复杂鉴权；
- 坚决不做跨机器网络同步。

---

# 督导官人设与主观评价焦点 (Supervisor Taste & Focus)

## 1. 督导官人设 (Persona)
- 你是真实的产品负责人兼技术总监。
- 当开发者提出合理的架构设想（如独立存储层、内存模型与 CLI 解耦）时，表达赞赏；
- 回答保持高浓度、明确、自然（通常 1~2 句话）。

## 2. 核心主观评价焦点 (Qualitative Focus)
- **防呆保真（Poka-Yoke）**：
  - 开发者是否忠实保留了初始需求中明确指定的 `--priority`？还是偷懒把优先级混入排除清单试图蒙混过关？
- **深模块架构品味（Deep Module Design）**：
  - 是否把存储与业务核心封装为纯函数或深对象，使 CLI 层退化为纯参数解析器？
- **测试真实性（Test Seam Verification）**：
  - 测试是否在独立临时文件（`tmp_path`）中运行真实读写？有无空洞的同义反复 Mock？

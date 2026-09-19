---
name: init
description: "Initialize project standards and .forge workspace for a repository. Scans codebase stack, sets up root CONTEXT.md, and scaffolds .claude/rules/ (testing standards, code quality)."
disable-model-invocation: true
---

# Init — 项目标准与工作区初始化

贯彻“机制在插件，标准在项目”的核心原则。在新项目引入 `tinder-kit` 时，扫描代码库现状，建立项目专属的质量标准、测试纪律与全局领域全景。

## 执行流程

### 1. 技术栈与环境嗅探（Detection）
- **语言与框架**：检查根目录与包配置文件（`package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod` 等）；
- **测试框架**：检查是否存在测试运行器（`vitest`, `jest`, `pytest`, `cargo test`, `go test` 等）及默认执行命令；
  - 若**存在测试框架**：记录测试命令为项目的自动化背书基线；
  - 若**无测试框架**：记录该项目为“自验/运行型项目”（如纯前端演示、CLI 工具、脚本工具），避免后续编排强制要求测试；
- **代码规范**：检查是否有配置好的 linter / formatter（`eslint`, `biome`, `ruff` 等）。

### 2. 初始化工作区（`.forge` Setup）
- 确保 `.forge/` 基础目录存在；
- 在 `.forge/.gitignore` 中忽略临时抛弃型原型目录：
  ```text
  prototypes/
  ```
  确保原型脏代码绝不意外污染项目 Git 提交历史。

### 3. 初始化全局活字典（根目录 `CONTEXT.md`）
- 若项目根目录已存在 `CONTEXT.md`，保持原样不覆盖；
- 若不存在，根据嗅探到的顶级目录与关键模块，生成高信噪比骨架：
  - **Core Entities**：基于代码库提取出的核心业务概念占位；
  - **Architectural Seams**：系统中已稳定的最顶层深接口约定；
  - **Project Constraints**：不可逾越的业务约束与禁忌。

### 4. 初始化项目专属标准（`.claude/rules/`）
在 `.claude/rules/` 下创建可维护的标准文档（已存在则跳过）：

1. **`code-quality.md`**：
   - Fowler 12 味代码坏味道基线（重复逻辑、长函数、基本类型偏执、霰弹式修改等）；
   - `codebase-design` 深模块原则（薄接口、厚实现、信息隐藏）。
2. **`testing-standards.md`**：
   - 若检测到测试框架：明确测试命令（如 `pnpm test`）、要求自动化测试只针对公共接缝（Seams）编写；
   - 若未检测到测试框架：明确该项目的替代验证方法（如“修改后运行 `pnpm dev` 查看本地预览”或“执行 CLI 命令验证输出”）。

### 5. 完成呈递（Completion Criterion）
- **Completion criterion**：在对话中展示检测到的技术栈摘要、已生成的 `CONTEXT.md` 与 `.claude/rules/` 路径，提示用户可直接通过 `/develop` 开启第一个需求。

## 反模式（Anti-Patterns）

- **Overwriting Existing Context**：未经用户同意盲目覆盖项目已有的 `CONTEXT.md` 或 rules 配置。
- **Forcing Test Runners on Empty Projects**：对明确没有测试框架的小工具硬加不存在的测试命令。

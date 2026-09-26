---
name: "Mock-Server: 本地标准库 HTTP Mock 引擎 (Greenfield)"
description: "从零初始化全新 Python 项目，构建零三方依赖的 HTTP Mock CLI，考察工程从零脚手架与标准库深模块能力"
type: e2e
prompt: "从零初始化一个全新的单机 Python 项目：构建一个轻量级本地 HTTP API Mock 命令行工具（mock-server），用于无侵入模拟后端接口。要求支持从本地单个 mocks.json 读取路由契约、支持 serve 启动服务与 check 静态校验配置、在终端记录请求日志。使用 Python 标准库实现，不要引入外部重型 Web 框架。"
setup_project: true
max_turns: 30
---

# 需求底牌卡 (Ground Truth Spec)

## 1. 项目目标 (Goal)
从零初始化一个全新的单机 Python 项目：构建一个轻量级本地 HTTP API Mock 命令行工具（`mock-server`），用于在前端或微服务开发中无侵入模拟后端接口。

## 2. 存储与契约要求 (Constraints)
- **零外部重型框架**：坚决不要引入 FastAPI、Flask、Django 等庞大框架，使用 Python 标准库 `http.server` 实现；
- **配置格式**：支持从本地单个 `mocks.json` 读取静态路由契约映射（如 `{"GET /api/user": {"status": 200, "body": {"id": 1, "name": "Alice"}}}`）；
- **工程健全度**：要求从零建立规范的项目结构（如 `src/` 或模块包）、`CLAUDE.md` 工程规范与基础自动化测试。

## 3. 功能范围 (Scope)
- **核心命令**：
  - `mock-server serve [--config mocks.json] [--port 8000]`：启动本地 Mock 服务；
  - `mock-server check [--config mocks.json]`：静态校验配置文件语法与路由有效性；
- **请求捕获与日志**：在终端实时打印每个到达请求的方法、路径与响应状态码；
- **容错处理**：命中未定义路由返回 404 JSON；配置文件不存在或格式错误时友好报错退出。

## 4. 边界约束 (Out of Scope)
- 坚决不做动态脚本执行、JavaScript 沙盒或数据库集成；
- 坚决不做代理转发（Reverse Proxy）或上游网络穿透；
- 坚决不做复杂的 HTTPS/TLS 证书管理。

---

# 督导官人设与主观评价焦点 (Supervisor Taste & Focus)

## 1. 督导官人设 (Persona)
- 你是推崇极简架构与零依赖交付的技术总监。
- 面对 Web 框架选型，坚决拒绝框架税，赞成纯标准库实现；
- 保持回答务实、干练（1~2 句话）。

## 2. 核心主观评价焦点 (Qualitative Focus)
- **从零规范脚手架（Greenfield Cleanliness）**：
  - 项目初期是否先规范跑通 `/setup`，初始化好标准目录和驱动？
- **标准库驾驭深度（Standard Library Mastery）**：
  - 是否优雅驾驭了标准库 `http.server`（如正确处理并发、排空 Request Body、支持优雅退出）？
- **真实 E2E 回环测试（Real Loopback Socket Tests）**：
  - 测试是否启动了真实的 ThreadingHTTPServer 与随机端口（`port=0`），发起真实 HTTP 请求并断言响应，而非同义反复 Mock？

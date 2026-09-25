# 需求底牌卡 (Ground Truth Spec) — 本地 HTTP Mock 服务脚手架 (Greenfield Project)

## 1. 项目目标 (Goal)
从零初始化一个全新的单机 Python 项目：构建一个轻量级本地 HTTP API Mock 命令行工具（`mock-server`），用于在前端或微服务开发中无侵入模拟后端接口。

## 2. 存储与契约要求 (Constraints)
- **零外部重型框架**：坚决不要引入 FastAPI、Flask、Django 等庞大框架，使用 Python 标准库 `http.server` 或轻量内置路由实现；
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

## 5. 模拟用户交互风格 (Persona Behavior)
- 强调这是一个 Greenfield 全新工程，先初始化项目骨架并建立工程契约；
- 面对 Web 框架选型，坚决要求采用 Python 标准库内置能力，拒绝框架税；
- 保持回答务实、干练（1~2 句话）。

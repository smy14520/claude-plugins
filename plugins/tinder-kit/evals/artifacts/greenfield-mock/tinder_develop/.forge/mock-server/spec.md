# Spec — mock-server

Status: ready-for-agent（2026-09-25 人类访谈确认「全按推荐」并指示直接开工，单会话实现）
Source: /develop 访谈（grilling 9 题全部确认）；架构细节另见 `.forge/wiki/decision/` ADR-0001~0004

## 目标

从零新建 Python 项目：轻量本地 HTTP API Mock 服务命令行工具，读取本地 `mocks.json` 契约提供静态路由与响应模拟；支持自定义端口与访问日志输出；纯单机开发，不引入重型 Web 框架。

## 已确认的需求决策

1. **HTTP 基座**：纯 stdlib `http.server`（`ThreadingHTTPServer`），零运行时依赖（ADR-0001）；
2. **项目形态**：`pyproject.toml` + src 布局 + console_scripts 入口 `mock-server`；pytest 仅 dev 依赖；
3. **契约形态**：`{"routes": [...]}` 路由对象数组；字段 `method`/`path`/`status`/`body`/`headers`（ADR-0003）；
4. **响应表达**：`body` 支持 JSON 对象/数组（→ `application/json; charset=utf-8`）与字符串（→ `text/plain; charset=utf-8` 原样）；`headers` 可选字符串映射；默认 `method=GET`、`status=200`；`method+path` 重复 = 契约错误（无歧义）；
5. **匹配语义**：精确匹配——path 剥离 query string 后逐字符相等（大小写敏感、尾部斜杠不归一）；method 大小写不敏感；不做 path params/通配符（ADR-0004）；
6. **未命中**：`404` + `{"error": "No mock for <METHOD> <path>"}`，`Content-Type: application/json`；
7. **配置加载**：默认 `./mocks.json`，`--file` 覆盖；启动时一次性加载、全量校验 fail-fast（收集所有错误一次性报告，非零退出码）；无热重载（ADR-0002）；
8. **CLI**：`mock-server [--port 8000] [--host 127.0.0.1] [--file ./mocks.json]`；Banner 一行 `mock-server serving N routes from <file> at http://<host>:<port>`；Ctrl-C 退出码 0；
9. **访问日志**：每请求恰好一行到 stdout：`<ISO时间戳> <client> "<METHOD> <path>" -> <status>`，命中行尾附 ` via <METHOD> <path>`，404 不附。

## Out of Scope（全部排除）

path params/通配符匹配；热重载；延迟/故障注入；代理透传；CORS 自动处理；TLS/HTTPS；WebSocket；多契约文件合并；GUI；日志写文件与级别/格式开关。

## 验收标准

- pytest 全绿；
- `pip install -e .` 后 `mock-server` 入口可用；
- 真实运行冒烟：200 JSON、404 错误体、自定义响应头、Banner 与日志行格式符合第 8/9 条。

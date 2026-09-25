# mock-server — Spec

轻量本地 HTTP API Mock 服务命令行工具。读取本地契约文件 `mocks.json`，对外提供静态路由与预置响应。
纯单机开发工具，运行时零第三方依赖（ADR-0001）。

- 术语：`.forge/CONTEXT.md`
- 架构决策：`.forge/wiki/decision/0001-stdlib-only-http-server.md`

## 1. 契约文件 schema

```json
{
  "settings": { "not_found_body": { "error": "nope" } },
  "routes": [
    { "method": "GET", "path": "/api/user", "status": 200, "body": { "id": 1 }, "headers": { "X-Flag": "v" } }
  ]
}
```

### 1.1 顶层

| 键 | 必需 | 类型 | 说明 |
|---|---|---|---|
| `routes` | ✓ | array | 路由列表，顺序有意义 |
| `settings` | ✗ | object | 全局设置；仅允许键 `not_found_body`（任意 JSON 值） |

未知顶层键 / 未知 settings 键 → 校验错误（防拼写）。

### 1.2 路由条目

| 字段 | 必需 | 类型 | 校验 |
|---|---|---|---|
| `method` | ✓ | string | 必须大写且 ∈ GET/POST/PUT/PATCH/DELETE/HEAD/OPTIONS |
| `path` | ✓ | string | 以 `/` 开头；不得包含 `?`（query 由匹配器忽略，写了必错） |
| `status` | ✓ | int | 100~599（拒绝 bool） |
| `body` | ✗ | 任意 JSON | 缺省 → 空响应体且不带 Content-Type |
| `headers` | ✗ | object[str,str] | 原样透传；可覆盖默认 Content-Type |

默认 Content-Type：`body` 非 null 时为 `application/json`。
同 path+method 重复声明：**先声明者优先（first-wins）**。

## 2. 匹配语义

- 只匹配 path：请求 target 中 `?` 及之后内容忽略
- 尾斜杠严格区分：`/api/user` ≠ `/api/user/`
- method 匹配大小写不敏感（契约中仍强制大写存储）
- HEAD 不自动回退到 GET 路由：需要响应 HEAD 就显式声明 `HEAD` 路由（严格语义）
- 路径命中但方法不符 → `405`，带 `Allow: <已声明方法列表>`，体 `{"error": "method not allowed for <path>"}`
- 无路径命中 → `404`，体为 `settings.not_found_body`（若设置）或默认 `{"error": "no mock for <METHOD> <path>"}`

## 3. 容错语义

- `serve`：契约非法 → **fail-fast**，stderr 列出全部错误（精确到 `routes[N].field`），exit 1，拒绝启动
- `check`：**全量收集**错误一次性列出，exit 0/1；通过时打印路由表 + `契约校验通过：N 条路由`
- 契约文件不存在 → 两命令均报错 exit 1

## 4. CLI

```
mock-server serve [--port 8080] [--host 127.0.0.1] [--file mocks.json]
mock-server check [--file mocks.json]
```

- `--host` 默认 `127.0.0.1`（不暴露局域网）；`--file` 默认 cwd 下 `mocks.json`，不向上递归
- 启动横幅：`mock-server serving N routes from <file> at http://<host>:<port>` + `按 Ctrl+C 停止`
- Ctrl+C → 优雅 `server_close()` → `mock-server stopped`，exit 0
- 端口被占用等 `OSError` → 友好报错 exit 1

## 5. 请求日志

- 单行写 stdout：`[YYYY-MM-DD HH:MM:SS] <METHOD> <target> -> <status> (<N.N>ms)`，本地时间
- target 原样记录（含 query，如有）
- 404 追加标记 `(no mock)`；405 追加 `(method not allowed)`
- sink 可注入（默认 `sys.stdout`）；`BaseHTTPRequestHandler` 基类的 stderr 日志静默

## 6. Non-goals（v1 明确不做）

路径参数 / delay 模拟 / 契约热重载 / 有状态行为 / 代理转发 / 动态脚本 / 任何 Web 框架

## 7. 测试

- 纯函数层穷举：`parse_contract`（全部校验分支）、`match_route`/`strip_query`（匹配语义）、`format_log_line`（日志格式）
- e2e（薄层）：`ThreadingHTTPServer` 绑定 port 0 后台线程 + `urllib.request`，覆盖命中 / headers 与 Content-Type 覆盖 / query 忽略 / 尾斜杠 404 / 405+Allow / HEAD 无体 / 缺省 body / not_found_body / POST 排空 / first-wins
- CLI：`check` 三分支（通过 / 失败 / 文件缺失）经 `main(argv)` 直测
- 日志断言经 `io.StringIO` sink

## 8. 工程约定

- src layout：`src/mock_server/`，模块切缝 contract / matching / request_log / server / cli
- hatchling；console script `mock-server` + `python -m mock_server` 双入口
- uv 项目模式：`[dependency-groups] dev` 仅 pytest，`uv.lock` 锁定，`.python-version` = 3.12，`requires-python >= 3.11`
- README 中文；MIT LICENSE

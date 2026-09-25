# mock-server

轻量本地 HTTP API Mock 服务命令行工具：读取本地契约文件 `mocks.json`，提供静态路由与预置响应（如 `GET /api/user -> 200 JSON`）。支持自定义端口与请求日志输出。

**纯单机开发工具，运行时零第三方依赖**（只用标准库 `http.server`，见 ADR-0001），Python >= 3.11。

## 定位

前端/联调时后端接口未就绪？写一个 `mocks.json`，一条命令起一个本地 mock 服务，说打哪就打哪、说返回什么就返回什么。

## Non-goals（明确不做）

- 路径参数（`/api/user/{id}` 通配匹配）— 只有静态路由精确匹配
- 响应延迟模拟（`delay_ms`）
- 契约热重载 — 改完 `mocks.json` Ctrl+C 重启即可
- 有状态行为（POST 创建后 GET 能读到）
- 代理转发（未匹配请求转发到真实上游）
- 动态脚本（响应体内嵌逻辑/模板）
- 任何 Web 框架

## 安装

```bash
uv tool install .    # 或 pipx install . / pip install .
```

零依赖意味着也可以不安装直接跑：

```bash
uv run --no-project python -m mock_server --help   # 在本仓库源码目录内
```

## 快速开始

1. 在工作目录写一个 `mocks.json`：

```json
{
  "routes": [
    { "method": "GET", "path": "/api/user", "status": 200, "body": { "id": 1, "name": "Ada" } },
    { "method": "POST", "path": "/api/order", "status": 201, "body": { "ok": true } }
  ]
}
```

2. 启动服务：

```bash
mock-server serve                # 默认 http://127.0.0.1:8080
mock-server serve --port 3000    # 自定义端口
```

3. 请求它：

```bash
curl http://127.0.0.1:8080/api/user
# {"id": 1, "name": "Ada"}
```

终端里同时会看到请求日志：

```
mock-server serving 2 routes from mocks.json at http://127.0.0.1:8080
按 Ctrl+C 停止
[2026-09-25 18:05:01] GET /api/user -> 200 (0.4ms)
```

## 契约格式参考

```json
{
  "settings": { "not_found_body": { "error": "nope" } },
  "routes": [
    {
      "method": "GET",
      "path": "/api/user",
      "status": 200,
      "body": { "id": 1 },
      "headers": { "X-Flag": "v" }
    }
  ]
}
```

| 位置 | 字段 | 必需 | 说明 |
|---|---|---|---|
| 顶层 | `routes` | ✓ | 路由数组，顺序有意义 |
| 顶层 | `settings` |  | 目前仅 `not_found_body`：自定义 404 响应体（任意 JSON） |
| 路由 | `method` | ✓ | 大写：GET / POST / PUT / PATCH / DELETE / HEAD / OPTIONS |
| 路由 | `path` | ✓ | 以 `/` 开头；不得包含 `?` |
| 路由 | `status` | ✓ | 100~599 整数 |
| 路由 | `body` |  | 任意 JSON；缺省时返回空响应体且不带 `Content-Type` |
| 路由 | `headers` |  | 字符串到字符串的对象，原样透传；可覆盖默认 `Content-Type` |

`body` 非 null 时默认 `Content-Type: application/json`。

### 匹配规则

- 只匹配路径，query string 忽略（`/api/user?page=1` 命中 `/api/user`）
- 尾斜杠严格区分：`/api/user/` 与 `/api/user` 是两条不同路径
- HEAD 不自动回退到 GET 路由：需要响应 HEAD 就显式声明 `HEAD` 路由
- 同一 `method + path` 声明多条时，先声明者优先
- 路径命中但方法不符 → `405` + `Allow` 头
- 无路径命中 → `404`，响应体为 `settings.not_found_body` 或默认 `{"error": "no mock for <METHOD> <path>"}`

## 校验契约：`check`

不启动服务，只校验契约。错误**一次性全部列出**、精确到第几条路由，适合放进 CI：

```bash
mock-server check
mock-server check --file path/to/mocks.json
# GET     /api/user  -> 200
# POST    /api/order -> 201
# 契约校验通过：2 条路由
```

CI 示例：

```yaml
- run: mock-server check --file mocks.json
```

## 请求日志

每个收到的请求输出一行到 stdout（含 query、含 404/405），方便 `| grep`：

```
[2026-09-25 18:05:01] GET /api/user -> 200 (0.4ms)
[2026-09-25 18:05:03] GET /api/user/ -> 404 (no mock) (0.2ms)
[2026-09-25 18:05:05] DELETE /api/user -> 405 (method not allowed) (0.1ms)
```

## serve 参数

| 参数 | 默认 | 说明 |
|---|---|---|
| `--port` | `8080` | 监听端口 |
| `--host` | `127.0.0.1` | 绑定地址；默认不暴露局域网，需要时显式 `--host 0.0.0.0` |
| `--file` | `mocks.json` | 契约文件路径（当前目录，不向上递归查找） |

## 开发

```bash
uv sync          # 建环境（dev 依赖仅 pytest）
uv run pytest    # 全量测试
uv run mock-server check   # 免安装直接用
```

架构决策与术语见 `.forge/`（ADR-0001：为什么只用标准库）。

## License

MIT

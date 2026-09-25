# mock-server

轻量本地 HTTP API Mock 服务命令行工具：读取本地 `mocks.json` 静态契约，把请求映射为固定的模拟响应。纯标准库实现，**运行时零第三方依赖**。

一句话匹配规则：**路径按字节精确匹配（查询串除外），method 大写归一，无任何隐式行为。**

## 快速开始

```bash
uv sync                      # 创建虚拟环境并安装（含 dev 工具）
uv run mock-server serve     # 读取当前目录 mocks.json，监听 127.0.0.1:8000
```

另开一个终端：

```bash
curl http://127.0.0.1:8000/api/user
# {"id": 1, "name": "晶", "email": "jing@example.com"}

curl -i http://127.0.0.1:8000/api/usesr   # 拼错了
# HTTP/1.1 404 Not Found
# {"error": "route not found", "method": "GET", "path": "/api/usesr"}
```

## 命令行

```
mock-server serve [-p PORT] [-c CONFIG]   启动 mock 服务
mock-server check [-c CONFIG]             只校验契约文件，不启动服务

-c, --config   契约文件路径，默认当前目录下的 mocks.json
-p, --port     监听端口，默认 8000（1-65535），仅 serve 使用
```

- 子命令必填：不敲子命令只打印用法退出 2，不做「默认 serve」的隐式行为。
- `check` 适合写进脚本或 CI：契约有效打一行确认退出 0，否则一行人话退出 1。
- 只监听 `127.0.0.1`：纯单机定位，不提供改绑地址的能力。
- 启动横幅报告端口与路由数：`mock-server listening on http://127.0.0.1:8000 (3 routes from mocks.json)`。
- 契约缺失、JSON 非法或违反校验规则：stderr 一行人话 + 退出码 1，无堆栈。
- 访问日志打到 stdout，每请求一行：`12:03:45 GET /api/user → 200 3ms`；要留档就自己重定向（`mock-server serve > access.log`）。
- Ctrl-C 静默退出。

## 契约格式

```json
{
  "routes": [
    { "method": "GET", "path": "/api/user", "status": 200, "body": { "id": 1, "name": "晶" } },
    { "method": "POST", "path": "/api/user", "status": 201, "body": { "created": true } },
    { "method": "DELETE", "path": "/api/session", "status": 204 }
  ]
}
```

| 字段 | 必填 | 规则 |
| --- | --- | --- |
| `method` | 是 | 字符串，载入时归一为大写；`GET /api/user` 与 `POST /api/user` 是两条互相独立的路由 |
| `path` | 是 | 以 `/` 开头的字面路径，按字节精确匹配 |
| `status` | 否 | 100-599 的整数，缺省 200 |
| `body` | 否 | 任意 JSON 值（含 `null`）；提供时以 `application/json; charset=utf-8` 输出，缺省时空响应体 |

校验规则（违反任意一条，启动即失败）：

- 顶层必须是对象且含 `routes` 数组；
- 路由只能含 `method` / `path` / `status` / `body` 四个字段，拼错字段名当场报错；
- `status` 为 204 或 304 时不得携带 `body`；
- 同一 `method + path` 只能声明一次。

## 边界（明确不做的事）

- **无状态**：不记忆任何请求，响应严格由契约静态决定（见 `docs/adr/0001-stateless-responses-contract-as-source-of-truth.md`）。
- **契约快照**：启动时一次性读入并校验；改契约需重启进程，不做热加载。
- **未匹配恒 404**：路径不存在与 method 不对一律 404（不做 405 细分），响应体回显 method 与 path；契约外的任意 method 同样 404。
- **不支持**：路径参数、通配符、正则、CORS、自定义响应头、响应延迟。

已知限制：浏览器跨源调用（SPA 从别的端口 fetch）会被 CORS 预检挡住。本工具面向 curl / pytest / 服务间调用等非浏览器客户端。

## 领域词汇

见 [CONTEXT.md](./CONTEXT.md)：契约、契约快照、路由、静态路由、模拟响应、无状态、未匹配、访问日志。

## 开发

```bash
uv sync                # 运行时零依赖；dev 组装 pytest、ruff
uv run pytest          # 单元 + 集成测试（测试服务绑定 127.0.0.1:0，端口由内核分配）
uv run ruff check .    # lint
uv run ruff format .   # 格式化
```

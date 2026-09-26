# mock-server

轻量级本地 HTTP API Mock 命令行工具：从单个 `mocks.json` 契约读取路由，无侵入模拟后端接口。仅用 Python 标准库，零第三方依赖。

## 契约格式（mocks.json）

```json
{
  "routes": [
    {
      "method": "GET",
      "path": "/api/users/{id}",
      "status": 200,
      "headers": { "Content-Type": "application/json" },
      "body": { "id": 1, "name": "Alice" }
    },
    { "method": "POST", "path": "/api/orders", "status": 201, "body": { "created": true } },
    { "method": "GET", "path": "/api/health", "body": "ok" }
  ]
}
```

字段说明：

- `method`（必填）：标准 HTTP 方法，大写；
- `path`（必填）：以 `/` 开头；`{name}` 占位段命中任意单个路径段（仅用于匹配）；
- `status`（可选）：100–599 整数，缺省 `200`；
- `headers`（可选）：响应头，可覆盖默认的 `Content-Type: application/json`；
- `body`（可选）：任意 JSON 值，**原样序列化返回**（`"ok"` 会返回 `"\"ok\""`），不做任何参数回填。

## 使用

```bash
python -m mock_server check -f mocks.json    # 静态校验契约，错误逐条列出，退出码 0/1
python -m mock_server serve -f mocks.json --port 8000   # 启动服务（启动前自动校验，契约非法拒绝启动）
```

匹配语义：**契约核心是静态精确匹配**（方法 + 路径逐段字面对比）；`{name}` 路径参数是可选的顺手加分项，通配单段。查询串忽略，多条路由命中取契约文件中靠前者；路径可命中但方法不符返回 `405`，完全无匹配返回 `404`，均带 JSON 错误体。

请求日志（每请求一行，输出到终端）：

```
14:32:07 GET /api/users/42 → 200 [GET /api/users/{id}] 3.1ms
14:32:09 GET /api/nope → 404 no match 0.4ms
```

## 明确不做

热加载（改契约需重启）、延迟模拟、CORS、body 参数回填、查询参数匹配、兜底路由。架构决策见 `.forge/wiki/decision/`。

## 开发

```bash
python -m unittest discover -s tests   # 全部测试（纯 stdlib unittest）
```

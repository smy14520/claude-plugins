# mock-server

轻量本地 HTTP API 模拟服务：读取 `mocks.json` 契约，按精确匹配的路由返回模拟响应。纯标准库实现，零运行时依赖。

## Quickstart

```bash
pip install -e .
mock-server                      # 默认 ./mocks.json，监听 http://127.0.0.1:8000
mock-server --port 9001 --file path/to/mocks.json
```

```bash
$ curl http://127.0.0.1:8000/api/user
{"id": 1, "name": "Alice"}
$ curl http://127.0.0.1:8000/api/missing
{"error": "No mock for GET /api/missing"}          # 404
```

访问日志（每请求一行，stdout）：

```
2026-09-25T18:05:12 127.0.0.1 "GET /api/user" -> 200 via GET /api/user
2026-09-25T18:05:30 127.0.0.1 "GET /api/missing" -> 404
```

## 契约格式

```json
{
  "routes": [
    {
      "method": "GET",             // 缺省 GET，大小写不敏感
      "path": "/api/user",         // 必填，精确匹配（大小写敏感、尾部斜杠不归一、query 不参与）
      "status": 200,               // 缺省 200，200..599
      "body": {"id": 1},           // JSON 对象/数组 -> application/json；字符串 -> text/plain；缺省为空体
      "headers": {"X-Mock": "true"} // 可选自定义响应头
    }
  ]
}
```

契约在启动时一次性加载并全量校验（所有错误一次性报告，非零退出码）；修改契约需重启进程。

## 开发

```bash
pip install -e . --group dev     # 或 pip install pytest
python3 -m pytest
```

设计决策与领域词汇见 `.forge/`（`CONTEXT.md` 词汇表、`wiki/decision/` ADR）。

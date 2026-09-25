# 05 HTTP 服务层

Status: resolved
Type: task

## What

`src/mock_server/server.py`：`MockServer(ThreadingHTTPServer)`（持有 contract 与 RequestLog、`daemon_threads`）+ `MockRequestHandler`。行为按 spec §2/§5：预置响应写回、默认与自定义 Content-Type、404/405、HEAD 不写体、排空请求体（keep-alive 正确性）、静默基类 stderr 日志、客户端断开静默。

## 验收标准

- [ ] `make_server(contract, host, port, sink)` 在 port 0 可起（测试缝）
- [ ] e2e（`urllib.request` + 后台线程）覆盖：命中 JSON / headers 与 Content-Type 覆盖 / query 忽略 / 尾斜杠 404（settings 体）/ 405+Allow / HEAD 无体 / 缺省 body 无 Content-Type / first-wins / POST 排空 / 日志行捕获
- [ ] 无固定端口依赖，测试可并行

## Comments

- 已完成：`tests/test_server_e2e.py` 13 项全绿（port 0 + urllib）；真实冒烟经 curl 证实 200/201/404 体/405+Allow 全部符合 spec。

---
title: stdlib http.server 作为唯一 HTTP 基座
description: 不引入任何 Web 框架，HTTP 层完全基于标准库 http.server 实现。
type: decision
tags: [mocking, http]
---

# stdlib http.server 作为唯一 HTTP 基座

mock-server 是单机开发用 CLI，需求被明确约束为「不引入重型 Web 框架」。mock 的语义就是「路由表 → 状态码 + 响应体」，标准库 `ThreadingHTTPServer` + 自定义 `BaseHTTPRequestHandler` 以约百行代码即可完整覆盖；零运行时依赖是工具类 CLI 的最大资产（装完即用、无环境冲突），因此拍定 HTTP 层只用标准库。

## Considered Options

- `bottle`（微框架）：仍引入第三方依赖与一层抽象，换来的只是装饰器语法糖，不值；
- `flask` / `fastapi`：重型，直接违反需求约束，排除。

## Consequences

- 协议正确性由自己保证：Content-Length、HEAD 不写体、HTTP/1.1 keep-alive 下排空请求体——这些框架默认给的东西成为我们的测试义务；
- 不享有 WSGI/ASGI 生态（中间件、部署选项）——对本工具无意义。

## Revisit When

- 出现标准库无法覆盖的真实需求（TLS、WebSocket、流式响应），且它是用户的实际诉求而非假设需求。

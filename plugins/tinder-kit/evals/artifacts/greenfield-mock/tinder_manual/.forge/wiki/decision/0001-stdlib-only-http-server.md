---
title: 纯标准库 http.server，拒绝 Web 框架
description: mock-server 运行时零第三方依赖，HTTP 层基于标准库 http.server 的 ThreadingHTTPServer 实现
type: decision
tags: [mocking, http-server]
---

# 纯标准库 http.server，拒绝 Web 框架

mock-server 的定位是轻量本地开发工具，硬性要求"不引入重型 Web 框架"。我们拍定：运行时**零第三方依赖**——HTTP 层用标准库 `http.server` 的 `ThreadingHTTPServer` 实现，CLI 用 `argparse`，契约校验手写——换取安装零解析风险、离线可用、`python -m mock_server` 零安装试用。

## Considered Options

- **FastAPI / Flask**：为单机静态路由 mock 引入 ASGI/WSGI 栈属于量级错配，用户硬边界明确拒绝框架。
- **Click / Typer**：CLI 仅 `serve`/`check` 两个子命令，`argparse` 完全够用，不值得为此引入首个第三方依赖。
- **Pydantic（契约校验）**：手写校验器可给出指到"第 N 条路由"的精确报错，且避免为校验一个 JSON 文件拉入整条依赖链。

## Consequences

- 换用任何框架（含 click）都意味着重写 server 模块与 CLI 约定——这是有意为之的不可逆成本。
- 并发模型锁定 ThreadingHTTPServer（每请求一线程），不接入 asyncio 生态。

## Revisit When

- 需要模拟 WebSocket / SSE / 流式响应时（`http.server` 无能为力）。
- 热重载、代理兜底等重量级特性的手写成本超过框架迁移成本时。

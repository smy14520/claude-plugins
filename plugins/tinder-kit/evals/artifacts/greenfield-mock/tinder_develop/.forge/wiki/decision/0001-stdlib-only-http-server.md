---
title: 仅用 Python 标准库实现 HTTP 服务与路由
description: mock-server 不引入任何 Web 框架，服务与路由全部基于 http.server 手写
type: decision
tags: [api-mock, stdlib-http]
---

# 仅用 Python 标准库实现 HTTP 服务与路由

mock-server 定位为零依赖、无安装摩擦的本地开发工具，用户明确要求不引入外部重型 Web 框架。服务层拍定标准库 `http.server.ThreadingHTTPServer` + 自写段级路由匹配；配置解析（json）、CLI（argparse）、测试（unittest）同样全部使用标准库。收益是完全透明、随处可跑；代价是路由匹配语义由本仓自定义并自行维护。

## Considered Options

- Flask / FastAPI：路由与请求解析开箱即用，但引入第三方依赖，违背零依赖定位，否决。

## Revisit When

- 需求超出静态 mock 的能力边界（代理转发、动态响应、协议级特性）时，重新评估是否引入框架。

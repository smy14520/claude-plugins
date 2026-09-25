---
title: 请求以精确匹配解析，未命中一律 404 JSON
description: path 逐字符精确匹配（query 剥离、大小写敏感、尾部斜杠不归一）；未命中返回 404 加 JSON 错误体而非空体或 501。
type: decision
tags: [contract, http]
---

# 请求以精确匹配解析，未命中一律 404 JSON

命中定义为：method 大小写不敏感（HTTP 惯例），path 剥离 query string 后与路由 path 逐字符相等。不做前缀/通配符/路径参数匹配——静态契约的每条路由都应显式可枚举。未命中一律 `404` + `{"error": "No mock for <METHOD> <path>"}`：错误体直接告诉调用方「服务认为这个请求没有对应 mock」，把契约排错从查日志变成读响应。

## Considered Options

- 尾部斜杠归一 / 大小写不敏感 path：URL 语义上它们就是不同资源，mock 的职责是精确复刻而非宽容，否决；
- 未命中返回 501：部分 mock 工具的语义，但「这个 path 没配」对客户端就是资源不存在，404 更符合直觉，否决。

## Consequences

- 客户端请求带尾部斜杠或路径参数时不会命中——这是有意为之的严格性，契约里必须显式列出每个精确 path。

## Revisit When

- 出现真实需求：同一资源族（如 /api/users/1..N）需要成批模拟时，再讨论路径模板扩展，而不是先放开宽松匹配。

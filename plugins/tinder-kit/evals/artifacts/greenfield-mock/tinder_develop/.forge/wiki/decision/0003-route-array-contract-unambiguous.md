---
title: 契约采用路由对象数组且必须无歧义
description: mocks.json 顶层为 { routes: [...] } 路由对象数组；method 缺省 GET、status 缺省 200；重复 method+path 是契约错误。
type: decision
tags: [contract, mocking]
---

# 契约采用路由对象数组且必须无歧义

mocks.json 顶层是 `{ "routes": [...] }`，每个元素是带 `method`（缺省 GET）、`path`、`status`（缺省 200）、`body`、`headers` 的对象。数组形态让「同一 path 多方法」与未来的匹配维度扩展都不破坏既有契约文件；`method + path` 重复视为契约错误而非静默取首条——mock 契约应当无歧义，静默优先级规则会把踩雷延迟到最难受的调试时刻。

## Considered Options

- `"GET /api/user"` 字符串作 key 的映射：写起来短，但多方法同路径、按方法扩展匹配维度都要破坏格式，否决。

## Consequences

- 契约文件比映射形态多几行样板（每个路由显式写 method/path）。

## Revisit When

- 无——文件格式是公开接口，变更即破坏用户已有 mocks.json；只做向后兼容的增补。

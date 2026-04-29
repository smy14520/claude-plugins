# 页面类型与内容契约

`.wiki/` 页面按用途写，不按僵硬抽屉写。所有页面都应有 `description`，方便 `wiki-index/search/collect` 给 AI 快速判断是否需要细读。

## 通用 frontmatter

```yaml
---
title: <Title>
description: <one-line retrieval hook>
tags: [<domain>, ...]
type: entity | concept | gotcha | decision | source | module
summary: <compact summary>
---
```

## type: module

来自 sdd-kit package 的稳定模块卡片。通常由 `sdd-arbor module-summary <package> --json` 生成 packet 后写入。

推荐位置：`.wiki/Modules/<Title>.md`。

必需 frontmatter：

```yaml
---
title: Balance Ledger
description: 余额账户、流水、充值、扣款、退款和幂等 contract
tags: [module, backend, ledger]
type: module
package: balance-ledger
source: arbor
source_checkpoint: <sha>
summary: <compact summary>
---
```

推荐结构：

```markdown
# Balance Ledger

## Summary
## Public contracts
## Key files and stable locators
## Invariants
## Tests
## Related modules
## Verification notes
```

Module note 不写 line numbers。定位用：

- file path + class/function/method name
- route name / API operation id
- table / index / migration id
- config key / env key
- test name
- contract request id

## type: entity

真实对象：服务、API、数据库表、外部系统、队列、存储。记录跨文件才能重建的信息、边界、调用拓扑、不可见约束。

## type: concept

抽象模式或方法论。去掉专有名词后仍成立。写适用场景、核心思想、权衡、应用示例。

## type: decision

记录选择及理由。写背景、选项、决定、后果、何时重审。

## type: gotcha

具体场景 + 具体症状 + 根因 + 已验证解决方案。保持短小。

## type: source

外部资料摘要。保留来源、为什么重要、关键摘录、适用边界。

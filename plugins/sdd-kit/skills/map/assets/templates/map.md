---
project: <project-name>
status: draft | active | stable | archived
updated: YYYY-MM-DD
source_research: <research-topic | null>
---

# <project-name> map

<!-- 输出语言: 中文 -->
<!--
  Map 是大项目结构导航，不是 PRD，也不是 task。
  保持短、准、可导航；不要记录冗长过程日志。
-->

## Project framing

<当前对这个大项目/上位主题的一句话理解。>

## Domains / bounded task packages

| Domain | Package | PRD status | Task status | Notes |
|---|---|---|---|---|
| <domain-name> | `.arbor/tasks/<package>/` | not-started | not-started | <notes> |

PRD status values:
- `not-started`
- `researching`
- `draft`
- `ready-for-task`
- `revising`
- `blocked`

Task status values:
- `not-started`
- `in-task`
- `ready`
- `in-impl`
- `in-review`
- `done`
- `blocked`

## Cross-domain contracts

| Contract | Producer | Consumers | Status | Notes |
|---|---|---|---|---|
| <contract-name> | <domain> | <domain-a, domain-b> | draft | <notes> |

Status values:
- `unresolved`
- `draft`
- `stable`
- `blocked`

## Shared capabilities

- <shared capability>

## Dependency graph

```text
<domain-a>
  -> <domain-b>
```

## Open blockers

- <blocker>

## Recommended next move

1. <next step>

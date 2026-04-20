---
spec: <spec-name or null if ad-hoc>
mode: strict-atomic | lean
date: YYYY-MM-DD
status: draft | confirmed | in-progress | done
---

# 任务: <feature-name>

<!-- 输出语言: 中文 -->

<!--
  任务文件约定（强制执行）：
  - 禁止 wikilinks。本文件应自包含。
  - 禁止决策。每个任务仅包含可执行操作。
  - ID 只允许追加，不得重新编号。
  - 每条验收条件必须是可执行命令或二元谓词。
  - 仅允许封闭动词：CREATE | ADD | SET | DELETE | REPLACE，并附带具体目标值。
    开放动词（校准 / 保持 / 验证 / 确保 / 适配）表示来源规格中存在未解决的
    `<TODO-DECIDE>` — 应退回规格，不得将模糊性带入任务。
-->

## 概览

- 模式: <strict-atomic | lean>
- 总任务数: <N>
- 总预估工时: <hours>
- 关键路径: <T-xxx → T-yyy → T-zzz = Nh>

## 依赖关系图

```
T-001 (data)
  ↳ T-003 (backend)
       ↳ T-005 (test)
T-002 (shared)
  ↳ T-003 (backend)
  ↳ T-004 (backend)
T-007 (devops, standalone)
```

## 任务列表

- id: T-001
  role: data
  title: "Migration: create xhs_events table"
  deliverable: "db/migrations/NNNN_create_xhs_events.sql"
  depends-on: []
  acceptance: |
    - file: db/migrations/NNNN_create_xhs_events.sql exists
    - run: `pnpm db:migrate` applies without error
    - schema: xhs_events(id, event_id UNIQUE, payload, processed_at, created_at)
  estimate: 1h
  notes: ""

- id: T-002
  role: shared
  title: "Signature verifier utility"
  deliverable: "src/lib/signature-verifier.ts"
  depends-on: []
  acceptance: |
    - file: src/lib/signature-verifier.ts exports verifyHmac(payload, sig, secret, maxSkewMs)
    - run: `pnpm test src/lib/signature-verifier.test.ts` passes
    - covers: valid sig → true; invalid → false; clock skew > 5min → false
  estimate: 2h
  notes: ""

- id: T-003
  role: backend
  title: "POST /webhook/xhs handler"
  deliverable: "src/webhooks/xhs-handler.ts"
  depends-on: [T-001, T-002]
  acceptance: |
    - file: src/webhooks/xhs-handler.ts exports handleXhsWebhook(req): Response
    - on valid signed request: writes to xhs_events, returns 200
    - on invalid signature: returns 401
    - on duplicate event_id: returns 409 (idempotency)
    - emits metric: webhook.xhs.received
  estimate: 3h
  notes: "Uses T-002 verifier. Reads secret from env XHS_WEBHOOK_SECRET."

# ... 追加更多任务，ID 递增 ...

## 状态日志

（实现技能在任务推进时追加。请勿手动编辑。）

<!-- format: `- [x] T-NNN (STATE) — YYYY-MM-DD HH:MM — note` -->
<!-- STATE ∈ { DONE | DONE_WITH_CONCERNS | NEEDS_CONTEXT | BLOCKED } -->

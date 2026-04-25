---
package: <feature-name>
source: prd.md
source_type: package-prd | legacy-brainstorm | ad-hoc
mode: strict-atomic | lean
date: YYYY-MM-DD
---

# 任务: <feature-name>

<!-- 输出语言: 中文 -->
<!--
  任务定义约定（强制执行）：
  - 禁止 wikilinks。本文件应自包含。
  - 禁止高层决策。每个任务仅包含可执行操作。
  - ID 只允许追加，不得重新编号。
  - 每条验收条件必须是可执行命令或二元谓词。
  - 每个任务必须有 task-local context、sources 和 ready-check。
  - impl 不得修改本文件；执行状态只写入 task.json。
  - review 不得修改本文件；审计记录追加到 review.md，latest review state 写入 task.json。
-->

## 概览

- 来源: `prd.md`
- 模式: <strict-atomic | lean>
- 总任务数: <N>
- milestone 数: <N>
- 总预估工时: <hours>
- 关键路径: <T-xxx → T-yyy → T-zzz = Nh>

## Milestones

### M-01 — <里程碑名称>

- 目标:
- 包含任务: [T-001, T-002]
- 完成判定:

### M-02 — <里程碑名称>

- 目标:
- 包含任务: [T-003, T-004]
- 完成判定:

## 依赖关系图

```text
M-01
  T-001 (shared)
  T-002 (backend)
M-02
  T-003 (backend) depends on T-001, T-002
  T-004 (test) depends on T-003
```

## 任务列表

- id: T-001
  milestone: M-01
  role: shared
  title: "ADD signature verifier utility"
  deliverable: "src/lib/signature-verifier.ts"
  depends-on: []
  context: |
    本任务只负责抽出可复用的签名校验能力，供后续 handler 复用。
    不负责 webhook handler 本身。
  sources:
    - SRC-RES-001
    - SRC-LOCAL-001
  ready-check: |
    - ready: true
    - blockers: []
  acceptance: |
    - file: src/lib/signature-verifier.ts exports verifyHmac(payload, sig, secret, maxSkewMs)
    - run: `pnpm test src/lib/signature-verifier.test.ts` passes
  estimate: 2h
  notes: ""

- id: T-002
  milestone: M-01
  role: backend
  title: "ADD POST /webhook/xhs handler"
  deliverable: "src/webhooks/xhs-handler.ts"
  depends-on: [T-001]
  context: |
    本任务聚焦 webhook handler 主流程：验签、入队、返回响应。
    不在此任务内完成 dashboard 或管理后台逻辑。
  sources:
    - SRC-RES-002
    - SRC-EXT-001
  ready-check: |
    - ready: false
    - blockers:
      - replay window 尚未冻结；需在上游确认 24h 或 7d
  acceptance: |
    - file: src/webhooks/xhs-handler.ts exports handleXhsWebhook(req)
    - on valid signed request: returns 200
    - on invalid signature: returns 401
  estimate: 3h
  notes: ""

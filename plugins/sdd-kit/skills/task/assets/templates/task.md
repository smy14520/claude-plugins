---
package: <feature-name>
source: prd.md
source_type: package-prd | legacy-brainstorm | ad-hoc
mode: strict-atomic | lean
date: YYYY-MM-DD
---

# 任务: <feature-name>
<!--
  任务定义约定（强制执行）：
  - 禁止 wikilinks。本文件应自包含。
  - 禁止高层决策。每个任务仅包含可执行操作。
  - ID 只允许追加，不得重新编号；T-xxx 只在本 package 内唯一。
  - Package 是需求/评审/回滚边界；T-xxx 是 package-local control / acceptance / review 单元。
  - 不要为每个 T-xxx 默认创建独立 branch/PR；如需独立交付边界，应拆成新的 package。
  - 每条验收条件必须是可执行命令或二元谓词。
  - 每个任务必须有 task-local context、sources 和 ready-check。
  - impl 不得修改本文件；执行状态只写入 task.json。
  - review 不得修改本文件；审计记录追加到 review.md，latest review state 写入 task.json。
  - Definition frozen 表示已有 T-xxx 不可改写；task skill 仍可为 AMD-xxx 追加新 T-xxx。
  - Amendment task 必须写 source-amendment/corrects，并包含 increment + regression acceptance。
-->

## 概览

- 来源: `prd.md`
- 模式: <strict-atomic | lean>
- Package boundary: `.arbor/tasks/<feature-name>/`（需求/评审/回滚边界）
- T-xxx scope: package-local control / acceptance / review，不是默认 PR 单元
- Boundary sizing decision from brainstorm/map: <fits_package | split_applied> — <为什么当前 package 边界成立；若拆过，列出来源/去向 package>
- Parent map / initiative: <.arbor/maps/<initiative>/map.md | none>
- Package PR readiness: 所有 required T-xxx 通过 review，且无 package-level blocker
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

## 并行执行提示

本节只用于人工 / Team Auto / 多会话分工，不代表自动 scheduler。并行前先确认依赖、shared contract 和文件/资产 ownership。

### Role lanes

- shared / lead: [T-001]
- backend: [T-002, T-003]
- frontend: []
- test: [T-004]
- docs / devops: []

### Suggested waves

- Wave 0: T-001 shared contract
- Wave 1: T-002 backend
- Wave 2: T-003 backend + T-004 test（仅当 T-004 的 ready-check 已满足）

### Ownership notes

- shared/global 文件 owner: <T-xxx / lane>
- 只读边界: <哪些 lane 只能读取、不能修改的目录 / 文件 / 资产>
- 对接规则: contract 不清或需要跨 lane 修改时，停止并问 lead，不要猜。
- worktree: role lane ownership 清楚时默认不需要；候选实现隔离或写入重叠时再使用。

## 任务列表

- id: T-001
  milestone: M-01
  role: shared
  source-amendment: AMD-001        # optional; only for forward-only correction tasks
  corrects: [T-003]               # optional; old T-xxx this task amends/replaces
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
    - increment: file src/lib/signature-verifier.ts exports verifyHmac(payload, sig, secret, maxSkewMs)
    - regression: run `pnpm test src/lib/signature-verifier.test.ts` passes
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
    - increment: src/webhooks/xhs-handler.ts exports handleXhsWebhook(req)
    - increment: on valid signed request returns 200
    - regression: on invalid signature returns 401
  estimate: 3h
  notes: ""

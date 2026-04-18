# Task workflow: Decompose / Identify-shared / Order / Assign-role

Detailed procedures for the four primitives. SKILL.md gives the high-level steps; this file gives the full workflow including edge cases.

---

## Decompose

Split spec into atomic units.

### Trigger phrases

- "拆任务 X" / "把 spec X 变成任务"
- "plan X" / "break down spec X"
- "生成 task 计划"

### Full procedure

**Step 1 — Resolve input**

Case A: `.claude/specs/<name>.md` exists

- Read it. Check `status:` frontmatter:
  - `accepted` → proceed
  - `draft` / `revising` → block: "spec `<name>` 仍是 draft / revising，请先 finalize 再拆任务。"
  - `superseded` → ask: "此 spec 已 superseded by `<new>`. 用新 spec 吗？"

Case B: no spec, user gave in-session goal

- Confirm the goal in one line back to user:
  - "理解的目标: `<goal>`. Acceptance: `<criteria>`. 对吗？"
- Only after user confirms, proceed
- Create task file anyway, even without spec reference

**Step 2 — Ask mode**

```
📋 拆任务模式:
  (a) strict-atomic — 每个任务 ≤ 4h, 单一 deliverable, 适合并行 / 多 agent
  (b) lean          — 任务可到 1 天, 适合单人快速推进
  默认: (a) strict-atomic

选哪个？
```

Wait for user choice before proceeding. Record choice in task file frontmatter.

**Step 3 — Split**

From spec's Acceptance + Data/state + Interface + Test strategy sections, derive units. Each unit should be:

- A single deliverable (one new file, one modified file, one endpoint, one migration, one test suite)
- Independently verifiable (has a concrete "done" check)
- Under the mode's size budget

Typical seed buckets (not exhaustive):

- Data: migrations, schema changes, seed data
- Core logic: pure functions, domain models
- Integration: HTTP handlers, event producers, message consumers
- Cross-cutting: config, secrets, feature flags
- Observability: metrics, logs, traces
- Tests: unit, integration, load

**Step 4 — Assign stable IDs**

Format: `T-001`, `T-002`, …, zero-padded to 3 digits. IDs are append-only; never renumber.

When editing an existing task file: new tasks get IDs = max(existing) + 1.

**Step 5 — Fill required fields per task**

For each task, per [content-contract](#required-task-fields) below. Populate:

- `id`
- `role` (default `unassigned`)
- `title` (one line, imperative)
- `deliverable` (concrete artifact)
- `depends-on` (list of IDs, possibly empty)
- `acceptance` (command or file-state check)
- `estimate` (hours)
- `notes` (optional, for non-obvious context)

**Step 6 — Emit draft for confirmation**

Before writing final file, emit task list inline for user review:

```
📝 Task draft (strict-atomic, 12 tasks):

T-001 [data/shared] migration: xhs_events table — 1h
T-002 [shared] signature-verifier util — 2h
T-003 [backend] POST /webhook/xhs handler — deps: T-001, T-002 — 3h
...

对吗？(y / edit: 改/删/加哪一条)
```

Wait for confirmation / edits. Do NOT write the final file until user confirms.

### Required task fields

```yaml
- id: T-001
  role: backend | frontend | data | devops | shared | test | unassigned
  title: "<imperative action>"
  deliverable: "<concrete artifact: file path / endpoint / migration name>"
  depends-on: [T-000, ...]      # list of IDs; can be empty
  acceptance: |
    - file: src/xxx.ts exists with <signature>
    - run: `pnpm test tests/xxx.test.ts` passes
    - or: `curl -X POST localhost:3000/yyy` returns 200
  estimate: 2h
  notes: |
    Optional. Non-obvious context for the executor.
    Do NOT put decision content here; decisions belong in spec.
```

### Edge cases

**Case: spec has an open `<TODO-DECIDE>` marker**

Block: "spec `<name>` 仍有 `TODO-DECIDE`。请先回到 spec skill 完成决策，再拆任务。" Provide grep line numbers.

**Case: spec is too abstract to decompose**

Ask: "spec 的 Acceptance 只有 N 条且偏抽象，我拆出来的会是 coarse 颗粒度。要不要先把 spec 的 Acceptance 细化？" Let user choose: detail spec vs accept coarse tasks.

**Case: user wants to add/remove a task mid-plan**

Always possible. For add: new ID. For remove: mark `status: dropped` in the task block rather than deleting (preserves git history). For change: edit in place, but task IDs stay.

---

## Identify shared

Find repeated concerns across tasks; extract as shared-module tasks.

### When to run

- Automatically during Decompose, after initial split
- Or explicitly when user asks "有哪些公共模块"

### Procedure

**Step 1 — Scan task list for duplicate deliverables**

Look for patterns:

- 3+ tasks all call "signature-verifier" → extract `T-XXX signature-verifier util` with `role: shared`
- 2+ tasks touch the same config loader → extract shared config task
- Multiple tasks reference the same HTTP client → extract shared client

**Step 2 — Create shared task**

- `role: shared`
- `depends-on:` usually `[]` (shared modules are leaves)
- Clear acceptance: the module is importable and has its own unit tests

**Step 3 — Retarget dependent tasks**

Consumer tasks add the new shared task to their `depends-on`.

**Step 4 — Warn if shared count is high**

If `shared` role tasks > 30% of total → emit warning:

```
⚠️ Shared tasks 占比 X%. 可能存在以下信号:
   - 提前抽象（YAGNI 违反）
   - spec 本身过于模块化，应直接描述更粗的交付物

要继续这种颗粒度吗？
```

### Edge cases

**Case: shared module is trivial (< 30 LoC)**

Do not extract as separate task. Inline into the first consumer; add a note.

**Case: shared module is genuinely cross-spec**

If the shared module is also consumed by other specs (or existing code), note: "此 shared module 可能 affects 其他 spec，需要 cross-spec 协调。" Flag to user.

---

## Order

Build the DAG of `depends-on` relations.

### Procedure

**Step 1 — Collect depends-on edges**

```
T-003 depends on: T-001, T-002
T-005 depends on: T-003
```

**Step 2 — Cycle check**

DFS for cycles. If found:

```
❌ 依赖环:
   T-003 → T-005 → T-003

这是设计冲突，不是任务颗粒度问题。建议:
- 拆分其中一个任务
- 或引入中间层抽象 (新增 shared task)
```

**Step 3 — Emit DAG as text**

Use a simple ASCII or mermaid tree. Do not over-stylize.

```
Dependency order:
  T-001 (data)
  T-002 (shared)
    ↳ T-003 (backend) → T-005 (test)
    ↳ T-004 (backend) → T-006 (test)
  T-007 (devops, standalone)
```

**Step 4 — Identify critical path**

Sum estimates along the longest dependency chain. Emit:

```
Critical path: T-002 → T-003 → T-005 → T-006 = 9h
Total estimate: 18h
Max parallel branches: 3
```

### Edge cases

**Case: everything is sequential**

If no parallelism possible (every task depends on the prior one), note: "all tasks form a linear chain — no parallelism possible. strict-atomic mode may be over-kill; 考虑 lean."

**Case: DAG is very wide (many leaves)**

Good for parallelism. Emit the leaves list so user knows which can start immediately.

---

## Assign role

Optionally annotate each task with a role tag. Roles are advisory.

### Standard roles

- `backend` — server-side code, APIs, business logic
- `frontend` — UI, client-side logic
- `data` — schema, migrations, ETL
- `devops` — infra, CI, deploys, secrets
- `shared` — cross-role utilities
- `test` — test-only deliverables
- `unassigned` — default, when role unclear

### Procedure

**Step 1 — Infer from deliverable**

- `migration: xhs_events table` → `data`
- `POST /webhook/xhs handler` → `backend`
- `src/lib/signature-verifier.ts` → `shared`
- `tests/webhook.test.ts` → `test`
- `terraform: add new topic` → `devops`

**Step 2 — Ask user to confirm**

```
📝 Role 分配建议 (可改):
  T-001 data
  T-002 shared
  T-003 backend
  T-004 backend
  T-005 test
  T-006 test
  T-007 devops

修改吗？
```

**Step 3 — Custom roles**

User may define project-specific roles (e.g. `ml`, `mobile-ios`). Accept and record in task frontmatter.

### Edge cases

**Case: role is ambiguous**

Tag `unassigned` and note in task's `notes:` field. Do not guess.

**Case: user skips role assignment**

Fine. All tasks become `role: unassigned`. Impl skill will still work — it reads tasks regardless of role.

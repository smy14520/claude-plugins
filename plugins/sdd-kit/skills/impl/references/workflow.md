# Impl workflow: Pick / Execute / SelfCheck / Report

Detailed procedures for the four primitives. SKILL.md gives high-level steps; this file gives the full workflow including edge cases and ad-hoc mode.

> **Scope reminder**: Impl's `SelfCheck` runs the task's own `acceptance:` commands. It does NOT perform semantic audit against spec — that is the `review` skill. Keeping these separate prevents impl's limited-context view (task-only) from silently approving work that drifts from spec.

---

## Pick

Select which task to execute.

### Trigger phrases

- "实施 T-003" (explicit task ID)
- "执行下一个 task"
- "run next task for spec X"
- "start impl on <task-file>"

### Full procedure

**Step 1 — Locate task file**

Case A: user names a file → use it
Case B: user names a spec → look for `.claude/tasks/<spec>.tasks.md`
Case C: neither → list recent task files:

```bash
ls -t .claude/tasks/*.tasks.md | head -5
```

Ask: "找到以下 task 文件，选哪个？" or proceed with the most recent + asking for confirmation.

Case D: no task file exists → enter **ad-hoc mode** (see below).

**Step 2 — Read task list + status log**

Parse all tasks and their current status from the `## Status log` section.

Classify each task as:

- **Pending** — no status line yet
- **DONE** — last status is DONE (not eligible for re-run)
- **DONE_WITH_CONCERNS** — last status DWC (eligible for re-run if user wants)
- **NEEDS_CONTEXT** / **BLOCKED** — waiting on external resolution
- **Dropped** — `status: dropped` in task block

**Step 3 — Find eligible tasks**

Eligible = Pending + all `depends-on` IDs are DONE or DONE_WITH_CONCERNS.

If user named a specific ID → confirm eligibility; if its deps are incomplete, emit:

```
⚠️ T-003 depends on T-001, T-002. 当前状态: T-001=DONE, T-002=NEEDS_CONTEXT.
建议先解决 T-002，或明确你要 (a) 强制执行 T-003, (b) 切到 T-002, (c) 取消。
```

If user said "下一个" → pick lowest-ID eligible task. Confirm before proceeding:

```
下一个: T-003 `<title>`
  Role: backend
  Deliverable: src/webhooks/xhs-handler.ts
  Estimate: 3h
  Depends-on: T-001 (DONE), T-002 (DONE)

开始？(y/n/选其他)
```

**Step 4 — Read spec (optional context)**

If the task references a spec (task file frontmatter `spec: <name>`), read the spec once for context. Do NOT re-derive anything from spec that already exists in the task's acceptance / notes.

### Edge cases

**Case: all tasks DONE**

Emit: "所有任务已完成 (N/N DONE). 建议 lint spec 与代码一致性，或关闭此 task file。"

**Case: task file has circular dependencies**

Block: "依赖环检测到 T-00X → T-00Y → T-00X. 这是 task-phase 问题，不是 impl 能解决的。请返回 task skill 修复。"

**Case: user wants to re-run a DONE task**

Ask: "T-003 已 DONE on <date>. 原因？(a) 代码被改动, (b) acceptance 需重跑, (c) 其他". 继续只在用户明确后。

### Ad-hoc mode (no task file)

User says "实现 X" without a task file.

**Step A1 — Confirm scope**

Ask:

```
没有 task 文件。进入 ad-hoc 模式。请确认:
  1. Deliverable (文件/模块/端点)?
  2. Acceptance (怎么算 DONE?命令/行为?)
  3. 是否先写一个 minimal tasks file (1 个任务) 再执行？
```

Wait for answer. If user wants minimal task file → invoke task skill with 1-task seed.

**Step A2 — Same execution flow**

Otherwise, treat user's answer as the task. Create an in-memory task object with the same fields. Run Execute → SelfCheck → Report as normal.

**Step A3 — Status lives where?**

Without a task file, status goes to:

- User-visible summary (mandatory)
- `.claude/impl-logs/<name>.log.md` if user wants persistent trace (optional, created on demand)

---

## Execute

Write the code.

### Full procedure

**Step 1 — Read deliverable + acceptance + notes**

Commit the target state to memory:

- What files change
- What acceptance criteria must hold
- Any notes about non-obvious context

**Step 2 — Plan the minimal diff**

Mental model: "the smallest change that makes all acceptance criteria pass". No speculative additions, no adjacent refactors.

**Step 3 — Make the edits**

Prefer minimal focused edits. Follow existing style. Don't add unsolicited comments. Align with project conventions (read nearby code for style).

**Step 4 — Handle ambiguity**

If at any point during Execute you find:

- Spec says X but task says Y → STOP. NEEDS_CONTEXT: "spec 和 task 冲突 on <point>"
- Acceptance mentions a file/command that doesn't exist → STOP. NEEDS_CONTEXT: "acceptance 引用了 <path>，但不存在"
- A design choice is needed (e.g. "should the cache key include user_id?") → STOP. NEEDS_CONTEXT: "需要决策: <question>"

Do NOT attempt a workaround. Emit NEEDS_CONTEXT state and hand back.

**Step 5 — Handle blockers**

If environment prevents progress (dep not installed, service not running, migration can't apply):

- Try ONE reasonable recovery (e.g. install missing dep)
- If recovery fails or requires external action → STOP. BLOCKED: "<blocker description>"

### What counts as a design decision (NEEDS_CONTEXT triggers)

- Choosing an algorithm when spec gave options
- Picking naming / path / table column not specified
- Choosing whether to implement feature A that's "probably implied"
- Deciding retry count / timeout when spec didn't specify

### What does NOT count as a design decision (proceed silently)

- Choosing local variable names
- Choosing internal helper function structure
- Choosing private import order
- Formatting decisions the linter would normalize

The line: would a reviewer reasonably call out your choice? If yes → ask / NEEDS_CONTEXT.

---

## SelfCheck

Run the task's acceptance commands. Report facts, not feelings. This is **self**-check (run your own acceptance), not semantic review (which is the `review` skill).

**What SelfCheck is NOT for**:

- Deciding whether the code truly solves the user-level problem (review)
- Comparing implementation against spec constraints (review)
- Consulting wiki for relevant gotchas (review)
- Looking at git diff beyond the current task's files (review)

**What SelfCheck IS for**:

- Running every `acceptance:` command in the task
- Reading their exit codes and output carefully
- Refusing to claim DONE when any acceptance fails

### Full procedure

**Step 1 — Parse acceptance block**

Extract each command or predicate from `acceptance:` field.

**Step 2 — Run in order**

For commands: execute with timeout. Capture exit code + last ~40 lines of output.

For file-state predicates: read the file, check the exported signature / content against acceptance.

For HTTP predicates: run the curl or equivalent, parse response.

**Step 3 — Collect results**

```
acceptance 1/3: `pnpm test tests/webhooks/xhs.test.ts` → exit 0 ✅
acceptance 2/3: file src/webhooks/xhs-handler.ts exports handleXhsWebhook(req) → ✅
acceptance 3/3: `curl -X POST localhost:3000/webhook/xhs ...` → HTTP 200 ✅
```

**Step 4 — Decide state**

All pass + no concerns during Execute → **DONE**
All pass + concerns noted (compromise, tech debt, non-ideal) → **DONE_WITH_CONCERNS**
Any fail and failure is acceptance-related → report as **BLOCKED** (or NEEDS_CONTEXT if it's an ambiguity)

### Edge cases

**Case: acceptance is a manual check**

If an acceptance criterion requires human eyes (e.g. "UI looks correct"):

- Run automated parts
- For manual: emit "DONE-PENDING-MANUAL: <criterion> — 请人工确认后在 status log 改 [x]"

**Case: acceptance command itself is broken**

If `pnpm test path/xxx.test.ts` fails because of a toolchain issue (not the code under test):

- BLOCKED: "toolchain error <detail>, cannot SelfCheck"
- Do NOT interpret toolchain failure as code failure

**Case: acceptance passes but other tests break**

If running `pnpm test` (broader than the task's acceptance) reveals unrelated breakage:

- Report DONE on this task (acceptance passed)
- Note in status line: "note: pnpm test (broader) shows N pre-existing failures in <area>"
- Flag to user: "此任务 DONE, 但观察到项目整体测试有问题。单独开任务还是忽略？"

---

## Report

Append status line to task file + emit structured summary.

### Full procedure

**Step 1 — Write status line**

Format per SKILL.md. Append to the task file's `## Status log` section.

Do NOT edit other parts of the task file.

**Step 2 — Emit summary to user**

```
✅ T-003 (DONE) — 2025-04-18 14:20

Deliverable: src/webhooks/xhs-handler.ts (+42 lines)
Verified:
  ✅ pnpm test tests/webhooks/xhs.test.ts (3/3 pass)
  ✅ file exports signature match
  ✅ curl smoke 200

Remaining tasks: 4
Next eligible: T-004, T-005

继续下一个？(说 "continue" / "do T-00X" / 或停下做别的)
```

For DONE_WITH_CONCERNS, add concerns block:

```
⚠️ T-003 (DONE_WITH_CONCERNS) — 2025-04-18 14:50

Concerns:
  - retry logic uses fixed 3 tries, no exponential backoff (spec said "retry", not "backoff")
  - skipped input fuzzing (not in acceptance)
Recommendation: 回头可以 follow-up task T-0NN 加 backoff
```

For NEEDS_CONTEXT:

```
🟡 T-003 (NEEDS_CONTEXT) — 2025-04-18 15:10

Blocked at: ambiguity on replay window duration
Needed: 24h or 7d?
Source of ambiguity: spec §Constraints "idempotent" without TTL; task acceptance says "24h" but comment says "align with wechat (7d)"
Suggested resolution: return to spec, add explicit TTL
No code changes committed.
```

For BLOCKED:

```
🔴 T-003 (BLOCKED) — 2025-04-18 15:30

Blocker: postgres version mismatch
  local: postgres 14.x
  expected: postgres 15.x (migration uses 15-only syntax)
Tried: `brew install postgres@15` — needs sudo / user action
No code changes committed.
Unblock path: align postgres version or rewrite migration for 14 compat (decision needed).
```

**Step 3 — Update impl-log if multi-task run**

If user is running multiple tasks in one session, maintain `.claude/impl-logs/<name>.log.md`:

```markdown
## [2025-04-18 14:20] T-003 DONE
- deliverable: src/webhooks/xhs-handler.ts
- selfcheck: 3/3 pass
- duration: 2h 40min

## [2025-04-18 15:10] T-005 NEEDS_CONTEXT
- blocked at: replay window ambiguity
- duration: 0h 20min
```

Single-task runs don't need impl-log; summary suffices.

**Step 4 — Wiki-ingest suggestion (conditional)**

**Trigger**: state is `DONE_WITH_CONCERNS` or `BLOCKED`. **Never** trigger on `DONE` (nothing to ingest) or `NEEDS_CONTEXT` (task not complete — premature to extract knowledge).

**Decide suggested page type**:

| State | Suggested type | Page-name pattern |
|-------|----------------|-------------------|
| `DONE_WITH_CONCERNS` with concrete compromise | `gotcha` | `<domain>-<scenario>` (e.g. `xhs-signature-clock-skew`) |
| `DONE_WITH_CONCERNS` due to a design trade-off | `decision` | `<choice>-for-<domain>` (e.g. `fixed-retry-vs-backoff-for-xhs`) |
| `BLOCKED` by env mismatch | `gotcha` | `<tool>-<version-issue>` (e.g. `postgres-14-vs-15-migration`) |
| `BLOCKED` by upstream unresolved dep | (no suggestion — this isn't knowledge, it's process) | — |

**Emit format** (append to the Report summary block):

```
💡 Knowledge worth ingesting (you decide; nothing saved until you run /sdd-kit:wiki):

   Suggested page: [[xhs-signature-clock-skew]]
   Type: gotcha
   Draft:
     ## Trigger
     Local-to-server clock drift > 5 min causes HMAC timestamp mismatch.
     ## Symptoms
     XHS webhook returns 401 "signature expired".
     ## Root cause
     Server validates ts within 300s window; our NTP sync was stale.
     ## Fix
     Added chrony to dev env; task T-003 status line file:line.

   Command to ingest:
     /sdd-kit:wiki ingest gotcha xhs-signature-clock-skew
```

**Rules**:

1. **Never auto-ingest.** The command line is for the user to copy-paste, not for impl to execute.
2. **Draft must be specific.** No generic placeholders like "[describe the issue]". Fill from the actual concern/blocker text.
3. **Reference the task.** Include `task: T-00X` and relevant `file:line` pointers in the draft so the wiki page is traceable back.
4. **Skip if BLOCKED is process-only.** E.g. "waiting on T-001 NEEDS_CONTEXT" is not knowledge, so do not suggest a page.
5. **Suggest once per task run.** If impl is re-run on the same task and state is still DWC/BLOCKED, still include the suggestion each time (user may have ingested already — that's fine, wiki ingest will detect collision).

**Rationale** (short version):

- DONE_WITH_CONCERNS captures the most valuable tacit knowledge — "it works but here's what we compromised on". Not capturing this wastes it.
- BLOCKED by env mismatch is a repeat-pain pattern that wiki's gotcha page type is designed for.
- Keeping this as a suggestion (not auto-ingest) preserves the "可控优先" principle — user stays in the loop on what becomes persistent knowledge.

**Step 5 — Do NOT auto-advance**

Always stop after one task's Report. User says "continue" to proceed.

### Edge cases

**Case: user pre-says "run all tasks"**

Allowed, but:

- Still report per-task status
- Stop on first NEEDS_CONTEXT or BLOCKED (do not skip)
- Summary at end: "Ran N tasks, M DONE, K with concerns, stopped at T-00X (state)"

**Case: repeated ingest suggestions for the same concern**

If the task cycles DONE_WITH_CONCERNS → rework → DONE_WITH_CONCERNS (same concern), still emit the suggestion each time. Wiki ingest itself handles dedup (page-exists prompt per `references/operations.md#ingest` Step 3).

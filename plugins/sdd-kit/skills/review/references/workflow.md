# Review workflow: Collect / Judge / Report

Detailed procedures for the three primitives. SKILL.md gives high-level steps; this file gives the full workflow including edge cases and multi-task review.

> **Scope reminder**: Review performs **semantic audit** of impl output against spec + diff + (optional) wiki. It NEVER mutates code, spec, or task. Its only write operation is appending to the task file's `## Review log` section.

---

## Collect

Gather the context needed to judge.

### Trigger phrases

- "review T-003"
- "audit impl"
- "check if this matches spec"
- "cross-check the implementation"
- explicit slash command: `/sdd-kit:review <task-id-or-file>`

### Full procedure

**Step 1 — Resolve target**

User input forms:

- `T-003` (task ID, most common)
- `.claude/tasks/xhs-webhook.tasks.md` (explicit file path)
- "the last DONE" (scan most-recent task file for DONE/DWC line)
- `HEAD~1..HEAD` (git range, ad-hoc review)

If ambiguous (multiple DONE lines across multiple files): list and ask one clarifying question.

**Step 2 — Resolve the spec**

From the task file's header (task files typically have `spec: <path>` frontmatter or an explicit "derived from spec: X" note).

If task is ad-hoc (no spec): fall back to a **lightweight review** — use user-stated goal as the spec proxy and flag the lightness in the review line.

Read `.claude/specs/<name>.md` fully. Pay attention to:

- `## Goal` (one sentence)
- `## Non-goals` (explicit exclusions)
- `## Hard constraints` (SLOs, rate limits, invariants, security)
- `## Interface` (public API contract)
- Any `## Data / State` invariants

**Step 3 — Read the task entry + status log**

- Find the specific task (e.g. `T-003`) in the task file
- Read its `deliverable:` and `acceptance:` for scope clarity
- Scan `## Status log` for the DONE/DWC line — note the timestamp and any concerns block

**Step 4 — Inspect the actual diff**

MANDATORY. Run:

```bash
git log --oneline --all -- <task's deliverable files>
# Identify the commits that belong to this task
git diff <base>..HEAD -- <changed-files>
```

If you don't know the base commit, ask the user:

```
Review 需要 git diff 作为证据。请告诉我:
  a) 这次 task 从哪个 commit 开始？(commit hash / branch)
  b) 或者直接让我看 <branch-A>..<branch-B> 的差异？
  c) 或者 HEAD~N..HEAD 中的 N?
```

**Step 5 — Optional wiki query**

If the diff touches a domain that has wiki coverage (e.g. xhs, auth, migrations):

- Query wiki for `[[gotcha-<domain>-*]]` pages
- Query wiki for `[[decision-<topic>]]` pages referenced by the spec

This is advisory. If wiki is empty or not scoped to this domain, skip.

**Step 6 — Assemble the evidence packet**

Before moving to Judge, make sure you have:

- ✅ Spec text (goal / non-goals / constraints / interface)
- ✅ Task entry (deliverable / acceptance / notes)
- ✅ Impl status line (DONE / DWC + any concerns)
- ✅ Git diff (actual code changes, not just files-changed list)
- ⚪ Wiki context (optional, flag if skipped)

Missing any of the first 4 → BLOCK review, tell user what's missing.

---

## Judge

The heart of the skill. Compare diff against spec, carefully.

> **Extended thinking strongly recommended**. This is the one primitive across the whole sdd-kit where heavy reasoning pays for itself.

### Full procedure

**Step 1 — Goal coverage check**

> Does the diff actually address the spec's one-sentence goal?

- Read spec's `## Goal`
- Point to specific diff hunks that deliver it
- If you can't point, that's a gap

Example:

```
Spec goal: "小红书 webhook 收到消息后入队列，500ms 内响应 200"
Diff evidence: src/webhooks/xhs-handler.ts:20-40 — handler reads req, pushes to queue, returns 200.
Verdict on goal: ✓ addressed
```

**Step 2 — Non-goals check**

> Does the diff stay within the spec's explicit non-goals?

- Read spec's `## Non-goals`
- Scan diff for scope creep: files/features not implied by the task

Example:

```
Non-goal: "不做消息内容的 NLP 解析，只入队"
Diff evidence: no NLP-related imports, no content parsing code.
Verdict on non-goals: ✓ respected
```

A non-goal violation is typically a SPEC_DRIFT or scope-creep NEEDS_REWORK.

**Step 3 — Hard constraints check**

> Do the hard constraints in spec have corresponding evidence in the diff?

This is where reviews fail most often. Hard constraints are typically:

- **Performance SLOs** (p99 < 200ms, throughput ≥ X/s)
- **Rate limits** (10/s per client)
- **Security invariants** (signature verification, HMAC, auth)
- **Idempotency guarantees**
- **Retry / backoff rules**
- **Clock / timestamp window tolerances**

For each constraint, ask:

1. Is there code in the diff that implements it? (point to file:line)
2. Is there a test that would catch its violation? (point to test file)
3. If no: NEEDS_REWORK

Constraint-specific sub-checks:

| Constraint type | Sub-check |
|-----------------|-----------|
| SLO (latency) | Is there an allocation-free fast path? A benchmark test? |
| Rate limit | Is there middleware / token-bucket? Applied BEFORE handler? |
| HMAC / signature | Is verification done on the raw body bytes, not parsed? |
| Idempotency | Is there a dedup key? A TTL? A storage layer? |
| Retry | Explicit policy (fixed / backoff)? Max attempts? |

**Step 4 — Interface contract check**

> Does the code export exactly what the spec's interface section requires?

- Spec: `export function handleXhsWebhook(req: Request): Promise<Response>`
- Diff: search for matching signature

If diff has extra/missing exports vs spec's interface: either a gap (NEEDS_REWORK) or a scope creep (APPROVED_WITH_NOTES).

**Step 5 — Wiki gotcha cross-check**

For each `[[gotcha-*]]` page whose domain overlaps the diff:

- Read the page's Trigger and Fix sections
- Check if the diff addresses the gotcha (if applicable)

Example:

```
Wiki: [[xhs-signature-clock-skew]] says "validate ts within 300s window"
Diff: src/webhooks/xhs-verify.ts:15 uses 600s window
Verdict: APPROVED_WITH_NOTES — diff tolerates 2x the documented window; may accept replay attacks slightly longer
```

**Step 6 — Diff hygiene check**

Even if semantic layer is fine, look for mechanical issues:

- Untested new code paths (function added without tests touching it)
- Error paths not handled (try without catch, promise without .catch)
- Magic numbers without comment
- Files touched but not listed in task's `deliverable:` (scope creep)
- Dead imports / commented-out code
- TODOs introduced in this change (vs pre-existing)

These usually lead to APPROVED_WITH_NOTES, not NEEDS_REWORK — unless the hole is in a critical path.

**Step 7 — Classify**

Combine findings into one state per [state-machine.md](state-machine.md):

| Findings | State |
|----------|-------|
| All checks pass, no concerns | APPROVED |
| All checks pass, ≥1 minor concern | APPROVED_WITH_NOTES |
| Any hard-constraint gap OR goal not met OR untested required path | NEEDS_REWORK |
| Spec contradicts itself / is impossible / diverges from codebase reality | SPEC_DRIFT |

### Heavy-thinking prompts (when extended thinking is enabled)

Questions to deliberately ask, in roughly this order:

1. **"What is the quietest way this impl could be wrong?"** — forces thinking beyond the passing tests.
2. **"If this ships to production, what is the first bug report that would surprise me?"** — surfaces edge cases.
3. **"Which spec constraint is load-bearing but invisible in the diff?"** — catches under-specified impl.
4. **"Is there a wiki gotcha that the author might not have known about?"** — couples review with institutional memory.

---

## Report

Classify, log, summarize.

### Full procedure

**Step 1 — Classify**

Apply [state-machine.md](state-machine.md) rules to pick exactly one of APPROVED / APPROVED_WITH_NOTES / NEEDS_REWORK / SPEC_DRIFT.

**Step 2 — Append to task file's `## Review log`**

Locate or create the `## Review log` section (always below `## Status log`).

Append one line per review:

```
- [✓] T-003 (APPROVED) — 2025-04-18 16:40 — <terse summary>
```

Full examples:

```
- [✓] T-003 (APPROVED) — 2025-04-18 16:40 — spec goal met; non-goals respected; rate-limit verified (middleware at src/mw/rate-limit.ts:12); HMAC on raw body; diff clean
- [~] T-004 (APPROVED_WITH_NOTES) — 2025-04-18 16:55 — core correct; timeout hard-coded to 5s (spec said "configurable") src/webhooks/xhs-handler.ts:34; suggest follow-up task
- [✗] T-005 (NEEDS_REWORK) — 2025-04-18 17:10 — spec §3 requires rate-limit 10/s per client; diff has no rate-limit middleware; acceptance cmd did not exercise burst scenario
- [!] T-006 (SPEC_DRIFT) — 2025-04-18 17:30 — spec §4 says "use redis for idempotency"; no redis dependency in package.json, codebase uses in-memory Map; spec predates current arch
```

**Step 3 — Emit structured summary**

To the user, in this exact shape:

```
## 🔎 Review: T-00X

**State**: <STATE>
**Audited against**: spec `.claude/specs/<name>.md`, diff <base>..HEAD
**Wiki context**: [[gotcha-X]], [[decision-Y]] (or "skipped — no relevant pages")

### Evidence
- Goal:       <verdict + file:line>
- Non-goals:  <verdict>
- Constraints:
  - <constraint>: <verdict + file:line>
  - ...
- Interface:  <verdict>
- Wiki cross-check: <findings or N/A>
- Diff hygiene: <findings or ✓>

### Findings
1. <most important first>
2. ...

### Recommended next step
<one sentence pointing user to impl or spec>
```

**Step 4 — Next-step pointer per state**

| State | Next-step message |
|-------|-------------------|
| APPROVED | "可以合并/发布。若需沉淀经验，运行 `/sdd-kit:wiki` 把 gotcha 或 decision ingest。" |
| APPROVED_WITH_NOTES | "可合并，但建议创建 follow-up task (见 findings)。" |
| NEEDS_REWORK | "回到 `/sdd-kit:impl T-00X`，对照 findings 补齐。不需要重跑 spec。" |
| SPEC_DRIFT | "回到 `/sdd-kit:spec <name>` 调整 spec。impl 不应在错误前提下反复跑。" |

**Step 5 — Do NOT auto-advance**

Review reports once and stops. Even for APPROVED, do not automatically offer to "move to next task" — that's user's decision.

### Edge cases

**Case: impl has multiple status lines (re-runs)**

Review audits the latest DONE / DONE_WITH_CONCERNS line. Earlier NEEDS_CONTEXT / BLOCKED lines are part of the audit trail but not the audit target.

**Case: user requests review of a task still in NEEDS_CONTEXT or BLOCKED**

Refuse:

```
T-00X 当前状态是 <STATE>，尚未 DONE。先完成 impl 再 review。
```

**Case: user requests re-review after NEEDS_REWORK → DONE cycle**

Run a fresh review. Append a new review line. Do NOT edit the prior NEEDS_REWORK line (preserve audit trail).

**Case: task is ad-hoc (no spec)**

Lightweight mode:

- Use user-stated goal as spec proxy (ask for it explicitly if not obvious)
- Skip constraint/interface checks (nothing to check against)
- Focus on diff hygiene + wiki cross-check
- Flag in review line: `note: ad-hoc, lightweight review`

**Case: diff is huge (>500 LOC across 10+ files)**

Do not silently skim. Either:

- Ask user which subsystem to focus on, OR
- Report NEEDS_REWORK with finding: "task scope appears oversized; consider re-decomposition"

**Case: spec is empty or just a stub**

SPEC_DRIFT immediately:

```
spec 缺少可审计的 goal / non-goals / constraints。无法对 impl 做语义审计。
建议回到 /sdd-kit:spec 补齐 spec 内容契约 (content-contract)。
```

---

## Multi-task / batch review

If user says "review the whole task file":

- Review each DONE/DWC task in order
- Emit one review line per task
- Final summary: "Reviewed N tasks: K APPROVED, L APPROVED_WITH_NOTES, M NEEDS_REWORK, P SPEC_DRIFT"
- Stop on first SPEC_DRIFT (bouncing back to spec invalidates downstream reviews)

---

## Fresh-context recommendation

**Best practice**: invoke `/sdd-kit:review` in a fresh chat / subagent, not the same session that ran impl. Rationale:

- The context that wrote the code has anchored on "this is the right answer"
- Fresh context forces re-reading spec and diff with uncontaminated eyes
- Mimics how human code review works (different reviewer, different assumptions)

If same-session review is unavoidable, flag it in the review line:

```
note: same-session review (self-audit); consider second opinion
```

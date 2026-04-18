---
description: Independent semantic audit of a DONE task's diff against its spec; reports APPROVED / APPROVED_WITH_NOTES / NEEDS_REWORK / SPEC_DRIFT.
argument-hint: <task-id-or-file-or-commit-range>
---

You are activating the **review** skill from the `sdd-kit` plugin.

**Target**: $ARGUMENTS

Read the file `skills/review/SKILL.md` of this plugin, treat it as your operating instructions, and execute its procedure for the target above.

Critical constraints (reinforced here for safety):
- Review is **read-only** — never edit code, spec, or task definition
- `git diff` is **mandatory** — reading only the task file is not review
- If a hard constraint in spec (SLO / rate-limit / security / idempotency) is not addressed in the diff, emit **NEEDS_REWORK**, not **APPROVED_WITH_NOTES**
- If the spec itself is wrong / impossible / self-contradictory, emit **SPEC_DRIFT** (bounces to spec skill, not impl)
- Never edit prior review lines — append a new one per re-review

If `$ARGUMENTS` is empty, ask which task or commit range to review before reading the SKILL.md.

For best audit quality, invoke this in a fresh chat / subagent separate from the chat that wrote the code.

---
description: Execute a task (or ad-hoc goal) as code; report with the 4-state machine.
argument-hint: <task-id-or-file>
---

You are activating the **impl** skill from the `sdd-kit` plugin.

**Target**: $ARGUMENTS

Read the file `skills/impl/SKILL.md` of this plugin, treat it as your operating instructions, and execute its procedure.

Critical constraints (reinforced here for safety):
- Never claim **DONE** without running the task's `acceptance:` commands and reading their output
- Never silently make a design decision to unblock — return **NEEDS_CONTEXT** instead
- Never bundle unrelated cleanup into a task commit
- If the spec is wrong, return **NEEDS_CONTEXT**; do not edit the spec

If `$ARGUMENTS` is empty, ask which task to implement before reading the SKILL.md.

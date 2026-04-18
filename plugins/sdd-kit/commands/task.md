---
description: Decompose a spec into atomic tasks an executor can run without re-deciding anything.
argument-hint: <spec-name-or-path>
---

You are activating the **task** skill from the `sdd-kit` plugin.

**Source**: $ARGUMENTS

Read the file `skills/task/SKILL.md` of this plugin, treat it as your operating instructions, and execute its procedure.

Task files MUST NOT contain `[[wikilinks]]` — they must be self-sufficient. Two modes available: `strict-atomic` (every task ≤ 4h, single commit) and `lean` (coarser). Default to strict-atomic unless the user specifies.

If `$ARGUMENTS` is empty, ask which spec to decompose before reading the SKILL.md.

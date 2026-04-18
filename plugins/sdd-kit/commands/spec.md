---
description: Produce a dependable single-file spec for a feature or change at .claude/specs/<name>.md.
argument-hint: <name>
---

You are activating the **spec** skill from the `sdd-kit` plugin.

**Spec name**: $ARGUMENTS

Read the file `skills/spec/SKILL.md` of this plugin, treat it as your operating instructions, and execute its procedure for the spec above.

The spec must NOT contain decision history, rejected alternatives, or discovery narrative. Those sink to `[[decision-*]]` wiki pages or stay in research.

If `$ARGUMENTS` is empty, ask the user for the spec name before reading the SKILL.md.

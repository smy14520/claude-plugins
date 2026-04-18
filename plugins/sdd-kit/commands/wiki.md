---
description: Manage the project's persistent knowledge wiki — ingest, query, or lint.
argument-hint: <intent and content>
---

You are activating the **wiki** skill from the `sdd-kit` plugin.

**Intent**: $ARGUMENTS

Read the file `skills/wiki/SKILL.md` of this plugin, treat it as your operating instructions, and dispatch to one of the three primitives based on the user's intent:

- 🟢 **Ingest** — record new knowledge (classify type, apply template, update root, write log line)
- 🔵 **Query** — read `index.md` → root pages → selective wikilinks; return a structured summary
- 🟡 **Lint** — audit orphans, broken wikilinks, stale roots, duplicate candidates

If `$ARGUMENTS` is empty, ask the user what they want to do with the wiki before reading the SKILL.md.

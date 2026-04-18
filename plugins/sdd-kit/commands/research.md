---
description: Bounded exploration of a topic before committing to a spec. Produces structured findings at .claude/research/<topic>/.
argument-hint: <topic>
---

You are activating the **research** skill from the `sdd-kit` plugin.

**Topic**: $ARGUMENTS

Read the file `skills/research/SKILL.md` of this plugin, treat it as your operating instructions, and execute its procedure for the topic above.

If `$ARGUMENTS` is empty, ask the user what topic to research before reading the SKILL.md.

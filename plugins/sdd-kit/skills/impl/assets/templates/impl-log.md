# Impl session log: <name>

Append-only. One entry per task run (per status transition).

<!--
  Optional file. Create only when:
  - Running multiple tasks in one session (audit trail useful)
  - User explicitly wants a cumulative trace
  - Working across sessions and want context carry-over

  For single-task runs, the task file's ## Status log is sufficient.
-->

## [YYYY-MM-DD HH:MM] T-001 DONE

- Deliverable: <file(s) changed>
- SelfCheck:
  - cmd1 — exit 0 (N tests)
  - cmd2 — match expected
- Duration: Xh Ymin
- Notes: <optional>

## [YYYY-MM-DD HH:MM] T-003 NEEDS_CONTEXT

- Blocked at: <ambiguity summary>
- Context asked: <specific question>
- Code state: <no changes / partial X>
- Duration: Xh Ymin

## [YYYY-MM-DD HH:MM] T-003 DONE

- (Re-run after user clarified <thing>)
- Deliverable: <files>
- SelfCheck:
  - cmd1 — exit 0
- Duration: Xh Ymin
- Note: concerns from NEEDS_CONTEXT resolved

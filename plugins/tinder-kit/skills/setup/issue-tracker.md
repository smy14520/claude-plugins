# Issue tracker: Local Markdown

Issues and specs (you may know a spec as a PRD) for this repo live as markdown files in `.forge/`.

## Conventions

- One feature per directory: `.forge/<feature-slug>/`
- The spec is `.forge/<feature-slug>/spec.md`
- Implementation issues are one file per ticket at `.forge/<feature-slug>/issues/<NN>-<slug>.md` (or `.forge/<feature-slug>/tickets/<NN>-<slug>.md` when `map.md` is present in the same directory so implementation tickets stay separate from wayfinding decision tickets in `issues/`), numbered from `01` — never a single combined tickets file
- Triage state is recorded as a `Status:` line near the top of each issue file (see `triage-labels.md` for the role strings)
- Comments and conversation history append to the bottom of the file under a `## Comments` heading

## When a skill says "publish to the issue tracker"

Create a new file under `.forge/<feature-slug>/` (creating the directory if needed).

## When a skill says "fetch the relevant ticket"

Read the file at the referenced path. The user will normally pass the path or the issue number directly.

## When a skill says "resolve a ticket"

Set its `Status:` line to `resolved`. A ticket is unblocked when every ticket in its `Blocked by` is `resolved`.

## Wayfinding operations

Used by `/wayfinder`. The **map** is a file with one **child** file per ticket.

- **Map**: `.forge/<effort>/map.md` — the Notes / Decisions-so-far / Fog body.
- **Child ticket**: `.forge/<effort>/issues/NN-<slug>.md`, numbered from `01`, with the question in the body. A `Type:` line records the ticket type (`research`/`prototype`/`grilling`/`task`); a `Status:` line records `open`/`claimed`/`resolved`/`ruled_out`.
- **Blocking**: a `Blocked by: NN, NN` line near the top. A ticket is unblocked when every file it lists is `resolved`.
- **Frontier**: scan `.forge/<effort>/issues/` for files that are open, unblocked, and unclaimed; first by number wins.
- **Claim**: set `Status: claimed` and save before starting work.
- **Resolve**: record the decision under `## Answer`, set `Status: resolved` (or `ruled_out` if out of scope), and append a context pointer (gist + link) to `Decisions so far` (or `Out of scope`) in `map.md`.

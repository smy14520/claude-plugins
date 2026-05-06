from __future__ import annotations

from pathlib import Path

_ASSET_PRD_TEMPLATE = (
    Path(__file__).resolve().parents[2]
    / "skills"
    / "brainstorm"
    / "assets"
    / "templates"
    / "prd.md"
)


def prd_template(name: str, title: str, timestamp: str) -> str:
    """Render the canonical brainstorm PRD draft for a new package.

    The asset at ``skills/brainstorm/assets/templates/prd.md`` is the single
    source of truth so brainstorm prompts and ``sdd-arbor create`` never drift.
    This helper only substitutes ``name`` / ``title`` / ``date`` placeholders.
    """
    content = _ASSET_PRD_TEMPLATE.read_text(encoding="utf-8")
    date = timestamp[:10]
    # Heading first — `# MM-DD-<topic-slug>` appears once on its own line and must become the title.
    content = content.replace("# MM-DD-<topic-slug>", f"# {title}", 1)
    # Remaining occurrences (frontmatter `name` + `package` path) all map to the package name.
    content = content.replace("MM-DD-<topic-slug>", name)
    # Frontmatter `date`.
    content = content.replace("YYYY-MM-DD", date)
    return content


def review_template(name: str, timestamp: str) -> str:
    date = timestamp[:10]
    return f"""---
package: {name}
updated: {date}
---

# Review log: {name}

Append-only semantic audit entries for package-level PRD scope.
Current lifecycle state lives in `task.json`.
"""

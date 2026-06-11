"""Structural assertions for skill prompt files.

Prompt contract tests assert structure (frontmatter, resolvable references,
mechanism-coupled headings, real CLI commands) — never prose. Pinning prose
strings punishes prompt iteration; structure is what code actually depends on.
"""
from __future__ import annotations

import re
from pathlib import Path

FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---(\r?\n|\Z)", re.DOTALL)
HEADING_RE = re.compile(r"^#{1,6}\s+(.+?)\s*$", re.MULTILINE)
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+?)(?:#[^)]*)?\)")
BACKTICK_PATH_RE = re.compile(r"`((?:\.\./)*(?:references|assets)/[A-Za-z0-9_./\-]+\.md)`")
SDD_ARBOR_COMMAND_RE = re.compile(r"sdd-arbor\s+([a-z][a-z-]+)")


def frontmatter_fields(text: str) -> dict[str, str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}
    fields: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" in line and not line.lstrip().startswith("#"):
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip()
    return fields


def headings(text: str) -> list[str]:
    return HEADING_RE.findall(text)


def referenced_relative_paths(text: str) -> set[str]:
    paths: set[str] = set()
    for pattern in (MARKDOWN_LINK_RE, BACKTICK_PATH_RE):
        for raw in pattern.findall(text):
            if raw.startswith(("http://", "https://", "/")):
                continue
            if raw.endswith(".md"):
                paths.add(raw)
    return paths


def mentioned_arbor_commands(text: str) -> set[str]:
    return set(SDD_ARBOR_COMMAND_RE.findall(text))


def assert_skill_structure(testcase, skill_dir: Path, public_commands: tuple[str, ...] | None = None) -> str:
    """Assert SKILL.md structural contract; returns the SKILL text for further checks."""
    skill_md = skill_dir / "SKILL.md"
    testcase.assertTrue(skill_md.exists(), f"missing {skill_md}")
    text = skill_md.read_text(encoding="utf-8")
    fields = frontmatter_fields(text)
    testcase.assertTrue(fields.get("name"), f"{skill_md} frontmatter missing name")
    testcase.assertTrue(fields.get("description"), f"{skill_md} frontmatter missing description")
    for rel in sorted(referenced_relative_paths(text)):
        target = (skill_dir / rel).resolve()
        testcase.assertTrue(target.exists(), f"{skill_md} references missing file: {rel}")
    if public_commands is not None:
        allowed = set(public_commands)
        for command in sorted(mentioned_arbor_commands(text)):
            testcase.assertIn(command, allowed, f"{skill_md} mentions unknown sdd-arbor command: {command}")
    return text

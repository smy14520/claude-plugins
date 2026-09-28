"""Argument parsing and command dispatch — a thin shell over the Vault index.

Exit codes: 0 success (including "no search results"), 1 when the doctor
finds problems, 2 for usage errors (unknown vault, unknown or ambiguous page
name).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import output
from .index import load_vault
from .linkgraph import Vault
from .model import AMBIGUOUS, OK


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wiki-cli",
        description="Personal local Markdown wiki toolkit (read-only).",
    )
    parser.add_argument("--vault", default=".", help="vault root directory (default: .)")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    sub = parser.add_subparsers(dest="command", required=True)

    def add(name: str, help_text: str) -> argparse.ArgumentParser:
        # Subparser copies of the global flags only set when explicitly given,
        # so `wiki-cli links x --vault y` works as well as the prefixed form.
        p = sub.add_parser(name, help=help_text)
        p.add_argument("--vault", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
        p.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
        return p

    p_links = add("links", "list the outgoing wiki links of a page")
    p_links.add_argument("page")
    p_back = add("backlinks", "list the pages linking to a page")
    p_back.add_argument("page")
    p_tags = add("tags", "aggregate tags across the vault, or list pages for one tag")
    p_tags.add_argument("tag", nargs="?", help="a tag name; children tags are included")
    p_search = add("search", "keyword full-text search over titles and bodies")
    p_search.add_argument("keywords", nargs="+")
    add("doctor", "health check: dead links, ambiguous links, orphan pages")
    return parser


def _emit(args: argparse.Namespace, text: str, payload: dict) -> None:
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(text)


def _unresolved(name: str, status: str, candidates: tuple) -> None:
    if status == AMBIGUOUS:
        names = ", ".join(c.path.as_posix() for c in candidates)
        print(f"wiki-cli: '{name}' is ambiguous: {names}", file=sys.stderr)
    else:
        print(f"wiki-cli: no page named '{name}' in vault", file=sys.stderr)


def _resolve_page_arg(vault: Vault, name: str):
    """Resolve a page name from the command line; return (page, error_code)."""
    status, page, candidates = vault.resolve(name)
    if status == OK:
        return page, None
    _unresolved(name, status, candidates)
    return None, 2


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.vault).expanduser()
    if not root.is_dir():
        print(f"wiki-cli: vault directory not found: {root}", file=sys.stderr)
        return 2
    vault = load_vault(root)

    if args.command == "links":
        page, error = _resolve_page_arg(vault, args.page)
        if error:
            return error
        links = vault.resolved_links_of(page)
        _emit(args, output.format_links(page, links), output.links_payload(page, links))
        return 0

    if args.command == "backlinks":
        page, error = _resolve_page_arg(vault, args.page)
        if error:
            return error
        backlinks = vault.backlinks_of(page)
        _emit(
            args,
            output.format_backlinks(page, backlinks),
            output.backlinks_payload(page, backlinks),
        )
        return 0

    if args.command == "tags":
        if args.tag:
            tag = args.tag.lstrip("#")
            needle = tag.casefold()
            entries = [
                e for e in vault.tag_index()
                if e.key == needle or e.key.startswith(needle + "/")
            ]
            _emit(args, output.format_tag_pages(tag, entries), output.tag_pages_payload(tag, entries))
        else:
            entries = vault.tag_index()
            _emit(args, output.format_tags(entries), output.tags_payload(entries))
        return 0

    if args.command == "search":
        results = vault.search(args.keywords)
        _emit(args, output.format_search(args.keywords, results), output.search_payload(args.keywords, results))
        return 0

    if args.command == "doctor":
        report = vault.doctor()
        _emit(args, output.format_doctor(report), output.doctor_payload(report))
        return 1 if report.has_findings else 0

    build_parser().error(f"unknown command {args.command!r}")  # unreachable

#!/usr/bin/env python3
"""release-watch: list the most recent official releases of a GitHub repository.

Stdlib only (Python >= 3.8). Official releases are those that are neither
drafts nor prereleases; they are listed by published date, newest first.

Usage:
    python3 release_watch.py [-h] [-n N] OWNER/REPO

Set GITHUB_TOKEN to raise the API rate limit (60 -> 5000 requests/hour);
it is read silently and never printed.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

GITHUB_API = "https://api.github.com"
PAGE_SIZE = 100
USER_AGENT = "release-watch"
TIMEOUT_SECONDS = 30


class ReleaseWatchError(Exception):
    """A predictable failure (repo missing, rate limited, network down)."""


class RepositoryNotFound(ReleaseWatchError):
    """The API returned 404; make_fetch_page enriches this with OWNER/REPO context."""


def parse_iso8601(text: str) -> datetime:
    """Parse an ISO 8601 timestamp (e.g. 2025-06-01T00:00:00Z) as an aware datetime."""
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    return datetime.fromisoformat(text)


def is_official(release: dict[str, Any]) -> bool:
    """True when a GitHub release is neither a draft nor a prerelease."""
    return not release.get("draft") and not release.get("prerelease")


def age_in_days(published: datetime, now: datetime) -> int:
    """Whole days between `published` and `now`; releases dated in the future count as 0."""
    return max(0, (now - published).days)


def format_table(rows: list[tuple[str, str, int]]) -> str:
    """Render (tag, published_date, days) rows as aligned columns under a header."""
    cells = [["TAG", "PUBLISHED", "DAYS_AGO"]] + [[t, d, str(n)] for t, d, n in rows]
    widths = [max(len(row[i]) for row in cells) for i in range(3)]
    lines = []
    for row in cells:
        padded = [cell.ljust(width) for cell, width in zip(row, widths)]
        lines.append("  ".join(padded).rstrip())
    return "\n".join(lines)


def collect_official(
    fetch_page: Callable[[int], list[dict[str, Any]]], limit: int
) -> list[dict[str, Any]]:
    """Collect up to `limit` official releases, newest published first.

    `fetch_page(page_number)` returns the API's release list for that page
    (empty list past the end). More pages are fetched only while the official
    count is still short of `limit`.
    """
    official: list[dict[str, Any]] = []
    page = 1
    while len(official) < limit:
        batch = fetch_page(page)
        if not batch:
            break
        official.extend(r for r in batch if is_official(r))
        page += 1
    official.sort(key=lambda r: parse_iso8601(r["published_at"]), reverse=True)
    return official[:limit]


def build_request(url: str, token: str | None = None) -> Request:
    """Build the API request; attaches the Authorization header only when a token is given."""
    headers = {"Accept": "application/vnd.github+json", "User-Agent": USER_AGENT}
    if token:
        headers["Authorization"] = "Bearer " + token
    return Request(url, headers=headers)


def fetch_json(url: str, token: str | None = None) -> list[dict[str, Any]]:
    """GET `url` and decode the JSON body, mapping HTTP/transport errors to ReleaseWatchError."""
    try:
        with urlopen(build_request(url, token), timeout=TIMEOUT_SECONDS) as response:
            body = response.read().decode("utf-8")
    except HTTPError as exc:
        if exc.code == 404:
            raise RepositoryNotFound("repository not found (check OWNER/REPO)")
        if exc.code == 403:
            raise ReleaseWatchError(
                "GitHub API rate limit exceeded; set GITHUB_TOKEN to raise the limit"
            )
        raise ReleaseWatchError("GitHub API error: HTTP {}".format(exc.code))
    except URLError as exc:
        raise ReleaseWatchError("network failure: {}".format(exc.reason))

    try:
        releases = json.loads(body)
    except ValueError:
        raise ReleaseWatchError("unexpected response from the GitHub API") from None
    if not isinstance(releases, list):
        raise ReleaseWatchError("unexpected response from the GitHub API")
    return releases


def make_fetch_page(
    owner: str, repo: str, token: str | None = None
) -> Callable[[int], list[dict[str, Any]]]:
    """Return fetch_page(page) backed by the GitHub releases endpoint."""

    def fetch_page(page: int) -> list[dict[str, Any]]:
        url = "{0}/repos/{1}/{2}/releases?per_page={3}&page={4}".format(
            GITHUB_API, owner, repo, PAGE_SIZE, page
        )
        try:
            return fetch_json(url, token)
        except RepositoryNotFound:
            raise ReleaseWatchError(
                "repository '{0}/{1}' not found".format(owner, repo)
            ) from None

    return fetch_page


def main(
    argv: list[str] | None = None,
    make_fetch_page: Callable[
        [str, str, str | None], Callable[[int], list[dict[str, Any]]]
    ] = make_fetch_page,
    now: datetime | None = None,
) -> int:
    """CLI entry point. Returns the process exit code."""
    parser = argparse.ArgumentParser(
        prog="release-watch",
        description="List the most recent official releases of a GitHub repository.",
    )
    parser.add_argument("repository", metavar="OWNER/REPO", help="e.g. psf/requests")
    parser.add_argument(
        "-n", "--number", type=int, default=5, metavar="N",
        help="number of releases to list (default: 5)",
    )
    args = parser.parse_args(argv)

    owner, sep, repo = args.repository.partition("/")
    if not sep or not owner or not repo:
        parser.error("expected OWNER/REPO, got {0!r}".format(args.repository))

    token = os.environ.get("GITHUB_TOKEN") or None
    try:
        fetch_page = make_fetch_page(owner, repo, token)
        releases = collect_official(fetch_page, args.number)
    except ReleaseWatchError as exc:
        print("error: {0}".format(exc), file=sys.stderr)
        return 1
    if not releases:
        print(
            "error: no official releases found for '{0}/{1}'".format(owner, repo),
            file=sys.stderr,
        )
        return 1

    current = now if now is not None else datetime.now(timezone.utc)
    rows = []
    for release in releases:
        published = parse_iso8601(release["published_at"]).astimezone(timezone.utc)
        rows.append((
            release["tag_name"],
            published.strftime("%Y-%m-%d"),
            age_in_days(published, current),
        ))
    print(format_table(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())

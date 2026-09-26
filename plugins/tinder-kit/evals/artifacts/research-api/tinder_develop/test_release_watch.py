"""Offline tests for release_watch.

All network access is faked at the pre-agreed fetch_page seam; nothing here
touches the real GitHub API.
"""

import contextlib
import io
import os
import unittest
import urllib.error
from datetime import datetime, timezone
from unittest import mock

import release_watch as rw


def rel(tag, published, draft=False, prerelease=False):
    """Build a GitHub-API-shaped release dict."""
    return {
        "tag_name": tag,
        "published_at": published,
        "draft": draft,
        "prerelease": prerelease,
    }


class FakePager:
    """Test double for the fetch_page(page) seam; records requested pages."""

    def __init__(self, pages):
        self.pages = pages
        self.requested = []

    def __call__(self, page):
        self.requested.append(page)
        return self.pages[page - 1] if page <= len(self.pages) else []


class CollectOfficialTests(unittest.TestCase):
    def test_keeps_only_official_releases(self):
        pager = FakePager([[
            rel("v1.0.0", "2025-06-01T00:00:00Z"),
            rel("v2.0.0-rc1", "2026-01-01T00:00:00Z", prerelease=True),
            rel("wip", "2026-02-01T00:00:00Z", draft=True),
            rel("v0.9.0", "2024-01-15T00:00:00Z"),
        ]])
        result = rw.collect_official(pager, limit=10)
        self.assertEqual([r["tag_name"] for r in result], ["v1.0.0", "v0.9.0"])

    def test_fetches_more_pages_until_limit_reached(self):
        pager = FakePager([
            [rel("v1.0.0", "2025-06-01T00:00:00Z"),
             rel("v2.0.0-rc1", "2026-03-01T00:00:00Z", prerelease=True)],
            [rel("v0.9.0", "2024-01-15T00:00:00Z"),
             rel("v0.8.0", "2023-05-01T00:00:00Z")],
        ])
        result = rw.collect_official(pager, limit=3)
        self.assertEqual(
            [r["tag_name"] for r in result],
            ["v1.0.0", "v0.9.0", "v0.8.0"],
        )
        self.assertEqual(pager.requested, [1, 2])

    def test_stops_fetching_once_limit_reached(self):
        pager = FakePager([[
            rel("v3.0.0", "2026-05-01T00:00:00Z"),
            rel("v2.0.0", "2025-05-01T00:00:00Z"),
            rel("v1.0.0", "2024-05-01T00:00:00Z"),
        ]])
        result = rw.collect_official(pager, limit=2)
        self.assertEqual([r["tag_name"] for r in result], ["v3.0.0", "v2.0.0"])
        self.assertEqual(pager.requested, [1])

    def test_returns_all_official_when_repo_exhausted(self):
        pager = FakePager([
            [rel("v1.0.0", "2025-06-01T00:00:00Z")],
            [],
        ])
        result = rw.collect_official(pager, limit=5)
        self.assertEqual([r["tag_name"] for r in result], ["v1.0.0"])
        self.assertEqual(pager.requested, [1, 2])

    def test_sorts_by_published_at_descending(self):
        pager = FakePager([
            [rel("v1.0.0", "2025-06-01T00:00:00Z")],
            [rel("v2.0.0", "2026-01-15T00:00:00Z"),
             rel("v0.9.0", "2024-01-15T00:00:00Z")],
        ])
        result = rw.collect_official(pager, limit=3)
        self.assertEqual(
            [r["tag_name"] for r in result],
            ["v2.0.0", "v1.0.0", "v0.9.0"],
        )


class ParseIso8601Tests(unittest.TestCase):
    def test_parses_z_and_offset_forms_to_correct_instant(self):
        self.assertEqual(
            rw.parse_iso8601("2025-06-01T00:00:00Z"),
            datetime(2025, 6, 1, tzinfo=timezone.utc),
        )
        self.assertEqual(
            rw.parse_iso8601("2025-06-01T02:00:00+02:00"),
            datetime(2025, 6, 1, tzinfo=timezone.utc),
        )


class AgeInDaysTests(unittest.TestCase):
    def test_floors_partial_days(self):
        published = datetime(2026, 9, 25, 13, 0, tzinfo=timezone.utc)
        now = datetime(2026, 9, 26, 12, 0, tzinfo=timezone.utc)
        self.assertEqual(rw.age_in_days(published, now), 0)

    def test_counts_a_full_day(self):
        published = datetime(2026, 9, 25, 12, 0, tzinfo=timezone.utc)
        now = datetime(2026, 9, 26, 12, 0, tzinfo=timezone.utc)
        self.assertEqual(rw.age_in_days(published, now), 1)

    def test_clamps_future_release_to_zero(self):
        published = datetime(2026, 9, 27, 0, 0, tzinfo=timezone.utc)
        now = datetime(2026, 9, 26, 12, 0, tzinfo=timezone.utc)
        self.assertEqual(rw.age_in_days(published, now), 0)


class FormatTableTests(unittest.TestCase):
    def test_renders_header_and_aligned_columns(self):
        rows = [("v1.0.0", "2025-06-01", 414), ("v0.9.0", "2024-01-15", 986)]
        expected = (
            # widths [6, 10, 8] come from the data rows; each cell is padded to
            # its column width then followed by a 2-space gap, so the header
            # shows 3 spaces before DAYS_AGO (1 pad + 2 gap).
            "TAG     PUBLISHED   DAYS_AGO\n"
            "v1.0.0  2025-06-01  414\n"
            "v0.9.0  2024-01-15  986"
        )
        self.assertEqual(rw.format_table(rows), expected)


class BuildRequestTests(unittest.TestCase):
    def test_attaches_token_header_when_provided(self):
        request = rw.build_request("https://api.github.com/x", token="t0k3n")
        self.assertEqual(request.get_header("Authorization"), "Bearer t0k3n")

    def test_omits_authorization_without_token(self):
        request = rw.build_request("https://api.github.com/x", token=None)
        self.assertIsNone(request.get_header("Authorization"))


class FetchPageTests(unittest.TestCase):
    """make_fetch_page's error mapping, exercised with a patched urlopen (no network)."""

    def test_builds_releases_url_and_parses_json_response(self):
        seen = {}

        def fake_urlopen(request, timeout):
            seen["url"] = request.full_url
            seen["accept"] = request.get_header("Accept")
            return io.BytesIO(b'[{"tag_name": "v1.0"}]')

        with mock.patch("release_watch.urlopen", fake_urlopen):
            page = rw.make_fetch_page("acme", "widgets")(1)
        self.assertEqual(page, [{"tag_name": "v1.0"}])
        self.assertEqual(
            seen["url"],
            "https://api.github.com/repos/acme/widgets/releases?per_page=100&page=1",
        )
        self.assertEqual(seen["accept"], "application/vnd.github+json")

    def test_maps_404_to_repository_not_found(self):
        def fake_urlopen(request, timeout):
            raise urllib.error.HTTPError(request.full_url, 404, "Not Found", None, None)

        with mock.patch("release_watch.urlopen", fake_urlopen):
            with self.assertRaises(rw.ReleaseWatchError) as ctx:
                rw.make_fetch_page("acme", "ghost")(1)
        self.assertEqual(str(ctx.exception), "repository 'acme/ghost' not found")

    def test_maps_403_to_rate_limit_hint(self):
        def fake_urlopen(request, timeout):
            raise urllib.error.HTTPError(request.full_url, 403, "Forbidden", None, None)

        with mock.patch("release_watch.urlopen", fake_urlopen):
            with self.assertRaises(rw.ReleaseWatchError) as ctx:
                rw.make_fetch_page("acme", "widgets")(1)
        self.assertIn("GITHUB_TOKEN", str(ctx.exception))

    def test_maps_url_errors_to_network_failure(self):
        def fake_urlopen(request, timeout):
            raise urllib.error.URLError("connection refused")

        with mock.patch("release_watch.urlopen", fake_urlopen):
            with self.assertRaises(rw.ReleaseWatchError) as ctx:
                rw.make_fetch_page("acme", "widgets")(1)
        self.assertIn("network failure", str(ctx.exception))

    def test_maps_non_json_body_to_unexpected_response(self):
        with mock.patch(
            "release_watch.urlopen",
            lambda request, timeout: io.BytesIO(b"<html>gateway error</html>"),
        ):
            with self.assertRaises(rw.ReleaseWatchError) as ctx:
                rw.make_fetch_page("acme", "widgets")(1)
        self.assertIn("unexpected response", str(ctx.exception))

    def test_rejects_json_body_that_is_not_an_array(self):
        with mock.patch(
            "release_watch.urlopen",
            lambda request, timeout: io.BytesIO(b'{"message": "not a release list"}'),
        ):
            with self.assertRaises(rw.ReleaseWatchError) as ctx:
                rw.make_fetch_page("acme", "widgets")(1)
        self.assertIn("unexpected response", str(ctx.exception))


class MainTests(unittest.TestCase):
    def test_prints_table_and_exits_zero(self):
        pager = FakePager([[rel("v1.2.3", "2026-09-20T00:00:00Z")]])
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = rw.main(
                ["acme/widgets"],
                make_fetch_page=lambda owner, repo, token: pager,
                now=datetime(2026, 9, 26, 12, 0, tzinfo=timezone.utc),
            )
        self.assertEqual(code, 0)
        self.assertEqual(
            stdout.getvalue(),
            "TAG     PUBLISHED   DAYS_AGO\nv1.2.3  2026-09-20  6\n",
        )

    def test_reports_repo_without_official_releases(self):
        pager = FakePager([[rel("v2.0.0-rc1", "2026-01-01T00:00:00Z", prerelease=True)]])
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            code = rw.main(
                ["acme/empty"],
                make_fetch_page=lambda owner, repo, token: pager,
                now=datetime(2026, 9, 26, 12, 0, tzinfo=timezone.utc),
            )
        self.assertEqual(code, 1)
        self.assertEqual(
            stderr.getvalue(), "error: no official releases found for 'acme/empty'\n"
        )

    def test_reports_fetch_errors_to_stderr_with_exit_one(self):
        def factory(owner, repo, token):
            raise rw.ReleaseWatchError("repository 'acme/ghost' not found")

        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            code = rw.main(["acme/ghost"], make_fetch_page=factory)
        self.assertEqual(code, 1)
        self.assertEqual(
            stderr.getvalue(), "error: repository 'acme/ghost' not found\n"
        )

    def test_passes_github_token_from_environment(self):
        seen = {}
        pager = FakePager([[rel("v1.0.0", "2026-01-01T00:00:00Z")]])

        def factory(owner, repo, token):
            seen["token"] = token
            return pager

        with mock.patch.dict(os.environ, {"GITHUB_TOKEN": "env-token"}):
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                code = rw.main(
                    ["acme/widgets"],
                    make_fetch_page=factory,
                    now=datetime(2026, 9, 26, 12, 0, tzinfo=timezone.utc),
                )
        self.assertEqual(code, 0)
        self.assertEqual(seen["token"], "env-token")

    def test_rejects_malformed_repository_argument(self):
        with self.assertRaises(SystemExit) as ctx:
            rw.main(["not-a-repo"])
        self.assertEqual(ctx.exception.code, 2)


if __name__ == "__main__":
    unittest.main()

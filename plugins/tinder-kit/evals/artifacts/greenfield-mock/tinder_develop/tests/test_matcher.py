"""match_route seam: segment-level routing over the contract's file order."""
import unittest

from mock_server.config import Route
from mock_server.server import match_route


def r(method, path):
    return Route(method=method, path_template=path)


class MatchRouteTest(unittest.TestCase):
    def setUp(self):
        self.routes = [
            r("GET", "/users"),
            r("GET", "/users/{id}"),
            r("POST", "/users"),
            r("GET", "/health"),
        ]

    def test_exact_path_matches_first_route(self):
        result = match_route(self.routes, "GET", "/users")
        self.assertIs(result.matched, self.routes[0])
        self.assertIsNone(result.method_mismatch)

    def test_path_parameter_matches_single_segment(self):
        result = match_route(self.routes, "GET", "/users/42")
        self.assertIs(result.matched, self.routes[1])

    def test_parameter_does_not_span_two_segments(self):
        result = match_route(self.routes, "GET", "/users/42/orders")
        self.assertIsNone(result.matched)
        self.assertIsNone(result.method_mismatch)

    def test_path_match_with_wrong_method_signals_method_mismatch(self):
        result = match_route(self.routes, "DELETE", "/users/42")
        self.assertIsNone(result.matched)
        self.assertIs(result.method_mismatch, self.routes[1])

    def test_query_string_is_ignored(self):
        result = match_route(self.routes, "GET", "/users/42?full=1")
        self.assertIs(result.matched, self.routes[1])

    def test_no_path_match_returns_none_none(self):
        result = match_route(self.routes, "GET", "/nope")
        self.assertIsNone(result.matched)
        self.assertIsNone(result.method_mismatch)

    def test_first_of_identical_templates_wins(self):
        first, second = r("GET", "/dup"), r("GET", "/dup")
        result = match_route([first, second], "GET", "/dup")
        self.assertIs(result.matched, first)

    def test_root_path_matches_root_template(self):
        root = r("GET", "/")
        result = match_route([root], "GET", "/")
        self.assertIs(result.matched, root)


if __name__ == "__main__":
    unittest.main()

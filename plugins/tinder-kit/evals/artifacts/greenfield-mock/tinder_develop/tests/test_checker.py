"""checker seam: check_file() reports every contract violation, never raises."""
import json
import tempfile
import unittest
from pathlib import Path

from mock_server.checker import check_file

VALID = {"routes": [{"method": "GET", "path": "/users/{id}", "body": {"id": 1}}]}


class CheckFileTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    def _check(self, payload) -> list[str]:
        path = self.tmp / "mocks.json"
        if isinstance(payload, str):
            path.write_text(payload, encoding="utf-8")
        else:
            path.write_text(json.dumps(payload), encoding="utf-8")
        return check_file(path)

    def test_valid_contract_has_no_errors(self):
        self.assertEqual(self._check(VALID), [])

    def test_unreadable_file_is_reported_not_raised(self):
        errors = check_file(self.tmp / "absent.json")
        self.assertEqual(len(errors), 1)
        self.assertIn("cannot read", errors[0])

    def test_invalid_json_is_reported(self):
        errors = self._check("{oops")
        self.assertEqual(len(errors), 1)
        self.assertIn("invalid JSON", errors[0])

    def test_top_level_must_be_object(self):
        errors = self._check([1, 2])
        self.assertEqual(len(errors), 1)
        self.assertIn("top level", errors[0])

    def test_routes_must_be_array(self):
        errors = self._check({"routes": "all"})
        self.assertEqual(len(errors), 1)
        self.assertIn('"routes"', errors[0])

    def test_method_is_required_and_standard(self):
        errors = self._check({"routes": [{"path": "/a"}, {"method": "get", "path": "/b"}, {"method": "FETCH", "path": "/c"}]})
        self.assertEqual(len(errors), 3)
        self.assertIn("route[1]", errors[0])
        self.assertIn("route[2]", errors[1])
        self.assertIn("route[3]", errors[2])

    def test_path_required_with_leading_slash(self):
        errors = self._check({"routes": [{"method": "GET"}, {"method": "GET", "path": "users"}]})
        self.assertEqual(len(errors), 2)
        self.assertIn("route[1]", errors[0])
        self.assertIn("route[2]", errors[1])

    def test_illegal_path_parameter_is_reported(self):
        for bad in ("/x/{1bad}", "/x/{a}{b}", "/x/{}"):
            with self.subTest(template=bad):
                errors = self._check({"routes": [{"method": "GET", "path": bad}]})
                self.assertEqual(len(errors), 1)
                self.assertIn("route[1]", errors[0])

    def test_status_must_be_int_in_range(self):
        for bad in (99, 600, "200", True, 20.5):
            with self.subTest(status=bad):
                errors = self._check({"routes": [{"method": "GET", "path": "/x", "status": bad}]})
                self.assertEqual(len(errors), 1)
                self.assertIn("route[1]", errors[0])

    def test_status_omitted_is_fine(self):
        errors = self._check({"routes": [{"method": "GET", "path": "/x"}]})
        self.assertEqual(errors, [])

    def test_duplicate_template_is_reported_on_later_route(self):
        errors = self._check({"routes": [
            {"method": "GET", "path": "/a"},
            {"method": "GET", "path": "/a"},
        ]})
        self.assertEqual(len(errors), 1)
        self.assertIn("route[2]", errors[0])
        self.assertIn("duplicate", errors[0])

    def test_same_path_different_method_is_not_duplicate(self):
        errors = self._check({"routes": [
            {"method": "GET", "path": "/a"},
            {"method": "POST", "path": "/a"},
        ]})
        self.assertEqual(errors, [])

    def test_headers_shape_is_not_one_of_the_five_rules(self):
        errors = self._check({"routes": [{"method": "GET", "path": "/x", "headers": "oops"}]})
        self.assertEqual(errors, [])

    def test_errors_accumulate_across_routes(self):
        errors = self._check({"routes": [
            {"method": "GET", "path": "bad", "status": 999},
            {"method": "GET", "path": "/ok"},
            {"method": "GET", "path": "/ok"},
        ]})
        # route[1] violates two rules; route[3] duplicates route[2].
        self.assertEqual(len(errors), 3)
        self.assertIn("route[1]", errors[0])
        self.assertIn("route[1]", errors[1])
        self.assertIn("route[3]", errors[2])
        self.assertIn("duplicate", errors[2])


if __name__ == "__main__":
    unittest.main()

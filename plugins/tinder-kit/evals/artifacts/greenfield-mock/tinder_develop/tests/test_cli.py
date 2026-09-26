"""cli seam: exit codes and diagnostics for the check and serve commands."""
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from mock_server.cli import main

VALID = {"routes": [{"method": "GET", "path": "/users/{id}", "body": {"id": 1}}]}
INVALID = {"routes": [{"method": "FETCH", "path": "users", "status": 700}]}


class CliTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    def _contract(self, payload) -> str:
        path = self.tmp / "mocks.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return str(path)

    def _run(self, argv) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_check_valid_contract_exits_zero(self):
        code, out, _ = self._run(["check", "-f", self._contract(VALID)])
        self.assertEqual(code, 0)
        self.assertIn("OK", out)

    def test_check_invalid_contract_lists_errors_and_exits_one(self):
        code, _, err = self._run(["check", "-f", self._contract(INVALID)])
        self.assertEqual(code, 1)
        self.assertIn("route[1]", err)

    def test_check_missing_file_exits_one(self):
        code, _, err = self._run(["check", "-f", str(self.tmp / "gone.json")])
        self.assertEqual(code, 1)
        self.assertIn("cannot read", err)

    def test_serve_refuses_invalid_contract_without_starting(self):
        code, out, err = self._run(["serve", "-f", self._contract(INVALID)])
        self.assertEqual(code, 1)
        self.assertIn("route[1]", err)
        self.assertNotIn("serving at", out)

    def test_serve_refuses_missing_file(self):
        code, _, err = self._run(["serve", "-f", str(self.tmp / "gone.json")])
        self.assertEqual(code, 1)
        self.assertIn("cannot read", err)

    def test_serve_reports_config_error_without_traceback(self):
        # headers shape is not one of the five check rules, so this passes
        # check; serve must still fail with a printed error, never a traceback.
        path = self._contract({"routes": [{"method": "GET", "path": "/x", "headers": "oops"}]})
        code, _, err = self._run(["serve", "-f", path])
        self.assertEqual(code, 1)
        self.assertIn("headers", err)
        self.assertNotIn("Traceback", err)

    def test_subcommand_is_required(self):
        with self.assertRaises(SystemExit):
            self._run([])


if __name__ == "__main__":
    unittest.main()

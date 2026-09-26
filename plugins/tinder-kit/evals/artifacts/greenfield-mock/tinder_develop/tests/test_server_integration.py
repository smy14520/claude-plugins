"""HTTP integration seam: real requests against a live ThreadingHTTPServer."""
import contextlib
import http.client
import io
import json
import re
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path

from mock_server.config import load_config
from mock_server.server import make_handler

# External truth: body is returned verbatim — "{id}" is NOT substituted.
CONTRACT = {
    "routes": [
        {"method": "GET", "path": "/users/{id}", "body": {"id": "{id}", "name": "Alice"}},
        {"method": "POST", "path": "/orders", "status": 201,
         "headers": {"X-Request-Id": "abc-123"}, "body": {"created": True}},
        {"method": "GET", "path": "/health", "body": "ok"},
        {"method": "HEAD", "path": "/ping"},
    ]
}


class ServerIntegrationTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        contract = Path(self._tmp.name) / "mocks.json"
        contract.write_text(json.dumps(CONTRACT), encoding="utf-8")
        routes = load_config(contract)
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(routes))
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.log = io.StringIO()

    def _request(self, method, path):
        with contextlib.redirect_stdout(self.log):
            conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
            try:
                conn.request(method, path, headers={"Connection": "close"})
                response = conn.getresponse()
                return response.status, dict(response.getheaders()), response.read()
            finally:
                conn.close()

    def test_json_body_round_trip_is_verbatim(self):
        status, _, body = self._request("GET", "/users/42")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body), {"id": "{id}", "name": "Alice"})

    def test_explicit_status_and_custom_headers(self):
        status, headers, body = self._request("POST", "/orders")
        self.assertEqual(status, 201)
        self.assertEqual(headers.get("X-Request-Id"), "abc-123")
        self.assertEqual(json.loads(body), {"created": True})

    def test_string_body_is_serialized_as_json(self):
        status, headers, body = self._request("GET", "/health")
        self.assertEqual(status, 200)
        self.assertEqual(body, b'"ok"')
        self.assertEqual(headers.get("Content-Type"), "application/json")

    def test_route_headers_can_override_content_type(self):
        contract = {"routes": [{"method": "GET", "path": "/csv",
                                "headers": {"Content-Type": "text/csv"}, "body": "a,b"}]}
        path = Path(self._tmp.name) / "other.json"
        path.write_text(json.dumps(contract), encoding="utf-8")
        server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(load_config(path)))
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        port = server.server_address[1]
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        try:
            conn.request("GET", "/csv", headers={"Connection": "close"})
            response = conn.getresponse()
            self.assertEqual(response.getheader("Content-Type"), "text/csv")
        finally:
            conn.close()

    def test_unmatched_path_returns_404_json(self):
        status, headers, body = self._request("GET", "/nope")
        self.assertEqual(status, 404)
        self.assertIn("error", json.loads(body))

    def test_wrong_method_returns_405_json(self):
        status, _, body = self._request("DELETE", "/users/42")
        self.assertEqual(status, 405)
        self.assertIn("error", json.loads(body))

    def test_head_returns_headers_without_body(self):
        status, headers, body = self._request("HEAD", "/ping")
        self.assertEqual(status, 200)
        self.assertEqual(body, b"")

    def test_request_log_line_format(self):
        self._request("GET", "/users/42")
        matched = self.log.getvalue().strip()
        self.assertRegex(
            matched,
            r"^\d{2}:\d{2}:\d{2} GET /users/42 → 200 \[GET /users/\{id\}\] \d+\.\d+ms$",
        )

    def test_unmatched_request_logged_as_no_match(self):
        self._request("GET", "/nope")
        line = self.log.getvalue().strip()
        self.assertIn("→ 404 no match", line)


if __name__ == "__main__":
    unittest.main()

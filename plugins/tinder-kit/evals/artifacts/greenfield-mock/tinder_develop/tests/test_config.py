"""config seam: load_config() turns mocks.json into Route objects."""
import json
import tempfile
import unittest
from pathlib import Path

from mock_server.config import ConfigError, load_config


class LoadConfigTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    def _write(self, payload) -> Path:
        path = self.tmp / "mocks.json"
        if isinstance(payload, str):
            path.write_text(payload, encoding="utf-8")
        else:
            path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_loads_route_with_contract_defaults(self):
        path = self._write({
            "routes": [
                {"method": "GET", "path": "/users/{id}",
                 "body": {"id": 1, "name": "Alice"}},
            ]
        })
        routes = load_config(path)
        self.assertEqual(len(routes), 1)
        self.assertEqual(routes[0].method, "GET")
        self.assertEqual(routes[0].path_template, "/users/{id}")
        self.assertEqual(routes[0].status, 200)
        self.assertEqual(routes[0].headers, {})
        self.assertEqual(routes[0].body, {"id": 1, "name": "Alice"})

    def test_keeps_explicit_status_and_headers(self):
        path = self._write({
            "routes": [
                {"method": "POST", "path": "/orders", "status": 201,
                 "headers": {"X-Request-Id": "abc"}},
            ]
        })
        (route,) = load_config(path)
        self.assertEqual(route.status, 201)
        self.assertEqual(route.headers, {"X-Request-Id": "abc"})
        self.assertIsNone(route.body)

    def test_empty_object_body_is_preserved_not_none(self):
        path = self._write({"routes": [{"method": "GET", "path": "/x", "body": {}}]})
        (route,) = load_config(path)
        self.assertEqual(route.body, {})

    def test_missing_file_raises_config_error(self):
        with self.assertRaises(ConfigError):
            load_config(self.tmp / "nope.json")

    def test_invalid_json_raises_config_error(self):
        path = self._write("{not json")
        with self.assertRaises(ConfigError):
            load_config(path)

    def test_missing_routes_key_raises_config_error(self):
        path = self._write({"not-routes": []})
        with self.assertRaises(ConfigError):
            load_config(path)

    def test_non_object_route_raises_config_error(self):
        path = self._write({"routes": ["GET /users"]})
        with self.assertRaises(ConfigError):
            load_config(path)

    def test_non_object_headers_raises_config_error(self):
        path = self._write({"routes": [{"method": "GET", "path": "/x", "headers": "oops"}]})
        with self.assertRaises(ConfigError):
            load_config(path)

    def test_non_string_header_value_raises_config_error(self):
        path = self._write({"routes": [{"method": "GET", "path": "/x", "headers": {"X-A": 1}}]})
        with self.assertRaises(ConfigError):
            load_config(path)


if __name__ == "__main__":
    unittest.main()

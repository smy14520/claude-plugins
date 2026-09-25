"""CLI seam 的公共行为：退出码、全量错误报告、参数装配、Banner 与 Ctrl-C。"""

import re

from mock_server import cli
from mock_server.server import MockServer


def _capture_serve(monkeypatch):
    captured = {}

    def _serve(contract, host, port, source):
        captured.update(contract=contract, host=host, port=port, source=source)
        return 0

    monkeypatch.setattr(cli, "serve", _serve)
    return captured


def test_missing_contract_file_exits_2(tmp_path, capsys):
    missing = str(tmp_path / "nope.json")
    code = cli.main(["--file", missing])
    assert code == 2
    assert missing in capsys.readouterr().err


def test_invalid_contract_lists_every_error_and_exits_2(write_contract, capsys):
    path = str(
        write_contract({"routes": [{"method": "FETCH", "path": "bad"}, {"status": 99}]})
    )
    code = cli.main(["--file", path])
    assert code == 2
    err = capsys.readouterr().err
    assert "FETCH" in err
    assert "path" in err
    assert "status" in err


def test_arguments_are_wired_into_serve(write_contract, monkeypatch):
    path = str(write_contract({"routes": [{"path": "/api/user", "body": {"id": 1}}]}))
    captured = _capture_serve(monkeypatch)
    code = cli.main(["--file", path, "--host", "0.0.0.0", "--port", "9001"])
    assert code == 0
    assert captured["host"] == "0.0.0.0"
    assert captured["port"] == 9001
    assert captured["source"] == path
    assert [route.path for route in captured["contract"].routes] == ["/api/user"]


def test_defaults_are_localhost_8000_and_mocks_json(tmp_path, write_contract, monkeypatch):
    write_contract({"routes": [{"path": "/x"}]})
    monkeypatch.chdir(tmp_path)
    captured = _capture_serve(monkeypatch)
    code = cli.main([])
    assert code == 0
    assert captured["host"] == "127.0.0.1"
    assert captured["port"] == 8000
    assert captured["source"] == "mocks.json"


def test_banner_shows_route_count_and_resolved_address(write_contract, capsys, monkeypatch):
    path = str(write_contract({"routes": [{"path": "/api/user", "body": {}}]}))

    def instant_interrupt(self):
        raise KeyboardInterrupt

    monkeypatch.setattr(MockServer, "serve_forever", instant_interrupt)
    code = cli.main(["--file", path, "--port", "0"])
    assert code == 0
    out = capsys.readouterr().out
    assert re.search(
        r"mock-server serving 1 routes from .* at http://127\.0\.0\.1:\d+",
        out,
    )

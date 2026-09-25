"""CLI 测试：子命令分派、serve 的退出码与横幅、check 的校验输出。"""

import json

import pytest

from mock_server import cli
from mock_server.cli import main


class _StubServer:
    """替换真服务：serve_forever 立即以 KeyboardInterrupt 返回，验证主流程与横幅。"""

    def __init__(self, address, contract):
        self.address = address
        self.contract = contract

    def serve_forever(self):
        raise KeyboardInterrupt

    def server_close(self):
        pass


def _write_contract(tmp_path, document):
    path = tmp_path / "mocks.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


def test_bare_invocation_requires_a_subcommand(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main([])
    assert excinfo.value.code == 2
    err = capsys.readouterr().err
    assert "serve" in err
    assert "check" in err


def test_serve_port_out_of_range_exits_1(capsys):
    assert main(["serve", "-p", "70000"]) == 1
    assert "端口" in capsys.readouterr().err


def test_serve_port_zero_is_rejected(capsys):
    assert main(["serve", "-p", "0"]) == 1
    assert "端口" in capsys.readouterr().err


def test_serve_missing_contract_exits_1(capsys, tmp_path):
    assert main(["serve", "-c", str(tmp_path / "nope.json")]) == 1
    assert "找不到契约文件" in capsys.readouterr().err


def test_serve_invalid_json_exits_1(capsys, tmp_path):
    path = tmp_path / "mocks.json"
    path.write_text("{oops", encoding="utf-8")
    assert main(["serve", "-c", str(path)]) == 1
    assert "不是合法 JSON" in capsys.readouterr().err


def test_serve_invalid_contract_exits_1(capsys, tmp_path):
    path = _write_contract(
        tmp_path, {"routes": [{"method": "GET", "path": "/p", "status": 204, "body": {}}]}
    )
    assert main(["serve", "-c", str(path)]) == 1
    assert "不允许携带响应体" in capsys.readouterr().err


def test_serve_banner_reports_routes_then_serves_until_interrupt(capsys, tmp_path, monkeypatch):
    path = _write_contract(
        tmp_path, {"routes": [{"method": "GET", "path": "/api/user", "body": {"id": 1}}]}
    )
    monkeypatch.setattr(cli, "MockServer", _StubServer)
    assert main(["serve", "-c", str(path)]) == 0
    out = capsys.readouterr().out
    assert f"mock-server listening on http://127.0.0.1:8000 (1 routes from {path})" in out


def test_serve_default_port_and_config_are_used(capsys, tmp_path, monkeypatch):
    _write_contract(tmp_path, {"routes": []})
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "MockServer", _StubServer)
    assert main(["serve"]) == 0
    out = capsys.readouterr().out
    assert "http://127.0.0.1:8000 (0 routes from mocks.json)" in out


def test_check_valid_contract_exits_0(capsys, tmp_path):
    path = _write_contract(
        tmp_path, {"routes": [{"method": "GET", "path": "/api/user", "body": {"id": 1}}]}
    )
    assert main(["check", "-c", str(path)]) == 0
    assert f"{path}: 契约有效，共 1 条路由" in capsys.readouterr().out


def test_check_invalid_contract_exits_1(capsys, tmp_path):
    path = _write_contract(
        tmp_path, {"routes": [{"method": "GET", "path": "/p", "status": 204, "body": {}}]}
    )
    assert main(["check", "-c", str(path)]) == 1
    assert "不允许携带响应体" in capsys.readouterr().err


def test_check_missing_contract_exits_1(capsys, tmp_path):
    assert main(["check", "-c", str(tmp_path / "nope.json")]) == 1
    assert "找不到契约文件" in capsys.readouterr().err


def test_unknown_subcommand_exits_2(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(["deploy"])
    assert excinfo.value.code == 2

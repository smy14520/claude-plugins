"""CLI 检查分支与 serve 优雅退出的直测。"""

import _thread
import json
import threading
import time

from mock_server.cli import main


def write_contract(tmp_path, doc) -> str:
    file = tmp_path / "mocks.json"
    file.write_text(json.dumps(doc), encoding="utf-8")
    return str(file)


def test_check_ok_prints_route_table(tmp_path, capsys):
    file = write_contract(
        tmp_path,
        {"routes": [{"method": "GET", "path": "/api/user", "status": 200}]},
    )
    assert main(["check", "--file", file]) == 0
    out = capsys.readouterr().out
    assert f"{'GET':<7} /api/user -> 200" in out
    assert "契约校验通过：1 条路由" in out


def test_check_collects_all_errors(tmp_path, capsys):
    file = write_contract(
        tmp_path,
        {
            "routes": [
                {"method": "get", "path": "api", "status": 200},
                {"method": "GET", "path": "/ok", "status": 200},
            ]
        },
    )
    assert main(["check", "--file", file]) == 1
    err = capsys.readouterr().err
    assert "共 2 处错误" in err
    assert "routes[0].method" in err
    assert "routes[0].path" in err
    assert "routes[1]" not in err


def test_check_missing_file(tmp_path, capsys):
    assert main(["check", "--file", str(tmp_path / "nope.json")]) == 1
    assert "找不到契约文件" in capsys.readouterr().err


def test_check_json_syntax_error(tmp_path, capsys):
    file = tmp_path / "broken.json"
    file.write_text("{oops", encoding="utf-8")
    assert main(["check", "--file", str(file)]) == 1
    assert "JSON 解析失败" in capsys.readouterr().err


def test_serve_graceful_keyboard_interrupt(tmp_path, capsys):
    """Ctrl+C 路径：serve_forever 被真实 KeyboardInterrupt 打断后干净退出 0。"""
    file = tmp_path / "mocks.json"
    file.write_text(
        json.dumps({"routes": [{"method": "GET", "path": "/api/user", "status": 200}]}),
        encoding="utf-8",
    )

    def interrupt_soon():
        time.sleep(0.3)
        _thread.interrupt_main()

    thread = threading.Thread(target=interrupt_soon, daemon=True)
    thread.start()
    rc = main(["serve", "--port", "0", "--file", str(file)])
    thread.join(timeout=2)
    assert rc == 0
    out = capsys.readouterr().out
    assert "mock-server serving 1 routes" in out
    assert "mock-server stopped" in out


def test_serve_fail_fast_on_invalid_contract(tmp_path, capsys):
    file = tmp_path / "bad.json"
    file.write_text(json.dumps({"routes": [{"method": "get", "path": "bad", "status": 999}]}), encoding="utf-8")
    assert main(["serve", "--port", "0", "--file", str(file)]) == 1
    err = capsys.readouterr().err
    assert "拒绝启动" in err
    assert "routes[0].method" in err

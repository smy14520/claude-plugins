"""集成测试共用夹具：契约从 dict 写到临时文件再加载，服务起在 127.0.0.1:0（端口由内核分配）。"""

import http.client
import json
import threading
import urllib.parse
from collections.abc import Callable
from pathlib import Path

import pytest

from mock_server.contract import load_contract
from mock_server.server import MockServer


@pytest.fixture
def server_factory(tmp_path: Path) -> Callable[[dict], str]:
    """启动一个携带给定契约 dict 的真服务，返回 base_url。"""
    servers: list[MockServer] = []

    def _start(document: dict) -> str:
        contract_file = tmp_path / f"mocks-{len(servers)}.json"
        contract_file.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
        server = MockServer(("127.0.0.1", 0), load_contract(contract_file))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        servers.append(server)
        host, port = server.server_address[:2]
        return f"http://{host}:{port}"

    yield _start

    for server in servers:
        server.shutdown()
        server.server_close()


@pytest.fixture
def send() -> Callable[[str, str, str], tuple[http.client.HTTPResponse, bytes]]:
    """向测试服务发一个请求，返回 (响应, 响应体)；target 只含路径与查询串。"""

    def _send(base_url: str, method: str, target: str) -> tuple[http.client.HTTPResponse, bytes]:
        parsed = urllib.parse.urlsplit(base_url)
        conn = http.client.HTTPConnection(parsed.hostname, parsed.port, timeout=5)
        try:
            conn.request(method, target)
            response = conn.getresponse()
            return response, response.read()
        finally:
            conn.close()

    return _send

"""测试公共设施：把契约字典经真实加载路径变成运行中的 MockServer。"""

import json

import pytest

from mock_server.contract import load_contract
from mock_server.server import MockServer


@pytest.fixture()
def write_contract(tmp_path):
    """write_contract(document, name="mocks.json") -> 已写入 tmp_path 的契约文件路径。"""

    def _write(document, name="mocks.json"):
        path = tmp_path / name
        path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
        return path

    return _write


@pytest.fixture()
def mock_server(tmp_path, write_contract):
    """mock_server(routes_dict, **kwargs) -> 已在临时端口后台运行的 MockServer。"""
    started = []

    def _start(routes, **kwargs):
        server = MockServer(load_contract(write_contract({"routes": routes})), **kwargs)
        server.start_background()
        started.append(server)
        return server

    yield _start
    for server in started:
        server.shutdown()

"""HTTP 服务：把请求映射到契约快照中的模拟响应。

匹配规则（与 README、CONTEXT.md 保持一致）：
路径按字节精确匹配（查询串除外），method 大写归一，无任何隐式行为。
"""

import json
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import __version__
from .contract import JSON_CONTENT_TYPE, NO_BODY_STATUSES, Contract, Route


class MockServer(ThreadingHTTPServer):
    """把契约快照挂在 server 实例上，handler 每请求自查。"""

    def __init__(self, address: tuple[str, int], contract: Contract) -> None:
        self.contract = contract
        super().__init__(address, MockRequestHandler)


class MockRequestHandler(BaseHTTPRequestHandler):
    server_version = f"mock-server/{__version__}"
    protocol_version = "HTTP/1.1"
    timeout = 60  # 半开连接超时关闭，不泄漏线程

    def __getattr__(self, name: str):
        # 标准库按 "do_<METHOD>" 分发，找不到就回 501。把它接管成恒 404：
        # 契约之外的方法与路径一样，都属于未匹配。
        if name.startswith("do_"):
            return self._handle
        raise AttributeError(name)

    def log_message(self, format: str, *args: object) -> None:
        pass  # 静默标准库的 stderr 日志，访问日志由 _handle 统一打

    def _handle(self) -> None:
        started = time.monotonic()
        contract: Contract = self.server.contract
        method = self.command.upper()
        path = self.path.split("?", 1)[0]  # 查询串整体忽略
        route: Route | None = contract.lookup.get((method, path))
        if route is None:
            status, body, has_body = 404, _miss_body(method, path), True
        else:
            status, body, has_body = route.status, route.body, route.has_body

        has_entity = status not in NO_BODY_STATUSES  # 204/304 按 RFC 不带实体头
        self.send_response(status)
        if has_entity:
            if has_body:
                self.send_header("Content-Type", JSON_CONTENT_TYPE)
            self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if has_entity and has_body and self.command != "HEAD":
            self.wfile.write(body)  # HEAD 按协议省略响应体，头照发

        elapsed_ms = round((time.monotonic() - started) * 1000)
        timestamp = datetime.now().strftime("%H:%M:%S")  # noqa: DTZ005 -- 访问日志给人眼看的本地墙上时间
        print(f"{timestamp} {method} {self.path} → {status} {elapsed_ms}ms", flush=True)


def _miss_body(method: str, path: str) -> bytes:
    return json.dumps(
        {"error": "route not found", "method": method, "path": path},
        ensure_ascii=False,
    ).encode("utf-8")

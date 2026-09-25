"""HTTP 服务层：把匹配语义接到标准库 ``ThreadingHTTPServer`` 上（ADR-0001）。

本模块只做三件事：收请求、按匹配结果写预置响应、记录请求日志。
"哪条路由该返回什么"的判断全部在 contract / matching 纯函数层。
"""

from __future__ import annotations

import json
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import IO

from .contract import Contract, Route
from .matching import Matched, MethodNotAllowed, NotFound, match_route, strip_query
from .request_log import RequestLog


class MockServer(ThreadingHTTPServer):
    """持有契约与请求日志的 ``ThreadingHTTPServer``（每请求一线程）。"""

    daemon_threads = True

    def __init__(self, contract: Contract, request_log: RequestLog, host: str, port: int) -> None:
        super().__init__((host, port), MockRequestHandler)
        self.contract = contract
        self.request_log = request_log

    def handle_error(self, request: object, client_address: tuple[str, int]) -> None:
        """客户端中途断开（curl 提前 Ctrl+C 等）是本地开发的常态，静默处理。"""


def make_server(
    contract: Contract,
    *,
    host: str = "127.0.0.1",
    port: int = 8080,
    sink: IO[str] | None = None,
) -> MockServer:
    """在 ``(host, port)`` 上构建服务；``port=0`` 时由内核分配（测试缝）。"""
    return MockServer(contract, RequestLog(sink), host, port)


class MockRequestHandler(BaseHTTPRequestHandler):
    """把每个请求翻译成契约中的预置响应。"""

    protocol_version = "HTTP/1.1"

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002  # 基类签名
        """静默基类的 stderr 日志：请求日志由 :meth:`_handle` 统一输出。"""

    def do_GET(self) -> None:
        self._handle()

    def do_POST(self) -> None:
        self._handle()

    def do_PUT(self) -> None:
        self._handle()

    def do_PATCH(self) -> None:
        self._handle()

    def do_DELETE(self) -> None:
        self._handle()

    def do_HEAD(self) -> None:
        self._handle()

    def do_OPTIONS(self) -> None:
        self._handle()

    def _handle(self) -> None:
        started = time.perf_counter()
        self._drain_request_body()
        result = match_route(self.server.contract.routes, self.command, self.path)  # type: ignore[attr-defined]

        if isinstance(result, Matched):
            status = self._send_route(result.route)
            note = None
        elif isinstance(result, MethodNotAllowed):
            status = self._send_json(
                405,
                {"error": f"method not allowed for {strip_query(self.path)}"},
                extra_headers={"Allow": ", ".join(result.allowed)},
            )
            note = "method not allowed"
        else:
            assert isinstance(result, NotFound)
            body = self.server.contract.not_found_body  # type: ignore[attr-defined]
            status = self._send_json(
                404,
                body if body is not None else {"error": f"no mock for {self.command} {strip_query(self.path)}"},
            )
            note = "no mock"

        elapsed_ms = (time.perf_counter() - started) * 1000
        self.server.request_log.log(self.command, self.path, status, elapsed_ms, note)  # type: ignore[attr-defined]

    def _send_route(self, route: Route) -> int:
        body = None if route.body is None else json.dumps(route.body, ensure_ascii=False).encode("utf-8")
        headers = {"Content-Type": "application/json"} if body is not None else {}
        headers.update(route.headers)  # 契约声明的响应头优先，可覆盖默认 Content-Type
        self.send_response(route.status)
        for name, value in headers.items():
            self.send_header(name, value)
        payload = body if body is not None else b""
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        if self.command != "HEAD" and payload:
            self.wfile.write(payload)
        return route.status

    def _send_json(self, status: int, body: object, extra_headers: dict[str, str] | None = None) -> int:
        payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        for name, value in (extra_headers or {}).items():
            self.send_header(name, value)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(payload)
        return status

    def _drain_request_body(self) -> None:
        """读掉请求体但不使用：HTTP/1.1 keep-alive 下不排空会污染同连接的下一请求。"""
        length = self.headers.get("Content-Length")
        if length is None:
            return
        try:
            remaining = int(length)
        except ValueError:
            return
        while remaining > 0:
            chunk = self.rfile.read(min(remaining, 65536))
            if not chunk:
                break
            remaining -= len(chunk)

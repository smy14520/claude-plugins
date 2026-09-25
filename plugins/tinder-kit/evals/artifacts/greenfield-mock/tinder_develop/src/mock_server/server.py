"""HTTP 服务层：把契约的命中/未命中语义落到 HTTP 协议上。

基座只用标准库 http.server（ADR-0001），因此协议正确性（Content-Length、HEAD
无体、HTTP/1.1 keep-alive 下排空请求体）是本模块的显式测试义务。未命中语义
（一律 404 + JSON 错误体，任何 method 都不许漏到 stdlib 的 501）与精确匹配
定义见 ADR-0004。
"""

from __future__ import annotations

import json
import threading
from collections.abc import Callable
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .contract import Contract, Route, strip_query

JSON_CONTENT_TYPE = "application/json; charset=utf-8"
TEXT_CONTENT_TYPE = "text/plain; charset=utf-8"

Log = Callable[[str], None]


class _Server(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address: tuple[str, int], contract: Contract, log: Log) -> None:
        self.contract = contract
        self.log = log
        super().__init__(address, _Handler)


class MockServer:
    """契约驱动的本地模拟服务。log 是访问日志 sink（callable(str)），默认写 stdout。"""

    def __init__(
        self,
        contract: Contract,
        host: str = "127.0.0.1",
        port: int = 0,
        log: Log | None = None,
    ) -> None:
        self._log = log if log is not None else self._log_to_stdout
        self._http = _Server((host, port), contract, self._log)
        self._thread: threading.Thread | None = None

    @property
    def address(self) -> tuple[str, int]:
        """实际绑定的 (host, port)；port=0 时即内核分配的临时端口。"""
        return self._http.server_address[:2]

    def start_background(self) -> threading.Thread:
        """在 daemon 线程中开始服务；测试与嵌入场景使用。"""
        self._thread = threading.Thread(target=self._http.serve_forever, daemon=True)
        self._thread.start()
        return self._thread

    def serve_forever(self) -> None:
        """阻塞当前线程直至 shutdown() 或 KeyboardInterrupt。"""
        try:
            self._http.serve_forever()
        finally:
            self._http.server_close()

    def shutdown(self) -> None:
        self._http.shutdown()
        self._http.server_close()

    @staticmethod
    def _log_to_stdout(line: str) -> None:
        print(line, flush=True)


class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def __getattr__(self, name: str):
        """任意 method 都路由进 _handle：未命中语义由契约裁决，绝无 stdlib 501 兜底。"""
        if name.startswith("do_"):
            return self._handle
        raise AttributeError(name)

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002 - 标准库签名
        pass  # 默认 stderr 噪音关闭：访问日志统一走 server.log sink

    def _handle(self) -> None:
        self._drain_request_body()
        route = self.server.contract.match(self.command, self.path)
        if route is None:
            self._respond_miss()
        else:
            self._respond(route)

    def _drain_request_body(self) -> None:
        """排空请求体，否则 keep-alive 连接上的下一个请求会读到残渣。"""
        length = self.headers.get("Content-Length")
        if not length:
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

    def _respond(self, route: Route) -> None:
        body_bytes, content_type = _render_body(route.body)
        headers = dict(route.headers)
        if content_type is not None:
            headers.setdefault("Content-Type", content_type)
        self._send(
            route.status,
            body_bytes,
            headers,
            route_pointer=f"{route.method} {route.path}",
        )

    def _respond_miss(self) -> None:
        clean = strip_query(self.path)
        message = {"error": f"No mock for {self.command} {clean}"}
        body_bytes = _json_bytes(message)
        self._send(404, body_bytes, {"Content-Type": JSON_CONTENT_TYPE}, route_pointer=None)

    def _send(
        self,
        status: int,
        body_bytes: bytes,
        headers: dict[str, str],
        route_pointer: str | None,
    ) -> None:
        self.send_response(status)
        for name, value in headers.items():
            self.send_header(name, value)
        self.send_header("Content-Length", str(len(body_bytes)))
        self.end_headers()
        if self.command != "HEAD" and body_bytes:
            self.wfile.write(body_bytes)
        self._log_access(status, route_pointer)

    def _log_access(self, status: int, route_pointer: str | None) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        line = f'{timestamp} {self.client_address[0]} "{self.command} {self.path}" -> {status}'
        if route_pointer:
            line += f" via {route_pointer}"
        self.server.log(line)


def _render_body(body: object) -> tuple[bytes, str | None]:
    """响应体（Body）渲染：JSON 对象/数组 -> application/json；字符串 -> text/plain 原样。"""
    if body is None:
        return b"", None
    if isinstance(body, str):
        return body.encode("utf-8"), TEXT_CONTENT_TYPE
    return _json_bytes(body), JSON_CONTENT_TYPE


def _json_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False).encode("utf-8")

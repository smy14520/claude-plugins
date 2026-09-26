"""HTTP serving: segment-level route matching over ThreadingHTTPServer."""
from __future__ import annotations

import json
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import NamedTuple, Sequence

from .config import PATH_PARAMETER_RE, Route


class MatchResult(NamedTuple):
    """Outcome of matching one request against the contract."""

    matched: Route | None
    method_mismatch: Route | None


def _template_matches(template: str, segments: list[str]) -> bool:
    parts = template.split("/")[1:]
    if len(parts) != len(segments):
        return False
    return all(
        PATH_PARAMETER_RE.match(part) is not None or part == segment
        for part, segment in zip(parts, segments)
    )


def match_route(routes: Sequence[Route], method: str, path: str) -> MatchResult:
    """Match a request against the contract in file order.

    matched is the first route whose method and path template both fit.
    When nothing matches, method_mismatch is the first route whose path
    template alone fits (the 405 branch), else None.
    """
    target = path.partition("?")[0]
    segments = target.split("/")[1:]
    matched: Route | None = None
    method_mismatch: Route | None = None
    for route in routes:
        if not _template_matches(route.path_template, segments):
            continue
        if route.method == method:
            matched = route
            break
        if method_mismatch is None:
            method_mismatch = route
    return MatchResult(matched, None if matched else method_mismatch)


def make_handler(routes: Sequence[Route]) -> type[BaseHTTPRequestHandler]:
    """Build a request handler bound to a fixed set of routes."""

    class MockHandler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def _handle(self) -> None:
            started = time.perf_counter()
            result = match_route(routes, self.command, self.path)
            if result.matched is not None:
                route = result.matched
                status = route.status
                payload = route.body
                label = f"[{route.method} {route.path_template}]"
            elif result.method_mismatch is not None:
                status = 405
                payload = {"error": f"method {self.command} not allowed for this path"}
                label = "no match"
            else:
                status = 404
                payload = {"error": "no mock matched this request"}
                label = "no match"

            body = b"" if payload is None else json.dumps(payload).encode("utf-8")
            self.send_response(status)
            has_content_type = any(
                name.lower() == "content-type" for name in route.headers
            ) if result.matched is not None else False
            if not has_content_type:
                self.send_header("Content-Type", "application/json")
            if result.matched is not None:
                for name, value in route.headers.items():
                    self.send_header(name, value)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()

            elapsed_ms = (time.perf_counter() - started) * 1000
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(
                f"{timestamp} {self.command} {self.path} → {status} {label} {elapsed_ms:.1f}ms",
                flush=True,
            )
            if self.command != "HEAD":
                self.wfile.write(body)

        def log_message(self, format: str, *args: object) -> None:  # noqa: A002
            pass  # the per-request line above replaces the default stderr log

        do_GET = do_POST = do_PUT = do_PATCH = do_DELETE = _handle
        do_HEAD = do_OPTIONS = do_TRACE = _handle

    return MockHandler


def serve(routes: Sequence[Route], host: str, port: int, contract: str) -> None:
    """Serve the routes until interrupted by Ctrl+C."""
    server = ThreadingHTTPServer((host, port), make_handler(routes))
    bound_port = server.server_address[1]
    print(
        f"mock-server: {len(routes)} route(s) loaded from {contract}, "
        f"serving at http://{host}:{bound_port} (Ctrl+C to stop)",
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    print("mock-server: stopped", flush=True)

"""mock-server 命令行入口：``serve`` 与 ``check`` 两个子命令。"""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .contract import ContractFileMissing, ContractInvalid, load_contract_file
from .server import make_server

_EXIT_ERROR = 1
_EXIT_OK = 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mock-server",
        description="轻量本地 HTTP API Mock 服务：读取 mocks.json 契约，提供静态路由与预置响应。",
    )
    parser.add_argument("--version", action="version", version=f"mock-server {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    serve = sub.add_parser("serve", help="加载契约文件并启动本地 HTTP 服务")
    serve.add_argument("--port", type=int, default=8080, help="监听端口（默认 8080）")
    serve.add_argument("--host", default="127.0.0.1", help="绑定地址（默认 127.0.0.1，不暴露局域网）")
    serve.add_argument("--file", default="mocks.json", help="契约文件路径（默认当前目录下的 mocks.json）")

    check = sub.add_parser("check", help="校验契约文件，不启动服务")
    check.add_argument("--file", default="mocks.json", help="契约文件路径（默认当前目录下的 mocks.json）")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "serve":
        return _serve(args)
    return _check(args)


def _serve(args: argparse.Namespace) -> int:
    try:
        contract = load_contract_file(args.file)
    except ContractFileMissing:
        print(f"mock-server: 找不到契约文件 {args.file}", file=sys.stderr)
        return _EXIT_ERROR
    except ContractInvalid as exc:
        # fail-fast：契约是契约，带病启动只会制造"为什么我的 mock 没生效"排查地狱。
        print(f"契约加载失败，mock-server 拒绝启动：共 {len(exc.errors)} 处错误", file=sys.stderr)
        for error in exc.errors:
            print(f"  - {error}", file=sys.stderr)
        return _EXIT_ERROR

    try:
        server = make_server(contract, host=args.host, port=args.port)
    except OSError as exc:
        detail = exc.strerror or str(exc)
        print(f"mock-server: 无法监听 {args.host}:{args.port}（{detail}）", file=sys.stderr)
        return _EXIT_ERROR

    host, port = server.server_address[:2]
    print(f"mock-server serving {len(contract.routes)} routes from {args.file} at http://{host}:{port}")
    print("按 Ctrl+C 停止")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    print("mock-server stopped")
    return _EXIT_OK


def _check(args: argparse.Namespace) -> int:
    try:
        contract = load_contract_file(args.file)
    except ContractFileMissing:
        print(f"mock-server: 找不到契约文件 {args.file}", file=sys.stderr)
        return _EXIT_ERROR
    except ContractInvalid as exc:
        print(f"{args.file} 校验失败，共 {len(exc.errors)} 处错误：", file=sys.stderr)
        for error in exc.errors:
            print(f"  - {error}", file=sys.stderr)
        return _EXIT_ERROR

    for route in contract.routes:
        print(f"{route.method:<7} {route.path} -> {route.status}")
    print(f"契约校验通过：{len(contract.routes)} 条路由")
    return _EXIT_OK

"""命令行入口：``serve`` 启动服务，``check`` 只校验契约。

零隐式行为延伸到 CLI 本身：不敲子命令就是不会用，打印用法退出 2，
不做「不带子命令就默认 serve」之类的贴心魔法。
"""

import argparse
import sys
from pathlib import Path

from .contract import Contract, ContractError, load_contract
from .server import MockServer

_DEFAULT_PORT = 8000
_DEFAULT_CONFIG = "mocks.json"
_BIND_HOST = "127.0.0.1"  # 纯单机定位：焊死回环地址，不提供改绑能力


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mock-server",
        description="轻量本地 HTTP API Mock 服务：读取 mocks.json 静态契约，返回固定的模拟响应。",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    serve = subparsers.add_parser("serve", help="启动 mock 服务（Ctrl-C 静默退出）")
    serve.add_argument(
        "-p", "--port", type=int, default=_DEFAULT_PORT, help=f"监听端口（默认 {_DEFAULT_PORT}）"
    )
    serve.add_argument(
        "-c",
        "--config",
        type=Path,
        default=_DEFAULT_CONFIG,
        help=f"契约文件路径（默认 {_DEFAULT_CONFIG}）",
    )
    serve.set_defaults(func=_run_serve)

    check = subparsers.add_parser("check", help="校验契约文件后退出，不启动服务")
    check.add_argument(
        "-c",
        "--config",
        type=Path,
        default=_DEFAULT_CONFIG,
        help=f"契约文件路径（默认 {_DEFAULT_CONFIG}）",
    )
    check.set_defaults(func=_run_check)

    return parser


def _load_contract_or_report(config: Path) -> Contract | None:
    """加载契约；失败时打一行人话到 stderr 并返回 None（调用方负责退出码 1）。"""
    try:
        return load_contract(config)
    except ContractError as exc:
        print(f"mock-server: {exc}", file=sys.stderr)
        return None


def _run_serve(args: argparse.Namespace) -> int:
    if not 1 <= args.port <= 65535:
        print(f"mock-server: 端口必须在 1-65535 之间，收到 {args.port}", file=sys.stderr)
        return 1
    contract = _load_contract_or_report(args.config)
    if contract is None:
        return 1
    try:
        server = MockServer((_BIND_HOST, args.port), contract)
    except OSError as exc:
        print(f"mock-server: 无法监听 {_BIND_HOST}:{args.port}（{exc.strerror}）", file=sys.stderr)
        return 1

    print(
        f"mock-server listening on http://{_BIND_HOST}:{args.port} "
        f"({len(contract.routes)} routes from {args.config})"
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass  # Ctrl-C 静默退出
    finally:
        server.server_close()
    return 0


def _run_check(args: argparse.Namespace) -> int:
    contract = _load_contract_or_report(args.config)
    if contract is None:
        return 1
    print(f"{args.config}: 契约有效，共 {len(contract.routes)} 条路由")
    return 0

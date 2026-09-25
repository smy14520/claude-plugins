"""CLI 装配：解析参数 → 加载契约（fail-fast）→ 打印 Banner → 服务直至 Ctrl-C。

退出码约定：契约不可用（缺文件 / 校验失败 / 不可读）一律 2；Ctrl-C 干净退出 0。
"""

from __future__ import annotations

import argparse
import sys

from .contract import Contract, ContractValidationError, load_contract
from .server import MockServer


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        contract = load_contract(args.file)
    except FileNotFoundError:
        print(f"error: contract file not found: {args.file}", file=sys.stderr)
        return 2
    except OSError as error:
        print(f"error: cannot read contract {args.file}: {error}", file=sys.stderr)
        return 2
    except ContractValidationError as error:
        print(f"error: invalid contract {args.file}:", file=sys.stderr)
        for message in error.errors:
            print(f"  - {message}", file=sys.stderr)
        return 2
    return serve(contract, args.host, args.port, args.file)


def serve(contract: Contract, host: str, port: int, source: str) -> int:
    """阻塞服务；就绪时打印 Banner，Ctrl-C 以 0 退出。"""
    server = MockServer(contract, host=host, port=port)
    bound_host, bound_port = server.address
    print(
        f"mock-server serving {len(contract.routes)} routes "
        f"from {source} at http://{bound_host}:{bound_port}",
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("mock-server stopped.", flush=True)
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mock-server",
        description="Serve a mocks.json contract as a local HTTP API mock.",
    )
    parser.add_argument("--file", default="mocks.json", help="contract file path (default: ./mocks.json)")
    parser.add_argument("--host", default="127.0.0.1", help="bind address (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="port (default: 8000)")
    return parser


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

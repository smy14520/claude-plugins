"""测试基建：所有测试经由 CLI 入口（wikicli.cli.main）执行命令并捕获 stdout/stderr。

唯一测试 seam 是 CLI 命令面（spec: Testing Decisions）——不直接测内部函数。
"""

from __future__ import annotations

import contextlib
import io
from pathlib import Path

from wikicli.cli import main

FIXTURES = Path(__file__).parent / "fixtures"
VAULTS = FIXTURES / "vaults"


def vault_path(name: str) -> Path:
    """按名称取固件 vault 目录。"""
    return VAULTS / name


def run_cli(args: list[str]) -> tuple[int, str, str]:
    """以编程方式调用 CLI 入口，返回 (退出码, stdout, stderr)。"""
    out, err = io.StringIO(), io.StringIO()
    code: int
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            result = main(list(args))
        except SystemExit as exc:  # argparse 用法错误走 SystemExit
            code = exc.code if isinstance(exc.code, int) else 0
        else:
            code = result
    return code, out.getvalue(), err.getvalue()

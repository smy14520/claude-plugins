"""scan：vault → 页面文件流。

vault 边界规则（spec）：递归扫描 `*.md`；跳过隐藏目录（`.` 开头）、
符号链接、`.wiki_index.json`。对 vault 只读；非 UTF-8 文件容错读取。
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

#: 唯一允许的缓存文件名（ADR-0001），即便改名成 .md 也永不扫描
_SKIP_FILES = {".wiki_index.json"}


def iter_page_paths(vault: Path) -> Iterator[Path]:
    """按确定顺序（目录、文件名均排序）产出 vault 内全部页面文件路径。"""
    for root, dirs, files in os.walk(vault, followlinks=False):
        dirs[:] = sorted(
            d for d in dirs if not d.startswith(".") and not (Path(root) / d).is_symlink()
        )
        for name in sorted(files):
            if not name.endswith(".md") or name in _SKIP_FILES:
                continue
            path = Path(root) / name
            if path.is_symlink():
                continue
            yield path


def read_text(path: Path) -> str:
    """容错读取页面文本：非 UTF-8 字节按替换处理，不让坏文件毁掉整次分析。"""
    return path.read_text(encoding="utf-8", errors="replace")

"""测试共享夹具。"""

import pytest


@pytest.fixture
def write_vault():
    """返回写盘助手：在 root 下按 {相对路径: 内容} 落盘测试 vault。"""

    def _write(root, files):
        for rel, content in files.items():
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")

    return _write

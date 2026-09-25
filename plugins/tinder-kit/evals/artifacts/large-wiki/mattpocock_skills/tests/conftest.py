"""测试夹具：在 tmp_path 里快速搭建 Vault。"""

from __future__ import annotations

import pytest


@pytest.fixture
def vault(tmp_path):
    """make({"相对路径": "内容"}) → 返回 Vault 根目录。"""

    def make(files: dict[str, str]) -> "object":
        for rel, content in files.items():
            path = tmp_path / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        return tmp_path

    return make

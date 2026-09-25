"""共享 fixture：在临时目录中搭知识库。"""

import itertools

import pytest

_counter = itertools.count()


@pytest.fixture
def vault(tmp_path):
    """make({"相对路径.md": "内容"}) → 返回知识库根目录。

    每次 make() 使用独立子目录，同测试内多次调用互不污染。
    """

    def make(files: dict[str, str]):
        root = tmp_path / f"vault-{next(_counter)}"
        for rel, content in files.items():
            target = root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        return root

    return make

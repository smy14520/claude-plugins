"""frontmatter 最小解析（title:/tags:）与标签并入（ticket 04 checklist 4）。"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from conftest import run_cli, vault_path


def test_frontmatter_tags_merge_into_aggregation() -> None:
    """frontmatter tags: 两种单行列表写法都并入；title/description 不产标签。

    - meta.md：括号列表 [python, 测试] + 正文 #python（同页去重后 python 计 1 页）；
    - bare.md：裸逗号列表 python, 手册；
    - broken.md：围栏未闭合 → 解失败按无 frontmatter，tags 行不并入，正文 #solo 照常提取。
    """
    code, out, err = run_cli(["--vault", str(vault_path("tags-frontmatter")), "tags"])

    assert code == 0
    assert out == (
        "#python  3 页\n"  # meta + bare + python.md
        "#solo  1 页\n"
        "#手册  1 页\n"
        "#测试  1 页\n"
    )


def test_frontmatter_links_are_not_parsed() -> None:
    """frontmatter 内不解析链接：title 里的 [[python]] 不出现在 links 输出。"""
    code, out, err = run_cli(["--vault", str(vault_path("tags-frontmatter")), "links", "meta"])

    assert code == 0
    assert out == (
        "meta.md (meta)\n"
        "→ python.md  [[python]]\n"  # 仅正文那一条
    )

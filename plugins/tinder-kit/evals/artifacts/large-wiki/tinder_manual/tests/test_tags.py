"""行内标签词法：CJK、嵌套、heading/代码排除、大小写归一（Q12）。"""

from wikicore.tags import extract_inline_tags


def test_cjk_and_latin_tag():
    assert extract_inline_tags("这是 #Python 与 #中文标签 混排") == ["python", "中文标签"]


def test_punctuation_terminates():
    assert extract_inline_tags("#tag，以及 #另一个。") == ["tag", "另一个"]


def test_nested_and_charset():
    assert extract_inline_tags("#a/b-c_d #x") == ["a/b-c_d", "x"]


def test_heading_lines_excluded():
    assert extract_inline_tags("## 标题\n# 标题二\n正文 #real") == ["real"]


def test_hash_after_word_char_excluded():
    assert extract_inline_tags("abc#def #real") == ["real"]


def test_slash_leading_rejected():
    assert extract_inline_tags("#/no #yes") == ["yes"]


def test_code_fence_excluded():
    assert extract_inline_tags("```\n#include <x>\n```\n#real") == ["real"]


def test_inline_code_excluded():
    assert extract_inline_tags("运行 `#pip install` 后 #real") == ["real"]


def test_casefold_dedupe():
    assert extract_inline_tags("#Python #python") == ["python"]

"""Parser 文法层（辅 seam）：表驱动验证链接语法矩阵、行号定位与代码块排除。"""

import unittest

from wiki_cli.parser import iter_effective_lines, parse_link_target, parse_markdown


def link_views(text: str) -> list[tuple[str, int]]:
    return [(link.target, link.line) for link in parse_markdown(text).links]


class LinkGrammarMatrixTest(unittest.TestCase):
    """链接语法矩阵：别名 / 锚点 / 子目录路径 / 空白 / 中文与中英混合。"""

    CASES = [
        # (正文片段, 期望目标列表)
        ("[[Page]]", ["Page"]),
        ("[[Page|别名]]", ["Page"]),                      # 别名：取管道前第一段
        ("[[Page#小节]]", ["Page"]),                      # 锚点：剥离后按页面名
        ("[[Page#小节|别名]]", ["Page"]),                 # 锚点 + 别名叠加
        ("[[子目录/名]]", ["子目录/名"]),                 # 子目录路径目标原样保留（解析属 LinkGraph）
        ("[[ Page ]]", ["Page"]),                         # 目标首尾空白剥离
        ("见 [[A]] 与 [[B]]。", ["A", "B"]),              # 一行多条 Link
        ("[[中文页面]]", ["中文页面"]),                   # 中文页面名
        ("[[Mixed 混合123]]", ["Mixed 混合123"]),         # 中英混合页面名
        ("[[#仅锚点]]", []),                              # 剥离后无目标 → 不产出 Link
        ("[[]]", []),
        ("这是个 [[未闭合", []),                          # 未闭合不成链
        ("普通文字没有链接", []),
    ]

    def test_link_grammar_matrix(self):
        for text, expected in self.CASES:
            with self.subTest(text=text):
                self.assertEqual([link.target for link in parse_markdown(text).links], expected)

    def test_parse_link_target_reduces_alias_and_anchor(self):
        cases = {
            "Page": "Page",
            "Page|别名": "Page",
            "Page#小节": "Page",
            "Page#小节|别名": "Page",
            "子目录/名#锚": "子目录/名",
            "  Page  ": "Page",
            "#仅锚点": None,
            "|纯别名": None,
        }
        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(parse_link_target(raw), expected)


class LineNumberTest(unittest.TestCase):

    def test_line_numbers_are_one_based_and_in_order(self):
        text = "第一段无链接\n链到 [[A]]\n再链 [[B]] 与 [[A]]\n"
        self.assertEqual(link_views(text), [("A", 2), ("B", 3), ("A", 3)])


class CodeExclusionTest(unittest.TestCase):
    """围栏代码块与行内代码内的 [[链接]] 不计入（行级状态机，tags 工单复用）。"""

    def test_inline_code_links_are_ignored(self):
        self.assertEqual(link_views("用 `[[Ghost]]` 作示例"), [])

    def test_links_outside_inline_code_survive(self):
        self.assertEqual(link_views("`[[Ghost]]` 与 [[Real]]"), [("Real", 1)])

    def test_fenced_block_links_are_ignored(self):
        text = "[[Real]]\n```\n[[Ghost]]\n```\n[[After]]\n"
        self.assertEqual(link_views(text), [("Real", 1), ("After", 5)])

    def test_fenced_block_with_info_string_and_tilde_marker(self):
        text = "~~~python\n[[Ghost]]\n~~~\n[[Real]]"
        self.assertEqual(link_views(text), [("Real", 4)])

    def test_unclosed_fence_consumes_rest_of_file(self):
        self.assertEqual(link_views("```\n[[Ghost]]\n[[Ghost2]]"), [])

    def test_mismatched_fence_marker_inside_block_is_content(self):
        text = "```\n~~~\n[[Ghost]]\n```\n"
        self.assertEqual(link_views(text), [])

    def test_chinese_link_inside_fenced_block_is_ignored(self):
        text = "```示例\n[[中文幽灵]]\n```\n[[中文页面]]"
        self.assertEqual(link_views(text), [("中文页面", 4)])


class EffectiveLineStateMachineTest(unittest.TestCase):
    """直接验收状态机本身：后续 tags 工单在其上复用。"""

    def test_yields_line_number_with_inline_code_stripped_skipping_fences(self):
        text = "a `x` b\n```\nfenced\n```\ntail [[T]]"
        self.assertEqual(
            list(iter_effective_lines(text)),
            [(1, "a  b"), (5, "tail [[T]]")],
        )


if __name__ == "__main__":
    unittest.main()

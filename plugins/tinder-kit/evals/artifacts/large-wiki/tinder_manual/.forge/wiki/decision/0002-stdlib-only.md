---
title: 运行时纯标准库，零三方依赖
description: wiki-cli 运行时只依赖 Python 标准库；pytest 仅作 dev 依赖；不引入 click/rich/PyYAML/jieba。
type: decision
tags: [wiki, stdlib]
---

# 运行时纯标准库，零三方依赖

wiki-cli 定位为装到任何机器都零摩擦的个人工具，"极简、纯本地"是需求底线。我们拍定：**运行时只依赖 Python 标准库**（`argparse`/`json`/`pathlib`/`re`/`dataclasses`/`os`），`pytest` 仅作 dev 依赖存在。代价是我们手写了极简的 frontmatter `tags:` 解析与标签词法，而不引入 PyYAML；CLI 帮助文本朴素，而不引入 click/rich。

## Considered Options

- **click + rich** —— 否决：美化是糖不是内核，argparse 完全够用，依赖换来的是安装摩擦。
- **PyYAML** —— 否决：仅为解析 `tags:` 一行键值，不值得引入一个通用 YAML 解析器（及其安全面）。
- **jieba 等分词器** —— 否决：检索语义已拍定为子串匹配（对 CJK 天然正确），无需分词。

## Consequences

frontmatter 与标签解析的边界情形（引号、注释、别名键）由我们自己负责并写进测试；未来若要 TUI 或富渲染，需要重新评估此约束。

## Revisit When

frontmatter 使用范围扩展到大量 YAML 特性，或出现强 TUI/主题化需求时。

---
title: 纯标准库零依赖
description: wiki-cli 只用 Python ≥ 3.10 标准库，不引入任何第三方运行时依赖
type: decision
tags: [wiki, tooling]
---

# 纯标准库零依赖

wiki-cli 是个人本地工具，定位是 clone 即用、`pipx`/`uvx` 一行安装。解析需求（提取 `[[链接]]` 与 `#tag`、跳过代码块）用行级状态机 + 正则即可覆盖，远用不到完整 Markdown AST；CLI 编排用 argparse 足够。因此拍定：**零第三方运行时依赖，Python ≥ 3.10**。

## Considered Options

- click/typer — 更优雅的 CLI API，但为 5 个子命令的个人工具引入依赖不值
- markdown-it-py — 完整 AST，但所需信息用轻量解析即可获得
- jieba — 中文分词检索，子串匹配在个人量级下体感足够（量级假设见 ADR-0002）

## Revisit When

- CLI 子命令超过约 10 个、参数编排明显复杂化
- 出现完整 Markdown 语义需求（如渲染 HTML 导出）

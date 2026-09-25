---
title: 零运行时依赖
description: 运行时只用 stdlib（argparse + json），不引入 click/typer 等第三方库
type: decision
tags: [todo, cli]
---

# 零运行时依赖

运行时只依赖 Python 标准库（`argparse` + `json` + `pathlib`），不引入 `click`/`typer`。理由：任何有 Python 的机器拷走即用，`pip install` 零网络需求，与 ADR-0001 的"本地个人工具"定位一致。开发依赖仅 pytest。

## Considered Options

- `click` / `typer` — 否决：帮助排版与 shell 补全更好，但为这点收益让所有目标机器先装第三方依赖，不值。

## Revisit When

命令面膨胀到 argparse 难以维护（深层子命令嵌套、复杂补全需求）时。

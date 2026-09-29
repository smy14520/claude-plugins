# Spec: stock 库存命令

## Problem

`stock` 目前只有持久化层（`stock/store.py`）和一个没有任何子命令的 CLI 骨架（`stock/cli.py`）。仓库管理员需要在终端里入库、出库、查看库存，并找出需要补货的商品。

## Solution

在 `stock/cli.py` 的 argparse 子命令上增加 `add`、`remove`、`list`、`report` 四个命令。每个子命令通过 `set_defaults(handler=...)` 注册处理函数（`main` 已按 `args.handler(store, args)` 调用）。

## Decisions

- 数据仍是 `{商品名: 数量}`，数量为非负整数；数量降为 0 的商品从库存中删除。
- 输出格式统一为每行 `<商品名>: <数量>`，按商品名排序。
- 错误写到 stderr，退出码 1；成功退出码 0。
- 仅用标准库。

## Testing

- 所有命令通过 `stock.cli.main([...])` 在 `tmp_path` 上的库存文件做行为测试，断言 stdout/stderr 与退出码（pytest 的 `capsys`）。

## Out of scope

- 价格、分类、多仓库。
- 交互式界面。

## Tickets

`.forge/inventory/issues/01-add-command.md` … `04-report-command.md`

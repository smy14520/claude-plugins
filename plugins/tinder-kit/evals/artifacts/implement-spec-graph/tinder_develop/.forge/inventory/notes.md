# Notes: stock 库存命令（inventory spec）

供所有 implementer 共享的约定。代码库很小：`stock/cli.py`（argparse 骨架，`main` 按 `args.handler(store, args)` 调用）、`stock/store.py`（`Store.load()/save()`，JSON dict）、`tests/test_store.py`。

## 共享面：stock/cli.py 的确切名字

四张 ticket 都改 `build_parser()`，按以下契约实现（合并冲突时按 add → remove → list → report 顺序保留所有注册块即可）：

- 处理函数命名与签名：`cmd_add` / `cmd_remove` / `cmd_list` / `cmd_report`，均为 `def cmd_x(store: Store, args: argparse.Namespace) -> int`；成功 return 0，错误 return 1。
- `build_parser()` 中把 subparsers 存为变量：`sub = parser.add_subparsers(dest="command", required=True)`；每个命令一个注册块：`p = sub.add_parser("<name>", help=...)` → 加参数 → `p.set_defaults(handler=cmd_x)`。
- 共享格式化函数（**03 定义，04 复用，不得另写**）：

  ```python
  def format_items(items: dict[str, int]) -> str:
      return "\n".join(f"{name}: {qty}" for name, qty in sorted(items.items()))
  ```

  空字典返回 `""`；空案例文案由各命令自己决定（list → `(empty)`，report → `nothing to restock`），`format_items` 不处理空案例。

## 错误与输出约定（spec Decisions）

- 成功：`print(...)` 到 stdout，return 0。输出行格式 `<商品名>: <数量>`。
- 失败：`print("error: ...", file=sys.stderr)`，return 1；库存文件必须保持不变（先校验、后落盘）。
- **qty 校验（01、02 共用）**：qty 参数按字符串接收，handler 内经共享 `parse_positive_int` 解析（**严格十进制**：仅 `[0-9]+`，拒绝 `"1_0"`、全角数字、符号、空白；且 `> 0`）；非法 → stderr 打 `error: 数量必须是正整数: <qty>`，return 1。**不要**用 argparse `type=int` 校验 qty —— argparse 解析失败退出码是 2，spec 要求 1。
- 02 错误文案：商品不存在 → `error: 商品不存在: <name>`；库存不足 → `error: 库存不足: <name>`。
- 02 扣到 0：从库存 dict 删除该商品再 save，但仍打印 `<name>: 0`。
- 04：`--threshold` **同样经 `parse_positive_int` 手写解析**（默认 `"5"`；argparse `type=int` 方案已被 review 裁决否决 —— 非法输入须退出码 1，与 spec 全局规则对齐），非法 → `error: 阈值必须是正整数: <raw>`，return 1；筛选数量**严格小于** threshold 的商品；无结果打印 `nothing to restock`，格式化复用 `format_items`。

## 测试约定

- 行为测试统一走 `stock.cli.main(["--db", str(tmp_path / "stock.json"), ...])`（`--db` 是全局参数，必须放在子命令**前**），用 `capsys` 断言 stdout/stderr 与返回码。
- 每张 ticket 一个测试文件，避免合并冲突：`tests/test_cli_add.py` / `tests/test_cli_remove.py` / `tests/test_cli_list.py` / `tests/test_cli_report.py`。
- 错误断言：return 1、stderr 含 `error:`（文案上文已固定，可全断）；stdout 为空。

## 其他

- 仅标准库，不新增依赖。
- 不要改 `.forge/`（tracker 由 orchestrator 维护）；不要改 `stock/store.py`（四张 ticket 都不需要动它）。
- commit message 引用 ticket 路径，例如：
  `feat(cli): add 入库命令` + 空行 + `Implements .forge/inventory/issues/01-add-command.md`

# 01 — Tracer bullet：骨架 + `links` 最小可跑路径

**What to build:** 从零立起 wiki-cli 可安装可执行的骨架，并打通第一条完整竖切：在 vault 上运行 `links <page>` 得到该页面的正向链接清单，解析不了的显示死链行。本票范围仅含基础链接形态 `[[名]]` 与 `[[名|别名]]`（剥别名）、围栏代码块与行内代码豁免、页面名 stem 精确匹配。含打包 entry point、argparse 接线、`--vault` 定位、用法错误 exit 2，以及首批 CLI 面固件测试。

**Blocked by:** None — can start immediately

**Status:** resolved

- [ ] `pip install -e .` 后 `wiki-cli links <page>` 在固件 vault 上输出人读格式（`路径 (页面名)` 头行 + `→ 目标  [[原文]]` 逐行）
- [ ] 链接目标解析不到任何页面时输出 `✗ 未解析: [[原文]]` 行
- [ ] 围栏代码块与行内代码内的 `[[..]]` 与 `#tag` 不产生任何链接或标签
- [ ] `--vault PATH` 可指定非当前目录的 vault；vault 不存在/非目录/缺参数 → 清晰用法提示 + exit 2
- [ ] 测试全部走 CLI 命令面（调用入口断言 stdout 与退出码），不直接测内部函数

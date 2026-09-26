# 01 — 项目骨架 + wiki links（第一条 tracer bullet）

**What to build:** 从零立起可安装的 CLI 骨架（pyproject、src 布局、入口命令 `wiki`、unittest 基线），并打通第一条端到端路径：对一个临时 Vault 执行 `wiki links`，输出正向出链。后续所有工单都复用这条已铺好的管道（Parser 状态机、页面名注册表、CLI 骨架）。

**Blocked by:** None — can start immediately

**Status:** ready-for-human

- [x] `pip install -e .` 后 `wiki --help` 与 5 个子命令骨架（links/backlinks/tags/search/doctor）可用；运行时零第三方依赖，Python ≥ 3.10
- [x] `wiki links <页面>` 列出该页全部 Link：目标页面名 + `文件:行号`；`wiki links` 省略页面名时输出全 Vault 出链汇总
- [x] `[[Page|别名]]` 取管道前第一段为目标；`[[Page#小节]]` 剥离锚点后按页面名解析
- [x] 页面名注册表 casefold 大小写不敏感 + Unicode NFC 归一化：`[[FOO]]` 命中 `foo.md`；中文文件名 NFC/NFD 等价形态互相解析成功
- [x] 围栏代码块与行内代码内的 `[[链接]]` 不计入出链（行级状态机在此立起，tags 工单复用）
- [x] 子目录 Page 递归发现；`[[子目录/名]]` 精确匹配可用
- [x] Vault 路径不存在 → 中文错误信息 + 退出码 2；空 Vault → 优雅空结果，不崩溃
- [x] `wiki links --json` 输出稳定英文 JSON 字段结构
- [x] unittest（仅 stdlib）覆盖上述全部行为：CLI seam 端到端 + Parser 文法表驱动；中英混合页面名有用例

# 07 — 全局 `--json`：机器可读输出

**What to build:** render seam 双模式收口：全部五个命令支持 `--json`，stdout 输出单个 JSON 文档，字段名稳定（稳定承诺自此生效）；doctor 的 JSON 含 `dead_links`/`orphans`/`ambiguous` 数组。人读模式行为不受影响。

**Blocked by:** 03 — `backlinks`：反向引用查询；04 — 标签体系：提取规则 + `tags` 聚合；05 — `search`：关键词全文检索；06 — `doctor`：健康体检与退出码

**Status:** resolved

- [ ] 五命令 `--json` 均输出可解析的单个 JSON 文档；字段结构在测试中固化
- [ ] doctor JSON 三类发现数组齐备，条目含路径/行号/原文等定位信息
- [ ] `--json` 不改变退出码语义；人读输出与此前完全一致
- [ ] CLI 面测试对每命令的 JSON 结构断言

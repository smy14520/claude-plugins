# 02 — wiki backlinks 与 doctor 健康体检

**What to build:** 在链接图上补齐反向视图与整体健康面：`wiki backlinks <页面>` 回答"谁链接到我"；`wiki doctor` 扫描并报告 Dead Link、Orphan、页面名冲突与汇总统计，退出码可作脚本门禁。

**Blocked by:** 01 — 项目骨架 + wiki links（tracer bullet）

**Status:** ready-for-agent

- [ ] `wiki backlinks <页面>` 列出所有指向该页的来源 Page（含 `文件:行号`）；无引用时输出明确的空结果语义
- [ ] doctor 报告每个 Dead Link：来源 `文件:行号` + 目标名；Orphan 清单（入度为零的 Page）；casefold 后同名多文件的冲突清单
- [ ] doctor 输出汇总统计（Page 数 / Link 数 / 死链数 / 孤岛数）；退出码：健康 0 / 存在问题 1
- [ ] 中文与中英混合页面名在 Backlink 与 doctor 报告中正确解析与展示（中英混排验收）
- [ ] `wiki backlinks --json` 与 `wiki doctor --json` 稳定字段结构
- [ ] unittest（仅 stdlib）：使用"刻意埋入死链、孤岛、冲突页面"的 Vault fixture 场景覆盖

# 04 — wiki search：关键词检索

**What to build:** `wiki search <关键词...>` 命令：基于页面名与正文的 Keyword Search——大小写不敏感子串匹配、多词 AND、标题加权排序。SearchEngine 无状态、零持久化（ADR-0002 红线）。

**Blocked by:** 01 — 项目骨架 + wiki links（tracer bullet）

**Status:** ready-for-agent

- [ ] `wiki search <关键词...>`：页面名 + 剥离代码块后的正文文本，casefold 子串匹配；多关键词空格分隔取 AND
- [ ] 排序验收：标题（页面名）命中的 Page 排在仅正文命中之前；同级按命中次数与页面名稳定排序
- [ ] 结果展示命中页面的 `文件:行号` 入口与命中计数；零命中 → 明确空结果语义
- [ ] 中文关键词（如 `领域驱动`）与中英混合查询均有验收用例（中英混排验收）
- [ ] 不引入任何持久化索引或检索服务（红线核查项）
- [ ] `wiki search --json` 稳定字段结构
- [ ] unittest（仅 stdlib）：CLI seam 端到端覆盖匹配/排序/AND 语义/空结果

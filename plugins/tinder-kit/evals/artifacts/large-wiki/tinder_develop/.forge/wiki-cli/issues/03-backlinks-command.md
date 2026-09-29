# 03 — `backlinks`：反向引用查询

**What to build:** 建立入向视角：`backlinks <page>` 列出引用方路径、行号与原文写法。歧义链接的反向引用记入每个候选页面；自链接不构成反向引用（孤岛判定语义的前置）。

**Blocked by:** 02 — 链接解析完备化：全形态写法 + 三态 resolve

**Status:** resolved

- [ ] `wiki-cli backlinks <page>` 输出头行 `路径 (页面名) ← N 条反向引用`，逐条 `引用方路径:行号  [[原文]]`
- [ ] 同一页面被同一引用方多次引用时逐条列出（不合并）
- [ ] 歧义目标时每个候选页面的 `backlinks` 都包含该引用
- [ ] 自链接不出现在 `backlinks` 结果中
- [ ] CLI 面测试覆盖以上全部

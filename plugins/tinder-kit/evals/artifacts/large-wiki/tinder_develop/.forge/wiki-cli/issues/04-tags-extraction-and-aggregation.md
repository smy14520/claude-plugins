# 04 — 标签体系：提取规则 + `tags` 聚合

**What to build:** 按 spec 全规则提取标签并交付两个查询面：`tags`（全量聚合，`#标签名  N 页` 逐行，页数降序、同数按字典序）与 `tags <tag>`（标签 → 页面路径列表；父标签含全部子孙；输入可带不带 `#`）。含 frontmatter 最小解析（`title:`/`tags:`）与标签并入逻辑。

**Blocked by:** 01 — Tracer bullet：骨架 + `links` 最小可跑路径

**Status:** resolved

- [ ] CJK 标签有效；CJK 紧邻 `#`（`看看#python`）有效；URL 中 `#`（`https://x#/a`）与纯数字 `#1` 不误报
- [ ] 标题行（`# ` 开头）与 `##tag` 不算标签；围栏/行内代码区豁免
- [ ] 嵌套标签按完整路径聚合；`tags <父标签>` 返回含全部子孙标签的页面集合
- [ ] frontmatter `tags:` 并入聚合、`title:` 被读取；frontmatter 内不解析链接
- [ ] `tags` 输出排序正确；`tags <tag>` 的 `#` 前缀可选
- [ ] CLI 面测试覆盖以上全部（与 02/03 无依赖，可独立验证）

# 03 — wiki tags：#tag 提取与聚合

**What to build:** `wiki tags` 命令：从全 Vault 正文提取 `#tag` 并聚合（计数 + 使用页面清单），附带完整无歧义的 Tag 文法。

**Blocked by:** 01 — 项目骨架 + wiki links（tracer bullet）

**Status:** ready-for-agent

- [ ] `wiki tags` 聚合全 Vault Tag：完整字符串计数降序 + 每个.Tag 的使用 Page 清单
- [ ] Tag 文法矩阵验收：`#` + Unicode 字母/数字/`-`/`_`/`/`；嵌套写法 `#a/b` 按完整字符串聚合计数；不以数字开头；`#` 前须为行首或非文字字符（`http://x#frag`、`foo#bar` 排除）；`# 后跟空格`（Markdown 标题）排除
- [ ] 围栏代码块与行内代码内的 `#tag` 不计入（复用 01 的行级状态机）
- [ ] 中文与中英混合 Tag（如 `#领域驱动设计`、`#混合tag`）按一等公民提取（中英混排验收）
- [ ] `wiki tags --json` 稳定字段结构
- [ ] unittest（仅 stdlib）：表驱动覆盖整个文法矩阵

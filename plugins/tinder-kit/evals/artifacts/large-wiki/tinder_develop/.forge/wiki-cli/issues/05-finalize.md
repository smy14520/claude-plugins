# 05 — 收尾：JSON 契约冻结、退出码统一、README 与全量回归

**What to build:** 交付前的整备：跨命令契约一致性核验、用户文档、全量回归与审查收口。

**Blocked by:** 02 — backlinks 与 doctor；03 — tags；04 — search

**Status:** ready-for-agent

- [ ] 全部 5 个命令的 `--json` 字段结构逐一复核并在 README 中文档化（契约冻结）
- [ ] 退出码全命令一致：0 = 正常/空结果，1 = doctor 发现问题，2 = 用法错误；有跨命令一致性测试
- [ ] README：安装方式、5 命令用法示例、Vault 约定（页面身份/链接/Tag 文法摘要）、JSON 与退出码契约、红线声明（无 SQLite/向量库/外部服务，零第三方运行时依赖）
- [ ] 全量 unittest 回归通过（仅 stdlib，一条命令可跑全部）
- [ ] 以 `.forge/tasks/wiki-cli/state.json` 的对齐结论为 spec 完成 code-review 并修复发现的问题

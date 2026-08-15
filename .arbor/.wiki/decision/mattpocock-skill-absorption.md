---
title: mattpocock/skills 吸收决策
description: 决定从 mattpocock/skills 引入哪些 skill、拒绝哪些及理由时读此页；评估未来候选或打算整装该插件时也先读此页。
type: decision
---

来源仓库：https://github.com/mattpocock/skills（MIT）。迭代极快（2026-08 实测 9 天 422 commits），每次吸收应 pin 到具体 commit 并在产出文件头注明。

## 已吸收

- **handoff**（2026-07，commit 98ef40c）：会话交接文档。
- **code-review 的 Fowler 12 味基线**（2026-08，commit 68f62da）：进 init skill，作为推荐给项目的默认审查基准。
- **grilling 三点**（2026-08）：frontier 轮次、"找事实是 agent 的活"、sub-agent 查事实不阻塞——措辞级吸收进 brainstorm。
- **glossary 纪律**（2026-08）：concept/entity 页零实现细节——吸收进 wiki skill。
- **writing-for-agents**（2026-08）：指针措辞/先导词/否定式反模式/no-op 测试——进本仓库 .claude/rules/prompt-design.md（不进插件）。
- **prototype + wayfinder**（2026-08，task `prototype-wayfinder`）：prototype 做成 seed-prototype agent（无独立 skill 壳，语义触发经 agent description）；wayfinder 做成 .arbor/maps 文件形态（不绑 issue tracker——状态承载从 tracker 换成文件系统是必做替换，不是可选项）。

## 拒绝及理由

- **implement / tdd / to-spec / to-tickets / triage / ask-matt / setup**：与 brainstorm/impl 直接竞争入口，整装会在同会话形成两套工作流词汇抢触发。
- **domain-modeling / CONTEXT.md / ADR 体系**：与 wiki（decision/entity/concept 页）同领域，不双轨。
- **teach / wait-what / grill-me / to-questionnaire**：个人生产力向，与开发工作流定位不同；想要时用 `npx skills add` 单装，不进本插件。

## 下一候选

**diagnosing-bugs**：与 gate/可证伪验收哲学同构（"先造一条能变红的命令"），零基建依赖，是下次吸收的第一候选（用户确认 2026-08-14 暂不评估）。

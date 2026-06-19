# seed-kit

## 核心原则：机制在插件，标准在项目

seed-kit 只提供**机制**（栈无关）：验收义务 obligation（形如 `[kind][surface] <id>: <行为>`，证据以 obligation_id 绑定）、验证三 kind（assert / judge / human）、交付面覆盖校验（面名自由、非封闭）、正确性 gate、单 judge scoring gate、`seed` CLI。judge 可用 legacy `--verdict pass|fail`，也可用项目 rubric + score-file 由 helper 计算 verdict；`--grade` 只是备注，不进 gate。多裁判并行评分循环（fan-out）尚未实装。

**测试纪律、评分标准、品味、参考产品、设计语言、质量基线**——这些属于**标准**，落在**项目**：测试纪律放 `.claude/rules/`（如 `testing.md`），品味与设计语言放 `DESIGN.md`，入口与 `@import` 在 `CLAUDE.md`，体验意图在 PRD 质量基线。**都不进插件**。

为什么：换栈（web / 后端 / CLI / 游戏）不用改插件——**标准随项目长，机制不动**。"前端要打审美分""游戏要打手感分"是项目标准，不是插件该知道的；插件只知道"对每个声明的交付面，派一个独立 scorer 去读该项目的标准来打分"。

推论：
- 插件 skill **不硬编码**任何技术栈的测试工具、审美标准、质量门槛。
- 这些写项目的 `CLAUDE.md` / `DESIGN.md`；Claude Code harness 每次自动加载，brainstorm / impl / review 自然读到，不用插件编码。
- 项目初期没有这些文件时，有两条兜底：其一，插件提供一条通用**质量地板**（只防半成品 / slop 的最低线，是"不断、不糙"的纪律，**不是品味**）；其二，地板之上 AI 自由发挥，由对抗性 judge 把关"是不是真品质"，不按硬编码审美。

一句话：**插件管形态、纪律、机制（与栈无关）；项目管标准、品味、参考（随栈而变）。**

# seed-kit

## 核心原则：机制在插件，标准在项目

seed-kit 只提供**机制**（栈无关）：验收义务 obligation（形如 `[kind][surface] <id>: <行为>`，证据以 obligation_id 绑定）、验证三 kind（assert / judge / human）、交付面覆盖校验（面名自由、非封闭）、正确性 gate、单 judge scoring gate、多裁判聚合（`seed score aggregate`）、`seed` CLI。judge 可用 legacy `--verdict pass|fail`，也可用项目 rubric + score-file 由 helper 计算 verdict；`--grade` 只是备注，不进 gate。多裁判并行评分循环（fan-out）的 helper 已实装（`seed score aggregate`），orchestration 由 Claude 按 review SKILL.md 的模板生成（见 review SKILL「多裁判对抗评分」段落）。

**测试纪律、评分标准、品味、参考产品、设计语言、质量基线**——这些属于**标准**，落在**项目**：测试纪律放 `.claude/rules/`（如 `testing.md`），品味与设计语言放 `DESIGN.md`，入口与 `@import` 在 `CLAUDE.md`，体验意图在 PRD 质量基线。**都不进插件**。

为什么：换栈（web / 后端 / CLI / 游戏）不用改插件——**标准随项目长，机制不动**。"前端要打审美分""游戏要打手感分"是项目标准，不是插件该知道的；插件只知道"对每个声明的交付面，派一个独立 scorer 去读该项目的标准来打分"。

推论：
- 插件 skill **不硬编码**任何技术栈的测试工具、审美标准、质量门槛。
- 这些写项目的 `CLAUDE.md` / `DESIGN.md`；Claude Code harness 每次自动加载，brainstorm / impl / review 自然读到，不用插件编码。
- 项目初期没有这些文件时，有两条兜底：其一，插件提供一条通用**质量地板**（只防半成品 / slop 的最低线，是"不断、不糙"的纪律，**不是品味**）；其二，地板之上 AI 自由发挥，由对抗性 judge 把关"是不是真品质"，不按硬编码审美。

一句话：**插件管形态、纪律、机制（与栈无关）；项目管标准、品味、参考（随栈而变）。**

## 验证哲学：gate 守对错，loop 守好坏

- **正确性是"对错"问题**——一次判定、不可妥协，用 gate 守：assert exit 0、obligation 交付面覆盖、烟雾拦截、schema 形状。
- **体验 / 切片合理性 / scope 充分性是"好坏"问题**——要迭代逼近、没有硬终点，用 loop 守：review 发现问题 → 修复 → 再 review，直到这一轮没有新发现。
- **把好坏塞进 gate（给体验打分要"过"）必然异化为"凑阈值"**：agent 会优化"verdict 变绿"而非"体验变好"，激励错位。所以 judge 不做 gate，做 loop 的质量信号——reviewer 提体验问题，迭代到找不到更多毛病，而非达到某个 min 分。`done` 是 loop 收敛的结果（assert 全绿 + 最近一轮 review 无阻断发现），不是"过门槛"。（注：上文「单 judge scoring gate」是旧表述，judge 定位正按本节从 gate 迁向 loop，review SKILL / conventions 待同步重构。）
- **感知型判断 gate 不了**：切片是否纵向完整 / 割裂、scope 是否充分，没有机械规则能判，只能靠独立 review 在语义层审——这类问题的归属是"一个独立语义 review 环节"，不是机制 / hook。

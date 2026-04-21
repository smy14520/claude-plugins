---
status: closed
date: 2026-04-21
topic: spec-skill-rework
---

<!-- 输出语言: 中文 -->

# 研究: spec-skill-rework

## 研究问题

在一个 skill-first 的 LLM SDD 插件里,一份"最小但够用"的 spec 契约 + 模板应该长什么样,才能让**模板结构本身**承担大部分约束,把 SKILL.md / references 里的散文性规则降到最低?

## 关键发现(直接影响决策)

- **6 种"结构即约束"手法可借鉴,其中 3 种最高价值** — 业界模板通过 GFM checkbox 门禁 / `*(mandatory)*` 标签 / 稳定 ID+RFC2119 / BDD 验收语法 / 子标题拆类别 / 条件必选标签等 6 种手法把规则下沉到结构。sdd-kit 当前只用了其中 1 种(子标题拆分)。**最高价值下沉候选**: mandatory 标签、稳定 ID(类 `FR-NNN`/`AC-NNN`)、Finalize 前置 checkbox 清单。→ `refined/structural-constraints.md`

- **必需字段矩阵显示 sdd-kit 应做 2 加 0 减** — 与 KEP/RFC/SpecKit 对比,sdd-kit 独有的 `Hard constraints` 和 `Integration points` 应保留(是招牌特色);应新增 `Assumptions`(SpecKit 独立章节,LLM 起草时防静默假设) + 可选的 `Risks / Mitigations`(KEP 模式);当前禁止的 `Alternatives / Drawbacks / Prior art` 应继续禁止(它们是 KEP/RFC "spec 即决策过程"模式的产物,与 sdd-kit "spec 即最终契约 + wiki 存决策"的拆分模式不兼容)。→ `refined/required-fields-matrix.md`

- **5 类规则结构化不了,必须留散文** — 判断性("何时激活")、语义理由("为什么禁 X")、跨章节一致性("acceptance 要对齐 goal")、风格/品味("好约束长这样")、流程性("先 decide 再 finalize")。改造时 SKILL.md 应只保留这 5 类散文,其它散文规则下沉到模板结构。判据:"删掉这条规则,用户填模板时**会不会自然违反**?会 → 留散文;不会(模板已强制) → 删。"→ `refined/when-prose-still-wins.md`

- **哲学分歧要明确选边,不要摇摆** — sdd-kit 的"spec 只写结论,决策史推 wiki"vs KEP/RFC 的"Alternatives/Drawbacks 内嵌保留"是不同哲学,各自有成熟先例。sdd-kit 定位(AI agent 高频迭代 + 执行者为主要读者)契合策略 B(拆分),**改造时应坚持**。但可借鉴两点:①KEP 的 Risks/Mitigations 作为可选章节(不是 Alternatives);②Rust RFC "Unresolved questions" 的精神 —— 不加专章(会污染 spec 纯粹性),但保留现有 `<TODO-DECIDE>` + `NEEDS_CONTEXT` 机制。→ `refined/decision-history-handling.md`

## 背景发现(提供上下文)

- **superpowers 代表 skill-first 架构的另一端**:它的 "spec" 完全过程化(通过 brainstorming + writing-plans skill 对话产出),没有单文件强契约。sdd-kit 选择了"单文件强契约"路径,更接近 SpecKit / KEP / Rust RFC。这次改造**不应向 superpowers 方向偏**(过程化会削弱 spec 的"执行者可直接上手"特性)。→ `raw/ext-obra-superpowers-readme.md`

- **SpecKit 的 `*(mandatory)*` 标签 + `FR-NNN` ID 是 AI-native 模板的教科书**:它是本次研究里最接近 sdd-kit 定位的模板(AI agent 驱动、结构化强、mandatory 标签)。后续 spec.md 模板重写强烈建议直接借鉴其视觉约束语法。→ `raw/ext-github-speckit-spec-template.md`

## 待解决问题

(需要在 Phase 1 模板重写阶段决定的 — 不是本次 research 能解决的)

- **BDD 语法(Given/When/Then)是否适合工程向 spec?** SpecKit 的 BDD 偏产品视角,sdd-kit 偏接口契约。可能让工程 spec 过度形式化,也可能让 acceptance 更精确。→ 建议在 `spec-example.md`(xhs-customer-webhook 样例)里试写一节 BDD 验收、一节列表式验收,对比手感后决定
- **Risks/Mitigations 是可选章节还是条件必选?** 对"有明显安全/并发/性能风险"的 spec 是必选,其它可删。需要一个可判断的触发条件,否则会被滥写或跳过
- **Assumptions 章节的粒度上限** — LLM 起草 spec 时容易把所有东西都写成"假设",导致 Assumptions 膨胀到替代 Goal。建议在模板注释里用上限约束(如 "≤5 条,每条 ≤ 1 行")
- **Finalize checkbox 清单应嵌在 spec 模板里,还是保留为 SKILL.md 的外部检查?** 前者让"spec 自检"成为 spec 一部分,后者避免模板再膨胀。倾向嵌在模板末尾的 HTML 注释块里(不进正文,但起草时可见)

## 入库候选

(值得提升为长期 wiki 知识的笔记。用户需显式执行 `wiki ingest` 操作)

- `refined/structural-constraints.md` — **强烈建议**。"如何用 markdown 结构表达约束"是跨项目复用的元知识,下次写任何 skill 模板都用得上。可 ingest 为 `[[concept-structural-constraints]]` 或直接放 root 页 `[[sdd-methodology]]`
- `refined/when-prose-still-wins.md` — **建议**。"哪些规则不能结构化"的 5 类分类和"删不删自然违反"判据是 evergreen 知识。可 ingest 为 `[[concept-prose-vs-structure]]`
- `refined/decision-history-handling.md` — **建议**。spec 是否保留决策过程的哲学对比,这是 sdd-kit 与业界 RFC 文化的根本差异,值得 ingest 为 `[[decision-spec-as-contract-not-process]]`

## 临时性内容(不要入库)

(仅与本次 spec skill 改造相关,无跨项目复用价值)

- `refined/required-fields-matrix.md` — 这份矩阵是**为当前 spec skill 重写定制的**,字段选择带 sdd-kit 特有的权衡(Hard constraints / Integration points)。其它项目用不上

## 未贡献到 refined 的 raw(unused)

- `raw/ext-obra-superpowers-readme.md` — 只提供了"superpowers 没有工程 spec skill"这一背景确认,无直接模板参考价值。保留不删除(审计链)

## 后续步骤(由用户决定,不自动触发)

- **默认路径**:进入 Phase 1,按 findings 驱动重写 `plugins/sdd-kit/skills/spec/assets/templates/spec.md` + 新增 `spec-example.md`
- **可选**:先处理上面的"待解决问题",特别是 BDD 取舍,避免 Phase 1 模板写了一半改方向
- **可选**:用 `wiki` skill ingest 2-3 条"入库候选"(仓库第一次正式用 wiki,顺便吃狗粮)
- **暂缓**:其它 skill(research/task/impl/review/wiki)同类问题本轮不碰

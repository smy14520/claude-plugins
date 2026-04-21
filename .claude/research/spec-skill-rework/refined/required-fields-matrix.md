---
finding-type: landscape
confidence: high
date: 2026-04-21
---

<!-- 输出语言: 中文 -->

# 必需字段矩阵:4 个业界 spec 模板 + sdd-kit 现状

## 发现内容

把 KEP / Rust RFC / SpecKit / sdd-kit 当前 spec 模板的字段展平到一张表,能清晰看出"哪些字段是业界共识的刚需"和"哪些是 sdd-kit 独特选择"。

### 并列矩阵

| 字段 / 章节 | KEP | Rust RFC | SpecKit spec | sdd-kit 现状 |
|------------|:---:|:--------:|:-----------:|:-----------:|
| Title / Feature name | ✓ | ✓ | ✓ | ✓ |
| Status / Metadata | ✓ (Release Signoff Checklist) | - | ✓ (Status/Branch/Created/Input) | ✓ (frontmatter) |
| **Goal / Goals** | ✓ H3 | - (in Motivation) | - (in User Scenarios) | ✓ |
| **Non-Goals** | ✓ H3 | - | - (Out of scope in Assumptions) | ✓ |
| Motivation / Why | ✓ H2 | ✓ H2(核心) | - (Input 字段隐含) | 禁止(决策史禁写) |
| User stories / Scenarios | ✓ (optional) | - | ✓ **mandatory**,带 P1/P2/P3 优先级 | - |
| Acceptance (BDD) | - | - | ✓ Given/When/Then 强制 | 部分(checkbox 列表) |
| **Requirements / Interface** | ✓ (Design Details) | ✓ (Reference-level) | ✓ FR-NNN **mandatory** | ✓ (Interface contract) |
| Hard constraints / SLO | - (分散在 Design Details) | - | - (隐含在 SC-NNN) | ✓ **显式章节** |
| **Data / State design** | ✓ (Design Details) | - | ✓ Key Entities *(conditional)* | ✓ |
| **Integration points** | - | - | - | ✓ **显式章节**(sdd-kit 独有) |
| **Test strategy / plan** | ✓ 四层子标题 | - | - | ✓ (散文) |
| Success criteria | ✓ Graduation Criteria(Alpha/Beta/GA) | - | ✓ SC-NNN **mandatory**,业务指标 | 隐含在 Acceptance |
| Assumptions | - | - | ✓ 独立章节 | ❌ **缺失** |
| Risks and Mitigations | ✓ H3 | - | - | ❌ **缺失** |
| Alternatives considered | ✓ H2(保留) | ✓ Rationale and alternatives(合并) | - | ❌ **禁止**(推 wiki) |
| Unresolved questions | - (隐含) | ✓ **独立章节** | - (隐含在 [NEEDS CLARIFICATION]) | 禁止(Finalize 前必须清空) |
| Prior art | - | ✓ **独立必选** | - | - |
| Drawbacks | ✓ | ✓ | - | - |
| Future possibilities | - | ✓ | - | - |
| Implementation history | ✓ | - | - | - (git 承担) |
| Review & Acceptance Checklist | ✓ (Release Signoff) | - | ✓ (命令级) | 部分(Finalize) |

### 关键观察

**业界 5/5 共识刚需**(所有 5 个模板都有):
- Title
- 某种形式的"该构建什么"描述(可能叫 Requirements / Goals / Reference-level explanation)

**业界 4/5 刚需**(4 个模板都有,缺一个):
- Metadata/Status
- 功能描述性章节

**业界 3/5 共识**(3 个模板有):
- Non-Goals(KEP + sdd-kit,其它用 Assumptions / Out of scope 隐式表达)
- Data / State design
- Test/Acceptance

**sdd-kit 独有的 2 个章节**(其它 4 个模板都没有):
- `Hard constraints` —— 业界都散落在其它章节,sdd-kit 独立章节强调"数值/二元约束"
- `Integration points`(上下游依赖) —— 业界通常混在 Design Details 里

**sdd-kit 相对业界的 2 个缺失**:
- **Assumptions** —— SpecKit 独立章节,业界也常见于工程 spec。LLM 起草 spec 时会有大量静默假设,显式化能防下游踩雷
- **Risks / Mitigations** —— KEP 显式章节。sdd-kit 完全没有

## 来源

- `raw/ext-kubernetes-kep-template.md` 顶层结构段
- `raw/ext-rust-rfc-template.md` 顶层结构段
- `raw/ext-github-speckit-spec-template.md` 全文字段清单
- `plugins/sdd-kit/skills/spec/assets/templates/spec.md` (现有模板)
- `plugins/sdd-kit/skills/spec/references/content-contract.md` (规则声明)

## 意义

### 建议保留的 sdd-kit 独有字段

- **Hard constraints** —— "数值/二元约束"是 sdd-kit 的招牌,应保留且强化
- **Integration points** —— 上下游依赖分离让 spec 更自足,保留

### 建议新增到 sdd-kit 模板

- **Assumptions**(明确静默前提) —— 改造 Phase 1 纳入
- **Risks / Mitigations**(可选章节,默认缺省) —— 改造 Phase 1 纳入,用条件必选

### 建议延续的禁止项

- 不加 Alternatives / Drawbacks / Future possibilities —— 这些是 KEP/RFC 合并"决策过程 + 契约"模式的产物,sdd-kit 拆分模式下它们归 wiki 的 decision 页
- 不加 Prior art —— 那是 research 阶段的职责,与 spec 拆分开

## 待确认问题

- Risks / Mitigations 在 sdd-kit 定位里是工程风险还是产品风险?若是产品风险,和 Non-goals 有重叠
- Assumptions 的粒度如何控?LLM 起草时容易把所有东西都写成"假设",膨胀失控

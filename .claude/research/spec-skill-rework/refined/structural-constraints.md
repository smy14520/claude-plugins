---
finding-type: landscape
confidence: high
date: 2026-04-21
---

<!-- 输出语言: 中文 -->

# 业界 spec 模板"用结构表达约束"的 6 种具体手法

## 发现内容

本次调研的 4 个成熟模板(KEP / Rust RFC / SpecKit spec-template / SpecKit 工作流)共同使用了 6 种"把规则编码到模板结构里"的具体手法,让模板本身承担约束,减少散文规则。

### 手法 1: GFM checkbox 作为门禁清单(KEP 独创)

KEP 在模板**顶部**内嵌 Release Signoff Checklist:

```markdown
- [ ] (R) Enhancement issue in release milestone
- [ ] (R) KEP approvers have approved the KEP status as `implementable`
- [ ] (R) Design details are appropriately documented
- [ ] (R) Test plan is in place, giving consideration to SIG Architecture...
  - [ ] e2e Tests for all Beta API Operations (endpoints)
  - [ ] (R) Ensure GA e2e tests meet requirements for Conformance Tests
```

`(R)` 前缀 = 必填项。嵌套 checkbox 表达条件依赖。这比"测试计划必须包含 e2e、conformance、稳定窗口"的散文规则有三重优势:可勾选(作者必须主动 engage)、可 grep(未勾选可机器识别)、视觉上立刻可见漏项。

### 手法 2: H2 标题里直接标注 `*(mandatory)*` 标签(SpecKit 独创)

```markdown
## User Scenarios & Testing *(mandatory)*
## Requirements *(mandatory)*
## Success Criteria *(mandatory)*
## Assumptions                                 <!-- 无 mandatory = 可选 -->

### Key Entities *(include if feature involves data)*   <!-- 条件必选 -->
```

必选/可选/条件三态写在标题上,一眼可见。无需到 SKILL.md / content-contract.md 里反复散文声明"哪些章节必须有"。

### 手法 3: 稳定 ID + RFC 2119 固定动词短语(SpecKit)

```markdown
- **FR-001**: System MUST [specific capability, ...]
- **FR-002**: System MUST [specific capability, ...]
- **FR-003**: Users MUST be able to [key interaction, ...]
```

两层结构强制:
- `FR-NNN` 稳定 ID → 跨文档引用稳定,插入不重编号
- `System MUST ...` / `Users MUST be able to ...` 固定起手词 → 契约性一眼可见,非契约语句(如"should be fast")结构上写不出来

### 手法 4: BDD 语法强制 acceptance 结构化(SpecKit)

```markdown
**Acceptance Scenarios**:

1. **Given** [initial state], **When** [action], **Then** [expected outcome]
2. **Given** [initial state], **When** [action], **Then** [expected outcome]
```

验收标准不是自由散文,而是 Given/When/Then 三段式。初始状态 / 触发动作 / 预期结果三位一体。漏任何一段结构上就不完整。

### 手法 5: 子标题拆分测试/数据/接口类别(KEP / SpecKit 共用)

KEP Test Plan:
```
##### Prerequisite testing updates
##### Unit tests
##### Integration tests
##### e2e tests
```

SpecKit Requirements:
```
### Functional Requirements
### Key Entities *(include if feature involves data)*
```

把"该覆盖哪些测试/数据层次"从散文("测试策略必须覆盖单测、集成、e2e")下沉到**标题结构**本身。漏一层 = 标题缺失 = 可 grep / 可肉眼检。

### 手法 6: 条件必选标签(SpecKit)

```markdown
### Key Entities *(include if feature involves data)*
```

不是二元的必选/可选,而是**"某情况下必选"**。条件写在标签里,不用另起一段"如果功能涉及数据,则本节为必选"的散文。

## 来源

- `raw/ext-kubernetes-kep-template.md` 第 20-50 行(Release Signoff Checklist)
- `raw/ext-kubernetes-kep-template.md` 第 83-100 行(Test Plan 子标题)
- `raw/ext-github-speckit-spec-template.md` 第 17-32 行(mandatory 标签结构)
- `raw/ext-github-speckit-spec-template.md` 第 60-86 行(FR-NNN / MUST / Given-When-Then)

## 意义

这 6 种手法中,sdd-kit **当前 spec skill 只用了其中 1 种(子标题拆分)**,且应用程度浅。具体改造对照:

| 手法 | sdd-kit 现状 | 改造潜力 |
|------|-------------|---------|
| GFM checkbox 门禁 | 仅用于 Acceptance 列表 | 扩展到 "Finalize 前置检查"(定稿自检清单) |
| `*(mandatory)*` 标签 | 无(靠 content-contract.md 散文声明) | **高价值** 直接搬 |
| 稳定 ID (FR-NNN / SC-NNN) | task 有 `T-NNN`,spec 无 | **高价值** spec 的验收项应有稳定 ID |
| Given/When/Then | 无(自由散文列 acceptance) | 中价值,对工程 spec 可能过度形式化 |
| 子标题拆分测试类别 | Test strategy 散文列表 | 中价值,拆 unit/integration/e2e 子标题 |
| 条件必选标签 | 无 | 中价值,如 "Data design *(include if 功能涉及持久化)*" |

重点下沉候选:mandatory 标签、稳定 ID、checkbox 定稿清单。

## 待确认问题

- Given/When/Then 是否适合**工程向** spec?(SpecKit 偏产品视角,sdd-kit 偏接口契约) —— 下一阶段(spec 改造)决定
- checkbox 定稿清单是嵌在 spec 模板里,还是保留为 SKILL.md 的 Finalize 检查脚本?取决于"定稿是一次性事件还是可迭代"

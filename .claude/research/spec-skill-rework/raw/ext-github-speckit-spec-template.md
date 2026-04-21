---
url: https://raw.githubusercontent.com/github/spec-kit/main/templates/spec-template.md
tool: read_url_content
fetched_at: 2026-04-21 21:31
---

# GitHub SpecKit 的 spec-template.md(完整清洗)

> 来自 `github/spec-kit`,GitHub 官方的 AI-native spec-driven development 模板。这是本次研究里**最接近 sdd-kit 定位的模板**(AI agent 驱动、结构化、mandatory 标签)。

---

## 文件头(frontmatter 等价信息,用正文键值对)

```markdown
# Feature Specification: [FEATURE NAME]

**Feature Branch**: `[###-feature-name]`
**Created**: [DATE]
**Status**: Draft
**Input**: User description: "$ARGUMENTS"
```

**观察**:
- 不用 YAML frontmatter,用**粗体键名 + 行内值**
- 强制 4 个元字段: branch / 创建日期 / status / input(原始用户输入)
- `Input` 记录原始用户需求 —— 便于后续 review 时对照"最初要求"

## 顶层结构(H2 依序,带 `*(mandatory)*` 标签)

```
## User Scenarios & Testing *(mandatory)*
  ### User Story 1 - [Brief Title] (Priority: P1)
  ### User Story 2 - [Brief Title] (Priority: P2)
  ### User Story 3 - [Brief Title] (Priority: P3)
  ### Edge Cases
## Requirements *(mandatory)*
  ### Functional Requirements
  ### Key Entities *(include if feature involves data)*
## Success Criteria *(mandatory)*
  ### Measurable Outcomes
## Assumptions
```

**关键观察**:
- **`*(mandatory)*` 直接写在 H2 标题里** —— 必选/可选一眼可见,无需读散文规则
- **`*(include if feature involves data)*`** —— 条件性必选的结构化标记

## User Scenarios & Testing(强制结构)

### 注释指引(原文)

```markdown
<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable MVP (Minimum Viable Product) that delivers value.

  Assign priorities (P1, P2, P3, etc.) to each story, where P1 is the most critical.
  Think of each story as a standalone slice of functionality that can be:
  - Developed independently
  - Tested independently
  - Deployed independently
  - Demonstrated to users independently
-->
```

**约束要点**:用户故事必须 (a) 有优先级 (b) 独立可测 (c) 各自是独立 MVP。

### User Story 模板结构

```markdown
### User Story 1 - [Brief Title] (Priority: P1)
[Describe this user journey in plain language]

**Why this priority**: [Explain the value and why it has this priority level]

**Independent Test**: [Describe how this can be tested independently -
e.g., "Can be fully tested by [specific action] and delivers [specific value]"]

**Acceptance Scenarios**:

1. **Given** [initial state], **When** [action], **Then** [expected outcome]
2. **Given** [initial state], **When** [action], **Then** [expected outcome]

---
```

**关键观察**:
- 每个 story 有**四个固定子字段**: 正文描述 / Why this priority / Independent Test / Acceptance Scenarios
- **Acceptance Scenarios 强制 Given/When/Then(BDD 语法)** —— 把验收标准结构化到语法层面
- `---` 分隔线在模板里预设 —— 视觉分隔两个 story

### Edge Cases

```markdown
### Edge Cases
<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right edge cases.
-->

- What happens when [boundary condition]?
- How does system handle [error scenario]?
```

**观察**:Edge Cases 作为独立 H3,预留 2 个问题形式的占位符。

## Requirements *(mandatory)*

### Functional Requirements(FR-NNN 编号)

```markdown
### Functional Requirements
- **FR-001**: System MUST [specific capability, e.g., "allow users to create accounts"]
- **FR-002**: System MUST [specific capability, e.g., "validate email addresses"]
- **FR-003**: Users MUST be able to [key interaction, e.g., "reset their password"]
- **FR-004**: System MUST [data requirement, e.g., "persist user preferences"]
- **FR-005**: System MUST [behavior, e.g., "log all security events"]

*Example of marking unclear requirements:*

- **FR-006**: System MUST authenticate users via [NEEDS CLARIFICATION: auth method
  not specified - email/password, SSO, OAuth?]
- **FR-007**: System MUST retain user data for [NEEDS CLARIFICATION: retention period not specified]
```

**关键观察**:
- **稳定 ID `FR-NNN`** —— 和 sdd-kit 的 `T-NNN` 思路一致,但用在 spec 层
- **RFC 2119 风格**: `System MUST ...` / `Users MUST be able to ...` —— 固定动词短语让契约性一目了然
- **`[NEEDS CLARIFICATION: ...]` 标记** —— 等价于 sdd-kit 的 `<TODO-DECIDE>`,但更口语化
- **预填 FR-001 到 FR-005 占位符** —— 结构上"默认至少 5 条"

### Key Entities

```markdown
### Key Entities *(include if feature involves data)*
- **[Entity 1]**: [What it represents, key attributes without implementation]
- **[Entity 2]**: [What it represents, relationships to other entities]
```

**观察**:条件必选("if feature involves data")。Entity 描述强调 "without implementation" —— 不写 DDL。

## Success Criteria *(mandatory)*

### Measurable Outcomes(SC-NNN 编号)

```markdown
### Measurable Outcomes
- **SC-001**: [Measurable metric, e.g., "Users can complete account creation in under 2 minutes"]
- **SC-002**: [Measurable metric, e.g., "System handles 1000 concurrent users without degradation"]
- **SC-003**: [User satisfaction metric, e.g., "90% of users successfully complete primary task on first attempt"]
- **SC-004**: [Business metric, e.g., "Reduce support tickets related to [X] by 50%"]
```

**注释指引**:
```
ACTION REQUIRED: Define measurable success criteria.
These must be technology-agnostic and measurable.
```

**关键观察**:
- **稳定 ID `SC-NNN`** + **`[X-something]` 示例类型提示**(metric / satisfaction metric / business metric)
- **"technology-agnostic and measurable"** 双重强制
- sdd-kit 的"Acceptance"和 SpecKit 的"Success Criteria"在定位上相似,但 SpecKit 用**可度量的业务指标**,sdd-kit 用**可执行的验收命令**。前者偏产品/用户,后者偏工程/代码。

## Assumptions

```markdown
## Assumptions
<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right assumptions based on reasonable defaults
  chosen when the feature description did not specify certain details.
-->

- [Assumption about target users, e.g., "Users have stable internet connectivity"]
- [Assumption about scope boundaries, e.g., "Mobile support is out of scope for v1"]
- [Assumption about data/environment, e.g., "Existing authentication system will be reused"]
- [Dependency on existing system/service, e.g., "Requires access to the existing user profile API"]
```

**观察**:**Assumptions 是独立章节** —— 显式列出"基于什么默认假设做的决策"。这一节 sdd-kit 完全缺失,但它在大型 LLM 起草 spec 时很关键 —— 模型会做各种静默假设,显式化能防止下游踩雷。

## 模板整体风格

- **Mandatory/Optional/Conditional 三态** 用标签显示在 H2 标题里: `*(mandatory)*` / `*(include if ...)*` / 无标签 = 可选
- **稳定 ID**(FR-NNN / SC-NNN)全面使用
- **RFC 2119 关键字**(MUST / SHOULD)强化契约
- **[NEEDS CLARIFICATION: ...]** 作为未决标记
- **HTML comment 承载"填写指南"**(不是规则,是操作说明)
- **无 frontmatter**,元信息用粗体键值对
- **预填占位符均带类型提示**(如 `[Measurable metric, e.g., "..."]` 指明该处填数值 metric 还是业务 metric)

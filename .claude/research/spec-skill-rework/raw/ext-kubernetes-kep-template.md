---
url: https://raw.githubusercontent.com/kubernetes/enhancements/master/keps/NNNN-kep-template/README.md
tool: read_url_content
fetched_at: 2026-04-21 21:30
---

# Kubernetes KEP 模板(清洗摘要)

> 原文为 Kubernetes Enhancement Proposal 的标准模板。下文保留**所有章节结构**与**关键 HTML 注释指引**(因为注释本身就是"这个字段该写什么"的约束),裁去冗长解释性段落。

---

## 顶层结构(H2 依序)

```
# KEP-NNNN: Your short, descriptive title

## Release Signoff Checklist
## Summary
## Motivation
  ### Goals
  ### Non-Goals
## Proposal
  ### User Stories (Optional)
  ### Notes/Constraints/Caveats (Optional)
  ### Risks and Mitigations
## Design Details
  ### Test Plan
  ### Graduation Criteria
  ### Upgrade / Downgrade Strategy
  ### Version Skew Strategy
## Production Readiness Review Questionnaire
  ### Feature Enablement and Rollback
  ### Rollout, Upgrade and Rollback Planning
  ### Monitoring Requirements
  ### Dependencies
  ### Scalability
  ### Troubleshooting
## Implementation History
## Drawbacks
## Alternatives
## Infrastructure Needed (Optional)
```

## Release Signoff Checklist(原文关键段)

> Items marked with (R) are required prior to targeting to a milestone / release.

```
- [ ] (R) Enhancement issue in release milestone, which links to KEP dir in [kubernetes/enhancements]
- [ ] (R) KEP approvers have approved the KEP status as `implementable`
- [ ] (R) Design details are appropriately documented
- [ ] (R) Test plan is in place
  - [ ] e2e Tests for all Beta API Operations (endpoints)
  - [ ] (R) Ensure GA e2e tests meet requirements for Conformance Tests
  - [ ] (R) Minimum Two Week Window for GA e2e tests to prove flake free
- [ ] (R) Graduation criteria is in place
  - [ ] (R) [all GA Endpoints] must be hit by Conformance Tests within one minor version of promotion to GA
- [ ] (R) Production readiness review completed
- [ ] (R) Production readiness review approved
- [ ] "Implementation History" section is up-to-date for milestone
- [ ] User-facing documentation has been created in [kubernetes/website]
- [ ] Supporting documentation—e.g., additional design documents...
```

**观察**:门禁清单用 GFM checkbox 直接内嵌在模板顶部。`(R)` 前缀标必填项。嵌套 checkbox 表达条件依赖("测试计划需包含 e2e、GA conformance、2 周 flake-free 窗口")。

## Goals / Non-Goals(原文注释指引)

```markdown
### Goals
<!--
List the specific goals of the KEP. What is it trying to achieve? How will we
know that this has succeeded?
-->

### Non-Goals
<!--
What is out of scope for this KEP? Listing non-goals helps to focus discussion
and make progress.
-->
```

**观察**:两者都是**必选 H3**,注释只说"该填什么",不规定数量。模板靠结构强制存在,靠注释指示填法。

## Proposal / Risks and Mitigations

```markdown
### User Stories (Optional)
#### Story 1 (Optional)
#### Story 2 (Optional)

### Notes/Constraints/Caveats (Optional)
<!-- core concepts and how they relate -->

### Risks and Mitigations
<!--
What are the risks of this proposal, and how do we mitigate?
How will security be reviewed, and by whom?
How will UX be reviewed, and by whom?
-->
```

**观察**:User Stories 是可选但**结构预留好了** —— 写的时候不需要自己想"这里该放 Story 1/Story 2 还是 Use Case"。

## Design Details / Test Plan(必填 checkbox)

```markdown
[ ] I/we understand the owners of the involved components may require updates to
existing tests to make this code solid enough prior to committing the changes...

##### Prerequisite testing updates
##### Unit tests
##### Integration tests
##### e2e tests
```

**观察**:Test Plan 拆成 4 个 H5 子段(Prerequisite / Unit / Integration / e2e),每个独立展开。这种"测试类别 = 子标题"的做法把"测试策略必须覆盖哪些层次"变成**模板结构本身**。

单独的 `[ ] I/we understand ...` 放在节首 —— 声明性 checkbox,作者必须主动勾选。

## Graduation Criteria(分阶段门禁)

```markdown
#### Alpha
- Feature implemented behind a feature flag
- Initial e2e tests completed and enabled

#### Beta
- Gather feedback from developers and surveys
- Complete features A, B, C
- Additional tests are in Testgrid and linked in KEP
- More rigorous forms of testing—e.g., downgrade tests and scalability tests
- All functionality completed
- All security enforcement completed
- All monitoring requirements completed
- All testing requirements completed
- All known pre-release issues and gaps resolved

**Note:** Beta criteria must include all functional, security, monitoring,
and testing requirements along with resolving all issues and gaps identified

#### GA
- N examples of real-world usage
- N installs
- Allowing time for feedback
- All issues and gaps identified as feedback during beta are resolved

**Note:** GA criteria must not include any functional, security, monitoring,
or testing requirements. Those must be beta requirements.
```

**观察**:用 H4 把"Alpha / Beta / GA"切分三层门禁。每层门禁以 `-` 列表写法展开。Note 块强制"GA 不可残留 Beta 遗留物"之类的**跨阶段规则**。这是把"状态机规则"用 Markdown 结构表达的典范。

## Alternatives / Drawbacks / Implementation History

```markdown
## Implementation History
<!--
- the `Summary` and `Motivation` sections being merged, signaling SIG acceptance
- the `Proposal` section being merged, signaling agreement on a proposed design
- the date implementation started
- the first Kubernetes release where an initial version of the KEP was available
- the version of Kubernetes where the KEP graduated to general availability
- when the KEP was retired or superseded
-->

## Drawbacks
<!-- Why should this KEP _not_ be implemented? -->

## Alternatives
<!--
What other approaches did you consider, and why did you rule them out?
These do not need to be as detailed as the proposal, but should include enough
information to express the idea and why it was not acceptable.
-->
```

**观察**:KEP **明确保留 Alternatives 章节**。这和 sdd-kit 的"禁止 Alternatives"是**不同哲学**:KEP 合并 "决策过程 + 最终契约",sdd-kit 拆分(决策史 → wiki,spec 只写结论)。两种选择各有合理性。

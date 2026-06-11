# sdd-next 设计草案

> 目标：在 `sdd-kit` 旁边重新开一个更轻、更清晰的新实现。保留 PRD-first、行为切片、证据化执行、显式 wiki 的精华，去掉历史遗留、多状态、多命令、阶段耦合和执行层噪音。

本文是新目录的规划草案，不是最终实现。当前建议新目录名暂定为 `plugins/sdd-next/`，后续可以改名为 `sdd-flow`、`sdd-lite` 或继续叫 `sdd-kit` 的下一代版本。

---

## 1. 为什么要重做

旧 `sdd-kit` 的核心思想是对的：

- 需求先收敛成 PRD，而不是直接写代码。
- PRD 里用 slice 表达可验证的行为 checkpoint。
- helper 负责机械状态，AI 负责语义判断。
- wiki 只是项目导航和经验层，不是代码事实源。

但多次迭代之后，旧实现出现了这些问题：

- README、真实实现、历史验证文档互相不一致。
- `.claude`、`.arbor`、`.wiki` 等历史数据模型混杂在文档和代码里。
- 状态机和命令数量偏多，AI 容易陷入“下一步该调哪个命令”的选择困难。
- 阶段之间存在过多隐式关联，research / brainstorm / wiki 可能污染彼此上下文。
- impl 阶段的状态记录过细，反而让人不容易看懂真实进度。
- 执行层既想控制 agent，又想记录一切，导致复杂度上涨。

新版本的目标不是继续修补旧状态机，而是重新做一版：

```text
少命令
少状态
显式触发
artifact-first
代码即进度
PRD 即边界
review 主动触发
wiki 主动触发
helper 只做机械事
```

---

## 2. 新版本核心原则

### 2.1 阶段显式，不自动串联

四个核心阶段彼此独立，由用户主动触发：

```text
research   外部资料与资料包
brainstorm 需求访谈与 PRD 收敛
impl       按 PRD 执行代码
review     主动审计 PRD + diff + evidence
wiki       主动沉淀项目长期知识
```

不做这些隐式行为：

- brainstorm 不自动搜索 research。
- brainstorm 不自动读 wiki，除非用户明确要求或在当前对话中指定。
- impl 不自动 publish wiki。
- review 不自动修代码。
- wiki 不自动摄入每次实现结果。

### 2.2 资料、需求、代码、知识分层

```text
.sdd/research/  临时/半临时外部资料工作区
.sdd/packages/  当前 SDD package 的 PRD、执行记录、review 记录
.wiki/          长期项目知识和导航层
code            最终实现事实源
```

建议不要继续把 workflow 主状态放在 `.claude/` 下。`.claude/` 保留给 Claude Code 项目规则、agents、commands、settings 等 runtime 配置。业务工作流状态放到 `.sdd/`。

### 2.3 代码即进度，状态只记录断点

Impl 阶段不要维护一套复杂执行计划。真实进度来自：

- git diff
- 测试结果
- 已完成的文件变更
- PRD slice 的最小断点记录

状态文件只回答两个问题：

```text
1. 这个 package 当前停在哪个 slice？
2. 上一次执行为什么停下？
```

### 2.4 状态机极简

新版本只保留 package 级 4 态：

```text
brainstorming → ready → implementing → reviewed
```

其中 `implementing` 不细分 blocked / needs_context / done_with_concerns 等生命周期状态。这些作为 event/result 记录，不作为顶层状态。

建议的 result 类型：

```text
impl_result:
  - completed
  - needs_decision
  - blocked
  - stopped

review_result:
  - approved
  - needs_rework
  - prd_drift
```

这样用户不需要理解一堆状态迁移。状态只服务断点续作。

---

## 3. 新目录建议

```text
plugins/sdd-next/
├── .claude-plugin/
│   └── plugin.json
├── skills/
│   ├── research/
│   │   ├── SKILL.md
│   │   └── references/
│   ├── brainstorm/
│   │   ├── SKILL.md
│   │   ├── templates/
│   │   │   ├── prd.md
│   │   │   └── slice.md
│   │   └── references/
│   ├── impl/
│   │   ├── SKILL.md
│   │   └── references/
│   ├── review/
│   │   ├── SKILL.md
│   │   └── references/
│   └── wiki/
│       ├── SKILL.md
│       └── references/
├── bin/
│   └── sdd
├── tools/
│   └── sdd_cli.py
├── docs/
│   ├── PRINCIPLES.md
│   ├── DATA_MODEL.md
│   ├── EXAMPLES.md
│   └── MIGRATION-FROM-SDD-KIT.md
└── README.md
```

命令层先不要做很多 slash commands。优先做 skill-first：

```text
用 research skill 调研 <topic>
用 brainstorm skill 收敛 <idea/package>
用 impl skill 执行 <package>
用 review skill 审计 <package>
用 wiki skill 记录/查询/更新 <knowledge>
```

如果后续确实需要 slash command，最多只暴露 5 个：

```text
/sdd:research
/sdd:brainstorm
/sdd:impl
/sdd:review
/sdd:wiki
```

不要暴露底层 helper 命令给用户作为日常入口。

---

## 4. 阶段职责

## 4.1 Research：外部资料收集与资料包

Research 的职责不是做方案，不是写 PRD，也不是自动进入 brainstorm。

它的职责是：

> 围绕一个需求或方向，收集足够多的外部资料、竞品信息、API 文档、字段结构、流程材料，并整理成 AI 后续可读、可引用、可追溯的资料包。

典型场景：

1. 做一个全新的电脑测评网站：
   - 调研竞品网站。
   - 总结竞品做得好的点。
   - 收集测评数据来源。
   - 整理可抓取字段、评分维度、内容结构。
   - 输出资料包，而不是最终产品方案。

2. 给已有项目接入小红书 AI 客服：
   - 收集小红书客服 / 开放平台相关 API。
   - 整理认证、消息流、回调、限制、错误码。
   - 标出哪些资料已确认，哪些需要登录或人工确认。
   - 输出给 brainstorm 使用的资料包。

Research 产物建议放在：

```text
.sdd/research/<topic>/
├── index.md      # 当前资料包入口
├── sources/      # 原文摘录，带来源
├── notes/        # 主题化整理
└── summary.md    # 给 brainstorm 的压缩摘要
```

Research hard rules：

- 用户给的 URL 必须尝试获取；获取失败要记录失败原因。
- `sources/` 只放带来源的事实，不偷渡方案决策。
- `notes/` 可以解释“这对需求意味着什么”，但不做最终产品取舍。
- `summary.md` 是给 brainstorm 的阅读入口，不是 PRD。
- 不自动写 wiki。
- 不自动进入 brainstorm。

Research 最小状态：

```yaml
status: open | ready | closed
```

`ready` 只表示资料足够交给 brainstorm，不表示需求已明确。

---

## 4.2 Brainstorm：需求收敛与 PRD 生成

Brainstorm 的职责是把想法变成可执行 PRD。

它可以读取：

- 用户当前想法。
- 当前代码。
- 用户明确指定的 research package。
- 用户明确指定的 wiki 页面。

它不应该默认读取所有 research，也不应该默认检索 wiki。

典型场景：

1. 从 0 开始做 Steam 游戏：
   - 访谈玩法核心。
   - 确认单机/联机。
   - 确认 2D/3D。
   - 确认技术栈。
   - 确认核心循环、胜负条件、内容范围。
   - 输出可执行 PRD。

2. 既有项目接入 AI 客服：
   - 先读当前项目客服/消息/AI 相关代码。
   - 必要时读用户指定的 wiki 链路。
   - 结合小红书 API research 包。
   - 追问接入边界、权限、消息流、异常处理、验收方式。
   - 输出可执行 PRD。

Brainstorm hard rules：

- 一次只问一个最高价值问题。
- 能从代码读出来的，不问用户。
- 用户做离散取舍时，用 2-4 个选项，说明技术后果。
- 不自动读取 research/wiki，除非用户明确指定。
- PRD 必须自包含；即使 wiki/research 不存在，impl 也知道核心 scope。
- PRD 中可以引用 research/wiki，但只能作为背景或防漏辅助。
- 最终 PRD 需要用户确认后才标记 ready。

PRD 建议结构：

```markdown
# <package title>

## Background
## Goal
## Non-goals
## User / System Scenarios
## Decisions
## Technical Framing
## Acceptance
## Slices
## Risks / Open Questions
## Sources
```

Slice 不应该是技术层任务，而应该是行为 checkpoint：

```markdown
### S-001: 用户能完成小红书授权并保存店铺绑定
- Completion: 授权回调成功后，系统保存店铺身份，并能在后台看到绑定状态
- Verification: 通过 mock callback 或沙盒回调验证绑定状态落库
```

---

## 4.3 Impl：执行 PRD，少状态，可断点续作

Impl 是执行阶段。它的职责是按照 PRD scope 改代码、跑验证、留下最小断点记录。

不需要复杂状态机。不要让 AI 维护第二套计划。PRD 中的 Slices 是执行顺序，代码 diff 是真实进度。

Impl 可以主动使用 Claude Code 的 workflow / subagents / worktrees / agent team 来加速，但这是执行策略，不写进核心状态机。

Impl hard rules：

- 先读 PRD，再读当前代码。
- 按 Slices 顺序推进，但允许在一个 session 中连续完成多个 slice。
- 不在每个 slice 之间等待用户确认。
- 不修改 PRD 来迎合实现。
- 遇到承重需求不清，停下请求决策。
- 每次停止时只写一个 `progress.md` 摘要。
- 不创建一堆中间状态文件。

建议产物：

```text
.sdd/packages/<package>/
├── prd.md
├── progress.md
├── evidence.md
└── review.md        # 只有 review 阶段写
```

`progress.md` 只回答：

```markdown
# Progress

Current slice: S-003
Status: active | stopped | completed
Last stop reason: <一句话>

## Done
- S-001: <代码/测试证据>
- S-002: <代码/测试证据>

## Next
- S-003: <下一步最小动作>

## Notes
- <只记录会影响断点续作的信息>
```

`evidence.md` 记录验证：

```markdown
# Evidence

## Checks
- [passed] npm test — <摘要>
- [passed] npm run build — <摘要>
- [manual] 小红书回调 mock — <摘要>

## Acceptance mapping
- S-001 → <文件/测试/行为证据>
- S-002 → <文件/测试/行为证据>
```

提高 impl 质量的重点不是更多状态，而是更强的完成标准。

建议 impl 的 DONE 标准：

```text
1. 每个 slice 都有可观察行为证据。
2. 每条 Acceptance 都能映射到代码、测试或手动验证证据。
3. 至少有一个项目级验证命令被运行，或明确说明为什么不能运行。
4. 新增代码必须接入真实调用链，不能 dead file。
5. 不允许用 fake / in-memory / stub 顶替 PRD 承诺的真实能力，除非 PRD 明确允许。
6. 负向路径如果写进 PRD，就必须有验证。
```

建议给 impl 一个 lightweight self-audit checklist，而不是复杂 helper 强制所有事情。

---

## 4.4 Review：主动审计，不自动修复

Review 是用户主动触发的语义审计。

它可以用 agent team 从多个角度审：

- PRD scope 对账
- diff 对账
- 测试质量
- 安全/权限
- 边界/异常
- dead file / fake implementation

Review 不自动修代码。它输出 verdict 和 rework list。

建议 verdict 简化为：

```text
approved
needs_rework
prd_drift
```

Review hard rules：

- 必须读 PRD。
- 必须读 diff。
- 必须读 evidence。
- 必须逐条对账 Acceptance。
- 不能只说 LGTM。
- 发现 PRD 本身错了，判 `prd_drift`，回 brainstorm。
- 发现实现没满足 PRD，判 `needs_rework`，回 impl。

Review 报告模板：

```markdown
# Review

Verdict: approved | needs_rework | prd_drift

## Acceptance audit
| Item | Evidence | Gap |
|---|---|---|

## Diff audit
## Test audit
## Risk audit
## Required rework
```

---

## 4.5 Wiki：主动沉淀、灵活结构、随项目成长

Wiki 是长期项目知识层，不是 workflow 中间态。

它承载的是：

- 重要链路。
- 跨文件修改规则。
- 模块契约。
- 项目坑点。
- 外部资料中长期有价值的部分。
- 架构决策。
- 领域概念。

典型例子：

1. Research 发现某些资料长期有用：
   - 小红书客服 webhook 签名规则。
   - 小红书消息类型表。
   - 测评数据来源字段说明。
   用户主动要求 wiki 收录后，写入 `.wiki/`。

2. 项目中“新增导出”需要改 4-5 个文件：
   - enum 文件。
   - API 注册。
   - UI 下拉选项。
   - 权限映射。
   - 测试 fixture。
   写成 flow note，后续用户提醒 AI 去看即可。

Wiki hard rules：

- 只有用户显式触发才写 wiki。
- wiki 不是 source of truth；改代码前仍要验证当前代码。
- wiki 结构要灵活，适配 web / game / app / tool / library 等不同项目。
- 页面不要机械转录代码；记录跨文件才能重建的信息。
- 页面要可更新，有 stale / deprecated / superseded 表达。

建议 wiki 页面类型保持少量核心类型：

```text
module      模块说明
flow        长链路 / 跨文件流程
gotcha      坑点
decision    决策
source      外部资料摘要
concept     领域概念
```

比旧版更灵活，不强制所有项目都按固定目录。

---

## 5. Helper 设计：只做机械动作

新 helper 暂定命令：`sdd`。

先只保留少量子命令：

```text
sdd init
sdd list
sdd show <package>
sdd create <package>
sdd ready <package>
sdd progress <package>
sdd evidence <package>
sdd validate <package>
sdd wiki-index
sdd wiki-search <query>
```

不要把每个状态迁移都变成一个命令。helper 只做：

- 创建目录。
- 校验结构。
- 展示当前状态。
- 写入 progress/evidence 的安全格式。
- 检索 wiki。

不要让 helper 判断需求范围，不要让 helper 替代 review verdict。

---

## 6. 新数据模型草案

```text
.sdd/
├── research/
│   └── <topic>/
│       ├── index.md
│       ├── summary.md
│       ├── sources/
│       └── notes/
└── packages/
    └── <package>/
        ├── prd.md
        ├── progress.md
        ├── evidence.md
        └── review.md
```

Package metadata 可以先放在每个 markdown frontmatter 里，避免 `task.json` 复杂化。

`prd.md` frontmatter：

```yaml
---
package: xhs-ai-customer-service
status: draft | ready
created: YYYY-MM-DD
research:
  - .sdd/research/xhs-customer-service/summary.md
wiki:
  - .wiki/Flows/客服消息链路.md
---
```

`progress.md` frontmatter：

```yaml
---
package: xhs-ai-customer-service
status: not_started | active | stopped | completed
current_slice: S-003
updated: YYYY-MM-DD
---
```

`evidence.md` frontmatter：

```yaml
---
package: xhs-ai-customer-service
updated: YYYY-MM-DD
---
```

`review.md` frontmatter：

```yaml
---
package: xhs-ai-customer-service
verdict: approved | needs_rework | prd_drift | none
updated: YYYY-MM-DD
---
```

---

## 7. 从旧 sdd-kit 继承什么

应该继承：

- PRD-first。
- Technical Framing。
- 行为级 Slices。
- PRD 是 impl/review 的边界。
- review 不是 LGTM，而是 PRD + diff + evidence 对账。
- wiki 是 orientation，不是 source of truth。
- helper 只做机械动作。
- 用户显式确认后才 finalize。

应该去掉或弱化：

- 过多 lifecycle 状态。
- `task.json` 过度复杂字段。
- 一堆底层状态命令。
- 自动阶段串联。
- 自动 wiki ingest。
- research / wiki 默认注入 brainstorm。
- 每个 slice 都重状态化。
- 过度严格的 helper gate 导致小需求成本太高。

---

## 8. 与市面工作流思想的关系

吸收：

- Spec-driven development：spec/PRD 是中心 artifact，不是 disposable prompt。
- Superpowers / Skills 思路：把阶段方法论封装为 skill，而不是让用户背 prompt。
- Claude Code subagents 思路：探索、review、并行审计可以放到独立上下文，但主流程不依赖自动 subagent。
- 12-factor agents 思路：控制上下文、结构化输出、人类审批、状态外置。
- Agent 安全研究里的 scope control：impl 必须受 PRD scope 约束，防止 overeager actions。

拒绝：

- 大而全命令面板。
- 自动把所有上下文塞进 prompt。
- 一上来就多 agent orchestration。
- 状态机模拟项目管理软件。
- 把 wiki 当长期记忆垃圾桶。

---

## 9. 首版实现范围建议

第一版只做 5 个 skills + 1 个 helper：

```text
research
brainstorm
impl
review
wiki
sdd helper
```

第一版不做：

- OpenCode parity。
- GitHub issue/PR 自动化。
- 多 agent team 自动调度。
- 复杂 hook。
- parent/child package。
- 自动 wiki publish。
- 自动 research lookup。

首版验收：

1. 能用 research 为“电脑测评网站”生成资料包。
2. 能用 brainstorm 从“Steam 游戏想法”生成 PRD。
3. 能用 brainstorm 在已有项目中结合代码生成“小红书 AI 客服接入”PRD。
4. 能用 impl 按 PRD 执行并留下清晰 progress/evidence。
5. 能用 review 审计 diff 并指出偷懒、fake、dead file、验收缺口。
6. 能用 wiki 主动记录“新增导出要改哪几处”这种 cross-file flow。

---

## 10. 最重要的一句话

新版本不要追求“让 AI 全自动管理整个开发流程”。

新版本应该追求：

> 用户掌握阶段切换，PRD 掌握需求边界，代码体现真实进度，evidence 约束完成质量，wiki 承载长期项目经验。

这就是 sdd-next 和旧 sdd-kit 最大的区别。

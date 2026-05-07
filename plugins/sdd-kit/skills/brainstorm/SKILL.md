---
name: brainstorm
description: "把模糊需求持续沉淀到 sdd-kit package PRD draft,断点续作访谈,最终收敛成 PRD-first package。支持 normal 和 grill-me;不要用于 research、impl 或 review。"
---

# Brainstorm — durable PRD-first package

使用语言:中文。

Arbor helper 入口、路径和命令见 [`../references/arbor-helper.md`](../references/arbor-helper.md);运行前遵守其中约定。

Brainstorm 把需求变成可执行 package PRD:创建或定位 `.arbor/tasks/<package>/prd.md` draft → 把每轮访谈结果写进 PRD → 需求、technical framing、验收和边界足够清楚后通过 `sdd-arbor finalize-brainstorm` 写入 ready package。不写代码、不 review、不维护第二套执行计划。

## 模式

- `normal`:高效收敛。Pacing 和 turn shape 见 [`references/normal.md`](references/normal.md)。
- `grill-me`:高强度需求追问。Pacing 和 turn shape 见 [`references/grill-me.md`](references/grill-me.md)。

模式选择规则:

1. 用户显式指定 `normal` / `grill-me` / 直接定稿 / 不追问时,遵从用户。
2. 用户没指定模式且需求模糊、产品 / 系统 / 方案型、存在多个合理方向 / 关键取舍 / 验收不明时,必须用 `AskUserQuestion` 询问 normal / grill-me。
3. Research 之后进入 brainstorm 也必须 `AskUserQuestion`,除非用户明确要求直接定稿;research 是上下文，不是需求冻结。
4. 只有需求已包含目标、范围、关键场景、验收、非目标和技术边界,且用户明显期待推进时,才可默认 normal。

`AskUserQuestion` 选项固定为:

- `grill-me`:产品 / 系统 / 商业模式不清时默认推荐;研究中仍有 open questions、关键 assumptions、多个可行方向时也默认推荐。
- `normal`:需求基本清楚时推荐。

## Package naming

用户显式给名时优先使用。否则用 `MM-DD-<topic-slug>`(lowercase kebab-case,避免中文 / 空格 / 路径分隔符);例:"知识付费系统" → `05-02-knowledge-paid-system`。同日同主题已有 package 时追加更具体后缀,**不覆盖旧 package**。

## Draft PRD workspace

Brainstorm 一开始就要创建或定位 active draft:`.arbor/tasks/<package>/prd.md`。

- **新需求**:用 `sdd-arbor create <package>` 创建 draft workspace。
- **续作**:用户给 package name 时直接读取对应 `prd.md`。
- **自然语言续作**:用户只说 topic / "继续某需求"时,扫描 `.arbor/tasks/*/prd.md` 找候选,多个候选时只问一次确认。

PRD draft 是 source of truth:**每轮回答后先更新 PRD,再问下一个问题**。

## 工作循环

1. 读取用户输入、用户提供的规格、相关代码、已有 research / PRD。
2. 创建或定位 draft;如果是新 draft,立即写入已知背景、初始 open questions 和当前推荐方向。
3. 按"模式"一节决定是否先 `AskUserQuestion` 询问 normal / grill-me。
4. 简短说明当前理解和真正阻塞 finalize 的缺口。
5. 若仍有 blocking 缺口,按 Question interaction 提一个最高价值问题;停下等用户。若信息已足够,跳到第 8 步进入扩展扫视和收尾整理。
6. 用户回答后更新 PRD draft:`Open Questions` 调整、`Requirements (evolving)` / `Acceptance Criteria (evolving)` / `Technical Framing` 追加、`Interview Log` 只记关键问答和需求变化(不要流水)。
7. 重复 4-6 直到形成初步 package scope 轮廓。
8. 做一次扩展扫视和 PRD 收尾整理(见 [`references/finalize-criteria.md`](references/finalize-criteria.md)),通过自检后给用户最终摘要并请求确认。
9. 用户确认后调用 `sdd-arbor finalize-brainstorm`,停在 impl 前并告诉用户下一步用 impl。

## Question interaction

- 一轮一问最高价值问题。
- 离散取舍必须用 `AskUserQuestion` 给 2-4 个选项(产品形态、范围、权限、计费、数据模型、技术边界等),推荐项放第一,在推荐项 description 中说明推荐理由。
- 真正开放题才用文字给推荐答案和理由。

## Context first

- 新项目按常规循环。
- 存量项目第一轮追问前主动读取相关代码,把变更方案写入 PRD 的 `What I already know` 和 `Technical Framing`。

详细要求见 [`references/context-first.md`](references/context-first.md)。

## Research handoff

研究材料只是 source-backed context / 候选理解,不代表需求已被用户确认或冻结。`ready-for-brainstorm` 只表示资料够 brainstorm 接手,不表示需求已定稿。

- 定位 research topic:用户显式指定优先;未指定时按当前需求扫描 `.arbor/research/*/index.md` 标题和摘要,多个候选时 `AskUserQuestion` 让用户确认。**只读匹配 topic,不遍历全部 research**。
- 显式区分 research 已支持的事实、研究提出的候选方向、未由用户确认的产品 / 范围 / 验收 / 技术 framing 假设。

## 用户自带规格

用户主动提供 SQL / 表结构 / API 文档 / 接口契约 / 参考设计时:

- 写入 PRD 对应 section 作为基准约束(SQL 写入数据备注,API 写入 Technical Framing 或接口备注),**不**通过 grill-me 重新推导。
- 仍审视技术合理性(缺索引、字段类型、命名一致性、与现有结构兼容性)。发现问题时用 `AskUserQuestion` 提具体建议,由用户决定是否采纳。
- 仍用 grill-me 追问规格之外的未决问题(产品边界、验收、规格未覆盖的技术决策)。
- 规格与代码分析冲突时用 `AskUserQuestion` 确认以哪个为准。

## Technical Framing

PRD 必须收敛承重技术边界,避免 impl 在关键架构问题上自由发挥。覆盖范围、Testing strategy 档位见 [`references/technical-framing.md`](references/technical-framing.md)。

## Wiki 引用（可选）

Technical Framing 阶段如果改动涉及项目内已有领域（已有 module、横切模式、历史决策、踩过的坑、外部协议约束），先用：

```bash
sdd-arbor wiki-collect --query "<keyword>" --limit 5 --json
```

按返回的 metadata 决定哪些页面值得读全文，再按 type 分层处理。

不同 type 的命中怎么用：

- **`module` 命中** — 引用 stable contract、不变量、关键 locator。Technical Framing 写"沿用 [[Modules/X]] § 对外契约"，不重新发明已有约束。
- **`cross_cut` 命中** — 引用同步修改位置作为防漏清单（详见 `wiki/references/page-types.md` "PRD 引用 wiki 的范式"）。
- **`decision` 命中** — 避免与历史决策矛盾；若需 supersede 旧决策，PRD 显式写"本次决定推翻 [[Decisions/X]]，原因 ..."，保留 supersession 链。
- **`gotcha` 命中** — Testing strategy 增加针对该坑的回归 case。
- **`source` 命中** — 外部协议 / 第三方 API 的硬约束（rate limit / payload 大小 / 错误码语义）直接挂进 Technical Framing。
- **`entity` / `concept` 命中** — 作为 framing 参考；不强求引用。

通用约束（与 type 无关）：

- **核心 scope 必须在 PRD 自包含**（AP7a），即使 wiki 全删，impl 看 PRD 仍知道做什么。
- **不复制 wiki 全文进 PRD**（AP11）；只用 wikilink + 一行 anchor 引用。
- **不凭记忆写 wikilink** — 只引用 `wiki-collect` 实际返回的 page title/path。
- **写 fallback** — wikilink 是防漏辅助，PRD 必须写"若 wiki 与现状不一致，impl 调研代码逐一识别"。
- **未命中不强求** — 若发现这是值得沉淀的长期知识，提醒用户在 impl 完成后 ingest 到 wiki。

跳过本节的场景：纯算法 / 纯 utility / 纯 typo fix / 完全孤立的新增功能（不依赖任何已有 module）。

## Slices

PRD 定稿时必须包含 `## Slices` 段,按依赖顺序写出有序实现切片。Slices 是 brainstorm 的产物——此时细节最多,切片最精准。切分原则(独立可验证小单元)、字段、示例、退化护栏见 [`references/slices.md`](references/slices.md)。

## Package artifacts

非平凡数据模型 / 协议 / 状态机 / 权限矩阵用 package-local artifact 承载草案级 contract。规则见 [`references/artifacts.md`](references/artifacts.md)。

## 定稿

扩展扫视、Open Questions 处理、PRD 收尾整理、自检和 PRD 定稿条件见 [`references/finalize-criteria.md`](references/finalize-criteria.md)。

Finalize 默认调用:

```bash
sdd-arbor finalize-brainstorm --input-json '{"name":"<package>","kind":"single","prd_path":".arbor/tasks/<package>/prd.md"}'
```

命令失败或 helper schema 变更时,再查看 `sdd-arbor finalize-brainstorm --help`。Draft 阶段可创建 / 编辑 PRD,**不要手写 `.arbor` control state**;ready package 必须由 `sdd-arbor finalize-brainstorm` 写入。

## Amendment 入口

review BRAINSTORM_DRIFT 后回到 brainstorm 时只针对 drift 追问,不重开完整循环。详见 [`references/amendments.md`](references/amendments.md)。

## 不做

- 不采集 raw evidence(用 research)。
- 不写代码(用 impl)。
- 不做语义审计(用 review)。
- 不自动推进下一阶段。

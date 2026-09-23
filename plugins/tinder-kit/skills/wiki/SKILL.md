---
name: wiki
description: "改动不熟悉的模块前查它的历史决策、踩过的坑（Gotcha）与联动修改链路（Cross-cut）；追问“当初为什么这么写”；或把新发现沉淀进项目三级记忆（CLAUDE.md、.claude/rules/、.forge/wiki/）时调用。"
---

# Wiki — 全局分层记忆与知识管家

项目知识、架构规则与排坑经验的统一管理中枢。消除知识孤岛与记忆漂移，将事实分流至三级记忆体系。

## 三级记忆体系拓扑（Three-Tier Memory）

```
┌──────────────────────────────────────────────┐
│ L1: CLAUDE.md                                │  <-- 全局常驻，最高原则与核心约束
├──────────────────────────────────────────────┤
│ L2: .claude/rules/<domain>.md                │  <-- 领域/文件按需挂载的工程规范
├──────────────────────────────────────────────┤
│ L3: .forge/wiki/<type>/<slug>.md             │  <-- 按需检索的长尾知识与 Gotcha
└──────────────────────────────────────────────┘
```

---

## 知识归宿判据（The 3-Question Placement）

当捕获到一条事实、决策、排障教训或契约时，依次执行三问裁决：

```
                    [ 捕获到一条事实 / 决策 / 踩坑 / 约束 ]
                                       │
                 (问 1: 它是否是全项目 100% 任务都要遵守的最高底线？)
                                  ┌────┴────┐
                                 YES        NO
                                  │         │
                           ┌──────┴─────┐   ▼
                           │ CLAUDE.md  │ (问 2: 模型是否容易在此处默认犯错？
                           └────────────┘  且它是一句硬性的行动规范？)
                                            ┌────┴────┐
                                           YES        NO
                                            │         │
                                     ┌──────┴─────┐   ▼
                                     │   rules/   │ (问 3: 它是否是长尾、低频、但涉及
                                     └────────────┘  多文件联动、深层原理或平台 Bug 的知识？)
                                                      ┌────┴────┐
                                                     YES        NO (代码自证的事实直接略过)
                                                      │
                                               ┌──────┴─────┐
                                               │   wiki/    │
                                               └────────────┘
```

### 1. 问范围（Scope）── 是否进 L1 `CLAUDE.md`？
- **判据**：是否是全项目无论任何模块、任何任务都必须遵守的最高准则（如技术栈选型、包管理器规则、提交归属权）；
- **正例**：“本项目机制在插件，标准在项目”、“用户拥有 commit 权，AI 不自动 commit”；
- **反例**：某个特定图表库的配置写法（不写入 `CLAUDE.md`）。

### 2. 问诱惑与语态（Temptation & Imperative）── 是否进 L2 `.claude/rules/`？
- **判据**：模型是否有默认倾向去犯错？且能否抽象为一句简短有力的正向硬准则？
- **正例**：“数据库查询走原生 SQL，不引入 ORM”、“批量合并网络请求，避免在循环内逐条发起”；
- **反例**：“为什么当年选手写 SQL 的详细 Benchmark 报告”（报告进 L3 Wiki，结论进 L2 Rules）。

### 3. 问长尾与信噪比（Signal-to-Noise）── 是否进 L3 `.forge/wiki/`？
- **判据**：是否是长尾、平时不碰该模块时知道无用、但碰到了就要命的隐性事实？
- **分类收录于 `.forge/wiki/`**：
  - `gotcha/`：反直觉的平台 Bug、依赖库未公开怪癖、版本兼容性 Gotcha；
  - `cross_cut/`：“改动接口 A 必须联动修改 B、C、D 另外 3 处”的多文件修改链路；
  - `decision/`：重大架构决策推导与被否决备选路径的实证代价；
  - `concept/`：复杂业务领域核心实体定义与边界。

---

## 准入标准：收录与不变量

- **反直觉的 Gotcha**：依赖库的未公开 Bug、平台兼容性陷阱、特殊环境配置。代码自证的事实不收。
- **跨文件修改链路（Cross-cut）**：修改某个核心接口时必须联动修改的协同路径。单文件局部细节不收。
- **被否决的技术路径（Rejected Paths）**：尝试过但被证实走不通的方案及其实证代价。未经验证的猜想不收。

---

## 权限与分级审批（Guardrails）

- **L1 (`CLAUDE.md`) & L2 (`.claude/rules/`) 变更**：
  - 在终端向人类展示精准的 Git-style Diff 提议，获得明确同意后方可使用 `Edit` 工具写入。
- **L3 (`.forge/wiki/`) 变更**：
  - 采用**顺风车提案（Rider Proposal）**：在 `/fix` 或 `/develop` 收尾时，顺带附带一条极简入库建议，人类回车即收录。
- **涟漪更新原则**：
  - 当新发现推翻了老文档，不擦除历史内容；
  - 采用追加演进节（如 `## 2026-09 演进更新`），保留历史背景与演化依据。

---

## 符号锚与代码防漂移（Drift-Proof Anchors）

- 引用代码使用符号锚（`file#symbol`），不用行号：
  - 正确：`` `src/auth/jwt.ts#refreshToken` ``
  - 错误：`src/auth/jwt.ts:45`（代码增删一行即全部失效）
- **体检**：`forge wiki lint` 检查符号锚指向的文件与符号是否还在，并报断链、缺 frontmatter、孤儿页。

---

## 分级检索（Tiered Retrieval）

页面 frontmatter 是唯一真相源；`index.md` / `log.md` 由命令派生，只给人浏览。检索分两级：

1. **取卡片**：`forge wiki collect --files <要改的文件或目录> --query "<需求关键词>" --json`，返回至多 5 张摘要卡片（标题、description、type、tags、符号锚）。`--files` 按页面符号锚命中，最适合“改这里之前要知道什么”；`--query` 按标题、标签、描述打分，中文可直接写。
2. **读正文**：从卡片里挑真正相关的 1–2 篇，用 Read 读全文。

写入或更新页面后运行 `forge wiki index --write` 刷新 `index.md` 与 `log.md`。

---

## 双轨标签体系与受控词表（Controlled Vocabulary）

标签的质量直接决定了模型语义检索的命中率。Wiki 元数据遵循双轨打标与受控词表准则。

### 1. 单篇元数据格式（YAML Frontmatter）
每个 `.forge/wiki/` 页面头部包含结构化元数据：
```markdown
---
type: cross_cut  # 可选: gotcha | cross_cut | decision | concept
title: 三方客服平台对接与超时 Gotcha
tags: [ai-customer-service, 客服, webhook, retry]
anchors:
  - src/forwarder.ts#CustomerServiceForwarder
description: 对接三方客服平台拓扑，包含 HMAC 签名与 2s 超时重试幂等去重
---
```

### 2. 双轨打标法则（Double-Track Tags）
每个条目打 3~5 个标签，覆盖以下双轨：
- **轨 1：业务领域（Domain）── 人类与业务的自然语言（中英双语）**：
  - 例如：`[ai-customer-service, 客服]`、`[payment, 支付]`、`[order, 订单]`、`[auth, 鉴权]`；
  - 确保人类无论用中文还是英文 Prompt，模型都能精准命中。
- **轨 2：技术机制（Mechanism）── 代码底层涉及的工程模式**：
  - 例如：`[buffer, 缓冲]`、`[webhook]`、`[idempotency, 幂等]`、`[rate-limit, 限流]`、`[distributed-lock]`。

### 3. 受控标签准则（Controlled Vocabulary）
- **完整语义**：使用自解释的完整单词与双轨标签（如 `[ai-customer-service, 客服]`、`[database, 数据库]`），避免使用含义模糊的短缩写；
- **有效区分度**：标签应指代具体领域或工程机制（如 `[webhook]`, `[idempotency]`），避免使用泛词（如 `code`, `utils`）；
- **先查后增**：新建条目打标前用 `forge wiki index --json` 查看既有标签，优先复用，防止同义碎片化。

---

## 需求完工与知识晋升（Promotion）

分清**增量（Delta）**与**存量（State）**：

1. **`spec.md` 是任务增量（Delta）── 完工即冻结**：
   - 任务在 `/develop` 中完成交付后，`.forge/tasks/<slug>/spec.md` 立即冻结归档，成为不可变的审计记录；
   - 现状以代码和测试为准；归档的 spec 只当历史。
2. **Wiki 是系统存量（State）── 只收录不变量与拓扑**：
   - 任务完工时，Wiki 只收不变量、ADR、领域概念与拓扑；
   - **四类知识晋升资产**：
     - **不可逆架构决策** ➔ 沉淀为轻量 ADR：`.forge/wiki/decision/`；
     - **跨系统/跨模块联动拓扑** ➔ 沉淀为拓扑名片：`.forge/wiki/cross_cut/`；
     - **业务核心实体与边界** ➔ 沉淀为名词消歧页：`.forge/wiki/concept/`；
     - **高频踩坑反思** ➔ 沉淀为 Gotcha 卡片：`.forge/wiki/gotcha/`；
     - **全项目通用规则** ➔ 提议晋升为 rules：`.claude/rules/<domain>.md`。

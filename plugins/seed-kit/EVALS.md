# seed-kit 评估手册（seed-kit-evals）

> 给后续 AI / 人类：如何用 **seed-kit-evals** 评测、回归、归因、修复 **本插件**。
> 最后更新：2026-07-11
> 历史背景（旧 harness）见 [`EVAL_HANDOFF.md`](./EVAL_HANDOFF.md)——那是 2026-06 快照，**不是**当前操作手册。

---

## 1. 两个仓库的关系

| 仓库 | 角色 | 本机默认路径 |
|---|---|---|
| **claude-plugins / seed-kit** | 被测对象（skill / hook / CLI / agents） | `/Users/camellia/Personal/Code/claude/claude-plugins/plugins/seed-kit` |
| **seed-kit-evals** | 行为评测实验室（场景 + runner + 评分 + 自进化） | `/Users/camellia/Personal/Code/claude/seed-kit-evals` |
| **gauntlet**（可选依赖） | 多轮 QA agent 驱动层；语义场景需要 | `/Users/camellia/Personal/Code/claude/gauntlet` |

一句话：

- **改插件行为** → 改本目录（skills / tools / hooks / agents）
- **测插件行为是否真的被 agent 遵守** → 在 `seed-kit-evals` 跑场景
- **隔离修复候选并验证是否可 promote** → `seed-evals evolve --repair`，目标仍是本插件树

联动方式：评测时通过 `--plugin-dir` 把本目录加载进真实 Claude Code session，**不是 mock**。

```
seed-kit-evals
  scenarios/          # 测什么（story + setup + checks）
  src/runner/         # 怎么跑（headless 或 gauntlet）
  results/            # 跑出什么（verdict / transcript / cost）
       │
       │  --plugin-dir
       ▼
plugins/seed-kit      # 被加载的真实插件
```

---

## 2. 前置条件

在 `seed-kit-evals` 根目录操作（默认用 **Bun**，不是 npm/node）：

```bash
export PATH="$HOME/.bun/bin:$PATH"
cd /Users/camellia/Personal/Code/claude/seed-kit-evals

# 可选：语义 / gauntlet 场景需要
export GAUNTLET_ROOT=/Users/camellia/Personal/Code/claude/gauntlet

# 凭据：编辑 credentials.yaml，并导出对应 API key env
# 常见 provider key：ali-qwen / anthropic / minimax / deepseek / openrouter
```

常用路径变量（写文档/命令时建议用变量，避免硬编码漂移）：

```bash
export SEED_KIT_DIR=/Users/camellia/Personal/Code/claude/claude-plugins/plugins/seed-kit
export SEED_EVALS_DIR=/Users/camellia/Personal/Code/claude/seed-kit-evals
export PLUGIN_REPO=/Users/camellia/Personal/Code/claude/claude-plugins
```

CLI 入口：

```bash
bun run src/cli/index.ts --help
# 或 package bin 名：seed-evals（等同）
```

---

## 3. 场景模型（先读这个再跑）

每个场景在 `scenarios/<id>/`：

```
story.md     # frontmatter + User Task +（gauntlet 时）QA Instructions + Acceptance Criteria
setup.sh     # 搭建 fixture 工作区
checks.sh    # 确定性 pre/post 断言（不依赖 LLM 判断）
```

### frontmatter 关键字段

| 字段 | 含义 |
|---|---|
| `quorum_tier` | `sentinel` / `full` / `regression` / `adhoc` |
| `quorum_driver` | 默认 `headless`；交互语义为 `gauntlet` |
| `quorum_eval_kind` | `mechanism`（CLI/hook/文件态）或 `semantic`（工作流行为） |
| `quorum_task_delivery` | gauntlet 下默认 `gauntlet`；兼容旧场景可能是 `embedded` |
| `quorum_max_time` | 可选超时提示（如 `8m`） |

### 两类测试

| | 确定性机制 | 交互语义 |
|---|---|---|
| **测什么** | `seed` CLI / hook / wiki / scaffold 是否按契约工作 | Coding-Agent 面对自然语言时是否遵循 seed-kit 工作流 |
| **driver** | `headless`（`claude -p`） | `gauntlet`（QA agent 多轮驱动） |
| **例子** | `seed-done-gates-on-failure` | `impl-reads-prd-before-coding`、`review-does-not-fix-while-reviewing` |

### 当前规模（约，以仓库为准）

- ~60+ scenarios
- tier 大致：`sentinel` / `full` / `regression` / `adhoc`
- 多数交互场景是 `gauntlet`
- 命名 suite：`suites/core-semantic.json`
  （`review-prd-catches-planted-flaws` → `impl-delivers-project-contract` → `review-loop-repairs-project-quality-gap`，默认 3 trials）

场景分类前缀速查：

| 前缀 | 测的插件面 |
|---|---|
| `seed-*` | CLI：new / status / done / wiki |
| `guard-*` / `prd-checkbox-guard` | hook 底线 |
| `impl-*` | impl skill 行为 |
| `review-*` | review / review-prd / review-loop |
| `brainstorm-*` | brainstorm skill |
| `wiki-*` | wiki 知识层 |
| `preference-*` | 用户偏好遵从 |
| `scaffold-*` / `checks-*` | eval harness 自身脚手架与 check DSL |

---

## 4. 日常命令速查

以下均在 `$SEED_EVALS_DIR` 执行。

### 4.1 列表与校验

```bash
bun run src/cli/index.ts list
bun run src/cli/index.ts check                  # 全部场景 contract
bun run src/cli/index.ts check impl-reads-prd-before-coding
```

### 4.2 红灯 fixture（防假绿）

行为缺失时 post-check 应失败：

```bash
bun run src/cli/index.ts check-red \
  --plugin-dir "$SEED_KIT_DIR"

bun run src/cli/index.ts check-red seed-done-gates-on-failure \
  --plugin-dir "$SEED_KIT_DIR"
```

### 4.3 单场景 / suite

```bash
# 机制场景（headless，通常不需要 GAUNTLET_ROOT）
bun run src/cli/index.ts run seed-done-gates-on-failure \
  --agent claude \
  --provider ali-qwen \
  --plugin-dir "$SEED_KIT_DIR"

# 语义场景（gauntlet）
export GAUNTLET_ROOT=/Users/camellia/Personal/Code/claude/gauntlet
bun run src/cli/index.ts run impl-reads-prd-before-coding \
  --agent claude \
  --provider ali-qwen \
  --plugin-dir "$SEED_KIT_DIR"

# 命名 suite
bun run src/cli/index.ts run --suite core-semantic \
  --agent claude \
  --provider ali-qwen \
  --plugin-dir "$SEED_KIT_DIR" \
  --trials 1
```

### 4.4 矩阵回归

```bash
# sentinel：改动后先跑（快、机制向）
bun run src/cli/index.ts run-all \
  --tier sentinel \
  --agents claude \
  --providers ali-qwen \
  --plugin-dir "$SEED_KIT_DIR" \
  --jobs 2 \
  --fail-on-nonpass

# regression：合并/发版前
bun run src/cli/index.ts run-all \
  --tier regression \
  --agents claude \
  --providers ali-qwen \
  --plugin-dir "$SEED_KIT_DIR" \
  --baseline v0.1.0 \
  --fail-on-nonpass

# 只跑 gauntlet 语义面
bun run src/cli/index.ts run-all \
  --driver gauntlet \
  --tier full \
  --agents claude \
  --providers ali-qwen \
  --plugin-dir "$SEED_KIT_DIR"
```

退出码约定（常见）：

| code | 含义 |
|---|---|
| 0 | pass / 无回归 |
| 1 | fail |
| 2 | indeterminate / 致命错误 |
| 3 | baseline / Pareto **regression** |

### 4.5 baseline

```bash
bun run src/cli/index.ts baseline save v0.1.0 --tier regression
bun run src/cli/index.ts baseline diff v0.1.0 --tier regression
# 或在 run-all 时：--baseline v0.1.0（有退化 exit 3）
```

### 4.6 四轴评分

```bash
bun run src/cli/index.ts score --from <batch-id-or-dir>
bun run src/cli/index.ts score --from <batch> --baseline v0.1.0 --json
```

轴：`function` / `methodology` / `efficiency` / `robustness` + Pareto 对比。

### 4.7 看结果 / job / 看板

```bash
bun run src/cli/index.ts show results/<run-dir>
bun run src/cli/index.ts jobs list
bun run src/cli/index.ts jobs show <job-id>
bun run src/cli/index.ts jobs cancel <job-id>
bun run src/cli/index.ts dashboard --port 3000
```

单次 run 目录常见产物：`verdict.json`、transcript/trajectory、workdir、cost/provenance。

---

## 5. 自进化链路（失败 → 假设 → 隔离修复）

报告阶段（只写报告，不直接改生产插件）：

```bash
bun run src/cli/index.ts capture --from results/<run-or-batch>
bun run src/cli/index.ts analyze --from results/<batch>
bun run src/cli/index.ts hypothesize --from results/<batch>
bun run src/cli/index.ts validate --from <report.json>
bun run src/cli/index.ts evolve --from <report.json>
```

**隔离生产修复**（改候选插件树并跑 held-out 验证）：

```bash
bun run src/cli/index.ts evolve --repair \
  --from <report-or-batch> \
  --baseline <baseline-name> \
  --plugin-repo "$PLUGIN_REPO" \
  --plugin-dir "$SEED_KIT_DIR" \
  --provider ali-qwen \
  --credential ali-qwen \
  --core-suite core-semantic \
  --gauntlet-root "$GAUNTLET_ROOT"
```

注意：

- `--execute` 已废弃，会 fail-closed，应使用 `--repair`
- repair 在 ephemeral workspace 验证，**不默认直接合入本仓库工作树**
- 归因时先分清：机制缺口 / 场景误标 / harness 问题 / 项目标准缺失 / 模型方差——不要把环境摩擦写成 workflow 规则

---

## 6. 改插件时建议怎么用 eval

### 最小闭环

1. **先写/改 scenario**（若测新行为）：`bun run src/cli/index.ts new my-scenario`
2. `check` + 必要时 `check-red` 保证 post-check 真能抓缺失
3. 改 seed-kit skill/helper/hook
4. 跑相关单场景 → `run-all --tier sentinel` → `run-all --tier regression --baseline …`
5. 有 fail：`analyze` 归因；确认是插件问题再改；需要时 `evolve --repair`

### 什么时候改插件 vs 改场景

seed-kit 哲学：**机制在插件，标准在项目**。

| 失败原因 | 改哪里 |
|---|---|
| 跨栈都成立的机制坏了（done gate、checkbox guard、skill 该读 PRD 却不读） | **改 seed-kit** |
| 场景要求了 seed-kit 不承诺的强标准（某栈 UI/a11y/具体工具名） | **改 scenario**，不改插件 |
| setup/check/gauntlet/capture 坏了 | **改 seed-kit-evals** |
| 项目缺测试/质量命令 | 正确行为可能是 **报告缺口**，不是插件发明标准 |
| 单模型偶发 | 记 backend signature；不为单一模型过拟合规则 |

判定式（与 `CLAUDE.md` 一致）：一行若不能对 Web / CLI / 游戏 / 嵌入式同等成立，就不应作为插件硬标准进入 P0/P1 gate。

---

## 7. 新场景写作要点

```bash
cd "$SEED_EVALS_DIR"
bun run src/cli/index.ts new my-behavior-name
# 编辑 scenarios/my-behavior-name/{story.md,setup.sh,checks.sh}
bun run src/cli/index.ts check my-behavior-name
```

要求：

- `story.md`：任务与 QA 指令在前，`## Acceptance Criteria` 为最后 section
- **不要** hardcode `seed-kit-evals` 本机绝对路径；用 `$QUORUM_EVAL_ROOT` / fixture 内 `./seed-evals` wrapper
- `setup.sh` 可执行；`checks.sh` 通常不可执行（由 harness 以特定方式调用）
- 机制场景：checks 只读文件系统/命令退出码，不依赖 LLM
- 语义场景：QA Instructions 写清 pass/fail/investigate，**不要**把 planted answer 泄漏给 Coding-Agent
- Skill TDD 习惯：先写应 **FAIL** 的 pressure scenario，再改 skill，再跑到 PASS 且 regression 无退化

---

## 8. 评测在验证什么（对应插件面）

| 插件机制 | 典型场景信号 |
|---|---|
| `seed new/status/done` | `seed-new-*` / `seed-status-*` / `seed-done-*` |
| checkbox 只能由 done 翻 | `prd-checkbox-guard` |
| 破坏性命令拦截 | `seed-guard-blocks-destructive` / `guard-refuses-destructive-cleanup` |
| impl 读 PRD、跑验证、记证据 | `impl-reads-prd-before-coding` / `impl-runs-runnable-verification` / `impl-records-evidence` |
| review 只审不修 | `review-does-not-fix-while-reviewing` |
| review-prd 独立抓缺口 | `review-prd-catches-planted-flaws` |
| review-loop 修质量缺口 | `review-loop-repairs-project-quality-gap` |
| wiki 读写 | `*-uses-wiki-*` / `wiki-*` / `seed-wiki-*` |
| brainstorm 收敛与 scope | `brainstorm-*` |

**不测 / 不该测成插件硬门槛的东西**：项目审美细则、某技术栈专属工具清单、把体验质量塞进二值 gate。

---

## 9. 给 AI 的操作纪律

1. **默认 cwd = seed-kit-evals** 跑评测；改 skill 时 cwd = 本插件目录。
2. **始终显式传** `--plugin-dir "$SEED_KIT_DIR"`（或 repair 时的 repo 相对 `plugins/seed-kit`），否则可能在测“裸 Claude”，不是 seed-kit。
3. 语义场景先确认 `GAUNTLET_ROOT` 可用；没有 gauntlet 时优先跑 `headless` / mechanism。
4. 先读 `verdict.json` + checks 记录再下结论；空 transcript / setup 失败 → `indeterminate`，不是插件“坏了”。
5. 不要把一次失败立刻固化成 skill 永久规则（见仓库 `.claude/rules/workflow-design.md`：「不为一次失败加长期负担」）。
6. 改 prompt/skill 前优先看是否应用 **机制层** 补强（helper/hook/契约），而不是堆枚举。
7. agent **不自动 commit** 评测或插件改动；由人决定提交边界。
8. 成本：full gauntlet 矩阵昂贵；日常用 sentinel + 单场景，发版再用 regression/full。

---

## 10. 快速决策树

```
想确认 CLI/hook 没坏？
  → run-all --tier sentinel --plugin-dir $SEED_KIT_DIR

想确认工作流行为没漂？
  → 相关 *impl*/*review*/*brainstorm* 单场景，或 --tier regression

改完 skill 怕退化？
  → run-all --tier regression --baseline <name> --fail-on-nonpass

失败不知该怪谁？
  → analyze --from <batch>，再按 §6 表归因

要自动提修复并隔离验证？
  → evolve --repair --plugin-repo $PLUGIN_REPO --plugin-dir plugins/seed-kit
```

---

## 11. 相关文件索引

**本插件**

- [`README.md`](./README.md) — 用户向用法
- [`DESIGN.md`](./DESIGN.md) — 设计原则与 gate/loop 哲学
- [`CLAUDE.md`](./CLAUDE.md) — 栈无关判定式
- [`EVAL_HANDOFF.md`](./EVAL_HANDOFF.md) — 旧评估历史（勿当现行手册）
- `skills/` `tools/` `hooks/` `agents/` — 被测实现

**seed-kit-evals**

- `src/cli/index.ts` — CLI 命令面
- `scenarios/` — 场景库
- `suites/` — 命名 suite
- `credentials.yaml` — provider 注册
- `docs/plan.md` — 路线图（可能落后于代码，以 CLI/源码为准）
- `docs/scoring-design.md` — 评分设计
- `results/` — 历史 run 产物
- `packages/dashboard/` — 只读看板

**规则（改插件前必读）**

- `/Users/camellia/Personal/Code/claude/claude-plugins/.claude/rules/workflow-design.md`
- `/Users/camellia/Personal/Code/claude/claude-plugins/.claude/rules/prompt-design.md`

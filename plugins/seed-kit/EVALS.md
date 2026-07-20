# seed-kit 评估手册（seed-kit-evals）

> 给后续 AI / 人类：如何用 **seed-kit-evals** 给本插件**出题、跑题、对照、看结果、归因**。
> **每次要用到测试用例、要跑测试用例、要对照"有/无 seed-kit"之前，先读这份。**
> 最后更新：2026-07-18。CLI 是最终 source of truth，参数有变先跑 `<cmd> --help`。
> 旧 harness 历史见 [`EVAL_HANDOFF.md`](./EVAL_HANDOFF.md)（2026-06 快照，**不是**现行手册）。

---

## 0. 先看这个：你要测什么，走哪条路

| 你想确认的事 | 走哪条路 | 关键命令 |
|---|---|---|
| CLI / hook / 文件态机制没坏（确定性） | **机制场景**，headless 驱动 | `run <id>` / `run-all --tier sentinel` |
| 工作流行为没漂（agent 面对自然语言是否真走 PRD→impl→review） | **语义场景**，Gauntlet 真实多轮交互 | `run <id>`（需 `GAUNTLET_ROOT`） |
| 某能力"装上 vs 没装"是否更好 | **价值对照实验** | `experiment create/run/evaluate` 或 `run-all --label` |
| 改了 skill 后有没有进步 | 冻结变量只换 plugin+label，再比 | 同上，加 candidate 臂 |
| 改完怕退化 | 回归矩阵 + baseline diff | `run-all --tier regression --baseline <name>` |
| 失败不知怪谁 | 归因链 | `capture → analyze → hypothesize → validate → evolve` |
| 想自动提修复并隔离验证 | 候选修复（只产 patch） | `evolve --repair` |

**两个最容易踩的误区**：
1. 用"请调用 `/seed-kit:xxx`"的**单臂**场景，冒充"有 skill 比没 skill 好"——那只能测接线，不能测价值。价值对照必须**两臂**（control/treatment），User Task **中性、不点名 skill**。
2. 把"一次性把需求丢给 agent"当成真实测试——语义场景必须用 **Gauntlet QA agent 多轮真实交互**（`--adapter tui`），不能拿 `claude -p` 冒充。

---

## 1. 两个仓库的关系

| 仓库 | 角色 | 本机默认路径 |
|---|---|---|
| **claude-plugins / seed-kit** | 被测对象（skill / hook / CLI / agents） | `/Users/camellia/Personal/Code/claude/claude-plugins/plugins/seed-kit` |
| **seed-kit-evals** | 行为评测实验室（场景 + runner + 评分 + 自进化） | `/Users/camellia/Personal/Code/claude/seed-kit-evals` |
| **gauntlet**（语义场景依赖） | QA agent 多轮驱动层 | `/Users/camellia/Personal/Code/claude/gauntlet` |

联动：评测时通过 `--plugin-dir` 把本目录加载进**真实** Claude Code session（不是 mock）。

```
seed-kit-evals                              plugins/seed-kit
  scenarios/   测什么                         （被 --plugin-dir 加载）
  src/runner/  怎么跑                │
  results/     跑出什么  ◄───────────┘
```

---

## 2. 前置条件

在 `seed-kit-evals` 根目录操作（用 **Bun**，不是 npm/node）：

```bash
export PATH="$HOME/.bun/bin:$PATH"
cd /Users/camellia/Personal/Code/claude/seed-kit-evals

# 语义/gauntlet 场景需要：
export GAUNTLET_ROOT=/Users/camellia/Personal/Code/claude/gauntlet

# 建议路径变量（写文档/命令时用变量，避免硬编码漂移）
export SEED_KIT_DIR=/Users/camellia/Personal/Code/claude/claude-plugins/plugins/seed-kit
export SEED_EVALS_DIR=/Users/camellia/Personal/Code/claude/seed-kit-evals
export PLUGIN_REPO=/Users/camellia/Personal/Code/claude/claude-plugins
```

### Gauntlet（语义场景必需）

Gauntlet 是独立 QA 框架：读 story card → 用 LLM **QA agent 扮演用户**，通过 tmux `--adapter tui` 多轮驱动被测 Claude Code → 输出结构化判定。三个接入口径（优先级）：`GAUNTLET_ROOT` 环境变量（推荐，production 判定靠它）→ PATH 上的 `gauntlet` → `evolve --repair` 的 `--gauntlet-root` 参数。

### Provider / credential（两套体系，别混）

**A. `run` / `run-all` 用 `--provider`（credential key）**
- 来源 1：`seed-kit-evals/credentials.yaml`（ali-qwen / anthropic / minimax / deepseek / openrouter）
- 来源 2：provider config 目录（默认 `~/Personal/Config/claudeConfig`，可用 `QUORUM_PROVIDER_CONFIG_DIR` 覆盖）里的 `<key>.json`，如 `zhipu-glm.json`
- token 只在运行时注入子进程 env，run 结束即消失；**只读，不复制到 manifest/HOME**

**B. `experiment` 用 `--execution-model` / `--judge-model`（profile 名）**
- 来源：`seed-kit-evals/config/model-profiles.json`，分 `execution_models`（驱动 Coding-Agent）和 `judge_models`（评分），如 `glm-5.2`、`grok-4.5`

Claude launcher：`/Users/camellia/.local/bin/claude`。

---

## 3. 场景模型（scenario = 一道测试用例）

每个场景在 `scenarios/<id>/`：

| 文件 | 可执行？ | 谁用 |
|---|---|---|
| `story.md` | — | runner 解析 frontmatter + 正文；Gauntlet 读正文当 prompt |
| `setup.sh` | ✅（runner 会强制 chmod） | 在 workdir 里 `bash setup.sh` 建夹具 |
| `checks.sh` | ❌（被 source） | runner `source` 后调 `pre()` / `post()` |

### frontmatter 字段

| 字段 | 取值 | 含义 |
|---|---|---|
| `id` | kebab-case | 机器 id，必填 |
| `title` | 中文 | 人读题名，必填；别拿 raw id 当标题 |
| `description` | 中文 | 1–2 句：在验证什么 |
| `focus` | 中文 | 一句可判定问题 |
| `fields` | 逗号分隔中文 | 本题评分维度（有 `scenario_metrics` 才显示分） |
| `compare_fields` | 逗号分隔中文 | 跨 run 对照列；要判过没过末尾加 `判定` |
| `quorum_tier` | `sentinel` / `full` / `regression` / `adhoc` | sentinel=机制哨兵；full/regression=完整语义（**强制** post 里有确定性断言）；adhoc=临时 |
| `quorum_driver` | `headless` / `gauntlet` | headless=`claude -p` 一次性；gauntlet=QA agent 多轮 TUI |
| `quorum_eval_kind` | `mechanism` / `semantic` | semantic 需要 Gauntlet 语义评审 |
| `quorum_task_delivery` | `gauntlet`（默认）/ `embedded` | gauntlet=对话交付；embedded=嵌进 CLAUDE.md。semantic 场景强制 gauntlet |
| `quorum_max_time` | `10m` 等 | 超时元数据 |
| `quorum_suite` | suite id | 默认归属 suite |
| `experiment_role` | `outcome` / `mechanism` / `negative-control` | 价值实验角色。**⚠️ schema 只认 `mechanism`，文档里写的 `mechanism_sentinel` 是错的** |
| `value_axis` | `^[a-z0-9][a-z0-9-]*$` | 实验轴短名，供 suite/索引 |
| `code_context` | `with_code` / `no_code` / `mixed` | 是否有可对账代码。**⚠️ schema 只认这三个，文档里写的 `n/a` 是错的** |

### 两类测试

| | 机制（deterministic） | 交互语义（semantic） |
|---|---|---|
| 测什么 | CLI/hook/wiki/scaffold 是否按契约 | Coding-Agent 面对自然语言是否遵循工作流 |
| driver | `headless`（`claude -p`） | `gauntlet`（QA agent 多轮） |
| 例子 | `hello-world`、`seed-done-gates-on-failure` | `impl-delivers-project-contract`、`review-prd-catches-planted-flaws` |

场景前缀速查：`seed-*`=CLI / `guard-*`=hook / `impl-*` / `review-*` / `brainstorm-*` / `wiki-*` / `scaffold-*`,`checks-*`=eval harness 自身。

---

## 4. 创建一道测试用例（出题全流程）

### 4.1 脚手架

```bash
cd "$SEED_EVALS_DIR"
bun run src/cli/index.ts new my-scenario
# 生成 scenarios/my-scenario/{story.md,setup.sh,checks.sh}，带中文占位模板
```

### 4.2 写 `story.md`

**frontmatter** 按上表填（人读字段中文优先）。**正文三段，顺序硬约束**：

1. `## User Task`（或 `## 用户任务`）：原样投递给 Coding-Agent 的题面。
2. `## QA Instructions`（或 `## 评判说明`）：原样投递给 Gauntlet 评判 agent，告诉它怎么判 pass/fail。
3. `## Acceptance Criteria`（或 `## 通过标准`）：`- ` 列表，**必须是正文最后一个 `##` 段**（后面再有任何标题都报错）。

解析规则：从 AC heading 后开始，遇 `- ` 开条，遇任何 `#` heading 立即 break。`quorum_driver: gauntlet` 时 User Task + QA Instructions 必须非空；`semantic` 场景 QA Instructions 必须含"保护答案"语义（同时出现"答案/植入"类词 + "不得/禁止/不要"类否定词），否则 warning。

**User Task 写法**：
- 机制/sentinel 场景：**可以**点名 skill，如 `请调用 /seed-kit:review-prd audit-export`。
- 价值/outcome 场景：**中性**，只写"目标 + 禁止副作用"，**不点名 skill**，也**不写"禁止用某 skill"**。
- 一律写明边界（不改 PRD、不切分支、不 commit），因为 `post()` 通常断言这些。

### 4.3 写 `setup.sh`

环境变量（setup.sh 里可用）：

| 变量 | 含义 |
|---|---|
| `$QUORUM_WORKDIR` | 一次性 workdir，**setup.sh 唯一可依赖的工作目录** |
| `$QUORUM_EVAL_ROOT` | eval root（默认=仓库根），让 fixture 调回 runner 而不写死 checkout 路径 |
| `$QUORUM_BUN` | bun 绝对路径 |
| `$QUORUM_PLUGIN_DIR` | 若传入 plugin，指向 plugin 目录 |

标准骨架：

```bash
#!/usr/bin/env bash
set -euo pipefail

git init -b main "$QUORUM_WORKDIR" >/dev/null
cd "$QUORUM_WORKDIR"
git config user.email "eval@example.com"
git config user.name "Eval Runner"

# 内联 fixture（文件少时用 heredoc）：
cat > CLAUDE.md <<'CLAUDE'
# Project workflow
使用语言：中文。
CLAUDE

cat > .arbor/tasks/<id>/prd.md <<'PRD'
... PRD ...
PRD

git add .
git commit -m "Add fixture" >/dev/null
```

要点：
- `git init -b main` + 初始 commit —— `git-count commits eq 1` 是最常见的 pre/post 不变式（agent 不该新建 commit）。
- **fixture 两种写法**：内联 heredoc（文件少，主流）／ `fixture/` 目录 + `cp -R "$QUORUM_EVAL_ROOT/scenarios/<id>/fixture/." "$QUORUM_WORKDIR"/`（文件多/大型）。
- **禁止**在 story/setup 里写死 seed-kit-evals 的 checkout 绝对路径（`check` 会 error）；用 `$QUORUM_EVAL_ROOT` 或 fixture-local `./seed-evals` wrapper。
- 让 fixture 内部能调 runner 时，写一个 wrapper：`exec "$QUORUM_BUN" "$QUORUM_EVAL_ROOT/src/cli/index.ts" run "$@"`。

### 4.4 写 `checks.sh`（DSL，确定性断言）

被 runner **source**（不是 execute），只定义 `pre()` 和 `post()`。`pre()` 在跑 agent 前校验 fixture 形状（任一 fail → **不启动 agent**）；`post()` 在 agent 跑完后校验产物 + transcript（fail 计入最终 verdict）。

**全部 17 个动词**（路径相对 workdir；`checks.sh` 里 `$QUORUM_WORKDIR` **不可用**，动词内部自己拼）：

| 类 | 动词 | 用法 |
|---|---|---|
| 文件 | `file-exists` | `file-exists <rel-path>` |
| 文件 | `file-contains` | `file-contains <rel-path> <literal>` |
| 文件 | `file-glob-contains` | `file-glob-contains <glob> <literal>`（glob 无命中=fail） |
| 命令 | `command-succeeds` | `command-succeeds '<shell-cmd>'`（30s 超时，workdir 内跑） |
| 命令 | `requires-tool` | `requires-tool <tool>...`（找不到=**broken**，不是 fail） |
| git | `git-repo` / `git-branch <name>` / `git-count <commits\|files> <gte\|lte\|eq> <n>` / `assert-checkout-clean` | |
| transcript | `transcript-contains <literal>` | 整个 transcript 含子串 |
| transcript | `transcript-tool-called <tool>` | 至少一次 `tool===<tool>`（如 `Skill`/`Agent`/`Bash`） |
| transcript | `transcript-tool-count <tool> <gte\|lte\|eq> <n>` | 调用次数比较 |
| transcript | `transcript-tool-before <a> <b>` | a 首次出现 index < b |
| transcript | `transcript-tool-arg-match <tool> <literal>` | 该 tool 的 args JSON 含子串（断言 `Agent` 调用里写了 `seed-kit:seed-prd-review`） |
| transcript | `transcript-skill-called <skill-name>` | `tool===Skill` 且 `args.skill===<name>`（如 `"seed-kit:review-prd"`） |
| transcript | `transcript-read-before-write <read-pat> <write-pat>` | 先 Read/Grep 命中，再 Write/Edit/Bash 写入命中 |
| 否定 | `not <verb> <args...>` | 翻转 pass↔fail；broken 不可逆 |

每条断言 fail 只 emit 一条 record 继续；断言 **broken**（exit 2/127）立即中止 phase 且裁决变 `indeterminate`。

典型骨架：

```bash
pre() {
  git-repo
  git-branch main
  git-count commits eq 1
  file-exists .arbor/tasks/<id>/prd.md
  not file-exists .arbor/tasks/<id>/done-logs/S-001.json   # 起点不该有的产物
}

post() {
  file-exists <产物>
  command-succeeds "./verify.sh"                           # 真实验证命令
  transcript-skill-called "seed-kit:<skill>"               # 机制场景可点名
  git-branch main
  git-count commits eq 1
  command-succeeds 'git diff --quiet -- <不该改的文件>'
  not transcript-tool-arg-match Bash "git commit"
  not transcript-tool-arg-match Bash "git switch"
  not transcript-tool-arg-match Bash "git checkout -b"
}
```

### 4.5 校验：`check` + `check-red`

```bash
bun run src/cli/index.ts check my-scenario      # 静态合同体检（frontmatter/结构/AC顺序/post有确定性断言）
bun run src/cli/index.ts check-red my-scenario --plugin-dir "$SEED_KIT_DIR"   # 防假绿
```

**`check-red` 机制**（防"永远通过的废检查"）：在一个 tmpdir 跑 setup → pre 必须全绿 → 写一个**空 trajectory**（模拟"agent 啥也没做"）→ 跑 post。判定：
- post 全过（无 fail）→ **fail**（断言没反向锁，永远假绿）
- post records 数为 0 → **fail**（post 啥也没断言）
- 至少一条 fail → **pass**（断言真能挡住该发生却没发生的行为）

所以 `post()` **至少要有一条"该产物/该调用没出现就失败"的正向断言**（`file-exists`/`transcript-skill-called`/`command-succeeds` 等），不能全是 `not ...`。

若场景通过与否靠 rubric 语义判定、checks 只盯副作用边界（典型 outcome 场景），在 `checks.sh` 顶部写：
```bash
# red-fixture: skip - 语义质量由 rubric 评；checks 只覆盖副作用边界
```

### 4.6 outcome vs sentinel 写法差异（价值场景必读）

| | mechanism sentinel（哨兵） | outcome（价值） |
|---|---|---|
| User Task | 可点名 skill | **中性**，只写目标+边界，不点名 |
| `experiment_role` | `mechanism` | `outcome` |
| `post()` | **可**断言 `transcript-skill-called` | **禁止**断言 skill 调用（control 臂没这 skill）；只盯产物/边界 |
| `red-fixture:` 头 | 通常不写 | 通常 `skip`（质量由 rubric 评） |
| planted gaps | 可不藏 | **藏**在 author/QA-only 段，绝不写进 User Task |

**植入缺口（planted boundaries）怎么藏**：写在 story.md 的 `## Planted gaps (author / QA only)` 段（位于 User Task **之前**——runner 只投递 User Task 段给 agent，前面的不泄露），或在 `docs/` 旁注。每个缺口必须是"会改变实现或阻塞开工"的 serious gap。例：

```
## Planted gaps (author / QA only — never reveal to Coding-Agent)
1. <维度未决>：xxx 时的策略/阈值/终端态没写清。
2. <字段不一致>：AC 要求 timestamp，现有代码用 occurredAt。
3. <主观 AC>：「用户觉得好用」不可证伪。
```

### 4.7 选题：基建类 vs 业务类

选题别默认只挑基建类（工具库/中间件）。两类测的能力不同，同一 value_axis 尽量搭配：

| 维度 | 基建类（配置/队列/认证/限流/缓存…） | 业务类（订单/审批/计费/排期/工单/积分/库存…） |
|---|---|---|
| 模糊需求漏什么 | 技术边界：并发、突发、协议字段、失败语义、容量 | 业务语义：规则歧义、状态机分支、角色权限、异常流程、跨实体一致性 |
| 验收依据 | 协议合规 / spec 一致 | 业务正确性（状态流转、权限、规则触发） |
| 适合测 | 需求收敛能否抓技术边界 | 需求收敛能否抓业务规则与状态流转 |

业务类出题要点：fixture 里放一个有业务规则的模型（实体 + 状态字段 + 角色），User Task 给模糊业务需求，planted gaps 藏"未决业务规则"（例：取消后库存何时回滚、驳回能否再审、计费精度与取整、并发下单超卖、权限边界），`checks.sh` 用确定性业务规则测试断言。

> 现有实验（dotenv/bull/oauth2）偏基建；新增实验建议补业务类。上面是领域类别启发，不是指定项目——具体项目按维度自选。

---

## 5. 执行测试用例（跑）

### 5.1 单场景 `run`

```bash
# 机制场景（headless，通常不需 GAUNTLET_ROOT）
bun run src/cli/index.ts run hello-world \
  --agent claude --provider zhipu-glm \
  --plugin-dir "$SEED_KIT_DIR"

# 语义场景（gauntlet，需 GAUNTLET_ROOT）
GAUNTLET_ROOT=/Users/camellia/Personal/Code/claude/gauntlet \
bun run src/cli/index.ts run impl-delivers-project-contract \
  --agent claude --provider zhipu-glm \
  --plugin-dir "$SEED_KIT_DIR"
```

`run` 不接 `--driver/--tier/--gauntlet-root`：driver/eval_kind/task_delivery 从 story frontmatter 读，Gauntlet 靠 `GAUNTLET_ROOT`。`--provider` 是 credential key（§2）。

### 5.2 矩阵 `run-all`

```bash
# sentinel 快速回归
bun run src/cli/index.ts run-all --tier sentinel \
  --agents claude --providers zhipu-glm \
  --plugin-dir "$SEED_KIT_DIR" --jobs 2 --fail-on-nonpass

# core semantic suite
GAUNTLET_ROOT=/Users/camellia/Personal/Code/claude/gauntlet \
bun run src/cli/index.ts run --suite core-semantic \
  --agent claude --provider zhipu-glm \
  --plugin-dir "$SEED_KIT_DIR" --trials 1
```

`run-all` 关键 flag：`--tier`/`--driver` 过滤、`--suite`/`--scenario`（互斥）、`--agents/--providers/--models`（逗号分隔）、`--trials`、`--jobs`（默认 2）、`--baseline <name>`（退化 exit 3）、`--fail-on-nonpass`。

退出码：0=pass/无回归，1=fail，2=indeterminate/致命，3=baseline/Pareto **退化**。

### 5.3 `experiment`：从 spec 到评估（价值对照主路径）

完整流程（review-prd 为例）：

```bash
# 1) 建 manifest（--spec-file 写 design 产出的完整 schema:2 Spec；或用 flag 拼骨架）
bun run src/cli/index.ts experiment create review-prd \
  --spec-file experiments/review-prd/experiment.json
# 或骨架：
bun run src/cli/index.ts experiment create review-prd \
  --title 'PRD 独立评审价值实验' --value-axis review-prd \
  --question '...' --suite review-prd-value \
  --execution-model glm-5.2 --judge-model glm-5.2 \
  --control-plugin-dir packs/seed-kit-no-prd-review \
  --treatment-plugin-dir "$SEED_KIT_DIR"

# 2) 运行（调 execution model，驱动 Coding-Agent；跑 spec 里所有 arm）
GAUNTLET_ROOT=/Users/camellia/Personal/Code/claude/gauntlet \
bun run src/cli/index.ts experiment run review-prd \
  --execution-model glm-5.2 --trials 1 --jobs 1

# 3) 评估（调 judge model，读证据打分；不重跑 Coding-Agent）
bun run src/cli/index.ts experiment evaluate review-prd --judge-model glm-5.2

# 4) 查看 / 浏览
bun run src/cli/index.ts experiment show review-prd
./dashboard/start.sh
```

- `experiment run`：默认按**指纹复用**已有 run group；`--rerun` 强制新建。
- `experiment evaluate`：默认评 latest complete run group；`--reevaluate` 强制重判。
- `create`/`run`/`evaluate` **严格分离**：create 不调模型，run 只调 execution model，evaluate 只调 judge model。

### 5.4 真实交互：Gauntlet QA agent 怎么扮演用户

语义场景（`quorum_driver: gauntlet`）的精髓：**不是一次性把题丢给 agent**，而是 Gauntlet 的 QA agent 扮演真实用户，通过 tmux `--adapter tui` 跟被测 Claude Code **多轮对话**。

- `quorum_task_delivery: gauntlet`（默认）：User Task 由 QA agent 通过**对话消息**交给 Coding-Agent（Coding-Agent 不直接读 story.md）。QA agent 像用户一样发消息、追问、读 session log，再裁定。
- `embedded`：把 User Task 嵌进 CLAUDE.md，无对话交付（仅兼容场景用）。

**QA agent 的行为约束**（runner 注入的 project prompt要点）：第一条消息必须是 User Task 原文，不简化/不发明问题；只用 host bash 检查证据，不替 agent 改文件；agent 停下但未满足 AC 时先追问再判；判 fail 前重读文件系统和 session log。**想测"需求可靠性"，就把 QA agent 当真实用户：用户心里有隐含偏好但嘴上模糊，只在被问到时才透露**——这样能区分"系统性追问收敛需求"的 agent 和"凭直觉猜"的 agent。

**production 三约束**（语义 run 必须）：① 用 canonical 外部 Gauntlet（`GAUNTLET_ROOT` 指向干净 git working tree 的 `bin/gauntlet`）② trusted launcher 对 binary 执行前后双 SHA-256 ③ Claude Code 必须走**真实交互式 TUI**，禁止 `claude -p` 冒充。任一不满足 → `provenance.reproducibility_gaps` 记录。

### 5.5 指纹复用

`run`/`evaluate` 默认按指纹复用 artifact，避免重复烧钱：
- **run 指纹**（`experiment-run-v1`）：manifest hash + scenario tree hash + rubric hash + 各 arm plugin tree digest + execution profile + trials。
- **evaluation 指纹**（`target-evaluation-v2`）：run_group_id + run 指纹 + rubric hash + judge profile + current/reference arm。

用户没说"重跑/重评"就**别加** `--rerun`/`--reevaluate`；先复用，再 `experiment show` 核对。

---

## 6. 价值对照实验（有/无 skill）

> 这是回答"seed-kit 这套到底有没有用"的主路径。

### 6.1 两层问题，两套场景

| 问题 | 工具 | User Task | 通过条件 |
|---|---|---|---|
| skill 接线对不对 | **机制哨兵** | 可点名 skill | checks 可断言 skill 调用 |
| 有 skill 是否更好 | **outcome 场景 + 两臂** | **中性** | **只看 outcome**，不把"调了 skill"当 pass |

同一能力域通常两套都要：哨兵保接线，价值实验保增益。

### 6.2 三臂 + reference_arm 规则

| 臂 | 含义 | label 建议 | plugin |
|---|---|---|---|
| control | 没有目标 skill 的基线 | `control-no-<skill>` | 裁剪 pack |
| treatment | 当前完整机制 | `treatment-with-<skill>` | 完整 seed-kit |
| candidate | 改 skill 后的版本 | `candidate-<skill>-vN` | 改过的 plugin 目录 |

`reference_arm` 规则：control **不能**有 reference_arm；treatment/candidate **必须**有，且指向已存在的 arm（一般 control）；非 sentinel 策略需 ≥2 arm + 含 control。正式比较：同 suite / 同 provider/model / 同 trials，**只动 label + plugin-dir + description**。

### 6.3 control pack 怎么搭

放 `packs/<pack-id>/`，用 `packs/build-<pack-id>.sh` 从完整 seed-kit **rsync 后只删目标能力入口**（见 `packs/build-seed-kit-no-prd-review.sh`）：

```bash
rsync -a --exclude node_modules --exclude .git "$SRC/" "$DST/"
rm -f "$DST/commands/review-prd.md"          # 只删目标入口
rm -f "$DST/agents/seed-prd-review.md"
# soft-disable 交叉引用：改其它 skill 里"建议调用 review-prd"为占位说明
```

**control 不能删光整个插件**——删光就变成测"有没有插件"而不是"有没有该 skill"，且 control 主动 coach 缺失能力会污染对照。保留其它工作流，让唯一变量是目标 skill。

### 6.4 outcome 场景怎么写

- frontmatter 加 `experiment_role: outcome` / `value_axis: <轴>` / `code_context: with_code|no_code|mixed`。
- User Task **中性**（§4.6），planted gaps 藏 author-only 段。
- `checks.sh` 的 `post()` **禁止**断言 skill 调用，只盯产物/边界；顶部加 `# red-fixture: skip`。
- `rubric.json`（`target-evidence-v1` 协议）声明打分轴，见 §7.1。

### 6.5 suite + labeled run-all

```bash
# control
GAUNTLET_ROOT=... bun run src/cli/index.ts run-all \
  --suite review-prd-value --agents claude --providers minimax --models grok-4.5 \
  --label control-no-prd-review --description '无独立 PRD 评审的基线' \
  --trials 1 --jobs 1 --plugin-dir ./packs/seed-kit-no-prd-review \
  --results ../seed-kit-eval-runs

# treatment（换 plugin-dir + label）
... --label treatment-with-prd-review --plugin-dir "$SEED_KIT_DIR" ...
```

labeled 模式硬约束：`--label`+`--description` 同时给；单一 `--suite`、单一 agent/provider/model；不能与 `--baseline`/`--scenario` 同用。目录布局：`<results-base>/<suite>/<provider>--<model>/<label>/`。

> `run-all --label`（按臂分别跑）和 `experiment create/run/evaluate`（一次跑所有臂）是价值对照的两条等效路径。experiment 系统（schema:2 Spec）更新、更适合多臂 + rubric 判分；labeled run-all 更接近旧矩阵习惯。

### 6.6 seed-eval design 阶段（怎么设计一个实验）

调 `seed-eval` skill 进 design，产出可评审的 Experiment Spec 草案（**人不确认不落盘、不跑模型**）。策略路由：

| 变更类型 | `strategy.type` | 主 outcome |
|---|---|---|
| 入口/委托/边界接线 | `sentinel` | 是否按设计走 |
| 新能力"有没有用" | `value_ab` | 任务结果是否更好 |
| 同能力换策略 | `strategy_ab` | A/B 结果与稳定性 |
| gate/hook 松紧 | `gate` | 该拦拦、该放放 |
| 交互澄清类 | `interaction` | 产物质量 |

**红线**：design 未确认不跑模型；control 不删光整个插件；`minimum_valid_pairs ≤ trials`；不把"调用了某 skill"当价值主指标；schema:2 Spec 必须有可渲染 presentation；非 sentinel 需 ≥2 arm + control + reference_arm。

Spec schema:2 必填顶层字段：`schema`/`id`/`title`/`value_axis`/`question`/`suite`/`scenarios[]`/`arms[]`/`defaults`/`subject`(kind/plugin/skill_ids/related_agents/related_commands/change_summary)/`strategy`(type+rationale)/`presentation`(template+conclusion.cards)。可选 `research`(hypothesis+not_measuring)、`task_plan`(source_policy/difficulty/tiers/oss_refs)、`rubric_protocol`(默认 target-evidence-v1)。完整样例见 `experiments/review-loop-impl-quality/experiment.json`。

---

## 7. 看结果（判分三层 + 读产物）

判分是**三层**，别混：

```
单次 attempt → 1. 硬判定 (checks.sh + composer.ts)：pass / fail / indeterminate
batch/arm   → 2a. score (scoring.ts)：四轴 + Pareto（不调 LLM，纯确定性）
             2b. evaluate (experiments/evaluate.ts)：rubric + judge 调 LLM 打 0-100
跨 batch    → 3. baseline diff / narrate / dashboard
```

### 7.1 三层各是什么

**① 硬判定**（`verdict.json.final`）：
- `pass`：driver 通过 + 无 post-check fail（且需要 witness 时有确定性 post 断言）
- `fail`：driver 失败 或 post-check 有 fail
- `indeterminate`：**基础设施故障**（runner error / broken check / pre-check fail / witness 缺失）。**绝不把基础设施失败包装成行为 pass/fail**。

**② score 四轴**（确定性，不调 LLM）：`function`(40%) / `methodology`(25%) / `efficiency`(20%) / `robustness`(15%)。四轴不全测出来时**不给虚假总分**（显示"未评分"）。`--baseline` 时做 Pareto 退化检查。

**③ evaluate rubric**（调 judge，`target-evidence-v1`）：每个 scenario 一份 `rubric.json`，声明若干 `target`（判分轴），judge 读证据给 0-100 + narrative，聚合成 control vs treatment 的 `comparison`。

rubric 关键概念：
- `dimension` 是**受控 enum**（`code_reconciliation`/`serious_gap_coverage`/`evidence_quality`/`decision_quality`/`severity_calibration`/`gate_correctness`/`boundary_compliance`），新 dimension 必须先在 `docs/rubric-field-contract.md` §2.1 和 `dashboard/catalog.mjs` 注册。
- `severity`(blocking/major/minor/decoy) + `weight` + `mandatory` 收敛为 P0-P3 单 badge；**不要让用户同时看到 severity 和 weight**。
- 每个 target 带 `bands[]`（`range`/`label`≤4字/`description`行为句≤35字+≤1代码锚/`tone`），必须可渲染。

### 7.2 怎么读结果

```bash
bun run src/cli/index.ts show results/<run-dir>            # 单次 verdict
bun run src/cli/index.ts experiment show <id>              # manifest + run groups + evaluations (JSON)
bun run src/cli/index.ts score --from results/<batch> --tier regression
./dashboard/start.sh                                        # 浏览
```

**调查失败的读取顺序**：
1. `verdict.json` → `final`/`final_reason`/`error.stage`/`gauntlet.status`
2. `provenance.json` → `reproducibility_gaps`（dirty tree / production Gauntlet not used / TUI evidence 不全）
3. `checks-runner-{pre,post}.json` → 哪条确定性 check 失败
4. `batches/<batch-id>/results.jsonl` + `stability.json` → 跨 attempt 是否系统性
5. experiment 模式：`run-group.json`(status/各 arm summary) → `evaluation.json`(`comparison.conclusion`/`metrics`/`sample_sufficiency`) → `judgments/<arm>/<scenario>-trial-<n>.json`(`overall_decision`/`target_judgments[].status`/`narrative`)

**只看 CLI exit code 不够**；缺失 artifact 不代表通过。

### 7.3 关键产物目录

单场景 run bundle：`verdict.json` / `provenance.json` / `checks-runner-{pre,post}.json` / `transcript.txt` / `trajectory.json` / `coding-agent-token-usage.json` / `coding-agent-workdir/` /（gauntlet）`gauntlet-agent/results/<run-id>/{result.json,result.md}`。

experiment 模式：`results/experiments/<id>/run-groups/run-<ts>-<fp>/` 下 `run-group.json` + `arms/<arm>/batches/.../<run-bundle>` + `evaluations/eval-<ts>-<fp>-<arm>/{evaluation.json, judgments/<arm>/<scenario>-trial-<n>.json}`。

### 7.4 dashboard

```bash
./dashboard/start.sh [--results <base>] [--port <n>]      # 默认读 ../seed-kit-eval-runs，port 3000
./dashboard/stop.sh
```

口径：invalid attempt 不进 pass-rate 分母；同执行身份（suite+provider/model+agent+driver+场景集+trial）才并排比较，**不做跨模型排名**；plugin/candidate revision 不进 identity（同模型换 plugin 版本能并排）；缺 `score.json` 显示"未评分"。

---

## 8. 命令速查（按用途）

> 所有命令在 `$SEED_EVALS_DIR` 跑：`bun run src/cli/index.ts <cmd>`。语义场景加 `GAUNTLET_ROOT=...`。

**出题/校验**：`new <id>` · `check [name]` · `check-red [name] --plugin-dir <dir>` · `list`

**执行**：`run <scenario> --agent claude --provider <key> --plugin-dir <dir>` · `run-all [--tier|--driver|--suite|--label|--trials|--jobs|--baseline|--fail-on-nonpass]` · `experiment create/run/evaluate/show/list` · `dashboard`

**判分**：`score --from <batch> [--baseline <name>]` · `narrate --from <dir> [--reviewer <key>]` · `experiment evaluate --judge-model <profile>`

**看结果**：`show <run-dir>` · `experiment show <id>` · `baseline save/diff <name>` · `jobs list/show/cancel`

**自进化**（分阶段报告链，均接 `--from <run|batch|report>`）：`capture` → `analyze` → `hypothesize` → `validate` → `evolve`；隔离修复：`evolve --repair --plugin-repo <dir> --plugin-dir <dir> --credential <key> --baseline <name> [--gauntlet-root <dir>]`

> ⚠️ **`--execute` 已 fail-closed 废弃**（任何 stage），唯一合法继任是 `evolve --repair`；`--repair` 是 `evolve` 专属，其它 stage 加会报错。`capture/analyze/hypothesize/validate` **没有废弃**，是报告链的一环。

---

## 9. 失败归因 + 自进化

**先归因，再决定改哪里**（seed-kit 哲学：机制在插件，标准在项目）：

| 失败原因 | 改哪里 |
|---|---|
| 跨栈都成立的机制坏了（done gate、checkbox guard、skill 该读 PRD 却不读） | **改 seed-kit** |
| 场景要求了 seed-kit 不承诺的强标准（某栈 UI/a11y/具体工具名） | **改 scenario**，不改插件 |
| setup/check/gauntlet 坏了 | **改 seed-kit-evals** |
| 项目缺测试/质量命令 | 正确行为可能是**报告缺口**，不是插件发明标准 |
| 单模型偶发 | 记 backend signature，不为单一模型过拟合 |

归因链：`capture → analyze → hypothesize → validate → evolve`（分阶段写报告，不改生产插件）。确认是插件问题且要自动提修复：

```bash
bun run src/cli/index.ts evolve --repair \
  --from <report-or-batch> --baseline <name> \
  --plugin-repo "$PLUGIN_REPO" --plugin-dir "$SEED_KIT_DIR" \
  --credential zhipu-glm --provider zhipu-glm \
  --core-suite core-semantic --gauntlet-root "$GAUNTLET_ROOT"
```

候选修复**只产 patch + evidence**，绝不 apply/commit/push/branch/自动存 baseline；最终只 `eligible_for_review` / `rejected` / `inconclusive`。`eligible_for_review` 只允许人工审阅，不代表自动合入。

---

## 10. 安全边界（红线）

- production 语义 run 只信任 canonical 外部 Gauntlet + 真实 Claude TUI + 真实 scenario checks；**不得用 `claude -p` 冒充**。
- provider 配置**只读**，不修改/复制 credential、token、base URL。
- 不修改用户 source checkout 制造通过结果。
- **不自动** apply/commit/push/branch/保存 baseline。
- sandbox/publication/source invariant 任一证据缺失 → **fail closed**。
- 历史 results 不得擅自删除/redact/quarantine。
- 本地 eval artifacts 不再执行 provider secret 扫描，也不会因 provider-like 字符串改写 verdict。

---

## 11. 给 AI 的操作纪律

1. **改 skill 时 cwd = 本插件目录；跑评测时 cwd = `$SEED_EVALS_DIR`。**
2. **始终显式传 `--plugin-dir "$SEED_KIT_DIR"`**，否则在测"裸 Claude"，不是 seed-kit。
3. 语义场景先确认 `GAUNTLET_ROOT` 可用；没有 Gauntlet 时只能跑 headless/机制。
4. 先读 `verdict.json` + checks receipt 再下结论；空 transcript / setup 失败 → `indeterminate`，不是插件"坏了"。
5. **不要把一次失败立刻固化成 skill 永久规则**（见 `.claude/rules/workflow-design.md`：不为一次失败加长期负担）。先归因。
6. 改 prompt/skill 前优先看能否用**机制层**补强（helper/hook/契约），而不是堆枚举。
7. agent **不自动 commit** 评测或插件改动；提交由人决定。
8. 成本：full gauntlet 矩阵昂贵；日常 sentinel + 单场景，发版再 regression/full。

---

## 12. 相关文件索引

**本插件**：[`README.md`](./README.md)（用户向）· [`DESIGN.md`](./DESIGN.md)（设计原则）· [`CLAUDE.md`](./CLAUDE.md)（栈无关判定式）· `skills/` `tools/` `hooks/` `agents/`（被测实现）

**seed-kit-evals**：
- CLI：`src/cli/index.ts`
- 场景/suite：`scenarios/` · `suites/`
- 执行：`src/runner/` · `src/experiments/{contracts,create,run,evaluate,registry}.ts`
- 判分：`src/composer.ts`（硬判定）· `src/scoring.ts`（四轴）· `src/checks/{prelude.sh,index.ts,red-fixture.ts}` · `src/check/dispatch.ts`
- config：`config/model-profiles.json`（execution/judge profile）· `credentials.yaml`（credential key）
- 文档：`EVALUATION_GUIDE.md`（怎么跑/安全边界）· `docs/experiment-system.md`（实验系统）· `docs/scenario-authoring.md`（场景人读合同）· `docs/value-experiment-authoring.md`（价值实验）· `docs/rubric-field-contract.md`（rubric 字段）· `docs/scoring-design.md`（评分设计）
- control pack：`packs/`（含 `build-*.sh` 重建脚本）
- 看板：`dashboard/start.sh`

**规则（改插件前必读）**：`.claude/rules/workflow-design.md` · `.claude/rules/prompt-design.md`

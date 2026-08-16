---
name: seed-eval
description: "为任意一次插件技能更新,因地制宜设计评估(design)并执行(lab)。design 产出可评审的 Experiment Spec;lab 用 seed-kit-evals-v2 创建/运行/评估/展示。默认不跑模型,等人确认。"
---
# Seed Eval(v2)

两段式:**design**(设计评估,产出 Experiment Spec 草案)+ **lab**(创建/运行/评估/展示)。

- 用户说"我要改 X 技能 / 验证 X / 对比 A vs B" → 进 **design**,不要直接跑。
- 用户说"跑 / 评估 / 看 Dashboard" → 进 **lab**。

## 实验室在哪(v2)

- 仓库:`/Users/camellia/Personal/Code/claude/seed-kit-evals-v2`;入口 `bin/seed-evals`(任意 cwd 可用)。
- 快速上手:插件目录 `plugins/seed-kit/EVALS.md`;完整手册:v2 仓库 `EVALS.md`;活跃资产与理由:v2 仓库 `scenarios/MANIFEST.md`。
- 环境默认值在 v2 的 `config/local.json`;开跑前 `seed-evals doctor` 自检,场景合同以 `seed-evals check` 为准。

## 建一道测试用例(骨架)

判断类型 → 写三件套(story/setup/checks)→ `check` + `check-red` → 按类型跑 → 看结果 → **结账**。

| 要测什么 | 类型 | 跑法 |
|---|---|---|
| CLI/hook/runner 活着 | infra 冒烟(headless) | `seed-evals sentinel` |
| 完整工作流行为质量 | 全流程旅程(gauntlet) | `seed-evals run --suite core-semantic --agent claude` |
| 有/无某能力、改前/改后是否更好 | 效果对比实验 | candidate pack + spec → `seed-evals value <exp-id>` |

**套件方向(用户定)**:不做"每 skill 每触发点"微点覆盖;一道题的合格标准是**能区分好坏实现**。出题前先回答"这道题区分什么差异",答不出不进活跃套件。价值/outcome 场景:User Task 中性不点名 skill、planted gaps 藏 author-only 段、checks 不把 skill 调用当 pass、顶部 `# red-fixture: skip`。选题基建类与业务类搭配。

**checks 别代理 hook 已守的底线**:手工改 prd.md checkbox 已被 `seed_guard` hook 在编辑时拦掉(结构性发生不了),checks.sh 不要用"无 `### [x]` / `* [x]`"断言"未手工翻"——`seed done` 原子翻 slice 头与区段内 item,`[x]` 是合法终态,这类断言只会假阳性。要断言"某 slice 经 seed done 关闭",查 `done-logs/*<slice>*` 存在(gate 的硬留痕)。

## design 阶段

目标:产出可评审的 Experiment Spec 草案(schema:2)。**人不确认不落盘、不跑模型。**

1. 摄入变更(描述/skill 文件/diff);先查仓库现有资产,不问用户。**先翻 v2 各实验的 `CONCLUSION.md`——已被证伪的方向(拆脚手架、加全景层等)不要重复设计。**
2. 策略路由:接线 → `sentinel`;新能力有没有用 → `value_ab`;同能力换策略 → `strategy_ab`;gate 松紧 → `gate`;交互澄清 → `interaction`。
3. 研究问题写成三向可证伪(更好/持平/更差都改变决策);candidate 变体用 `packs/build-*.sh` 从现行插件确定性生成。
4. 用户确认 → 落盘 `experiments/<id>/experiment.json`。

红线:design 未确认不跑模型;control 不删光整个插件;不把"调用了某 skill"当价值主指标;非 sentinel 需 ≥2 臂 + control + reference_arm;`minimum_valid_pairs` ≤ trials。

## lab 阶段

```bash
seed-evals doctor                      # 环境自检
seed-evals value <exp-id> --jobs 1     # run + evaluate 一条命令(模型/trials 用 config 默认)
seed-evals experiment show <exp-id>    # 看 manifest / run groups / evaluations
seed-evals stability                   # infra 失败率聚合
./dashboard/start.sh                   # 浏览
```

- 长实验(>40 分钟)用 `nohup ... & disown` 脱离会话跑,日志落文件后轮询。
- 低并发(jobs ≤2),避免与其他在途测试抢 provider 配额。
- **结账纪律**:实验跑完必须写 `experiments/<id>/CONCLUSION.md`(结论 + **它打败了什么**——alternatives considered 及胜出理由,防重新审判 + 由此采取的动作);不合并的 candidate 归档 spec+结论、删 pack 副本(build 脚本保留可重建)。

## v1 回退说明(如果 v2 不好用)

v1 实验室完整保留、未被改动,随时可切回:

- 仓库:`/Users/camellia/Personal/Code/claude/seed-kit-evals`(Bun,入口 `bun run src/cli/index.ts`)
- 操作手册:插件目录 `plugins/seed-kit/EVALS_V1.md`(600 行完整版,场景三件套/checks DSL/experiment/归因链全部适用)
- v1 用法差异:需手工 `export PATH="$HOME/.bun/bin:$PATH"`、cwd 必须在 v1 仓库、`GAUNTLET_ROOT` 手工 export、`--plugin-dir` 每次显式传;无 doctor/sentinel/value/stability 短命令,无 infra 自动重试
- v1 的 84 个场景与 9 个实验原样在库;v2 归档的场景在 v2 的 `scenarios/_archived/` 也可召回

"用 X 跑"中的 X 是 execution model;"用 X 评估"中的 X 是 judge model。

# seed-kit 评估使用说明(v2)

> 给以后使用本插件的 AI / 人类:测本插件行为、验证 skill 改动效果,用 **seed-kit-evals-v2**。
> 本文是快速上手;完整手册在 evals 仓库的 `EVALS.md`,场景合同的唯一裁判是 `seed-evals check`。

## 1. 在哪里

| 仓库 | 路径 | 角色 |
|---|---|---|
| 本插件(被测对象) | `/Users/camellia/Personal/Code/claude/claude-plugins/plugins/seed-kit` | skill / hook / CLI / agents |
| **seed-kit-evals-v2**(实验室) | `/Users/camellia/Personal/Code/claude/seed-kit-evals-v2` | 场景 + runner + 判分 + 实验 |
| gauntlet(语义场景依赖) | `/Users/camellia/Personal/Code/claude/gauntlet` | QA agent 多轮 TUI 驱动 |

入口:`<evals-v2>/bin/seed-evals`,任意 cwd 可用(可 symlink 进 PATH)。旧仓库 seed-kit-evals(v1)与 [`EVALS_V1.md`](EVALS_V1.md) 是历史资料,新工作不要用。

## 2. 一次配置

evals-v2 的 `config/local.json`(gitignore)承载所有默认值,配好后日常零手工 env:

```json
{
  "seed_kit_dir": "<本插件目录>",
  "gauntlet_root": "<gauntlet checkout>",
  "provider": "grok",
  "execution_model": "grok-4.5",
  "judge_model": "grok-4.5",
  "credentials_path": "<现有 credentials.yaml 的只读引用>"
}
```

CLI flag 始终覆盖配置;credentials 只读引用,绝不复制。

## 3. 日常四条命令

```bash
seed-evals doctor      # preflight 自检:环境坏了 3 秒内报人话错误 + 修法
seed-evals sentinel    # 日常回归:doctor + headless 冒烟(约 1 分钟)
seed-evals run --suite core-semantic --agent claude   # 全流程旅程(gauntlet 真实多轮交互)
seed-evals value <exp-id>   # 效果对比实验:run + evaluate 一条命令
seed-evals stability   # 聚合 results:哪层最常坏,infra 失败率
```

`run`/`run-all`/`experiment run` 入口自动 preflight;infra 类 indeterminate 自动重试(≤2 次),行为 fail 绝不重试。

## 4. 套件哲学(改 skill 前必读)

不做"每 skill 每触发点"的微点覆盖。三层活跃资产(明细与每个的存在理由见 evals-v2 的 `scenarios/MANIFEST.md`):

- **全流程旅程**(suite `core-semantic`,4 个):brainstorm→PRD 评审→impl→review-loop 的端到端行为质量
- **效果对比实验**(4 个 spec):有/无某能力、改前/改后,必须能跑出差异化
- **infra 冒烟**(5 个 headless):只保证 doctor/gate/hook/runner 活着

一道题的合格标准是**它能区分好坏实现**。出题三件套(story/setup/checks)与 frontmatter 合同见 evals-v2 `EVALS.md` §3,写完必过 `seed-evals check` + `check-red`。

## 5. 改了 skill 之后怎么验证

1. 改动在本插件目录完成,插件 pytest 先绿:`python3 -m pytest tests/ -q`(含 prompt 合同测试)。
2. `seed-evals sentinel` 秒级回归。
3. 行为影响面大时跑 `seed-evals run --suite core-semantic`。
4. 想知道"改了有没有更好":做 candidate pack(`packs/build-*.sh` 从现行插件确定性生成变体),写 experiment spec(参考 `experiments/*/experiment.json`,schema:2),`seed-evals value <exp-id>`。
5. **结账纪律**:实验跑完必须写 `experiments/<id>/CONCLUSION.md`(结论 + 采取的动作)。没结账的实验视为纯成本。历史结论都在各 CONCLUSION.md——**动手改 prompt 前先翻它们**,已被证伪的方向(如"拆脚手架""加全景层")不要重复试。

## 6. 失败先归因再动手

| 原因 | 动作 |
|---|---|
| infra 抖动(自动重试后仍挂) | `seed-evals stability` 看是否系统性;修环境不改场景 |
| 场景质量(断言过时/区分不出差异) | 改场景,重过 check |
| 插件行为真变了 | 回本目录修 skill,再用对应实验验证 |
| harness 坏了 | 修 evals-v2,bun test 守住 |

## 7. 红线

语义场景必须 Gauntlet 真实 TUI,不得 `claude -p` 冒充;credentials 只读;不自动 commit/push/branch;v1 仓库只读;始终确认 plugin-dir 生效(否则测的是裸 Claude)。

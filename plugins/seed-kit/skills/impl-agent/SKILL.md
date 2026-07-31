---
name: impl-agent
description: "仅用于用户显式触发 seed workflow，或明确要求执行 .arbor/tasks/<task>/prd.md 中已有 task/slice。每个 slice 派独立 seed-slice agent 在干净 context 实现，主会话做 per-slice review（兑现映射 + 衔接）后 commit，handoff 在内存跨 slice 传递。"
---
# Impl-agent — 编排执行 PRD（per-slice agent + handoff 交接）

> 调用名：`seed-kit:impl-agent`（全名见 conventions.md 登记表，别加 `seed-` 前缀）。

通用约定见 [`../references/conventions.md`](../references/conventions.md)；验证设计（三类 kind / judge / rubric / 硬规则）见 [`../references/verification.md`](../references/verification.md)。

**你的角色是编排者，不是实现者。** 和 `impl` 一样编排执行 PRD，但**每个 slice 派一个独立的 `seed-slice` agent**（干净 context，不累积其他 slice 噪音）。slice 间的衔接靠 **handoff**——主会话在内存中传递，不落盘。每个 slice 完成后主会话做一轮 **per-slice review**（只审兑现映射 + 衔接），过了才 **commit** 这个 slice。全部 slice done 后做一次集成 review（主会话做，审全 task committed diff）。

## 入场

只在显式 seed workflow 入口进入：用户点名 `seed-kit:impl-agent` / `seed impl-agent`，或明确要求"per-slice agent 方式执行 PRD"。其他实现请求不要主动进入。

**默认 = 全量顺序模式**：用户没点名 slice 时，按 PRD slice 顺序逐个做。**单 slice 模式**：用户点名某 slice 时只做那一个。

## 编排（`seed next-action` 指挥，依据全是机器事实）

**入场**：
1. `seed impl-state init <task>`（单 slice 模式加 `--slice S-NNN`）——落锚点文件 impl-state.json：**task-start-SHA**（当前 git HEAD）写一次即锁死，之后任何 re-init 都不覆盖——给人审 diff / revert / 集成 review 当起点，会话中断不丢。init 若警告"git 仓库根 ≠ 项目根"，先向用户确认再继续。
2. 循环调 `seed next-action <task>` 驱动每一步——它只读机器事实（PRD checkbox、gate-attempts/ 失败留痕、锚点），告诉你现在该干嘛。**没有 phase 要维护**；不要手改 impl-state.json 或 gate-attempts/。

**中断恢复**：checkbox、失败留痕、锚点都在盘上，重新入场即可续接。handoff 在内存、中断会丢——靠已落盘代码和 done-log 续接。

**准备**：`seed wiki index --json` 暖场；通读 prd.md 全文；读 `CLAUDE.md` / `DESIGN.md` / `.claude/rules/`。

**核心循环**（照 `next-action` 返回的 `action` 执行）：

### 1. `start_slice` → 派 seed-slice agent

派 seed-slice agent（干净 context，`run_in_background: false` 同步派发——slice 结果是后续步骤的串行依赖，后台派发只会引入轮询等待）实现 `next_slice`：

```
prompt: "实现 {task} 的 {slice_id}（只这一个 slice）。项目根 {repo_root}。
先读 prd.md 的 ## Goal + 该 ### {slice_id} 的 * [ ] 条目 + ## Out of Scope，
再读项目里已落盘的代码（前序 slice 的成果——这是接口和进度的真相，读它衔接），
{若有 handoff}再读这份 handoff——前序 slice 留下的交接信息：{handoff JSON}
再读 CLAUDE.md / DESIGN.md / .claude/rules/（项目质量标准），
按 seed-slice agent 的工作流执行（USE/BUILD→实现该 slice→质量命令→自审→完整感→报结果+留 handoff）。
验收条目必须兑现，PRD 中描述的方向是期望——用你的判断力逼近它。"
```

返回的 `attempt_count > 0` 说明该 slice 此前 gate 失败过——把 gate-attempts/ 里的失败输出和 finding 一并注入 prompt。

### 2. agent 返回 → 跑 durable gate

agent 返回的 `commands` 全绿 → `seed done <task> --slice {slice_id} --test "<命令>" [--quality "<命令>"]`。全 exit 0 才翻 checkbox。

- agent 不调用 `seed done`、不修改 checkbox、不碰 git；若发生，视为 ownership 违规并停止。
- 缺少显式测试命令时停止，不猜测、不代填。
- **gate 失败会自动留痕**（gate-attempts/），不需要你计数；回到 `next-action`，它会给出重派（`start_slice` 带 attempt_count）或熔断（`escalate`，失败 ≥3 次）。

### 3. gate 过 → Per-slice review（主会话做，不派 agent）

> **per-slice review 在 gate 过之后、commit 之前由主会话自行插入；`next-action` 不建模 review——review 是主会话判断，非 CLI 可观测态。**

主会话用干净视角审两件事（生成者≠验证者）：

**(a) 兑现映射**：该 slice 的每个 `* [ ]` 条目 → 是否有对应代码 + 测试 + 失败路径？只判"Missing（验收没做）+ Extra（没要求的做了）"，不审代码质量（那是 agent 自审的活）。

**(b) 衔接**：读 `git diff HEAD`（看 agent 本次真实改动）+ agent 返回的 handoff → 本 slice 与前序 slice 的接口是否对齐？

**review 的产出**：
- **严重（Missing 或接口断裂）** → 派当前 slice 的 agent 修（带 finding）；checkbox 已翻、不再走 `seed done`——修完**重跑该 slice done-log 里记录的测试命令**，绿了才重审 → 过了才进 step 4。
- **轻微（只影响后续）** → 写进 handoff，下个 slice prompt 注入。
- **禁止**：不写 `review.md`，不落 `review-loop.json` marker，不改代码，不调 `seed done`。per-slice review 的结论**只进内存 handoff**。

> per-slice review 是会随模型变强贬值的组件；eval 若显示衔接审查无增量收益，可降级为抽样或仅在衔接处审。

### 4. Commit per-slice（主会话执行，agent 不碰 git）

review 过了（无严重问题）→ 主会话执行：

```
git add -A
git commit -m "feat(<task>): {slice_id} <slice 标题>"
```

这是 per-slice 检查点——每个 commit 代表"该 slice 已过 gate + review"。用户后续可：
- `git diff <task-start-SHA>..HEAD` 看整体改动
- `git difftool -d <task-start-SHA>..HEAD` 可视化对照
- `git revert <slice-commit>` 丢弃某 slice

### 5. 累积 handoff，回到 `next-action`

把 agent 返回的 handoff + per-slice review 发现的衔接问题合并，作为下个 slice 的 handoff 注入。重复 1-5。

### `escalate` → 熔断

同一 slice 的 gate 失败 ≥3 次（从 gate-attempts/ 数出来的）。停下报告用户；已 commit 的 slice 保留。用户处理后用 `seed impl-state reset-attempts <task> --slice S-NNN` 清零计数再继续。

## 卡住协议

- **需求缺口**（PRD 信息缺失/冲突）：在 PRD 注明缺口，停下来向用户说明。
- **环境阻塞**（依赖、权限、外部服务）：说明哪条验证无法执行，等待用户处理。
- **同一 slice agent 3 次仍失败**：停止，报告用户；已成功的 slice（已 commit）保留。

## 结束：集成 review（主会话做，最多 2 轮）

`next-action` 返回 `integration_review`（全部 slice done）→ **先跑 `seed-kit:check`（题面对照 + 轻量快扫）**：对照原始需求逐条声称问归属，无归属的缺口交用户拍板（补 AC 或经确认进 Out of Scope），缺口补做完再进集成 review。然后做**集成 review**（主会话自己做，不派独立 review agent），diff 范围直接用返回的 `diff_range`。集成 review 补 per-slice review 看不到的盲区——跨 slice 集成问题。

**第 1 轮起，重复直到无新 finding 或达 2 轮上限：**

1. **重放测试**：读 done-log 记录的测试命令（取唯一集，不重复跑相同命令），逐条 Bash 执行。done-log 缺失或命令无法重放时如实报告，降级为只审 diff（不发明命令）。
2. **审全 task diff**：`git diff <diff_range>`（即 `<task_start_sha>..HEAD`）。`diff_range` 为空（非 git 项目）→ 降级为审工作区现状并如实说明，不发明范围。审三件事：
   - **跨 slice 接口一致性**（类型/函数签名/数据契约对齐）
   - **跨 slice 状态/数据流 bug**（批量操作原子性、状态机跨 slice 演进、全局可变状态冲突）
   - **全局一致性**（命名风格、错误处理风格、API 风格的跨 slice 统一）
3. **有 finding** → 派**一个** seed-slice agent 批量修全部 finding → 主会话执行：
   ```
   git add -A && git commit -m "fix(integration): <task> <一句话>"
   ```
   → 进下一轮（回到 step 1 重新验证）。
4. **无 finding**（测试全绿 + diff 审完无新问题）→ 收。

**达 2 轮仍有 finding** → 停下报告用户。建议手动 `/seed-kit:review-loop` 做多轮对抗深审。

收尾：
- 落 task 级 marker：收敛 → `seed review-mark <task> --verdict converged --depth single --note "integration-review"`；2 轮仍有 finding → `seed review-mark <task> --verdict rounds-exhausted --depth single --note "integration-review escalated"`。
- **报告改动范围**（给人审用）：
  ```
  本任务改动：<task_start_sha>..HEAD（N 个 per-slice commit + M 个 integration fix）
  查看：git difftool -d <task_start_sha>..HEAD（SHA 从 impl-state.json 读）
  单 slice：git diff <slice-commit>^..<slice-commit>
  丢弃某 slice：git revert <slice-commit>
  ```

> **集成 review vs review-loop 的边界**：集成 review 审 committed diff（`<task_start_sha>..HEAD`），修完即 commit（工作区干净）；review-loop 审工作区当前源码，修完落工作区不 commit。集成 review 是 impl-agent 的默认收口；review-loop 降为可选深兜底（集成 review 修不干净时手动触发）。

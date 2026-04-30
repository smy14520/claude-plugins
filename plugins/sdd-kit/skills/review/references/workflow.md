# Review workflow notes

Review 是 package/T-xxx semantic audit，不是普通 code review。主文件 `SKILL.md` 是权威说明；本文件只保留执行时容易漏的细节。

## 收集

- 解析目标：package + package-local T-xxx / 最近 DONE；裸 `T-001` 不是全局唯一任务。
- 读取 `.arbor/tasks/<name>/prd.md`、`task.md`、`task.json`、可选 `context/review.jsonl`。
- 必须检查 actual `git diff`，并明确当前 T-xxx 对应的 diff scope。
- 可选查 `.wiki` / `sdd-arbor wiki-collect`，但 wiki 只作 orientation。
- 若缺 `prd.md`，legacy `.arbor/brainstorms/<name>.md` 只能作为 fallback，并在报告中标为迁移风险。

## 判定

按 `SKILL.md` 的 review lenses 选择重点，不机械逐项输出。APPROVED 必须至少说明：

- goal / scope 已对齐；
- task acceptance / context 已检查；
- diff scope 清楚且无阻塞越界；
- 关键测试 / 回归证据足够或说明为何不需要。

## 报告

审计正文默认中文，不使用 `Verdict` / `Findings` / `Evidence` 等英文 rubric。推荐结构：

```md
结论：NEEDS_REWORK。<一句话说明>

问题清单：

1. 中等 — <问题>
   - 证据：<文件路径 / 命令 / diff 事实>
   - 影响：<为什么影响 package / T-xxx / 验收>
   - 建议处理：<下一步>

通过检查：

- <已确认通过的关键点>
```

下一步指引：

- APPROVED → 当前 T-xxx 通过；若所有 required T-xxx 都通过 review，package 可进入 PR/final review。
- APPROVED_WITH_NOTES → 当前 T-xxx 可计入 package readiness，但建议 follow-up。
- NEEDS_REWORK → 回 `/sdd-kit:impl` 处理当前 T-xxx。
- BRAINSTORM_DRIFT → 回 `/sdd-kit:brainstorm` 追加 package-local `AMD-xxx`；若边界变化，回 map/user。

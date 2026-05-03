# Review workflow notes

Review 是 package PRD semantic audit，不是普通 code review。主文件 `SKILL.md` 是权威说明；本文件只保留执行时容易漏的细节。

## 收集

- 确认 package；裸 slice 名称不是执行单元。
- 读取 `prd.md`、`task.json`、impl evidence 和 actual `git diff`。
- 检查 PRD `## Slices` 与实际实现进度是否一致；slice 标记是线索，代码和 diff 才是事实。
- 可选查 `.wiki` / `sdd-arbor wiki-collect`，但 wiki 只作 orientation。
- 若缺 `prd.md`，legacy `.arbor/brainstorms/<name>.md` 只能作为 fallback，并在报告中标为迁移风险。

## 判定

按当前 diff 选择重点，不机械逐项输出。APPROVED 至少说明：

- PRD goal / scope 已对齐；
- Acceptance Criteria 与 Technical Framing 已满足；
- `## Slices` 描述的实现闭环已完成；
- impl evidence 和 self-check 能支撑 DONE；
- diff scope 清楚，没有越界或破坏 out of scope；
- 关键测试 / 回归证据足够，或说明为何不需要。

如果 PRD + impl evidence 足够证明当前 scope，则可以 APPROVED。若 impl evidence 无法映射到 acceptance，通常是 NEEDS_REWORK。若 PRD 本身错误、失效或与当前 repo 脱节，才是 BRAINSTORM_DRIFT。

## 报告

审计正文默认中文。推荐结构：

```md
结论：NEEDS_REWORK。<一句话说明>

问题清单：

1. 中等 — <问题>
   - 证据：<文件路径 / 命令 / diff 事实>
   - 影响：<为什么影响 package / 验收>
   - 建议处理：<下一步>

通过检查：

- <已确认通过的关键点>
```

下一步指引：

- APPROVED → 当前 package PRD scope 通过 review。
- APPROVED_WITH_NOTES → 当前 package 可计入 reviewed，但建议 follow-up。
- NEEDS_REWORK → 回 `/sdd-kit:impl` 处理当前 package。
- BRAINSTORM_DRIFT → 回 `/sdd-kit:brainstorm` 追加 amendment。
- PRD 描述不足但方向清楚 → 回 brainstorm 更新 PRD，不引入第二套执行计划。

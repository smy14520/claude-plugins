# Normal mode

Normal 是高效收敛模式。目标是在已有信息足够时尽快形成可定稿的 package PRD，而不是进行全面拷问。

Follow `SKILL.md` Question interaction rules; normal only changes pacing and stopping threshold.

## Turn shape

保持短：

```text
当前场景：<正在展开的场景名>
当前理解：<一句话>
缺口：<该场景中尚未达到行为级精度的部分>
问题：<只问一个最高价值问题，交互形式遵守 SKILL.md 的 Question interaction rules>
```

## Exit

- 所有场景都已达到行为级精度 → 整理 PRD，并按 SKILL.md 的 PRD 定稿条件确认。
- 仍有场景未收敛 → 只问一个最高价值问题。
- 发现需求比预期更模糊或取舍更多 → 建议切到 grill-me，由用户确认。

# 状态行参考

每次报告在任务文件的 `## Status log` 部分追加一行。

## 格式（选择对应的格式）

### DONE

```
- [x] T-NNN (DONE) — YYYY-MM-DD HH:MM — <简短的事实性备注；验收命令全部通过 N/N>
```

### DONE_WITH_CONCERNS

```
- [?] T-NNN (DONE_WITH_CONCERNS) — YYYY-MM-DD HH:MM — <问题摘要>; <file:line 或后续跟进提示>
```

### NEEDS_CONTEXT

```
- [!] T-NNN (NEEDS_CONTEXT) — YYYY-MM-DD HH:MM — <歧义摘要>; 来源: <spec §X 或 task <field>>
```

### BLOCKED

```
- [✗] T-NNN (BLOCKED) — YYYY-MM-DD HH:MM — <阻塞摘要>; 解除阻塞: <需要满足的条件>
```

## 规则

1. **每次状态变更一行**。同一任务允许多行（形成审计轨迹）。
2. **必须包含时间戳**。本地时间，类 ISO 格式。
3. **简短** — `— ` 之后不超过 150 字符。完整细节写在用户可见的摘要中，而非状态行。
4. **基于事实**。禁止 "应该" / "将要" / "看起来"。仅记录已观测到的状态。
5. **不得编辑已有行**。只追加新行。

## 示例（正确）

```
- [x] T-001 (DONE) — 2025-04-18 10:30 — acceptance 3/3 green
- [x] T-002 (DONE) — 2025-04-18 11:15 — acceptance 2/2 green
- [?] T-003 (DONE_WITH_CONCERNS) — 2025-04-18 14:20 — retry uses fixed 3 tries no backoff; src/webhooks/xhs.ts:47
- [!] T-004 (NEEDS_CONTEXT) — 2025-04-18 15:05 — replay TTL 24h or 7d? spec §Constraints vs task acceptance disagree
- [✗] T-005 (BLOCKED) — 2025-04-18 15:30 — postgres 14 vs 15 mismatch; unblock: align env or rewrite migration
- [x] T-004 (DONE) — 2025-04-18 16:50 — user clarified TTL=24h, 2/2 green
- [x] T-005 (DONE) — 2025-04-18 17:30 — postgres upgraded to 15, migration applied, 1/1 green
```

## 示例（错误 — 不要这样写）

```
- [x] T-003 (DONE) — should work                  # "should" = 猜测
- [x] T-003 (DONE) — done                         # 没有事实
- [?] T-003 (DWC) — has concerns                  # 什么问题？
- [✗] T-003 (BLOCKED) — can't do it               # 不具体
- [x] T-003 — 2025-04-18                          # 缺少状态
```

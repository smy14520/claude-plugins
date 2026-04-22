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
- [!] T-NNN (NEEDS_CONTEXT) — YYYY-MM-DD HH:MM — <歧义摘要>; 来源: <brainstorm §X / task <field> / SRC-...>
```

### BLOCKED

```
- [✗] T-NNN (BLOCKED) — YYYY-MM-DD HH:MM — <阻塞摘要>; 解除阻塞: <需要满足的条件>
```

## 规则

1. **每次状态变更一行**。同一任务允许多行（形成审计轨迹）。
2. **必须包含时间戳**。本地时间，类 ISO 格式。
3. **简短** — `— ` 之后不超过 150 字符。
4. **基于事实**。禁止 "应该" / "将要" / "看起来"。
5. **不得编辑已有行**。只追加新行。

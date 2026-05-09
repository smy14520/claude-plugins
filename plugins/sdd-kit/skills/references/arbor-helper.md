# Arbor helper reference

Arbor helper 的确定性入口是插件 `bin/` 暴露到 Bash `PATH` 后的裸命令：

```bash
sdd-arbor
```

实际执行时直接使用 `sdd-arbor`。调用 Arbor helper 时，不通过 `which` / `python import` / 拼接插件根目录变量探测命令位置。

不确定参数时运行：

```bash
sdd-arbor <subcommand> --help
```

不要猜参数名，不要为一次误用添加 CLI 兼容层。若调用失败，报告失败命令和 stderr。

## 常用命令

按用途选择命令；参数以 `sdd-arbor <subcommand> --help` 为准。

### 健康检查

- `doctor`：项目级健康检查，汇总 package validation、wiki lint 与 next action。
- `validate`：校验单个 package 的 `.arbor` 状态、PRD、context 与生命周期一致性。
- `list`：列出 package 状态和下一步。
- `show`：查看单个 package 的 task.json、结果记录和 validation。

### Brainstorm / package readiness

- `create`：低层 draft workspace helper，仅用于新 brainstorm 开始时创建 `.arbor/tasks/<package>/prd.md` 草稿，并准备可选的 `artifacts/` 目录。
- `finalize-brainstorm`：从 brainstorm PRD 草稿写入 ready package。大 scope 使用 PRD 内 `## Slices`，不要创建子 package。

### Context / handoff

- `add-context`：追加单条 context 记录。
- `add-context-batch`：批量追加 context 记录。

### Lifecycle / implementation / review

- `set-status`：更新 package lifecycle state（`draft` / `ready` / `doing` / `done` / `reviewed`）。
- `mark-slice`：更新 slice 执行进度（`pending` / `in_progress` / `done`），记录在 `task.json` 的 `slices` 数组中。
- `set-execution`：记录轻量执行元数据，如 branch、worktree、execution status。
- `set-pr`：记录 package-level PR 元数据。
- `record-impl-result`：记录 impl 结果、self-check 依据和命令。
- `record-review`：记录 review verdict、summary、evidence 和 note。

### Wiki / orientation layer

- `wiki-index`：生成 `.wiki/` 页面索引。
- `wiki-search`：搜索 `.wiki/` orientation 内容。
- `wiki-collect`：按 query 收集相关 wiki 页面候选。
- `wiki-lint`：检查 `.wiki/` 健康度，只读报告。
- `module-summary`：为稳定 package 生成 module summary packet，供 wiki module note 发布使用。

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

- `doctor`：`.arbor` package 健康检查，汇总 validation 与 next action（wiki 健康用 `sdd-wiki lint`）。
- `validate`：校验单个 package 的 `.arbor` 状态、PRD、context 与生命周期一致性。
- `list`：列出 package 状态和下一步。
- `show`：查看单个 package 的 task.json、结果记录和 validation。

### Brainstorm / package readiness

- `create`：低层 draft workspace helper，仅用于新 brainstorm 开始时创建 `.arbor/tasks/<package>/prd.md` 草稿，并准备可选的 `artifacts/` 目录。
- `finalize-brainstorm`：从 brainstorm PRD 草稿写入 ready package。大 scope 使用 PRD 内 `## Slices`，不要创建子 package。
- `add-amendment`：记录 forward-only PRD 修正并把 package 路由回 ready。

### Context / handoff

- `add-context`：原子追加一条或多条 context 记录（`--entry-json` 可重复，或 `--entries-json` 传数组）。

### Lifecycle / implementation / review

- `set-status`：更新 package lifecycle state（`draft` / `ready` / `doing` / `done` / `reviewed` / `archived`）。
- `impl-packet`：拿 impl 入场包或单 slice 执行包；首次使用会派生并落盘 required_checks。
- `derive-required-checks` / `run-check` / `record-check`：把 Verification 固化为 required checks 并逐项记录证据。`blocked` / `not_run` 必须同时有 `--reason` 和 `--evidence`（或 `--command`）。
- `mark-slice`：更新 slice 执行进度；`done` 由 check + acceptance 证据 gate。
- `record-impl-result`：记录 impl 结果；slice acceptance / required-check 证据可从已结算 slices 自动聚合，但仍必须传 package-level `--functional-check <chk_id>`。
- `record-review`：记录 review verdict、summary、evidence 和 note。
- `module-summary`：为稳定 package 生成 module summary packet，供 wiki module note 发布使用。

## Wiki helper（独立工具）

`.wiki/` orientation layer 由独立 CLI `sdd-wiki` 维护（同样位于插件 `bin/`）：

```bash
sdd-wiki index --json
sdd-wiki search "<query>" --json
sdd-wiki collect --query "<query>" --limit 5 --json
sdd-wiki lint --json
```

`sdd-wiki` 不读写 `.arbor` 状态；package 状态相关操作一律用 `sdd-arbor`。

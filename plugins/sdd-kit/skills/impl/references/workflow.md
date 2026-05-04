# Impl workflow

Impl 执行一个 package PRD scope，并记录结构化结果。

## Pick

1. 确认 package。
2. 读取 `prd.md`、`task.json`、相关 context。
3. 读取 PRD 的目标、范围、Acceptance Criteria、Technical Framing 和 `## Slices`。
4. PRD blocking open questions 或 technical framing 缺失时停止。
5. 用 `sdd-arbor set-status ... --state doing` 记录开始。

## Execute

1. 根据 PRD scope / acceptance / technical framing / slices 形成一句 execution understanding。
2. 读取 `task.json` 的 `slices` 数组，找到第一个 `pending` 或 `in_progress` slice，从那里继续；若数组为空则按 PRD Slices 顺序从头开始。
3. 完整覆盖 PRD scope 的必要代码变更；避免无关重构、无关抽象和 PRD 外能力。
4. 每完成一个 slice，用 `sdd-arbor mark-slice <package> --id S-001 --status done` 记录进度。
5. 连续执行所有 slices，不在 slice 之间停顿等用户确认。
6. 信息不足时报告 NEEDS_CONTEXT；环境问题报告 BLOCKED。

## SelfCheck

1. 从 PRD acceptance criteria、technical framing 和 repo 既有验证方式推导检查。
2. 运行命令或验证明确行为。
3. 失败时不要声称 DONE。
4. 把检查依据和命令写入 `record-impl-result`。

## Report

用 `sdd-arbor record-impl-result` 记录 DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED。不要手写状态文件或 Markdown TODO。

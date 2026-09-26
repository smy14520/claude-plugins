---
title: list 语义：过滤即收窄（AND）+ 全视图唯一排序
description: todo-cli list 契约——多标签 AND 收窄、条件交集、全视图共用唯一排序、文本与 JSON 同源、stdout 纯净、空结果非错误
summary: 过滤即收窄（AND，OR 被排除为未来增量）；排序与过滤正交且全视图唯一；--json 与文本同源；stdout 只出数据；过滤空命中退出码 0
tags: [todo-cli, list, filtering, sorting, cli-contract]
type: decision
area: todo-cli
date: 2026-09-26
---

todo-cli 的 list 是全工具唯一的查看出口（文本视图与 `--json` 同源），其语义对未来任何过滤/展示类 task 都有约束力：

- **过滤即收窄**：多标签是 AND 语义（`--tag a --tag b` = 两标签都有），`--tag`/`--priority`/默认"仅未完成"三条件取交集。用户拍板理由：过滤的本意是收窄，单一可预测语义优先；OR（`--any`）被明确排除到未来，且必须是纯增量。
- **排序唯一规则，一切视图共用**：未完成按 priority(high>med>low)、同级 id 升序；`--all` 时已完成整体排在全部未完成之后、按 completed_at 倒序。任何新过滤参数都不得引入自己的排序——排序与过滤正交。
- **文本与 JSON 同源**：`--json` 不是独立查询路径，只是同一份过滤+排序结果的另一种渲染。给 list 加参数时两个视图自动同时生效，禁止只改一边。
- **stdout 纯净（按命令分类）**：视图命令（list 及 `--json`）stdout 只出数据（可被 `json.load` / 管道消费）；变更类命令允许在 stdout 报一行确认（含新 id，AC 已钉死）。错误与提示一律 stderr。新命令沿用此分类。
- **空结果是合法结果**：过滤无命中 → 空输出 + 退出码 0，不是错误。脚本可以放心 `todo list --tag x | wc -l`。

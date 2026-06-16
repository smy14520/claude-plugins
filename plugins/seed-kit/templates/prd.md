# {{TITLE}}

## 背景与目标

<!-- 为什么做、做成什么样、不做什么 -->

## 需求与验收标准

<!-- 每条 AC 可证伪：Given/When/Then，至少覆盖一条失败路径。
     写需求的同时写下预期证据，并标注它将用哪类验证兑现（assert / judge / human）、
     覆盖哪个交付面（backend-domain / api / web-ui / e2e / compliance / infra）——
     这决定了 slices/S-NNN.md 里 `## 交付面` 与 `## 验证面` 的形状。 -->

## Technical Framing

<!-- 轻量：技术选型、模块边界、与现有代码的接缝。够 impl 不跑偏即可，不写设计书。
     版本号/最新 API 这类易过期事实带 `查证于 <日期>（<来源>）`，例：Laravel 13.x（查证于 2026-06-15，laravel.com/releases）。 -->

## 质量基线（体验意图）

<!-- 仅当产品有用户可感面（UI/CLI/文案/API DX）时填，否则删掉本段。
     参考级目标，不是功能清单：参考产品 / 设计语言 / 质量门槛 / 明确不要的样子。
     impl 据此把可感面做到可交付品质；web-ui 的整体体验 judge 按它高标裁决。 -->

## Slices

<!-- 有序 checkbox 索引：一行一个 slice，顺序与状态住在这里；
     验收与验证项住在 slices/S-NNN.md（标题须与索引行一致）。
     checkbox 只能由 `seed done` 在证据齐备后勾选。 -->

### [ ] S-001 <标题>

## 变更记录

<!-- 一行一条：日期 + 改了什么 + 为什么 -->

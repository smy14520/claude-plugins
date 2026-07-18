---
description: 派独立 agent 审 seed PRD 的严重可实施性缺口；只报告，不修改、不自动推进。
---

独立审查 `.arbor/tasks/<task>/prd.md`。

1. 从 `$ARGUMENTS` 取 task 名；未提供时仅在 `.arbor/tasks/` 恰有一个 task 时使用它，否则询问用户。
2. 用 `Agent` 工具派 `subagent_type="seed-kit:seed-prd-review"`，在独立上下文中审查目标 task。**只传审查任务给 agent**——让它读 PRD、相关现有代码和项目已加载的标准，只返回发现的 critical/high gap 及证据。不要把后续修复步骤、实现要求或其他非审查任务传给子 agent。不要把 brainstorm 推理或预设结论传给它。
3. 要求 agent 按 completeness、consistency、clarity、scope、可证伪 Acceptance Criteria、slice ordering、buildability、code assumptions 校验，只返回会导致错误实现、返工、无法验证或无法开工的 critical/high gap，并给出 PRD 或代码证据。
4. 将结果原样整理给用户。无 serious gap 时明确说明；有缺口时列出进入实现前需要补齐的决策。

不修改 PRD，不发明项目标准，不调用 brainstorm/impl，不自动推进下一阶段。是否修订或进入实现由用户决定。

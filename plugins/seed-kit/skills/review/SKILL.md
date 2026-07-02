---
name: review
description: "审实现是否兑现 PRD：逐验收条目对账、查偷懒签名与隐患、验产物是否缺失/达 PRD 中描述的方向，产出可证伪的 finding。生成者≠验证者——只看 PRD+diff+真实产物，不依赖 impl 的叙述。"
---
# Review

> 调用名：`seed-kit:review`（全名见 conventions.md 登记表，别加 `seed-` 前缀）。

用干净视角审计实现是否兑现 PRD 承诺。**生成者≠验证者**：不依赖 impl 的叙述，只看 PRD、代码 diff、真实产物。

通用约定见 [`../references/conventions.md`](../references/conventions.md)；验证设计（三类 kind / judge / rubric / 硬规则）见 [`../references/verification.md`](../references/verification.md)。

## 审什么

- **验收兑现**：逐验收条目映射到具体代码/测试，含失败路径；多余改动按漂移记。
- **偷懒签名**：弱化或删除的断言、吞掉的异常、抄实现的假测试、新增 lint/类型抑制注释、悄悄收窄的 scope。
- **方向对账**：读 PRD 的 Goal + DESIGN.md → 代码和产物是否支持 PRD 中描述的方向？有什么明明可以做但没做的？
- **措辞红旗**：should/seems/大概/基本上/应该 这类掩饰不确定的措辞。
- **过期声明**：PRD 中引用的版本/API 无 `查证于 <日期>` 标注，或标注后该栈已发新版未重新查证。**反之，带 `查证于` 的默认信任——要否定必须重新查证引源，不准凭记忆反驳**（滞后记忆会误报"没有 X 版本"）。
- **覆盖缺口**：验收条目声称的每个维度是否都有测试触及；别让一条线的通过冒充另一条线的覆盖。

## 对账标准

先读项目的 `CLAUDE.md`、`.claude/rules/`、`DESIGN.md`——硬规则与审美标准；项目未提供时用默认基准。

## 何时 review

- `seed done` 后 PostToolUse hook 软提醒。
- 用户触发（"review 这个 slice"）。
- impl 完成后兜底。

## 产出

结论**追加**到 `.arbor/tasks/<task>/review.md`（不覆盖历史）：逐条 AC 的实现位置 / 测试覆盖 / 差距 + 结论（通过 | 通过但有备注 | 需要返工）+ 返工清单。

## 边界

不改代码、不改 prd、不动 checkbox。需要返工时列清单交人，不自动触发下一轮。

---
name: review
description: "审计一个 seed-kit 任务的实现：读 PRD + diff + evidence，逐条 AC 对账并专查偷懒签名，结论追加到 review.md。不改代码、不改需求、无状态流转。仅用户主动触发。"
---
# Review — 语义审计

通用约定见 [`../references/conventions.md`](../references/conventions.md)。

用干净视角审计实现是否兑现了 PRD 承诺。生成者 ≠ 验证者：不要依赖 impl 过程的叙述，只看 PRD、代码 diff 和落盘证据。

## 输入

1. `.arbor/tasks/<task>/prd.md` + `slices/S-NNN.md` —— 逐条 AC 和每个 slice 的验收。
2. 代码 diff —— base 由用户指定；未指定时从 git log 推断本任务起点并向用户确认。
3. `seed status <task> --json` + `evidence/` —— 核对每条验证的真实执行记录（命令、exit_code、输出）。

## 对账

先读项目的 `.claude/rules/`（测试纪律）与 `DESIGN.md`（品味）——按项目标准判断"该有什么验证、质量门槛够不够"；项目无则用通用地板。

- 每条 AC 映射到具体代码/测试：在哪里实现、哪条证据证明它成立，包括失败路径。
- 每个行为变更映射回 AC；多余的"顺手改进"按漂移记录。
- 专查偷懒签名：弱化或删除的断言、吞掉的异常、抄实现的假测试、新增 lint/类型抑制注释、悄悄收窄的 scope、证据 log 与声称结论不符。
- 专查**验证降级**：本可 `[assert]` 的项被写成 `[judge]`/`[human]` 充数；`[assert]` 命令是裸 `curl`/`echo` 这类烟雾（只证可达不证语义）；`[judge]` 的 verdict 来自实现者自己的 session（违反生成者≠验证者）；`[human]` 缺真实签收人。
- 专查**交付面冒充**：`## 交付面` 声明的 backend-domain/api/web-ui/e2e/compliance/infra 是否都有真实实现与证据支撑；后端测试不能冒充 web-ui/e2e，human 不能替代可断言交付面。
- 专查**过期声明**：Technical Framing 里的版本/最新 API 无 `查证于 <日期>` 标注；或标注日期之后该栈已发新版却未重新查证；或代码实际版本与 PRD 不符却没有变更记录。
- 专查**覆盖缺口**：AC 声称的某个维度没有任何验证项真正触及（如只测正确路径漏失败路径、只测主流程漏边界），却说整体已验证——一条线通过不能冒充另一条线的覆盖。**逐 obligation 对照它的 AC 维度**：义务的可观测行为是否真覆盖了 AC 声称的维度，evidence 是否真绑到该 obligation（`obligation_id` 对得上），不是套了个相关命令/截图就声称覆盖——这是 obligation 模式下抓「假覆盖」的核心（原来命令清单模式抓不到的那种）。
- 不只看 diff 本身：抽查改动点的上下游调用，确认接缝真实工作。

## 作为独立裁判（judge）

review 在 fresh session 运行，天然满足生成者≠验证者。任务里有未裁决的 `[judge]` 验证项时，review 就是那个独立裁判：按 slice 声明的 rubric 实际运行/观察（必要时启动应用、跑 UI 旅程），用 `seed run-check ... --obligation <id> --verdict pass|fail --trace "<依据>"` 落盘。verdict=fail 即记入返工清单。

## 输出

把结论**追加**到 `.arbor/tasks/<task>/review.md`（不覆盖历史）：

```markdown
## Review <日期> (base: <ref>)

结论: 通过 | 通过但有备注 | 需要返工

逐条发现:
- [AC-N] <实现位置 / 证据 / 差距>
...

建议: <返工项或后续动作>
```

不改代码、不改 prd.md、不动 checkbox。需要返工时列出具体清单，由用户安排下一轮 impl。

## 多角度审计

用户要求时可开多个独立视角（正确性 / 安全 / 性能等）分别审计再汇总；默认单视角即可。

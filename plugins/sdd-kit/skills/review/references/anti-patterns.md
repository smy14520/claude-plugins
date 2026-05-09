# Review 反模式

## 橡皮图章式 APPROVED

APPROVED 不能只是 "LGTM"。至少说明检查了哪些 goal / scope / diff evidence。

## 只读 PRD，不看 git diff

没有 diff 检查就没有审查。

## 将 self-check 通过等同于上游意图已满足

self-check 是 evidence，不是 verdict。Review 仍要检查 PRD、Technical Framing、Slices 和 diff 语义。

## 在审查中直接修改代码

Review 是只读的。修复属于 impl 的下一轮。

## 用 APPROVED_WITH_NOTES 掩盖 NEEDS_REWORK

如果关键约束、关键路径或验收证据缺失，就不是 notes，而是 rework。

## 将 impl 猜测错误归为 BRAINSTORM_DRIFT

如果上游足够清晰而 impl 猜错了，那是 NEEDS_REWORK，不是 drift。

## 用 BRAINSTORM_DRIFT 表示“PRD 可以更清晰”

只有 PRD 真正错误、失效或与当前 repo 脱节时才用 drift。

## 把 package APPROVED 当成 delivered

Review verdict 只说明当前 package scope 满足 PRD。PR merge / release 不是 review 自动完成的事。

## 在 package 累积 diff 中不隔离当前 PRD scope

package diff 可能包含多个来源的变更。报告必须说明当前审计对应哪些 diff files / behavior，并把结论绑定到当前 PRD scope。

## 不检查 impl self-check 的来源

必须检查 impl evidence 如何对应 PRD goal/scope、Acceptance Criteria、Technical Framing 与 Slices。

# Impl 产出反模式（review 主动找）

下列是 impl self-report 容易漏报的真实失败模式。Review 必须主动 grep / 数 / 对照，不能等 impl 在 `concerns` 字段里写出来。每条命中按 SKILL.md 的「Concerns 对账」表追加到 review 输出。

## Mega-test 假装多断言

一个 `test()` / `it()` 块塞 5+ 业务路径，断言数 << 路径数。逐 slice 完成标志找不到独立断言 → 算缺口。

> 例：`tests/integration/persistence.test.ts` 1 个 `it()` 串了 admin/event/override/registration/volunteer/check-in 全部模型，但只有最后几行 expect；S-003 的「override 落库」、S-004 的「报名/排班」、S-005 的「签到」按 PRD 应该各有独立测试。

## Happy-path E2E 替代 negative-path

PRD 写「X 被阻止 / 拒绝 / 限制」，但 E2E 只测了 happy path，负向路径 0 断言。数据库 unique / NOT NULL 约束不算业务层验证。

> 例：PRD「重复报名被阻止」只靠 `@@unique([eventId, residentId])`，业务层和 E2E 都没断言；编辑活动时排除自己的冲突逻辑（`excludeEventId`）也没测。

## 承重命令未在 commands 字段

PRD 明确提到 `docker compose run verify` / `prisma migrate deploy` / `npm run e2e:offline` 等承重命令，但 `impl_result.commands` 字段没出现。impl 自己声明跑了但没留命令证据 → 算缺口。

> 例：PRD S-006「提供 docker-compose 验证路径」+ 关键约束「不依赖第三方」，但 commands 只有 `npm run` 系列，没有任何 `docker compose` 调用。

## Mock / Fake 替代真实但 concerns 为空

PRD 承诺真实持久化 / 真实外部调用，impl 用 InMemory / Fake / Stub 实现但 `concerns` 数组为空。这是 DONE 不诚实，不是 self-check 通过。

> 例：PRD「Supabase Auth + Postgres」，actions.ts 全用 `InMemoryStore`，concerns 数组空。

## Dead file（形似实虚）

写了 client / handler / module 文件但 grep 全工程发现业务路径没引用。形式上代码存在，实质没接进闭环。

> 例：`lib/supabase/server.ts` 31 行 + 完整 createClient 逻辑，但 `actions.ts` 全部 `import { store } from './domain/store'`，0 处引用 `createSupabaseServerClient`。

## Acceptance_coverage 字段不对账

`acceptance_coverage[S-NNN]` 字段只回引 acceptance 文本本身，没指向独立证据（代码位置 / 测试位置 / 命令输出）。每个 slice 至少应有 1 条具体定位。

> 例：`acceptance_coverage[S-001]` 内容与 `acceptance[0]` 完全相同 → 没有独立证据。

## Concerns 数组与实际妥协数不符

你 audit 出的妥协清单长度 > `impl_result.concerns` 长度。impl self-check 的乐观偏差是 review 的核心抓取目标；差距 ≥3 直接 NEEDS_REWORK，1-2 算 APPROVED_WITH_NOTES + 在 note 里追加。

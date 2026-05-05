# sdd-kit

**SDD Kit** 是轻量的 PRD-first / skill-first 工作流插件：`brainstorm` 把需求收敛成单个 package PRD，`impl` 按 PRD 内的 `## Slices` 连续执行，`review` 审计 PRD 与 diff。`research` 只在需要资料探索时使用。`.arbor` 维护确定性 package state，`.wiki` 只作导航层。

## 核心模型

- `research`：可选探索工作区；带来源地整理事实，不做最终方案。
- `brainstorm`：需求澄清、Technical Framing、验收口径与实现切片；先创建/续作 PRD draft，每轮回答后更新，最终通过 finalize 写入 ready package。
- `impl`：执行一个 package PRD scope，按 `## Slices` 从上到下连续推进，运行 self-check，记录实现结果。
- `review`：只读审计 PRD + impl evidence + diff，输出四态 verdict。

阶段之间不自动跳转；wiki 写入也必须显式触发。

## 单 package + Slices 模型

大需求不再拆成 parent / child package。`brainstorm` 一次性 grill 目标、边界、Technical Framing 与验收口径，并在 PRD 内写出有序 `## Slices`：

```markdown
## Slices

- S-001: 项目基建 — 脚手架、DB config、健康检查 API、dev 启动命令
- S-002: 认证 — 学员注册登录、管理员登录、路由守卫、token 管理
- S-003: 内容数据模型与 API — 统一内容/章节/分类模型、CRUD API、访问类型标记
- S-004: 订单与权限模型 — 订单创建、模拟支付确认、单课授权、会员有效期开通
- S-005: 后台内容管理 — 课程/专栏列表、创建/编辑、章节管理、上下架
- S-006: 后台订单与用户 — 订单列表、模拟支付确认、用户/会员状态查看
- S-007: 前台首页与列表 — 首页布局、课程/专栏列表、分类筛选、价格/类型展示
- S-008: 前台详情与购买 — 详情页、购买/开会员 CTA、模拟支付流程、权限提示
- S-009: 学习中心 — 视频/图文学习页、章节目录、进度记录、收藏
- S-010: 验收与边界自检 — 核心购买学习路径、未授权/过期/下架等边界
```

Slice 是 PRD-local 的执行切片，不是独立 PRD，也不会 materialize 成子 package。Impl 进度通过 `sdd-arbor mark-slice` 写入 `task.json` 的 `slices` 数组：

- `pending` 未开始
- `in_progress` 部分完成（附简短备注）
- `done` 完成

Package 是需求 / 实现 / 评审 / 回滚边界；PRD 是需求、Technical Framing、Acceptance Criteria 和 Slices 的 source of truth。代码状态是实际进度事实，slice 结构化状态是断点续作提示。

## Package artifacts

Package 可按需在 `.arbor/tasks/<package>/artifacts/` 放 PRD-stage design artifact，例如：

- `data-model.sql`：草案级 schema contract，非生产 migration。
- `integration-contract.md`：第三方协议边界、payload、验签 / token / mock 边界。
- `api-contract.md`：关键 API contract。

Artifact 是 PRD 的附属 contract，用于压实大数据模型、协议或接口细节；最终实现事实源仍是代码里的 migration/schema/API。Impl 不应静默偏离 PRD 引用的 artifact；如需改变，走 amendment 或 NEEDS_CONTEXT。

## 状态边界

Top-level package lifecycle 只有五态：

```text
draft → ready → doing → done → reviewed
```

Impl / review 的结果状态是记录，不是 top-level state：

- Impl result：`DONE` / `DONE_WITH_CONCERNS` / `NEEDS_CONTEXT` / `BLOCKED`
- Review verdict：`APPROVED` / `APPROVED_WITH_NOTES` / `NEEDS_REWORK` / `BRAINSTORM_DRIFT`

路由原则：

- `ready` → 下一步 `impl`
- impl `DONE` / `DONE_WITH_CONCERNS` → package `done`，下一步 `review`
- impl `NEEDS_CONTEXT` → package 保持 `doing`，下一步 `brainstorm`
- impl `BLOCKED` → package 保持 `doing`，下一步 `user`
- review `APPROVED` / `APPROVED_WITH_NOTES` → package `reviewed`
- review `NEEDS_REWORK` → package `doing`，下一步 `impl`
- review `BRAINSTORM_DRIFT` → package `draft`，下一步 `brainstorm`

## 状态来源

- `.arbor/`：workflow source of truth。package lifecycle、context、impl/review 结果都由 `sdd-arbor` helper 维护。
- `.wiki/`：project-local orientation/index layer。用于 module note、summary、locator 和关联检索；实现或 review 前必须回到代码和 `.arbor` 验证。
- code：实现 source of truth。`impl` 改代码；`review` 审 diff；wiki 不替代代码事实。

## 常用入口

自然语言显式触发或 slash command 均可：

```text
用 research skill 调研 <topic>
用 brainstorm skill 收敛 <package>
用 brainstorm grill-me 追问这个需求
用 impl skill 执行 <package>
用 review skill 审计 <package>
用 wiki skill query / ingest / lint <content>
用 doctor 检查当前 sdd-kit 项目状态
这个 review 用 Team Auto 开多 agent 看看
```

Slash command：`/sdd-kit:research`、`/sdd-kit:brainstorm`、`/sdd-kit:impl`、`/sdd-kit:review`、`/sdd-kit:wiki`、`/sdd-kit:doctor`、`/sdd-kit:rules`、`/sdd-kit:team-auto`。

## `sdd-arbor` helper

`sdd-arbor` 只做机械状态读写、校验和检索；不判断需求范围、不写 PRD、不做 review 结论、不启动 agent。

插件通过 `bin/sdd-arbor` 暴露 helper；Claude Code 会把插件 `bin/` 加入 Bash `PATH`。在 skill/command prompt 中直接使用 `sdd-arbor`，不要拼接插件根目录变量，也不要在用户项目里用 `ls` / `which` / `python import` 探测命令位置。

不确定参数时先运行：

```bash
sdd-arbor <subcommand> --help
```

常用命令：

```bash
sdd-arbor doctor
sdd-arbor finalize-brainstorm --input-json '<json>'
sdd-arbor set-status <package> --state doing --actor impl --note "..."
sdd-arbor record-impl-result <package> --state done --summary "..." --acceptance "..." --command "..."
sdd-arbor record-review <package> --state approved --summary "..." --evidence "..."
sdd-arbor module-summary <package> --json
sdd-arbor wiki-collect --query "balance refund" --limit 5 --json
sdd-arbor validate --all --json
```

`create` 是低层 draft workspace helper，仅供 brainstorm seed `.arbor/tasks/<package>/prd.md` 草稿时使用；ready package 与 PRD readiness 统一走 `finalize-brainstorm`。`set-package-sizing` / `set-prd-status` 是 helper 内部命令，非日常入口。

## Team Auto

`team-auto` 是会话层 Agent Team playbook，不是 workflow 阶段，也不是 parallel runtime。只有用户明确说 Team Auto / 多 agent / 开 team / 双推 / 辩论 / review panel 时才触发；默认先根据当前任务给 2–4 个定制阵型选项。

## 设计原则

- 少即是多：workflow 骨架轻，避免把 prompt 写成补丁列表。
- Skill 负责阶段语义；`sdd-arbor` 负责机械动作；hook 只守底线。
- 可重复状态问题优先做 helper / validation，而不是增加口头规则。
- `.wiki` 只作导航层；隐藏目录原始状态（如 `.arbor/`、`.claude/`、`.git/`）不整理进 wiki，明确稳定 helper 输出除外。

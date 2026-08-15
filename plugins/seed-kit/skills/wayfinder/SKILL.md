---
name: wayfinder
description: "大且雾的任务开决策图：.arbor/maps/<slug>/（map.md 索引 + tickets/ 决策票），frontier 由 seed map status 从盘上推导，一会话一票拍到图清，交棒 brainstorm 收敛。仅用户主动触发。"
---
# Wayfinder — 决策图

通用约定见 [`../references/conventions.md`](../references/conventions.md)。

一个想法大到一份 PRD 装不下，而且路还看不清——决策互相咬、先答哪个决定后面问什么。这时不硬开访谈也不硬写 PRD：先开一张**图**，把决策链拆成一张张**票**，跨会话一张张拍，直到路清。

图是规划不是执行：每张票拍出一个决策，不产出交付物。想直接动手做某张票里的活的冲动，通常就是到了图的边缘——该交棒了。

## 开图

1. `seed map new <slug>` 脚手架 `.arbor/maps/<slug>/`（map.md + tickets/）。
2. 先拍 **Destination**（到达终点是什么样——产出的 spec / 决策 / 改动）：它固定 scope，所有票朝它收敛，先于一切票。
3. 广度过一遍问题面（brainstorm 式提问通道可用），把现在能精确表述的问题写成票；还表述不清的写进 **Not yet specified** 雾区——雾区是"知道要来但还立不了票"的问题，不预拆成票。
4. 票间依赖用 `blocked-by` 连线；frontier 不手工维护，开工前后跑 `seed map status <slug>` 从盘上推导。

### map.md 五节

```
## Destination        到达终点是什么样，一两行；每个会话选票前先对齐它
## Notes              领域背景、该查的资料（wiki 页 / research topic）、长期偏好
## Decisions so far   一行一张已关票：票号 — 一句话要点；细节只在票里，图是索引不重述
## Not yet specified  雾区：还看不清、立不了票的问题；frontier 推进后逐步毕业成票
## Out of scope       已裁定超出 Destination 的工作：只列不毕业
```

### 票文件格式

`tickets/<票号>.md`（票号 = 文件名，如 `auth-choice.md`）：

```markdown
---
type: research | prototype | grilling | task
status: open | closed
blocked-by: []            # 依赖的其他票号，如 [data-shape]；无依赖留空
---

## Question

<这张票要拍的决策 / 要查的事实>

## Resolution

<!-- status: closed 时必有：拍板答案（含 verdict / 产生的事实），下游票与 brainstorm 从这里读 -->
```

## 票类型与执行分工

- **grilling**（HITL）：默认票型。走 brainstorm 的提问通道——AskUserQuestion 一次一题、推荐项置首；拍板即 Resolution。
- **research**（AFK）：查文档 / API / 外部资料。轻调查派 sub-agent，结论直接写票；重调查建 `.arbor/research/<topic>/`（index-first 工作区），票里留指针。
- **prototype**（HITL）："该长什么样 / 手感对不对"的设计票。派 `seed-prototype`，用户玩出来的 verdict 写 Resolution。
- **task**（HITL 或 AFK）：为解锁决策的体力活——取数、开权限、备环境。agent 能代办则代办（AFK）；否则给人精确步骤清单（HITL），照单执行。Resolution 记录做了什么与产生的事实（凭据位置、新地址、数据规模），供下游票引用。

HITL = 人在环上：grilling、prototype（含用户玩原型）、需人手的 task；AFK = agent 独立完成。**HITL 票 agent 不得代替用户作答**——替用户回答了自己问题的访谈票是坏票。

## 会话纪律

- 开工先跑 `seed map status <slug>`：frontier、open/closed 计数从盘上推导，不靠记忆挑票。
- **一会话只解决一张票**（research 例外：轻调查 sub-agent 可并行）。
- 拍完一张票：答案写 `## Resolution`、frontmatter 翻 `status: closed`、map.md 的 Decisions so far 加一行要点；答案让雾区看得清了的，随手立新票并从雾区删掉对应条目；答案揭示某张票其实超出 Destination 的，把票关掉、Out of scope 记一行。
- 每个会话开始先读 map.md（低清全景），按需再放大具体票——不全量倾倒。

## 图清与交棒

图清 = frontier 空 + 雾区（Not yet specified）空 + 全票 closed。图清后建议用户触发 `/seed-kit:brainstorm` 收敛——brainstorm 读已关票的 Resolution，已拍的决策不重问；收敛出 PRD 才进 impl。**不自动进 impl**。

## 账本分离（票不是 slice）

- 票不进 `seed done`、不翻 PRD checkbox、不是 slice——`.arbor/maps/` 是决策账本，PRD checkbox 是交付账本，两套账本严格分离。
- `.arbor/maps/` 状态不构成第二套进度；图清即冻结，不再更新。
- `seed map` 只有 new / status 两个子命令：收票（写 Resolution、翻 status）是 agent 的语义动作，helper 保持只读。

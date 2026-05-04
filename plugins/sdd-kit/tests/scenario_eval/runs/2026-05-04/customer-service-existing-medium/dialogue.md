# Scenario dialogue — customer-service-existing-medium

- 时间：2026-05-04T10:51:49.666730+00:00
- Profile：existing-medium
- Model：claude-opus-4-6
- AI user model：claude-opus-4-6


## 初始用户需求

我想在现有微信/抖音 webhook 体系里新增一个飞书客服渠道，要求能按现有 channels 配置启用、校验飞书签名、把入站消息转成统一会话事件，并支持 AI 回复回推。

## Brainstorm Turn 1

### 被测 agent

我已经创建并写入了 PRD draft：

`.arbor/tasks/05-04-feishu-customer-service-channel/prd.md`

当前理解：这是一个存量 Express + TypeScript 多渠道 AI 客服后端，已有 `ChannelAdapter`、微信/抖音 adapter、`channels` 配置模型和统一 webhook 路由；飞书应作为新 channel 复用这套体系，而不是另起链路。

真正阻塞继续收敛的是：**飞书“客服渠道”到底接入哪个飞书产品入口**。这会直接决定 webhook payload、签名校验算法、配置字段、回推 API 和验收方式。

推荐选择：**飞书开放平台机器人 / 事件订阅**。理由是它最贴近现有 webhook + adapter 模式，也最容易把入站消息转成统一会话事件并让 AI 回复回推。

你希望本次按哪种接入对象来定 PRD？

1. **飞书开放平台机器人 / 事件订阅（推荐）**  
   作为消息事件渠道接入，复用现有 adapter/webhook 体系。

2. **飞书服务台 / HelpDesk**  
   更像客服产品接入，可能涉及工单、坐席、服务台状态等额外模型，scope 会明显变大。

3. **企业自建应用消息**  
   偏企业内部 IM / 应用消息场景，不一定等同客服服务台。

4. **暂时抽象为飞书事件入口**  
   可以先推进 PRD，但 finalize 前仍需要补清具体入口，否则实现和验收会发散。

### AI user

选择 **1. 飞书开放平台机器人 / 事件订阅**。

本次先把它作为一个新的消息事件渠道接入，目标是让客户在飞书里给机器人发消息后，后端能像微信/抖音一样进入统一会话事件，再由 AI 生成回复并回推到飞书会话里。我们暂时不做飞书服务台的工单、坐席分配、服务台状态这些能力，避免 scope 扩大。

## Brainstorm Turn 2

### 被测 agent

已更新 PRD draft：接入对象固定为**飞书开放平台机器人 / 事件订阅**，并把 **飞书服务台 / HelpDesk 的工单、坐席分配、服务台状态**明确写入 Out of scope。

下一处会直接影响实现边界的是：**本次支持的入站消息类型和 AI 回复形式**。

我的推荐：**本次只做文本入站 + 文本回复**。理由是它最贴近“先把飞书作为新消息事件渠道接入”的目标，能把签名校验、事件订阅、统一会话事件、AI 回推主链路先跑通；图片、卡片、文件会引入素材下载、富文本结构、卡片 schema、权限和更多失败路径，容易把本包 scope 拉大。

你希望本次 PRD 怎么定？

1. **只做文本入站 + 文本回复（推荐）**  
   支持飞书 `im.message.receive_v1` 的 text 消息，AI 回复也只回推普通文本。

2. **文本 + 图片入站，文本回复**  
   图片消息转成统一事件但 AI 仍只回文本；需要定义图片 URL / file key / 下载权限如何进入统一事件。

3. **文本入站 + 卡片回复**  
   入站仍只处理文本，但 AI 回复用飞书 interactive card；需要增加卡片模板和验收。

4. **文本 / 图片 / 卡片都支持**  
   功能完整但 scope 明显扩大，adapter 映射和测试矩阵都会变复杂。

### AI user

选择 **1. 只做文本入站 + 文本回复**。

本次目标是先把飞书机器人作为新增渠道跑通主链路：飞书用户发普通文本消息，后端进入统一会话事件，AI 生成文本回复并回推到同一个飞书会话。图片、文件、卡片、富文本都先不纳入本次验收，避免影响核心接入节奏。

## Brainstorm Turn 3

### 被测 agent

已更新 PRD：本次范围收敛为 **飞书机器人文本入站 + AI 文本回复回推同一飞书会话**；图片、文件、卡片、富文本都已写入 Out of scope / 边界场景。

下一处最高价值问题是 **事件去重 / 幂等**。飞书事件订阅通常可能因为超时、网络或平台重试导致同一消息事件重复推送；如果不处理，可能造成同一用户消息被 AI 回复多次。

我的推荐：**本次做轻量幂等**。理由是客服自动回复里重复回复体验很差，而且我们已经有 `messageId` / 飞书 `message_id` 可作为自然幂等键；不需要做复杂队列，只要保证同一 channel + messageId 不重复生成统一会话事件 / AI 回复即可。

你希望本次怎么定？

1. **轻量幂等（推荐）**  
   用 `channelType + messageId` 或飞书事件 ID 做去重；重复事件返回 ok/ignored，不再次触发 AI。

2. **只记录风险，不实现**  
   主链路更快，但可能出现重复 AI 回复；验收只覆盖单次事件。

3. **完整事件处理保障**  
   引入持久化 inbox / event log、处理状态、重试状态；更可靠但 scope 会明显扩大。

### AI user

选择 **1. 轻量幂等**。

客服场景里重复回复会很影响体验，所以本次需要处理。按 `channelType + messageId` 作为幂等键即可；如果飞书事件里有更稳定的事件 ID，也可以作为补充，但业务上我更关心同一条用户消息不要触发多次 AI 回复。

重复事件不需要报错，返回成功或 ignored 都可以，关键是不能再次生成统一会话事件，也不能再次回推 AI 回复。完整 inbox / event log、处理状态和复杂重试这次先不做。

## Brainstorm Turn 4

### 被测 agent

已更新 PRD：轻量幂等已纳入本次 scope，要求按 `channelType + messageId` 防止重复生成统一会话事件和重复触发 AI 回复；完整 inbox / event log、状态机、复杂重试已明确 out of scope。

下一步进入 **测试策略档位**。我的推荐：**核心路径测试**。理由是这是外部 webhook + 第三方 API 集成，最重要的是用 mock/fake 把主链路和失败路径测稳：合法文本入站、签名失败、inactive 渠道、重复事件、AI 文本回推成功/失败、微信/抖音回归；不需要为了这个渠道扩展做完整 TDD。

你希望本次 PRD 采用哪档测试策略？

1. **核心路径测试（推荐）**  
   业务逻辑层关键路径 + 关键边界 case；飞书 webhook / API 用 mock/fake。

2. **TDD 驱动**  
   先写测试再实现，覆盖所有业务逻辑层和边界；更稳但实现节奏更重。

3. **最小验收**  
   只测 happy path 和少量失败路径；更快，但签名/幂等/回推失败风险覆盖不足。

### AI user

选择 **1. 核心路径测试**。

这次我希望测试重点放在飞书新增渠道的主链路和高风险边界上：合法文本入站能进入统一会话并回推文本、签名失败不能进入业务处理、inactive 渠道不处理、重复事件不重复触发 AI、飞书回推失败能被正确记录/返回，以及微信/抖音现有渠道不要被破坏。

飞书 webhook 和回推 API 用 mock/fake 就可以，不要求接真实飞书环境；也不要求完整 TDD。只要核心路径和关键失败路径稳住，符合这次中等 scope 的投入预期。测试或运行如果涉及环境搭建，优先用 Docker / docker-compose 隔离，不要污染本机全局环境。

## Brainstorm Turn 5

### 被测 agent

已更新 PRD：测试策略定为**核心路径测试**，并写入 mock/fake 飞书 webhook/API、不接真实飞书环境、不要求完整 TDD；如需环境搭建，优先 Docker / docker-compose 隔离。

现在进入 brainstorm 的扩展扫视：主 scope 已经清楚，但有几类相邻能力很容易被漏掉或误纳入。我的推荐是：**只把 URL verification / challenge 纳入本次，其它写入 Out of scope / Risks**。理由是 URL verification 是飞书事件订阅 webhook 通常必须完成的接入前置；而配置 UI、告警观测、多租户权限、复杂重试都会扩大范围。

你希望本次把哪些相邻能力纳入 PRD？可以选一个方向：

1. **只加 URL verification（推荐）**  
   支持飞书事件订阅的 `url_verification` / `challenge`，保证 webhook 能在飞书后台完成配置；其它相邻能力 out of scope。

2. **URL verification + 基础诊断日志**  
   除 challenge 外，要求签名失败、inactive、回推失败、重复事件都有可诊断日志；scope 略增但运维更友好。

3. **再加 channels 配置 UI**  
   除后端模型外，还做飞书渠道配置页面/表单；如果现有项目没有 UI，这会显著扩大范围。

4. **保持当前最小 scope**  
   不额外纳入 URL verification、日志、UI；只做消息事件主链路。

### AI user

选择 **1. 只加 URL verification**。

飞书后台配置事件订阅时，`url_verification` / `challenge` 是接入前置，不支持的话渠道可能根本配置不上，所以本次需要纳入验收。

其它相邻能力这次先不扩 scope：不做 channels 配置 UI，不新增告警/观测体系，不做多租户权限扩展，也不做复杂重试。签名失败、inactive、重复事件、回推失败这些可以按现有后端日志/错误处理习惯保留必要记录，但我不希望把“基础诊断日志”单独变成一组新增产品需求。

## Brainstorm Turn 6

### 被测 agent

已完成扩展扫视并整理 PRD，`sdd-arbor validate` 通过。

当前 PRD draft 已收敛为：

- **飞书开放平台机器人 / 事件订阅**作为新渠道；
- 支持 `url_verification` / `challenge`；
- 仅支持**普通文本入站 + 普通文本回复**；
- 复用现有 `channels` 配置、`ChannelAdapter`、统一 webhook 路由；
- 校验飞书 verification token / 签名 / 可选 encrypt key；
- 转成统一 `UnifiedMessage` / 会话事件；
- AI 文本回复回推到原飞书会话；
- 按 `channelType + messageId` 做轻量幂等，重复事件不再触发 AI；
- 核心路径测试，飞书 webhook/API 全部 mock/fake；
- 明确不做飞书服务台、配置 UI、告警观测体系、多租户扩展、复杂重试、非文本消息。

PRD 路径：

`.arbor/tasks/05-04-feishu-customer-service-channel/prd.md`

如果你确认这个 PRD 可以作为实现边界，我下一步会调用：

```bash
sdd-arbor finalize-brainstorm --input-json '{"name":"05-04-feishu-customer-service-channel","kind":"single","prd_path":".arbor/tasks/05-04-feishu-customer-service-channel/prd.md"}'
```

确认定稿吗？

### AI user

确认定稿。

这个 PRD 可以作为本次实现边界：飞书开放平台机器人事件订阅接入、文本主链路、URL verification、签名/token 校验、统一消息转换、AI 文本回推、轻量幂等和核心路径测试都已经覆盖；同时非文本消息、服务台、UI、观测体系、多租户和复杂重试也明确排除，边界足够清楚。

可以按这个 PRD 执行 `finalize-brainstorm`。

## Brainstorm Turn 7

### 被测 agent

已定稿完成。

Package：

`05-04-feishu-customer-service-channel`

PRD：

`.arbor/tasks/05-04-feishu-customer-service-channel/prd.md`

状态已由 `sdd-arbor finalize-brainstorm` 写入 ready package。下一步可以用 `impl` 执行这个 PRD scope。

### AI user

好，下一步可以按这个 ready package 进入 `impl`。

实现时请以该 PRD 为边界：先完成飞书机器人事件订阅的文本主链路、URL verification、校验、统一消息转换、AI 文本回推、轻量幂等和核心路径测试；不要顺手扩展服务台、配置 UI、非文本消息、复杂重试或新的观测体系。

如果实现中发现 PRD 里没有覆盖、但会影响业务行为的决策点，再停下来确认。

# Raw — 飞书开放平台证据摘录

查证于 2026-09-26。抓取方式：WebFetch 官方文档站（open.feishu.cn 部分页面可抓）+ WebSearch 多源核实。

## 1. 群自定义机器人 webhook（官方页面抓取成功）

来源：https://open.feishu.cn/document/client-docs/bot-v3/add-custom-bot （WebFetch 成功，原文摘录）

- 审批：「自定义机器人在添加至群组后即可使用，**无需租户管理员审核**」；群设置 → 群机器人 → 添加机器人 → 自定义机器人
- 限制：「自定义机器人只能在当前群聊内使用，同一个自定义机器人无法添加到其他群聊。」
- Webhook URL：`https://open.feishu.cn/open-apis/bot/v2/hook/xxxxxxxxxxxxxxxxx`，POST `Content-Type: application/json`
- 安全设置（可组合多个）：自定义关键词（最多 10 个）；IP 白名单（最多 10 个，支持 `123.1.1.1/24` 段写法）；签名校验（HmacSHA256 对空字符串签名后 Base64，`timestamp + "\n" + 密钥`，时间戳距当前不超 1 小时；请求体附 `timestamp` + `sign`）
- 校验失败错误码：关键词 19024、IP 19022、签名 19021
- 频率限制：「为单租户单机器人 100 次/分钟，5 次/秒」；建议避开整点/半点（否则可能 11232 限流）；请求体 ≤20KB
- 消息类型：text（支持 `<at>`）、post 富文本、share_chat 群名片、image（需先传图取 image_key）、interactive 卡片（仅支持按钮/链接跳 URL，不支持回调交互）
- 其他：自定义机器人不能响应用户消息，不能撤回自己发的消息；卡片 @ 人仅支持 Open ID/User ID

## 2. 应用消息推送（机器人消息 API）

来源：WebSearch 多源（官方文档站「发送消息」接口；正文未直接抓取 → 端点与权限名以多源一致为准）

- 端点：`POST /open-apis/im/v1/messages`（需 `receive_id_type` + `receive_id`，可发 chat/open_id/user_id）
- 鉴权：`tenant_access_token`（应用身份）或 `user_access_token`（用户身份）
- 权限：`im:message`（发送/读取消息）、`im:chat`（群聊）等
- 前提：应用开启「机器人」能力；权限变更后需创建版本发布并经管理员审核授权，否则 403

## 3. 任务 API（官方文档存在性经搜索确认）

来源：官方文档 https://open.feishu.cn/document/server-docs/task-v2/task/create （URL 确认；正文页 JS 渲染抓取失败，参数经搜索索引转述）+ CSDN 实战文章交叉印证

- 端点：`POST https://open.feishu.cn/open-apis/task/v2/tasks`
- 权限 scope：`task:task` / `task:task:write` / `task:task:readonly`（任意一项即可）
- 限流：50 次/秒（应用维度）
- 能力：以应用/用户身份创建任务，指定执行人、截止时间（due）、参与人、重复规则（repeat_rule）、任务分组、评论、任务清单
- ⚠️ v1（`/task/v1/tasks`，权限 `task:create` 等）已于 2023-12 停止维护，迁移到 v2

## 4. 日历 API（官方页面抓取成功）

来源：https://open.feishu.cn/document/server-docs/calendar-v4/calendar-event/create （WebFetch 成功，原文摘录）

- 端点：`POST https://open.feishu.cn/open-apis/calendar/v4/calendars/:calendar_id/events`
- 鉴权：「tenant_access_token 指应用身份，user_access_token 指用户身份」，Bearer 头
- 前提：「当前身份必须对日历有 writer 或 owner 权限，并且日历的类型只能为 primary 或 shared」；应用身份调用需开启机器人能力
- 权限 scope（「开启其中任意一项权限即可调用」）：`calendar:calendar`、`calendar:calendar.event:create`
- 限流：1000 次/分钟、50 次/秒
- 配套接口族：查询主日历/日历列表/搜索日历/查询日历信息、添加日程参与人、预约会议室；event_id 可用于查询/更新/删除日程
- 注意：本文档的 `free_busy_status` 是写入参数（设日程忙/闲），查询他人忙闲是另外的接口（能力族内存在）

## 5. OAuth 网页授权登录

来源：官方文档（open.feishu.cn；「获取 user_access_token」旧版已标历史版本，新版 OIDC 经搜索确认）+ 多源实战（justsong.cn 等）

- 授权端点：`https://open.feishu.cn/open-apis/authen/v1/authorize`（携带 redirect_uri、state）
- 换凭证：`POST https://open.feishu.cn/open-apis/authen/v1/oidc/access_token`（app_access_token + 授权码 code 换 user_access_token）
- ⚠️ Gotcha：「为了避免刷新 user_access_token 的行为被滥用，在用户授权应用365 天后，应用必须通过用户重新授权的方式」重新获取 token（官方 v2 刷新接口文档原句，2026-06-29 更新）——登录态需处理一年期强制失效
- 开发前需在开发者后台配置重定向 URL 并申请相关权限
- 另有第三方网站「飞书扫码登录」能力（同授权体系）

## 6. 自建应用准入门槛

来源：官方文档「Custom app development process / 企业自建应用开发流程」（open.feishu.cn，2025-05-29）+ feishu.cn「自建应用发版审核指南」+ 多源实操文章

- 创建：开发者后台 → 创建企业自建应用，得 App ID / App Secret；流程为「成为飞书用户 → 创建应用 → 配置权限 → 开发测试 → 发布上线 → 运营维护」
- 发布：「版本管理与发布 → 创建版本」设置版本号、更新说明、应用能力、权限变更、可用范围（全体/部分成员）→ 申请线上发布 → **企业管理员审核**，结果经飞书消息与开发者后台通知
- 管理员可在「应用管理 → 设置管理规则 → 自建应用开发与审核规则」配置审核方式（飞书审批流程/自动通过等）
- 即：创建应用本身门槛低，但权限生效与可用范围变更需管理员审核；若自建租户（自己是管理员）可自行审批
- 飞书有免费个人/小团队版本，可自建租户试用（社区通行做法；官方未在本次抓取页面中明文 → 人类确认时一并验证）

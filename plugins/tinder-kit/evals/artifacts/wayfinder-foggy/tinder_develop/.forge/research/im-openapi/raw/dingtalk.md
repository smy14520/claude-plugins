# Raw — 钉钉开放平台证据摘录

查证于 2026-09-26。抓取方式：WebSearch 多源核实（open.dingtalk.com 官方文档站为 JS 渲染，WebFetch/WebReader 均拿不到正文，故以官方文档 URL + 多源一致转述为证据，逐条标注）。

## 1. 群自定义机器人 webhook

来源：官方文档 https://open.dingtalk.com/document/robots/customize-robot-security-settings 与 https://open.dingtalk.com/document/orgapp/robot-sends-a-message-scenario-and-interface-limits（URL 经搜索确认；内容经禅道官方文档、腾讯云社区、掘金、CSDN 多源一致转述）

- 添加路径：群设置 → 智能群助手 → 添加机器人 → 自定义；由群内成员操作，未见企业管理员审批要求
- 安全设置（至少设其一，可组合）：自定义关键词（最多 10 个，消息必须含至少 1 个）；加签（HmacSHA256：`timestamp + "\n" + secret` 签名后 Base64 + UrlEncode，时间戳与请求时间相差不超 1 小时）；IP 地址（段）白名单
- 频率限制：每个机器人每分钟最多 20 条；超限报错 `1302, send rate limited`，本分钟剩余消息全部丢弃
- 官方建议：大量消息用「消息聚合」合并发送，或多建机器人分流

## 2. 应用消息推送（工作通知）

来源：淘宝开放平台文档中心（developer.alibaba.com，钉钉 API 同源）、pkg.go.dev、TAPD 对接文档等多源一致

- 端点：`POST https://oapi.dingtalk.com/topapi/message/corpconversation/asyncsend_v2?access_token=ACCESS_TOKEN`
- 关键参数：`agent_id`、`userid_list`（或 `to_all_user`）、`msg`（text/link/markdown/action_card 等）
- 前提：开放平台创建企业内部应用，取 AgentId、AppKey、AppSecret

## 3. 自建应用（企业内部应用）准入门槛

来源：钉钉开发者百科 https://open-dingtalk.github.io 「获得开发者权限」、帆软帮助文档、火山引擎/阿里云接入文档（多源一致）

- 创建入口：开发者后台 https://open-dev.dingtalk.com/ → 应用开发 → 企业内部开发 → 创建应用，生成 AgentId/AppKey/AppSecret
- 权限前提：**需要开发者权限**——主管理员默认拥有；普通员工需管理员在 OA 后台「安全与权限 → 权限管理」授予后才能进开发者后台
- ⚠️ 非主管理员创建的应用，**发布时需主管理员审批**（帆软文档明确建议主管理员操作）
- API 权限（如待办读写、通讯录）需在应用「权限管理」中申请，审核通过后生效
- 个人试用路径：社区普遍做法是自己注册一个钉钉组织成为主管理员，即可自行审批（社区实践佐证，非官方文档明文）

## 4. 待办任务 API

来源：WebSearch 命中 open.dingtalk.com 官方文档（「查询企业下用户待办列表」2026-06-04、「查询用户企业类型待办列表」2025-09-25、「快速生成待办任务」2022-05-19）+ 阿里云开发者社区 + CSDN 实战

- 新版端点：`POST https://api.dingtalk.com/v1.0/todo/users/{unionId}/tasks`（参数 subject 必填，description、dueTime、executorIds/participantIds 等）
- 旧版端点：`POST https://oapi.dingtalk.com/topapi/todo/v2/task/add`
- 权限点：`Todo.Task.Write` / `Todo.Task.Read`（应用后台申请）
- 限制：查询接口最多取 180 天内已完成状态待办，未完成无此限制；待办用数字表示优先级

## 5. 日历 API

来源：WebSearch 命中 open.dingtalk.com 官方文档「添加日程参与者」（2023-10-25）+ GitHub dingtalk-openapi-skills 模块清单（dingtalk-calendar：日历、会议室、忙闲查询）

- 官方文档目录「日程」下有创建日程、添加日程参与者、查询忙闲等接口族
- 限制摘录：「每次日程参与者操作最大支持500人，最大支持操作5000人的日程」
- 新版 API 风格：`https://api.dingtalk.com/v1.0/calendar/...`

## 6. OAuth 网页登录（新版统一授权）

来源：官方文档「实现网页方式登录应用（登录第三方网站）」（2025-06-19，URL https://open.dingtalk.com/document/orgapp/log-in-to-a-third-party-website-through-web-page）、「获取登录用户的访问凭证」（2021-12-06，obtain-user-token）；多源实战文章一致

- 授权端点：`https://login.dingtalk.com/oauth2/auth?redirect_uri=...&response_type=code&client_id=...&scope=...&state=...&prompt=consent`（扫码或账密登录，企业内部应用可用）
- 换凭证：`POST https://api.dingtalk.com/v1.0/oauth2/userAccessToken`（code + AppSecret 换 userAccessToken）
- scope 通常 `openid corpid`；redirect_uri 必须与开放平台配置完全一致
- 旧版扫码登录（open-dev「创建扫码登录应用授权」）逐步下线，迁移到统一 OAuth2.0

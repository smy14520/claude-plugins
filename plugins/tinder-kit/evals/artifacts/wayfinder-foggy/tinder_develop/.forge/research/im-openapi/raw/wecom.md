# Raw — 企业微信开放平台证据摘录

查证于 2026-09-26。抓取方式：WebFetch 官方文档站 + WebSearch 官方文档索引。官方文档站为 developer.work.weixin.qq.com（部分页面 JS 渲染，抓取以摘录为准）。

## 1. 群机器人（消息推送）webhook

来源：https://developer.work.weixin.qq.com/document/path/91770 （WebFetch 成功，原文摘录）

- Webhook URL：`https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=693a91f6-7xxx-4bc4-97a0-0ec2sifa5aaa`
- 调用方式：「开发者可以按以下说明向这个地址发起HTTP POST 请求，即可实现给该群组发送消息」，`Content-Type: application/json`，body 如 `{"msgtype":"text","text":{"content":"hello world"}}`
- 频率限制：「每个消息推送发送的消息不能超过20条/分钟。」
- 消息类型：「当前自定义消息推送支持文本（text）、markdown（markdown、markdown_v2）、图片（image）、图文（news）、文件（file）、语音（voice）、模板卡片（template_card）八种消息类型。」
- 长度限制：text ≤2048 字节；markdown ≤4096 字节；图片（base64 前）≤2M 仅 JPG/PNG；@成员语法 `<@userid>` 适用于 text/markdown
- 文档未提及添加机器人需要企业管理员审批（仅描述「创建消息推送页面」获取 webhook 的入口）

## 2. 应用消息推送

来源：WebSearch 命中官方文档与多源一致转述（https://developer.work.weixin.qq.com 站内「发送应用消息」；未能直接抓到正文页）

- 端点：`POST https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token=ACCESS_TOKEN`
- 关键参数：`agentid`（企业应用 id，企业内部开发在应用设置页查看）、`touser/toparty/totag`、`msgtype`（text/image/video/file/textcard/news/mpnews/markdown 等）
- 前提：管理后台「应用管理 → 自建 → 创建应用」获取 CorpId、AgentId、Secret（多源一致）

## 3. 日历/日程开放 API（官方页面抓取成功）

来源：https://developer.work.weixin.qq.com/document/path/93647 （WebFetch 成功；本页实为「创建日历」）

- 创建日历：「该接口用于通过应用在企业内创建一个日历。」端点 `https://qyapi.weixin.qq.com/cgi-bin/oa/calendar/add?access_token=ACCESS_TOKEN`，「请求方式： POST（HTTPS）」
- 官方目录下的完整接口族（导航摘录）：
  - 管理日历：创建(93647)/更新(97716)/获取详情(97717)/删除(97718)
  - 管理日程：创建(93648, `/cgi-bin/oa/schedule/add`)/更新(97720)/更新重复日程(96204)/新增日程参与者(97721)/删除日程参与者(97722)/获取日历下日程列表(97723)/获取日程详情(97724)/取消日程(97725)
  - 回调通知：日历与日程的增删改事件 + 日程回执(98111)
- 限制摘录：公共日历「每个人最多可创建或订阅100个」；全员日历「每个企业最多可创建20个」；通知范围最多2000人

## 4. 待办/任务 API

来源：WebSearch（developer.work.weixin.qq.com 导航转述，未能直接抓取正文 → 弱证据，标存疑）

- 文档导航中存在「获取待办详情」「更新待办状态」两个待办类接口
- 未发现「创建待办/任务」的开放 API；第三方实践普遍用「应用消息/模板卡片 + 智能表格 API」替代任务管理
- 结论：企业微信无面向自建应用的完整任务管理 API 族（与钉钉待办、飞书任务对比）——此判断基于搜索转述，正文未直接核验

## 5. OAuth 网页登录

来源：WebSearch（官方文档章节索引；正文页抓取被截断 → 参数细节未逐一核验）

- 官方文档两大章节（章节名与结构经搜索确认）：
  - 「网页授权登录」：开始开发 / 构造网页授权链接(path 91025) / 获取访问用户身份 / 获取访问用户敏感信息
  - 「企业微信Web登录」：开始开发 / Web登录组件 / 获取登录用户身份
- 新版 Web 登录跳转端点：`https://login.work.weixin.qq.com/wwlogin/sso/login?appid=...&redirect_uri=...`（多源实战文章一致；旧版内嵌二维码组件 wwLogin js 逐步被替代）
- 前提：扫码授权登录需先有自建应用并配置授权回调域（多源一致）

## 6. 自建应用准入门槛

来源：WebSearch 多源（官方帮助中心 open.work.weixin.qq.com/help2/pc/14936、知乎、微伴助手、meta.appinn.net/t/topic/37816）

- 个人无需营业执照可注册企业微信（未验证企业）
- 人数口径：未验证企业默认 200 人；官方帮助中心 2023 后口径「未认证企业可使用人数上限 100 人」；已验证 1000 人；已认证理论上无上限
- ⚠️ 存疑待确认：社区报告（appinn 论坛，时间点近）称个人注册的未验证/未认证企业做自建应用消息推送「近期似乎受到接入限制」——未在官方文档找到对应说明，需人类向 IT 或实测确认
- 在已有公司组织内创建自建应用需管理员身份或由管理员操作（管理后台权限体系）

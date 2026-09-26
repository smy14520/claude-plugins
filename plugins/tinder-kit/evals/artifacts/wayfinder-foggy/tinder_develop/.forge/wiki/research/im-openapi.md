---
title: 公司 IM 开放平台能力全景（企业微信 / 钉钉 / 飞书）
tags: [im-integration, external-api]
checked: 2026-09-26
source: .forge/research/im-openapi/
---

# 公司 IM 开放平台能力全景（企业微信 / 钉钉 / 飞书）

面向「团队任务平台」可能的三家 IM 集成对象的长期认知。能力与时点以查证日为准（2026-09-26），原始证据见 `.forge/research/im-openapi/raw/`。

## 能力拓扑

- **零门槛层（无需企业管理员审批）**：三家的群机器人 webhook——单向推送 text/markdown/卡片。限流：企微 20 条/分钟、钉钉 20 条/分钟（强制关键词/加签/IP 三选一）、飞书 100 次/分钟 + 5 次/秒（关键词/IP/签名可选）。适用于：到期提醒、digest、告警通知。
- **应用层（需企业管理员审批）**：自建应用解锁——应用消息直达个人、OAuth 网页登录（三家都是授权码模式 + 扫码登录）、事件回调（双向交互）、任务/日历/待办 API。
- **API 丰度**：飞书（task v2 + calendar v4，均支持 tenant/user 身份）≈ 钉钉（待办 + 日历 + 忙闲）> 企微（日历/日程族完整，但无任务创建 API）。

## 时序与机制

- 机器人 webhook：POST JSON，即发即走，无鉴权握手（安全靠 webhook 保密 + 关键词/签名/IP 白名单）。
- 自建应用：corpid/corpId + AppSecret 换 access_token（企微 qyapi、钉钉 oapi/api、飞书 tenant_access_token）→ 调服务端 API。飞书另有 user_access_token（用户身份）。
- OAuth：三家端点分别为企微 `wwlogin/sso/login`（Web 登录）与 `oauth2/authorize`（客户端内）、钉钉 `login.dingtalk.com/oauth2/auth`、飞书 `authen/v1/authorize`。

## 限制与核心约束

- 群机器人是单向的：飞书官方明文不能响应用户消息；双向交互必须自建应用 + 事件回调。
- 自建应用在「公司已有组织」内一律需要管理员介入（企微管理后台建应用、钉钉开发者权限 + 发布审批、飞书发版审核）。
- 个人试用路径：自建组织/租户当管理员，全流程自批；企微未验证企业有 100~200 人上限且社区报告 API 权限收紧（存疑）。

## Gotcha

- 钉钉机器人超限错误码 `1302 send rate limited`，本分钟剩余消息全部丢弃（不是排队）。
- 飞书 user_access_token 在用户授权 365 天后强制要求用户重新授权，登录态设计需处理一年期失效。
- 钉钉 OAuth 的 redirect_uri 必须与开放平台配置完全一致；企微扫码登录需先配置授权回调域。
- 飞书卡片消息（自定义机器人发的 interactive）不支持回调交互，仅支持跳转链接。

## 原始证据指针

- 调研工作区：`.forge/research/im-openapi/`（index.md 导航；raw/ 含三家官方文档出处 URL + 查证日期 + 原文摘录；notes/comparison.md 为对比表）。

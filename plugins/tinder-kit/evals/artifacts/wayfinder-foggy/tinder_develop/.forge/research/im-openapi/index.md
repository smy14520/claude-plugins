# Research Index — 公司 IM 开放 API 调研（企业微信 / 钉钉 / 飞书）

调研完成于 2026-09-26。服务决策票：`.forge/tasks/team-task-platform/issues/04-公司IM开放API调研.md`（已 resolved）。下游：ticket 06「到期提醒通道与时机」、map「IM 集成产品形态」。

## 结论一句话

三家的群机器人 webhook 都是零审批门槛的单向推送通道（20~100 条/分钟，够提醒场景用）；应用级深度集成（双向交互、OAuth 登录、任务/日历 API）三家都有但都需企业管理员审批；API 丰度上飞书 ≈ 钉钉 > 企微（企微无任务创建 API）。**公司实际用哪家 IM 未确认，是遗留的人类待决项。**

## 核心认知（详细对比见 notes/comparison.md）

- 消息推送：三条零门槛路——群机器人 webhook（三家一致）；应用消息推送三家都有但需自建应用（管理员审批）。
- OAuth 网页登录：三家都提供（授权码模式 + 扫码登录），形态趋同。
- 任务/日历 API：飞书 task v2 + calendar v4 齐全；钉钉待办 + 日历齐全；企微仅日历/日程族完整、无任务 API。
- 准入门槛：个人/小团队试用路径 = 自己注册组织/租户当管理员（企微未验证企业有 100~200 人与 API 收紧风险，存疑）。

## 资料清单

| 文件 | 内容 | 出处与抓取状态 |
|---|---|---|
| `raw/wecom.md` | 企业微信：群机器人 91770（抓取成功原文）、message/send、日历族 93647（抓取成功）、OAuth 章节、准入门槛 | 官方 developer.work.weixin.qq.com + 官方帮助中心；OAuth 与待办部分为搜索索引转述 |
| `raw/dingtalk.md` | 钉钉：自定义机器人（安全设置/20条每分钟）、工作通知 asyncsend_v2、开发者权限门槛、待办/日历 API、新版 OAuth | 官方 open.dingtalk.com（JS 渲染无法直接抓正文，全部为官方 URL + 多源一致转述） |
| `raw/feishu.md` | 飞书：自定义机器人（抓取成功原文，含 100次/分钟）、im/v1 消息、task v2、calendar v4（抓取成功原文）、OAuth + 365 天重授权 gotcha、发版审核门槛 | 官方 open.feishu.cn 两个页面直抓，其余为官方文档索引转述 |
| `notes/comparison.md` | 三家能力对比表、关键差异的工程含义、存疑项清单 | 汇总自上述 raw |

## Wiki 晋升

长期认知已归档：`.forge/wiki/research/im-openapi.md`（外部系统全景）。

## 交棒建议

结论已折入 ticket 04 的 Answer（对比表 + 对 ticket 06「到期提醒」与远期 IM 集成的建议 + 人类 checklist）。下一步：ticket 06 可开工（设计提醒通道时按「webhook provider 抽象 + 站内兜底」落地）；人类拿到「公司用哪家 IM」答案后，只需在 provider 层填对应适配器，必要时回看本工作区 raw/ 里的端点与限流参数。

---
name: "Release-Watch: 依赖外部 API 事实的小工具"
description: "构建查询 GitHub 仓库 release 的 CLI，设计取决于第三方 API 的真实契约（端点、分页、限流、鉴权），考察访谈中是否主动查证外部事实（research）而不是凭记忆拍板"
type: e2e
prompt: "用 Python 写一个命令行小工具 release-watch：输入一个 GitHub 仓库（owner/repo），列出它最近 N 个正式 release 的版本号、发布日期和距今天数。只用标准库，不引入第三方依赖。"
setup_project: true
max_turns: 20
---

# 需求底牌卡 (Ground Truth Spec)

## 1. 项目目标 (Goal)
单机 Python CLI `release-watch <owner/repo> [-n N]`，列出最近 N 个正式 release（默认 5）的 tag、发布日期（YYYY-MM-DD）与距今天数。

## 2. 外部事实（需要查证，而不是凭记忆）
- GitHub REST API 端点 `GET /repos/{owner}/{repo}/releases`，支持 `per_page` 分页参数；
- release 对象含 `draft`、`prerelease` 字段——"正式 release" 需排除这两类；
- 未鉴权请求有较低的限流额度，超限返回 403/429；可通过 `GITHUB_TOKEN` 环境变量携带 token 提升额度；
- 仓库不存在返回 404。

## 3. 约束 (Constraints)
- 只用标准库（`urllib`、`json`、`datetime`、`argparse`）；
- 测试不得访问真实网络：HTTP 层需要可替换的 Seam。

## 4. 边界约束 (Out of Scope)
- 不做 Web 界面、不做本地缓存数据库、不做 GitLab 等其他平台。

---

# 督导官人设与主观评价焦点 (Supervisor Taste & Focus)

## 1. 督导官人设 (Persona)
- 你是想要这个小工具的开发者，对 GitHub API 细节并不熟；被问到 API 细节（限流、分页、字段含义）时回答"我不清楚，你查一下"。
- 被问到产品选择（默认 N、是否包含 prerelease、输出格式）时直接拍板，回答 1~2 句。

## 2. 核心主观评价焦点 (Qualitative Focus)
- **事实查证**：访谈或实现中，是否主动查证 API 契约（调用 research、查官方文档），而不是把 API 细节问题抛给用户？
- **Seam**：网络访问是否隔离在可替换的接口后面，测试是否离线？
- **错误路径**：404、限流、网络失败是否有友好的报错与非零退出？

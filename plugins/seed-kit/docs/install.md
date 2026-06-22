# 安装与三种 review 模式

## 为什么需要安装

Claude Code 插件**不分发 workflow**（`workflows/` 非插件标准目录）。所以 review-loop workflow 不能随插件自动可用——要手动装到项目 `.claude/workflows/`。

## 安装 review-loop（模式 2：workflow）

在项目根目录跑：

```bash
bash <path-to-seed-kit>/scripts/install-review-loop.sh
```

它会把 `templates/review-loop.template.js` 复制成项目的 `.claude/workflows/review-loop.js`。**重启 Claude Code** 后 `/review-loop` 注册可用：

```
/review-loop task=family-ledger slice=S-005 repo=/path/to/project
```

## 三种 review 模式（选哪种由用户指定或 Claude 按场景，不在 review SKILL）

| 模式 | 触发 | 适合 | 要装吗 |
|---|---|---|---|
| **subagent（轻）** | Claude 自主用 Agent tool 派 `seed-kit:seed-review` | 简单 slice / 快速查 | 不用 |
| **workflow（中）** | `/review-loop` | 标准 review（多 agent + loop） | 要（上面 install） |
| **agent team（重）** | Claude 自主 TeamCreate 组 architect-A/B + devil's-advocate | 高价值 / 架构争议 | 不用（实验性） |

review SKILL 只管"审什么"（知识），不规定用哪种模式——那是编排，由 workflow / Agent tool / TeamCreate 各自承担。

## 已知待验证点

`/review-loop` 跑时，workflow 里的 `agentType: 'seed-kit:seed-*'` 能否解析到插件 agent——重启后第一次用 `/review-loop` 时重点确认（不报 `not found` 即通；若报错，fallback 是 template 改用通用 agent，或退到 subagent 模式）。

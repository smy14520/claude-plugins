# 页面类型与内容契约

`.wiki/` 页面按用途写，不按僵硬抽屉写。所有页面都应有 `description`，方便 `sdd-wiki index/search/collect` 给 AI 快速判断是否需要细读。

## 通用 frontmatter

```yaml
---
title: <中文标题>
description: <中文一行检索提示>
tags: [<domain>, ...]
type: module | cross_cut | entity | concept | gotcha | decision | source
summary: <中文紧凑摘要>
last_updated: YYYY-MM-DD
---
```

`last_updated` 记录页面最近一次实质内容修改的日期；定义与同步规则见 `operations.md` Frontmatter 最小契约。

## type: module

来自 sdd-kit package 的稳定模块卡片。通常由 `sdd-arbor module-summary <package> --json` 生成 packet 后写入。

推荐位置：`.wiki/Modules/<中文标题>.md`。

必需 frontmatter：

```yaml
---
title: 余额账本
description: 余额账户、流水、充值、扣款、退款和幂等 contract
tags: [module, backend, ledger]
last_updated: 2026-05-07
type: module
package: balance-ledger
source: arbor
source_checkpoint: <sha>
summary: <中文紧凑摘要>
---
```

推荐结构：

```markdown
# 余额账本

## 摘要
## 对外契约
## 关键文件与稳定定位
## 不变量
## 测试
## 相关模块
## 验证记录
```

Module note 不写 line numbers。定位用：

- file path + class/function/method name
- route name / API operation id
- table / index / migration id
- config key / env key
- test name
- contract request id

## type: cross_cut

跨模块同步改动页。大项目里"做某类操作必须同步改 N 处"是高价值场景：导出函数、API 路由注册、enum 同步、数据库迁移、权限映射等。`cross_cut` 页面承载这种“做什么动作要看哪些地方”的备查页。

**命名原则**：页面名直接用**那件事的名字**——动作短语或领域名，不加统一后缀。名字本身要 self-explanatory，不需讲解。

示例：

- `新增导出`
- `API 路由注册`
- `新增 enum 值`
- `数据库迁移`
- `权限映射`
- `配置项注册`

**不推荐**“X 散点 / X 触点 / X 清单 / X 地图”这类合成后缀——本页类型已由 `type: cross_cut` 表达，页名不需重复分类信息。

推荐 frontmatter（`type: cross_cut` 是结构化分类；`cross-cut` tag 仍建议保留，方便按 tag 聚合和自然语言检索）：

```yaml
---
title: 新增导出
description: 新增导出函数时全项目需同步修改的位置与命名规则
tags: [cross-cut, exports, backend]
type: cross_cut
summary: 新增导出时必须同步检查的 N 处位置与命名规则
last_updated: 2026-05-07
---
```

推荐结构：

```markdown
# 新增导出

## 适用场景
新增导出 / 修改导出签名 / 删除已弃用导出。

## 同步修改位置（按模块）

### auth 模块
- 位置定位：`services/auth/exports.py`、`api/auth_routes.py`
- 命名规则：`auth_export_{kind}`
- 详细函数清单见 [[Modules/auth]] § 对外契约

### payment 模块
- 位置定位：`services/payment/exports.py`、`api/payment_routes.py` 的 `register`
- 命名规则：`payment_exporter_{kind}`（历史包袱，注意与 auth 不一致）
- 详细函数清单见 [[Modules/payment]] § 对外契约

## 命名映射表
跨模块命名差异的权威记录（这是本页 single source）：

| 模块 | 命名前缀 | 历史原因 |
|---|---|---|
| auth | `auth_export_*` | 早期约定 |
| payment | `payment_exporter_*` | 第三方对接遗留 |

## 验证步骤
做完新增导出后，用 `grep -rE "(auth_export_|payment_exporter_)" services/ api/` 确认所有位置已同步。
```

要点：

- **同步修改位置**列表是本页 single source。
- 各模块的**函数签名细节**用 `[[Modules/<name>]] § 对外契约` 引用，不复制（见 `anti-patterns.md` AP11）。
- 跨模块**命名映射表**是本页独有 single source（任何单模块都看不到全貌）。
- 命名 stable section 标题（`## 同步修改位置`、`## 命名映射表`），避免 PRD anchor 漂移。

## type: entity

真实对象：服务、API、数据库表、外部系统、队列、存储。记录跨文件才能重建的信息、边界、调用拓扑、不可见约束。

## type: concept

抽象模式或方法论。去掉专有名词后仍成立。写适用场景、核心思想、权衡、应用示例。

## type: gotcha

具体场景 + 具体症状 + 根因 + 已验证解决方案。保持短小。

## type: decision

记录选择及理由。写背景、选项、决定、后果、何时重审。

## type: source

外部资料摘要。保留来源、为什么重要、关键摘录、适用边界。

---

## 内容权威性与跨页引用

`.wiki/` 鼓励**纵向 module page + 横向 cross-cut page** 共存（见 `index-and-root.md`）。两种视角难免触及同一内容（例：auth 模块导出函数既属于 `Modules/auth.md`，也属于 `新增导出.md`）。处理原则：

1. **每个内容片段只在一个 page 权威定义**（single source）。
2. **另一页用 wikilink + 一行 anchor 引用**，不复制完整内容。
3. **判断 single source 归属**：
   - 内容只对单个模块成立 → single source 在 module page。
   - 内容跨模块才有意义（命名映射、规则比较、跨域联动） → single source 在 cross-cut page。
4. **stable section 标题**：被引用的 section 标题保持稳定（如 `## 对外契约`、`## 同步修改位置`），重命名前先 grep 是否被其他 page 或 PRD 引用。

详见 `anti-patterns.md` AP11。

---

## PRD 引用 wiki 的范式

brainstorm 写 PRD 时，如果 Technical Framing 触及 cross-cut 模式（导出/路由/enum/迁移/权限/配置等），可以引用 wiki cross-cut 页面作为防漏辅助，但必须遵循三层结构：

```markdown
## Technical Framing

### 影响范围

新增导出功能，涉及全项目多处同步修改。

- **核心 scope**：在 auth 模块新增 `auth_export_user_session(user_id) -> Session`，签名见下；触发 GET `/api/auth/session/export`。
- **同步修改位置**：详见 [[新增导出]] § 同步修改位置 / § 命名映射表。
- **预期位置数**：5 处（brainstorm 调研结果，wiki 实际清单可能更新）。
- **Fallback**：若 wiki 页面缺失或与 brainstorm 时不一致，impl 调研代码逐一识别；识别完成后建议向用户提议 ingest 到 wiki。
```

三层属性：

| 层 | 内容 | 是否自包含 |
|---|---|---|
| 1. 核心 scope | 函数名 + 签名 + 路由 | ✅ wiki 全删 impl 仍知道做什么 |
| 2. 位置细节 | `详见 [[页面]] § 章节` | ❌ 依赖 wiki，但只是“防漏” |
| 3. Fallback | “若页面缺失则 impl 调研” | ✅ 自包含降级路径 |

使用前提：

- brainstorm 写 wikilink 前先 `sdd-wiki collect --query "<keyword>" --limit 5 --json`，只引用结果中实际返回的 page title/path；未命中就不写引用，直接让 impl 调研。
- 单模块 / 单文件 / 纯算法改动**不需要**引用 wiki。只在涉及 cross-cut 模式时引用。
- 不把 wiki 全文复制进 PRD（违反 AP11 single-source 原则）。

详见 `anti-patterns.md` AP7a / AP7b。

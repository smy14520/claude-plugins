---
command: /module-index
description: 生成模块索引（支持轻模块/重模块）
---

# /module-index

为项目模块生成 **AI 可执行的模块地图**，让 AI 和开发者快速知道模块负责什么、怎么分块、主链路是什么、该从哪里继续下钻。

## 用法

```bash
/module-index <模块路径>
/module-index app/Modules/User
/module-index <路径> --update  # 更新已有索引
```

## 路径说明

**索引存储在项目目录**：`./.claude/modules/`

```bash
# 在项目目录执行
/module-index app/Modules/User

# 轻模块保存到
→ ./.claude/modules/User-index.md

# 重模块还可额外生成
→ ./.claude/modules/User/INDEX.md
→ ./.claude/modules/User/<Submodule>-index.md
```

## 设计目标

`module-index` 不是目录摘要，而是 **模块导航图**。它要优先回答：

1. 这个模块负责什么
2. 这个模块怎么分块
3. 核心主链路是什么
4. 关键入口在哪里
5. 哪些点最容易误判
6. 继续深挖时应该读哪个子索引

## 控制范围

本命令明确**不做**：

- 不把每个模块都写成长篇说明书
- 不为每个类/方法逐个写解释
- 不让 `INDEX.md` 承担正文内容
- 不做三层以上递归索引
- 不按目录机械拆出很多子索引

> 原则：**优先高价值信息，不做无限膨胀。**

## 输出层级

### Level 0：全局模块索引

```text
.claude/modules/INDEX.md
```

只做全项目定位，不展开模块正文。

### Level 1：模块主索引

```text
.claude/modules/<Module>-index.md
```

这是模块总览页，必须能独立回答“这个模块是什么、怎么运转、先看哪”。

### Level 1.5：子模块索引（仅复杂模块启用）

```text
.claude/modules/<Module>/INDEX.md
.claude/modules/<Module>/<Submodule>-index.md
```

只在复杂模块中启用，用于按需加载更细的子域说明；不继续往下递归。

## 模块分类

### 轻模块（light）

满足以下大多数特征时，判为轻模块：
- 职责单一
- 目录浅
- 没有多个稳定业务子域
- 没有复杂状态流
- 没有明显特殊流/例外分支
- 外部依赖少

**产出**：只生成一个主索引文件。

### 重模块（heavy）

满足以下任意 **2 条以上**，判为重模块：
- 存在 3 个以上稳定业务子域
- 有明确核心主链路（如消息流、计费流、接管流）
- 有多渠道 / 多角色 / 多状态分流
- 有明显缓存 / Event / Job / Listener 副作用
- 有多个外部依赖系统
- 存在高频误判点或特殊流

**产出**：主索引 + 子模块索引目录 + 2–4 个子索引。

### 子索引数量限制

- 每个重模块最多 **4 个**子索引
- 超过 4 个时，先合并相近子域
- 不允许生成第 3 层索引

## 拆分原则

### 优先按业务子域拆

推荐按这些维度拆：
- 消息流
- 状态与缓存
- AI 回复链路
- 计费流
- Admin 配置
- 渠道接入
- 权限/审核
- 模板/场景

### 不优先按目录拆

不要优先拆成：
- `Services-index`
- `Repositories-index`
- `Controllers-index`

除非这个目录本身就等于一个稳定业务子域。

> 原则：**AI 更需要业务地图，不只是文件夹地图。**

## 执行流程

1. 分析模块目录结构
2. 判断是轻模块还是重模块
3. 识别关键入口、核心类、依赖与主链路
4. 轻模块：生成主索引
5. 重模块：生成主索引，并按需生成子模块索引目录与少量子索引
6. 更新 `./.claude/modules/INDEX.md`

## 轻模块主索引模板

轻模块主索引应尽量控制在 **60–100 行**，回答 5 个问题：
- 负责什么
- 目录结构是什么
- 关键入口是什么
- 关键类/服务是什么
- 依赖什么

```markdown
# User 模块

> 路径: `app/Modules/User`
> 更新: 2026-02-11
> 类型: 轻模块索引

## 职责
用户注册、登录、个人信息管理等功能。

## 目录结构
```text
app/Modules/User/
├── Api/UserController.php
├── Services/
│   ├── UserService.php
│   └── AuthService.php
├── Models/User.php
└── Repositories/UserRepository.php
```

## 关键入口

**API 端点**
- `POST /api/user/login` - 用户登录
- `POST /api/user/register` - 用户注册
- `GET /api/user/profile` - 获取个人信息

**核心类**
- `UserController` - 用户请求入口
- `UserService` - 用户业务逻辑
- `AuthService` - 认证逻辑

## 依赖
- `Common/Database` - 数据库访问
- `Redis` - 用户会话缓存
```

## 重模块主索引模板

重模块主索引目标控制在 **120–220 行**，必须回答 8 个问题：
- 模块整体职责
- 稳定子域有哪些
- 核心主链路是什么
- 外部入口在哪
- 核心类/服务如何分工
- 依赖哪些模块/系统
- 哪些点最容易误判
- 继续深挖应该看哪个子索引

```markdown
# CustomerService 模块

> 路径: `app/Modules/CustomerService`
> 更新: 2026-04-14
> 类型: 重模块索引
> 子索引: [INDEX.md](./CustomerService/INDEX.md)

## 职责
统一接入多渠道客服、管理会话状态、人工接管与 AI 回复链路。

## 子域地图
| 子域 | 主要职责 | 关键文件/类 |
|------|----------|-------------|
| 渠道接入层 | 屏蔽不同客服渠道差异 | `Channels/*`, `ChannelManager` |
| 状态与缓存层 | 管理接待状态、缓存一致性 | `CustomerServiceCacheManager`, `Listeners/*` |
| AI 回复层 | AI 自动回复与异步发送 | `ReplyMessageJob`, `SendCustomerReplyJob` |

## 核心主链路
### 链路 1
```text
渠道消息进入 → ChannelManager 分发 → 状态判断 → AI/人工分流 → 发送
```

## 模块分层理解
### Controller 层
### Service 层
### 状态/缓存层
### 异步/事件层

## 关键入口

**API 端点**
- `POST /api/admin/customerService/toggleTakeoverStatus` - 切换人工接管状态
- `GET /api/admin/customerService/getMessageList` - 获取会话消息列表

**核心类**
- `CustomerServiceService` - 业务编排主入口
- `ChannelManager` - 渠道分发核心
- `CustomerServiceCacheManager` - 状态缓存中心

## 关键状态 / 核心判断
- 当前是否人工接管
- 当前 AI 绑定是否有效
- 当前缓存状态是否最新

## 外部依赖
- `AICreationCenter` - AI 绑定与回复能力
- `Wecom / WxEcShop` - 外部客服渠道能力

## 易混淆点
- Channel 抽象统一，不代表行为完全一致
- AI 删除 / 设置更新会通过 Listener 隐式改变状态

## 推荐继续下钻的子模块索引
- `StateAndCache-index.md`
- `AIReply-index.md`
- `Channels-index.md`
```

## 子模块索引目录模板

仅重模块启用：

```markdown
# CustomerService 子模块索引

> 上级模块: [CustomerService-index.md](../CustomerService-index.md)
> 最后更新: 2026-04-14

| 子模块 | 索引文件 | 作用 | 适用场景 |
|--------|----------|------|----------|
| AIReply | [AIReply-index.md](./AIReply-index.md) | AI 自动回复、人工接管与异步发送链路 | AI 没回 / 回错 / 分流异常 |
| StateAndCache | [StateAndCache-index.md](./StateAndCache-index.md) | 状态缓存、事件清理、配置变更副作用 | 接管状态异常 / AI 删除残留 |
| Channels | [Channels-index.md](./Channels-index.md) | 不同渠道的消息结构、发送能力与差异 | 渠道行为不一致 |
```

**规则**：
- 只保留一张表格 + 元信息
- 每行必须有“适用场景”
- 不展开正文

## 二级子索引模板

二级子索引目标控制在 **80–180 行**，必须回答：
- 这个子域负责什么
- 跟主模块的关系是什么
- 相关文件有哪些
- 相关 API / 入口有哪些
- 核心主链路是什么
- 状态点 / 决策点是什么
- 易混淆点是什么
- 排查问题先看哪里

```markdown
# CustomerService / AIReply 子模块

> 上级模块: `CustomerService`
> 路径范围: `Services`, `Channels`, `Jobs`
> 适用: 排查 AI 自动回复、人工接管、异步发送时优先阅读

## 这个子模块负责什么
负责消息进入后是否走 AI 回复、如何异步发送、何时被人工接管中断。

## 相关文件
| 文件/类 | 作用 |
|--------|------|
| `ChannelManager` | 按渠道分发 |
| `ReplyMessageJob` | 回复异步任务 |

## 相关 API / 操作入口
| 端点/入口 | 说明 | 为什么重要 |
|-----------|------|-----------|
| `POST /api/admin/customerService/toggleTakeoverStatus` | 切换人工接管状态 | 这是 AI 回复是否继续生效的关键分流点 |

## 核心主链路
### 链路 1
```text
渠道消息进入 → ChannelManager 分发 → 状态判断 → ReplyMessageJob → SendCustomerReplyJob
```

## 决策点 / 状态点
- 当前是否人工接管
- 当前 AI 绑定是否有效

## 最容易误判的地方
- AI 没回复不一定是模型问题，也可能是 takeover 或缓存状态问题

## 排查顺序
### 场景 1：AI 没有自动回复
1. 查 takeover 状态
2. 查缓存状态
3. 查 ReplyMessageJob
```

## API 端点描述规则

### 一级模块索引中的 API

格式：

```markdown
- `POST /api/...` - 一句话说明
```

规则：
- 只列关键 API
- 推荐 6–12 个
- 每个端点只允许一句话
- 不解释参数细节

### 二级索引中的 API

格式：

```markdown
| 端点 | 说明 | 为什么重要 |
|------|------|-----------|
```

规则：
- 只列与该子域直接相关的 API
- 推荐 3–6 个
- “为什么重要”必须说明它在当前子域中的作用
- 不是所有 API 都要在每个子索引重复出现

## 信息密度规则

### 必须写
- 模块职责
- 子域划分
- 核心主链路
- 关键入口
- 关键状态 / 判断
- 依赖
- 易混淆点
- 排查入口

### 不该写太多
- 每个文件逐个解释
- 每个方法的说明
- 明显能从代码直接看出来的内容
- 太长的教程式介绍
- 泛泛而谈的“最佳实践”

> 原则：**优先写 AI 不容易从目录树和函数名直接推出来的信息。**

## 长度控制

- 全局模块索引：只允许元信息 + 一张表
- 轻模块主索引：目标 60–100 行
- 重模块主索引：目标 120–220 行
- 二级子索引：目标 80–180 行
- 子索引数量：每个重模块最多 4 个

## 全局 `INDEX.md` 格式

> ⚠️ `./.claude/modules/INDEX.md` 仍然是纯索引文件！只做“查找 → 定位”，不重复模块正文。

```markdown
# 模块索引

> 最后更新: <日期>
> 模块总数: <数量>

| 模块 | 路径 | 索引文件 | 类型 | 一句话职责 | 子索引 |
|------|------|----------|------|-----------|--------|
| CustomerService | app/Modules/CustomerService | [CustomerService-index.md](./CustomerService-index.md) | heavy | 多渠道客服接入、会话状态、人工接管与 AI 回复调度 | 3 |
| User | app/Modules/User | [User-index.md](./User-index.md) | light | 用户注册、登录与资料管理 | - |
```

**INDEX.md 规则**：
- ✅ 只有一张表格 + 元信息
- ✅ `一句话职责` 限制为一句话
- ✅ `子索引` 只写数量或 `-`
- ❌ 不要在这里塞主链路、依赖、风险点、技术栈分类
- 📌 模块详情只放在模块主索引与子索引中

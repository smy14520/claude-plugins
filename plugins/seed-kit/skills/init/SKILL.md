---
name: init
description: "新项目初始化时推荐默认基准。把 Fowler 12 味坏味道作为代码审查默认基准，推荐写入项目的 CLAUDE.md 或 .claude/rules/。仅用户主动触发。"
---
# Init — 新项目默认基准推荐

> 调用名：`seed-kit:init`（全名见 conventions.md 登记表，别加 `seed-` 前缀）。

新项目初始化时，向用户推荐代码审查默认基准。**推荐而非强制**——项目决定是否采纳，采纳后写入项目自己的标准文件（标准在项目，插件不内置）。

## 推荐内容

**代码审查默认基准**：Fowler 12 味坏味道（《重构》ch.3）——项目未提供代码标准时，review 用它做默认基准：

- **Mysterious Name** — 名字看不出用途
- **Duplicated Code** — 重复逻辑
- **Feature Envy** — 方法伸手拿别的对象的数据
- **Data Clumps** — 同组字段老一起出现
- **Primitive Obsession** — 用基本类型代替领域概念
- **Repeated Switches** — 对同一类型反复 switch
- **Shotgun Surgery** — 一个改动散落多处
- **Divergent Change** — 一个文件为多个原因变
- **Speculative Generality** — 为不存在的需求加抽象
- **Message Chains** — 长串 a.b().c() 导航
- **Middle Man** — 纯转发
- **Refused Bequest** — 子类忽略大部分继承

三条绑定规则：项目文档化标准优先（repo 标准覆盖基线）；每条是判断不是硬违规；工具已强制的不重复报。

## 写入位置

用户确认采纳后，写入项目标准文件（看项目已有结构）：
- 有 `.claude/rules/` → 写 `code-review-baseline.md`
- 只有 `CLAUDE.md` → 追加一节

## 停止

用户确认采纳或明确拒绝后停止。不自动改文件——先推荐，等用户拍板。

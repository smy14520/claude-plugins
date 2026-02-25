---
description: 沉淀经验
agent: knowledge-engineer
subtask: true
---

调用 **knowledge-engineer** 沉淀经验。

## 用法

```
/extract-experience <名称>
/extract-experience <名称> --common   # 沉淀为通用经验
```

等价于：`$ARGUMENTS` 为名称。

## 核心原则：普适性优先

> ⚠️ **关键要求**：经验文档必须具有普适性（可复用性）。
> 记录的不是"这次具体做了什么"，而是"下次再遇到同类问题该怎么做"。

### 普适性检查清单

在生成经验之前，对每一条内容自检：

- ❌ **反例**（不要写）：`给 Agent 添加了 name、description、tools 三个字段`
- ✅ **正例**（应该写）：`给智能体添加新字段的通用流程：1) 在 schema 中定义字段类型 2) 在 model 层添加字段 3) 在 API 层暴露字段 4) 更新相关测试`

泛化规则：
1. **去掉具体值**：用 `<字段名>` `<文件路径>` 等占位符替代具体名称
2. **提炼步骤模式**：从具体操作中抽象出"先做什么、再做什么"的通用步骤
3. **标注变化点**：哪些部分是每次都一样的，哪些部分需要根据情况调整
4. **补充判断依据**：什么情况下选择方案 A，什么情况下选择方案 B

## 执行（严格按顺序，不可跳过任何步骤）

1. 调用 **knowledge-engineer** subagent
2. 提取关键信息，**必须按普适性原则泛化**
3. 产出 `./.claude/experience/$ARGUMENTS.md`
4. **【必须】更新 `./.claude/experience/INDEX.md`**（格式见下方）
5. 询问："发现规律？使用 /optimize-flow 沉淀为规则"

## INDEX.md 更新规则（不可跳过）

每次生成经验文档后，**必须立即**更新 `./.claude/experience/INDEX.md`。

如果 INDEX.md 不存在，先创建：

```markdown
# 经验索引

> 自动维护，记录所有沉淀的经验文档。

| 名称 | 标签 | 关键文件 | 更新日期 |
|------|------|---------|---------|
```

然后在表格末尾追加一行：

```markdown
| [<名称>](./<名称>.md) | `tag1`, `tag2` | `file1`, `file2` | YYYY-MM-DD |
```

> ⚠️ 如果你没有更新 INDEX.md，这次任务视为**未完成**。


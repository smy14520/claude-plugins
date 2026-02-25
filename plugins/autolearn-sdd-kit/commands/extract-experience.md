---
command: /extract-experience
description: 沉淀经验
agent: KnowledgeEngineer
---

# /extract-experience

调用 **KnowledgeEngineer**（知识工程师）沉淀经验。

## 用法

```bash
/extract-experience <名称>
/extract-experience <名称> --common   # 沉淀为通用经验
```

## 执行步骤

你必须依次完成以下 3 个动作，每个动作都产出一个文件操作，缺一不可：

### 动作 1：生成经验文档

按 KnowledgeEngineer 的产出模板，写入 `./.claude/experience/<名称>.md`。

**写之前先自检普适性**（详见下方"普适性规则"）。

### 动作 2：更新 INDEX.md

读取 `./.claude/experience/INDEX.md`：
- 如果文件**不存在**，创建它，内容为：

```markdown
# 经验索引

> 自动维护，记录所有沉淀的经验文档。

| 名称 | 标签 | 关键文件 | 更新日期 |
|------|------|---------|---------|
| [<本次名称>](./<本次名称>.md) | `tag1`, `tag2` | `file1`, `file2` | YYYY-MM-DD |
```

- 如果文件**已存在**，在表格末尾追加一行：

```markdown
| [<本次名称>](./<本次名称>.md) | `tag1`, `tag2` | `file1`, `file2` | YYYY-MM-DD |
```

### 动作 3：完成确认

向用户输出：
1. ✅ 经验文档已生成：`./.claude/experience/<名称>.md`
2. ✅ 索引已更新：`./.claude/experience/INDEX.md`
3. 询问："发现规律？使用 /optimize-flow 沉淀为规则"

> 如果你在动作 3 中无法确认动作 2 已完成，说明你漏掉了，请立即补做。

---

## 普适性规则

经验文档必须具有普适性（可复用性）。记录的不是"这次具体做了什么"，而是"下次再遇到同类问题该怎么做"。

写之前对每一条内容自检：

- ❌ **反例**：`给 Agent 添加了 name、description、tools 三个字段`
- ✅ **正例**：`给智能体添加新字段的通用流程：1) 在 schema 中定义 2) 在 model 层添加 3) 在 API 层暴露 4) 更新测试`

泛化技巧：
1. **去掉具体值**：用 `<字段名>` `<文件路径>` 等占位符替代
2. **提炼步骤模式**：从具体操作中抽象出通用步骤顺序
3. **标注变化点**：哪些每次一样，哪些需要根据情况调整
4. **补充判断依据**：什么情况下选方案 A，什么情况下选方案 B


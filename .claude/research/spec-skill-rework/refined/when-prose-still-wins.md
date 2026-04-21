---
finding-type: constraint
confidence: medium
date: 2026-04-21
---

<!-- 输出语言: 中文 -->

# 哪些规则不能结构化 —— 必须保留在散文里

## 发现内容

"模板承重"不是万能。有几类规则**结构无法表达**,硬塞进模板反而让模板失去指导性。通过对比 KEP / RFC / SpecKit 的做法,可以识别这些"散文仍是最优解"的规则类型。

### 类型 1: 判断性规则("什么时候应用")

模板只能呈现"结构应该长什么样",不能回答"什么情况下使用这个结构"。

**例子**:

- sdd-kit: "用户想修一个一行 bug → 跳过 spec,直接 impl"
- KEP: 模板本身从不说明"什么 enhancement 需要 KEP",这条规则在 SIG 的流程文档里
- SpecKit: "如果是 spike 或 exploratory prototype,显式说明 skip clarification"

**为什么必须散文**:
- 条件边界是模糊的("一行 bug" 包括只改 emoji 吗?)
- 需要上下文判断(项目规模、团队结构、现有技术债)
- 列举可能性会让模板膨胀,读者只想看"当前是不是该用它"的判定依据

### 类型 2: 语义/契约理由("为什么禁止 X")

模板可以通过结构上不给位置来**禁止**某件事(比如 sdd-kit 模板没有 Alternatives 章节),但**读者想知道"为什么禁止"**时仍需散文。

**例子**:

- sdd-kit: "不列出备选方案,因为被否决的选项在执行阶段是噪音" —— 这个因果只能散文讲
- Rust RFC: "Note that while precedent set by other languages is some motivation,
  it does not on its own motivate an RFC" —— 提醒作者别过度依赖先例,散文警告

**为什么必须散文**:因果关系的解释本身就是语言行为,不是结构体。

### 类型 3: 跨章节一致性规则("X 和 Y 必须对齐")

单个章节的约束可以结构化(一个章节有/无、占位符数量够/不够),**跨章节**的一致性(如 "acceptance 必须覆盖 goal 的每个动作")只能散文表达。

**例子**:
- sdd-kit: "验收标准必须覆盖正常路径、异常路径、幂等、可观测性" —— 可以拆成 4 个子标题(手法 5),但"这 4 类必须和 goal 对应"仍需散文
- KEP: "Beta criteria must include all functional, security, monitoring, and
  testing requirements" —— 一句散文 note
- Rust RFC: "Its interaction with other features is clear" —— 跨章节交互,散文

**为什么必须散文**:结构只管局部,全局一致性是语义层面的。

### 类型 4: 风格/品味指导("好例子长这样")

模板可以提供占位符,但"什么算好"/"什么算过度"的判断只能靠散文 + 示例。

**例子**:
- sdd-kit: "约束使用抽象能力 + 数值,而非技术选型(除非选型本身是硬约束)" —— 边界模糊,举例讲
- SpecKit: "Do not focus on the tech stack at this point" —— 散文禁令
- Rust RFC: "Corner cases are dissected by example" —— 风格指导

**为什么必须散文**:模板无法区分 "PostgreSQL" 是"硬约束"还是"过度指定",需要人判断。

### 类型 5: 流程性指导("什么时候做什么")

模板是**静态产物**,描述一个被填好的文件。"怎么一步步填它"是流程,属于 skill workflow,不是模板。

**例子**:
- sdd-kit: Frame → Decide → Finalize 的顺序,以及"Decide 阶段逐个决策不打包"
- SpecKit: `/speckit.clarify` 必须在 `/speckit.plan` 之前

**为什么必须散文**:模板没有时间维度。

## 来源

- `raw/ext-kubernetes-kep-template.md` 第 95-100 行("**Note:** Beta criteria must include...")
- `raw/ext-rust-rfc-template.md` 第 56-63 行(Reference-level explanation 的交互一致性)
- `raw/ext-github-speckit-readme.md` "Do not focus on the tech stack at this point"
- `raw/ext-github-speckit-readme.md` STEP 3 的 clarify 流程性指导
- `plugins/sdd-kit/skills/spec/references/content-contract.md` 多条

## 意义

**sdd-kit spec skill 瘦身不是全面删散文**,而是识别并保留这 5 类散文,把其它散文规则下沉到模板结构。

具体映射到当前 skill 的 5 个文件:

| 文件 | 应保留的散文类型 | 可下沉结构的类型 |
|------|----------------|----------------|
| `SKILL.md` | 类型 1(何时激活/不激活)、类型 5(原语流程骨架) | 其它 |
| `references/content-contract.md` | 类型 2(每节为什么禁 X)、类型 3(跨章节一致性)、类型 4(风格) | 每节该写什么 → 模板注释 |
| `references/workflow.md` | 类型 5(流程、边界情况) | 输出样例格式 → 统一格式说明 |
| `references/anti-patterns.md` | 类型 4(风格/品味)、类型 2(为什么是反模式) | 结构性反模式(如缺 non-goals)可被模板直接防住 |
| `assets/templates/spec.md` | (模板里只有结构和占位符) | 把能下沉的全吃进来 |

### 新的判断准则

提出一条简单判据:
> "如果把这条规则从文件里删掉,用户填模板时**会不会自然违反**?"
> - 会自然违反 → 必须保留在散文
> - 不会(因为模板结构已强制) → 可以删

## 待确认问题

- 类型 2(因果说明)的**粒度**:每条禁令都要解释原因吗?如果 SKILL.md 只写"禁止 X",references 里详解,会不会出现"读 SKILL.md 时不懂为什么禁"的问题?
- 类型 5 的流程描述和模板之间如何交叉引用?如"Finalize 步骤 3 的检查清单"和"模板 frontmatter 底部的自检块"如果都有,是否重复?

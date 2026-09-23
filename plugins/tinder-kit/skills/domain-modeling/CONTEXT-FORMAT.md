# CONTEXT.md Format

## 结构模板

```md
# {Context Name}

{一至两句话精炼说明：本 Context 是什么、为什么存在。}

## Language（领域统一语言表）

**Order**:
{一至两句话定义该实体的核心本质，定义是什么而非怎么做}
_Avoid_: Purchase, transaction

**Invoice**:
交货后向客户发出的正式请款凭据。
_Avoid_: Bill, payment request

**Customer**:
下单购买产品的主体（自然人或机构）。
_Avoid_: Client, buyer, account
```

## 核心撰写纪律

1. **Be opinionated（立场鲜明，消灭近义词）**：
   当团队内部有多个词汇指代同一概念时，强制选出唯一的一个官方词，并将其他混淆词一律列入 `_Avoid_`。
2. **Keep definitions tight（紧凑精炼）**：
   严格限制在 1~2 句话。定义它**“是什么”**，而不是展开描述它“怎么做”。
3. **Only include domain terms（只收本领域专有名词）**：
   只收录本业务领域独有的实体与概念，通用编程概念（如超时、异常类、缓存）不写入。
4. **按业务子域适度聚合**：当概念较多时，可以在 `## Language` 下使用三级标题归类分组。

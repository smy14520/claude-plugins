---
tags: [search, index]
---

# ADR-0003: CJK 二元组 + Latin 分词的混合倒排索引

## Status
Accepted（2026-09-25）

## Context
全文检索需要中文匹配能力，但纯标准库约束下无 jieba 等分词器。中文文本无法按空白切词。

## Decision
统一 token 化规则（`tokenize`）：Latin 与数字按 `\w+` 连续段切分并 casefold；CJK 连续段按**二元组（bigram）**切分（长度为 1 的残段取单字）。索引侧建 `postings: token → {page: tf}`，查询侧同样 token 化后取各 token 倒排的**交集**，按 TF 累加计分排序。

## Consequences
- "知识库" 可被 "知识"/"识库" 命中，中文检索可用；
- 纯标准库 ~几十行实现，索引体积可控（bigram 词表有界）；
- 代价：单词 CJK 查询需整字匹配（如查"库"无法命中"知识库"的 bigram）— 对个人检索场景可接受，记录在案。

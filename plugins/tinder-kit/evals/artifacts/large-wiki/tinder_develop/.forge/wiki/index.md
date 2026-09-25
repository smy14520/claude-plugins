# Wiki Index — 知识大盘

按标签检索请先读 [tags.md](tags.md) 对齐受控词汇。

## 架构决策（ADR）

| ADR | 决策 | 标签 |
| :-- | :--- | :--- |
| [0001](decision/0001-flat-case-insensitive-pagename.md) | 扁平命名空间 + 大小写不敏感 PageName | `wiki-syntax` |
| [0002](decision/0002-single-json-index-no-db.md) | 单文件 `.wiki_index.json`，严禁数据库 | `index` |
| [0003](decision/0003-cjk-bigram-latin-word-inverted-index.md) | CJK bigram + Latin 分词混合倒排 | `search` `index` |
| [0004](decision/0004-explicit-build-mtime-incremental.md) | 显式 build + mtime 增量，查询只读 | `index` |

## Gotchas

- `##tag`（井号后紧跟更多井号）不算 Tag；ATX 标题记号 `#{1,6}` + 空格整行豁免 tag 扫描，但行内的 `#标签` 仍计数。
- PageName 大小写不敏感匹配用 `casefold`，重名冲突在 build 时显式报错，绝不静默任选。

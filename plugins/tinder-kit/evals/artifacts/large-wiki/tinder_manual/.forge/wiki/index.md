# Wiki Index

项目知识大盘索引：架构决策（ADR）与经验沉淀的检索入口。检索前先读 [tags.md](tags.md) 对齐受控标签。

## Decisions（架构决策）

| ADR | 标题 | 标签 |
| :--- | :--- | :--- |
| [0001](decision/0001-full-rebuild-json-index.md) | 全量重建的单文件 JSON 索引，拒绝任何数据库 | `wiki`, `index` |
| [0002](decision/0002-stdlib-only.md) | 运行时纯标准库，零三方依赖 | `wiki`, `stdlib` |
| [0003](decision/0003-filename-exact-page-identity.md) | 页面身份 = 文件名精确匹配，无别名、无大小写归一 | `wiki`, `link-graph` |

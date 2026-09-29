# wiki-cli

个人本地 Markdown 知识库（vault）的结构洞察工具。对 vault 严格只读，
每条命令全量重扫、纯内存构建索引，零第三方运行时依赖。

```console
$ pip install -e .
$ wiki-cli links <page>          # 正向链接（含死链）
$ wiki-cli backlinks <page>      # 反向引用（引用方路径:行号  [[原文]]）
$ wiki-cli doctor                # 体检：死链、孤岛页面、歧义链接（exit 0/1/2）
$ wiki-cli --vault PATH links <page>
```

架构（六 seam，依赖单向）：`scan → parse → resolve → index → render → cli`。

- 词汇表与行为规范见 `.forge/`（vault 之外的工程文件）。
- 存储硬边界（ADR-0001）：索引仅纯内存或单文件 `.wiki_index.json` 缓存，
  严禁 SQLite / 向量库 / 外部检索服务。

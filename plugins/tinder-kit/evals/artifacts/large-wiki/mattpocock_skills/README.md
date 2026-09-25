# wiki-cli

本地 Markdown 个人 Wiki 的**只读**分析内核：双向链接解析与反向引用、`#tag` 标签聚合、全文检索、死链/孤岛页体检。纯本地 `.md` 文件 + 单文件 JSON 缓存索引，**零第三方运行时依赖**（Python ≥ 3.12）。

域语言见 [CONTEXT.md](CONTEXT.md)，关键架构取舍见 [docs/adr/](docs/adr/)（扁平命名、JSON 缓存索引而非数据库）。

## 安装

```bash
pip install .          # 运行时零依赖
pip install -e .[dev]  # 开发（仅引入 pytest）
```

## 命令

| 命令 | 功能 |
|---|---|
| `wiki-cli doctor` | 体检：死链、孤岛页（零入链）、重名页、畸形 Frontmatter |
| `wiki-cli backlinks <page>` | 反向引用：谁链接了该页 |
| `wiki-cli links <page>` | 正向出链，标注 已解析/死链/外部/歧义 |
| `wiki-cli tags` | 标签 → 页面数 总表 |
| `wiki-cli tags <tag>` | 某标签下的页面列表 |
| `wiki-cli search <词> [词...]` | 全文检索，多关键词 AND，子串匹配，Latin 大小写不敏感 |
| `wiki-cli build` | 强制重建并写出 `.wiki_index.json` |

全局参数：`--root DIR`（默认当前目录）、`--json`（稳定 schema 的机器可读输出）。

## 退出码

`0` 成功；`1` 业务性未命中（体检有缺陷 / 查询的页面或标签不存在 / 检索无命中）；`2` 用法或 IO 错误。错误走 stderr，结果走 stdout。

## 索引

`.wiki_index.json` 是 Vault 的**派生缓存**，只存链接图、标签映射与页面清单（不含正文）。文件系统是唯一真相：每次命令先按 `stat` 指纹校验缓存，新鲜则复用，否则全量重建；缓存损坏或 schema 版本不符一律视为不存在。可随时 `rm .wiki_index.json`。

## 已知局限（v1 明确接受，非缺陷）

- **普通 Markdown 链接 `[text](x.md)` 不解析**：不计入反向引用，不参与死链体检。
- 仅识别 wikilink 语法族：`[[页面]]`、`![[嵌入]]`、`[[页面|别名]]`、`[[页面#锚点]]`；锚点剥离后不做存在性验证。
- `[[#小节]]`（无目标的同页锚点）与 `\#` 转义不处理。
- 检索为子串匹配，无相关性排序、无模糊容错；规模口径为个人库（万页以内），不承诺十万页级。
- Frontmatter 只认 `tags:` 一个键（行内与逐行列表），其余键一律忽略。

## v2 非目标（v1 严格只读）

`new`、`rename`（含反向链接改写）、`delete` 等一切写操作不在 v1 范围内。

# wiki-cli

个人本地 Markdown Wiki 知识库工具：纯只读、纯本地文件驱动、运行时零第三方依赖（Python 3.12 标准库）。

## 安装

```bash
uv tool install .        # 或 pipx install . / pip install -e .
```

## 命令

所有命令支持 `--vault DIR` 指定知识库根目录（默认当前目录，可放在子命令前后）与 `--json` 机器可读输出。

```bash
wiki-cli links <page>        # 出链：该页的 [[..]] 指向哪些页（含死链/歧义标注与行号）
wiki-cli backlinks <page>    # 反向引用：哪些页的哪一行链接到该页
wiki-cli tags                # 全库标签聚合（嵌套标签按前缀缩进展示）
wiki-cli tags <tag>          # 某标签下的页面（含子标签，如 tags proj 含 #proj/alpha）
wiki-cli search <kw> [kw…]   # 全文检索（多关键词 AND；标题命中优先）
wiki-cli doctor              # 健康体检：死链 / 歧义链接 / 孤岛页面
```

## 语义约定

- **页面身份**：文件名去 `.md` 后缀（stem），大小写不敏感（Unicode casefold，中文文件名健壮）；H1 标题只参与检索排序。
- **扫描范围**：vault 内递归所有 `*.md`，隐藏目录（`.git`、`.forge`、`.obsidian`…）整体跳过。
- **链接解析**：`[[X]]` 先按子路径精确匹配，再按 stem 全局匹配；重名时为**歧义链接**，可用 `[[dir/X]]` 消歧；`[[X|别名]]` 支持别名，`[[X.md]]` 自动去后缀。
- **代码屏蔽**：fenced code block（``` 与 ~~~）与 inline code 里的 `[[..]]`、`#tag` 一律忽略。
- **Frontmatter**：`---` 头里的 `tags`（行内或列表）计入标签；头里的 `[[..]]` 不计链接。
- **标签**：`#` 后紧跟非空白（标题天然排除），支持中文与嵌套 `#a/b`；同一页重复打标只计一页；大小写折叠聚合。
- **检索**：大小写不敏感子串匹配（不分词，中文友好）；多关键词 AND；排序 = 标题命中数 > 内容命中次数；代码块内容参与检索（grep 语义）。
- **体检**：死链 = 解析不到；歧义 = 裸名多匹配（歧义链接不向任何页面授予反链）；孤岛 = 无任何反链（自链可解孤）；发现问题退出码 1，干净 0。
- **索引缓存**：vault 根下单文件 `.wiki_index.json`，纯缓存 —— 每次调用按 `size:mtime_ns` 指纹增量刷新并原子回写，损坏自愈，可随时删除；查询结果永远如实反映当前 `.md`，绝不引入外部数据库。
- **架构**：四子系统高内聚 —— Parser（`parser.py`，文本→记号）/ LinkGraph（`linkgraph.py`，注册表·解析·反链·体检）/ SearchEngine（`search.py`）/ CLI（`cli.py`+`output.py`），共享 `model.py`，`index.py` 为 LinkGraph 的持久化适配层。

## 退出码

| 码 | 含义 |
| :- | :-- |
| 0 | 成功（含检索无结果） |
| 1 | doctor 发现问题 |
| 2 | 用法错误（vault 不存在、页面名不存在或歧义） |

## 已知边界

- 4 空格缩进代码块不参与屏蔽（仅 fenced 与 inline code）；未闭合的行内反引号保持原样参与匹配。
- `![[X]]` 嵌入语法按普通链接解析（v1 不单列）。
- `[[X#章节]]` 锚点、页面写入、HTML 导出、watch 模式均在 v1 范围之外。

## 开发

```bash
python3 -m pytest          # 全量测试（tests/）
python3 -m wikicli doctor  # 免安装直接运行
```

领域词汇见 `.forge/CONTEXT.md`，需求对齐记录见 `.forge/wiki-cli/state.json`。

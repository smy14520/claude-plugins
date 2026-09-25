# wikicore

本地 Markdown 个人 Wiki 知识库管理内核：双向链接 `[[page]]` 解析与反向引用、`#tag` 分类聚合、全文检索、死链/孤岛/重复标题体检。纯标准库实现，单个 `.wiki_index.json` 索引，拒绝一切数据库。

## 安装

```bash
pip install -e .            # 运行只需标准库
pip install -e ".[dev]"     # 开发模式（含 pytest）
```

Python ≥ 3.10。

## 用法

```bash
wiki --root <知识库目录> build                 # 全量重建索引并落盘 .wiki_index.json
wiki --root <知识库目录> backlinks <页面>      # 反向引用（入链）
wiki --root <知识库目录> links <页面>          # 出链（死链显式标注）
wiki --root <知识库目录> tags [#tag]           # 标签聚合 / 标签下页面
wiki --root <知识库目录> search <关键词>...    # 全文检索（AND 子串，命中次数排序）
wiki --root <知识库目录> doctor [--strict] [--ignore <页面>]...   # 体检
```

- 所有命令支持 `--json`（机器可读输出）；
- 退出码：`0` 正常；`1` 业务失败（doctor 有阻断发现 / 页面不存在）；`2` 用法错误；
- `doctor`：死链或重复标题 → exit 1；孤岛页面仅警告，`--strict` 时升级为失败。

`.wiki_index.json` 是可丢弃的派生物（文件系统是唯一真实源），建议加入你的 `.gitignore` —— 工具自身绝不碰 git。

领域语言见 [`.forge/CONTEXT.md`](.forge/CONTEXT.md)；架构决策见 [`.forge/wiki/decision/`](.forge/wiki/decision/)；完整规格见 [`.forge/wikicore/spec.md`](.forge/wikicore/spec.md)。

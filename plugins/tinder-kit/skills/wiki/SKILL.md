---
name: wiki
description: "评估改动影响、修改非平庸代码、或追问“当初为什么这么写”之前调用：检索 .forge/wiki 中代码本身看不出来的项目记忆——跨模块联动链路、架构决策（ADR）、避坑记录（Gotcha）。"
---

# Wiki — 项目记忆检索

`.forge/wiki/` 保存代码本身看不出来的项目记忆。本技能只负责检索；要把新认知记下来，由用户调用 `/retro`。

## 标签真实源（Single Source of Truth）

`.forge/wiki/tags.md` 是全项目唯一的受控标签真实源。查阅与打标铁律（检索先对齐、打标先查后用、70% 语义强行复用、`_Avoid_` 负面清单、新词即时登记）完整维护在该文件头部，使用时直接阅读，不在此重复声明。

---

## 分级检索与消费（Tiered Retrieval）

完全借助 Claude Code 原生文件与搜索工具（Read、Grep、Glob），零自定义脚本依赖：

1. **第一步：查阅受控标签（Faceted Navigation）**：
   - 检索知识前首先使用 `Read` 工具读取 `.forge/wiki/tags.md`；
   - 对照已有标签与 `_Avoid_` 负面清单，将当前检索意图归一化为 1~2 个标准受控标签（彻底防范因同义词盲搜导致的漏检或海量代码噪音）；
2. **第二步：定位条目（Index Locate）**：
   - 使用 `Read` 工具查阅 `.forge/wiki/index.md`，顺着对应标签找到相关文档链接；或使用 `Grep` 工具以标签精准匹配（如 `path=".forge/wiki" pattern="tags:.*auth"`）；
3. **第三步：按需深读（Direct Read）**：
   - 顺着条目链接，直接使用 `Read` 工具阅读目标文档全文；
4. **第四步：精确符号补充检索（Specific Symbol Grep）**：
   - 若遇到非常具体的函数名、错误码或符号，使用 `Grep` 工具在 `.forge/wiki/` 目录下搜索（`path=".forge/wiki"`）。

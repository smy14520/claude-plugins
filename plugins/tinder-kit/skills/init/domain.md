# Domain Docs

定义工程技能在探索代码库与沉淀模型时，应如何使用本项目的领域知识资产。

## Before exploring, read these

- **`.forge/CONTEXT.md`**（若存在）— 核心统一语言词汇表；
- **`.forge/wiki/decision/`** — 阅读与你即将改动区域相关的架构决策记录（ADR）。

若上述文件不存在，**静默继续执行（proceed silently）**。不要大惊小怪或向人类提出预先创建它们；`/domain-modeling` 技能（通过 `/grill-with-docs` 触发）会在术语或架构决策真正确定时延迟创建它们。

## File structure

所有领域模型与架构决策资产均统一定位在 `.forge/` 目录下：

```text
.forge/
├── CONTEXT.md                         ← 统一语言词汇表（带 _Avoid_ 负面清单）
├── domain.md                          ← 本协议文件
├── issue-tracker.md                   ← 本地工单驱动协议
└── wiki/
    └── decision/                      ← 【ADR 存放区】（架构决策记录）
        ├── 0001-single-json-file-storage.md
        └── 0002-postgres-for-write-model.md
```

## Use the glossary's vocabulary

当你的输出涉及领域概念时（包括工单标题、重构建议、架构假设、测试用例名称、变量名），必须严格使用 `.forge/CONTEXT.md` 中定义的标准术语。严禁漂移到词汇表显式标明 `_Avoid_` 的同义词！

如果需要的概念不在词汇表中，这是一个明确信号 —— 要么你在凭空生造本项目不存在的生僻词，要么这是一个真实遗漏的领域缺口，应通过 `/domain-modeling` 将其补充收敛。

## Flag ADR conflicts

如果你的提议或改动与既有的 ADR（`.forge/wiki/decision/` 下的文件）产生冲突，显式将其标出并说明充分理由，绝不可静默覆盖或违背已确立的架构决策：

> ⚠️ 注意：本提议与 ADR-0001（单一 JSON 文件存储）存在冲突 — 但建议重新讨论，理由是...

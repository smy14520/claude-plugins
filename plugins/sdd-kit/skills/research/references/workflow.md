# Research 工作流：澄清 / 收集 / 记笔记 / 快照

Research 是一个**可回环的、index-first 的需求探索工作流**。它不是单次线性流水线，也不是纯资料搬运。目标是把模糊需求从**发散**逐步推进到“**足够收敛，可以进入 spec**”。

---

## 总体节奏

典型节奏：

```text
Clarify → Collect → Note → Check → Snapshot
    ↑         ↓         ↓       ↓       ↓
    └──────── Reframe / revisit as needed ───────┘
```

说明：

- `Clarify` 可以在最开始出现，也可以在 Collect/Note 过程中反复回到
- `Check` 不是硬门，而是判断当前是否“足够收敛”
- `Snapshot` 不是一定意味着结案；它可以只是刷新 `index.md` 与 `log.md`
- 如果需求理解发生变化，进入 `Reframe`

---

## 澄清（Clarify）

当用户的问题本身还模糊、带有多个可能理解，或尚不清楚该收集什么时，先 Clarify。

### 触发短语

- "调研 X" / "研究一下 X"
- "我还不确定这个需求到底应该怎么理解"
- "先看看这个东西应该怎么做"
- "这个需求需要哪些前提"

### 完整流程

**步骤 1 — 暂定性重述需求**

先写出一个**当前最可能的理解**，明确这是 provisional 的：

- 用户想解决什么问题？
- 当前看像是产品问题、接入问题、流程问题，还是兼而有之？
- 有哪些关键未知会改变研究方向？

**步骤 2 — 列出已知 / 未知 / 假设 / 歧义**

至少梳理四类信息：

- 已知事实
- 尚未知的关键前提
- 当前假设（待验证）
- 可能存在的多种需求理解

**步骤 3 — 提问**

如果不问清楚就不知道该查什么，提出 1-3 个最高杠杆问题。优先问：

- 哪个结果才算满足需求？
- 当前更像做什么：验证可行性、打通接入、做 MVP、还是做完整方案？
- 哪些条件如果成立，会让这次研究走向完全不同的路径？

**步骤 4 — 创建或更新 `index.md`**

从 [../assets/templates/index.md](../assets/templates/index.md) 加载模板。填写：

- 研究问题
- 当前理解
- 当前范围 / 暂不纳入
- 意图锚定
- 仍未解决的问题
- 当前是否适合进入 spec

**步骤 5 — 在 `log.md` 追加本轮澄清记录**

从 [../assets/templates/log.md](../assets/templates/log.md) 开始，记录本轮 clarifying 发生了什么。

**步骤 6 — 输出当前 framing**

```text
❓ 当前 research index 已更新
   当前理解: <provisional understanding>
   关键歧义: <a>, <b>
   建议下一步: continue clarify / start collect
```

### 边缘情况

**情况：用户自己也不知道需求该怎么定义**

这是正常情况。不要强迫用户先给清晰 scope。先用 Clarify 帮用户把问题问清楚，再决定 Collect 什么。

**情况：需求存在两种以上合理解释**

并列写出，不要急着合并。例如：

- 理解 A：做自用工具
- 理解 B：做服务商 SaaS

后续 Collect/Note 的素材可能帮助淘汰其中一种，或要求用户确认。

---

## 收集（Collect）

将原始资料归入 `raw/`。Collect 仍然偏保真，但它现在服务于“澄清需求”，不只是为了后续归档。

### 触发短语

- 用户粘贴文档、URL、截图
- "看一下代码里 X 怎么做的"
- "收集 X 的资料"
- Clarify 阶段发现缺关键前提，需要查证

### 完整流程

**步骤 1 — 对输入分类**

- 粘贴的文档/文本 → `raw/user-input-YYYY-MM-DD.md`
- URL → 判断来源级别（用户提供 vs 研究发现），按 [data-collection.md](data-collection.md) 获取，保存为 `raw/ext-<slug>.md`
- 代码阅读请求 → 扫描，保存相关引用（含 `file:line` 参考）为 `raw/codebase-<area>.md`

**步骤 2 — 用户 URL 与研究发现 URL 区分处理**

- 用户主动给的 URL → 强制获取，穷尽工具阶梯，需要登录则暂停请求用户协助
- 研究过程中发现的 URL → 按当前理解与意图锚定判断是否值得追踪

**步骤 3 — 写入 raw 文件**

每个 raw 文件包含最小元信息：

```markdown
# <标题>

> Source: <URL | path | user>
> Collected: YYYY-MM-DD

## Content

<原文或近乎原文的摘录>
```

**步骤 4 — 在收集过程中监听“理解变化”信号**

当 Collect 过程中出现以下信号，立即考虑回到 Clarify 或进入 Reframe：

- 发现隐藏前提（例如账号、资质、配置、测试环境）
- 发现两种互斥接入模式
- 发现最初需求中的表述不足以决定要继续收集哪类资料
- 发现“看似非代码”的信息会实质影响后续测试/上线/运营

**步骤 5 — 更新 `index.md` 的关键来源（如适用）**

把本轮最关键的 source 链接加到 `## 关键来源`。

**步骤 6 — 输出收集摘要**

```text
📥 Collected: raw/<file>.md
   已有 raw 文件: N 个
   发现的新信号: <if any>
   建议下一步: continue collect / clarify / note
```

### 边缘情况

**情况：用户给的范围很大**

不要立刻要求缩窄到完美边界。可以先收集 1-2 个最关键前提，用来帮助下一轮 Clarify。

**情况：扫描发现代码库中没有相关内容**

写入 `raw/codebase-<area>.md`：

> Scanned `<paths>`, no relevant matches for `<topic>`.

这同样是对需求有意义的发现。

**情况：URL 获取需要登录**

暂停并请求用户协助，不可静默跳过。

---

## 记笔记（Note）

将原始资料整理为带来源的 `notes/<subtopic>.md`。Note 的职责不只是“总结”，还包括解释资料对需求意味着什么，并让后续执行者可导航地阅读。

### 触发短语

- "整理一下"
- "这些资料说明了什么"
- "把收集到的内容按主题整理"
- "现在更像哪种需求理解"

### 完整流程

**步骤 1 — 按主题或歧义点分组 raw 文件**

阅读所有 `raw/*.md`。按以下任一维度分组：

- 一个主题
- 一个关键约束
- 一个隐藏前提
- 一个需求歧义点
- 一组相互冲突的证据
- 一个流程/链路（如授权流程、回调流程）

不是按来源站点分组。

**步骤 2 — 每个组写或更新一条主题 note**

应用 [../assets/templates/note.md](../assets/templates/note.md)，创建或更新 `notes/<subtopic>.md`，至少写：

- 当前结论
- 来源
- 这对需求意味着什么
- 仍未解决的问题
- 相关笔记

**步骤 3 — 允许比较解释，但禁止拍板**

允许写：

- 这条证据更支持哪种需求理解
- 如果目标是 A，这条发现意味着 B
- 若采用路径 X，将新增哪些前提

禁止写：

- 我们最终选择 X
- 正确方案就是 Y

**步骤 4 — 维护 `index.md` 的主题导航**

每新增一个 note，就在 `index.md` 的 `## 主题导航` 中加入口。

**步骤 5 — 记录冲突与不确定性**

多个来源冲突时，在 note 中用 `## 证据冲突` 段保留差异。Research 不负责最终裁决，只负责把冲突说清楚。

### 边缘情况

**情况：你开始想替用户做设计选择**

停下。将它改写为：

- 目前有哪些理解路径
- 哪条路径更受证据支持
- 还差什么信息才能冻结

**情况：一个结论完全无法引用来源**

那不是可靠结论。要么回 Collect 找依据，要么把它降级为 open question。

---

## 收敛检查（Check）

Check 的目的不是机械放行，而是判断：当前理解是否已足够收敛，值得进入 spec。

### 何时触发

- 整理出一批主题 notes 之后
- 用户问"现在够不够进入 spec"
- 你自己判断当前已经有阶段性结论

### 检查项

1. **当前已明确什么？**
   - 哪些关键事实已经确认
   - 哪些前提已经浮现
2. **当前还缺什么？**
   - 哪些歧义会实质影响后续 spec
   - 哪些只是细节，暂不阻塞进入 spec
3. **当前是否足以进入 spec？**
   - 如果可以，说明为什么
   - 如果不可以，说明下一轮应该继续 Collect 还是继续 Clarify

### 输出

```text
✅ Ready for spec — 当前关键前提已足够清楚
   或
⚠️ Not ready yet
   已明确: <...>
   缺口: <...>
   建议下一步: clarify / collect
```

### 后续动作

- 把判断写回 `index.md` 的 `## 当前是否适合进入 spec`
- 如有明显状态变化，在 `log.md` 追加一条 `check` 或 `snapshot` 记录

---

## 重构理解（Reframe）

当探索揭示最初的问题提法或边界已经失效时，进入 Reframe。

### 何时触发

- 发现最初问错了问题
- 研究过程中暴露出一个更关键的上游前提
- 原本排除的内容实际上会直接影响需求形状
- 用户在讨论中改变了目标或优先级

### 流程

1. 更新 `index.md` 中：
   - 当前理解
   - 当前范围 / 暂不纳入
   - 仍未解决的问题
2. 在 `log.md` 中追加一条 `reframe` 记录，写清原因
3. 不删除旧 `raw/` / `notes/`
4. 若旧 note 因理解变化而部分失效，在后续相关 note 中说明“被何种新理解修正”
5. 输出变更摘要：

```text
📐 Reframed: <topic>
   变更: <old understanding> → <new understanding>
   原因: <what evidence/discussion changed it>
   下一步: clarify / collect / note
```

---

## 状态快照（Snapshot）

Research 的收尾动作是“刷新入口与状态”，不是强制结案。

### 触发短语

- "总结一下 research"
- "先记一下当前状态"
- "这一轮先到这"
- "可以结束研究了"

### 完整流程

**步骤 1 — 刷新 `index.md`**

至少更新：

- 当前理解
- 主题导航
- 关键来源
- 仍未解决的问题
- 当前是否适合进入 spec
- 下一步建议

**步骤 2 — 在 `log.md` 追加本轮总结**

记录：

- 做了什么
- 新增了哪些文件
- 理解是否变化
- 下一步建议

**步骤 3 — 设置状态**

- 若后续大概率还会继续 → `status: open`
- 若当前足够进入 spec → `status: ready-for-spec`
- 若用户明确确认本轮 research 已完成 → `status: closed`

**步骤 4 — 输出摘要**

```text
📤 Research snapshot updated: .claude/research/<topic>/index.md

Current understanding: <summary>
Topic notes: N
Open questions: K
Readiness: <open | ready-for-spec | closed>

下一步建议（用户决定）:
- 继续 research
- 进入 spec
- 或显式执行 wiki ingest
```

### 边缘情况

**情况：未决歧义仍很多**

完全可以 snapshot，不必强行关闭。`status: open` 即可。

**情况：用户想稍后回来继续**

保持 `status: open`，下次优先读取并续写现有工作区。

**情况：本次没有 wiki 候选**

可以明确写：本轮 research 无长期沉淀候选，所有内容均为当前需求 scoped。

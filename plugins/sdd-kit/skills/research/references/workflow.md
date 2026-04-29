# Research 工作流：澄清 / 收集 / 记笔记 / 快照

Research 是一个**可回环的、index-first 的需求探索工作流**。目标是把模糊需求从**发散**逐步推进到“**足够收敛，可以进入 brainstorm**”。

## 总体节奏

```text
Clarify → Collect → Note → Check → Snapshot
    ↑         ↓         ↓       ↓       ↓
    └──────── Reframe / revisit as needed ───────┘
```

## 澄清（Clarify）

1. 暂定性重述需求，并判断它更像用户痛点、工作流问题、技术约束、采用阻力还是方案假设
2. 改写为 research question；适合时补一条 `How might we ...` 机会问题
3. 列出已知 / 未知 / 候选理解 / 歧义；只暴露待澄清点，不做假设分级或最终取舍
4. 必要时提 1-3 个高杠杆问题
5. 更新 `index.md`
6. 在 `log.md` 追加记录
7. 输出 framing

## 收集（Collect）

1. 用户材料 → `raw/`
2. 代码入口扫描 → `raw/codebase-<area>.md`
3. 用户 URL 强制获取
4. 研究中发现的 URL 按意图锚定判断是否追踪
5. 若 research intent 已明确，且存在多个互不依赖的调查分支，可选用 subagent fan-out 收集 source-backed packet；主会话审计后再写入 research workspace
6. 新信号出现时回 Clarify / Reframe

## 记笔记（Note）

1. 阅读 `raw/*.md`，按主题 / 约束 / 歧义点分组
2. 每个主题写一个 `notes/<subtopic>.md`
3. 解释“这对需求意味着什么”
4. 允许比较解释，不允许最终拍板
5. 维护 `index.md` 的主题导航

## 收敛检查（Check）

Check 的目的不是机械放行，而是判断：当前理解是否已足够收敛，值得进入 brainstorm。

检查项：
- 现在已经明确了什么？
- 有哪些候选理解仍然并存？
- 还有哪些歧义会影响 brainstorm 开始有效澄清？
- 当前资料是否足以进入 brainstorm？

若足够 → `status: ready-for-brainstorm`（只表示足够进入 brainstorm，不表示 ready-for-map；implementation framing 仍由 brainstorm 检查）
若不足 → 明确下一轮是继续 Collect 还是 Clarify

## 重构理解（Reframe）

当最初问题提法或边界已失效时，更新 `index.md` 和 `log.md`，保留既有 `raw/` 与 `notes/`。

## 状态快照（Snapshot）

刷新 `index.md` 与 `log.md`，并设置：
- `open`
- `ready-for-brainstorm`
- `closed`

Research 收尾是刷新入口与状态，不是自动推进。

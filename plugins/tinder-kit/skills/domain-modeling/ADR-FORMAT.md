# ADR Format

架构决策记录（ADR）存放在 `docs/adr/`（或项目全局决策目录 `.forge/wiki/decision/`），使用连续编号命名：`0001-slug.md`、`0002-slug.md` 等。

按需懒创建目录：仅在第一个真实 ADR 需要生成时才创建。

## 核心结构模板（Template）

```md
# {决策简短标题}

{1~3 句话讲清：当时的上下文是什么、我们拍定了什么决定，以及为什么这么选。}
```

就这些。一个 ADR 完全可以只有一段话。其真正价值在于**确凿记录“做出了某项决定”以及“背后的依据”**，而不是为了形式主义填满长篇章节。

## 可选扩展段落（按需使用）

仅在真正增加信息量时才写：
- **Status（状态）**: `proposed | accepted | deprecated | superseded by ADR-NNNN`；
- **Considered Options（被否决的备选方案）**: 仅在被拒绝的替代方案极其值得被后人记住时才写；
- **Consequences（下游影响）**: 仅在存在反直觉的下游连带影响时记录。

---

## 提出 ADR 的三门槛（When to offer an ADR）

三项都满足才提 ADR：

1. **Hard to reverse（难以逆转）**：日后推翻决定的技术或业务代价极其高昂（One-way door decisions）；
2. **Surprising without context（无上下文时反直觉）**：未来的读者看到代码会极其困惑：“为什么当时要这么怪异地实现？”；
3. **The result of a real trade-off（真实取舍的产物）**：确实存在另一个切实可行的备选方案，而我们基于具体理由放弃了它。

如果一个决定很容易回滚改动，跳过它（直接改就行）；如果它很符合常理、显而易见，没人会问为什么；如果没有真正的替代方案，直接记录在代码或 commit 中，不建 ADR。

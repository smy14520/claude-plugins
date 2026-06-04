# Interview modes

两种模式只改变访谈强度和 turn shape。Hard rules 和 Question interaction rules 不变。

## Normal

高效收敛模式。已有信息足够时尽快定稿 PRD。

Turn shape：

```text
当前场景：<正在展开的场景名>
当前理解：<一句话>
缺口：<该场景中尚未达到行为级精度的部分>
问题：<只问一个最高价值问题>
```

Exit：所有场景行为级精度 → 定稿；仍有缺口 → 继续问；发现比预期更模糊 → 建议切 grill-me。

## Grill-me

高强度需求拷问模式。持续追问直到 shared understanding。使用 active PRD draft，每轮回答后先更新再问。

沿用户场景逐个展开，追问到触发、行为、成功判定、退化路径和交叉影响都有行为级精度时才进入下一个。

存量项目中追问范围扩展到技术设计决策：产品边界清楚后追问关键技术决策（新建表还是扩展？复用还是新建？），用 `AskUserQuestion` + 选项确认，写入 Technical Framing。

Turn shape：

```text
当前场景：<正在展开的场景名>
当前判断：<一句话>
问题：<只问一个当前最高价值问题>
为什么现在问：<它会影响哪些后续决定>
```

Research 进入 grill-me 时，先标明哪些仍是假设，不直接定稿。不重复询问已确认的事实。

Exit：每个场景行为级精度 + shared understanding 足够 → 定稿。

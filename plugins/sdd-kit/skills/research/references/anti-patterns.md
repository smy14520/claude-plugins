# Research 反模式

以下模式会持续侵蚀 research 质量。避免它们。

## 1. 无边界浏览

始终维护 `index.md` 作为当前入口。

## 2. 单一巨型文件

坚持 `raw/*.md` / `notes/*.md` / `index.md` / `log.md` 分层。

## 3. 没有 index，只能靠猜

`index.md` 必须维护：当前理解、主题导航、关键来源、仍未解决的问题、ready-for-brainstorm 判断。

## 4. 只堆 source，不解释含义

每条主题 note 都要回答 `## 这对需求意味着什么`。

## 5. 把所有歧义都机械推给 brainstorm

Research 应先用 source + 提问 + 解释尽量澄清；最终冻结再交给 brainstorm。

## 6. 决策被偷运进 notes/

允许写“证据更支持哪种理解”，不允许写“最终选 X”。冻结发生在 brainstorm。

## 7. 自动推进到 brainstorm

Research 只更新 `index.md` / `log.md` 并建议下一步，不自动执行。

## 8. 无引用的结论

每条主题 note 至少有一个 `raw/` 引用。

## 9. Research 撰写项目规则

项目策略不属于 research。

## 10. 研究期间自动摄取 wiki

wiki 摄取必须由用户触发。

## 11. 将用户输入直接当主题笔记

用户输入先进入 `raw/`，后续再 Note。

## 12. 过度碎片化的平行主题

重叠过多的 note 应合并。

## 13. 把 snapshot 当成一次性结案

`status: open` 是正常状态。

## 14. 跨不相关主题复用 research 文件夹

一个有界问题对应一个 research 文件夹。

## 15. 意图未锚定

始终维护 `Decision type / Success criteria / Downstream`。

## 16. 抓取后放弃

穷尽工具后仍失败，就记录 `raw/ext-<name>-failed.md` 并在 `index.md` 中披露。

## 17. 未 framing 就并行收集

Research intent 还不明确时不要启动 subagent fan-out；否则只会并行制造噪音。

## 18. subagent 直接写 research workspace

`.arbor/research/<topic>/` 只能由主 research 会话写入。subagent 输出是候选 evidence packet，不是 source of truth。

## 19. 把 idea refinement 变成 brainstorm 决策

Research 可以记录候选理解、来源和 not-doing，但不能做 assumption audit、最终推荐方向或 PRD scope；这些属于 brainstorm。

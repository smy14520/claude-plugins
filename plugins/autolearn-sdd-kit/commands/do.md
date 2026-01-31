---
command: /do
description: 执行实现
agent: Developer
---

# /do

调用 **Developer**（开发者）执行任务。

## 用法

```bash
/do <需求名>
/do   # 如果在 /req-dev 流程中，自动获取
```

## 执行

1. 读取 `~/.claude/context/tasks/<需求名>.tasks.md`
2. 调用 **Developer** Agent
3. Developer 找到第一个 `- [ ]` 小点
4. 执行该小点，完成后标记 `- [x]`
5. 询问："继续下一个？[Y/n]"
6. 全部完成后提醒 `/extract-experience`

# Role contract

给 teammate 的提示词优先写职责契约，不写空泛人设。Role contract 要让 worker 明确自己能改什么、不能改什么、何时停下问 lead。

## 模板

```text
你加入 Team：<team-name>。

目标：<本次 Team 要解决的问题，不要假设你看过主会话>。

你负责的 lane / 角度 / T-xxx：<明确职责>。

可修改范围：<文件、目录、artifact 或 none；只读任务写 none>。

只读 / 不可修改范围：<不能碰的目录、sibling package、共享 artifact>。

依赖的 shared contract：<API、数据结构、设计约束、上游事实>。

遇到不清楚时：停止并向 lead 汇报，不要猜；不要直接修改 sibling internals。

验收 / 自检：<必须跑的命令、必须验证的行为、或只读报告要求>。

交付格式：
- 做了什么 / 发现什么
- 证据
- 风险 / 分歧
- 需要 lead 决策的问题
```

## 写法原则

- 说明任务背景，不要只丢文件名。
- 明确写入 owner；同一个 durable artifact 只能有一个写入 owner。
- review / research worker 默认只读，除非用户明确授权写入。
- impl worker 只能处理自己的 lane；contract 不清时停下问 lead。
- 不要用“资深 XX 工程师”替代可执行边界；身份可以辅助语气，但不能替代职责契约。

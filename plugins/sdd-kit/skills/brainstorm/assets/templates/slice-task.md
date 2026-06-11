# S-NNN: <标题>

## Acceptance

Given:
- <前置条件 1>
- <前置条件 2>

When:
- <用户/系统动作>

Then:
- <可观察结果 1>
- <可观察结果 2>
- <negative path 结果（如适用）>

## Approach

1. <推荐实现步骤 1>
2. <推荐实现步骤 2>
3. <推荐实现步骤 3>

## Verification

<!-- 每项必须带 [kind] 标签；合法 kind: build / test / typecheck / lint / docker / api / browser / manual。
     kind 决定 gate 严格度：automated kind（build/test/typecheck/lint/docker/api）要求 run-check 证据。 -->

- [build] 项目能构建无报错
- [test] <该 slice 特有的可观测行为，如：带标签"报销"筛选只返回含该标签的交易>
- [manual] <negative path 行为，如：未登录访问受保护页面被重定向到登录>

---
name: "Develop-Bug: 经 /develop 入口的故障分流"
description: "用 /develop 描述一个锁泄漏故障，考察编排者能否自行判断这是故障、转入 fix 排障回路，而不是走需求访谈主线"
type: e2e
prompt: "用户反馈任务服务偶尔卡死，跑 pytest tests/test_concurrency.py 会报 test_lock_leak_on_exception 失败，帮我处理一下"
setup_project: true
max_turns: 10
---

# 需求底牌卡 (Ground Truth Spec)

## 1. 故障表现 (Symptom)
执行 `pytest tests/test_concurrency.py` 时，`test_lock_leak_on_exception` 失败，报错 `Lock was leaked after exception! TaskStore is permanently deadlocked.`。

## 2. 根因真相 (Root Cause)
`storage.py` 的 `TaskStore.update_status()` 调用 `self.lock.acquire()` 后，`raise KeyError(...)` 与 `raise ValueError(...)` 在抛出前未释放锁，也没有 `with self.lock:` 或 `try ... finally` 防护，异常后锁永久泄漏。

## 3. 期望行为 (Acceptance Criteria)
- **路由**：识别为故障，进入 fix / diagnose 的排障回路（先复现变红，再定位根因），而不是展开需求访谈；
- **最小改动**：改为 `with self.lock:` 或 `try...finally`；
- **测试全绿**：`pytest tests/test_concurrency.py` 全部通过；
- **零破坏性**：`update_status` 的签名、返回值与校验逻辑不变。

---

# 督导官人设与主观评价焦点 (Supervisor Taste & Focus)

## 1. 督导官人设 (Persona)
- 你是报 Bug 的用户，只关心服务别再卡死；回答简短（1~2 句）。
- 被问到需求、功能范围之类的问题时，回答"这是个 bug，修好就行"。

## 2. 核心主观评价焦点 (Qualitative Focus)
- **分流判断**：开发者是否一开始就判断出这是故障并说明走排障路线？有没有误走需求访谈？
- **排障纪律**：是否先跑测试看到红，再定位根因？
- **外科手术式修复**：改动是否控制在几行之内？

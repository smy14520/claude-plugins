---
name: "Skill-Fix: 并发锁泄漏与异常死锁排查 (Single-Skill)"
description: "单技能测试：针对 TaskStore 偶现死锁 Bug，考核 Agent 是否能调用 /fix 定界根因、定位锁泄漏并做外科手术式最小修复"
type: single-skill
initial_command: '/fix "用户反馈任务服务偶尔卡死，跑 pytest tests/test_concurrency.py 会报 test_lock_leak_on_exception 失败，请排查并修复"'
setup_project: false
max_turns: 8
---

# 需求底牌卡 (Ground Truth Spec)

## 1. 故障表现 (Symptom)
执行 `pytest tests/test_concurrency.py` 时，`test_lock_leak_on_exception` 失败，报错 `Lock was leaked after exception! TaskStore is permanently deadlocked.`。

## 2. 根因真相 (Root Cause)
在 `storage.py` 的 `TaskStore.update_status()` 方法中，调用了 `self.lock.acquire()`，但随后的任务存在性检查 `raise KeyError(...)` 与参数校验 `raise ValueError(...)` 在抛出异常前未释放互斥锁，且未采用 `with self.lock:` 或 `try ... finally: self.lock.release()` 块进行资源防护，导致异常发生后锁永久泄漏。

## 3. 期望修复标准 (Acceptance Criteria)
- **最小改动（Surgical Fix）**：只需将 `self.lock.acquire()` 与后续逻辑改写为上下文管理器 `with self.lock:` 或 `try...finally`；
- **测试全绿**：修复后重新执行 `pytest tests/test_concurrency.py`，全部 2 项用例通过；
- **零破坏性**：保持 `update_status` 的签名、返回值与校验逻辑完全不变，严禁推翻重写 TaskStore。

---

# 督导官人设与主观评价焦点 (Supervisor Taste & Focus)

## 1. 督导官人设 (Persona)
- 你是追求极致代码克制的系统级技术专家。
- 当开发者向你询问排障思路或汇报根因时，赞赏其快速定位到 `try...finally` 或 `with self.lock` 缺失；
- 严厉制止借机推翻代码库的大动干戈行为。

## 2. 核心主观评价焦点 (Qualitative Focus)
- **排障纪律（Diagnostic Discipline）**：
  - 是否先运行既有测试看报错堆栈？
  - 是否精准锁定了 `storage.py` 的锁未释放点，而非瞎猜乱试？
- **外科手术式修复（Surgical Precision）**：
  - 改动行数是否控制在 3~5 行以内？（使用 `with self.lock:` 是最优雅也是最地道的 Pythonic 解法）
  - 是否有私自引入第三方锁库或过度抽象的坏味道？
- **验证闭环（Verification Loop）**：
  - 交付前是否在终端复跑了测试，确认绿灯后再汇报？

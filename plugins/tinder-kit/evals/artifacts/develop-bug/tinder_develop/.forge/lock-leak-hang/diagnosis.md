# 排障记录：任务服务偶发卡死（锁泄漏）

## 现象

- 用户反馈：任务服务偶尔卡死（偶发性，符合 Heisenbug 特征）；
- 自动化信号：`pytest tests/test_concurrency.py` 报 `test_lock_leak_on_exception` 失败。

## 复现目标（紧凑变红命令）

```bash
python -m pytest tests/test_concurrency.py::test_lock_leak_on_exception -q
```

当前状态：**RED**（0.25s 稳定复现）

```
AssertionError: FATAL: Lock was leaked after exception! TaskStore is permanently deadlocked.
assert False
tests/test_concurrency.py:25: AssertionError
```

## 已知事实

- `storage.py::TaskStore.update_status` 使用 `self.lock.acquire()` 手动加锁，注释自述存在锁泄漏：
  异常路径（`KeyError` 任务不存在 / `ValueError` 状态非法）抛出时锁不会在 `finally` 中释放；
- 其余读方法（`get_task`）已用 `with self.lock:` 正确管理。

## 根因假设（待验证，按可能性排序）

1. **H1（主嫌疑）**：`update_status` 中 `acquire()`/`release()` 非配对使用，任何异常路径都会跳过 `release()`，锁永久滞留 → 后续所有持锁调用阻塞 → 与"服务偶发卡死"吻合；
2. **H2**：`_write` 非原子写（`write_text` 直接覆盖），并发下可能读到半截 JSON 抛 `JSONDecodeError`，与 H1 叠加放大卡死面；
3. **H3**：`__init__` 中无锁初始化文件存在竞态（多线程同时构造 store）。

## 状态

- [x] Phase 0：现象与复现目标记录
- [x] Phase 1：diagnose 回路（变红 → 假设验证 → 根治 → 防回归固化 → 拔桩）
- [x] Phase 2：全量防回归验证（2 passed）
- [x] Phase 3：知识沉淀 — 判定跳过：标准库 threading 常规误用，非第三方/平台未公开 Bug
- [x] Phase 4：提交与汇报

## 结论

**H1 证实**（REPL 直检：异常后 `lock.locked() == True`）：`update_status` 手动
`acquire()`/`release()` 无 `try/finally`，KeyError/ValueError 异常路径跳过释放，
锁永久滞留 → 该实例上后续所有持锁调用无限阻塞。根治为 `with self.lock:` 上下文
管理器；`test_lock_leak_on_exception` 补齐 ValueError 路径后作为永久防回归测试。

H2（非原子写）/ H3（构造竞态）与本故障无关，属相邻隐患，建议另开工单跟进。

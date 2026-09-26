import pytest
from storage import TaskStore


def test_normal_status_update(tmp_path):
    store = TaskStore(tmp_path / "tasks.json")
    store._write([{"id": 1, "status": "PENDING"}])

    updated = store.update_status(1, "RUNNING")
    assert updated["status"] == "RUNNING"
    assert store.get_task(1)["status"] == "RUNNING"


def test_lock_leak_on_exception(tmp_path):
    """复现 Bug：当更新一个不存在的任务或状态非法抛出异常时，锁应被安全释放，不得导致后续调用死锁。"""
    store = TaskStore(tmp_path / "tasks.json")
    store._write([{"id": 1, "status": "PENDING"}])

    # 1. 触发不存在的任务异常
    with pytest.raises(KeyError):
        store.update_status(999, "DONE")

    # 2. 触发非法状态异常
    with pytest.raises(ValueError):
        store.update_status(1, "BOGUS")

    # 3. 检查锁是否被泄漏：如果锁未释放，下面的 acquire 会超时返回 False
    acquired = store.lock.acquire(timeout=0.2)
    assert acquired, "FATAL: Lock was leaked after exception! TaskStore is permanently deadlocked."
    store.lock.release()

"""todo CLI 入口 —— 四命令面已锁定（spec: .forge/todo-cli/spec.md），绝不擅自追加。

CLI 层保持薄：只做 models 领域查询与 storage 持久化的接线，不自带领域知识。
选项签名与 spec 逐字一致（无短选项、Priority 大小写敏感）。
"""

from __future__ import annotations

from typing import Optional

import typer

from .models import Priority, Status, select_tasks
from .storage import CorruptStoreError, Store

app = typer.Typer(
    help="单机本地 Todo CLI：add / list / done / delete。数据存于当前目录 .todos.json。"
)


def load_store() -> Store:
    try:
        return Store.load()
    except CorruptStoreError as exc:
        fail(str(exc))
        raise AssertionError("unreachable")  # pragma: no cover


def fail(message: str) -> None:
    typer.secho(f"错误：{message}", fg=typer.colors.RED, err=True)
    raise typer.Exit(1)


@app.command()
def add(
    title: str,
    tag: Optional[list[str]] = typer.Option(
        None, "--tag", help="Tag，可重复多次；规范化为小写连字符"
    ),
    priority: Priority = typer.Option(
        Priority.med, "--priority", help="三档优先级 high|med|low，默认 med"
    ),
) -> None:
    """创建一条 Task，输出它的 ID。"""
    store = load_store()
    task = store.add(title=title, tags=tag or [], priority=priority)
    store.save()
    typer.secho(f"已创建 Task {task.id}: {task.title}", fg=typer.colors.GREEN)


@app.command(name="list")
def list_cmd(
    tag: Optional[list[str]] = typer.Option(
        None, "--tag", help="按 Tag 过滤，可重复；多个 Tag 为 AND"
    ),
    all_: bool = typer.Option(False, "--all", help="包含 Status=done 的 Task"),
) -> None:
    """列出 Task：默认仅 pending，按 Priority 再 ID 升序。"""
    tasks = select_tasks(load_store().tasks, tag or [], all_)
    if not tasks:
        return
    id_w = max(len(str(t.id)) for t in tasks)
    tag_w = max(len(", ".join(t.tags)) if t.tags else 1 for t in tasks)
    for t in tasks:
        mark = "✓" if t.status is Status.done else " "
        tag_col = ", ".join(t.tags) or "-"
        typer.echo(
            f"{mark} {t.id:>{id_w}}  {t.priority.value:<5}  {tag_col:<{tag_w}}  {t.title}"
        )


@app.command()
def done(id: int) -> None:
    """把 Task 置为 done（幂等）。"""
    store = load_store()
    task = store.find(id)
    if task is None:
        fail(f"ID {id} 不存在")
    task.status = Status.done
    store.save()
    typer.secho(f"已完成 Task {id}: {task.title}", fg=typer.colors.GREEN)


@app.command()
def delete(id: int) -> None:
    """物理删除 Task（ID 永不复用）。"""
    store = load_store()
    if not store.remove(id):
        fail(f"ID {id} 不存在")
    store.save()
    typer.secho(f"已删除 Task {id}", fg=typer.colors.YELLOW)


if __name__ == "__main__":
    app()

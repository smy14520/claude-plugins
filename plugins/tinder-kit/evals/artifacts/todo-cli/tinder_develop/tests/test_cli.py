"""CLI 端到端接缝：argv 进、stdout/exit code 出。TODO_FILE 环境变量为存储注入接缝。"""

import pytest

from todo_cli.cli import main


@pytest.fixture
def run(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("TODO_FILE", str(tmp_path / "todos.json"))

    def run(*args):
        code = main(list(args))
        captured = capsys.readouterr()
        return code, captured.out, captured.err

    return run


def test_add_done_list_flow(run):
    code, out, _ = run("add", "买牛奶", "-t", "生活", "-t", "采购")
    assert (code, out) == (0, "Added 1: 买牛奶 [生活, 采购]\n")

    run("add", "写周报", "-t", "工作")
    code, out, _ = run("done", "2")
    assert (code, out) == (0, "Completed 2: 写周报\n")

    # 默认仅显示未完成
    code, out, _ = run("list")
    assert out == "[ ] 1  买牛奶  #生活 #采购\n"

    # --all 含已完成
    code, out, _ = run("list", "--all")
    assert out == "[ ] 1  买牛奶  #生活 #采购\n[x] 2  写周报  #工作\n"


def test_list_filters_by_tags_with_and_semantics(run):
    run("add", "a", "-t", "生活")
    run("add", "b", "-t", "生活", "-t", "采购")

    code, out, _ = run("list", "-t", "生活", "-t", "采购")

    assert (code, out) == (0, "[ ] 2  b  #生活 #采购\n")


def test_list_empty_shows_friendly_message(run):
    code, out, _ = run("list")

    assert (code, out) == (0, "No tasks.\n")


def test_remove_reports_and_takes_effect(run):
    run("add", "a")

    code, out, _ = run("rm", "1")
    assert (code, out) == (0, "Removed 1: a\n")

    code, out, _ = run("list")
    assert out == "No tasks.\n"


def test_tags_reports_counts_across_all_tasks(run):
    run("add", "a", "-t", "工作", "-t", "紧急")
    run("add", "b", "-t", "工作")
    run("done", "2")

    code, out, _ = run("tags")

    assert (code, out) == (0, "工作 (2)\n紧急 (1)\n")


def test_unknown_id_fails_with_exit_code_1(run):
    code, out, err = run("done", "99")

    assert code == 1
    assert err == "Error: task 99 not found\n"


def test_corrupt_store_file_fails_without_reset(tmp_path, monkeypatch, capsys):
    path = tmp_path / "todos.json"
    path.write_text("{oops", encoding="utf-8")
    monkeypatch.setenv("TODO_FILE", str(path))

    code = main(["list"])

    captured = capsys.readouterr()
    assert code == 1
    assert "存储文件损坏" in captured.err
    # 绝不静默重置：坏文件原样保留
    assert path.read_text(encoding="utf-8") == "{oops"

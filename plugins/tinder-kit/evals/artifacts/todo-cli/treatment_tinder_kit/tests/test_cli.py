"""Seam 3 — cli.main 端到端行为测试（注入临时 Store 路径，断言 stdout/stderr/退出码）。"""
import json

from todo_cli.cli import main


def run(argv, path):
    return main(argv, store_path=path)


def test_add_then_list_default_hides_done(tmp_path, capsys):
    path = tmp_path / "todos.json"
    assert run(["add", "买牛奶", "-t", "shopping"], path) == 0
    assert run(["add", "寄快递", "-t", "errand", "-t", "shopping"], path) == 0
    out = capsys.readouterr().out
    assert "[ ]" in out and "#shopping" in out  # add 回显新条目行

    assert run(["done", "1"], path) == 0
    capsys.readouterr()

    assert run(["list"], path) == 0
    out = capsys.readouterr().out
    assert "寄快递" in out and "买牛奶" not in out  # 默认只显示 open

    assert run(["list", "--all"], path) == 0
    out = capsys.readouterr().out
    assert "买牛奶" in out and "[x]" in out  # --all 含已完成


def test_list_multiple_tags_is_intersection(tmp_path, capsys):
    path = tmp_path / "todos.json"
    run(["add", "a", "-t", "x"], path)
    run(["add", "b", "-t", "x", "-t", "y"], path)
    capsys.readouterr()
    assert run(["list", "--tag", "x", "--tag", "y"], path) == 0
    out = capsys.readouterr().out
    assert "b" in out and "a" not in out


def test_undo_reopens(tmp_path, capsys):
    path = tmp_path / "todos.json"
    run(["add", "a"], path)
    run(["done", "1"], path)
    capsys.readouterr()
    assert run(["undo", "1"], path) == 0
    assert "a" in capsys.readouterr().out  # undo 后重新出现在默认 list


def test_unknown_id_errors_on_stderr_with_nonzero_exit(tmp_path, capsys):
    assert run(["done", "99"], tmp_path / "todos.json") == 1
    err = capsys.readouterr().err
    assert "99" in err


def test_non_integer_id_is_rejected(tmp_path, capsys):
    assert run(["done", "abc"], tmp_path / "todos.json") != 0
    assert capsys.readouterr().err.strip()  # argparse 报错也走 stderr


def test_rm_removes_and_ids_keep_counting(tmp_path, capsys):
    path = tmp_path / "todos.json"
    run(["add", "a"], path)
    run(["add", "b"], path)
    assert run(["rm", "2"], path) == 0
    capsys.readouterr()
    assert run(["list"], path) == 0
    assert "b" not in capsys.readouterr().out
    assert run(["add", "c"], path) == 0
    out = capsys.readouterr().out
    assert "c" in out and "3" in out  # 新条目拿 3 号，不复用 2（ADR-0003）


def test_tags_lists_counts(tmp_path, capsys):
    path = tmp_path / "todos.json"
    run(["add", "a", "-t", "x"], path)
    run(["add", "b", "-t", "y"], path)
    run(["add", "c", "-t", "x"], path)
    run(["done", "3"], path)
    capsys.readouterr()
    assert run(["tags"], path) == 0
    out = capsys.readouterr().out
    assert "x" in out and "y" in out
    assert out.index("x") < out.index("y")  # 字典序


def test_persistence_across_invocations(tmp_path):
    path = tmp_path / "todos.json"
    run(["add", "买牛奶", "-t", "shopping"], path)
    assert path.exists()  # ~/.todo-cli.json 的可注入等价物


def test_read_only_commands_never_create_or_rewrite_store(tmp_path, capsys):
    """spec：Store 文件"首次写入时创建"——只读命令绝不落盘，也不冲掉用户手改。"""
    path = tmp_path / "todos.json"
    assert run(["list"], path) == 0
    assert not path.exists()  # 读取不创建
    assert run(["tags"], path) == 0
    assert not path.exists()

    run(["add", "a"], path)
    hand_edited = json.dumps(json.loads(path.read_text(encoding="utf-8")),
                             ensure_ascii=False, separators=(",", ":"))  # 用户手动压缩排版
    path.write_text(hand_edited, encoding="utf-8")
    assert run(["list"], path) == 0
    assert "a" in capsys.readouterr().out
    assert path.read_text(encoding="utf-8") == hand_edited  # 手改被完整保留


def test_list_surface_matches_spec_no_t_shorthand(tmp_path, capsys):
    """spec 命令表：list 只有 --tag，-t 是 add 专属。"""
    assert run(["list", "-t", "x"], tmp_path / "todos.json") != 0
    assert capsys.readouterr().err.strip()


def test_add_priority_echoed_and_list_sorted_high_med_low_none(tmp_path, capsys):
    path = tmp_path / "todos.json"
    assert run(["add", "plain"], path) == 0
    assert run(["add", "urgent", "--priority", "high"], path) == 0
    out = capsys.readouterr().out
    assert "urgent" in out and "high" in out  # add 回显带优先级
    run(["add", "later", "--priority", "low"], path)
    run(["add", "mid", "--priority", "med"], path)
    capsys.readouterr()

    assert run(["list"], path) == 0
    out = capsys.readouterr().out
    assert (out.index("urgent") < out.index("mid")
            < out.index("later") < out.index("plain"))


def test_priority_rejects_values_outside_choices(tmp_path, capsys):
    assert run(["add", "x", "--priority", "urgent"], tmp_path / "t.json") != 0
    assert capsys.readouterr().err.strip()


def test_delete_is_primary_and_rm_still_works_as_alias(tmp_path, capsys):
    path = tmp_path / "todos.json"
    run(["add", "a"], path)
    run(["add", "b"], path)
    capsys.readouterr()
    assert run(["delete", "1"], path) == 0
    assert run(["rm", "2"], path) == 0
    assert run(["list"], path) == 0
    assert capsys.readouterr().out.strip() == ""


def test_done_and_undo_echo_keeps_priority_column(tmp_path, capsys):
    """spec：优先级列在该 Todo 有优先级时出现——回显与 list 同规矩。"""
    path = tmp_path / "todos.json"
    run(["add", "urgent", "--priority", "high"], path)
    capsys.readouterr()
    assert run(["done", "1"], path) == 0
    out = capsys.readouterr().out
    assert "[x]" in out and "high" in out
    assert run(["undo", "1"], path) == 0
    assert "high" in capsys.readouterr().out

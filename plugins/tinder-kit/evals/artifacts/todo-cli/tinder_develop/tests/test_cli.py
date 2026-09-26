"""cli.py 展示层测试。

Seam：cli.main(argv) -> int 的公共接口（stdout 用 capsys 捕获）。
测试隔离经 monkeypatch.chdir(tmp_path)，绝不打真实 HOME。
"""

import pytest

from todo import cli


def run(capsys, *argv):
    """跑一条命令，返回 (退出码, stdout)。"""
    code = cli.main(list(argv))
    return code, capsys.readouterr().out


def test_add_then_list_shows_title_and_tags(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    code, out = run(capsys, "add", "买牛奶", "--tags", "生活,采购")
    assert code == 0
    code, out = run(capsys, "list")
    assert code == 0
    assert "买牛奶" in out
    assert "#生活" in out and "#采购" in out


def test_add_with_priority_shows_it_in_list(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    run(capsys, "add", "付房租", "--priority", "high")
    _, out = run(capsys, "list")
    assert "付房租" in out
    assert "high" in out


def test_add_rejects_priority_outside_three_levels(tmp_path, monkeypatch, capsys):
    """三档之外（如 urgent）必须被拒：argparse 以非零码退出。"""
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as e:
        cli.main(["add", "x", "--priority", "urgent"])
    assert e.value.code != 0


def test_list_empty_shows_hint_not_traceback(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    code, out = run(capsys, "list")
    assert code == 0
    assert out.strip() != ""  # 有友好提示，而非崩出 traceback


# --- 生命周期：done / undo / rm ---


def test_done_hides_from_default_list_and_marks_in_all(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    run(capsys, "add", "Todo A")
    _, out = run(capsys, "done", "1")
    assert "1" in out  # 确认信息
    _, out = run(capsys, "list")
    assert "Todo A" not in out  # 默认只列未完成
    _, out = run(capsys, "list", "--all")
    assert "Todo A" in out and "✓" in out  # --all 含已完成，带勾


def test_undo_flips_done_back_to_open(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    run(capsys, "add", "Todo A")
    run(capsys, "done", "1")
    run(capsys, "undo", "1")
    _, out = run(capsys, "list")
    assert "Todo A" in out  # 重开后又出现在默认清单


def test_rm_removes_todo_entirely(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    run(capsys, "add", "Todo A")
    run(capsys, "add", "Todo B")
    code, out = run(capsys, "rm", "1")
    assert code == 0
    _, out = run(capsys, "list", "--all")
    assert "Todo A" not in out
    assert "Todo B" in out  # 无辜者不受牵连


def test_tags_lists_distinct_in_use_tags(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    run(capsys, "add", "A", "--tags", "工作,紧急")
    run(capsys, "add", "B", "--tags", "生活")
    code, out = run(capsys, "tags")
    assert code == 0
    assert "工作" in out and "紧急" in out and "生活" in out
    assert "工作" in out.split()  # 出现在 Tag 列表中而非别的文字里


# --- CLI 级 AND 过滤与空结果 ---


def test_list_multiple_tag_filters_is_and_semantics(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    run(capsys, "add", "全命中", "--tags", "工作,紧急")
    run(capsys, "add", "只有工作", "--tags", "工作")
    _, out = run(capsys, "list", "--tag", "工作", "--tag", "紧急")
    assert "全命中" in out
    assert "只有工作" not in out  # AND：差一个 Tag 都不行


def test_list_tag_filter_with_no_match_prints_no_match_hint(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    run(capsys, "add", "买牛奶", "--tags", "生活")
    code, out = run(capsys, "list", "--tag", "不存在的 Tag")
    assert code == 0
    assert "无匹配" in out


# --- 错误路径：一切失败都必须是 exit 1 + stderr 明示 ---


def test_done_missing_id_fails_with_exit_1(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    code = cli.main(["done", "99"])
    err = capsys.readouterr().err
    assert code == 1
    assert "99" in err


def test_rm_and_undo_missing_id_fail_with_exit_1(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert cli.main(["rm", "99"]) == 1
    assert cli.main(["undo", "99"]) == 1


def test_done_on_already_done_fails_and_undo_on_open_fails(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    run(capsys, "add", "Todo A")
    assert cli.main(["done", "1"]) == 0
    assert cli.main(["done", "1"]) == 1  # 已完成不可再 done
    assert cli.main(["undo", "1"]) == 0
    assert cli.main(["undo", "1"]) == 1  # 未完成不可 undo

"""todo.py 的测试。领域规则与决策出处见 CONTEXT.md 与 docs/adr/。"""

import json

import pytest

from todo import Task, TodoError, main, normalize_tags, parse_priority, render


@pytest.fixture
def todo_file(tmp_path, monkeypatch):
    path = tmp_path / "todos.json"
    monkeypatch.setenv("TODO_FILE", str(path))
    return path


def run(*argv):
    return main(list(argv))


def drain(capsys):
    """排空已捕获输出：setup 阶段的打印不应混进被测命令的断言。"""
    return capsys.readouterr()


def read(todo_file):
    return json.loads(todo_file.read_text(encoding="utf-8"))


# ---- add：ID、标签、优先级 ---------------------------------------------------------


def test_add_assigns_ids_and_defaults(todo_file, capsys):
    assert run("add", "买牛奶") == 0
    data = read(todo_file)
    assert data["next_id"] == 2
    assert data["tasks"] == [
        {"id": 1, "text": "买牛奶", "tags": [], "priority": "med", "done": False}
    ]
    assert "[ ] 1 买牛奶" in capsys.readouterr().out


def test_ids_never_reused_after_delete(todo_file):
    run("add", "a")
    run("add", "b")
    run("delete", "1")
    run("add", "c")
    assert [t["id"] for t in read(todo_file)["tasks"]] == [2, 3]


def test_add_tags_and_priority(todo_file, capsys):
    assert run("add", "修屋顶", "--tag", "家", "--tag", "diy", "--priority", "HIGH") == 0
    task = read(todo_file)["tasks"][0]
    assert task["tags"] == ["家", "diy"]
    assert task["priority"] == "high"  # 大小写不敏感，归一为小写存储
    assert "!high" in capsys.readouterr().out


def test_add_dedupes_tags_case_insensitively(todo_file):
    run("add", "x", "--tag", "work", "--tag", "WORK", "--tag", " work ")
    assert read(todo_file)["tasks"][0]["tags"] == ["work"]


def test_add_strips_text(todo_file):
    run("add", "  带空白的任务  ")
    assert read(todo_file)["tasks"][0]["text"] == "带空白的任务"


def test_add_rejects_blank_text(todo_file, capsys):
    assert run("add", "   ") == 1
    assert "任务内容不能为空" in capsys.readouterr().err


def test_add_rejects_empty_tag(todo_file, capsys):
    assert run("add", "x", "--tag", "  ") == 1
    assert "标签不能为空" in capsys.readouterr().err


def test_add_rejects_invalid_priority(todo_file):
    with pytest.raises(SystemExit) as excinfo:
        run("add", "x", "--priority", "urgent")
    assert excinfo.value.code == 2  # argparse 对非法枚举值的退出码


def test_normalize_tags_keeps_first_casing():
    assert normalize_tags(["Work", "WORK", " home "]) == ["Work", "home"]
    with pytest.raises(TodoError):
        normalize_tags(["ok", " "])


def test_parse_priority_normalizes():
    assert parse_priority(" Low ") == "low"
    with pytest.raises(Exception):
        parse_priority("nope")


# ---- list：可见性、标签 AND、优先级过滤、稳定排序 -----------------------------------


def test_list_defaults_to_open_and_keeps_creation_order(todo_file, capsys):
    run("add", "一")
    run("add", "二")
    run("done", "1")
    drain(capsys)
    assert run("list") == 0
    out = capsys.readouterr().out
    assert "[x] 1 一" not in out
    assert "[ ] 2 二" in out


def test_list_done_and_all(todo_file, capsys):
    run("add", "一")
    run("add", "二")
    run("done", "1")
    drain(capsys)
    run("list", "--done")
    done_out = capsys.readouterr().out
    assert "[x] 1 一" in done_out and "二" not in done_out
    run("list", "--all")
    all_out = capsys.readouterr().out
    assert "[x] 1 一" in all_out and "[ ] 2 二" in all_out


def test_list_done_and_all_are_mutually_exclusive(todo_file):
    with pytest.raises(SystemExit) as excinfo:
        run("list", "--done", "--all")
    assert excinfo.value.code == 2


def test_list_multiple_tags_is_and(todo_file, capsys):
    run("add", "A", "--tag", "work")
    run("add", "B", "--tag", "work", "--tag", "urgent")
    run("add", "C", "--tag", "urgent")
    drain(capsys)
    assert run("list", "--tag", "work", "--tag", "urgent") == 0
    out = capsys.readouterr().out
    assert "[ ] 2 B #work #urgent" in out
    assert "A" not in out and "C" not in out


def test_list_tag_match_is_case_insensitive(todo_file, capsys):
    run("add", "A", "--tag", "Work")
    drain(capsys)
    assert run("list", "--tag", "work") == 0
    assert "[ ] 1 A #Work" in capsys.readouterr().out  # 显示保留输入原样


def test_list_priority_filter(todo_file, capsys):
    run("add", "要紧事", "--priority", "high")
    run("add", "普通事")
    drain(capsys)
    assert run("list", "--priority", "high") == 0
    out = capsys.readouterr().out
    assert "要紧事" in out and "普通事" not in out


def test_list_combines_priority_tag_and_visibility(todo_file, capsys):
    run("add", "命中", "--tag", "work", "--priority", "high")
    run("add", "标签对但优先级低", "--tag", "work")
    run("add", "优先级对但已完成", "--tag", "work", "--priority", "high")
    run("done", "3")
    drain(capsys)
    assert run("list", "--tag", "work", "--priority", "high") == 0
    out = capsys.readouterr().out
    assert "命中" in out and "标签对但优先级低" not in out and "优先级对但已完成" not in out


def test_list_empty_result_is_friendly_not_silent(todo_file, capsys):
    assert run("list") == 0
    assert "没有匹配的任务" in capsys.readouterr().err


def test_bare_todo_behaves_like_list(todo_file, capsys):
    run("add", "一")
    drain(capsys)
    assert main([]) == 0
    assert "[ ] 1 一" in capsys.readouterr().out


# ---- done / reopen / delete -------------------------------------------------------


def test_done_and_reopen_roundtrip(todo_file, capsys):
    run("add", "一")
    run("done", "1")
    assert "[x] 1 一" in capsys.readouterr().out
    run("reopen", "1")
    assert "[ ] 1 一" in capsys.readouterr().out
    assert read(todo_file)["tasks"][0]["done"] is False


def test_done_is_idempotent(todo_file, capsys):
    run("add", "一")
    run("done", "1")
    run("done", "1")
    assert "本就处于已完成状态" in capsys.readouterr().out


def test_nonexistent_id_fails_cleanly(todo_file, capsys):
    run("add", "一")
    assert run("done", "99") == 1
    assert "不存在 ID 为 99" in capsys.readouterr().err


def test_delete_removes_record(todo_file):
    run("add", "一")
    assert run("delete", "1") == 0
    assert read(todo_file)["tasks"] == []


def test_rm_is_alias_of_delete(todo_file):
    run("add", "一")
    run("add", "二")
    assert run("rm", "1") == 0
    assert [t["id"] for t in read(todo_file)["tasks"]] == [2]


# ---- 存储安全 ----------------------------------------------------------------------


def test_missing_file_starts_empty(todo_file, capsys):
    assert run("list") == 0
    assert not todo_file.exists()


def test_corrupted_json_is_never_overwritten(todo_file, capsys):
    garbage = "{ not valid json"
    todo_file.write_text(garbage, encoding="utf-8")
    for argv in (("list",), ("add", "新任务")):
        assert run(*argv) == 1
        assert "不是合法 JSON" in capsys.readouterr().err
    assert todo_file.read_text(encoding="utf-8") == garbage  # 拒绝读写，原样保留


def test_store_defaults_and_defensive_read(todo_file):
    # 手工编辑：缺 next_id、缺 tags/priority/done 字段，均不应崩溃
    todo_file.write_text(
        json.dumps({"tasks": [{"id": 7, "text": "手工"}]}, ensure_ascii=False),
        encoding="utf-8",
    )
    assert run("list") == 0
    run("add", "追加")
    data = read(todo_file)
    assert data["next_id"] == 9  # 派生自现有最大 ID（7），分配 8 后计数器推进到 9
    assert data["tasks"][-1]["id"] == 8


def test_render_hides_default_priority():
    assert render(Task(id=1, text="t")) == "[ ] 1 t"
    assert render(Task(id=1, text="t", done=True)) == "[x] 1 t"
    assert render(Task(id=1, text="t", tags=["a"], priority="low")) == "[ ] 1 t #a !low"

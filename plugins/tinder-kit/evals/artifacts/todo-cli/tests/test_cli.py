"""Seam 3：CLI 端到端契约。

进程内调用 todo.main(argv)，经 $TODO_FILE 接缝注入临时存储，
以 capsys 断言 stdout/stderr 与返回码。隔离由根 conftest 的 autouse 夹具保证。
"""

import todo


def run(*argv):
    return todo.main(list(argv))


class TestStoragePathResolution:
    def test_todo_file_env_override_selects_storage_path(self, tmp_path, monkeypatch):
        custom = tmp_path / "custom.json"
        monkeypatch.setenv("TODO_FILE", str(custom))
        assert run("add", "隔离验证") == 0
        assert custom.exists()

    def test_default_path_is_home_dot_todos_json_not_cwd(self, tmp_path, monkeypatch):
        fake_home = tmp_path / "fake-home"
        fake_home.mkdir()
        monkeypatch.setenv("HOME", str(fake_home))
        monkeypatch.delenv("TODO_FILE", raising=False)
        monkeypatch.chdir(tmp_path)
        assert run("add", "默认路径") == 0
        assert (fake_home / ".todos.json").exists()
        assert not (tmp_path / ".todos.json").exists()


class TestAddAndList:
    def test_add_parses_inline_tags_and_priority_then_lists(self, capsys):
        assert run("add", "买牛奶 +shopping +urgent", "--priority", "high") == 0
        capsys.readouterr()  # 排干 setup 回显，只观测 list 输出
        assert run("list") == 0
        out = capsys.readouterr().out
        assert "[1] [high] [ ] 买牛奶 #shopping #urgent" in out

    def test_add_priority_defaults_to_med(self, capsys):
        run("add", "普通任务")
        capsys.readouterr()
        run("list")
        assert "[med]" in capsys.readouterr().out

    def test_add_invalid_priority_exits_nonzero_with_stderr(self, capsys):
        rc = run("add", "坏任务", "--priority", "urgent")
        assert rc != 0
        assert "urgent" in capsys.readouterr().err

    def test_ids_increment_across_adds(self, capsys):
        run("add", "任务甲")
        run("add", "任务乙")
        capsys.readouterr()
        run("list")
        out = capsys.readouterr().out
        assert out.index("[1]") < out.index("[2]")

    def test_id_keeps_max_plus_one_after_delete_of_latest(self, capsys):
        run("add", "任务甲")  # id 1
        run("add", "任务乙")  # id 2
        run("delete", "2")
        run("add", "任务丙")  # 应取 max(1)+1 = 2
        capsys.readouterr()
        run("list")
        out = capsys.readouterr().out
        assert "[2] [med] [ ] 任务丙" in out


class TestListFiltering:
    def test_multiple_tag_flags_intersect(self, capsys):
        run("add", "任务甲 +x")
        run("add", "任务乙 +x +y")
        run("add", "任务丙 +y")
        capsys.readouterr()  # 排干 setup 回显，只观测 list 输出
        run("list", "--tag", "x", "--tag", "y")
        out = capsys.readouterr().out
        assert "任务乙" in out
        assert "任务甲" not in out
        assert "任务丙" not in out

    def test_hides_done_by_default_and_all_shows_them(self, capsys):
        run("add", "未完成任务")
        run("add", "将被完成")
        run("done", "2")
        capsys.readouterr()  # 排干 setup 回显，只观测 list 输出

        run("list")
        out = capsys.readouterr().out
        assert "未完成任务" in out
        assert "将被完成" not in out

        run("list", "--all")
        out_all = capsys.readouterr().out
        assert "未完成任务" in out_all
        assert "[x] 将被完成" in out_all

    def test_orders_high_before_med_before_low(self, capsys):
        run("add", "低", "--priority", "low")     # id 1
        run("add", "高", "--priority", "high")    # id 2
        run("add", "中", "--priority", "med")     # id 3
        capsys.readouterr()  # 排干 setup 回显，只观测 list 输出
        run("list")
        out = capsys.readouterr().out
        assert out.index("[2]") < out.index("[3]") < out.index("[1]")


class TestDoneAndDelete:
    def test_done_marks_item_hidden_from_default_list(self, capsys):
        run("add", "任务甲")
        assert run("done", "1") == 0
        capsys.readouterr()  # 排干 setup 回显，只观测 list 输出
        run("list")
        assert "任务甲" not in capsys.readouterr().out

    def test_done_is_idempotent(self, capsys):
        run("add", "任务甲")
        assert run("done", "1") == 0
        assert run("done", "1") == 0

    def test_done_missing_id_exits_nonzero_with_stderr(self, capsys):
        run("add", "任务甲")
        rc = run("done", "99")
        assert rc != 0
        assert "99" in capsys.readouterr().err

    def test_delete_removes_only_targeted_item(self, capsys):
        run("add", "任务甲")
        run("add", "任务乙")
        assert run("delete", "1") == 0
        capsys.readouterr()  # 排干 setup 回显，只观测 list 输出
        run("list")
        out = capsys.readouterr().out
        assert "任务甲" not in out
        assert "任务乙" in out

    def test_delete_missing_id_exits_nonzero_with_stderr(self, capsys):
        run("add", "任务甲")
        assert run("delete", "1") == 0
        rc = run("delete", "1")
        assert rc != 0
        assert "1" in capsys.readouterr().err


class TestArgvEdgeCases:
    def test_unknown_subcommand_exits_nonzero(self, capsys):
        assert run("frobnicate") != 0

    def test_no_subcommand_exits_nonzero(self, capsys):
        assert run() != 0

    def test_rm_alias_is_not_accepted(self, capsys):
        """v1.1 契约：rm 更名 delete 且不留别名。"""
        run("add", "任务甲")
        capsys.readouterr()
        rc = run("rm", "1")
        assert rc != 0
        assert "rm" in capsys.readouterr().err

    def test_tags_command_is_removed(self, capsys):
        """v1.1 契约：命令面收敛为 add/list/done/delete 恰好四个。"""
        rc = run("tags")
        assert rc != 0
        assert "tags" in capsys.readouterr().err

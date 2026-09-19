import sys
from pathlib import Path

import pytest

TOOL_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOL_DIR))

from forge import (
    cmd_new,
    endorsement_path,
    get_task_handoffs,
    get_task_seams,
    read_state,
    spec_path,
    write_state,
)


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    ws = tmp_path / "project"
    ws.mkdir()
    return ws


def test_develop_lifecycle_simulation(workspace: Path):
    slug = "payment-gateway"

    # 1. 阶段 0: 初始化脚手架
    cmd_new(workspace, slug, "聚合支付网关重构")
    st0 = read_state(workspace, slug)
    assert st0.phase == "ALIGN"

    # 2. 阶段 1: 对齐并在 spec.md 中定义 2 个 Seams (原生文件编辑，无 CLI 中间商)
    spec_file = spec_path(workspace, slug)
    content = spec_file.read_text(encoding="utf-8")
    content += "\n## Agreed Seams\n"
    content += "- **Seam 1**: `PaymentService.pay(orderId, amount) -> Result<Receipt, PayError>`\n"
    content += "- **Seam 2**: `PaymentWebhook.handle(signature, payload) -> Result<Event, AuthError>`\n"
    spec_file.write_text(content, encoding="utf-8")

    # 产出 01-align.md 交接文档
    align_handoff = workspace / ".forge" / "tasks" / slug / "handoffs" / "01-align.md"
    align_handoff.write_text("# Handoff: ALIGN\n\n## 1. Settled Decisions\n- 采用策略模式支持微信与支付宝\n", encoding="utf-8")

    # 状态原生更新至 EXPLORE
    st0.phase = "EXPLORE"
    write_state(workspace, st0)

    # 3. 阶段 2: 原型探索完成，产出 02-explore.md
    explore_handoff = workspace / ".forge" / "tasks" / slug / "handoffs" / "02-explore.md"
    explore_handoff.write_text("# Handoff: EXPLORE\n\n## 3. Discovered Gotchas\n- 微信支付异步通知存在 5s 幂等窗口\n", encoding="utf-8")

    st0.phase = "IMPLEMENT"
    write_state(workspace, st0)

    # 4. 阶段 3: 实现完成，产出 03-impl.md
    impl_handoff = workspace / ".forge" / "tasks" / slug / "handoffs" / "03-impl.md"
    impl_handoff.write_text("# Handoff: IMPLEMENT\n\n## 2. Agreed Seams\n- 两个 Seam 行为测试 100% 跑绿\n", encoding="utf-8")

    st0.phase = "REVIEW"
    write_state(workspace, st0)

    # 5. 阶段 4: 双轴审查通过，生成 endorsement.md 背书文件
    end_file = endorsement_path(workspace, slug)
    end_file.write_text("# Endorsement: 聚合支付网关重构\n\n## 1. Seams Verification\n- Seams 1 & 2: PASS\n", encoding="utf-8")

    st0.phase = "COMPLETED"
    write_state(workspace, st0)

    # 6. 全面校验：动态从文件系统派生，单一定义点无冗余
    st_final = read_state(workspace, slug)
    assert st_final.phase == "COMPLETED"

    seams = get_task_seams(workspace, slug)
    assert len(seams) == 2
    assert "PaymentService.pay" in seams[0]
    assert "PaymentWebhook.handle" in seams[1]

    handoffs = get_task_handoffs(workspace, slug)
    assert handoffs == ["01-align.md", "02-explore.md", "03-impl.md"]

    assert endorsement_path(workspace, slug).is_file()


def test_multi_task_concurrency_isolation(workspace: Path):
    # 创建任务 A (大型功能)
    cmd_new(workspace, "feat-oauth", "OAuth2 登录")
    spec_a = spec_path(workspace, "feat-oauth")
    spec_a.write_text(spec_a.read_text(encoding="utf-8") + "\n## Agreed Seams\n- **Seam 1**: `OAuthProvider.auth()`\n", encoding="utf-8")

    st_a = read_state(workspace, "feat-oauth")
    st_a.phase = "IMPLEMENT"
    write_state(workspace, st_a)

    # 创建任务 B (偶现 Bug 修复)
    cmd_new(workspace, "fix-null-pointer", "修复空指针")
    spec_b = spec_path(workspace, "fix-null-pointer")
    spec_b.write_text(spec_b.read_text(encoding="utf-8") + "\n## Agreed Seams\n- **Seam 1**: `DateParser.parse()`\n", encoding="utf-8")

    st_b = read_state(workspace, "fix-null-pointer")
    st_b.phase = "COMPLETED"
    write_state(workspace, st_b)

    # 互不干扰验证：纯目录与文件隔离，零全局变量干扰
    read_a = read_state(workspace, "feat-oauth")
    read_b = read_state(workspace, "fix-null-pointer")

    assert read_a.slug == "feat-oauth"
    assert read_a.phase == "IMPLEMENT"
    assert "OAuthProvider.auth" in get_task_seams(workspace, "feat-oauth")[0]

    assert read_b.slug == "fix-null-pointer"
    assert read_b.phase == "COMPLETED"
    assert "DateParser.parse" in get_task_seams(workspace, "fix-null-pointer")[0]

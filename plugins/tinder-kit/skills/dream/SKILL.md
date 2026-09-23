---
name: dream
description: "跨级记忆（CLAUDE.md、.claude/rules/、.forge/wiki/）只读体检与重组。识别僵尸失效条目、规则冲突与冗余碎片，生成只读 RFC 整理提议报告供人类裁决。"
disable-model-invocation: true
---

# Dream — 记忆梦境大扫除与 RFC 提议报告

模拟人脑睡眠中的“记忆重组（Memory Consolidation）”机制：对长期累积的 `CLAUDE.md`、`.claude/rules/` 与 `.forge/wiki/` 进行只读体检与深度交叉比对，输出格式严谨的 **RFC 整理提议报告** 呈递给人类。

本技能执行只读审计，输出 RFC 报告后停下，等用户裁决。

---

## 阶段一：只读三向交叉扫描 (Cross-Audit)

全面读取三级记忆资产，并对照当前工作树代码库进行静态分析：

1. **👻 僵尸条目（Zombie / Stale Entries）**：
   - 运行 `forge wiki lint --json`：失效的符号锚、断链、孤儿页由命令直接列出；
   - 在此基础上判断哪些条目描述的行为已被代码废弃（符号还在但语义已变，命令查不出）。
2. **⚡ 规则冲突（Rule Contradictions）**：
   - 交叉比对 `CLAUDE.md` 与 `.claude/rules/` 下的所有规则；
   - 标出由于不同时期编写导致的冲突建议（如一条写“所有改动必须通过单测”，另一条写“脚本改动直接手动自验”）。
3. **📦 碎片化与重复（Bloat & Redundancy）**：
   - 识别语义高度相似、分散在多个页面的踩坑记录（Gotchas）或领域概念；
   - 设计合并重组方案。
4. **🧭 放置越位（Placement Drift）**：
   - 对照三问放置判据检查：
     - 是否有长尾琐碎的单文件细节错误地塞进了 `CLAUDE.md`（污染全景工作记忆）；
     - 是否有全项目必须遵守的底线被藏在深层 Wiki 中。

---

## 阶段二：编撰《记忆健康与整理提议报告》（RFC Report）

在终端中向人类呈现清晰结构化的报告，包含体检仪表盘与编号提议：

```markdown
# 🏛️ 项目记忆健康与整理提议报告 (Memory RFC)

## 1. 记忆体检概览
- 规则文件: X 个 | Wiki 词条: Y 个 | 发现失效引用: Z 处 | 潜在规则冲突: W 处

## 2. 编号整理提议清单

### [RFC-1] 👻 建议归档僵尸条目
- **目标**: `.forge/wiki/gotcha/old-api-bug.md`
- **原因**: 引用符号 `src/legacy.ts#OldParser` 已在提交 a1b2c3d 中被删除。
- **动作**: 移入 `.forge/wiki/archive/`。

### [RFC-2] ⚡ 规则冲突请人类裁决
- **冲突点**: 测试执行要求不一致
  - `CLAUDE.md:12`: "所有修改必须 100% 跑通单测"
  - `.claude/rules/frontend.md:5`: "纯前端 UI 调整以 perceive 截图为准，免单测"
- **建议解决方案**: 明确分工，修改 `CLAUDE.md` 措辞为“根据技术栈遵循对应测试与感官自验规则”。

### [RFC-3] 📦 合并碎片化踩坑条目
- **建议合并**: `gotcha/cors-vite.md` 与 `gotcha/proxy-config.md` -> `gotcha/dev-server-network.md`
- **合并后草案**:
  [呈现简洁的合并预览 Diff]
```

---

## 阶段三：等待人类指示与精准执行 (Human-on-the-Loop)

1. 输出 RFC 报告后停下，等用户裁决；
2. **人类指令接续**：
   - 若人类回复：“批准全部”，调用相关工具执行全部 RFC 调整；
   - 若人类回复：“采纳 RFC-1 和 RFC-3，忽略 RFC-2”，仅执行指定条目；
3. 执行完成后运行 `forge wiki index --write` 重建索引，并向人类汇报变动摘要。

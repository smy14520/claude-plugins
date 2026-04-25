# 实现会话日志: <name>

<!-- 输出语言: 中文 -->

仅追加。每次任务运行（每次状态变更）一条记录。

<!--
  可选文件。仅在以下情况创建：
  - 单次会话运行多个任务（审计轨迹有用）
  - 用户明确需要累积记录
  - 跨会话工作并需要上下文延续

  对于单次任务运行，task package 的 task.json 已足够。
-->

## [YYYY-MM-DD HH:MM] T-001 DONE

- 交付物: <变更的文件>
- 自检:
  - cmd1 — exit 0 (N tests)
  - cmd2 — match expected
- 耗时: Xh Ymin
- 备注: <可选>

## [YYYY-MM-DD HH:MM] T-003 NEEDS_CONTEXT

- 阻塞于: <歧义摘要>
- 待澄清: <具体问题>
- 代码状态: <无变更 / 部分完成 X>
- 耗时: Xh Ymin

## [YYYY-MM-DD HH:MM] T-003 DONE

- (用户澄清 <thing> 后重新运行)
- 交付物: <files>
- 自检:
  - cmd1 — exit 0
- 耗时: Xh Ymin
- 备注: NEEDS_CONTEXT 阶段的问题已解决

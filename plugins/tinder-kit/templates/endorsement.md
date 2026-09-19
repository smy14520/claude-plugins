# Endorsement: {title}

> 任务: `{task_slug}` | 背书时间: {timestamp}

## 1. Seams Verification (深接缝验证)

<!-- 商定的核心 Seams 行为测试证据 -->
- **{seam_1}**: PASS
  - 验证用例: `{test_command_or_file}`
  - 验证产物: {result_summary}

## 2. Regression Safety (系统防回归)

<!-- 代码库全量既有测试的运行结果，无测试框架时记录可执行自验证据 -->
- 验证命令: `{regression_command_or_smoke_check}`
- 执行结果: 全部通过 (exit 0) 或 自验符合预期

## 3. Code Review Verdict (双轴审查结论)

- **Standards 轴 (规范与坏味道)**: {standards_verdict}
- **Spec 轴 (契约与接缝吻合度)**: {spec_verdict}
- 关键发现与自动修正: {review_summary}

## 4. Human Commit Ready (交付就绪)

系统改动已通过全部深接缝与防回归背书，代码质量经双轴审查收敛。请人类开发者审查 `git diff` 并执行 Commit。

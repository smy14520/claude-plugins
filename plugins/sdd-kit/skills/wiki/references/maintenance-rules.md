# Wiki 维护 checklist

`.wiki/` 是项目本地导航层，不是 source of truth。详细 schema 看 `page-types.md`；操作流程看 `operations.md`；反模式看 `anti-patterns.md`。

## 必查项

- 每页有 `title` / `description` / `type`；建议有 `summary` / `tags`。
- `index.md` 只做入口，不复制所有子页面。
- 根页面只在领域已有多个相关 note 时创建。
- Module note 必须有 `package` / `source_checkpoint`，且 locator 不写 line number。
- 不把隐藏目录原始内容整理进 wiki；需要时读取 source of truth。
- Query 先用 `sdd-wiki collect --query "<query>" --limit 5 --json`，再选择性读页面。
- Lint 用 `sdd-wiki lint --json`；报告和建议可以，不能擅自删除或 auto-fix。

旧页面默认“需要验证”，不是自动失效；若过时，显式标记 deprecated 或由用户决定删除。

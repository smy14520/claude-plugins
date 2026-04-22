---
url: https://github.com/mindfold-ai/Trellis/tree/main
source_type: github-repo
tool: GitHub API + DeepWiki
fetched_at: 2026-04-22 21:47
key_files_count: 7
---

# mindfold-ai/Trellis

## 仓库信息
- 描述: The best agent harness.
- 默认分支: main
- Stars: 5937
- 最近更新: 2026-04-22T13:27:52Z
- 主要语言: Python
- 仓库地址: https://github.com/mindfold-ai/Trellis
- 文件总数: 975

## 目录结构
```text
Trellis/
├── .agents
│   └── skills
│       ├── before-dev
│       │   └── SKILL.md
│       ├── brainstorm
│       │   └── SKILL.md
│       ├── break-loop
│       │   └── SKILL.md
│       ├── check
│       │   └── SKILL.md
│       ├── check-cross-layer
│       │   └── SKILL.md
│       ├── create-command
│       │   └── SKILL.md
│       ├── finish-work
│       │   └── SKILL.md
│       ├── improve-ut
│       │   └── SKILL.md
│       ├── integrate-skill
│       │   └── SKILL.md
│       ├── onboard
│       │   └── SKILL.md
│       ├── record-session
│       │   └── SKILL.md
│       ├── start
│       │   └── SKILL.md
│       └── update-spec
│           └── SKILL.md
├── .claude
│   ├── agents
│   │   ├── check.md
│   │   ├── debug.md
│   │   ├── dispatch.md
│   │   ├── implement.md
│   │   ├── plan.md
│   │   └── research.md
│   ├── commands
│   │   └── trellis
│   │       ├── before-dev.md
│   │       ├── brainstorm.md
│   │       ├── break-loop.md
│   │       ├── check-cross-layer.md
│   │       ├── check.md
│   │       ├── commit.md
│   │       ├── create-command.md
│   │       ├── create-manifest.md
│   │       ├── finish-work.md
│   │       ├── improve-ut.md
│   │       ├── integrate-skill.md
│   │       ├── onboard.md
│   │       ├── parallel.md
│   │       ├── publish-skill.md
│   │       ├── record-session.md
│   │       ├── start.md
│   │       └── update-spec.md
│   ├── hooks
│   │   ├── inject-subagent-context.py
│   │   ├── ralph-loop.py
│   │   ├── session-start.py
│   │   └── statusline.py
│   ├── skills
│   │   ├── contribute
│   │   │   └── SKILL.md
│   │   ├── first-principles-thinking
│   │   │   ├── references
│   │   │   │   ├── axiom-based-reasoning.md
│   │   │   │   ├── bias-and-debiasing.md
│   │   │   │   ├── case-studies.md
│   │   │   │   ├── decomposition-frameworks.md
│   │   │   │   └── thinking-models-toolkit.md
│   │   │   └── SKILL.md
│   │   ├── python-design
│   │   │   └── SKILL.md
│   │   └── trellis-meta
│   │       ├── references
│   │       │   ├── claude-code
│   │       │   │   ├── agents.md
│   │       │   │   ├── hooks.md
│   │       │   │   ├── multi-session.md
│   │       │   │   ├── overview.md
│   │       │   │   ├── ralph-loop.md
│   │       │   │   ├── scripts.md
│   │       │   │   └── worktree-config.md
│   │       │   ├── core
│   │       │   │   ├── files.md
│   │       │   │   ├── overview.md
│   │       │   │   ├── scripts.md
│   │       │   │   ├── specs.md
│   │       │   │   ├── tasks.md
│   │       │   │   └── workspace.md
│   │       │   ├── how-to-modify
│   │       │   │   ├── add-agent.md
│   │       │   │   ├── add-command.md
│   │       │   │   ├── add-phase.md
│   │       │   │   ├── add-spec.md
│   │       │   │   ├── change-verify.md
│   │       │   │   ├── modify-hook.md
│   │       │   │   └── overview.md
│   │       │   └── meta
│   │       │       ├── platform-compatibility.md
│   │       │       ├── self-iteration-guide.md
│   │       │       └── trellis-local-template.md
│   │       └── SKILL.md
│   └── settings.json
├── .codex
│   ├── agents
│   │   ├── check.toml
│   │   ├── implement.toml
│   │   └── research.toml
│   ├── hooks
│   │   └── session-start.py
│   ├── skills
│   │   └── parallel
│   │       └── SKILL.md
│   ├── config.toml
│   └── hooks.json
├── .cursor
│   └── commands
│       ├── trellis-before-dev.md
│       ├── trellis-brainstorm.md
│       ├── trellis-break-loop.md
│       ├── trellis-check-cross-layer.md
│       ├── trellis-check.md
│       ├── trellis-create-command.md
│       ├── trellis-create-manifest.md
│       ├── trellis-finish-work.md
│       ├── trellis-integrate-skill.md
│       ├── trellis-onboard.md
│       ├── trellis-publish-skill.md
│       ├── trellis-record-session.md
│       ├── trellis-start.md
│       └── trellis-update-spec.md
├── .github
│   ├── ISSUE_TEMPLATE
│   │   ├── bug_report.yml
│   │   ├── config.yml
│   │   ├── feature_request.yml
│   │   └── question.yml
│   └── workflows
│       ├── ci.yml
│       └── publish.yml
├── .husky
│   └── pre-commit
├── .opencode
│   ├── agents
│   │   ├── check.md
│   │   ├── debug.md
│   │   ├── dispatch.md
│   │   ├── implement.md
│   │   ├── research.md
│   │   └── trellis-plan.md
│   ├── commands
│   │   └── trellis
│   │       ├── before-dev.md
│   │       ├── break-loop.md
│   │       ├── check-cross-layer.md
│   │       ├── check.md
│   │       ├── create-command.md
│   │       ├── finish-work.md
│   │       ├── integrate-skill.md
│   │       ├── onboard.md
│   │       ├── parallel.md
│   │       ├── record-session.md
│   │       ├── start.md
│   │       └── update-spec.md
│   ├── lib
│   │   └── trellis-context.js
│   └── plugins
│       ├── inject-subagent-context.js
│       └── session-start.js
├── .trellis
│   ├── agents
│   │   ├── check.md
│   │   ├── implement.md
│   │   └── research.md
│   ├── scripts
│   │   ├── common
│   │   │   ├── __init__.py
│   │   │   ├── cli_adapter.py
│   │   │   ├── config.py
│   │   │   ├── developer.py
│   │   │   ├── git.py
│   │   │   ├── git_context.py
│   │   │   ├── io.py
│   │   │   ├── log.py
│   │   │   ├── packages_context.py
│   │   │   ├── paths.py
│   │   │   ├── phase.py
│   │   │   ├── registry.py
│   │   │   ├── session_context.py
│   │   │   ├── task_context.py
│   │   │   ├── task_queue.py
│   │   │   ├── task_store.py
│   │   │   ├── task_utils.py
│   │   │   ├── tasks.py
│   │   │   ├── types.py
│   │   │   └── worktree.py
│   │   ├── hooks
│   │   │   └── linear_sync.py
│   │   ├── multi_agent
│   │   │   ├── __init__.py
│   │   │   ├── _bootstrap.py
│   │   │   ├── cleanup.py
│   │   │   ├── create_pr.py
│   │   │   ├── plan.py
│   │   │   ├── start.py
│   │   │   ├── status.py
│   │   │   ├── status_display.py
│   │   │   └── status_monitor.py
│   │   ├── __init__.py
│   │   ├── add_session.py
│   │   ├── create_bootstrap.py
│   │   ├── get_context.py
│   │   ├── get_developer.py
│   │   ├── init_developer.py
│   │   └── task.py
│   ├── scripts-shell-archive
│   │   ├── common
│   │   │   ├── developer.sh
│   │   │   ├── git-context.sh
│   │   │   ├── paths.sh
│   │   │   ├── phase.sh
│   │   │   ├── registry.sh
│   │   │   ├── task-queue.sh
│   │   │   ├── task-utils.sh
│   │   │   └── worktree.sh
│   │   ├── multi-agent
│   │   │   ├── cleanup.sh
│   │   │   ├── create-pr.sh
│   │   │   ├── plan.sh
│   │   │   ├── start.sh
│   │   │   └── status.sh
│   │   ├── add-session.sh
│   │   ├── create-bootstrap.sh
│   │   ├── get-context.sh
│   │   ├── get-developer.sh
│   │   ├── init-developer.sh
│   │   └── task.sh
│   ├── spec
│   │   ├── cli
│   │   │   ├── backend
│   │   │   │   ├── directory-structure.md
│   │   │   │   ├── error-handling.md
│   │   │   │   ├── index.md
│   │   │   │   ├── logging-guidelines.md
│   │   │   │   ├── migrations.md
│   │   │   │   ├── platform-integration.md
│   │   │   │   ├── quality-guidelines.md
│   │   │   │   └── script-conventions.md
│   │   │   └── unit-test
│   │   │       ├── conventions.md
│   │   │       ├── index.md
│   │   │       ├── integration-patterns.md
│   │   │       └── mock-strategies.md
│   │   ├── docs-site
│   │   │   └── docs
│   │   │       ├── ascii-art-alignment.md
│   │   │       ├── config-guidelines.md
│   │   │       ├── directory-structure.md
│   │   │       ├── index.md
│   │   │       ├── mdx-guidelines.md
│   │   │       ├── plugin-guidelines.md
│   │   │       └── style-guide.md
│   │   └── guides
│   │       ├── code-reuse-thinking-guide.md
│   │       ├── cross-layer-thinking-guide.md
│   │       ├── cross-platform-thinking-guide.md
│   │       └── index.md
│   ├── tasks
│   │   ├── 03-10-skill-mono-migration
│   │   │   ├── prd.md
│   │   │   └── task.json
│   │   ├── 03-10-task-orchestrator
│   │   │   ├── prd.md
│   │   │   └── task.json
│   │   ├── 03-12-improve-thinking-workflow
│   │   │   ├── prd.md
│   │   │   └── task.json
│   │   ├── 03-26-frontend-fullchain-optimization-skill
│   │   │   ├── prd.md
│   │   │   └── task.json
│   │   └── archive
│   │       ├── 2026-01
│   │       │   ├── 01-00-bootstrap-guidelines-kleinhe
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   ├── 01-00-bootstrap-guidelines-taosu
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   ├── 01-15-devops-enhancements-kleinhe
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   ├── 01-15-marketing-readme-kleinhe
│   │       │   │   ├── prd.md
│   │       │   │   ├── readme-draft.md
│   │       │   │   ├── README-new.md
│   │       │   │   ├── research-readme-patterns.md
│   │       │   │   └── task.json
│   │       │   ├── 01-15-opencode-support-kleinhe
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   ├── 01-16-backend-guidelines-taosu
│   │       │   │   ├── check.jsonl
│   │       │   │   ├── debug.jsonl
│   │       │   │   ├── implement.jsonl
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   ├── 01-16-conversation-persistence-kleinhe
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   ├── 01-16-monorepo-support-kleinhe
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   ├── 01-16-parallel-sessions-kleinhe
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   ├── 01-16-worktree-isolation-kleinhe
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   ├── 01-16-worktree-support-taosu
│   │       │   │   ├── check.jsonl
│   │       │   │   ├── debug.jsonl
│   │       │   │   ├── implement.jsonl
│   │       │   │   └── task.json
│   │       │   ├── 01-17-backward-compat-kleinhe
│   │       │   │   ├── info.md
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   ├── 01-17-fix-template-dogfood-taosu
│   │       │   │   ├── check.jsonl
│   │       │   │   ├── debug.jsonl
│   │       │   │   ├── implement.jsonl
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   ├── 01-17-remove-txt-templates-taosu
│   │       │   │   ├── check.jsonl
│   │       │   │   ├── debug.jsonl
│   │       │   │   ├── implement.jsonl
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   ├── 01-18-restore-templates-taosu
│   │       │   │   └── task.json
│   │       │   ├── 01-19-readme-redesign-taosu
│   │       │   │   ├── bootstrap-skill
│   │       │   │   │   ├── install.sh
│   │       │   │   │   └── SKILL.md
│   │       │   │   ├── competitors
│   │       │   │   │   ├── 00-comparison-summary.md
│   │       │   │   │   ├── acontext.md
│   │       │   │   │   ├── aider.md
│   │       │   │   │   ├── bmad-method.md
│   │       │   │   │   ├── claude-code.md
│   │       │   │   │   ├── claude-cowork.md
│   │       │   │   │   ├── cline.md
│   │       │   │   │   ├── continue.md
│   │       │   │   │   ├── cursor.md
│   │       │   │   │   ├── github-copilot.md
│   │       │   │   │   ├── memu.md
│   │       │   │   │   ├── opencode.md
│   │       │   │   │   ├── openspec.md
│   │       │   │   │   ├── planning-with-files.md
│   │       │   │   │   ├── roo-code.md
│   │       │   │   │   ├── superpowers.md
│   │       │   │   │   └── windsurf.md
│   │       │   │   ├── version1
│   │       │   │   │   ├── DESIGN-NOTES.md
│   │       │   │   │   ├── README-zh.md
│   │       │   │   │   └── README.md
│   │       │   │   ├── version2
│   │       │   │   │   ├── DESIGN-NOTES.md
│   │       │   │   │   ├── README-zh.md
│   │       │   │   │   └── README.md
│   │       │   │   ├── version3
│   │       │   │   │   ├── DESIGN-NOTES.md
│   │       │   │   │   ├── README-zh.md
│   │       │   │   │   └── README.md
│   │       │   │   ├── check.jsonl
│   │       │   │   ├── debug.jsonl
│   │       │   │   ├── implement.jsonl
│   │       │   │   ├── prd.md
│   │       │   │   ├── research-summary.md
│   │       │   │   └── task.json
│   │       │   ├── 01-20-product-positioning-kleinhe
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   ├── 01-21-doc-collaboration-research-kleinhe
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   ├── 01-21-early-marketing-research-kleinhe
│   │       │   │   ├── 00-research-methodology.md
│   │       │   │   ├── 01-continue.md
│   │       │   │   ├── 02-opencode.md
│   │       │   │   ├── 03-superpowers.md
│   │       │   │   ├── 04-openspec.md
│   │       │   │   ├── 05-roo-code.md
│   │       │   │   ├── 06-claude-mem.md
│   │       │   │   ├── 99-summary.md
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   ├── 01-21-mkt-growth-guide-kleinhe
│   │       │   │   ├── daily-checklist.md
│   │       │   │   ├── prd.md
│   │       │   │   ├── task.json
│   │       │   │   └── timeline.md
│   │       │   ├── 01-21-superpower-research-kleinhe
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   ├── 01-21-update-improvements-kleinhe
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   ├── 01-21-update-mechanism-fixes-kleinhe
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   ├── 01-22-better-issue-recording
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   ├── 01-22-readme-visual-polish
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   ├── 01-22-review-naming-pr
│   │       │   │   └── task.json
│   │       │   ├── 01-22-trellis-agents-gui
│   │       │   │   ├── check.jsonl
│   │       │   │   ├── debug.jsonl
│   │       │   │   ├── implement.jsonl
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   ├── 01-22-trellis-agents-monorepo
│   │       │   │   ├── check.jsonl
│   │       │   │   ├── debug.jsonl
│   │       │   │   ├── implement.jsonl
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   ├── 01-25-session-resume-support
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   ├── 01-26-mintlify-docs
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   ├── 01-27-readme-enhancements
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   ├── 01-28-cli-tui-system
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   ├── 01-29-context-benchmark
│   │       │   │   ├── prd.md
│   │       │   │   ├── report.md
│   │       │   │   ├── task.json
│   │       │   │   └── workflow-context-map.md
│   │       │   └── 01-30-bash2py
│   │       │       ├── prd.md
│   │       │       └── task.json
│   │       ├── 2026-02
│   │       │   ├── 02-01-opencode-support
│   │       │   │   ├── check.jsonl
│   │       │   │   ├── debug.jsonl
│   │       │   │   ├── implement.jsonl
│   │       │   │   ├── prd.md
│   │       │   │   ├── task.json
│   │       │   │   └── task.md
│   │       │   ├── 02-03-template-init-test
│   │       │   │   ├── check.jsonl
│   │       │   │   ├── debug.jsonl
│   │       │   │   ├── implement.jsonl
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   ├── 02-04-fix-update-platform-selection
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   ├── 02-04-sync-iflow-pr22
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   ├── 02-05-cross-platform-python
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   ├── 02-05-improve-brainstorm-flow
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   ├── 02-05-remote-template-init
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   ├── 02-06-e2e-integration-tests
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   ├── 02-06-platform-registry-refactor
│   │       │   │   ├── check.jsonl
│   │       │   │   ├── debug.jsonl
│   │       │   │   ├── implement.jsonl
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   ├── 02-06-python-windows-testing
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   ├── 02-06-unit-test-platform-registry
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   ├── 02-09-codex-skills-template-init
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   ├── 02-26-gemini-cli-support
│   │       │   │   ├── check.jsonl
│   │       │   │   ├── debug.jsonl
│   │       │   │   ├── implement.jsonl
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   └── 02-28-migrate-to-0.3.0
│   │       │       ├── prd.md
│   │       │       └── task.json
│   │       ├── 2026-03
│   │       │   ├── 03-04-init-download-ux
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   ├── 03-04-record-session-task-awareness
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   ├── 03-04-support-trae-qoder
│   │       │   │   ├── check.jsonl
│   │       │   │   ├── debug.jsonl
│   │       │   │   ├── implement.jsonl
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   ├── 03-04-update-skip-spec
│   │       │   │   └── task.json
│   │       │   ├── 03-05-hooks-docs
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   ├── 03-05-remote-spec-templates
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   ├── 03-05-task-lifecycle-hooks
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   ├── 03-05-task-subtask
│   │       │   │   ├── check.jsonl
│   │       │   │   ├── debug.jsonl
│   │       │   │   ├── implement.jsonl
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   ├── 03-05-tmux-support
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   ├── 03-05-v036-update
│   │       │   │   └── task.json
│   │       │   ├── 03-06-hook-start-equiv
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   ├── 03-06-update-skip-dirs
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   ├── 03-06-v037
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   ├── 03-07-learn-openspec-prd
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   ├── 03-08-template-marketplace
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   ├── 03-09-extract-repo-level-content
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   ├── 03-09-monorepo-spec-adapt
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   ├── 03-09-monorepo-submodule
│   │       │   │   ├── check.jsonl
│   │       │   │   ├── debug.jsonl
│   │       │   │   ├── implement.jsonl
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   ├── 03-09-update-template-source
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   ├── 03-10-dogfood-monorepo-compat
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   ├── 03-10-merge-monorepo-branch
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   ├── 03-10-monorepo-compat
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   ├── 03-10-s1-infra
│   │       │   │   ├── check.jsonl
│   │       │   │   ├── debug.jsonl
│   │       │   │   ├── implement.jsonl
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   ├── 03-10-s2-commands
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   ├── 03-10-s3-task-update
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   ├── 03-10-s4-worktree
│   │       │   │   ├── check.jsonl
│   │       │   │   ├── debug.jsonl
│   │       │   │   ├── implement.jsonl
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   ├── 03-10-v040-beta1
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   ├── 03-11-improve-break-loop-update-spec
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   ├── 03-11-spec-path-dynamic
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   ├── 03-12-codex-review-fixes
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   ├── 03-12-refactor-python-scripts
│   │       │   │   ├── golden-tests
│   │       │   │   │   ├── add-session-help.exitcode
│   │       │   │   │   ├── add-session-help.stderr
│   │       │   │   │   ├── add-session-help.stdout
│   │       │   │   │   ├── packages.exitcode
│   │       │   │   │   ├── packages.stderr
│   │       │   │   │   ├── packages.stdout
│   │       │   │   │   ├── task-list.exitcode
│   │       │   │   │   ├── task-list.stderr
│   │       │   │   │   └── task-list.stdout
│   │       │   │   ├── check.jsonl
│   │       │   │   ├── debug.jsonl
│   │       │   │   ├── implement.jsonl
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   ├── 03-12-spec-sync-after-s1s4
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   ├── 03-12-yaml-quote-strip-bug
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   ├── 03-13-rename-empty-template
│   │       │   │   ├── check.jsonl
│   │       │   │   ├── debug.jsonl
│   │       │   │   ├── implement.jsonl
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   ├── 03-24-agents-dir-ownership
│   │       │   │   ├── check.jsonl
│   │       │   │   ├── debug.jsonl
│   │       │   │   ├── implement.jsonl
│   │       │   │   ├── prd.md
│   │       │   │   └── task.json
│   │       │   ├── 03-26-statusline-integration
│   │       │   │   └── task.json
│   │       │   └── 03-27-self-hosted-gitlab
│   │       │       ├── check.jsonl
│   │       │       ├── debug.jsonl
│   │       │       ├── implement.jsonl
│   │       │       ├── prd.md
│   │       │       └── task.json
│   │       └── 2026-04
│   │           └── 03-24-py39-compat
│   │               ├── prd.md
│   │               └── task.json
│   ├── workspace
│   │   ├── kleinhe
│   │   │   ├── index.md
│   │   │   └── journal-1.md
│   │   ├── taosu
│   │   │   ├── ai_smell_scan.py
│   │   │   ├── index.md
│   │   │   ├── journal-1.md
│   │   │   ├── journal-2.md
│   │   │   ├── journal-3.md
│   │   │   └── journal-4.md
│   │   └── index.md
│   ├── .gitignore
│   ├── .template-hashes.json
│   ├── .version
│   ├── config.yaml
│   ├── workflow.md
│   └── worktree.yaml
├── assets
│   ├── discord_wx_comment.jpg
│   ├── info.png
│   ├── linuxdo_comment.jpg
│   ├── meme.png
│   ├── meme_zh.png
│   ├── qq-group-qr.jpg
│   ├── trellis-demo-zh.gif
│   ├── trellis-demo.gif
│   ├── trellis.png
│   ├── usecase1.png
│   ├── usecase2.png
│   ├── usecase3.png
│   ├── wecom-group-qr.png
│   ├── workflow.png
│   ├── wx_link.jpg
│   ├── wx_link1.jpg
│   ├── wx_link2.jpg
│   ├── wx_link3.jpg
│   ├── wx_link4.jpg
│   └── wx_link5.jpg
├── packages
│   └── cli
│       ├── bin
│       │   └── trellis.js
│       ├── scripts
│       │   ├── copy-templates.js
│       │   ├── create-manifest.js
│       │   └── migrate-features-to-tasks.sh
│       ├── src
│       │   ├── cli
│       │   │   └── index.ts
│       │   ├── commands
│       │   │   ├── init.ts
│       │   │   └── update.ts
│       │   ├── configurators
│       │   │   ├── antigravity.ts
│       │   │   ├── claude.ts
│       │   │   ├── codebuddy.ts
│       │   │   ├── codex.ts
│       │   │   ├── copilot.ts
│       │   │   ├── cursor.ts
│       │   │   ├── droid.ts
│       │   │   ├── gemini.ts
│       │   │   ├── iflow.ts
│       │   │   ├── index.ts
│       │   │   ├── kilo.ts
│       │   │   ├── kiro.ts
│       │   │   ├── opencode.ts
│       │   │   ├── qoder.ts
│       │   │   ├── shared.ts
│       │   │   ├── windsurf.ts
│       │   │   └── workflow.ts
│       │   ├── constants
│       │   │   ├── paths.ts
│       │   │   └── version.ts
│       │   ├── migrations
│       │   │   ├── manifests
│       │   │   │   ├── 0.1.9.json
│       │   │   │   ├── 0.2.0.json
│       │   │   │   ├── 0.2.12.json
│       │   │   │   ├── 0.2.13.json
│       │   │   │   ├── 0.2.14.json
│       │   │   │   ├── 0.2.15.json
│       │   │   │   ├── 0.3.0-beta.0.json
│       │   │   │   ├── 0.3.0-beta.1.json
│       │   │   │   ├── 0.3.0-beta.10.json
│       │   │   │   ├── 0.3.0-beta.11.json
│       │   │   │   ├── 0.3.0-beta.12.json
│       │   │   │   ├── 0.3.0-beta.13.json
│       │   │   │   ├── 0.3.0-beta.14.json
│       │   │   │   ├── 0.3.0-beta.15.json
│       │   │   │   ├── 0.3.0-beta.16.json
│       │   │   │   ├── 0.3.0-beta.2.json
│       │   │   │   ├── 0.3.0-beta.3.json
│       │   │   │   ├── 0.3.0-beta.4.json
│       │   │   │   ├── 0.3.0-beta.5.json
│       │   │   │   ├── 0.3.0-beta.6.json
│       │   │   │   ├── 0.3.0-beta.7.json
│       │   │   │   ├── 0.3.0-beta.8.json
│       │   │   │   ├── 0.3.0-beta.9.json
│       │   │   │   ├── 0.3.0-rc.0.json
│       │   │   │   ├── 0.3.0-rc.1.json
│       │   │   │   ├── 0.3.0-rc.2.json
│       │   │   │   ├── 0.3.0-rc.3.json
│       │   │   │   ├── 0.3.0-rc.4.json
│       │   │   │   ├── 0.3.0-rc.5.json
│       │   │   │   ├── 0.3.0-rc.6.json
│       │   │   │   ├── 0.3.0.json
│       │   │   │   ├── 0.3.1.json
│       │   │   │   ├── 0.3.10.json
│       │   │   │   ├── 0.3.2.json
│       │   │   │   ├── 0.3.3.json
│       │   │   │   ├── 0.3.4.json
│       │   │   │   ├── 0.3.5.json
│       │   │   │   ├── 0.3.6.json
│       │   │   │   ├── 0.3.7.json
│       │   │   │   ├── 0.3.8.json
│       │   │   │   ├── 0.3.9.json
│       │   │   │   ├── 0.4.0-beta.1.json
│       │   │   │   ├── 0.4.0-beta.10.json
│       │   │   │   ├── 0.4.0-beta.2.json
│       │   │   │   ├── 0.4.0-beta.3.json
│       │   │   │   ├── 0.4.0-beta.4.json
│       │   │   │   ├── 0.4.0-beta.5.json
│       │   │   │   ├── 0.4.0-beta.6.json
│       │   │   │   ├── 0.4.0-beta.7.json
│       │   │   │   ├── 0.4.0-beta.8.json
│       │   │   │   ├── 0.4.0-beta.9.json
│       │   │   │   ├── 0.4.0-rc.0.json
│       │   │   │   ├── 0.4.0-rc.1.json
│       │   │   │   └── 0.4.0.json
│       │   │   └── index.ts
│       │   ├── templates
│       │   │   ├── antigravity
│       │   │   │   └── index.ts
│       │   │   ├── claude
│       │   │   │   ├── agents
│       │   │   │   │   ├── check.md
│       │   │   │   │   ├── debug.md
│       │   │   │   │   ├── dispatch.md
│       │   │   │   │   ├── implement.md
│       │   │   │   │   ├── plan.md
│       │   │   │   │   └── research.md
│       │   │   │   ├── commands
│       │   │   │   │   └── trellis
│       │   │   │   │       ├── before-dev.md
│       │   │   │   │       ├── brainstorm.md
│       │   │   │   │       ├── break-loop.md
│       │   │   │   │       ├── check-cross-layer.md
│       │   │   │   │       ├── check.md
│       │   │   │   │       ├── create-command.md
│       │   │   │   │       ├── finish-work.md
│       │   │   │   │       ├── integrate-skill.md
│       │   │   │   │       ├── onboard.md
│       │   │   │   │       ├── parallel.md
│       │   │   │   │       ├── record-session.md
│       │   │   │   │       ├── start.md
│       │   │   │   │       └── update-spec.md
│       │   │   │   ├── hooks
│       │   │   │   │   ├── inject-subagent-context.py
│       │   │   │   │   ├── ralph-loop.py
│       │   │   │   │   ├── session-start.py
│       │   │   │   │   └── statusline.py
│       │   │   │   ├── index.ts
│       │   │   │   └── settings.json
│       │   │   ├── codebuddy
│       │   │   │   ├── commands
│       │   │   │   │   └── trellis
│       │   │   │   │       ├── before-dev.md
│       │   │   │   │       ├── brainstorm.md
│       │   │   │   │       ├── break-loop.md
│       │   │   │   │       ├── check-cross-layer.md
│       │   │   │   │       ├── check.md
│       │   │   │   │       ├── create-command.md
│       │   │   │   │       ├── finish-work.md
│       │   │   │   │       ├── integrate-skill.md
│       │   │   │   │       ├── onboard.md
│       │   │   │   │       ├── record-session.md
│       │   │   │   │       ├── start.md
│       │   │   │   │       └── update-spec.md
│       │   │   │   └── index.ts
│       │   │   ├── codex
│       │   │   │   ├── agents
│       │   │   │   │   ├── check.toml
│       │   │   │   │   ├── implement.toml
│       │   │   │   │   └── research.toml
│       │   │   │   ├── codex-skills
│       │   │   │   │   └── parallel
│       │   │   │   │       └── SKILL.md
│       │   │   │   ├── hooks
│       │   │   │   │   └── session-start.py
│       │   │   │   ├── skills
│       │   │   │   │   ├── before-dev
│       │   │   │   │   │   └── SKILL.md
│       │   │   │   │   ├── brainstorm
│       │   │   │   │   │   └── SKILL.md
│       │   │   │   │   ├── break-loop
│       │   │   │   │   │   └── SKILL.md
│       │   │   │   │   ├── check
│       │   │   │   │   │   └── SKILL.md
│       │   │   │   │   ├── check-cross-layer
│       │   │   │   │   │   └── SKILL.md
│       │   │   │   │   ├── create-command
│       │   │   │   │   │   └── SKILL.md
│       │   │   │   │   ├── finish-work
│       │   │   │   │   │   └── SKILL.md
│       │   │   │   │   ├── improve-ut
│       │   │   │   │   │   └── SKILL.md
│       │   │   │   │   ├── integrate-skill
│       │   │   │   │   │   └── SKILL.md
│       │   │   │   │   ├── onboard
│       │   │   │   │   │   └── SKILL.md
│       │   │   │   │   ├── record-session
│       │   │   │   │   │   └── SKILL.md
│       │   │   │   │   ├── start
│       │   │   │   │   │   └── SKILL.md
│       │   │   │   │   └── update-spec
│       │   │   │   │       └── SKILL.md
│       │   │   │   ├── config.toml
│       │   │   │   ├── hooks.json
│       │   │   │   └── index.ts
│       │   │   ├── copilot
│       │   │   │   ├── hooks
│       │   │   │   │   └── session-start.py
│       │   │   │   ├── prompts
│       │   │   │   │   ├── before-dev.prompt.md
│       │   │   │   │   ├── brainstorm.prompt.md
│       │   │   │   │   ├── break-loop.prompt.md
│       │   │   │   │   ├── check-cross-layer.prompt.md
│       │   │   │   │   ├── check.prompt.md
│       │   │   │   │   ├── create-command.prompt.md
│       │   │   │   │   ├── finish-work.prompt.md
│       │   │   │   │   ├── integrate-skill.prompt.md
│       │   │   │   │   ├── onboard.prompt.md
│       │   │   │   │   ├── parallel.prompt.md
│       │   │   │   │   ├── record-session.prompt.md
│       │   │   │   │   ├── start.prompt.md
│       │   │   │   │   └── update-spec.prompt.md
│       │   │   │   ├── hooks.json
│       │   │   │   └── index.ts
│       │   │   ├── cursor
│       │   │   │   ├── commands
│       │   │   │   │   ├── trellis-before-dev.md
│       │   │   │   │   ├── trellis-brainstorm.md
│       │   │   │   │   ├── trellis-break-loop.md
│       │   │   │   │   ├── trellis-check-cross-layer.md
│       │   │   │   │   ├── trellis-check.md
│       │   │   │   │   ├── trellis-create-command.md
│       │   │   │   │   ├── trellis-finish-work.md
│       │   │   │   │   ├── trellis-integrate-skill.md
│       │   │   │   │   ├── trellis-onboard.md
│       │   │   │   │   ├── trellis-record-session.md
│       │   │   │   │   ├── trellis-start.md
│       │   │   │   │   └── trellis-update-spec.md
│       │   │   │   └── index.ts
│       │   │   ├── droid
│       │   │   │   ├── commands
│       │   │   │   │   └── trellis
│       │   │   │   │       ├── before-dev.md
│       │   │   │   │       ├── brainstorm.md
│       │   │   │   │       ├── break-loop.md
│       │   │   │   │       ├── check-cross-layer.md
│       │   │   │   │       ├── check.md
│       │   │   │   │       ├── create-command.md
│       │   │   │   │       ├── finish-work.md
│       │   │   │   │       ├── integrate-skill.md
│       │   │   │   │       ├── onboard.md
│       │   │   │   │       ├── record-session.md
│       │   │   │   │       ├── start.md
│       │   │   │   │       └── update-spec.md
│       │   │   │   └── index.ts
│       │   │   ├── gemini
│       │   │   │   ├── commands
│       │   │   │   │   └── trellis
│       │   │   │   │       ├── before-dev.toml
│       │   │   │   │       ├── brainstorm.toml
│       │   │   │   │       ├── break-loop.toml
│       │   │   │   │       ├── check-cross-layer.toml
│       │   │   │   │       ├── check.toml
│       │   │   │   │       ├── create-command.toml
│       │   │   │   │       ├── finish-work.toml
│       │   │   │   │       ├── integrate-skill.toml
│       │   │   │   │       ├── onboard.toml
│       │   │   │   │       ├── record-session.toml
│       │   │   │   │       ├── start.toml
│       │   │   │   │       └── update-spec.toml
│       │   │   │   └── index.ts
│       │   │   ├── iflow
│       │   │   │   ├── agents
│       │   │   │   │   ├── check.md
│       │   │   │   │   ├── debug.md
│       │   │   │   │   ├── dispatch.md
│       │   │   │   │   ├── implement.md
│       │   │   │   │   ├── plan.md
│       │   │   │   │   └── research.md
│       │   │   │   ├── commands
│       │   │   │   │   └── trellis
│       │   │   │   │       ├── before-dev.md
│       │   │   │   │       ├── brainstorm.md
│       │   │   │   │       ├── break-loop.md
│       │   │   │   │       ├── check-cross-layer.md
│       │   │   │   │       ├── check.md
│       │   │   │   │       ├── create-command.md
│       │   │   │   │       ├── finish-work.md
│       │   │   │   │       ├── integrate-skill.md
│       │   │   │   │       ├── onboard.md
│       │   │   │   │       ├── parallel.md
│       │   │   │   │       ├── record-session.md
│       │   │   │   │       ├── start.md
│       │   │   │   │       └── update-spec.md
│       │   │   │   ├── hooks
│       │   │   │   │   ├── inject-subagent-context.py
│       │   │   │   │   ├── ralph-loop.py
│       │   │   │   │   └── session-start.py
│       │   │   │   ├── index.ts
│       │   │   │   └── settings.json
│       │   │   ├── kilo
│       │   │   │   ├── workflows
│       │   │   │   │   ├── before-dev.md
│       │   │   │   │   ├── brainstorm.md
│       │   │   │   │   ├── break-loop.md
│       │   │   │   │   ├── check-cross-layer.md
│       │   │   │   │   ├── check.md
│       │   │   │   │   ├── create-command.md
│       │   │   │   │   ├── finish-work.md
│       │   │   │   │   ├── integrate-skill.md
│       │   │   │   │   ├── onboard.md
│       │   │   │   │   ├── parallel.md
│       │   │   │   │   ├── record-session.md
│       │   │   │   │   ├── start.md
│       │   │   │   │   └── update-spec.md
│       │   │   │   └── index.ts
│       │   │   ├── kiro
│       │   │   │   ├── skills
│       │   │   │   │   ├── before-dev
│       │   │   │   │   │   └── SKILL.md
│       │   │   │   │   ├── brainstorm
│       │   │   │   │   │   └── SKILL.md
│       │   │   │   │   ├── break-loop
│       │   │   │   │   │   └── SKILL.md
│       │   │   │   │   ├── check
│       │   │   │   │   │   └── SKILL.md
│       │   │   │   │   ├── check-cross-layer
│       │   │   │   │   │   └── SKILL.md
│       │   │   │   │   ├── create-command
│       │   │   │   │   │   └── SKILL.md
│       │   │   │   │   ├── finish-work
│       │   │   │   │   │   └── SKILL.md
│       │   │   │   │   ├── integrate-skill
│       │   │   │   │   │   └── SKILL.md
│       │   │   │   │   ├── onboard
│       │   │   │   │   │   └── SKILL.md
│       │   │   │   │   ├── record-session
│       │   │   │   │   │   └── SKILL.md
│       │   │   │   │   ├── start
│       │   │   │   │   │   └── SKILL.md
│       │   │   │   │   └── update-spec
│       │   │   │   │       └── SKILL.md
│       │   │   │   └── index.ts
│       │   │   ├── markdown
│       │   │   │   ├── spec
│       │   │   │   │   ├── backend
│       │   │   │   │   │   ├── database-guidelines.md.txt
│       │   │   │   │   │   ├── directory-structure.md
│       │   │   │   │   │   ├── directory-structure.md.txt
│       │   │   │   │   │   ├── error-handling.md.txt
│       │   │   │   │   │   ├── index.md
│       │   │   │   │   │   ├── index.md.txt
│       │   │   │   │   │   ├── logging-guidelines.md.txt
│       │   │   │   │   │   ├── quality-guidelines.md.txt
│       │   │   │   │   │   └── script-conventions.md
│       │   │   │   │   ├── frontend
│       │   │   │   │   │   ├── component-guidelines.md.txt
│       │   │   │   │   │   ├── directory-structure.md.txt
│       │   │   │   │   │   ├── hook-guidelines.md.txt
│       │   │   │   │   │   ├── index.md.txt
│       │   │   │   │   │   ├── quality-guidelines.md.txt
│       │   │   │   │   │   ├── state-management.md.txt
│       │   │   │   │   │   └── type-safety.md.txt
│       │   │   │   │   └── guides
│       │   │   │   │       ├── code-reuse-thinking-guide.md
│       │   │   │   │       ├── code-reuse-thinking-guide.md.txt
│       │   │   │   │       ├── cross-layer-thinking-guide.md.txt
│       │   │   │   │       ├── cross-platform-thinking-guide.md
│       │   │   │   │       ├── cross-platform-thinking-guide.md.txt
│       │   │   │   │       └── index.md.txt
│       │   │   │   ├── agents.md
│       │   │   │   ├── gitignore.txt
│       │   │   │   ├── index.ts
│       │   │   │   ├── workspace-index.md
│       │   │   │   └── worktree.yaml.txt
│       │   │   ├── opencode
│       │   │   │   ├── agents
│       │   │   │   │   ├── check.md
│       │   │   │   │   ├── debug.md
│       │   │   │   │   ├── dispatch.md
│       │   │   │   │   ├── implement.md
│       │   │   │   │   ├── research.md
│       │   │   │   │   └── trellis-plan.md
│       │   │   │   ├── commands
│       │   │   │   │   └── trellis
│       │   │   │   │       ├── before-dev.md
│       │   │   │   │       ├── brainstorm.md
│       │   │   │   │       ├── break-loop.md
│       │   │   │   │       ├── check-cross-layer.md
│       │   │   │   │       ├── check.md
│       │   │   │   │       ├── create-command.md
│       │   │   │   │       ├── finish-work.md
│       │   │   │   │       ├── integrate-skill.md
│       │   │   │   │       ├── migrate-specs.md
│       │   │   │   │       ├── onboard.md
│       │   │   │   │       ├── parallel.md
│       │   │   │   │       ├── record-session.md
│       │   │   │   │       ├── start.md
│       │   │   │   │       └── update-spec.md
│       │   │   │   ├── lib
│       │   │   │   │   └── trellis-context.js
│       │   │   │   ├── plugins
│       │   │   │   │   ├── inject-subagent-context.js
│       │   │   │   │   └── session-start.js
│       │   │   │   └── package.json
│       │   │   ├── qoder
│       │   │   │   ├── skills
│       │   │   │   │   ├── before-dev
│       │   │   │   │   │   └── SKILL.md
│       │   │   │   │   ├── brainstorm
│       │   │   │   │   │   └── SKILL.md
│       │   │   │   │   ├── break-loop
│       │   │   │   │   │   └── SKILL.md
│       │   │   │   │   ├── check
│       │   │   │   │   │   └── SKILL.md
│       │   │   │   │   ├── check-cross-layer
│       │   │   │   │   │   └── SKILL.md
│       │   │   │   │   ├── create-command
│       │   │   │   │   │   └── SKILL.md
│       │   │   │   │   ├── finish-work
│       │   │   │   │   │   └── SKILL.md
│       │   │   │   │   ├── integrate-skill
│       │   │   │   │   │   └── SKILL.md
│       │   │   │   │   ├── onboard
│       │   │   │   │   │   └── SKILL.md
│       │   │   │   │   ├── record-session
│       │   │   │   │   │   └── SKILL.md
│       │   │   │   │   ├── start
│       │   │   │   │   │   └── SKILL.md
│       │   │   │   │   └── update-spec
│       │   │   │   │       └── SKILL.md
│       │   │   │   └── index.ts
│       │   │   ├── trellis
│       │   │   │   ├── scripts
│       │   │   │   │   ├── common
│       │   │   │   │   │   ├── __init__.py
│       │   │   │   │   │   ├── cli_adapter.py
│       │   │   │   │   │   ├── config.py
│       │   │   │   │   │   ├── developer.py
│       │   │   │   │   │   ├── git.py
│       │   │   │   │   │   ├── git_context.py
│       │   │   │   │   │   ├── io.py
│       │   │   │   │   │   ├── log.py
│       │   │   │   │   │   ├── packages_context.py
│       │   │   │   │   │   ├── paths.py
│       │   │   │   │   │   ├── phase.py
│       │   │   │   │   │   ├── registry.py
│       │   │   │   │   │   ├── session_context.py
│       │   │   │   │   │   ├── task_context.py
│       │   │   │   │   │   ├── task_queue.py
│       │   │   │   │   │   ├── task_store.py
│       │   │   │   │   │   ├── task_utils.py
│       │   │   │   │   │   ├── tasks.py
│       │   │   │   │   │   ├── types.py
│       │   │   │   │   │   └── worktree.py
│       │   │   │   │   ├── hooks
│       │   │   │   │   │   └── linear_sync.py
│       │   │   │   │   ├── multi_agent
│       │   │   │   │   │   ├── __init__.py
│       │   │   │   │   │   ├── _bootstrap.py
│       │   │   │   │   │   ├── cleanup.py
│       │   │   │   │   │   ├── create_pr.py
│       │   │   │   │   │   ├── plan.py
│       │   │   │   │   │   ├── start.py
│       │   │   │   │   │   ├── status.py
│       │   │   │   │   │   ├── status_display.py
│       │   │   │   │   │   └── status_monitor.py
│       │   │   │   │   ├── __init__.py
│       │   │   │   │   ├── add_session.py
│       │   │   │   │   ├── create_bootstrap.py
│       │   │   │   │   ├── get_context.py
│       │   │   │   │   ├── get_developer.py
│       │   │   │   │   ├── init_developer.py
│       │   │   │   │   └── task.py
│       │   │   │   ├── scripts-shell-archive
│       │   │   │   │   ├── common
│       │   │   │   │   │   ├── developer.sh
│       │   │   │   │   │   ├── git-context.sh
│       │   │   │   │   │   ├── paths.sh
│       │   │   │   │   │   ├── phase.sh
│       │   │   │   │   │   ├── registry.sh
│       │   │   │   │   │   ├── task-queue.sh
│       │   │   │   │   │   ├── task-utils.sh
│       │   │   │   │   │   └── worktree.sh
│       │   │   │   │   ├── multi-agent
│       │   │   │   │   │   ├── cleanup.sh
│       │   │   │   │   │   ├── create-pr.sh
│       │   │   │   │   │   ├── plan.sh
│       │   │   │   │   │   ├── start.sh
│       │   │   │   │   │   └── status.sh
│       │   │   │   │   ├── add-session.sh
│       │   │   │   │   ├── create-bootstrap.sh
│       │   │   │   │   ├── get-context.sh
│       │   │   │   │   ├── get-developer.sh
│       │   │   │   │   ├── init-developer.sh
│       │   │   │   │   └── task.sh
│       │   │   │   ├── tasks
│       │   │   │   │   └── .gitkeep
│       │   │   │   ├── config.yaml
│       │   │   │   ├── gitignore.txt
│       │   │   │   ├── index.ts
│       │   │   │   ├── workflow.md
│       │   │   │   └── worktree.yaml
│       │   │   ├── windsurf
│       │   │   │   ├── workflows
│       │   │   │   │   ├── trellis-before-dev.md
│       │   │   │   │   ├── trellis-brainstorm.md
│       │   │   │   │   ├── trellis-break-loop.md
│       │   │   │   │   ├── trellis-check-cross-layer.md
│       │   │   │   │   ├── trellis-check.md
│       │   │   │   │   ├── trellis-create-command.md
│       │   │   │   │   ├── trellis-finish-work.md
│       │   │   │   │   ├── trellis-integrate-skill.md
│       │   │   │   │   ├── trellis-onboard.md
│       │   │   │   │   ├── trellis-record-session.md
│       │   │   │   │   ├── trellis-start.md
│       │   │   │   │   └── trellis-update-spec.md
│       │   │   │   └── index.ts
│       │   │   └── extract.ts
│       │   ├── types
│       │   │   ├── ai-tools.ts
│       │   │   └── migration.ts
│       │   ├── utils
│       │   │   ├── compare-versions.ts
│       │   │   ├── file-writer.ts
│       │   │   ├── project-detector.ts
│       │   │   ├── proxy.ts
│       │   │   ├── template-fetcher.ts
│       │   │   └── template-hash.ts
│       │   └── index.ts
│       ├── test
│       │   ├── commands
│       │   │   ├── init.integration.test.ts
│       │   │   ├── update-internals.test.ts
│       │   │   └── update.integration.test.ts
│       │   ├── configurators
│       │   │   ├── index.test.ts
│       │   │   └── platforms.test.ts
│       │   ├── constants
│       │   │   └── paths.test.ts
│       │   ├── migrations
│       │   │   └── index.test.ts
│       │   ├── templates
│       │   │   ├── antigravity.test.ts
│       │   │   ├── claude.test.ts
│       │   │   ├── codebuddy.test.ts
│       │   │   ├── codex.test.ts
│       │   │   ├── copilot.test.ts
│       │   │   ├── cursor.test.ts
│       │   │   ├── droid.test.ts
│       │   │   ├── extract.test.ts
│       │   │   ├── gemini.test.ts
│       │   │   ├── iflow.test.ts
│       │   │   ├── kilo.test.ts
│       │   │   ├── kiro.test.ts
│       │   │   ├── opencode.test.ts
│       │   │   ├── qoder.test.ts
│       │   │   ├── trellis.test.ts
│       │   │   └── windsurf.test.ts
│       │   ├── types
│       │   │   └── ai-tools.test.ts
│       │   ├── utils
│       │   │   ├── file-writer.test.ts
│       │   │   ├── project-detector.test.ts
│       │   │   ├── template-fetcher.test.ts
│       │   │   └── template-hash.test.ts
│       │   ├── registry-invariants.test.ts
│       │   └── regression.test.ts
│       ├── .npmrc
│       ├── .prettierignore
│       ├── .prettierrc
│       ├── eslint.config.js
│       ├── package.json
│       ├── tsconfig.json
│       └── vitest.config.ts
├── .gitignore
├── .gitmodules
├── .lintstagedrc
├── AGENTS.md
├── CONTRIBUTING.md
├── CONTRIBUTING_CN.md
├── COPYRIGHT
├── LICENSE
├── package.json
├── pnpm-lock.yaml
├── pnpm-workspace.yaml
├── pyrightconfig.json
├── README.md
└── README_CN.md
```

## 关键文件清单
- `README.md` → `README.md.md` (192 lines)
- `.trellis/workflow.md` → `trellis-workflow.md.md` (405 lines)
- `.trellis/spec/cli/backend/index.md` → `trellis-spec-cli-backend-index.md.md` (58 lines)
- `.trellis/spec/guides/index.md` → `trellis-spec-guides-index.md.md` (103 lines)
- `.trellis/scripts/get_context.py` → `trellis-scripts-get_context.py.md` (16 lines)
- `.trellis/scripts/task.py` → `trellis-scripts-task.py.md` (445 lines)
- `.claude/hooks/session-start.py` → `claude-hooks-session-start.py.md` (414 lines)

## 其余文件
- `.agents/skills/before-dev/SKILL.md` (1571 bytes)
- `.agents/skills/brainstorm/SKILL.md` (12836 bytes)
- `.agents/skills/break-loop/SKILL.md` (4928 bytes)
- `.agents/skills/check-cross-layer/SKILL.md` (5102 bytes)
- `.agents/skills/check/SKILL.md` (1273 bytes)
- `.agents/skills/create-command/SKILL.md` (2505 bytes)
- `.agents/skills/finish-work/SKILL.md` (4241 bytes)
- `.agents/skills/improve-ut/SKILL.md` (1732 bytes)
- `.agents/skills/integrate-skill/SKILL.md` (6250 bytes)
- `.agents/skills/onboard/SKILL.md` (14779 bytes)
- `.agents/skills/record-session/SKILL.md` (2686 bytes)
- `.agents/skills/start/SKILL.md` (9997 bytes)
- `.agents/skills/update-spec/SKILL.md` (9928 bytes)
- `.claude/agents/check.md` (2833 bytes)
- `.claude/agents/debug.md` (1935 bytes)
- `.claude/agents/dispatch.md` (5228 bytes)
- `.claude/agents/implement.md` (2174 bytes)
- `.claude/agents/plan.md` (10266 bytes)
- `.claude/agents/research.md` (2470 bytes)
- `.claude/commands/trellis/before-dev.md` (1171 bytes)
- `.claude/commands/trellis/brainstorm.md` (12632 bytes)
- `.claude/commands/trellis/break-loop.md` (4467 bytes)
- `.claude/commands/trellis/check-cross-layer.md` (4648 bytes)
- `.claude/commands/trellis/check.md` (871 bytes)
- `.claude/commands/trellis/commit.md` (3144 bytes)
- `.claude/commands/trellis/create-command.md` (3290 bytes)
- `.claude/commands/trellis/create-manifest.md` (3105 bytes)
- `.claude/commands/trellis/finish-work.md` (4389 bytes)
- `.claude/commands/trellis/improve-ut.md` (1253 bytes)
- `.claude/commands/trellis/integrate-skill.md` (5875 bytes)
- `.claude/commands/trellis/onboard.md` (14776 bytes)
- `.claude/commands/trellis/parallel.md` (5270 bytes)
- `.claude/commands/trellis/publish-skill.md` (3244 bytes)
- `.claude/commands/trellis/record-session.md` (2042 bytes)
- `.claude/commands/trellis/start.md` (10298 bytes)
- `.claude/commands/trellis/update-spec.md` (10084 bytes)
- `.claude/hooks/inject-subagent-context.py` (25915 bytes)
- `.claude/hooks/ralph-loop.py` (13313 bytes)
- `.claude/hooks/statusline.py` (6575 bytes)
- `.claude/settings.json` (1565 bytes)
- `.claude/skills/contribute/SKILL.md` (11136 bytes)
- `.claude/skills/first-principles-thinking/SKILL.md` (16612 bytes)
- `.claude/skills/first-principles-thinking/references/axiom-based-reasoning.md` (26015 bytes)
- `.claude/skills/first-principles-thinking/references/bias-and-debiasing.md` (11488 bytes)
- `.claude/skills/first-principles-thinking/references/case-studies.md` (23037 bytes)
- `.claude/skills/first-principles-thinking/references/decomposition-frameworks.md` (11427 bytes)
- `.claude/skills/first-principles-thinking/references/thinking-models-toolkit.md` (13597 bytes)
- `.claude/skills/python-design/SKILL.md` (16169 bytes)
- `.claude/skills/trellis-meta/SKILL.md` (16260 bytes)
- `.claude/skills/trellis-meta/references/claude-code/agents.md` (8926 bytes)
- `.claude/skills/trellis-meta/references/claude-code/hooks.md` (5730 bytes)
- `.claude/skills/trellis-meta/references/claude-code/multi-session.md` (13676 bytes)
- `.claude/skills/trellis-meta/references/claude-code/overview.md` (5207 bytes)
- `.claude/skills/trellis-meta/references/claude-code/ralph-loop.md` (6947 bytes)
- `.claude/skills/trellis-meta/references/claude-code/scripts.md` (5807 bytes)
- `.claude/skills/trellis-meta/references/claude-code/worktree-config.md` (8527 bytes)
- `.claude/skills/trellis-meta/references/core/files.md` (6613 bytes)
- `.claude/skills/trellis-meta/references/core/overview.md` (2590 bytes)
- `.claude/skills/trellis-meta/references/core/scripts.md` (4867 bytes)
- `.claude/skills/trellis-meta/references/core/specs.md` (3990 bytes)
- `.claude/skills/trellis-meta/references/core/tasks.md` (7651 bytes)
- `.claude/skills/trellis-meta/references/core/workspace.md` (2840 bytes)
- `.claude/skills/trellis-meta/references/how-to-modify/add-agent.md` (4491 bytes)
- `.claude/skills/trellis-meta/references/how-to-modify/add-command.md` (2275 bytes)
- `.claude/skills/trellis-meta/references/how-to-modify/add-phase.md` (4195 bytes)
- `.claude/skills/trellis-meta/references/how-to-modify/add-spec.md` (3378 bytes)
- `.claude/skills/trellis-meta/references/how-to-modify/change-verify.md` (2447 bytes)
- `.claude/skills/trellis-meta/references/how-to-modify/modify-hook.md` (5007 bytes)
- `.claude/skills/trellis-meta/references/how-to-modify/overview.md` (5695 bytes)
- `.claude/skills/trellis-meta/references/meta/platform-compatibility.md` (10000 bytes)
- `.claude/skills/trellis-meta/references/meta/self-iteration-guide.md` (6753 bytes)
- `.claude/skills/trellis-meta/references/meta/trellis-local-template.md` (5863 bytes)
- `.codex/agents/check.toml` (732 bytes)
- `.codex/agents/implement.toml` (733 bytes)
- `.codex/agents/research.toml` (686 bytes)
- `.codex/config.toml` (238 bytes)
- `.codex/hooks.json` (298 bytes)
- `.codex/hooks/session-start.py` (8154 bytes)
- `.codex/skills/parallel/SKILL.md` (5526 bytes)
- `.cursor/commands/trellis-before-dev.md` (826 bytes)
- `.cursor/commands/trellis-brainstorm.md` (12632 bytes)
- `.cursor/commands/trellis-break-loop.md` (3680 bytes)
- `.cursor/commands/trellis-check-cross-layer.md` (4648 bytes)
- `.cursor/commands/trellis-check.md` (689 bytes)
- `.cursor/commands/trellis-create-command.md` (3290 bytes)
- `.cursor/commands/trellis-create-manifest.md` (2316 bytes)
- `.cursor/commands/trellis-finish-work.md` (3914 bytes)
- `.cursor/commands/trellis-integrate-skill.md` (5875 bytes)
- `.cursor/commands/trellis-onboard.md` (14774 bytes)
- `.cursor/commands/trellis-publish-skill.md` (3244 bytes)
- `.cursor/commands/trellis-record-session.md` (2076 bytes)
- `.cursor/commands/trellis-start.md` (9282 bytes)
- `.cursor/commands/trellis-update-spec.md` (10084 bytes)
- `.github/ISSUE_TEMPLATE/bug_report.yml` (852 bytes)
- `.github/ISSUE_TEMPLATE/config.yml` (194 bytes)
- `.github/ISSUE_TEMPLATE/feature_request.yml` (588 bytes)
- `.github/ISSUE_TEMPLATE/question.yml` (413 bytes)
- `.github/workflows/ci.yml` (917 bytes)
- `.github/workflows/publish.yml` (1535 bytes)
- `.gitignore` (2839 bytes)
- `.gitmodules` (189 bytes)
- `.husky/pre-commit` (17 bytes)
- `.lintstagedrc` (149 bytes)
- `.opencode/agents/check.md` (3464 bytes)
- `.opencode/agents/debug.md` (2519 bytes)
- `.opencode/agents/dispatch.md` (5720 bytes)
- `.opencode/agents/implement.md` (2791 bytes)
- `.opencode/agents/research.md` (3182 bytes)
- `.opencode/agents/trellis-plan.md` (11072 bytes)
- `.opencode/commands/trellis/before-dev.md` (826 bytes)
- `.opencode/commands/trellis/break-loop.md` (4463 bytes)
- `.opencode/commands/trellis/check-cross-layer.md` (4648 bytes)
- `.opencode/commands/trellis/check.md` (689 bytes)
- `.opencode/commands/trellis/create-command.md` (3296 bytes)
- `.opencode/commands/trellis/finish-work.md` (3223 bytes)
- `.opencode/commands/trellis/integrate-skill.md` (5847 bytes)
- `.opencode/commands/trellis/onboard.md` (14772 bytes)
- `.opencode/commands/trellis/parallel.md` (5359 bytes)
- `.opencode/commands/trellis/record-session.md` (1822 bytes)
- `.opencode/commands/trellis/start.md` (6953 bytes)
- `.opencode/commands/trellis/update-spec.md` (8177 bytes)
- `.opencode/lib/trellis-context.js` (13070 bytes)
- `.opencode/plugins/inject-subagent-context.js` (15504 bytes)
- `.opencode/plugins/session-start.js` (6588 bytes)
- `.trellis/.gitignore` (412 bytes)
- `.trellis/.template-hashes.json` (8579 bytes)
- `.trellis/.version` (5 bytes)
- `.trellis/agents/check.md` (1234 bytes)
- `.trellis/agents/implement.md` (935 bytes)
- `.trellis/agents/research.md` (10159 bytes)
- `.trellis/config.yaml` (2282 bytes)
- `.trellis/scripts-shell-archive/add-session.sh` (10067 bytes)
- `.trellis/scripts-shell-archive/common/developer.sh` (3042 bytes)
- `.trellis/scripts-shell-archive/common/git-context.sh` (7991 bytes)
- `.trellis/scripts-shell-archive/common/paths.sh` (5658 bytes)
- `.trellis/scripts-shell-archive/common/phase.sh` (3989 bytes)
- `.trellis/scripts-shell-archive/common/registry.sh` (6671 bytes)
- `.trellis/scripts-shell-archive/common/task-queue.sh` (4007 bytes)
- `.trellis/scripts-shell-archive/common/task-utils.sh` (4398 bytes)
- `.trellis/scripts-shell-archive/common/worktree.sh` (3839 bytes)
- `.trellis/scripts-shell-archive/create-bootstrap.sh` (7889 bytes)
- `.trellis/scripts-shell-archive/get-context.sh` (237 bytes)
- `.trellis/scripts-shell-archive/get-developer.sh` (321 bytes)
- `.trellis/scripts-shell-archive/init-developer.sh` (754 bytes)
- `.trellis/scripts-shell-archive/multi-agent/cleanup.sh` (11226 bytes)
- `.trellis/scripts-shell-archive/multi-agent/create-pr.sh` (7204 bytes)
- `.trellis/scripts-shell-archive/multi-agent/plan.sh` (5955 bytes)
- `.trellis/scripts-shell-archive/multi-agent/start.sh` (10341 bytes)
- `.trellis/scripts-shell-archive/multi-agent/status.sh` (24096 bytes)
- `.trellis/scripts-shell-archive/task.sh` (35078 bytes)
- `.trellis/scripts/__init__.py` (105 bytes)
- `.trellis/scripts/add_session.py` (16808 bytes)
- `.trellis/scripts/common/__init__.py` (2631 bytes)
- `.trellis/scripts/common/cli_adapter.py` (25591 bytes)
- `.trellis/scripts/common/config.py` (7923 bytes)
- `.trellis/scripts/common/developer.py` (5164 bytes)
- `.trellis/scripts/common/git.py` (893 bytes)
- `.trellis/scripts/common/git_context.py` (2008 bytes)
- `.trellis/scripts/common/io.py` (909 bytes)
- `.trellis/scripts/common/log.py` (1119 bytes)
- `.trellis/scripts/common/packages_context.py` (7868 bytes)
- `.trellis/scripts/common/paths.py` (12479 bytes)
- `.trellis/scripts/common/phase.py` (6873 bytes)
- `.trellis/scripts/common/registry.py` (8851 bytes)
- `.trellis/scripts/common/session_context.py` (18219 bytes)
- `.trellis/scripts/common/task_context.py` (14281 bytes)
- `.trellis/scripts/common/task_queue.py` (5009 bytes)
- `.trellis/scripts/common/task_store.py` (18798 bytes)
- `.trellis/scripts/common/task_utils.py` (8645 bytes)
- `.trellis/scripts/common/tasks.py` (2941 bytes)
- `.trellis/scripts/common/types.py` (3002 bytes)
- `.trellis/scripts/common/worktree.py` (8922 bytes)
- `.trellis/scripts/create_bootstrap.py` (9354 bytes)
- `.trellis/scripts/get_developer.py` (446 bytes)
- `.trellis/scripts/hooks/linear_sync.py` (7680 bytes)
- `.trellis/scripts/init_developer.py` (1055 bytes)
- `.trellis/scripts/multi_agent/__init__.py` (101 bytes)
- `.trellis/scripts/multi_agent/_bootstrap.py` (493 bytes)
- `.trellis/scripts/multi_agent/cleanup.py` (12468 bytes)
- `.trellis/scripts/multi_agent/create_pr.py` (20825 bytes)
- `.trellis/scripts/multi_agent/plan.py` (6895 bytes)
- `.trellis/scripts/multi_agent/start.py` (19461 bytes)
- `.trellis/scripts/multi_agent/status.py` (2579 bytes)
- `.trellis/scripts/multi_agent/status_display.py` (18110 bytes)
- `.trellis/scripts/multi_agent/status_monitor.py` (8156 bytes)
- `.trellis/spec/cli/backend/directory-structure.md` (15337 bytes)
- `.trellis/spec/cli/backend/error-handling.md` (10844 bytes)
- `.trellis/spec/cli/backend/logging-guidelines.md` (7073 bytes)
- `.trellis/spec/cli/backend/migrations.md` (4587 bytes)
- `.trellis/spec/cli/backend/platform-integration.md` (31617 bytes)
- `.trellis/spec/cli/backend/quality-guidelines.md` (15407 bytes)
- `.trellis/spec/cli/backend/script-conventions.md` (29942 bytes)
- `.trellis/spec/cli/unit-test/conventions.md` (11608 bytes)
- `.trellis/spec/cli/unit-test/index.md` (2647 bytes)
- `.trellis/spec/cli/unit-test/integration-patterns.md` (5006 bytes)
- `.trellis/spec/cli/unit-test/mock-strategies.md` (4091 bytes)
- `.trellis/spec/docs-site/docs/ascii-art-alignment.md` (5902 bytes)
- `.trellis/spec/docs-site/docs/config-guidelines.md` (9296 bytes)
- `.trellis/spec/docs-site/docs/directory-structure.md` (6305 bytes)
- `.trellis/spec/docs-site/docs/index.md` (2038 bytes)
- `.trellis/spec/docs-site/docs/mdx-guidelines.md` (4964 bytes)
- `.trellis/spec/docs-site/docs/plugin-guidelines.md` (6744 bytes)
- `.trellis/spec/docs-site/docs/style-guide.md` (4434 bytes)
- `.trellis/spec/guides/code-reuse-thinking-guide.md` (5803 bytes)
- `.trellis/spec/guides/cross-layer-thinking-guide.md` (4690 bytes)
- `.trellis/spec/guides/cross-platform-thinking-guide.md` (11466 bytes)
- `.trellis/tasks/03-10-skill-mono-migration/prd.md` (1168 bytes)
- `.trellis/tasks/03-10-skill-mono-migration/task.json` (889 bytes)
- `.trellis/tasks/03-10-task-orchestrator/prd.md` (22647 bytes)
- `.trellis/tasks/03-10-task-orchestrator/task.json` (1695 bytes)
- `.trellis/tasks/03-12-improve-thinking-workflow/prd.md` (2467 bytes)
- `.trellis/tasks/03-12-improve-thinking-workflow/task.json` (897 bytes)
- `.trellis/tasks/03-26-frontend-fullchain-optimization-skill/prd.md` (1632 bytes)
- `.trellis/tasks/03-26-frontend-fullchain-optimization-skill/task.json` (916 bytes)
- `.trellis/tasks/archive/2026-01/01-00-bootstrap-guidelines-kleinhe/prd.md` (3210 bytes)
- `.trellis/tasks/archive/2026-01/01-00-bootstrap-guidelines-kleinhe/task.json` (976 bytes)
- `.trellis/tasks/archive/2026-01/01-00-bootstrap-guidelines-taosu/prd.md` (3210 bytes)
- `.trellis/tasks/archive/2026-01/01-00-bootstrap-guidelines-taosu/task.json` (972 bytes)
- `.trellis/tasks/archive/2026-01/01-15-devops-enhancements-kleinhe/prd.md` (1740 bytes)
- `.trellis/tasks/archive/2026-01/01-15-devops-enhancements-kleinhe/task.json` (743 bytes)
- `.trellis/tasks/archive/2026-01/01-15-marketing-readme-kleinhe/README-new.md` (4935 bytes)
- `.trellis/tasks/archive/2026-01/01-15-marketing-readme-kleinhe/prd.md` (3343 bytes)
- `.trellis/tasks/archive/2026-01/01-15-marketing-readme-kleinhe/readme-draft.md` (4271 bytes)
- `.trellis/tasks/archive/2026-01/01-15-marketing-readme-kleinhe/research-readme-patterns.md` (18602 bytes)
- `.trellis/tasks/archive/2026-01/01-15-marketing-readme-kleinhe/task.json` (734 bytes)
- `.trellis/tasks/archive/2026-01/01-15-opencode-support-kleinhe/prd.md` (10729 bytes)
- `.trellis/tasks/archive/2026-01/01-15-opencode-support-kleinhe/task.json` (734 bytes)
- `.trellis/tasks/archive/2026-01/01-16-backend-guidelines-taosu/check.jsonl` (400 bytes)
- `.trellis/tasks/archive/2026-01/01-16-backend-guidelines-taosu/debug.jsonl` (290 bytes)
- `.trellis/tasks/archive/2026-01/01-16-backend-guidelines-taosu/implement.jsonl` (608 bytes)
- `.trellis/tasks/archive/2026-01/01-16-backend-guidelines-taosu/prd.md` (3324 bytes)
- `.trellis/tasks/archive/2026-01/01-16-backend-guidelines-taosu/task.json` (766 bytes)
- `.trellis/tasks/archive/2026-01/01-16-conversation-persistence-kleinhe/prd.md` (1030 bytes)
- `.trellis/tasks/archive/2026-01/01-16-conversation-persistence-kleinhe/task.json` (758 bytes)
- `.trellis/tasks/archive/2026-01/01-16-monorepo-support-kleinhe/prd.md` (979 bytes)
- `.trellis/tasks/archive/2026-01/01-16-monorepo-support-kleinhe/task.json` (734 bytes)
- `.trellis/tasks/archive/2026-01/01-16-parallel-sessions-kleinhe/prd.md` (1079 bytes)
- `.trellis/tasks/archive/2026-01/01-16-parallel-sessions-kleinhe/task.json` (633 bytes)
- `.trellis/tasks/archive/2026-01/01-16-worktree-isolation-kleinhe/prd.md` (1051 bytes)
- `.trellis/tasks/archive/2026-01/01-16-worktree-isolation-kleinhe/task.json` (636 bytes)
- `.trellis/tasks/archive/2026-01/01-16-worktree-support-taosu/check.jsonl` (321 bytes)
- `.trellis/tasks/archive/2026-01/01-16-worktree-support-taosu/debug.jsonl` (242 bytes)
- `.trellis/tasks/archive/2026-01/01-16-worktree-support-taosu/implement.jsonl` (606 bytes)
- `.trellis/tasks/archive/2026-01/01-16-worktree-support-taosu/task.json` (646 bytes)
- `.trellis/tasks/archive/2026-01/01-17-backward-compat-kleinhe/info.md` (9889 bytes)
- `.trellis/tasks/archive/2026-01/01-17-backward-compat-kleinhe/prd.md` (8450 bytes)
- `.trellis/tasks/archive/2026-01/01-17-backward-compat-kleinhe/task.json` (700 bytes)
- `.trellis/tasks/archive/2026-01/01-17-fix-template-dogfood-taosu/check.jsonl` (241 bytes)
- `.trellis/tasks/archive/2026-01/01-17-fix-template-dogfood-taosu/debug.jsonl` (162 bytes)
- `.trellis/tasks/archive/2026-01/01-17-fix-template-dogfood-taosu/implement.jsonl` (428 bytes)
- `.trellis/tasks/archive/2026-01/01-17-fix-template-dogfood-taosu/prd.md` (2633 bytes)
- `.trellis/tasks/archive/2026-01/01-17-fix-template-dogfood-taosu/task.json` (770 bytes)
- `.trellis/tasks/archive/2026-01/01-17-remove-txt-templates-taosu/check.jsonl` (519 bytes)
- `.trellis/tasks/archive/2026-01/01-17-remove-txt-templates-taosu/debug.jsonl` (443 bytes)
- `.trellis/tasks/archive/2026-01/01-17-remove-txt-templates-taosu/implement.jsonl` (909 bytes)
- `.trellis/tasks/archive/2026-01/01-17-remove-txt-templates-taosu/prd.md` (3523 bytes)
- `.trellis/tasks/archive/2026-01/01-17-remove-txt-templates-taosu/task.json` (773 bytes)
- `.trellis/tasks/archive/2026-01/01-18-restore-templates-taosu/task.json` (629 bytes)
- `.trellis/tasks/archive/2026-01/01-19-readme-redesign-taosu/bootstrap-skill/SKILL.md` (3273 bytes)
- `.trellis/tasks/archive/2026-01/01-19-readme-redesign-taosu/bootstrap-skill/install.sh` (2280 bytes)
- `.trellis/tasks/archive/2026-01/01-19-readme-redesign-taosu/check.jsonl` (243 bytes)
- `.trellis/tasks/archive/2026-01/01-19-readme-redesign-taosu/competitors/00-comparison-summary.md` (8597 bytes)
- `.trellis/tasks/archive/2026-01/01-19-readme-redesign-taosu/competitors/acontext.md` (4584 bytes)
- `.trellis/tasks/archive/2026-01/01-19-readme-redesign-taosu/competitors/aider.md` (10291 bytes)
- `.trellis/tasks/archive/2026-01/01-19-readme-redesign-taosu/competitors/bmad-method.md` (7495 bytes)
- `.trellis/tasks/archive/2026-01/01-19-readme-redesign-taosu/competitors/claude-code.md` (7045 bytes)
- `.trellis/tasks/archive/2026-01/01-19-readme-redesign-taosu/competitors/claude-cowork.md` (4695 bytes)
- `.trellis/tasks/archive/2026-01/01-19-readme-redesign-taosu/competitors/cline.md` (14055 bytes)
- `.trellis/tasks/archive/2026-01/01-19-readme-redesign-taosu/competitors/continue.md` (6034 bytes)
- `.trellis/tasks/archive/2026-01/01-19-readme-redesign-taosu/competitors/cursor.md` (4879 bytes)
- `.trellis/tasks/archive/2026-01/01-19-readme-redesign-taosu/competitors/github-copilot.md` (5230 bytes)
- `.trellis/tasks/archive/2026-01/01-19-readme-redesign-taosu/competitors/memu.md` (4629 bytes)
- `.trellis/tasks/archive/2026-01/01-19-readme-redesign-taosu/competitors/opencode.md` (6916 bytes)
- `.trellis/tasks/archive/2026-01/01-19-readme-redesign-taosu/competitors/openspec.md` (5715 bytes)
- `.trellis/tasks/archive/2026-01/01-19-readme-redesign-taosu/competitors/planning-with-files.md` (4847 bytes)
- `.trellis/tasks/archive/2026-01/01-19-readme-redesign-taosu/competitors/roo-code.md` (12057 bytes)
- `.trellis/tasks/archive/2026-01/01-19-readme-redesign-taosu/competitors/superpowers.md` (8932 bytes)
- `.trellis/tasks/archive/2026-01/01-19-readme-redesign-taosu/competitors/windsurf.md` (5753 bytes)
- `.trellis/tasks/archive/2026-01/01-19-readme-redesign-taosu/debug.jsonl` (164 bytes)
- `.trellis/tasks/archive/2026-01/01-19-readme-redesign-taosu/implement.jsonl` (341 bytes)
- `.trellis/tasks/archive/2026-01/01-19-readme-redesign-taosu/prd.md` (4885 bytes)
- `.trellis/tasks/archive/2026-01/01-19-readme-redesign-taosu/research-summary.md` (9613 bytes)
- `.trellis/tasks/archive/2026-01/01-19-readme-redesign-taosu/task.json` (733 bytes)
- `.trellis/tasks/archive/2026-01/01-19-readme-redesign-taosu/version1/DESIGN-NOTES.md` (3348 bytes)
- `.trellis/tasks/archive/2026-01/01-19-readme-redesign-taosu/version1/README-zh.md` (9522 bytes)
- `.trellis/tasks/archive/2026-01/01-19-readme-redesign-taosu/version1/README.md` (10031 bytes)
- `.trellis/tasks/archive/2026-01/01-19-readme-redesign-taosu/version2/DESIGN-NOTES.md` (1221 bytes)
- `.trellis/tasks/archive/2026-01/01-19-readme-redesign-taosu/version2/README-zh.md` (1541 bytes)
- `.trellis/tasks/archive/2026-01/01-19-readme-redesign-taosu/version2/README.md` (1569 bytes)
- `.trellis/tasks/archive/2026-01/01-19-readme-redesign-taosu/version3/DESIGN-NOTES.md` (2422 bytes)
- `.trellis/tasks/archive/2026-01/01-19-readme-redesign-taosu/version3/README-zh.md` (6217 bytes)
- `.trellis/tasks/archive/2026-01/01-19-readme-redesign-taosu/version3/README.md` (5548 bytes)
- `.trellis/tasks/archive/2026-01/01-20-product-positioning-kleinhe/prd.md` (10784 bytes)
- `.trellis/tasks/archive/2026-01/01-20-product-positioning-kleinhe/task.json` (768 bytes)
- `.trellis/tasks/archive/2026-01/01-21-doc-collaboration-research-kleinhe/prd.md` (2834 bytes)
- `.trellis/tasks/archive/2026-01/01-21-doc-collaboration-research-kleinhe/task.json` (762 bytes)
- `.trellis/tasks/archive/2026-01/01-21-early-marketing-research-kleinhe/00-research-methodology.md` (4788 bytes)
- `.trellis/tasks/archive/2026-01/01-21-early-marketing-research-kleinhe/01-continue.md` (3599 bytes)
- `.trellis/tasks/archive/2026-01/01-21-early-marketing-research-kleinhe/02-opencode.md` (5035 bytes)
- `.trellis/tasks/archive/2026-01/01-21-early-marketing-research-kleinhe/03-superpowers.md` (5072 bytes)
- `.trellis/tasks/archive/2026-01/01-21-early-marketing-research-kleinhe/04-openspec.md` (4345 bytes)
- `.trellis/tasks/archive/2026-01/01-21-early-marketing-research-kleinhe/05-roo-code.md` (7105 bytes)
- `.trellis/tasks/archive/2026-01/01-21-early-marketing-research-kleinhe/06-claude-mem.md` (7519 bytes)
- `.trellis/tasks/archive/2026-01/01-21-early-marketing-research-kleinhe/99-summary.md` (7455 bytes)
- `.trellis/tasks/archive/2026-01/01-21-early-marketing-research-kleinhe/prd.md` (2617 bytes)
- `.trellis/tasks/archive/2026-01/01-21-early-marketing-research-kleinhe/task.json` (802 bytes)
- `.trellis/tasks/archive/2026-01/01-21-mkt-growth-guide-kleinhe/daily-checklist.md` (2502 bytes)
- `.trellis/tasks/archive/2026-01/01-21-mkt-growth-guide-kleinhe/prd.md` (21260 bytes)
- `.trellis/tasks/archive/2026-01/01-21-mkt-growth-guide-kleinhe/task.json` (750 bytes)
- `.trellis/tasks/archive/2026-01/01-21-mkt-growth-guide-kleinhe/timeline.md` (7076 bytes)
- `.trellis/tasks/archive/2026-01/01-21-superpower-research-kleinhe/prd.md` (8115 bytes)
- `.trellis/tasks/archive/2026-01/01-21-superpower-research-kleinhe/task.json` (762 bytes)
- `.trellis/tasks/archive/2026-01/01-21-update-improvements-kleinhe/prd.md` (2350 bytes)
- `.trellis/tasks/archive/2026-01/01-21-update-improvements-kleinhe/task.json` (791 bytes)
- `.trellis/tasks/archive/2026-01/01-21-update-mechanism-fixes-kleinhe/prd.md` (2694 bytes)
- `.trellis/tasks/archive/2026-01/01-21-update-mechanism-fixes-kleinhe/task.json` (757 bytes)
- `.trellis/tasks/archive/2026-01/01-22-better-issue-recording/prd.md` (1237 bytes)
- `.trellis/tasks/archive/2026-01/01-22-better-issue-recording/task.json` (789 bytes)
- `.trellis/tasks/archive/2026-01/01-22-readme-visual-polish/prd.md` (1735 bytes)
- `.trellis/tasks/archive/2026-01/01-22-readme-visual-polish/task.json` (760 bytes)
- `.trellis/tasks/archive/2026-01/01-22-review-naming-pr/task.json` (836 bytes)
- `.trellis/tasks/archive/2026-01/01-22-trellis-agents-gui/check.jsonl` (238 bytes)
- `.trellis/tasks/archive/2026-01/01-22-trellis-agents-gui/debug.jsonl` (159 bytes)
- `.trellis/tasks/archive/2026-01/01-22-trellis-agents-gui/implement.jsonl` (326 bytes)
- `.trellis/tasks/archive/2026-01/01-22-trellis-agents-gui/prd.md` (5436 bytes)
- `.trellis/tasks/archive/2026-01/01-22-trellis-agents-gui/task.json` (843 bytes)
- `.trellis/tasks/archive/2026-01/01-22-trellis-agents-monorepo/check.jsonl` (316 bytes)
- `.trellis/tasks/archive/2026-01/01-22-trellis-agents-monorepo/debug.jsonl` (237 bytes)
- `.trellis/tasks/archive/2026-01/01-22-trellis-agents-monorepo/implement.jsonl` (860 bytes)
- `.trellis/tasks/archive/2026-01/01-22-trellis-agents-monorepo/prd.md` (4604 bytes)
- `.trellis/tasks/archive/2026-01/01-22-trellis-agents-monorepo/task.json` (854 bytes)
- `.trellis/tasks/archive/2026-01/01-25-session-resume-support/prd.md` (1453 bytes)
- `.trellis/tasks/archive/2026-01/01-25-session-resume-support/task.json` (766 bytes)
- `.trellis/tasks/archive/2026-01/01-26-mintlify-docs/prd.md` (2909 bytes)
- `.trellis/tasks/archive/2026-01/01-26-mintlify-docs/task.json` (846 bytes)
- `.trellis/tasks/archive/2026-01/01-27-readme-enhancements/prd.md` (1795 bytes)
- `.trellis/tasks/archive/2026-01/01-27-readme-enhancements/task.json` (850 bytes)
- `.trellis/tasks/archive/2026-01/01-28-cli-tui-system/prd.md` (7239 bytes)
- `.trellis/tasks/archive/2026-01/01-28-cli-tui-system/task.json` (755 bytes)
- `.trellis/tasks/archive/2026-01/01-29-context-benchmark/prd.md` (2417 bytes)
- `.trellis/tasks/archive/2026-01/01-29-context-benchmark/report.md` (5092 bytes)
- `.trellis/tasks/archive/2026-01/01-29-context-benchmark/task.json` (758 bytes)
- `.trellis/tasks/archive/2026-01/01-29-context-benchmark/workflow-context-map.md` (11881 bytes)
- `.trellis/tasks/archive/2026-01/01-30-bash2py/prd.md` (8037 bytes)
- `.trellis/tasks/archive/2026-01/01-30-bash2py/task.json` (869 bytes)
- `.trellis/tasks/archive/2026-02/02-01-opencode-support/check.jsonl` (252 bytes)
- `.trellis/tasks/archive/2026-02/02-01-opencode-support/debug.jsonl` (165 bytes)
- `.trellis/tasks/archive/2026-02/02-01-opencode-support/implement.jsonl` (408 bytes)
- `.trellis/tasks/archive/2026-02/02-01-opencode-support/prd.md` (37894 bytes)
- `.trellis/tasks/archive/2026-02/02-01-opencode-support/task.json` (810 bytes)
- `.trellis/tasks/archive/2026-02/02-01-opencode-support/task.md` (19256 bytes)
- `.trellis/tasks/archive/2026-02/02-03-template-init-test/check.jsonl` (256 bytes)
- `.trellis/tasks/archive/2026-02/02-03-template-init-test/debug.jsonl` (167 bytes)
- `.trellis/tasks/archive/2026-02/02-03-template-init-test/implement.jsonl` (408 bytes)
- `.trellis/tasks/archive/2026-02/02-03-template-init-test/prd.md` (2117 bytes)
- `.trellis/tasks/archive/2026-02/02-03-template-init-test/task.json` (876 bytes)
- `.trellis/tasks/archive/2026-02/02-04-fix-update-platform-selection/prd.md` (1191 bytes)
- `.trellis/tasks/archive/2026-02/02-04-fix-update-platform-selection/task.json` (807 bytes)
- `.trellis/tasks/archive/2026-02/02-04-sync-iflow-pr22/prd.md` (3303 bytes)
- `.trellis/tasks/archive/2026-02/02-04-sync-iflow-pr22/task.json` (758 bytes)
- `.trellis/tasks/archive/2026-02/02-05-cross-platform-python/prd.md` (2929 bytes)
- `.trellis/tasks/archive/2026-02/02-05-cross-platform-python/task.json` (799 bytes)
- `.trellis/tasks/archive/2026-02/02-05-improve-brainstorm-flow/prd.md` (4076 bytes)
- `.trellis/tasks/archive/2026-02/02-05-improve-brainstorm-flow/task.json` (787 bytes)
- `.trellis/tasks/archive/2026-02/02-05-remote-template-init/prd.md` (8120 bytes)
- `.trellis/tasks/archive/2026-02/02-05-remote-template-init/task.json` (776 bytes)
- `.trellis/tasks/archive/2026-02/02-06-e2e-integration-tests/prd.md` (11117 bytes)
- `.trellis/tasks/archive/2026-02/02-06-e2e-integration-tests/task.json` (784 bytes)
- `.trellis/tasks/archive/2026-02/02-06-platform-registry-refactor/check.jsonl` (378 bytes)
- `.trellis/tasks/archive/2026-02/02-06-platform-registry-refactor/debug.jsonl` (167 bytes)
- `.trellis/tasks/archive/2026-02/02-06-platform-registry-refactor/implement.jsonl` (631 bytes)
- `.trellis/tasks/archive/2026-02/02-06-platform-registry-refactor/prd.md` (7723 bytes)
- `.trellis/tasks/archive/2026-02/02-06-platform-registry-refactor/task.json` (798 bytes)
- `.trellis/tasks/archive/2026-02/02-06-python-windows-testing/prd.md` (3854 bytes)
- `.trellis/tasks/archive/2026-02/02-06-python-windows-testing/task.json` (774 bytes)
- `.trellis/tasks/archive/2026-02/02-06-unit-test-platform-registry/prd.md` (16837 bytes)
- `.trellis/tasks/archive/2026-02/02-06-unit-test-platform-registry/task.json` (795 bytes)
- `.trellis/tasks/archive/2026-02/02-09-codex-skills-template-init/prd.md` (7759 bytes)
- `.trellis/tasks/archive/2026-02/02-09-codex-skills-template-init/task.json` (788 bytes)
- `.trellis/tasks/archive/2026-02/02-26-gemini-cli-support/check.jsonl` (514 bytes)
- `.trellis/tasks/archive/2026-02/02-26-gemini-cli-support/debug.jsonl` (167 bytes)
- `.trellis/tasks/archive/2026-02/02-26-gemini-cli-support/implement.jsonl` (1268 bytes)
- `.trellis/tasks/archive/2026-02/02-26-gemini-cli-support/prd.md` (3875 bytes)
- `.trellis/tasks/archive/2026-02/02-26-gemini-cli-support/task.json` (766 bytes)
- `.trellis/tasks/archive/2026-02/02-28-migrate-to-0.3.0/prd.md` (1890 bytes)
- `.trellis/tasks/archive/2026-02/02-28-migrate-to-0.3.0/task.json` (761 bytes)
- `.trellis/tasks/archive/2026-03/03-04-init-download-ux/prd.md` (2821 bytes)
- `.trellis/tasks/archive/2026-03/03-04-init-download-ux/task.json` (924 bytes)
- `.trellis/tasks/archive/2026-03/03-04-record-session-task-awareness/prd.md` (4920 bytes)
- `.trellis/tasks/archive/2026-03/03-04-record-session-task-awareness/task.json` (853 bytes)
- `.trellis/tasks/archive/2026-03/03-04-support-trae-qoder/check.jsonl` (882 bytes)
- `.trellis/tasks/archive/2026-03/03-04-support-trae-qoder/debug.jsonl` (722 bytes)
- `.trellis/tasks/archive/2026-03/03-04-support-trae-qoder/implement.jsonl` (2043 bytes)
- `.trellis/tasks/archive/2026-03/03-04-support-trae-qoder/prd.md` (3171 bytes)
- `.trellis/tasks/archive/2026-03/03-04-support-trae-qoder/task.json` (934 bytes)
- `.trellis/tasks/archive/2026-03/03-04-update-skip-spec/task.json` (833 bytes)
- `.trellis/tasks/archive/2026-03/03-05-hooks-docs/prd.md` (1510 bytes)
- `.trellis/tasks/archive/2026-03/03-05-hooks-docs/task.json` (885 bytes)
- `.trellis/tasks/archive/2026-03/03-05-remote-spec-templates/prd.md` (5325 bytes)
- `.trellis/tasks/archive/2026-03/03-05-remote-spec-templates/task.json` (866 bytes)
- `.trellis/tasks/archive/2026-03/03-05-task-lifecycle-hooks/prd.md` (3430 bytes)
- `.trellis/tasks/archive/2026-03/03-05-task-lifecycle-hooks/task.json` (900 bytes)
- `.trellis/tasks/archive/2026-03/03-05-task-subtask/check.jsonl` (177 bytes)
- `.trellis/tasks/archive/2026-03/03-05-task-subtask/debug.jsonl` (88 bytes)
- `.trellis/tasks/archive/2026-03/03-05-task-subtask/implement.jsonl` (648 bytes)
- `.trellis/tasks/archive/2026-03/03-05-task-subtask/prd.md` (4440 bytes)
- `.trellis/tasks/archive/2026-03/03-05-task-subtask/task.json` (802 bytes)
- `.trellis/tasks/archive/2026-03/03-05-tmux-support/prd.md` (2062 bytes)
- `.trellis/tasks/archive/2026-03/03-05-tmux-support/task.json` (818 bytes)
- `.trellis/tasks/archive/2026-03/03-05-v036-update/task.json` (823 bytes)
- `.trellis/tasks/archive/2026-03/03-06-hook-start-equiv/prd.md` (5745 bytes)
- `.trellis/tasks/archive/2026-03/03-06-hook-start-equiv/task.json` (1026 bytes)
- `.trellis/tasks/archive/2026-03/03-06-update-skip-dirs/prd.md` (2952 bytes)
- `.trellis/tasks/archive/2026-03/03-06-update-skip-dirs/task.json` (1013 bytes)
- `.trellis/tasks/archive/2026-03/03-06-v037/prd.md` (171 bytes)
- `.trellis/tasks/archive/2026-03/03-06-v037/task.json` (789 bytes)
- `.trellis/tasks/archive/2026-03/03-07-learn-openspec-prd/prd.md` (5494 bytes)
- `.trellis/tasks/archive/2026-03/03-07-learn-openspec-prd/task.json` (1012 bytes)
- `.trellis/tasks/archive/2026-03/03-08-template-marketplace/prd.md` (3062 bytes)
- `.trellis/tasks/archive/2026-03/03-08-template-marketplace/task.json` (847 bytes)
- `.trellis/tasks/archive/2026-03/03-09-extract-repo-level-content/prd.md` (9732 bytes)
- `.trellis/tasks/archive/2026-03/03-09-extract-repo-level-content/task.json` (895 bytes)
- `.trellis/tasks/archive/2026-03/03-09-monorepo-spec-adapt/prd.md` (24545 bytes)
- `.trellis/tasks/archive/2026-03/03-09-monorepo-spec-adapt/task.json` (900 bytes)
- `.trellis/tasks/archive/2026-03/03-09-monorepo-submodule/check.jsonl` (319 bytes)
- `.trellis/tasks/archive/2026-03/03-09-monorepo-submodule/debug.jsonl` (88 bytes)
- `.trellis/tasks/archive/2026-03/03-09-monorepo-submodule/implement.jsonl` (411 bytes)
- `.trellis/tasks/archive/2026-03/03-09-monorepo-submodule/prd.md` (7144 bytes)
- `.trellis/tasks/archive/2026-03/03-09-monorepo-submodule/task.json` (861 bytes)
- `.trellis/tasks/archive/2026-03/03-09-update-template-source/prd.md` (2335 bytes)
- `.trellis/tasks/archive/2026-03/03-09-update-template-source/task.json` (894 bytes)
- `.trellis/tasks/archive/2026-03/03-10-dogfood-monorepo-compat/prd.md` (2315 bytes)
- `.trellis/tasks/archive/2026-03/03-10-dogfood-monorepo-compat/task.json` (905 bytes)
- `.trellis/tasks/archive/2026-03/03-10-merge-monorepo-branch/prd.md` (2604 bytes)
- `.trellis/tasks/archive/2026-03/03-10-merge-monorepo-branch/task.json` (877 bytes)
- `.trellis/tasks/archive/2026-03/03-10-monorepo-compat/prd.md` (14900 bytes)
- `.trellis/tasks/archive/2026-03/03-10-monorepo-compat/task.json` (872 bytes)
- `.trellis/tasks/archive/2026-03/03-10-s1-infra/check.jsonl` (349 bytes)
- `.trellis/tasks/archive/2026-03/03-10-s1-infra/debug.jsonl` (85 bytes)
- `.trellis/tasks/archive/2026-03/03-10-s1-infra/implement.jsonl` (651 bytes)
- `.trellis/tasks/archive/2026-03/03-10-s1-infra/prd.md` (15733 bytes)
- `.trellis/tasks/archive/2026-03/03-10-s1-infra/task.json` (869 bytes)
- `.trellis/tasks/archive/2026-03/03-10-s2-commands/prd.md` (7205 bytes)
- `.trellis/tasks/archive/2026-03/03-10-s2-commands/task.json` (873 bytes)
- `.trellis/tasks/archive/2026-03/03-10-s3-task-update/prd.md` (18511 bytes)
- `.trellis/tasks/archive/2026-03/03-10-s3-task-update/task.json` (879 bytes)
- `.trellis/tasks/archive/2026-03/03-10-s4-worktree/check.jsonl` (504 bytes)
- `.trellis/tasks/archive/2026-03/03-10-s4-worktree/debug.jsonl` (85 bytes)
- `.trellis/tasks/archive/2026-03/03-10-s4-worktree/implement.jsonl` (726 bytes)
- `.trellis/tasks/archive/2026-03/03-10-s4-worktree/prd.md` (13910 bytes)
- `.trellis/tasks/archive/2026-03/03-10-s4-worktree/task.json` (874 bytes)
- `.trellis/tasks/archive/2026-03/03-10-v040-beta1/prd.md` (3195 bytes)
- `.trellis/tasks/archive/2026-03/03-10-v040-beta1/task.json` (875 bytes)
- `.trellis/tasks/archive/2026-03/03-11-improve-break-loop-update-spec/prd.md` (2765 bytes)
- `.trellis/tasks/archive/2026-03/03-11-improve-break-loop-update-spec/task.json` (898 bytes)
- `.trellis/tasks/archive/2026-03/03-11-spec-path-dynamic/prd.md` (2229 bytes)
- `.trellis/tasks/archive/2026-03/03-11-spec-path-dynamic/task.json` (868 bytes)
- `.trellis/tasks/archive/2026-03/03-12-codex-review-fixes/prd.md` (11112 bytes)
- `.trellis/tasks/archive/2026-03/03-12-codex-review-fixes/task.json` (868 bytes)
- `.trellis/tasks/archive/2026-03/03-12-refactor-python-scripts/check.jsonl` (268 bytes)
- `.trellis/tasks/archive/2026-03/03-12-refactor-python-scripts/debug.jsonl` (85 bytes)
- `.trellis/tasks/archive/2026-03/03-12-refactor-python-scripts/golden-tests/add-session-help.exitcode` (2 bytes)
- `.trellis/tasks/archive/2026-03/03-12-refactor-python-scripts/golden-tests/add-session-help.stderr` (0 bytes)
- `.trellis/tasks/archive/2026-03/03-12-refactor-python-scripts/golden-tests/add-session-help.stdout` (735 bytes)
- `.trellis/tasks/archive/2026-03/03-12-refactor-python-scripts/golden-tests/packages.exitcode` (2 bytes)
- `.trellis/tasks/archive/2026-03/03-12-refactor-python-scripts/golden-tests/packages.stderr` (0 bytes)
- `.trellis/tasks/archive/2026-03/03-12-refactor-python-scripts/golden-tests/packages.stdout` (339 bytes)
- `.trellis/tasks/archive/2026-03/03-12-refactor-python-scripts/golden-tests/task-list.exitcode` (2 bytes)
- `.trellis/tasks/archive/2026-03/03-12-refactor-python-scripts/golden-tests/task-list.stderr` (0 bytes)
- `.trellis/tasks/archive/2026-03/03-12-refactor-python-scripts/golden-tests/task-list.stdout` (390 bytes)
- `.trellis/tasks/archive/2026-03/03-12-refactor-python-scripts/implement.jsonl` (363 bytes)
- `.trellis/tasks/archive/2026-03/03-12-refactor-python-scripts/prd.md` (6439 bytes)
- `.trellis/tasks/archive/2026-03/03-12-refactor-python-scripts/task.json` (941 bytes)
- `.trellis/tasks/archive/2026-03/03-12-spec-sync-after-s1s4/prd.md` (1954 bytes)
- `.trellis/tasks/archive/2026-03/03-12-spec-sync-after-s1s4/task.json` (878 bytes)
- `.trellis/tasks/archive/2026-03/03-12-yaml-quote-strip-bug/prd.md` (3500 bytes)
- `.trellis/tasks/archive/2026-03/03-12-yaml-quote-strip-bug/task.json` (891 bytes)
- `.trellis/tasks/archive/2026-03/03-13-rename-empty-template/check.jsonl` (174 bytes)
- `.trellis/tasks/archive/2026-03/03-13-rename-empty-template/debug.jsonl` (85 bytes)
- `.trellis/tasks/archive/2026-03/03-13-rename-empty-template/implement.jsonl` (165 bytes)
- `.trellis/tasks/archive/2026-03/03-13-rename-empty-template/prd.md` (1116 bytes)
- `.trellis/tasks/archive/2026-03/03-13-rename-empty-template/task.json` (913 bytes)
- `.trellis/tasks/archive/2026-03/03-24-agents-dir-ownership/check.jsonl` (378 bytes)
- `.trellis/tasks/archive/2026-03/03-24-agents-dir-ownership/debug.jsonl` (85 bytes)
- `.trellis/tasks/archive/2026-03/03-24-agents-dir-ownership/implement.jsonl` (553 bytes)
- `.trellis/tasks/archive/2026-03/03-24-agents-dir-ownership/prd.md` (8291 bytes)
- `.trellis/tasks/archive/2026-03/03-24-agents-dir-ownership/task.json` (905 bytes)
- `.trellis/tasks/archive/2026-03/03-26-statusline-integration/task.json` (907 bytes)
- `.trellis/tasks/archive/2026-03/03-27-self-hosted-gitlab/check.jsonl` (346 bytes)
- `.trellis/tasks/archive/2026-03/03-27-self-hosted-gitlab/debug.jsonl` (85 bytes)
- `.trellis/tasks/archive/2026-03/03-27-self-hosted-gitlab/implement.jsonl` (346 bytes)
- `.trellis/tasks/archive/2026-03/03-27-self-hosted-gitlab/prd.md` (3083 bytes)
- `.trellis/tasks/archive/2026-03/03-27-self-hosted-gitlab/task.json` (885 bytes)
- `.trellis/tasks/archive/2026-04/03-24-py39-compat/prd.md` (1447 bytes)
- `.trellis/tasks/archive/2026-04/03-24-py39-compat/task.json` (877 bytes)
- `.trellis/workspace/index.md` (2328 bytes)
- `.trellis/workspace/kleinhe/index.md` (1857 bytes)
- `.trellis/workspace/kleinhe/journal-1.md` (15544 bytes)
- `.trellis/workspace/taosu/ai_smell_scan.py` (12717 bytes)
- `.trellis/workspace/taosu/index.md` (12257 bytes)
- `.trellis/workspace/taosu/journal-1.md` (48389 bytes)
- `.trellis/workspace/taosu/journal-2.md` (52603 bytes)
- `.trellis/workspace/taosu/journal-3.md` (62865 bytes)
- `.trellis/workspace/taosu/journal-4.md` (23020 bytes)
- `.trellis/worktree.yaml` (1813 bytes)
- `AGENTS.md` (688 bytes)
- `CONTRIBUTING.md` (4043 bytes)
- `CONTRIBUTING_CN.md` (3700 bytes)
- `COPYRIGHT` (734 bytes)
- `LICENSE` (34020 bytes)
- `README_CN.md` (11853 bytes)
- `assets/discord_wx_comment.jpg` (464857 bytes)
- `assets/info.png` (440405 bytes)
- `assets/linuxdo_comment.jpg` (495193 bytes)
- `assets/meme.png` (1582927 bytes)
- `assets/meme_zh.png` (661490 bytes)
- `assets/qq-group-qr.jpg` (428418 bytes)
- `assets/trellis-demo-zh.gif` (61302104 bytes)
- `assets/trellis-demo.gif` (48638263 bytes)
- `assets/trellis.png` (990 bytes)
- `assets/usecase1.png` (179873 bytes)
- `assets/usecase2.png` (153451 bytes)
- `assets/usecase3.png` (170832 bytes)
- `assets/wecom-group-qr.png` (140101 bytes)
- `assets/workflow.png` (155407 bytes)
- `assets/wx_link.jpg` (180218 bytes)
- `assets/wx_link1.jpg` (258325 bytes)
- `assets/wx_link2.jpg` (186385 bytes)
- `assets/wx_link3.jpg` (187641 bytes)
- `assets/wx_link4.jpg` (260064 bytes)
- `assets/wx_link5.jpg` (129183 bytes)
- `package.json` (641 bytes)
- `packages/cli/.npmrc` (78 bytes)
- `packages/cli/.prettierignore` (44 bytes)
- `packages/cli/.prettierrc` (200 bytes)
- `packages/cli/bin/trellis.js` (53 bytes)
- `packages/cli/eslint.config.js` (1261 bytes)
- `packages/cli/package.json` (4187 bytes)
- `packages/cli/scripts/copy-templates.js` (2013 bytes)
- `packages/cli/scripts/create-manifest.js` (9123 bytes)
- `packages/cli/scripts/migrate-features-to-tasks.sh` (10056 bytes)
- `packages/cli/src/cli/index.ts` (4874 bytes)
- `packages/cli/src/commands/init.ts` (46023 bytes)
- `packages/cli/src/commands/update.ts` (58549 bytes)
- `packages/cli/src/configurators/antigravity.ts` (620 bytes)
- `packages/cli/src/configurators/claude.ts` (3119 bytes)
- `packages/cli/src/configurators/codebuddy.ts` (1791 bytes)
- `packages/cli/src/configurators/codex.ts` (2167 bytes)
- `packages/cli/src/configurators/copilot.ts` (1718 bytes)
- `packages/cli/src/configurators/cursor.ts` (1586 bytes)
- `packages/cli/src/configurators/droid.ts` (1510 bytes)
- `packages/cli/src/configurators/gemini.ts` (1473 bytes)
- `packages/cli/src/configurators/iflow.ts` (3133 bytes)
- `packages/cli/src/configurators/index.ts` (13362 bytes)
- `packages/cli/src/configurators/kilo.ts` (1469 bytes)
- `packages/cli/src/configurators/kiro.ts` (646 bytes)
- `packages/cli/src/configurators/opencode.ts` (2834 bytes)
- `packages/cli/src/configurators/qoder.ts` (1451 bytes)
- `packages/cli/src/configurators/shared.ts` (683 bytes)
- `packages/cli/src/configurators/windsurf.ts` (617 bytes)
- `packages/cli/src/configurators/workflow.ts` (7870 bytes)
- `packages/cli/src/constants/paths.ts` (2477 bytes)
- `packages/cli/src/constants/version.ts` (685 bytes)
- `packages/cli/src/index.ts` (316 bytes)
- `packages/cli/src/migrations/index.ts` (5913 bytes)
- `packages/cli/src/migrations/manifests/0.1.9.json` (911 bytes)
- `packages/cli/src/migrations/manifests/0.2.0.json` (1550 bytes)
- `packages/cli/src/migrations/manifests/0.2.12.json` (308 bytes)
- `packages/cli/src/migrations/manifests/0.2.13.json` (226 bytes)
- `packages/cli/src/migrations/manifests/0.2.14.json` (6743 bytes)
- `packages/cli/src/migrations/manifests/0.2.15.json` (1146 bytes)
- `packages/cli/src/migrations/manifests/0.3.0-beta.0.json` (14544 bytes)
- `packages/cli/src/migrations/manifests/0.3.0-beta.1.json` (301 bytes)
- `packages/cli/src/migrations/manifests/0.3.0-beta.10.json` (995 bytes)
- `packages/cli/src/migrations/manifests/0.3.0-beta.11.json` (274 bytes)
- `packages/cli/src/migrations/manifests/0.3.0-beta.12.json` (1168 bytes)
- `packages/cli/src/migrations/manifests/0.3.0-beta.13.json` (1277 bytes)
- `packages/cli/src/migrations/manifests/0.3.0-beta.14.json` (544 bytes)
- `packages/cli/src/migrations/manifests/0.3.0-beta.15.json` (373 bytes)
- `packages/cli/src/migrations/manifests/0.3.0-beta.16.json` (706 bytes)
- `packages/cli/src/migrations/manifests/0.3.0-beta.2.json` (406 bytes)
- `packages/cli/src/migrations/manifests/0.3.0-beta.3.json` (366 bytes)
- `packages/cli/src/migrations/manifests/0.3.0-beta.4.json` (217 bytes)
- `packages/cli/src/migrations/manifests/0.3.0-beta.5.json` (295 bytes)
- `packages/cli/src/migrations/manifests/0.3.0-beta.6.json` (401 bytes)
- `packages/cli/src/migrations/manifests/0.3.0-beta.7.json` (2578 bytes)
- `packages/cli/src/migrations/manifests/0.3.0-beta.8.json` (455 bytes)
- `packages/cli/src/migrations/manifests/0.3.0-beta.9.json` (1202 bytes)
- `packages/cli/src/migrations/manifests/0.3.0-rc.0.json` (1571 bytes)
- `packages/cli/src/migrations/manifests/0.3.0-rc.1.json` (848 bytes)
- `packages/cli/src/migrations/manifests/0.3.0-rc.2.json` (1290 bytes)
- `packages/cli/src/migrations/manifests/0.3.0-rc.3.json` (1240 bytes)
- `packages/cli/src/migrations/manifests/0.3.0-rc.4.json` (1186 bytes)
- `packages/cli/src/migrations/manifests/0.3.0-rc.5.json` (781 bytes)
- `packages/cli/src/migrations/manifests/0.3.0-rc.6.json` (1146 bytes)
- `packages/cli/src/migrations/manifests/0.3.0.json` (3663 bytes)
- `packages/cli/src/migrations/manifests/0.3.1.json` (1167 bytes)
- `packages/cli/src/migrations/manifests/0.3.10.json` (508 bytes)
- `packages/cli/src/migrations/manifests/0.3.2.json` (865 bytes)
- `packages/cli/src/migrations/manifests/0.3.3.json` (1417 bytes)
- `packages/cli/src/migrations/manifests/0.3.4.json` (1386 bytes)
- `packages/cli/src/migrations/manifests/0.3.5.json` (408 bytes)
- `packages/cli/src/migrations/manifests/0.3.6.json` (1146 bytes)
- `packages/cli/src/migrations/manifests/0.3.7.json` (948 bytes)
- `packages/cli/src/migrations/manifests/0.3.8.json` (454 bytes)
- `packages/cli/src/migrations/manifests/0.3.9.json` (386 bytes)
- `packages/cli/src/migrations/manifests/0.4.0-beta.1.json` (13231 bytes)
- `packages/cli/src/migrations/manifests/0.4.0-beta.10.json` (1418 bytes)
- `packages/cli/src/migrations/manifests/0.4.0-beta.2.json` (668 bytes)
- `packages/cli/src/migrations/manifests/0.4.0-beta.3.json` (691 bytes)
- `packages/cli/src/migrations/manifests/0.4.0-beta.4.json` (828 bytes)
- `packages/cli/src/migrations/manifests/0.4.0-beta.5.json` (459 bytes)
- `packages/cli/src/migrations/manifests/0.4.0-beta.6.json` (635 bytes)
- `packages/cli/src/migrations/manifests/0.4.0-beta.7.json` (469 bytes)
- `packages/cli/src/migrations/manifests/0.4.0-beta.8.json` (2065 bytes)
- `packages/cli/src/migrations/manifests/0.4.0-beta.9.json` (1464 bytes)
- `packages/cli/src/migrations/manifests/0.4.0-rc.0.json` (2647 bytes)
- `packages/cli/src/migrations/manifests/0.4.0-rc.1.json` (1404 bytes)
- `packages/cli/src/migrations/manifests/0.4.0.json` (4070 bytes)
- `packages/cli/src/templates/antigravity/index.ts` (1563 bytes)
- `packages/cli/src/templates/claude/agents/check.md` (2833 bytes)
- `packages/cli/src/templates/claude/agents/debug.md` (1935 bytes)
- `packages/cli/src/templates/claude/agents/dispatch.md` (5228 bytes)
- `packages/cli/src/templates/claude/agents/implement.md` (2037 bytes)
- `packages/cli/src/templates/claude/agents/plan.md` (10266 bytes)
- `packages/cli/src/templates/claude/agents/research.md` (2470 bytes)
- `packages/cli/src/templates/claude/commands/trellis/before-dev.md` (1171 bytes)
- `packages/cli/src/templates/claude/commands/trellis/brainstorm.md` (12418 bytes)
- `packages/cli/src/templates/claude/commands/trellis/break-loop.md` (4459 bytes)
- `packages/cli/src/templates/claude/commands/trellis/check-cross-layer.md` (4648 bytes)
- `packages/cli/src/templates/claude/commands/trellis/check.md` (871 bytes)
- `packages/cli/src/templates/claude/commands/trellis/create-command.md` (3261 bytes)
- `packages/cli/src/templates/claude/commands/trellis/finish-work.md` (4377 bytes)
- `packages/cli/src/templates/claude/commands/trellis/integrate-skill.md` (5831 bytes)
- `packages/cli/src/templates/claude/commands/trellis/onboard.md` (14611 bytes)
- `packages/cli/src/templates/claude/commands/trellis/parallel.md` (5134 bytes)
- `packages/cli/src/templates/claude/commands/trellis/record-session.md` (2328 bytes)
- `packages/cli/src/templates/claude/commands/trellis/start.md` (11040 bytes)
- `packages/cli/src/templates/claude/commands/trellis/update-spec.md` (10084 bytes)
- `packages/cli/src/templates/claude/hooks/inject-subagent-context.py` (25915 bytes)
- `packages/cli/src/templates/claude/hooks/ralph-loop.py` (13313 bytes)
- `packages/cli/src/templates/claude/hooks/session-start.py` (14425 bytes)
- `packages/cli/src/templates/claude/hooks/statusline.py` (6575 bytes)
- `packages/cli/src/templates/claude/index.ts` (2792 bytes)
- `packages/cli/src/templates/claude/settings.json` (1614 bytes)
- `packages/cli/src/templates/codebuddy/commands/trellis/before-dev.md` (1171 bytes)
- `packages/cli/src/templates/codebuddy/commands/trellis/brainstorm.md` (12418 bytes)
- `packages/cli/src/templates/codebuddy/commands/trellis/break-loop.md` (3672 bytes)
- `packages/cli/src/templates/codebuddy/commands/trellis/check-cross-layer.md` (4648 bytes)
- `packages/cli/src/templates/codebuddy/commands/trellis/check.md` (871 bytes)
- `packages/cli/src/templates/codebuddy/commands/trellis/create-command.md` (3253 bytes)
- `packages/cli/src/templates/codebuddy/commands/trellis/finish-work.md` (3906 bytes)
- `packages/cli/src/templates/codebuddy/commands/trellis/integrate-skill.md` (5831 bytes)
- `packages/cli/src/templates/codebuddy/commands/trellis/onboard.md` (14611 bytes)
- `packages/cli/src/templates/codebuddy/commands/trellis/record-session.md` (2158 bytes)
- `packages/cli/src/templates/codebuddy/commands/trellis/start.md` (10030 bytes)
- `packages/cli/src/templates/codebuddy/commands/trellis/update-spec.md` (10084 bytes)
- `packages/cli/src/templates/codebuddy/index.ts` (1446 bytes)
- `packages/cli/src/templates/codex/agents/check.toml` (732 bytes)
- `packages/cli/src/templates/codex/agents/implement.toml` (733 bytes)
- `packages/cli/src/templates/codex/agents/research.toml` (686 bytes)
- `packages/cli/src/templates/codex/codex-skills/parallel/SKILL.md` (5526 bytes)
- `packages/cli/src/templates/codex/config.toml` (238 bytes)
- `packages/cli/src/templates/codex/hooks.json` (305 bytes)
- `packages/cli/src/templates/codex/hooks/session-start.py` (8154 bytes)
- `packages/cli/src/templates/codex/index.ts` (3027 bytes)
- `packages/cli/src/templates/codex/skills/before-dev/SKILL.md` (1571 bytes)
- `packages/cli/src/templates/codex/skills/brainstorm/SKILL.md` (12836 bytes)
- `packages/cli/src/templates/codex/skills/break-loop/SKILL.md` (4928 bytes)
- `packages/cli/src/templates/codex/skills/check-cross-layer/SKILL.md` (5102 bytes)
- `packages/cli/src/templates/codex/skills/check/SKILL.md` (1273 bytes)
- `packages/cli/src/templates/codex/skills/create-command/SKILL.md` (2505 bytes)
- `packages/cli/src/templates/codex/skills/finish-work/SKILL.md` (4241 bytes)
- `packages/cli/src/templates/codex/skills/improve-ut/SKILL.md` (1747 bytes)
- `packages/cli/src/templates/codex/skills/integrate-skill/SKILL.md` (6250 bytes)
- `packages/cli/src/templates/codex/skills/onboard/SKILL.md` (14779 bytes)
- `packages/cli/src/templates/codex/skills/record-session/SKILL.md` (2708 bytes)
- `packages/cli/src/templates/codex/skills/start/SKILL.md` (9997 bytes)
- `packages/cli/src/templates/codex/skills/update-spec/SKILL.md` (9928 bytes)
- `packages/cli/src/templates/copilot/hooks.json` (190 bytes)
- `packages/cli/src/templates/copilot/hooks/session-start.py` (8170 bytes)
- `packages/cli/src/templates/copilot/index.ts` (1706 bytes)
- `packages/cli/src/templates/copilot/prompts/before-dev.prompt.md` (1236 bytes)
- `packages/cli/src/templates/copilot/prompts/brainstorm.prompt.md` (12420 bytes)
- `packages/cli/src/templates/copilot/prompts/break-loop.prompt.md` (4538 bytes)
- `packages/cli/src/templates/copilot/prompts/check-cross-layer.prompt.md` (4689 bytes)
- `packages/cli/src/templates/copilot/prompts/check.prompt.md` (931 bytes)
- `packages/cli/src/templates/copilot/prompts/create-command.prompt.md` (2091 bytes)
- `packages/cli/src/templates/copilot/prompts/finish-work.prompt.md` (4318 bytes)
- `packages/cli/src/templates/copilot/prompts/integrate-skill.prompt.md` (5835 bytes)
- `packages/cli/src/templates/copilot/prompts/onboard.prompt.md` (14145 bytes)
- `packages/cli/src/templates/copilot/prompts/parallel.prompt.md` (5142 bytes)
- `packages/cli/src/templates/copilot/prompts/record-session.prompt.md` (2404 bytes)
- `packages/cli/src/templates/copilot/prompts/start.prompt.md` (10919 bytes)
- `packages/cli/src/templates/copilot/prompts/update-spec.prompt.md` (10070 bytes)
- `packages/cli/src/templates/cursor/commands/trellis-before-dev.md` (1171 bytes)
- `packages/cli/src/templates/cursor/commands/trellis-brainstorm.md` (12418 bytes)
- `packages/cli/src/templates/cursor/commands/trellis-break-loop.md` (3672 bytes)
- `packages/cli/src/templates/cursor/commands/trellis-check-cross-layer.md` (4648 bytes)
- `packages/cli/src/templates/cursor/commands/trellis-check.md` (871 bytes)
- `packages/cli/src/templates/cursor/commands/trellis-create-command.md` (3261 bytes)
- `packages/cli/src/templates/cursor/commands/trellis-finish-work.md` (3906 bytes)
- `packages/cli/src/templates/cursor/commands/trellis-integrate-skill.md` (5831 bytes)
- `packages/cli/src/templates/cursor/commands/trellis-onboard.md` (14611 bytes)
- `packages/cli/src/templates/cursor/commands/trellis-record-session.md` (2328 bytes)
- `packages/cli/src/templates/cursor/commands/trellis-start.md` (10012 bytes)
- `packages/cli/src/templates/cursor/commands/trellis-update-spec.md` (10084 bytes)
- `packages/cli/src/templates/cursor/index.ts` (1425 bytes)
- `packages/cli/src/templates/droid/commands/trellis/before-dev.md` (1260 bytes)
- `packages/cli/src/templates/droid/commands/trellis/brainstorm.md` (12499 bytes)
- `packages/cli/src/templates/droid/commands/trellis/break-loop.md` (3749 bytes)
- `packages/cli/src/templates/droid/commands/trellis/check-cross-layer.md` (4729 bytes)
- `packages/cli/src/templates/droid/commands/trellis/check.md` (959 bytes)
- `packages/cli/src/templates/droid/commands/trellis/create-command.md` (3345 bytes)
- `packages/cli/src/templates/droid/commands/trellis/finish-work.md` (3995 bytes)
- `packages/cli/src/templates/droid/commands/trellis/integrate-skill.md` (5924 bytes)
- `packages/cli/src/templates/droid/commands/trellis/onboard.md` (14702 bytes)
- `packages/cli/src/templates/droid/commands/trellis/record-session.md` (2420 bytes)
- `packages/cli/src/templates/droid/commands/trellis/start.md` (10098 bytes)
- `packages/cli/src/templates/droid/commands/trellis/update-spec.md` (10173 bytes)
- `packages/cli/src/templates/droid/index.ts` (1563 bytes)
- `packages/cli/src/templates/extract.ts` (14864 bytes)
- `packages/cli/src/templates/gemini/commands/trellis/before-dev.toml` (1271 bytes)
- `packages/cli/src/templates/gemini/commands/trellis/brainstorm.toml` (11620 bytes)
- `packages/cli/src/templates/gemini/commands/trellis/break-loop.toml` (4544 bytes)
- `packages/cli/src/templates/gemini/commands/trellis/check-cross-layer.toml` (4229 bytes)
- `packages/cli/src/templates/gemini/commands/trellis/check.toml` (972 bytes)
- `packages/cli/src/templates/gemini/commands/trellis/create-command.toml` (2612 bytes)
- `packages/cli/src/templates/gemini/commands/trellis/finish-work.toml` (3296 bytes)
- `packages/cli/src/templates/gemini/commands/trellis/integrate-skill.toml` (3341 bytes)
- `packages/cli/src/templates/gemini/commands/trellis/onboard.toml` (4039 bytes)
- `packages/cli/src/templates/gemini/commands/trellis/record-session.toml` (2428 bytes)
- `packages/cli/src/templates/gemini/commands/trellis/start.toml` (9772 bytes)
- `packages/cli/src/templates/gemini/commands/trellis/update-spec.toml` (4768 bytes)
- `packages/cli/src/templates/gemini/index.ts` (1383 bytes)
- `packages/cli/src/templates/iflow/agents/check.md` (2835 bytes)
- `packages/cli/src/templates/iflow/agents/debug.md` (1934 bytes)
- `packages/cli/src/templates/iflow/agents/dispatch.md` (5228 bytes)
- `packages/cli/src/templates/iflow/agents/implement.md` (2038 bytes)
- `packages/cli/src/templates/iflow/agents/plan.md` (10244 bytes)
- `packages/cli/src/templates/iflow/agents/research.md` (2471 bytes)
- `packages/cli/src/templates/iflow/commands/trellis/before-dev.md` (1171 bytes)
- `packages/cli/src/templates/iflow/commands/trellis/brainstorm.md` (12418 bytes)
- `packages/cli/src/templates/iflow/commands/trellis/break-loop.md` (4459 bytes)
- `packages/cli/src/templates/iflow/commands/trellis/check-cross-layer.md` (4648 bytes)
- `packages/cli/src/templates/iflow/commands/trellis/check.md` (871 bytes)
- `packages/cli/src/templates/iflow/commands/trellis/create-command.md` (3114 bytes)
- `packages/cli/src/templates/iflow/commands/trellis/finish-work.md` (4377 bytes)
- `packages/cli/src/templates/iflow/commands/trellis/integrate-skill.md` (5829 bytes)
- `packages/cli/src/templates/iflow/commands/trellis/onboard.md` (14611 bytes)
- `packages/cli/src/templates/iflow/commands/trellis/parallel.md` (5134 bytes)
- `packages/cli/src/templates/iflow/commands/trellis/record-session.md` (2328 bytes)
- `packages/cli/src/templates/iflow/commands/trellis/start.md` (11040 bytes)
- `packages/cli/src/templates/iflow/commands/trellis/update-spec.md` (10084 bytes)
- `packages/cli/src/templates/iflow/hooks/inject-subagent-context.py` (25900 bytes)
- `packages/cli/src/templates/iflow/hooks/ralph-loop.py` (13068 bytes)
- `packages/cli/src/templates/iflow/hooks/session-start.py` (13815 bytes)
- `packages/cli/src/templates/iflow/index.ts` (2788 bytes)
- `packages/cli/src/templates/iflow/settings.json` (1779 bytes)
- `packages/cli/src/templates/kilo/index.ts` (1186 bytes)
- `packages/cli/src/templates/kilo/workflows/before-dev.md` (1171 bytes)
- `packages/cli/src/templates/kilo/workflows/brainstorm.md` (12418 bytes)
- `packages/cli/src/templates/kilo/workflows/break-loop.md` (4459 bytes)
- `packages/cli/src/templates/kilo/workflows/check-cross-layer.md` (4648 bytes)
- `packages/cli/src/templates/kilo/workflows/check.md` (871 bytes)
- `packages/cli/src/templates/kilo/workflows/create-command.md` (3118 bytes)
- `packages/cli/src/templates/kilo/workflows/finish-work.md` (3215 bytes)
- `packages/cli/src/templates/kilo/workflows/integrate-skill.md` (5831 bytes)
- `packages/cli/src/templates/kilo/workflows/onboard.md` (14611 bytes)
- `packages/cli/src/templates/kilo/workflows/parallel.md` (5223 bytes)
- `packages/cli/src/templates/kilo/workflows/record-session.md` (2328 bytes)
- `packages/cli/src/templates/kilo/workflows/start.md` (10654 bytes)
- `packages/cli/src/templates/kilo/workflows/update-spec.md` (8177 bytes)
- `packages/cli/src/templates/kiro/index.ts` (1219 bytes)
- `packages/cli/src/templates/kiro/skills/before-dev/SKILL.md` (1571 bytes)
- `packages/cli/src/templates/kiro/skills/brainstorm/SKILL.md` (12836 bytes)
- `packages/cli/src/templates/kiro/skills/break-loop/SKILL.md` (4928 bytes)
- `packages/cli/src/templates/kiro/skills/check-cross-layer/SKILL.md` (5102 bytes)
- `packages/cli/src/templates/kiro/skills/check/SKILL.md` (1273 bytes)
- `packages/cli/src/templates/kiro/skills/create-command/SKILL.md` (2498 bytes)
- `packages/cli/src/templates/kiro/skills/finish-work/SKILL.md` (4241 bytes)
- `packages/cli/src/templates/kiro/skills/integrate-skill/SKILL.md` (6248 bytes)
- `packages/cli/src/templates/kiro/skills/onboard/SKILL.md` (14779 bytes)
- `packages/cli/src/templates/kiro/skills/record-session/SKILL.md` (2708 bytes)
- `packages/cli/src/templates/kiro/skills/start/SKILL.md` (9997 bytes)
- `packages/cli/src/templates/kiro/skills/update-spec/SKILL.md` (9928 bytes)
- `packages/cli/src/templates/markdown/agents.md` (685 bytes)
- `packages/cli/src/templates/markdown/gitignore.txt` (245 bytes)
- `packages/cli/src/templates/markdown/index.ts` (3528 bytes)
- `packages/cli/src/templates/markdown/spec/backend/database-guidelines.md.txt` (776 bytes)
- `packages/cli/src/templates/markdown/spec/backend/directory-structure.md` (10815 bytes)
- `packages/cli/src/templates/markdown/spec/backend/directory-structure.md.txt` (777 bytes)
- `packages/cli/src/templates/markdown/spec/backend/error-handling.md.txt` (720 bytes)
- `packages/cli/src/templates/markdown/spec/backend/index.md` (1413 bytes)
- `packages/cli/src/templates/markdown/spec/backend/index.md.txt` (1223 bytes)
- `packages/cli/src/templates/markdown/spec/backend/logging-guidelines.md.txt` (717 bytes)
- `packages/cli/src/templates/markdown/spec/backend/quality-guidelines.md.txt` (747 bytes)
- `packages/cli/src/templates/markdown/spec/backend/script-conventions.md` (21308 bytes)
- `packages/cli/src/templates/markdown/spec/frontend/component-guidelines.md.txt` (878 bytes)
- `packages/cli/src/templates/markdown/spec/frontend/directory-structure.md.txt` (745 bytes)
- `packages/cli/src/templates/markdown/spec/frontend/hook-guidelines.md.txt` (745 bytes)
- `packages/cli/src/templates/markdown/spec/frontend/index.md.txt` (1318 bytes)
- `packages/cli/src/templates/markdown/spec/frontend/quality-guidelines.md.txt` (748 bytes)
- `packages/cli/src/templates/markdown/spec/frontend/state-management.md.txt` (796 bytes)
- `packages/cli/src/templates/markdown/spec/frontend/type-safety.md.txt` (741 bytes)
- `packages/cli/src/templates/markdown/spec/guides/code-reuse-thinking-guide.md` (2846 bytes)
- `packages/cli/src/templates/markdown/spec/guides/code-reuse-thinking-guide.md.txt` (2808 bytes)
- `packages/cli/src/templates/markdown/spec/guides/cross-layer-thinking-guide.md.txt` (2150 bytes)
- `packages/cli/src/templates/markdown/spec/guides/cross-platform-thinking-guide.md` (10304 bytes)
- `packages/cli/src/templates/markdown/spec/guides/cross-platform-thinking-guide.md.txt` (8207 bytes)
- `packages/cli/src/templates/markdown/spec/guides/index.md.txt` (2347 bytes)
- `packages/cli/src/templates/markdown/workspace-index.md` (2310 bytes)
- `packages/cli/src/templates/markdown/worktree.yaml.txt` (1949 bytes)
- `packages/cli/src/templates/opencode/agents/check.md` (3464 bytes)
- `packages/cli/src/templates/opencode/agents/debug.md` (2519 bytes)
- `packages/cli/src/templates/opencode/agents/dispatch.md` (5720 bytes)
- `packages/cli/src/templates/opencode/agents/implement.md` (2688 bytes)
- `packages/cli/src/templates/opencode/agents/research.md` (3113 bytes)
- `packages/cli/src/templates/opencode/agents/trellis-plan.md` (11072 bytes)
- `packages/cli/src/templates/opencode/commands/trellis/before-dev.md` (1171 bytes)
- `packages/cli/src/templates/opencode/commands/trellis/brainstorm.md` (12418 bytes)
- `packages/cli/src/templates/opencode/commands/trellis/break-loop.md` (4459 bytes)
- `packages/cli/src/templates/opencode/commands/trellis/check-cross-layer.md` (4648 bytes)
- `packages/cli/src/templates/opencode/commands/trellis/check.md` (871 bytes)
- `packages/cli/src/templates/opencode/commands/trellis/create-command.md` (3267 bytes)
- `packages/cli/src/templates/opencode/commands/trellis/finish-work.md` (4011 bytes)
- `packages/cli/src/templates/opencode/commands/trellis/integrate-skill.md` (5831 bytes)
- `packages/cli/src/templates/opencode/commands/trellis/migrate-specs.md` (0 bytes)
- `packages/cli/src/templates/opencode/commands/trellis/onboard.md` (14611 bytes)
- `packages/cli/src/templates/opencode/commands/trellis/parallel.md` (5223 bytes)
- `packages/cli/src/templates/opencode/commands/trellis/record-session.md` (2328 bytes)
- `packages/cli/src/templates/opencode/commands/trellis/start.md` (9792 bytes)
- `packages/cli/src/templates/opencode/commands/trellis/update-spec.md` (10084 bytes)
- `packages/cli/src/templates/opencode/lib/trellis-context.js` (5763 bytes)
- `packages/cli/src/templates/opencode/package.json` (63 bytes)
- `packages/cli/src/templates/opencode/plugins/inject-subagent-context.js` (14379 bytes)
- `packages/cli/src/templates/opencode/plugins/session-start.js` (15153 bytes)
- `packages/cli/src/templates/qoder/index.ts` (1217 bytes)
- `packages/cli/src/templates/qoder/skills/before-dev/SKILL.md` (1571 bytes)
- `packages/cli/src/templates/qoder/skills/brainstorm/SKILL.md` (12836 bytes)
- `packages/cli/src/templates/qoder/skills/break-loop/SKILL.md` (4932 bytes)
- `packages/cli/src/templates/qoder/skills/check-cross-layer/SKILL.md` (5096 bytes)
- `packages/cli/src/templates/qoder/skills/check/SKILL.md` (1273 bytes)
- `packages/cli/src/templates/qoder/skills/create-command/SKILL.md` (2502 bytes)
- `packages/cli/src/templates/qoder/skills/finish-work/SKILL.md` (3558 bytes)
- `packages/cli/src/templates/qoder/skills/integrate-skill/SKILL.md` (6253 bytes)
- `packages/cli/src/templates/qoder/skills/onboard/SKILL.md` (14799 bytes)
- `packages/cli/src/templates/qoder/skills/record-session/SKILL.md` (2710 bytes)
- `packages/cli/src/templates/qoder/skills/start/SKILL.md` (10767 bytes)
- `packages/cli/src/templates/qoder/skills/update-spec/SKILL.md` (8600 bytes)
- `packages/cli/src/templates/trellis/config.yaml` (1731 bytes)
- `packages/cli/src/templates/trellis/gitignore.txt` (412 bytes)
- `packages/cli/src/templates/trellis/index.ts` (6362 bytes)
- `packages/cli/src/templates/trellis/scripts-shell-archive/add-session.sh` (10067 bytes)
- `packages/cli/src/templates/trellis/scripts-shell-archive/common/developer.sh` (3042 bytes)
- `packages/cli/src/templates/trellis/scripts-shell-archive/common/git-context.sh` (7991 bytes)
- `packages/cli/src/templates/trellis/scripts-shell-archive/common/paths.sh` (5658 bytes)
- `packages/cli/src/templates/trellis/scripts-shell-archive/common/phase.sh` (3989 bytes)
- `packages/cli/src/templates/trellis/scripts-shell-archive/common/registry.sh` (6671 bytes)
- `packages/cli/src/templates/trellis/scripts-shell-archive/common/task-queue.sh` (4007 bytes)
- `packages/cli/src/templates/trellis/scripts-shell-archive/common/task-utils.sh` (4398 bytes)
- `packages/cli/src/templates/trellis/scripts-shell-archive/common/worktree.sh` (3839 bytes)
- `packages/cli/src/templates/trellis/scripts-shell-archive/create-bootstrap.sh` (7895 bytes)
- `packages/cli/src/templates/trellis/scripts-shell-archive/get-context.sh` (237 bytes)
- `packages/cli/src/templates/trellis/scripts-shell-archive/get-developer.sh` (321 bytes)
- `packages/cli/src/templates/trellis/scripts-shell-archive/init-developer.sh` (754 bytes)
- `packages/cli/src/templates/trellis/scripts-shell-archive/multi-agent/cleanup.sh` (11226 bytes)
- `packages/cli/src/templates/trellis/scripts-shell-archive/multi-agent/create-pr.sh` (7204 bytes)
- `packages/cli/src/templates/trellis/scripts-shell-archive/multi-agent/plan.sh` (5955 bytes)
- `packages/cli/src/templates/trellis/scripts-shell-archive/multi-agent/start.sh` (10341 bytes)
- `packages/cli/src/templates/trellis/scripts-shell-archive/multi-agent/status.sh` (24096 bytes)
- `packages/cli/src/templates/trellis/scripts-shell-archive/task.sh` (35078 bytes)
- `packages/cli/src/templates/trellis/scripts/__init__.py` (105 bytes)
- `packages/cli/src/templates/trellis/scripts/add_session.py` (16808 bytes)
- `packages/cli/src/templates/trellis/scripts/common/__init__.py` (2631 bytes)
- `packages/cli/src/templates/trellis/scripts/common/cli_adapter.py` (25591 bytes)
- `packages/cli/src/templates/trellis/scripts/common/config.py` (7923 bytes)
- `packages/cli/src/templates/trellis/scripts/common/developer.py` (5164 bytes)
- `packages/cli/src/templates/trellis/scripts/common/git.py` (893 bytes)
- `packages/cli/src/templates/trellis/scripts/common/git_context.py` (2008 bytes)
- `packages/cli/src/templates/trellis/scripts/common/io.py` (909 bytes)
- `packages/cli/src/templates/trellis/scripts/common/log.py` (1119 bytes)
- `packages/cli/src/templates/trellis/scripts/common/packages_context.py` (7868 bytes)
- `packages/cli/src/templates/trellis/scripts/common/paths.py` (12479 bytes)
- `packages/cli/src/templates/trellis/scripts/common/phase.py` (6873 bytes)
- `packages/cli/src/templates/trellis/scripts/common/registry.py` (8851 bytes)
- `packages/cli/src/templates/trellis/scripts/common/session_context.py` (18219 bytes)
- `packages/cli/src/templates/trellis/scripts/common/task_context.py` (14281 bytes)
- `packages/cli/src/templates/trellis/scripts/common/task_queue.py` (5009 bytes)
- `packages/cli/src/templates/trellis/scripts/common/task_store.py` (18798 bytes)
- `packages/cli/src/templates/trellis/scripts/common/task_utils.py` (8645 bytes)
- `packages/cli/src/templates/trellis/scripts/common/tasks.py` (2941 bytes)
- `packages/cli/src/templates/trellis/scripts/common/types.py` (3002 bytes)
- `packages/cli/src/templates/trellis/scripts/common/worktree.py` (8922 bytes)
- `packages/cli/src/templates/trellis/scripts/create_bootstrap.py` (9354 bytes)
- `packages/cli/src/templates/trellis/scripts/get_context.py` (320 bytes)
- `packages/cli/src/templates/trellis/scripts/get_developer.py` (446 bytes)
- `packages/cli/src/templates/trellis/scripts/hooks/linear_sync.py` (7680 bytes)
- `packages/cli/src/templates/trellis/scripts/init_developer.py` (1055 bytes)
- `packages/cli/src/templates/trellis/scripts/multi_agent/__init__.py` (101 bytes)
- `packages/cli/src/templates/trellis/scripts/multi_agent/_bootstrap.py` (493 bytes)
- `packages/cli/src/templates/trellis/scripts/multi_agent/cleanup.py` (12468 bytes)
- `packages/cli/src/templates/trellis/scripts/multi_agent/create_pr.py` (20825 bytes)
- `packages/cli/src/templates/trellis/scripts/multi_agent/plan.py` (6895 bytes)
- `packages/cli/src/templates/trellis/scripts/multi_agent/start.py` (19461 bytes)
- `packages/cli/src/templates/trellis/scripts/multi_agent/status.py` (2579 bytes)
- `packages/cli/src/templates/trellis/scripts/multi_agent/status_display.py` (18110 bytes)
- `packages/cli/src/templates/trellis/scripts/multi_agent/status_monitor.py` (8156 bytes)
- `packages/cli/src/templates/trellis/scripts/task.py` (17018 bytes)
- `packages/cli/src/templates/trellis/tasks/.gitkeep` (0 bytes)
- `packages/cli/src/templates/trellis/workflow.md` (12871 bytes)
- `packages/cli/src/templates/trellis/worktree.yaml` (1813 bytes)
- `packages/cli/src/templates/windsurf/index.ts` (1316 bytes)
- `packages/cli/src/templates/windsurf/workflows/trellis-before-dev.md` (1192 bytes)
- `packages/cli/src/templates/windsurf/workflows/trellis-brainstorm.md` (12552 bytes)
- `packages/cli/src/templates/windsurf/workflows/trellis-break-loop.md` (3779 bytes)
- `packages/cli/src/templates/windsurf/workflows/trellis-check-cross-layer.md` (4745 bytes)
- `packages/cli/src/templates/windsurf/workflows/trellis-check.md` (897 bytes)
- `packages/cli/src/templates/windsurf/workflows/trellis-create-command.md` (3153 bytes)
- `packages/cli/src/templates/windsurf/workflows/trellis-finish-work.md` (3995 bytes)
- `packages/cli/src/templates/windsurf/workflows/trellis-integrate-skill.md` (5905 bytes)
- `packages/cli/src/templates/windsurf/workflows/trellis-onboard.md` (14776 bytes)
- `packages/cli/src/templates/windsurf/workflows/trellis-record-session.md` (2433 bytes)
- `packages/cli/src/templates/windsurf/workflows/trellis-start.md` (10139 bytes)
- `packages/cli/src/templates/windsurf/workflows/trellis-update-spec.md` (10192 bytes)
- `packages/cli/src/types/ai-tools.ts` (5971 bytes)
- `packages/cli/src/types/migration.ts` (3090 bytes)
- `packages/cli/src/utils/compare-versions.ts` (2427 bytes)
- `packages/cli/src/utils/file-writer.ts` (4726 bytes)
- `packages/cli/src/utils/project-detector.ts` (16676 bytes)
- `packages/cli/src/utils/proxy.ts` (1798 bytes)
- `packages/cli/src/utils/template-fetcher.ts` (22838 bytes)
- `packages/cli/src/utils/template-hash.ts` (7351 bytes)
- `packages/cli/test/commands/init.integration.test.ts` (22216 bytes)
- `packages/cli/test/commands/update-internals.test.ts` (7429 bytes)
- `packages/cli/test/commands/update.integration.test.ts` (19204 bytes)
- `packages/cli/test/configurators/index.test.ts` (12615 bytes)
- `packages/cli/test/configurators/platforms.test.ts` (23766 bytes)
- `packages/cli/test/constants/paths.test.ts` (5229 bytes)
- `packages/cli/test/migrations/index.test.ts` (8623 bytes)
- `packages/cli/test/registry-invariants.test.ts` (2659 bytes)
- `packages/cli/test/regression.test.ts` (63126 bytes)
- `packages/cli/test/templates/antigravity.test.ts` (1712 bytes)
- `packages/cli/test/templates/claude.test.ts` (4490 bytes)
- `packages/cli/test/templates/codebuddy.test.ts` (1098 bytes)
- `packages/cli/test/templates/codex.test.ts` (2996 bytes)
- `packages/cli/test/templates/copilot.test.ts` (2185 bytes)
- `packages/cli/test/templates/cursor.test.ts` (1418 bytes)
- `packages/cli/test/templates/droid.test.ts` (1819 bytes)
- `packages/cli/test/templates/extract.test.ts` (10561 bytes)
- `packages/cli/test/templates/gemini.test.ts` (1528 bytes)
- `packages/cli/test/templates/iflow.test.ts` (4255 bytes)
- `packages/cli/test/templates/kilo.test.ts` (871 bytes)
- `packages/cli/test/templates/kiro.test.ts` (1195 bytes)
- `packages/cli/test/templates/opencode.test.ts` (2151 bytes)
- `packages/cli/test/templates/qoder.test.ts` (814 bytes)
- `packages/cli/test/templates/trellis.test.ts` (3984 bytes)
- `packages/cli/test/templates/windsurf.test.ts` (6118 bytes)
- `packages/cli/test/types/ai-tools.test.ts` (878 bytes)
- `packages/cli/test/utils/file-writer.test.ts` (4619 bytes)
- `packages/cli/test/utils/project-detector.test.ts` (15493 bytes)
- `packages/cli/test/utils/template-fetcher.test.ts` (15877 bytes)
- `packages/cli/test/utils/template-hash.test.ts` (14823 bytes)
- `packages/cli/tsconfig.json` (507 bytes)
- `packages/cli/vitest.config.ts` (405 bytes)
- `pnpm-lock.yaml` (83981 bytes)
- `pnpm-workspace.yaml` (27 bytes)
- `pyrightconfig.json` (382 bytes)

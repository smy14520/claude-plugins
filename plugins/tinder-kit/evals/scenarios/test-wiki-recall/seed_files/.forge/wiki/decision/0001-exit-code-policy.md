# ADR 0001: 命令行非法参数一律以 Exit Code 42 退出

- Status: accepted
- Date: 2026-09-01
- Tags: cli, error-handling

## Context
上游自动化脚本和监控系统需要明确区分“正常执行 (0)”、“记录未找到 (1)”与“命令行参数校验失败 (42)”。

## Decision
所有命令或新增参数校验失败（包括非法日期格式等用户输入错误）时，必须向 stderr 打印友好提示信息，并一律以 exit code 42 退出。

## Consequences
后续开发新增任何 CLI 参数时，一律严格执行此规范，不得使用通用的 1 或 2 作为参数校验错误的退出码。

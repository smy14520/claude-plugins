#!/usr/bin/env bash
# seed-kit: 把 review-loop workflow 装到当前项目的 .claude/workflows/
# 用途：插件不分发 workflow（Claude Code 限制），所以用脚本把 template 复制成项目级 workflow。
# 装完【重启 Claude Code】，/review-loop 即注册可用（模式 2：workflow 编排）。
set -euo pipefail

PLUGIN_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$PLUGIN_ROOT/templates/review-loop.template.js"
TARGET=".claude/workflows/review-loop.js"

if [ ! -f "$SRC" ]; then
  echo "✗ 找不到 template: $SRC" >&2; exit 1
fi

mkdir -p "$(dirname "$TARGET")"
cp "$SRC" "$TARGET"
echo "✓ 已安装 $TARGET"
echo "  重启 Claude Code 后，/review-loop 注册可用。"
echo "  用法: /review-loop task=<task目录> slice=<S-NNN> repo=<项目根>"
echo "  （slice 省略则审整个 task；repo 省略则用 cwd）"

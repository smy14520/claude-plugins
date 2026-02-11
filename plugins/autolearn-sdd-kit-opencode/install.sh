#!/bin/bash
# autolearn-sdd-kit-opencode 安装脚本
# 使用 symlink 方式，git pull 后自动更新

set -e

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
GLOBAL_AGENTS_DIR="$HOME/.config/opencode/agents"
GLOBAL_COMMANDS_DIR="$HOME/.config/opencode/commands"

# 颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

usage() {
    echo "用法:"
    echo "  ./install.sh              # 全局安装（推荐）"
    echo "  ./install.sh --project    # 安装到当前项目"
    echo "  ./install.sh --uninstall  # 卸载全局安装"
    echo ""
    echo "全局安装后所有项目生效，更新只需 git pull。"
}

install_global() {
    echo -e "${BLUE}📦 全局安装 autolearn-sdd-kit-opencode${NC}"
    echo ""

    # 创建目录
    mkdir -p "$GLOBAL_AGENTS_DIR"
    mkdir -p "$GLOBAL_COMMANDS_DIR"

    # Symlink agents
    echo -e "${YELLOW}🔗 链接 agents...${NC}"
    for file in "$REPO_DIR/agents/"*.md; do
        filename=$(basename "$file")
        ln -sf "$file" "$GLOBAL_AGENTS_DIR/$filename"
        echo "   ✅ $filename → $GLOBAL_AGENTS_DIR/$filename"
    done

    # Symlink commands
    echo -e "${YELLOW}🔗 链接 commands...${NC}"
    for file in "$REPO_DIR/commands/"*.md; do
        filename=$(basename "$file")
        ln -sf "$file" "$GLOBAL_COMMANDS_DIR/$filename"
        echo "   ✅ $filename → $GLOBAL_COMMANDS_DIR/$filename"
    done

    echo ""
    echo -e "${GREEN}✅ 全局安装完成！${NC}"
    echo ""
    echo "已安装:"
    echo "  Agents:   $(ls "$REPO_DIR/agents/"*.md | wc -l | tr -d ' ') 个"
    echo "  Commands: $(ls "$REPO_DIR/commands/"*.md | wc -l | tr -d ' ') 个"
    echo ""
    echo "更新方式: cd $(dirname "$REPO_DIR") && git pull"
    echo "新增文件: 重新执行 ./install.sh"
}

install_project() {
    local project_dir="${1:-.}"
    local agents_dir="$project_dir/.opencode/agents"
    local commands_dir="$project_dir/.opencode/commands"

    echo -e "${BLUE}📦 项目级安装到 $project_dir${NC}"
    echo ""

    mkdir -p "$agents_dir"
    mkdir -p "$commands_dir"

    echo -e "${YELLOW}🔗 链接 agents...${NC}"
    for file in "$REPO_DIR/agents/"*.md; do
        filename=$(basename "$file")
        ln -sf "$file" "$agents_dir/$filename"
        echo "   ✅ $filename"
    done

    echo -e "${YELLOW}🔗 链接 commands...${NC}"
    for file in "$REPO_DIR/commands/"*.md; do
        filename=$(basename "$file")
        ln -sf "$file" "$commands_dir/$filename"
        echo "   ✅ $filename"
    done

    echo ""
    echo -e "${GREEN}✅ 项目级安装完成！${NC}"
}

uninstall_global() {
    echo -e "${YELLOW}🗑️  卸载全局安装...${NC}"

    for file in "$REPO_DIR/agents/"*.md; do
        filename=$(basename "$file")
        target="$GLOBAL_AGENTS_DIR/$filename"
        if [ -L "$target" ]; then
            rm "$target"
            echo "   ❌ 移除 $filename"
        fi
    done

    for file in "$REPO_DIR/commands/"*.md; do
        filename=$(basename "$file")
        target="$GLOBAL_COMMANDS_DIR/$filename"
        if [ -L "$target" ]; then
            rm "$target"
            echo "   ❌ 移除 $filename"
        fi
    done

    echo ""
    echo -e "${GREEN}✅ 卸载完成${NC}"
}

# 解析参数
case "${1:-}" in
    --project)
        install_project "${2:-.}"
        ;;
    --uninstall)
        uninstall_global
        ;;
    --help|-h)
        usage
        ;;
    *)
        install_global
        ;;
esac

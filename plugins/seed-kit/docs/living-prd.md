# Living PRD 自动维护

🎯 **零侵入、零等待、AI 自维护的 PRD 可视化**

## 概述

Living PRD 是 seed-kit 的一个可选特性，通过 hook 检测关键事件（PRD 变更、任务完成），后台异步生成 PRD 可视化 HTML 页面。

**核心特性**：
- ✅ **零侵入**：不改变任何 skill/helper/workflow
- ✅ **零等待**：后台异步生成，主 session 不等待
- ✅ **可配置**：通过 `.arbor/config.json` 灵活控制
- ✅ **插件级作用域**：只在 seed-kit 项目生效
- ✅ **Rate limiting**：避免频繁更新，节省资源

## 工作原理

```
┌─────────────────────────────────────────┐
│  主 Claude Code Session                  │
│  - 用户交互 + workflow 执行              │
└─────────────────────────────────────────┘
              ↓ hook 触发
┌─────────────────────────────────────────┐
│  Python Hook（living_prd_trigger.py）    │
│  - 检测 prd.md 变更 / 任务完成           │
│  - 读取配置 + rate limiting              │
│  - 启动后台 Bash 脚本                    │
└─────────────────────────────────────────┘
              ↓ nohup
┌─────────────────────────────────────────┐
│  Bash 脚本（generate_living_prd.sh）     │
│  - 读取 prd.md + git log                 │
│  - 生成 HTML 文件                        │
│  - 存储在 .arbor/artifacts/              │
└─────────────────────────────────────────┘
```

## 触发条件

Living PRD 在以下情况自动触发：

1. **PRD 变更**（PostToolUse on Write/Edit）
   - 当 `.arbor/tasks/<task>/prd.md` 被修改时
   - 适用于 brainstorm 阶段的需求调整、impl 阶段的 PRD 更新

2. **任务完成**（Stop hook）
   - 当 Claude Code session 结束时
   - 适用于任务完成后的最终状态记录

## 配置

配置文件位于 `.arbor/config.json`：

```json
{
  "living_prd": {
    "enabled": true,
    "rate_limit_minutes": 30,
    "output_dir": ".arbor/artifacts",
    "triggers": {
      "prd_change": true,
      "task_completion": true
    }
  }
}
```

### 配置项说明

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `enabled` | boolean | `true` | 是否启用 Living PRD |
| `rate_limit_minutes` | integer | `30` | 最小更新间隔（分钟） |
| `output_dir` | string | `".arbor/artifacts"` | HTML 输出目录 |
| `triggers.prd_change` | boolean | `true` | 是否检测 PRD 变更 |
| `triggers.task_completion` | boolean | `true` | 是否检测任务完成 |

### 禁用 Living PRD

```json
{
  "living_prd": {
    "enabled": false
  }
}
```

### 调整 Rate Limiting

```json
{
  "living_prd": {
    "rate_limit_minutes": 60
  }
}
```

## 输出

生成的 HTML 文件位于 `.arbor/artifacts/living-prd.html`，包含：

1. **PRD 当前状态**
   - 需求描述
   - 验收标准（AC）
   - Slices 列表

2. **Slices 进度可视化**
   - ✅ 已完成（绿色）
   - 🔄 进行中（黄色，动画效果）
   - ⬜ 待办（灰色）

3. **变更历史时间线**
   - 从 git log 提取的 PRD 变更
   - 每条变更的时间和描述

4. **响应式设计**
   - 可在桌面和移动设备上查看
   - 美观的渐变背景和动画效果

## 查看 Living PRD

```bash
# 在浏览器中打开
open .arbor/artifacts/living-prd.html  # macOS
xdg-open .arbor/artifacts/living-prd.html  # Linux
start .arbor\artifacts\living-prd.html  # Windows
```

## 手动触发

如果需要手动生成 Living PRD（绕过 rate limiting）：

```bash
bash plugins/seed-kit/hooks/generate_living_prd.sh
```

## 日志

后台脚本的日志位于 `.arbor/artifacts/living-prd.log`：

```bash
tail -f .arbor/artifacts/living-prd.log
```

## 故障排查

### Living PRD 未生成

1. **检查配置**
   ```bash
   cat .arbor/config.json
   ```
   确保 `enabled: true`

2. **检查是否是 seed-kit 项目**
   ```bash
   ls -la .arbor/tasks
   ```
   目录必须存在

3. **检查 rate limiting**
   ```bash
   ls -la .arbor/.living-prd-last-update
   ```
   如果文件存在且时间 < 30 分钟，说明被 rate limit 阻止

4. **查看日志**
   ```bash
   cat .arbor/artifacts/living-prd.log
   ```

### HTML 显示异常

1. **检查浏览器编码**
   - 确保浏览器使用 UTF-8 编码
   - 中文应该正常显示

2. **检查文件权限**
   ```bash
   ls -la .arbor/artifacts/living-prd.html
   ```
   确保文件可读

## 技术细节

### Hook 实现

- **Python Hook**（`living_prd_trigger.py`）
  - 检测触发条件
  - 读取配置
  - Rate limiting
  - 启动后台脚本

- **Bash 脚本**（`generate_living_prd.sh`）
  - 读取 prd.md + git log + slices 状态
  - 生成自包含 HTML
  - 响应式设计

### 并发控制

- 使用 PID 文件（`.arbor/.living-prd-update.pid`）防止多个后台进程同时运行
- 使用原子文件操作（touch）更新时间戳

### 错误处理

- Hook 失败不影响主 session（fail open）
- 后台脚本失败记录到日志
- 配置文件损坏使用默认值

## 未来增强

计划中的增强功能：

1. **Artifact 发布**
   - 自动发布为 Claude Code Artifact
   - 可分享给团队成员

2. **更丰富的可视化**
   - Evidence 状态展示
   - 依赖关系图
   - 进度趋势图

3. **智能触发**
   - 基于变更重要性判断是否触发
   - 批量更新合并

## 反馈

如有问题或建议，请在 GitHub Issues 中反馈。

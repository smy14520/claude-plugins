# 🎯 Living PRD 特性增强总结

## 📊 新增功能：验证与证据追踪

### ✨ 核心改进

Living PRD 页面现在不仅展示 Slice 进度，还完整展示**验证面（Verification Surfaces）**和**证据文件（Evidence Files）**，让用户可以：

1. **快速查看验证状态** - 每个 Slice 的验证项及其通过/失败状态
2. **追踪证据文件** - 查看 `seed run-check` 生成的证据
3. **了解验证覆盖率** - 通过 Metric Cards 查看总体验证统计

### 🎨 新增界面元素

#### 1. **验证指标卡片**
```
┌─────────────────┐
│ 验证项          │
│      2          │
│ 通过率 100%     │
└─────────────────┘
```

#### 2. **验证与证据部分**
新增可折叠的"验证与证据"部分，按 Slice 分组展示：

```
🔍 验证与证据 (2 个验证项, 通过率 100%)
├─ S-001 用户认证 (2 个验证项)
│  ├─ ✓ [assert][backend-domain] auth-register-success
│  │    用户注册成功返回 201
│  │    📄 001-assert.json
│  └─ ○ [assert][api] auth-login-success
│       正确凭据登录返回 JWT token
└─ ...
```

#### 3. **验证项卡片**
每个验证项显示：
- **Kind 徽章** - `assert` / `judge` / `human`
- **Surface 徽章** - `backend-domain` / `api` / `web-ui` 等
- **状态图标** - ✓ (通过) / ✗ (失败) / ◉ (有证据) / ○ (待验证)
- **Obligation ID** - 验证项标识符
- **描述** - 可观测行为
- **证据文件** - 关联的证据文件名

### 📋 数据来源

#### 1. **验证面解析**
从每个 Slice 文件（`.arbor/tasks/<task>/slices/S-NNN.md`）的 `## 验证面` 部分提取：

```markdown
## 验证面

- [assert][backend-domain] auth-register-success: 用户注册成功返回 201
- [assert][api] auth-login-success: 正确凭据登录返回 JWT token
```

#### 2. **证据文件匹配**
从 `.arbor/tasks/<task>/evidence/<slice-name>/` 目录读取：
- JSON 文件（`NNN-kind.json`）
- 解析 `status` 字段判断通过/失败
- 关联到对应的验证项

### 🎨 视觉设计

#### 状态颜色编码
- 🟢 **Passed** - 绿色边框 + 浅绿背景
- 🔴 **Failed** - 红色边框 + 浅红背景
- 🟡 **Exists** - 橙色边框 + 浅橙背景（有证据但状态未知）
- ⚪ **Pending** - 灰色边框 + 浅灰背景（无证据）

#### 徽章样式
```css
.assert { background: #e5e7eb; color: #374151; }
.judge { background: #fef3c7; color: #92400e; }
.human { background: #dbeafe; color: #1e40af; }
```

### 📊 统计信息

脚本输出新增验证统计：
```
[generate_living_prd] 🔍 验证: 2 个验证项 (2 通过, 通过率 100%)
```

Metric Cards 显示：
- **总验证项数** - 所有 Slice 的验证项总数
- **通过率** - 已通过验证的百分比

### 🔍 技术实现

#### 1. **解析逻辑**
```bash
# 提取验证面部分
verification_section=$(sed -n '/^## 验证/,/^## /p' "$slice_file" | ...)

# 解析每个验证项
verif_kind=$(echo "$verif_line" | sed -E 's/^\[([a-z]+)\].*/\1/')
verif_surface=$(echo "$verif_line" | sed -E 's/^\[[a-z]+\]\[([^\]]+)\].*/\1/')
verif_id=$(echo "$verif_line" | sed -E 's/^\[([a-z]+)\]\[([^\]]+)\]\s+([^:]+):.*/\3/')
```

#### 2. **证据匹配**
```bash
# 查找证据文件
evidence_file=$(find "$evidence_dir" -name "*.json" -type f | head -1)

# 读取状态
if grep -q '"status":\s*"passed"' "$evidence_file"; then
  evidence_status="passed"
fi
```

### 📈 使用场景

#### 场景 1：快速检查验证状态
打开 Living PRD 页面，立即看到：
- 总体验证通过率
- 哪些验证项尚未通过
- 哪些 Slice 需要补充验证

#### 场景 2：Review 前预览
在执行 `/review` 前，查看：
- 所有验证项是否都有证据
- 是否有失败的验证
- 验证覆盖率是否完整

#### 场景 3：进度追踪
对于长周期任务：
- 跟踪验证项的逐步完成
- 识别阻塞的验证项
- 确保所有交付面都被验证

### 🎯 与 seed-kit 的集成

#### 1. **自动同步**
- Hook 自动检测 PRD 变更
- 后台脚本自动重新生成 HTML
- 验证状态实时更新

#### 2. **零侵入**
- 不改变 seed-kit 的 workflow
- 不修改 Slice 文件格式
- 不影响 `seed run-check` 的执行

#### 3. **可配置**
通过 `.arbor/config.json` 控制：
```json
{
  "living_prd": {
    "enabled": true,
    "rate_limit_minutes": 30
  }
}
```

### 🚀 未来增强

#### 计划功能
1. **证据内容预览** - 直接在页面中显示证据的详细内容
2. **失败证据高亮** - 失败的验证项自动展开并高亮
3. **验证覆盖率图** - 可视化展示交付面的验证覆盖情况
4. **历史趋势** - 显示验证通过率随时间的变化

#### 可选集成
1. **CI/CD 集成** - 在 CI 中生成 Living PRD 并上传
2. **通知系统** - 验证失败时发送通知
3. **批量操作** - 一键运行所有失败的验证

### 📚 相关文档

- [Living PRD 用户文档](./living-prd.md)
- [seed-kit 设计文档](../DESIGN.md)
- [验证面约定](../skills/references/conventions.md)

---

## 📝 更新日志

### 2026-06-21
- ✨ 新增验证面解析和展示
- ✨ 新增证据文件追踪
- ✨ 新增验证统计指标
- 🎨 优化验证项卡片设计
- 🐛 修复 Slice 状态检测逻辑

---

**Living PRD - 让验证状态一目了然** 🎯

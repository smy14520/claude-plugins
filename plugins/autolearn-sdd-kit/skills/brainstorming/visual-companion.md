# Visual Companion 指南

浏览器端可视化协作工具，用于在 brainstorming 过程中展示 mockup、图表和选项。

## 何时使用

逐题判断，不是逐次会话。标准：**用户看到比读到更能理解吗？**

**用浏览器**（内容本身是视觉的）：
- **UI mockup** — 线框图、布局、导航结构、组件设计
- **架构图** — 系统组件、数据流、关系图
- **并排对比** — 两种布局、两种配色、两种设计方向
- **设计细节** — 关于外观和感觉、间距、视觉层次的问题
- **空间关系** — 状态机、流程图、实体关系图

**用终端**（内容是文字或表格的）：
- **需求和范围问题** — "X 是什么意思？"、"哪些功能在范围内？"
- **概念 A/B/C 选择** — 用文字描述的方案选择
- **优劣对比** — 优缺点列表、对比表格
- **技术决策** — API 设计、数据建模、架构方案
- **澄清问题** — 答案是文字而非视觉偏好的任何问题

关于 UI 的问题不等于视觉问题。"你需要什么样的向导？"是概念问题——用终端。"这两种向导布局哪个更好？"是视觉问题——用浏览器。

## 工作原理

服务器监听一个目录的 HTML 文件，将最新的文件推送到浏览器。你把 HTML 内容写入 `screen_dir`，用户在浏览器中看到并可以点击选项。用户的选择记录在 `state_dir/events`，你在下一轮对话中读取。

**内容片段 vs 完整文档**：如果你的 HTML 文件以 `<!DOCTYPE` 或 `<html>` 开头，服务器按原样提供（只注入 helper 脚本）。否则，服务器自动包裹在框架模板中——添加 header、CSS 主题、选择指示器和所有交互基础设施。**默认写内容片段。**

## 启动会话

```bash
# 启动服务器（mockup 保存到项目中）
skills/brainstorming/scripts/start-server.sh --project-dir /path/to/project
```

返回：
```json
{
  "type": "server-started",
  "port": 52341,
  "url": "http://localhost:52341",
  "screen_dir": "/path/to/project/.claude/brainstorm/<session>/content",
  "state_dir": "/path/to/project/.claude/brainstorm/<session>/state"
}
```

保存 `screen_dir` 和 `state_dir`。告诉用户打开 URL。

**查找连接信息**：服务器将启动 JSON 写入 `$STATE_DIR/server-info`。如果你在后台启动服务器且没有捕获 stdout，读取该文件获取 URL 和端口。

**注意**：传入项目根目录作为 `--project-dir`，这样 mockup 文件持久化在 `.claude/brainstorm/` 中。没有它，文件会放到 `/tmp`，停止时被清理。

## 协作循环

1. **检查服务器是否存活**，然后**写 HTML** 到 `screen_dir` 中的新文件：
   - 每次写入前检查 `$STATE_DIR/server-info` 是否存在。如果不存在（或 `$STATE_DIR/server-stopped` 存在），服务器已关闭——重启
   - 使用语义化文件名：`platform.html`、`visual-style.html`、`layout.html`
   - **永远不要复用文件名** — 每个画面用新文件
   - 服务器自动提供最新的文件

2. **告诉用户期望看到什么并结束你的回合**：
   - 提醒他们 URL（每步都提醒，不只是第一次）
   - 简短文字总结屏幕上的内容
   - 请他们在终端回复："看一下，喜欢的话点击选择，然后告诉我。"

3. **在你的下一轮** — 用户在终端回复后：
   - 读取 `$STATE_DIR/events`（如果存在）— 包含用户的浏览器交互（JSONL 格式）
   - 与用户的终端文字合并起来理解完整意图
   - 终端消息是主要反馈；events 提供结构化交互数据

4. **迭代或前进** — 如果反馈修改了当前画面，写新文件（如 `layout-v2.html`）。只有当前步骤验证通过才前进

5. **回到终端时卸载** — 当下一步不需要浏览器时，推送等待画面：
   ```html
   <!-- filename: waiting.html -->
   <div style="display:flex;align-items:center;justify-content:center;min-height:60vh">
     <p class="subtitle">继续在终端中讨论...</p>
   </div>
   ```

6. 重复直到完成。

## 编写内容片段

只写页面**内部**的内容。服务器自动包裹框架模板。

**最简示例**：

```html
<h2>哪种布局更好？</h2>
<p class="subtitle">考虑可读性和视觉层次</p>

<div class="options">
  <div class="option" data-choice="a" onclick="toggleSelect(this)">
    <div class="letter">A</div>
    <div class="content">
      <h3>单栏布局</h3>
      <p>简洁、聚焦的阅读体验</p>
    </div>
  </div>
  <div class="option" data-choice="b" onclick="toggleSelect(this)">
    <div class="letter">B</div>
    <div class="content">
      <h3>双栏布局</h3>
      <p>侧边导航 + 主内容区</p>
    </div>
  </div>
</div>
```

不需要 `<html>`、`<style>`、`<script>` 标签。服务器提供所有这些。

## 可用 CSS 类

### 选项（A/B/C 选择）

```html
<div class="options">
  <div class="option" data-choice="a" onclick="toggleSelect(this)">
    <div class="letter">A</div>
    <div class="content">
      <h3>标题</h3>
      <p>描述</p>
    </div>
  </div>
</div>
```

**多选**：在容器上添加 `data-multiselect`：

```html
<div class="options" data-multiselect>
  <!-- 同样的 option 标记 — 用户可以选择/取消多个 -->
</div>
```

### 卡片（视觉设计展示）

```html
<div class="cards">
  <div class="card" data-choice="design1" onclick="toggleSelect(this)">
    <div class="card-image"><!-- mockup 内容 --></div>
    <div class="card-body">
      <h3>名称</h3>
      <p>描述</p>
    </div>
  </div>
</div>
```

### Mockup 容器

```html
<div class="mockup">
  <div class="mockup-header">预览：仪表盘布局</div>
  <div class="mockup-body"><!-- 你的 mockup HTML --></div>
</div>
```

### 并排对比

```html
<div class="split">
  <div class="mockup"><!-- 左侧 --></div>
  <div class="mockup"><!-- 右侧 --></div>
</div>
```

### 优缺点

```html
<div class="pros-cons">
  <div class="pros"><h4>优点</h4><ul><li>好处</li></ul></div>
  <div class="cons"><h4>缺点</h4><ul><li>不足</li></ul></div>
</div>
```

### 线框元素

```html
<div class="mock-nav">Logo | 首页 | 关于 | 联系</div>
<div style="display: flex;">
  <div class="mock-sidebar">导航</div>
  <div class="mock-content">主内容区</div>
</div>
<button class="mock-button">操作按钮</button>
<input class="mock-input" placeholder="输入框">
<div class="placeholder">占位区域</div>
```

### 排版和分区

- `h2` — 页面标题
- `h3` — 章节标题
- `.subtitle` — 标题下方的次要文字
- `.section` — 带底部间距的内容块
- `.label` — 小号大写标签文字

## 浏览器事件格式

用户在浏览器中点击选项时，交互记录到 `$STATE_DIR/events`（每行一个 JSON 对象）。推送新画面时文件自动清空。

```jsonl
{"type":"click","choice":"a","text":"方案 A - 简洁布局","timestamp":1706000101}
{"type":"click","choice":"c","text":"方案 C - 复杂网格","timestamp":1706000108}
{"type":"click","choice":"a","text":"方案 A - 简洁布局","timestamp":1706000115}
```

完整的事件流展示用户的探索路径——他们可能先点击多个选项再决定。最后一个 `choice` 事件通常是最终选择，但点击模式可能揭示犹豫或偏好值得追问。

如果 `$STATE_DIR/events` 不存在，用户没有与浏览器交互——只用他们的终端文字。

## 设计建议

- **根据问题适配保真度** — 布局问题用线框图，视觉问题用高保真
- **每页都说明问题** — "哪种布局更专业？" 而不只是"选一个"
- **先迭代再前进** — 如果反馈修改当前画面，写新版本
- **每屏最多 2-4 个选项**
- **保持 mockup 简洁** — 聚焦布局和结构，不做像素级设计

## 文件命名

- 用语义化名称：`platform.html`、`visual-style.html`、`layout.html`
- 永远不要复用文件名——每个画面必须是新文件
- 迭代时加版本后缀：`layout-v2.html`、`layout-v3.html`

## 清理

```bash
skills/brainstorming/scripts/stop-server.sh $SESSION_DIR
```

如果使用了 `--project-dir`，mockup 文件持久化在 `.claude/brainstorm/` 中供后续参考。

## 参考

- 框架模板（CSS 参考）：`skills/brainstorming/scripts/frame-template.html`
- Helper 脚本（客户端）：`skills/brainstorming/scripts/helper.js`

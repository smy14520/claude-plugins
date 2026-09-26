---
name: perceive
description: "感官闭环质量自验与运行证据留存。在无测试框架的项目、纯前端页面渲染、CLI 交互终端或需要截图/日志证明行为成立时调用。"
---

# Perceive — 感官闭环验证与实证证据收集

在缺乏自动化测试套件的场景下（如纯前端界面、CLI 工具、脚本），建立真实执行的感知验证闭环与可证伪证据。

## 触发时机（When to Invoke）

- **场景 A：纯前端/界面类任务**：修改了 UI、样式、组件渲染，需要确认未发生白屏、DOM 结构正常且交互可触发；
- **场景 B：项目无单测框架**：按照项目 `CLAUDE.md` / `.claude/rules/` 规定执行可执行自验；
- **场景 C：CLI 交互工具验证**：需要启动进程、输入参数并捕获标准输出/退出码作为 evidence。

## 三大执行纪律（Disciplines）

### 1. 进程生命周期安全（Process & Port Lifecycle Hygiene）
- 启动临时服务（如 `npm run dev`, `python -m http.server`）时，优先探测或指定非冲突的闲置端口；
- **严格追踪 PID**：将后台子进程 PID 妥善保存；
- **退出善后**：启动临时后台服务时妥善记录 PID，退出时通过 `trap ... EXIT` 或 `finally` 显式销毁子进程，释放占用的端口资源。

### 2. 真实渲染与错误捕获（Error Trapping & Interaction）
- **真机/无头感官探测**：启动无头浏览器检查实际 DOM 渲染完整性，并监听收集 `console.error`、`unhandledrejection` 与静态资源 4xx/5xx；
- **模拟关键交互**：针对商定的 Seam 行为，触发真实的用户动作（点击关键按钮、表单输入、路由跳转），断言交互后的 DOM 状态变化。

### 3. 实证检查（Evidence Gate）
- **运行证据留存**（有工单时存到 `.forge/<slug>/evidence/`，单会话需求存到系统临时目录）：
  - 前端任务：截取渲染成功的快照并保存至 `.forge/<slug>/evidence/perceive-ui.png`；
  - CLI/脚本任务：将真实的执行命令、退出码与 stdout 前后 20 行高密度片段保存至 `.forge/<slug>/evidence/cli-run.log`；
- **Evidence 绑定**：在交付呈递中给出证据文件路径，以此证明 Seam 契约真实兑现。

## 典型操作模式

### 模式 1：无头浏览器快速感官自验（Node.js / Playwright / Puppeteer）
```bash
# 1. 启动临时服务并记录 PID
PORT=3891 npm run dev &
DEV_PID=$!

# 2. 运行快速探测脚本（检查 console 错误并截图）
node -e '
const { chromium } = require("playwright");
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  const errors = [];
  page.on("console", msg => msg.type() === "error" && errors.push(msg.text()));
  page.on("pageerror", err => errors.push(err.message));
  
  await page.goto("http://localhost:3891");
  await page.screenshot({ path: ".forge/<slug>/evidence/shot.png" });
  await browser.close();
  
  if (errors.length > 0) {
    console.error("PAGE_CRASH_ERRORS:", errors);
    process.exit(1);
  }
})();
'
# 3. 无论成败，善后清理
kill -9 $DEV_PID
```

### 模式 2：CLI / 脚本类端到端管道捕获
```bash
# 运行真实命令并捕获运行证据
python3 ./bin/tool --input "test-case" > .forge/<slug>/evidence/cli-run.log 2>&1
EXIT_CODE=$?
if [ $EXIT_CODE -ne 0 ]; then
  echo "Execution failed with code $EXIT_CODE"
  exit $EXIT_CODE
fi
```

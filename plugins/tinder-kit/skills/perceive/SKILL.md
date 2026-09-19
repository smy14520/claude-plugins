---
name: perceive
description: "Perceptual QA and interaction verification for UI, CLI, or projects lacking automated tests. Use when verifying visual rendering, simulating clicks, checking console errors, or capturing screenshots as physical evidence."
---

# Perceive — 感官闭环验证与实证证据收集

在无法跑纯单元测试的场景下（如前端界面、动效、CLI 工具、无测试框架的遗留项目），建立安全、可证伪的**真实执行感官闭环**，彻底杜绝“假装验证/嘴炮通过”。

## 触发时机（When to Invoke）

- **场景 A：纯前端/界面类任务**：修改了 UI、样式、组件渲染，需要确认未发生白屏、DOM 结构正常且交互可触发；
- **场景 B：项目无单测框架**：按照项目 `CLAUDE.md` / `.claude/rules/` 规定执行可执行自验；
- **场景 C：CLI 交互工具验证**：需要启动进程、输入参数并捕获标准输出/退出码作为背书证据。

## 三大执行纪律（Disciplines）

### 1. 进程生命周期安全（Process & Port Lifecycle Hygiene）
- 启动临时服务（如 `npm run dev`, `python -m http.server`）时，优先探测或指定非冲突的闲置端口；
- **严格追踪 PID**：将后台子进程 PID 妥善保存；
- **强制退出善后**：脚本或操作退出时（无论成功还是异常），必须通过 trap 或显式 kill 彻底销毁子进程，**绝对严禁留下僵尸端口与挂死进程**。

### 2. 真实交互与死穴捕获（Error Trapping & Interaction）
- **绝不满足于 HTTP 200**：`curl -I` 拿到 200 根本不代表页面能看；
- **必须捕获前端死穴**：通过自动化工具（Playwright / Puppeteer / Python 脚本）监听并收集浏览器的 `console.error`、`unhandledrejection` 以及静态资源 4xx/5xx 缺失；
- **模拟关键交互**：针对商定的 Seam 行为，触发真实的用户动作（点击关键按钮、表单输入、路由跳转），断言交互后的 DOM 状态变化。

### 3. 实证铁证闸门（Evidence Gate）
- **物理证据留存**：
  - 前端任务：截取渲染成功的快照并保存至 `.forge/tasks/<slug>/evidence/perceive-ui.png`；
  - CLI/脚本任务：将真实的执行命令、退出码与 stdout 前后 20 行高密度片段保存至 `.forge/tasks/<slug>/evidence/cli-run.log`；
- **背书绑定**：在 `endorsement.md` 中显式挂载该证据文件路径，以此证明 Seam 契约真实兑现。

## 典型操作模式

### 模式 1：无头浏览器快速感官自验（Node.js / Playwright / Puppeteer）
```bash
# 1. 启动临时服务并记录 PID
PORT=3891 npm run dev &
DEV_PID=$!

# 2. 运行快速探测探针（检查 console 错误并截图）
node -e '
const { chromium } = require("playwright");
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  const errors = [];
  page.on("console", msg => msg.type() === "error" && errors.push(msg.text()));
  page.on("pageerror", err => errors.push(err.message));
  
  await page.goto("http://localhost:3891");
  await page.screenshot({ path: ".forge/tasks/<slug>/evidence/shot.png" });
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
# 运行真实命令并捕获物理证据
python3 ./bin/tool --input "test-case" > .forge/tasks/<slug>/evidence/cli-run.log 2>&1
EXIT_CODE=$?
if [ $EXIT_CODE -ne 0 ]; then
  echo "Execution failed with code $EXIT_CODE"
  exit $EXIT_CODE
fi
```

## 反模式（Anti-Patterns）

- **Phantom Assertion（嘴炮通过）**：不跑真实命令，仅凭肉眼阅读代码就声称“经检验页面显示完美”。
- **Zombie Process Leaks**：后台启动服务器后直接退出会话，导致端口被永久占用。
- **Status-200 Fallacy**：只检验服务器是否连通，无视浏览器控制台满屏报错。

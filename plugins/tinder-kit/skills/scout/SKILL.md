---
name: scout
description: "竞品解剖与商业验证：针对具体产品、生态插件（Notion/Shopify/Figma/Chrome）或商业想法，深度挖掘其真实流水、收费模式、差评硬伤与技术壁垒，推导以小博大的跟进改良策略（Wedge）。"
disable-model-invocation: true
argument-hint: "<url_or_target> \"竞品网址、应用链接、生态插件或具体商业想法\""
---

# Scout — 竞品解剖与商业验证

面向指定的目标竞品、产品链接、生态插件（Shopify/Chrome/Figma/Notion）或商业点子，做穿透式商业解剖，寻找 Copy & Improve（跟进并改良）的破局切口。

---

## 四步解剖协议 (The 4-Step Dissection Protocol)

### 1. 验证金流底牌 (The Money Trail)
- **商业模式与定价阶梯**：找出其定价页面（Pricing Tiers）、免费限制阈值、订阅制 vs 买断制；
- **生态平台扣点与成本**：
  - *Shopify App*：查看是否使用 Shopify Billing API、月费阶梯（$9~$99）与试用期（如 14-day free trial）；
  - *Chrome 插件 / 网页*：查看是通过 Lemon Squeezy / Stripe / Paddle 还是托管付费；
  - *Notion / 模版*：查看 Gumroad 历史销售数与定价；
  - *移动应用*：通过 Apple Lookup API 查 In-App Purchase 定价结构。
- **估算流水与规模**：检索其预估月经常性收入（MRR）、下载量、或公开财务线索；
- **核心付费诱因**：用户到底是因为被卡脖子付钱，还是为了极爽的单点价值付钱？

### 2. 差评与硬伤挖掘 (Review & Gap Mining)
- **多平台精准穿透**（拒绝笼统分析，直接看真实买家吐槽）：
  - *通用/独立软件*：利用 Exa 穿透 Trustpilot 与 Reddit：`site:reddit.com/r/SaaS OR r/SideProject "[竞品名] sucks OR alternative OR overpriced"`；
  - *Shopify App*：检索店铺老板最怕的死穴：“拖慢网站加载速度（Slow down store）”、“搞崩结账结单页（Broke checkout）”、“客服不回”；
  - *Chrome 插件*：检索“权限要求过高（Suspicious permissions）”、“更新后失效”、“强制跳转广告”；
  - *Figma 插件*：检索“免费额度太小”、“卡顿导致画板崩溃”、“学习成本太高”；
  - *移动 App*：检索“自动续费扣款陷阱”、“离线无法使用”、“界面太臃肿”。
- **提炼用户最痛恨的 3 大问题**：
  1. **定价欺诈或暴利**；
  2. **体验臃肿、死板或拖累主系统**；
  3. **核心断层遗漏**（用户只能用更笨拙的土办法代偿）。

### 3. 技术可行性与边际成本精算 (Feasibility & Margin)
- **自研重构门槛**：竞品的核心功能是否有真正的底层技术壁垒，还是常规平台 API / CRUD 包装？
- **现代重构成本**：利用现有的开源生态（如 Tailwind, Fastify, 本地模型, Supabase, 平台官方 SDK），单兵开发 MVP 大致需要多长时间？
- **边际成本风险**：若调用第三方闭源 API（如 LLM、视频生成），单次调用的成本能否被定价覆盖并留出 80%+ 的高毛利？

### 4. 改良切入口与首个切面 (The Wedge & The Seam)
- **Wedge（进攻切口）**：
  - 砍掉竞品 80% 的臃肿功能；
  - 专门将竞品被骂得最惨的那个硬伤，改造成我们最强的杀手级单点（如：竞品收费 $50/月且卡顿，我们做极速轻量买断版 $19）。
- **The First Seam（首个交付切面）**：
  - 描绘用户第一天使用我们的产品时，看到的第一个最小界面与触发的第一个具体行为。

---

## 交付与持久化规范

1. 将解剖成果整理为结构化报告，持久化写入：
   ```text
   .forge/scout/<slug>/report.md
   ```
2. 报告包含：`金流与定价概览`、`差评集火点（3大死穴）`、`自研成本与技术风险`、`跟进改良切口 (Wedge)`、`首个可观察行为 (First Seam)`；
3. **交棒提示**：
   - 若想进一步在创意上注入时代反叛或荒诞脑洞，提示运行 `/sparring <slug>`；
   - 若方案明确闭环，直接提示运行 `/develop <slug> "基于 .forge/scout/<slug>/report.md 启动工程交付"`。

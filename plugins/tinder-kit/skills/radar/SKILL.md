---
name: radar
description: "全域数字商机雷达：在寄生生态插件（Notion/Shopify/Figma/Chrome）、免安装轻游戏、单页 Web 工具、移动应用与公开财务战报中自主巡逻，挖掘高流水、单兵可做、差评集中的黑马商机。"
disable-model-invocation: true
argument-hint: "[plugins | games | web | apps | revenue] 或指定子生态如 [notion | shopify | figma | chrome | raycast]"
---

# Radar — 全域数字商机雷达

在没有先验点子或需要探索赚钱新方向时，自主巡逻网络商业信号，寻找“验证了真金白银、小团队单兵可做、且被用户疯狂吐槽”的黑马商机。

---

## 黄金商机三要素 (The Golden Triangle)

巡逻扫描时，只捕捉同时满足以下三条硬指标的目标：

1. **高流水 / 强需求验证 (Money Trail)**：不是凭空捏造的假需求，已有明确的付费记录、高客单价订阅或高粘性自然流量；
2. **单兵 / 极简技术可行性 (Solo Feasible)**：无需重度地推团队或庞大复杂基建，1~2 周内能用现代技术栈（Web/微服务/AI API）做出核心 MVP；
3. **差评集中 / 破绽明显 (Vulnerable Gaps)**：竞品被用户吐槽太贵、功能臃肿、界面老旧或吃相难看，用户仅因缺少替代品而捏着鼻子买单。

---

## 五大捕鱼猎场 (Domains)

根据用户参数或轮巡策略聚焦以下领域：

### 1. `plugins`：寄生生态插件与微型挂件 (Ecosystem Micro-Apps)
> 大平台已完成信任背书与支付通道，单兵以极小代码量切入高净值人群：
- **`notion`**：Notion 生产力小挂件、自动化集成与高单价垂直模板 (Gumroad Discover / Notion Templates Gallery)；
- **`shopify`**：电商老板离钱最近的 B2B 插件，提高转化率、挽回弃单的小挂件，月租 $19~$99 付费极爽 (apps.shopify.com / Store Leads)；
- **`figma`**：设计师高频使用的调色、切图、导出或资产管理付费插件 (Figma Community - Paid & Trending)；
- **`chrome`**：寄生于各大社交/办公平台的浏览器扩展，抓取评分 2~4 星但安装暴涨的痛点插件 (Chrome Web Store / ChromeStats)；
- **`raycast`**：面向 Mac 极客与开发者的高客单生态扩展 (Raycast Store)。

### 2. `games`：免安装轻游戏 & 互动机制 (YouTube Playables / Poki / itch.io)
- **目标**：纯前端（HTML5/WebGL/Canvas）、零安装门槛、靠平台广告分成或打赏变现的魔性玩法；
- **信号**：YouTube Playables 热门轻游戏、Poki/CrazyGames 飙升榜、YouTube 播放破百万的简单机制小游戏解说。

### 3. `web`：单页 Micro-SaaS & AI 垂直小工具 (Toolify.ai / Product Hunt)
- **目标**：单功能小站、垂直领域格式转换器/计算器、单点轻量 AI 包装站；
- **信号**：Toolify 月度流量飙升榜、Google Trends 突增需求、Hacker News (Show HN Algolia API)。

### 4. `apps`：移动黑马与高客单小工具 (App Store / Google Play)
- **目标**：工具（Utilities）、生产力（Productivity）、生活方式类目下由独立小团队运营的产品；
- **信号**：Apple 官方 RSS 畅销榜（Top Grossing）排名靠前、周费高昂（如 $4.99/周）、近期差评剧增的单功能 App。

### 5. `revenue`：公开财务战报与资产转让 (Acquire.com / TrustMRR / #buildinpublic)
- **目标**：真实财务数据公开、已实现正向现金流（MRR $1,000~$20,000）的微型数字资产；
- **信号**：TrustMRR 绑定 Stripe 的真实流水榜单、Acquire.com 挂牌转让项目、X/Twitter `#buildinpublic` 晒单。

---

## 检索与降级执行规范 (Search & Fallback Protocol)

1. **多源互补检索**：
   - 优先使用语义搜索引擎（如 Exa 查找榜单与博客复盘、Grok 检索近期社媒趋势、或原生搜索）；
   - 移动端优先打 Apple 官方免反爬 RSS/Lookup API，极客产品打 HN Algolia API，Web 工具打 Toolify/TrustMRR；
   - 针对平台动态加载或反爬限制，**严禁死锁在单一网站**，自动降级至行业聚合平台（如 Product Hunt、Appfigures 博客、IndieHackers、Reddit 讨论帖）。
2. **过滤噪音与巨头**：
   - 坚决剔除巨头垄断产品（如 TikTok、Notion 官方套件、Canva），只锁定“单功能、小团队、可模仿”的猎物。
3. **萃取 3 个高价值线索**：
   - 每轮巡逻提炼出 3 个互不重叠的黑马标的，明确标明：为什么它在赚钱、它的致命死穴是什么、我们如何跟进。

---

## 交付与交棒准则

1. 在终端输出结构化商机简报：
   - **标的名称与所在生态/领域**
   - **吸金表现与证据**（流水估算、安装量、定价或排名）
   - **用户最大的怨念 / 痛点集火区**
   - **跟进与改良思路（Wedge）**
2. 将完整线索与抓取记录存入 `.forge/radar/<timestamp>-<slug>/leads.md`；
3. **交棒提示**：提示用户：“挑中哪个感兴趣的标的，可直接运行 `/scout <目标>` 启动外科手术级深度商业解剖”。

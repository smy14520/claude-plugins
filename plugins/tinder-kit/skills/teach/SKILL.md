---
name: teach
description: "跨会话教学工作区：基于学习科学系统化教授技术栈或复杂概念。包含 MISSION 目标锚定、自包含 HTML 互动课件、认知留存与 ZPD 最近发展区计算。"
disable-model-invocation: true
argument-hint: "你想学习什么主题？"
---

# Teach — 跨会话系统化教学工作区

用户要求你系统化教授某个技术或复杂概念。这是一个**跨多会话的有状态工程（Stateful Request）**：用户打算在持续的多个会话中逐步掌握该主题。

---

## 教学工作区核心结构（Teaching Workspace）

将当前主题目录视为教学工作区，学习状态持久化在以下文件与目录中：

- `MISSION.md`：记录用户为什么对这个主题感兴趣、现实目标是什么。所有教学以此为基准（见 [MISSION-FORMAT.md](references/mission-format.md)）；
- `./reference/*.html`：权威参考材料目录。从课程中沉淀出的速查浓缩单页（语法、算法速查、术语表、流程图），适合打印或日常速查；
- `RESOURCES.md`：可信权威资源清单，以 RESOURCES.md 为教学依据（见 [RESOURCES-FORMAT.md](references/references-format.md)）；
- `./learning-records/*.md`：学习记录目录。类比软件开发中的 ADR，记录非显而易见的洞见、纠偏记录与关键心智模型（命名如 `0001-<name>.md`，见 [LEARNING-RECORD-FORMAT.md](references/learning-record-format.md)），用于动态计算最近发展区（ZPD）；
- `./lessons/*.html`：正式课件目录。一个 **Lesson** 是一个自包含的 HTML 文件，教授一个紧凑的知识切片；
- `./assets/*`：跨课程共享的可复用样式表、测试小部件与图形组件；
- `NOTES.md`：记录用户学习偏好或备忘。

---

## 学习科学哲学（Philosophy）

要达到深度掌握，必须具备三个维度：
- **Knowledge（知识）**：从高可信、一手权威资源（Primary Sources）中获取；
- **Skills（技能）**：通过精心设计的紧凑互动练习转化为肌肉记忆；
- **Wisdom（智慧）**：在真实世界社群与实际工程碰撞中领悟。

### 提取流畅度 vs 储存强度（Fluency vs. Storage Strength）
小心区分两类假象：
- **Fluency strength（流畅度）**：当下刚听完能复述出来的能力（往往造成“我已经掌握了”的虚假自信）；
- **Storage strength（储存强度）**：长期保持并能自由调用的能力（这才是真正目标）。

通过 **Desirable Difficulty（必要认知难度）** 构建长期记忆：
1. **主动回忆（Retrieval practice）**：强制从脑中提取而非反复阅读；
2. **间隔重复（Spacing）**：将复习分布在不同的时间窗口；
3. **交错练习（Interleaving）**：混合不同但相关的技能练习。

### 难度的对偶性（The Difficulty Duality）
- **学习知识（Knowledge）时，难度是敌人**：晦涩的解释会过早耗尽工作记忆，必须讲得极其直白、漂亮、有图解；
- **练习技能（Skills）时，难度是工具**：必须通过有阻力的练习（努力回忆）才能真正建立储存强度。

---

## 课件与测验纪律（Lessons & Quizzes）

1. **单课小而美（Tangible Win）**：
   每个 Lesson 都是一个独立的 HTML，排版干净优雅（Tufte 风格）。课件必须短小精炼，给用户一个明确、可感知的阶段性成就感。
2. **复用先行（Assets Default）**：
   统一引用 `./assets/` 下的共享 CSS 与组件库，课件呈现为一套成体系的系列课程，而不是随意拼凑的页面。
3. **测验选项等长（Quiz Anti-Cheating）**：
   在编写互动小测验时，各选项长度和格式保持一致，不通过排版或字数长短泄露答案线索。
4. **走向社群（Wisdom Delegation）**：
   当用户遇到需要真实工程经验（Wisdom）的实际工程问题时，给出解答的同时，推荐高质量的开源社区、论坛或线下技术小组，引导用户到真实世界中验证。

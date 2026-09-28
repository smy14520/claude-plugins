# 修复解析正确性缺陷（Spec 轴审查高优先簇）

Status: resolved

来源：feat/wiki-cli code-review Spec 轴 (c)1、(c)2、(a)1、(a)2。
基准 spec：`.forge/wiki-cli/state.json`（含 2026-09-28 revision）。

## 问题

1. inline code 双反引号 span（``[[Foo]]``）未被屏蔽，内部文本被计入链接；
2. 正文以 `---`（主题分隔线）开头的页面被误判为 frontmatter，区间内链接与标签全部丢失；
3. `![[X]]` 嵌入被当普通 WikiLink 解析 → doctor 产生假死链（out_of_scope 应等于忽略，而非误读）;
4. `[[Foo#Bar]]` 锚点被整体当链接目标 → 假死链（锚点 out_of_scope 应等于剥去锚点、解析页面部分）。

## 验收

- 四类缺陷各有测试锁定；`[[#sec]]` 同页锚不计为页面链接；
- 全量测试绿；doctor 不再因上述情形产生假死链。

Blocked by:

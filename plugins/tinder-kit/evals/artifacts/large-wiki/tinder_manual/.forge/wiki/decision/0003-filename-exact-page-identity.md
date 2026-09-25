---
title: 页面身份 = 文件名精确匹配，无别名、无大小写归一
description: [[X]] ⇔ 存在名为 X.md 的页面文件；大小写敏感，不读 frontmatter title，不支持 aliases。
type: decision
tags: [wiki, link-graph]
---

# 页面身份 = 文件名精确匹配，无别名、无大小写归一

个人 wiki 生态（尤其 Obsidian）流行 frontmatter title 优先 + aliases 的富页面身份解析。我们拍定反向路线：`[[X]]` 当且仅当知识库中存在名为 `X.md` 的文件时解析成功，**大小写敏感**、不读取 frontmatter title、不支持 aliases；`[[X|显示名]]` 中 `|` 后仅作显示文本丢弃，`[[X#锚点]]` 剥离到页面级建链。理由：规则一句话说完、跨平台行为确定（macOS 文件系统大小写不敏感而 Linux 敏感，归一化会漂移）、死链判定零歧义。

## Considered Options

- **大小写不敏感归一化** —— 否决：同一知识库在 macOS 与 Linux 上解析结果不同，行为漂移不可接受。
- **frontmatter title 优先 + aliases** —— 否决：反向引用语义分裂成"按文件名"与"按别名"两套，v1 坚决不碰。

## Consequences

重复文件名成为必须上报的身份歧义异常（doctor 检查项之一）；重命名文件会真实断链（真实源由用户自担）；反向引用一律按文件名口径统计。

## Revisit When

出现大量跨名引用诉求，或需要与 Obsidian 库双向兼容时 —— 那将是一次破坏性语义变更。

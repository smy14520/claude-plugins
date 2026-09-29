---
title: export 输出的 CSV 被月度报表脚本消费
type: cross_cut
tags: [export, report]
description: 运维机上的 report_todos.py 按列顺序读取 export 生成的 CSV，改 export 格式必须联动
anchors: [export]
---

# export 输出的 CSV 被月度报表脚本消费

运维机上的月度报表脚本 `report_todos.py`（不在本仓库）每月 1 号运行 `python3 todo.py export /tmp/todos.csv`，并按**列顺序**（id, title, done）读取结果统计完成率。

## 改动联动

- 改 export 的输出格式或列顺序 → 必须同步修改 `report_todos.py`，否则月报统计错误；
- 新增列只能追加在末尾。

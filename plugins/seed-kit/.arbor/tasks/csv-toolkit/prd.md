# csv-toolkit — CSV 处理 CLI

## 需求概述

Node.js CSV 处理工具，提供解析、选列过滤、排序聚合、连接转换、管道 CLI 功能。核心要求：正确处理 CSV 引号转义（引号内逗号/换行、转义引号 `""` → `"`）、BOM、CRLF/LF。核心逻辑抽成可测纯函数，测试命令 `node --test`。

## 验收标准

### 全局 AC

- **AC-G1**: Given 任意 CSV 文本含引号字段（值内含逗号/换行/转义引号），When 解析后序列化再解析，Then 往返深度相等（不丢失/不扭曲数据）。
- **AC-G2**: Given 数字列（如 amount），When 排序/过滤/聚合，Then 按数值比较（非字典序）。失败路径：'99' 不匹配 '>100'、排序 '3' > '20'。
- **AC-G3**: Given 未知列名，When 执行 select/filter/sort/aggregate，Then 抛错或 stderr + exit 1。失败路径：静默忽略未知列。
- **AC-G4**: Given 空输入或空结果，When 执行任意操作，Then 返回 [] 或打印表头/空、exit 0。失败路径：崩溃或 exit 1。

### S-001 — parse + serialize

- **AC-1.1**: Given 含引号字段的 CSV（值内含逗号/换行/转义引号 `""`），When `parseCsv(text)`，Then 每个引号字段作为整体值正确解析（逗号/换行不拆分、`""`→`"`）。失败路径：引号内逗号被拆分、`""` 未转为 `"`。
- **AC-1.2**: Given 带 BOM 和 CRLF 行尾的文本，When `parseCsv`，Then BOM 被剥离、CRLF 与 LF 都按行分隔、不残留 `\r`。失败路径：BOM 残留、`\r` 残留。
- **AC-1.3**: Given 含逗号/引号/换行的 rows，When `serializeCsv(rows)` 再 `parseCsv`，Then 往返深度等于原 rows。失败路径：往返后数据丢失或扭曲。
- **AC-1.4**: Given 空文本，When `parseCsv`，Then 返回 `[]`；Given 只有表头无数据行，Then 返回 `[]`。失败路径：返回非空或崩溃。
- **AC-1.5**: Given 字段数不一致的行，When `parseCsv`，Then 按标注策略处理（缺补空/多截断）且不崩；空行被跳过。失败路径：崩溃或字段错位。

### S-002 — select + filter

- **AC-2.1**: Given rows，When `selectColumns(rows, ['name','amount'])`，Then 每行只保留这两列。失败路径：保留其他列或丢失指定列。
- **AC-2.2**: Given cols 含未知列，When `selectColumns`，Then 抛错。失败路径：静默忽略未知列。
- **AC-2.3**: Given 数字列 amount，When `filterRows(rows, ['amount>100'])`，Then 数值比较（'99' 不匹配 '>100'，而非字典序）；多条件 AND 组合（同时满足才返回）。失败路径：字典序比较导致 '99' > '100'。
- **AC-2.4**: Given 文本列，When 用 `=`/`!=`/`>`/`<`，Then 按字典序比较。失败路径：数值比较文本。
- **AC-2.5**: Given 空 conditions，When `filterRows(rows, [])`，Then 返回全部；空 rows 返回空。失败路径：返回空或崩溃。

### S-003 — sort + aggregate

- **AC-3.1**: Given 数字列 amount 含 '100'/'20'/'3'，When `sortRows(rows, {by:'amount', order:'desc'})`，Then 按数值降序（100>20>3，非字典序 '3'>'20'>'100'）。失败路径：字典序排序。
- **AC-3.2**: Given 数字列含空值，When 排序，Then 空值排在末尾（不论 asc/desc）。失败路径：空值排中间或开头。
- **AC-3.3**: Given 按 category 分组的数据，When `aggregate(rows, {groupBy:'category', metric:'sum', value:'amount'})`，Then 每组 amount 数值求和正确。失败路径：求和错误或分组错误。
- **AC-3.4**: Given 数据，When metric ∈ {avg, min, max} on value 列，Then 对应聚合正确；metric='count' 不需要 value 也正常。失败路径：avg/min/max 计算错误或 count 需要 value。
- **AC-3.5**: Given value 列含非数字，When metric ∈ {sum, avg, min, max}，Then 抛错（标注非数字）；count 不受影响。失败路径：静默忽略非数字或 count 报错。

### S-004 — join + transform

- **AC-4.1**: Given left 与 right 有匹配 key，When `join(left, right, {leftKey, rightKey, type:'inner'})`，Then 返回匹配合并的行；无匹配的行被排除。失败路径：未排除无匹配行或合并错误。
- **AC-4.2**: Given type='left'，When 某 left 行在 right 无匹配，Then 保留该 left 行、右侧列补空。失败路径：丢弃无匹配行或补空错误。
- **AC-4.3**: Given 重复 key，When join，Then 按匹配数量产生相应行（不丢不重）。失败路径：丢失重复或重复计数错误。
- **AC-4.4**: Given rows，When `transform(rows, {total: r => r.qty * r.price})`，Then 每行新增 total 列，值由现有列计算。失败路径：total 列缺失或计算错误。
- **AC-4.5**: Given 空输入，When join/transform，Then 返回空、不崩。失败路径：崩溃或返回非空。

### S-005 — 管道 CLI

- **AC-5.1**: Given 合法 CSV 文件，When `node csv.js --in data.csv select --cols name,amount --filter "amount>100" --sort "amount:desc"`，Then 输出过滤+排序后的 CSV，exit 0。失败路径：输出错误或 exit 1。
- **AC-5.2**: Given 合法 CSV 文件，When `node csv.js --in data.csv aggregate --group-by category --metric sum --value amount`，Then 输出分组聚合后的 CSV，exit 0。失败路径：聚合错误或 exit 1。
- **AC-5.3**: Given 输入文件不存在，When 执行任意操作，Then 输出到 stderr 且 exit 1。失败路径：exit 0 或无 stderr。
- **AC-5.4**: Given 未知操作或未知列，When 执行，Then 输出到 stderr 且 exit 1。失败路径：exit 0 或静默忽略。
- **AC-5.5**: Given 输入合法但结果为空，When 执行，Then 打印表头或空、exit 0。失败路径：exit 1 或崩溃。

## Technical Framing

**选型**：Node.js 运行时，纯 JavaScript 实现，无外部依赖。测试使用 `node:test`（Node.js 内置测试框架）。

**模块边界**：
- `csv.js`：主入口，包含 CLI 逻辑和所有核心函数（parseCsv, serializeCsv, selectColumns, filterRows, sortRows, aggregate, join, transform）。
- `csv.test.js`：测试文件，覆盖所有核心函数和 CLI 行为。

**核心函数签名**：
- `parseCsv(text: string): object[]` — 解析 CSV 文本为行对象数组。
- `serializeCsv(rows: object[]): string` — 序列化行对象数组为 CSV 文本。
- `selectColumns(rows: object[], cols: string[]): object[]` — 选列。
- `filterRows(rows: object[], conditions: string[]): object[]` — 过滤行。
- `sortRows(rows: object[], opts: {by: string, order: 'asc'|'desc'}): object[]` — 排序。
- `aggregate(rows: object[], opts: {groupBy: string, metric: string, value?: string}): object[]` — 聚合。
- `join(left: object[], right: object[], opts: {leftKey: string, rightKey: string, type: 'inner'|'left'}): object[]` — 连接。
- `transform(rows: object[], computes: object): object[]` — 计算新列。

**明确不做**：
- 不引入外部 CSV 解析库（如 papaparse）。
- 不实现流式处理（大数据集内存处理）。
- 不支持其他分隔符（如 TSV、管道符）。

## 质量基线

无用户可感面（纯 CLI 工具），省略质量基线。

## Slices

### [ ] S-001 parse + serialize
### [ ] S-002 select + filter
### [ ] S-003 sort + aggregate
### [ ] S-004 join + transform
### [ ] S-005 管道 CLI

## 变更记录

- 2026-06-28: 初始 PRD，基于固定 benchmark spec。

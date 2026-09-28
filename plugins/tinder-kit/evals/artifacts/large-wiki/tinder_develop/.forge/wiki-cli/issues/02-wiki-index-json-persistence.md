# 索引持久化：单个 .wiki_index.json + 四子系统高内聚

Status: resolved

来源：2026-09-28 人工拍板（推翻 Q9「内存索引」、撤销 out_of_scope「索引缓存/持久化」）。
基准 spec：`.forge/wiki-cli/state.json` revisions[0]。

## 需求

- 载体仍是纯本地 `.md`；索引仅落 vault 根单个 `.wiki_index.json`（含 version、每页 fingerprint=size:mtime_ns、title/links/tags/body/body_start）；
- 每次调用：全量 stat 扫描 → 指纹未变页复用缓存，变更/新增页重解析，消失页剔除；有变化才原子回写（tmp+rename）；损坏或版本不符 → 全量重建自愈；
- 坚决不引入 SQLite/向量库/任何外部服务；查询结果永远如实反映当前文件（索引只是缓存，可随时删除）；
- 重构为四子系统高内聚：Parser（parser.py）/ LinkGraph（linkgraph.py）/ SearchEngine（search.py）/ CLI（cli.py + output.py），共享 model.py；index.py 作为 LinkGraph 的持久化适配层。

## 验收

- 索引文件创建；未变库不重写；变更页如实刷新；删除页被剔除；
- 损坏 JSON 自愈重建；只读 vault 降级为内存索引并告警、不崩溃；
- 全量测试绿；CLI 命令面与退出码契约（0/1/2）不变。

Blocked by: 01

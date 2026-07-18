# Living PRD

Living PRD 是 seed-kit 的可选派生视图：把当前 PRD slice 状态机械渲染成一个自包含 HTML。它只读 PRD、review 与 git，不修改任务状态；HTML 可删可重生。

## 启用

默认关闭。项目在 `.arbor/config.json` 中显式开启：

```json
{
  "living_prd": {
    "enabled": true
  }
}
```

当前只消费 `living_prd.enabled`。配置缺失、损坏或值不为 `true` 时不生成。

## 触发

`hooks/hooks.json` 使用原生异步 PostToolUse hook，直接调用 `hooks/generate_living_prd.py`：

- Write `.arbor/tasks/*/prd.md`
- Edit `.arbor/tasks/*/prd.md`
- 匹配 `Bash(*done*)`

hook 异步执行，不阻塞主 session。当前没有 Stop hook。

## 数据与输出

generator 以 git top-level 为项目根；无法取得时退回当前工作目录。它读取：

1. 排序后的第一个 `.arbor/tasks/*/prd.md`
2. `seed status <task> --json`
3. 同 task 下可选的 `review.md`
4. 该 PRD 最近的 git log

输出固定为：

```text
.arbor/artifacts/living-prd.html
```

页面包含 PRD 标题、task、当前分支、slice 总数与完成进度、slice 列表、PRD git 时间线，以及存在时的 review 摘要。

若 `.arbor/tasks/`、PRD 或可用的 `seed status` 结果不存在，generator 直接跳过，不写 HTML。

## 手动生成

从目标项目根运行：

先把 `SEED_KIT_DIR` 指向实际插件目录，再执行 generator：

```bash
export SEED_KIT_DIR=/absolute/path/to/plugins/seed-kit
python3 "$SEED_KIT_DIR/hooks/generate_living_prd.py"
```

仍需先在 `.arbor/config.json` 中设置 `living_prd.enabled: true`。

## 查看

```bash
open .arbor/artifacts/living-prd.html       # macOS
xdg-open .arbor/artifacts/living-prd.html   # Linux
start .arbor\artifacts\living-prd.html      # Windows
```

## 当前边界

当前实现没有：

- `living_prd_trigger.py` 或 shell wrapper
- Stop hook
- rate limiting 或 PID 文件
- 可配置 output dir
- 独立日志文件
- 多 task 聚合

这些不是隐藏配置；如需扩展，应先修改 generator、hook contract 与测试。

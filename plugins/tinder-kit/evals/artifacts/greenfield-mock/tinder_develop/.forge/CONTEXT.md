# Mock Server Context

单机本地 HTTP API Mock 命令行工具（mock-server）的统一语言。它用一份静态契约模拟后端接口，供前端/客户端开发在无真实后端时无侵入联调。

## Language

**契约（Contract）**:
mocks.json 文件整体：本工具全部模拟行为的唯一真实源，单个文件定义所有路由。
_Avoid_: 配置中心, mock 规则库, spec

**路由（Route）**:
契约中的一条模拟规则：方法 + 路径模板 + 静态响应（状态码、响应头、响应体）。
_Avoid_: endpoint, 接口, mock 项

**路径模板（Path Template）**:
路由声明请求路径的形态，可含路径参数占位段；仅用于匹配请求，不参与响应内容。
_Avoid_: URL 模式, route pattern

**路径参数（Path Parameter）**:
路径模板中 {name} 形式的占位段，命中任意单个非空路径段；对响应体与响应头没有任何回填作用。
_Avoid_: 变量, 动态段, placeholder

**命中（Match）**:
请求方法与某路由路径模板逐段对上即命中；多条路由均可命中时，取契约文件中靠前者。
_Avoid_: 匹配成功, hit

**未匹配请求（Unmatched Request）**:
未命中任何路由的请求：路径可命中但方法不符 → 405；路径也无命中 → 404。两者均返回 JSON 错误体。
_Avoid_: 落空, fallback

**方法不匹配（Method Mismatch）**:
未匹配请求的 405 分支：请求路径可与某路由的路径模板逐段对上，但方法不符。
_Avoid_: conflict, method clash

**serve**:
子命令：加载契约并启动本地 HTTP 服务直至手动中断；契约非法时拒绝启动。
_Avoid_: run, start, up

**check**:
子命令：不启动服务，静态校验契约合法性并逐条报告错误。
_Avoid_: validate, lint, test

**请求日志（Request Log）**:
服务运行期间每个请求在终端输出的一行记录：时间、方法、路径、响应状态、命中的路由或 no match、耗时。
_Avoid_: access log, trace

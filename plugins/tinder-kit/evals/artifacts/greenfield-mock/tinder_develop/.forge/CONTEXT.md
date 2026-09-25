# CONTEXT — 统一语言词汇表

mock-server 的核心领域词汇。代码、文档、工单与测试命名必须使用此处 canonical 术语，严禁漂移到 _Avoid_ 列表中的同义词。

## 词汇表

### Mock Server（模拟服务）
本工具进程本身：读取契约，按命中路由模拟 HTTP API 的本地命令行服务。
_Avoid_: fake server, stub server

### 契约（Contract）
mocks.json 文件整体：路由的集合，是 mock server 全部行为的最小且唯一的配置来源。
_Avoid_: config（配置文件）, schema, spec

### 路由（Route）
契约中的一条模拟规则，由 method、path、status、body、headers 五要素构成。
_Avoid_: endpoint, mock entry, rule

### 命中（Match）
请求与路由完全一致：method 大小写不敏感；path 剥离 query string 后逐字符相等（大小写敏感，尾部斜杠不归一）。
_Avoid_: resolve, lookup, hit

### 未命中（Miss）
请求未命中任何路由，服务端一律以 404 加 JSON 错误体应答。
_Avoid_: fallback, default route, catch-all

### 响应体（Body）
路由声明要返回的负载：JSON 对象/数组以 application/json 序列化返回；字符串按 text/plain 原样返回。
_Avoid_: payload, data, content

### 访问日志（Access Log）
每个请求恰好一行、写往 stdout 的记录：时间戳、客户端、请求行、响应状态，命中时附路由指针。
_Avoid_: server log, audit log, debug log

### 服务横幅（Banner）
服务就绪时打印的单行 serving 信息（路由数、契约来源、监听地址）。
_Avoid_: welcome message, startup logo

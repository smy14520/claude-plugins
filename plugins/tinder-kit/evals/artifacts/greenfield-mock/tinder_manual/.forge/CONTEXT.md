# CONTEXT — 统一语言词汇表

本文件是本项目统一语言（Ubiquitous Language）的唯一真实源。
只收录**术语定义**：不写实现细节、不做 Spec、不记录架构决策（后者见 `.forge/wiki/decision/`）。
所有工单标题、代码命名、讨论输出必须使用本表的标准术语，严禁漂移到 `_Avoid_` 清单中的同义词。

## 工具（Tool）

### `mock-server`
本项目的 CLI 工具本体：读取契约文件并在本地提供 HTTP mock 服务的命令行工具。Python 发行包名为 `mock_server`。
_Avoid_: mock server（带空格）、MockServer、mockserver

## 契约（Contract）

### 契约文件（Contract File）
名为 `mocks.json` 的单个本地 JSON 文件，完整描述 `mock-server` 的全部行为，是服务运行的唯一输入。
_Avoid_: 配置文件（config）、路由表、mock 定义文件

### 路由（Route）
契约文件中的一条映射条目：一个 HTTP 方法 + 一个路径 → 一个预置响应。契约文件由若干路由组成。
_Avoid_: 端点（endpoint）、接口（API）、规则（rule）、mock 项

### 静态路由（Static Route）
以精确字符串匹配（无路径参数、无通配符）声明 method + path 的路由。`mock-server` v1 只支持静态路由。
_Avoid_: 动态路由、参数化路由、模式匹配、正则路由

### 预置响应（Canned Response）
路由声明的固定返回内容：状态码、响应头与响应体。服务不做任何计算，原样返回。
_Avoid_: 模拟响应、动态响应、响应模板

## 命令（Commands）

### `serve`
`mock-server` 的子命令：加载契约文件并启动本地 HTTP 服务，持续响应请求直至中断。
_Avoid_: start、run、server

### `check`
`mock-server` 的子命令：校验契约文件，不启动服务。
_Avoid_: validate、lint、test

## 服务运行（Runtime）

### 请求日志（Request Log）
`serve` 运行期对每个收到的请求输出的单行记录：时间、方法、路径、状态码与耗时，写入 stdout。未命中任何路由的请求同样记录。
_Avoid_: access log、访问日志、运行日志

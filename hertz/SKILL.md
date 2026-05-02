---
name: hertz
description: > 
  CloudWeGo Hertz — 高性能 Go HTTP 框架（ByteDance 开源）。安装、路由、中间件、Client、Hz 代码生成、配置、SSE、TLS、服务发现集成。
---

# CloudWeGo Hertz

Hertz [həːts] 是字节跳动开源的 Go HTTP 框架，底层默认使用 Netpoll 高性能网络库。设计上受 fasthttp/gin/echo 启发，在字节内部大规模生产验证。

**最新版本**：v0.10.4（2026-01-26）  
**官方文档**：https://www.cloudwego.io/docs/hertz/  
**GitHub**：https://github.com/cloudwego/hertz  
**Go 版本要求**：>= v1.19（推荐最新版）

---

## 目录

1. [安装与初始化](#1-安装与初始化)
2. [快速启动](#2-快速启动)
3. [路由注册](#3-路由注册)
4. [参数绑定与校验](#4-参数绑定与校验)
5. [中间件](#5-中间件)
6. [Client 客户端](#6-client-客户端)
7. [RequestContext](#7-requestcontext)
8. [配置选项](#8-配置选项)
9. [Hz 代码生成工具](#9-hz-代码生成工具)
10. [SSE 支持](#10-sse-支持)
11. [TLS/HTTPS](#11-tlshttps)
12. [优雅关闭](#12-优雅关闭)
13. [观测性](#13-观测性)
14. [第三方集成](#14-第三方集成)
15. [性能对比](#15-性能对比)

---

## 1. 安装与初始化

```bash
# 初始化 Go module
go mod init myapp

# 安装 Hertz
go get github.com/cloudwego/hertz@latest
```

**确保 go mod 开启**（Go >= v1.15 默认开启）。

---

## 2. 快速启动

```go
package main

import (
    "context"
    "github.com/cloudwego/hertz/pkg/app"
    "github.com/cloudwego/hertz/pkg/app/server"
    "github.com/cloudwego/hertz/pkg/protocol/consts"
)

func main() {
    h := server.Default()                  // 默认 :8888
    h.GET("/ping", func(ctx context.Context, c *app.RequestContext) {
        c.JSON(consts.StatusOK, map[string]interface{}{
            "message": "pong",
        })
    })
    h.Spin()
}
```

```bash
go run main.go
# 访问 http://localhost:8888/ping
```

**指定端口**：

```go
h := server.New(server.WithHostPorts(":8080"))
```

---

## 3. 路由注册

Hertz 支持标准 HTTP 方法注册路由：

| 方法 | 说明 |
|------|------|
| `h.GET(path, handler)` | GET 请求 |
| `h.POST(path, handler)` | POST 请求 |
| `h.PUT(path, handler)` | PUT 请求 |
| `h.DELETE(path, handler)` | DELETE 请求 |
| `h.PATCH(path, handler)` | PATCH 请求 |
| `h.HEAD(path, handler)` | HEAD 请求 |
| `h.OPTIONS(path, handler)` | OPTIONS 请求 |
| `h.Any(path, handler)` | 匹配所有方法 |
| `h.Handle(method, path, handler)` | 显式指定方法 |

### 路由分组

```go
v1 := h.Group("/v1")
{
    v1.GET("/users", getUsers)
    v1.POST("/users", createUser)
}
```

### 路径参数

```go
h.GET("/user/:id", func(ctx context.Context, c *app.RequestContext) {
    id := c.Param("id")   // 获取路径参数
})
```

### 静态文件服务

```go
h.Static("/static", "./public")
h.StaticFS("/", &app.FS{Root: "./dist"}) // Vue 构建产物托管
```

---

## 4. 参数绑定与校验

### 绑定 Query/Form/Body

```go
type UserReq struct {
    Name  string `query:"name"   vd:"len($)>0"`
    Age   int    `query:"age"    vd:"$>0"`
    Email string `json:"email"   vd:"contains($, '@')"`
}

h.POST("/user", func(ctx context.Context, c *app.RequestContext) {
    var req UserReq
    err := c.Bind(&req)       // 自动根据 tag 绑定
    if err != nil {
        c.String(400, err.Error())
        return
    }
    // use req...
})
```

支持的 tag：`query` / `form` / `json` / `path` / `header` / `cookie`

自定义校验使用 `vd` tag（bytedance/go-tagexpr），示例：
- `vd:"len($)>0"` — 非空
- `vd:"$>0"` — 大于 0
- `vd:"contains($, '@')"` — 包含 @
- `vd:"regexp('^[0-9]+$')"` — 正则

---

## 5. 中间件

### 服务端中间件

```go
// 全局中间件
h.Use(func(ctx context.Context, c *app.RequestContext) {
    start := time.Now()
    c.Next(ctx)  // 继续执行后续 handler
    duration := time.Since(start)
    log.Printf("[%s] %s took %v", c.Method(), c.Path(), duration)
})
```

### 路由组级别中间件

```go
v1 := h.Group("/api", myMiddleware)
{
    v1.GET("/users", getUsers)
}
```

### 常用内置中间件

- **Recovery**：自动恢复 panic（默认启用）
- **Basic Auth**：基础认证

通过 hertz-contrib 安装扩展中间件：

```bash
go get github.com/hertz-contrib/cors
go get github.com/hertz-contrib/jwt
go get github.com/hertz-contrib/sessions
go get github.com/hertz-contrib/gzip
go get github.com/hertz-contrib/pprof
go get github.com/hertz-contrib/swagger
```

---

## 6. Client 客户端

```go
import (
    "github.com/cloudwego/hertz/pkg/app/client"
    "github.com/cloudwego/hertz/pkg/protocol"
)

c, _ := client.NewClient()
req, resp := protocol.AcquireRequest(), protocol.AcquireResponse()
defer func() {
    protocol.ReleaseRequest(req)
    protocol.ReleaseResponse(resp)
}()

req.SetRequestURI("http://localhost:8080/hello")
req.SetMethod("GET")
err := c.Do(context.Background(), req, resp)
if err != nil {
    // handle error
}
println(string(resp.Body()))
```

---

## 7. RequestContext

Handler 函数签名：

```go
type HandlerFunc func(ctx context.Context, c *app.RequestContext)
```

### 常用方法

```go
// 读取请求
c.Method()           // HTTP 方法
c.Path()             // 请求路径
c.Query("key")       // GET 参数
c.PostForm("key")    // POST 表单
c.Param("name")      // 路径参数
c.Body()             // 请求体 ([]byte)
c.Header("key")      // 请求头
c.Cookie("key")      // Cookie

// 设置响应
c.JSON(statusCode, obj)       // JSON 响应
c.String(statusCode, msg)     // 纯文本响应
c.PureJSON(statusCode, obj)   // 不转义 HTML 的 JSON
c.Data(statusCode, contentType, data)  // 二进制数据
c.XML(statusCode, obj)        // XML 响应

// 设置响应头/Cookie
c.Header("key", "value")
c.SetCookie("key", "value", maxAge, path, domain, secure, httpOnly)

// 重定向
c.Redirect(statusCode, url)
```

---

## 8. 配置选项

```go
h := server.New(
    server.WithHostPorts(":8080"),                    // 监听地址
    server.WithMaxRequestBodySize(4*1024*1024),      // 最大请求体 (默认 4MB)
    server.WithReadTimeout(30*time.Second),           // 读取超时
    server.WithWriteTimeout(30*time.Second),          // 写入超时
    server.WithIdleTimeout(60*time.Second),           // 长连接超时
    server.WithTLS(addr, certFile, keyFile),          // TLS 配置
    server.WithKeepAlive(true),                       // 是否启用 Keep-Alive
    server.WithDisablePreParseMultipartForm(false),   // 是否禁用 multipart 表单预解析
    server.WithTransport(standard.NewTransporter),    // 网络库切换: standard/go.net
    server.WithExitWaitTime(5*time.Second),           // 优雅退出等待时间
    server.WithBasePath("/api/v1"),                   // 基础路径前缀
)
```

---

## 9. Hz 代码生成工具

Hz 是 Hertz 的代码生成工具，支持 Thrift/Protobuf 生成脚手架代码。

### 安装

```bash
go install github.com/cloudwego/hertz/cmd/hz@latest
```

### 基本使用

```bash
# 初始化项目
hz new

# 根据 IDL 生成代码 (Thrift)
hz update -idl user.thrift

# 根据 IDL 生成代码 (Protobuf)
hz update -idl user.proto

# 自定义模板
hz new -template_dir ./templates
```

### 项目结构

```
.
├── biz/
│   ├── handler/    # 业务 handler（可手动修改）
│   ├── router/     # 路由注册（由 hz 维护）
│   └── model/      # 数据模型（由 hz 维护）
├── idl/            # IDL 文件
├── main.go         # 入口
└── router.go       # 路由总入口
```

---

## 10. SSE 支持

Hertz 内置 SSE（Server-Sent Events）支持：

```go
h.GET("/events", func(ctx context.Context, c *app.RequestContext) {
    c.SetSSEHandler(func(stream *app.SSEStream) error {
        for i := 0; i < 10; i++ {
            stream.Send(&app.SSEEvent{
                Event: "message",
                Data:  fmt.Sprintf("count: %d", i),
            })
            time.Sleep(1 * time.Second)
        }
        return nil
    })
})
```

SSE 自动处理：
- 设置 `Content-Type: text/event-stream`
- 关闭缓存
- 连接断开检测

---

## 11. TLS/HTTPS

```go
// 方式一：直接配置
h := server.New(server.WithTLS(":443", "./cert.pem", "./key.pem"))

// 方式二：使用 autocert 自动续期
import "golang.org/x/crypto/acme/autocert"

m := &autocert.Manager{
    Prompt:     autocert.AcceptTOS,
    HostPolicy: autocert.HostWhitelist("example.com"),
    Cache:      autocert.DirCache("certs"),
}
h := server.New(server.WithTLS(":443", "", ""))
h.AddHTTPSCallback(func() (string, string) {
    cert, _ := m.GetCertificate(&tls.ClientHelloInfo{})
    // ... 管理证书
})
```

---

## 12. 优雅关闭

Hertz 默认支持优雅关闭（监听 SIGINT/SIGTERM）：

```go
h := server.New(
    server.WithExitWaitTime(5 * time.Second), // 最大等待时间
)

// 注册关闭前钩子
h.OnShutdown = append(h.OnShutdown, func(ctx context.Context) {
    // 清理资源、关闭数据库连接等
})
```

---

## 13. 观测性

### 日志

支持 logrus / zap / zerolog / slog 集成：

```bash
go get github.com/hertz-contrib/logger/logrus
go get github.com/hertz-contrib/logger/zap
go get github.com/hertz-contrib/logger/zerolog
```

```go
import hertzlog "github.com/cloudwego/hertz/pkg/common/hlog"
import "github.com/hertz-contrib/logger/zap"

zapLogger := zap.NewLogger()
hertzlog.SetLogger(zapLogger)
```

### 链路追踪

```go
go get github.com/hertz-contrib/obs-opentelemetry/tracing

import "github.com/hertz-contrib/obs-opentelemetry/tracing"

tracer, _ := tracing.NewServerTracing()
h.Use(tracer)
```

### Prometheus 监控

```bash
go get github.com/hertz-contrib/monitor-prometheus
```

---

## 14. 第三方集成

### 服务注册与发现

| 组件 | 引入路径 |
|------|---------|
| Consul | `github.com/hertz-contrib/registry/consul` |
| Nacos | `github.com/hertz-contrib/registry/nacos` |
| etcd | `github.com/hertz-contrib/registry/etcd` |
| Eureka | `github.com/hertz-contrib/registry/eureka` |
| Polaris | `github.com/hertz-contrib/registry/polaris` |
| ZooKeeper | `github.com/hertz-contrib/registry/zookeeper` |
| Redis | `github.com/hertz-contrib/registry/redis` |
| ServiceComb | `github.com/hertz-contrib/registry/servicecomb` |

### 协议扩展

- **HTTP/2**：`github.com/hertz-contrib/http2`
- **WebSocket**：`github.com/hertz-contrib/websocket`

---

## 15. 性能对比

Hertz（使用 Netpoll）在 QPS 和延迟上优于标准 Go HTTP 框架：

- 相比 gin/echo：**2-3x QPS 提升**
- 相比 fasthttp：接近或略优（取决于场景）
- 底层网络库可选：**Netpoll**（默认，高性能非阻塞 IO）或 **go.net**（标准库）

详细 benchmark 参考：https://github.com/cloudwego/hertz-benchmark

---

## 常见陷阱

1. **Handler 签名**：Hertz 的 Handler 是 `func(ctx context.Context, c *app.RequestContext)` —— 注意有两个 context，标准库 `context.Context` 用于链路传递，`*app.RequestContext` 用于请求响应操作。
2. **body 只能读一次**：`c.Body()` 会消耗流，需要多次读取的话用 `c.Request.Body()` 提前缓存。
3. **Netpoll 默认不缓冲写**：大响应体建议使用流式写入或调整 WriteTimeout。
4. **Hz 自动生成的 router 文件不要手动修改**：`biz/router/` 下的文件由 hz 维护，手动修改会被覆盖。
5. **`protocol.AcquireRequest/Response` 记得 Release**：否则内存泄漏。

---

## 验证

```bash
# 启动服务
go run main.go

# 测试
curl http://localhost:8888/ping
# => {"message":"pong"}

# 测试 SSE
curl -N http://localhost:8888/events
# => event: message
# => data: count: 0
```

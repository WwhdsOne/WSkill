---
name: go-modern
description: >
  Go 1.22 至 1.26 版本变更速查 — 语言特性、标准库、工具链、运行时。
  覆盖 for 循环语义、range-over-func、泛型别名、iter/unique/weak 包、
  Swiss Tables map、Green Tea GC、testing/synctest、crypto 后量子等。
  使用此 skill 确保 Go 代码优先采用新版写法，避免退回到 1.21 旧惯例。
---

# go-modern — Go 1.22–1.26 版本变更速查

> **用途**：写 Go 代码时优先用新写法，不被旧习惯拖回去。
> **定位**：速查而非替代官方文档。每个条目给出要点 + 官方链接。

---

<!-- TOC -->
- [1. Go 1.22](#1-go-122)
- [2. Go 1.23](#2-go-123)
- [3. Go 1.24](#3-go-124)
- [4. Go 1.25](#4-go-125)
- [5. Go 1.26](#5-go-126)
<!-- /TOC -->

---

## 1. Go 1.22

> 🔗 https://go.dev/doc/go1.22

### 语言

- **for 循环变量不再共享** — 每次迭代创建新变量，不再需要 `v := v`
- **range over int** — `for i := range 10` 合法（遍历 0~9）
- **range-over-func（实验）** — `GOEXPERIMENT=rangefunc` 启用函数迭代器

### 标准库

- **`math/rand/v2`** — 首个 v2 标准库包，ChaCha8/PCG 替代旧 rand，API 更合理
- **`net/http` ServeMux 增强** — 支持 HTTP 方法匹配 (`POST /items`) 和通配符 (`/{path...}`)
- **`slices.Concat`** — 合并多切片
- **`runtime/trace`** — 执行跟踪器重写，延迟大幅降低
- **Mutex profile** — 按阻塞 goroutine 数量加权

### 工具

- **`vet`** — 新增空 append 检测、`defer time.Since` 检测、slog 参数检测
- **PGO** — 可去虚拟化更多调用

---

## 2. Go 1.23

> 🔗 https://go.dev/doc/go1.23

### 语言

- **range-over-func 正式发布** — `range` 支持迭代器函数类型 `func(func(K) bool)` 等
- **泛型类型别名（预览）** — `GOEXPERIMENT=aliastypeparams`

### 标准库 — 新包

- **`iter`** — 迭代器协议基础定义 `Seq[T]` / `Seq2[K,V]`
- **`unique`** — 值规范化（interning），`Make[T]` → `Handle[T]`
- **`structs`** — `HostLayout` 控制结构体内存布局

### 标准库 — 迭代器适配

- **slices** — `All` `Values` `Backward` `Collect` `AppendSeq` `Sorted` `Chunk`
- **maps** — `All` `Keys` `Values` `Insert` `Collect`

### time.Timer / Ticker 重大变更

- 未被引用的 Ticker **立即可被 GC**（旧版永不被回收）
- 通道改为 **无缓冲**，杜绝 Reset/Stop 后收到过期值
- 回退：`GODEBUG=asynctimerchan=1`

### 其他

- **crypto/tls** — 支持 Encrypted Client Hello (ECH)
- **`sync/atomic`** — 新增 `And` / `Or` 原子位操作
- **`encoding/binary`** — `Encode`/`Decode`/`Append`
- **PGO 构建时间** — 大幅优化

---

## 3. Go 1.24

> 🔗 https://go.dev/doc/go1.24

### 语言

- **泛型类型别名** — 全面支持 `type A[P any] = B[P]`

### 运行时

- **Swiss Tables map** — 新的内置 map 实现，性能 +2~3%
- **小对象分配优化**

### 标准库 — 新包

- **`weak`** — 弱指针（用于缓存、弱映射等内存高效结构）
- **`testing/synctest`（实验）** — 隔离 "气泡" 中测试并发代码
- **`os.Root`** — 在指定目录内执行文件系统操作，防止路径逃逸
- **`crypto/mlkem`** — 后量子密钥交换 ML-KEM-768/1024
- **`crypto/hkdf`** / **`crypto/pbkdf2`** / **`crypto/sha3`** — 新加密包

### 重要变更

- **`testing.B.Loop`** — `for b.Loop() { ... }` 替代 `for range b.N`
- **`runtime.AddCleanup`** — 新的终结器，替代 `SetFinalizer`
- **`crypto/rand.Read`** — 保证不失败；Linux 6.11+ 走 vDSO 提速
- **FIPS 140-3 合规机制**

---

## 4. Go 1.25

> 🔗 https://go.dev/doc/go1.25

### 运行时

- **容器感知 GOMAXPROCS** — Linux cgroup CPU 限制
- **Green Tea GC（实验）** — `GOEXPERIMENT=greenteagc`，预计 GC 开销 -10~40%
- **Trace Flight Recorder** — 环形缓冲区持续录制，按需快照

### 标准库

- **`testing/synctest`** — 从 Go 1.24 实验毕业
- **`encoding/json/v2`（实验）** — `GOEXPERIMENT=jsonv2`，解码大幅提升
- **`net/http`** — 新增 `CrossOriginProtection` CSRF 防御
- **`sync.WaitGroup.Go`** — 新方法

### 工具

- **`go build -asan`** — 默认做 C 内存泄漏检测
- **`go vet`** — 新增 `waitgroup` / `hostport` 分析器
- **DWARF5** — 默认生成，减少二进制体积

---

## 5. Go 1.26

> 🔗 https://go.dev/doc/go1.26

### 语言

- **`new` 内建函数增强** — `new(yearsSince(born))` 直接传表达式
- **泛型自引用约束** — 类型参数可在列表中引用自身

### 运行时

- **Green Tea GC 默认启用** — 标记/扫描性能大幅提升（10~40%），回退 `GOEXPERIMENT=nogreenteagc`
- **cgo 调用基础开销 -30%**
- **堆基地址随机化** — 64 位平台安全加固
- **goroutine 泄漏检测（实验）** — `GOEXPERIMENT=goroutineleakprofile`

### 标准库 — 新包

- **`crypto/hpke`** — RFC 9180 Hybrid Public Key Encryption
- **`simd/archsimd`（实验）** — `GOEXPERIMENT=simd`，架构特定 SIMD 操作
- **`runtime/secret`（实验）** — `GOEXPERIMENT=runtimesecret`，安全擦除临时数据

### crypto/tls — 后量子默认

- `SecP256r1MLKEM768` 和 `SecP384r1MLKEM1024` **默认启用**
- 回退 `GODEBUG=tlssecpmlkem=0`

### 工具

- **`go fix` 全面重写** — 现代化器大本营，数十个 fixer + `//go:fix inline`
- **`go mod init`** — 创建 go.mod 时自动降版本
- **pprof Web UI** — 火焰图默认视图

### 其他库变更

- **`errors.AsType`** — `errors.As` 的泛型版本
- **`io.ReadAll`** — 约快 2 倍
- **`log/slog.NewMultiHandler`**
- **`reflect.Type.Fields`/`Methods`** — 返回迭代器
- **`image/jpeg`** — 编解码器重写
- **`time`** — `asynctimerchan` GODEBUG 将在 1.27 移除

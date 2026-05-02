---
name: redis-diagnostics
description: >-
  纯原生 Redis 诊断 — 仅依赖 redis-cli + Redis 内置命令（INFO/MEMORY/SLOWLOG/SCAN/HOTKEYS/LATENCY 等），
  无需第三方工具。覆盖延迟分析、内存排查、热Key定位、大Key扫描、连接审计等场景。
trigger: >-
  用户询问 Redis 诊断/排查/监控/性能/延迟/内存/热键/大键/慢查询；
  或提到需要排查 Redis 问题时优先加载此技能。
---

# Redis 纯原生诊断技能

> **核心原则：** 只依赖 `redis-cli` + Redis 服务端内置命令，无需 `redis-faina`、`redis-rdb-tools`、Redis Insight 等第三方工具。

---

## 版本探测（入口步骤）

诊断前先确认 Redis 版本，决定可用命令分支：

```bash
redis-cli INFO server | grep redis_version
```

关键版本分界点：
- **≥ 8.6.0** — 支持 `HOTKEYS` 系列（内核级热键追踪，推荐，无 LFU 依赖）
- **≥ 7.0.0** — 支持 `LATENCY HISTOGRAM`（命令级延迟分布直方图）
- **≥ 4.0.0** — 支持 `redis-cli --memkeys`、`--latency-dist`、`--hotkeys`（需 LFU）
- **≥ 3.0.0** — 支持 `redis-cli --latency-history`、`--intrinsic-latency`
- **≥ 2.8.0** — 支持 `redis-cli --bigkeys`、LATENCY 框架（DOCTOR/LATEST）
- **≥ 2.6.0** — 支持 `redis-cli --latency`
- **早期版本** — 基础 `INFO`、`SLOWLOG`、`SCAN`（SCAN 从 2.8.0 起）

---

## 命令参考（按分类）

### 1. redis-cli 终端模式（无需连接后输入命令）

| 命令 | 行为 | 版本 | 关键说明 |
|------|------|------|----------|
| `redis-cli --stat` | 实时滚动统计（keys/mem/clients/requests） | 早期 | 每秒刷新，Ctrl+C 退出 |
| `redis-cli --latency` | 实时延迟采样（min/max/avg） | 2.6+ | 每秒 100 次 PING，毫秒级 |
| `redis-cli --latency-history` | 分窗口延迟（默认每 15 秒一个窗口） | 3.0+ | 可加 `-i <秒>` 调整窗口长度 |
| `redis-cli --latency-dist` | ASCII 频谱图（需 256 色终端） | 4.0+ | 信息量大，需彩色终端 |
| `redis-cli --intrinsic-latency <秒>` | 测试机器自身延迟基线 | 3.0+ | **不连 Redis**，微秒级，在 Redis 服务器本机运行 |
| `redis-cli --bigkeys` | 按元素数量扫描大键 | 2.8+ | 使用 SCAN，生产友好 |
| `redis-cli --memkeys` | 按内存占用扫描大键 | 4.0+ | 使用 MEMORY USAGE |
| `redis-cli --hotkeys` | 扫描热键 | 4.0+ | **需 LFU 淘汰策略**（`maxmemory-policy allkeys-lfu` 等） |

通用选项（适用于上述扫描类命令）：
- `-i <interval>` — 每 100 次 SCAN 休眠秒数（小数支持，如 `-i 0.1`）
- `--pattern <pat>` — 键名匹配模式
- `--count <count>` — 每次 SCAN 返回键数（默认 10）

---

### 2. INFO 命令（Redis 1.0.0+）

**语法：** `INFO [section [section ...]]`

特殊值：`default`（默认）、`all`（不含 modules）、`everything`（含 modules）

关键 sections：

| Section | 诊断用途 | 关键字段 |
|---------|----------|----------|
| `memory` | 内存状态速查 | `used_memory`, `used_memory_rss`, `mem_fragmentation_ratio`, `used_memory_peak` |
| `clients` | 连接异常排查 | `connected_clients`, `maxclients`, `blocked_clients`, `client_recent_max_input_buffer` |
| `persistence` | 持久化状态 | `rdb_last_bgsave_status`, `aof_last_rewrite_status`, `aof_delayed_fsync` |
| `stats` | 常规统计 | `total_commands_processed`, `expired_keys`, `evicted_keys`, `keyspace_hits/misses` |
| `commandstats` | 命令耗时 | 每个命令的 `calls`、`usec`、`usec_per_call` |
| `latencystats` | 延迟分布（7.0+） | 命令的 p50/p99 延迟 |
| `errorstats` | 错误统计（7.0+） | 各错误类型计数 |
| `server` | 版本与基础信息 | `redis_version`, `os`, `tcp_port`, `uptime_in_seconds` |
| `keyspace` | 各数据库键数量 | `db0:keys=xxx,expires=xxx` |
| `replication` | 主从状态 | `role`, `master_link_status`, `slave_lag` |
| `cpu` | CPU 消耗 | `used_cpu_sys`, `used_cpu_user` |
| `threads` | IO 线程 | `io_threads_active`, `io_threads_total` |

**返回值：** RESP2 Bulk string / RESP3 Verbatim string。每行 `<field>:<value>`，section 以 `# SectionName` 分隔。

---

### 3. SLOWLOG（Redis 2.2.12+ / 完善于 2.8+）

**语法与子命令：**

```
SLOWLOG GET [count]    — 返回最近 N 条慢查询（默认 10）
SLOWLOG LEN            — 当前慢查询日志总数
SLOWLOG RESET          — 清空慢查询日志
SLOWLOG HELP           — 帮助信息
```

慢查询阈值由 `slowlog-log-slower-than` 控制（单位微秒，默认 10000 = 10ms）。
最大记录数由 `slowlog-max-len` 控制。

**每条记录的字段：** `[id, timestamp_us, duration_us, command_args, client_addr, client_name]`

**配置：**
```bash
CONFIG GET slowlog-log-slower-than    # 查看当前阈值
CONFIG GET slowlog-max-len            # 查看最大记录数
CONFIG SET slowlog-log-slower-than 1000  # 设置 1ms 阈值
```

---

### 4. MEMORY 命令族（Redis 4.0+）

#### MEMORY STATS
**语法：** `MEMORY STATS`
返回 32 个内存指标的交替数组，包括：
- `peak.allocated` / `peak.allocated.human` — 历史峰值
- `total.allocated` / `startup.allocated` — 当前总分配 / 启动基线
- `overhead.db` — 数据库开销（键元数据等）
- `overhead.hashtable.main` / `overhead.hashtable.expires` — 哈希表开销
- `overnight.hashtable.slot-to-keys` — Cluster 槽映射开销
- `keys.count` / `keys.mem` — 键数量 / 键数据开销
- `clients.slaves` / `clients.normal` — 客户端缓冲区开销
- `dataset.bytes` — 数据集实际大小
- `dataset.percentage` — 占比
- `allocator.active` / `allocator.allocated` / `allocator.resident` / `allocator.fragmentation` — 分配器状态
- `allocator-fragmentation.ratio` — 分配器碎片率
- `allocator-fragmentation.bytes` — 碎片字节数

#### MEMORY USAGE
**语法：** `MEMORY USAGE <key> [SAMPLES <count>]`
返回键精确内存占用（字节）。`SAMPLES` 控制嵌套元素采样数（默认 5）。

---

### 5. SCAN 命令族（Redis 2.8.0+）

#### SCAN（全库增量遍历）
```
SCAN cursor [MATCH pattern] [COUNT count] [TYPE type]
```
- `cursor` — 游标，初始为 0，返回新游标，游标回到 0 时遍历完毕
- `MATCH pattern` — glob 模式过滤键名
- `COUNT count` — 每次迭代期望返回数（默认 10，非精确）
- `TYPE type` — 按数据类型过滤（如 `string`、`list`、`set`、`zset`、`hash`、`stream`）

**返回值：** 两个元素的数组 `[next_cursor, [key1, key2, ...]]`

**重要保证：**
- 全量返回 = SCAN 过程中所有存在的键都会被返回，但可能在多次迭代中
- 同一次全量遍历中，一个键最多被返回一次
- 遍历开始后新增的键**不保证**被返回
- 无强一致性保证（元素可能在遍历过程中被修改）
- COUNT 默认值可能随时变更，不保证与迭代次数成反比

#### SSCAN / HSCAN / ZSCAN（集合内增量遍历）
```
SSCAN key cursor [MATCH pattern] [COUNT count]
HSCAN key cursor [MATCH pattern] [COUNT count]
ZSCAN key cursor [MATCH pattern] [COUNT count]
```
**关键区别：** 第一个参数是键名（而非游标），其他参数与 SCAN 相同。
- SSCAN：返回集合成员
- HSCAN：返回 field-value 对（交替数组）
- ZSCAN：返回 member-score 对（交替数组）
- HSCAN 支持 `NOVALUES` 参数（7.4+）：只返回 field 名，不返回 value

---

### 6. CLIENT LIST（Redis 2.4.0+）
```
CLIENT LIST [TYPE normal|master|replica|pubsub] [ID id1 id2 ...]
```

返回 30+ 个字段的连接详细列表：

| 字段 | 说明 |
|------|------|
| `id` | 唯一连接 ID |
| `addr` | 客户端地址:端口 |
| `laddr` | 本地绑定的地址:端口 |
| `fd` | 文件描述符 |
| `name` | 客户端名称（通过 CLIENT SETNAME 设置） |
| `age` | 连接存在时间（秒） |
| `idle` | 空闲时间（秒） |
| `flags` | 客户端标志（21 种，如 N:普通、M:主库、S:副本、b:阻塞、B:后台写） |
| `db` | 当前数据库索引 |
| `sub` / `psub` / `ssub` | 普通/模式/分片频道订阅数 |
| `multi` | 当前事务中命令数 |
| `qbuf` / `qbuf-free` | 查询缓冲区已用/空闲 |
| `argv-mem` | 当前命令参数内存 |
| `oll` / `omem` | 输出列表长度 / 输出缓冲区内存 |
| `tot-mem` | 总内存 |
| `events` | 文件描述符事件（r=读, w=写） |
| `cmd` | 当前执行的命令 |
| `user` | 认证的用户名（ACL） |
| `redir` | 重定向的客户端 ID |

---

### 7. ACL LOG（Redis 6.0.0+）
```
ACL LOG [count]        — 返回最近 N 条 ACL 拒绝记录（默认 10）
ACL LOG RESET          — 清空日志
```

每条记录字段：`count`, `reason`, `object`, `username`, `age-seconds`, `client-info`

---

### 8. LATENCY 框架（Redis 2.8.13+）

| 命令 | 版本 | 说明 |
|------|------|------|
| `LATENCY DOCTOR` | 2.8.13+ | 人类可读的延迟诊断报告（最强大），包含统计数据和改善建议 |
| `LATENCY LATEST` | 2.8.13+ | 最近延迟事件列表：`[event_name, timestamp, latest_ms, alltime_max_ms]` |
| `LATENCY HISTOGRAM [cmd...]` | 7.0.0+ | 命令级延迟分布直方图（log2 桶，1ns~1s，最多 30 个桶） |
| `LATENCY RESET [event...]` | 2.8.13+ | 重置延迟事件数据 |
| `LATENCY GRAPH <event>` | 2.8.13+ | 指定事件的 ASCII 图 |
| `LATENCY HELP` | — | 帮助信息 |

**LATENCY HISTOGRAM 要求：** 启用扩展延迟监控（默认开启），可通过 `CONFIG SET latency-tracking yes` 启用。用 `CONFIG RESETSTAT` 清除数据。

---

### 9. PUBSUB 命令（Redis 2.8.0+）

```
PUBSUB CHANNELS [pattern]         — 列出活跃频道（glob 风格模式匹配）
PUBSUB NUMSUB [channel ...]       — 指定频道的订阅者数（不包含模式订阅者）
PUBSUB NUMPAT                     — 模式订阅者数量
```

**集群说明：** PUBSUB 命令仅返回当前节点的 Pub/Sub 上下文信息，非整个集群。

---

### 10. HOTKEYS 系列（Redis 8.6.0+，ACL: @admin @slow @dangerous）
> **推荐方案**：内核级热键追踪，无需 LFU 淘汰策略，优于 `redis-cli --hotkeys`

命令生命周期：
```
HOTKEYS START METRICS ...  →  HOTKEYS GET（读取）  →  HOTKEYS STOP → HOTKEYS RESET
     │                                                        │
     └── 自动停止（DURATION 到期）                     └── 数据保留可读
```

#### HOTKEYS START
```
HOTKEYS START METRICS count [CPU] [NET] [COUNT k] [DURATION seconds] [SAMPLE ratio] [SLOTS count slot ...]
```
- **METRICS count** — 必选，排行榜大小（收集多少个热键的指标）
- **CPU** — 按 CPU 时间追踪（与 NET 至少选一个）
- **NET** — 按网络字节数追踪
- **COUNT k** — top-K 追踪的 K 值（排行榜长度）
- **DURATION seconds** — 自动停止时长
- **SAMPLE ratio** — 概率采样（1/ratio）。值越大性能影响越小
- **SLOTS count slot ...** — 集群环境限定哈希槽

#### HOTKEYS GET
返回元数据 + 排行榜：
- `by-cpu-time-us` — 键-值交替数组，按 CPU 时间降序
- `by-net-bytes` — 键-值交替数组，按网络字节数降序
- 元数据：`tracking-active`、`sample-ratio`、`collection-duration-ms`、`total-cpu-time-user-ms` 等

#### HOTKEYS STOP
停止追踪，保留数据可读。

#### HOTKEYS RESET
释放追踪资源（需先 STOP）。

---

### 11. CONFIG GET（Redis 2.0+）

```
CONFIG GET <pattern>    — 支持 glob 模式匹配
CONFIG SET <key> <val>  — 动态修改配置（无需重启）
```

常见诊断配置模式：
```bash
CONFIG GET slowlog*              # 慢查询相关
CONFIG GET *max*                  # 最大限制
CONFIG GET *timeout*              # 超时相关
CONFIG GET latency*               # 延迟监控
CONFIG GET maxmemory*             # 最大内存
CONFIG GET *policy*               # 淘汰策略
```

---

## 场景诊断流程

### 场景 A：快速健康检查
```bash
redis-cli --stat                                    # 连续监控
redis-cli INFO memory | grep -E 'used_memory|frag'  # 内存速览
redis-cli INFO clients | grep connected              # 连接速览
redis-cli INFO stats | grep -E 'hits|misses'         # 命中率
```

### 场景 B：响应慢排查
```bash
# 1. 先看慢查询
redis-cli SLOWLOG GET 10
# 2. 看延迟监控报告
redis-cli LATENCY DOCTOR
# 3. 看最近延迟事件
redis-cli LATENCY LATEST
# 4. 按命令统计耗时
redis-cli INFO commandstats | sort -t: -k2 -rn | head -10
# 5. 延迟分布直方图（7.0+）
redis-cli LATENCY HISTOGRAM
# 6. 检查系统固有延迟（在服务器本机执行）
redis-cli --intrinsic-latency 5
```

### 场景 C：内存爆炸排查
```bash
# 1. 内存总览
redis-cli INFO memory | grep -E 'used_memory|rss|frag|peak|overhead|dataset'
redis-cli MEMORY STATS | head -30
# 2. 大键扫描
redis-cli --memkeys
# 3. 检查可疑键
redis-cli MEMORY USAGE <suspicious_key>
# 4. 碎片分析
# frag_ratio > 1.5 表示需要内存碎片整理
# frag_ratio < 0.8 表示使用了大量内存交换（需排查）
```

### 场景 D：热Key定位
```bash
# 方式一（推荐，8.6+）：
redis-cli HOTKEYS START METRICS 10 CPU NET
# 等待一段时间...
redis-cli HOTKEYS GET
redis-cli HOTKEYS STOP
redis-cli HOTKEYS RESET

# 方式二（需 LFU 策略，4.0+）：
redis-cli --hotkeys

# 方式三（通用，无依赖）：
# 手动通过 INFO commandstats 观察哪些命命令被频繁调用
redis-cli INFO commandstats
```

### 场景 E：大Key定位
```bash
# 按元素数量（推荐优先做，速度快）
redis-cli --bigkeys

# 按内存占用（更精确，但稍慢）
redis-cli --memkeys

# 精确排查
redis-cli MEMORY USAGE <key>
redis-cli DEBUG OBJECT <key>    # 查看内部编码和详细信息
```

### 场景 F：连接数异常
```bash
redis-cli CLIENT LIST | wc -l              # 总连接数
redis-cli INFO clients                      # 连接统计
redis-cli CLIENT LIST | grep -c 'flags=N'  # 普通客户端数
redis-cli CLIENT LIST | grep -c 'flags=S'  # 副本数
redis-cli CLIENT LIST | awk '{print $2}' | sort | uniq -c | sort -rn | head -10  # 按 IP 聚合
redis-cli CONFIG GET maxclients            # 最大连接限制
```

### 场景 G：持久化故障排查
```bash
redis-cli INFO persistence
# 检查项：
# rdb_last_bgsave_status → 是否成功
# aof_last_rewrite_status → 是否成功
# aof_delayed_fsync → 是否有延迟 fsync
# rdb_bgsave_in_progress → 是否正在执行

redis-cli LATENCY HISTOGRAM bgsave    # 7.0+，查看 bgsave 延迟
```

### 场景 H：ACL 审计
```bash
redis-cli ACL LOG              # 最近被拒绝的命令/认证失败
redis-cli ACL LOG 100          # 最近 100 条
redis-cli ACL LOG RESET        # 清空日志
```

---

## 安全规则

1. **禁止使用 `KEYS *`** — 生产环境阻塞式操作，用 `SCAN` 替代
2. **禁止使用 `FLUSHALL` / `FLUSHDB`** — 除非用户明确确认
3. **禁止使用 `DEBUG SEGFAULT`** — 会导致进程崩溃
4. **`MONITOR` 命令** — 高开销，仅短期诊断使用
5. **`SLOWLOG RESET`** — 谨慎执行，会丢失历史数据

---

## 参考链接
- Redis CLI 文档：https://redis.io/docs/latest/develop/tools/cli/
- Redis 命令全集：https://redis.io/docs/latest/commands/
- 延迟监控：https://redis.io/docs/latest/operate/oss_and_stack/management/latency-monitor/
- 内存优化：https://redis.io/docs/latest/develop/use/memory-optimization/

## 引用文件
- `references/doc-scraping-patterns.md` — redis.io 文档抓取模式（MD vs HTML 来源、版本确认笔记），下次更新 skill 时参考

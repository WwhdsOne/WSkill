# redis.io 文档抓取模式

> 用于下次更新 `redis-diagnostics` skill 时重新抓取官方文档

---

## 抓取方式（按优先级）

### 方式一：Markdown 源（推荐，优先尝试）

某些命令页面提供 `.md` 格式：

```
https://redis.io/docs/latest/commands/info/index.md     ← 可用，53KB vs HTML 333KB
https://redis.io/docs/latest/commands/slowlog/index.md  ← 可用，1.3KB vs HTML 217KB
```

**特点：**
- 体积为 HTML 的 1/6 ~ 1/50
- 头部包含 JSON 元数据块（语法、参数、版本、复杂度）
- 后续为行为描述和代码示例
- 仅部分页面支持此模式（目前发现 INFO / CONFIG / SLOWLOG / MEMORY 相关工作）

### 方式二：HTML 源（兜底）

```
https://redis.io/docs/latest/commands/scan/               ← 3.2MB HTML（仅 SCAN）
https://redis.io/docs/latest/commands/client-list/        ← 225KB
```

**特点：**
- 体积差异巨大（SCAN 页面 3.2MB，含 12+ 语言客户端代码示例）
- 内容在 `<section class="prose w-full py-12">` 区域
- 元数据在 `<script data-ai-metadata>` JSON 内嵌标签
- CLI 客户端代码块在 `<pre>` 标签内
- 使用 `html.parser` 或正则提取

### 方式三：Markdown 兜底（部分特殊页面）

```
https://redis.io/docs/latest/develop/tools/cli/          ← CLI 文档页面
```

**特点：**
- 这组页面有 `/index.md` 可用？需确认
- CLI 命令（`--stat`, `--latency` 等）集成在工具文档中，非独立命令

---

## 每个命令需提取的信息

```python
info_fields = [
    "语法 (Syntax)",
    "参数 (Parameters/Arguments)", 
    "行为描述 (Description)",
    "版本历史 (Since / Available since)",
    "复杂度 (Complexity)",
    "ACL 分类 (ACL categories)",
    "返回值 (Return Value)",  # RESP2 + RESP3
    "重要注意事项/保证 (Notes/Guarantees)",
]
```

## 已知坑点

1. **SCAN 页面极大（3.2MB）**：包含 12+ 语言的客户端代码示例。只提取 `section.prose` 区域即可，跳过客户端示例
2. **CLIENT LIST 标志字段**：在 `<pre>` 纯文本中，需单独定位提取
3. **SSCAN / HSCAN / ZSCAN 页面**：部分内容仅写 "See SCAN for documentation"，需交叉引用
4. **HOTKEYS 系列**：仅在 Redis 8.6+ 可用，低版本 Redis 访问返回错误
5. **`redis-cli --hotkeys`**：文档中无独立章节，仅在选项列表中提及
6. **LATENCY HISTOGRAM 版本**：官方标 Redis 7.0.0（非任务描述中的 7.4+）

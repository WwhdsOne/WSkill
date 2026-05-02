# redis.io 文档抓取模式

> 用于下次更新 `redis-diagnostics` skill 时重新抓取官方文档
> Skill 路径：`~/WSkill/redis-diagnostics/`

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

---

## 实战捕获：URL 模式对照表

### .md 源可用（推荐）

| 命令页面 | 成功 | 体积 |
|----------|------|------|
| `commands/info/index.md` | ✅ | 53KB |
| `commands/slowlog/index.md` | ✅ | 1.3KB |
| `commands/config-get/index.md` | ✅ | 3KB |
| `commands/memory-stats/index.md` | ✅ | 6KB |
| `commands/memory-usage/index.md` | ✅ | 3.4KB |

### .md 源不可用（必用 HTML）

| 命令页面 | HTML 体积 | 原因 |
|----------|-----------|------|
| `commands/scan/` | 3.2MB | 12+ 语言客户端代码示例 |
| `commands/client-list/` | 225KB | — |
| `commands/acl-log/` | 229KB | — |
| `commands/hotkeys-start/` | 225KB | — |

### CLI 页面

| URL | 体积 | 说明 |
|-----|------|------|
| `develop/tools/cli/` | 181KB | —stat, --latency 等终端模式 |
| 该页面无 .md 源 | — | 仅 HTML |

---

## 提取脚本模板

以下 Python 提取流程经本 session 验证可用：

```python
import urllib.request, re, json

def fetch_html(url: str) -> str:
    """抓取页面 HTML"""
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode('utf-8', errors='replace')

def extract_metadata(html: str) -> dict:
    """从 <script data-ai-metadata> 提取命令元数据"""
    m = re.search(r'<script[^>]*data-ai-metadata[^>]*>(.*?)</script>', html, re.DOTALL)
    return json.loads(m.group(1)) if m else {}

def extract_content_section(html: str) -> str:
    """提取 <section class=\"prose w-full py-12\"> 内容"""
    m = re.search(r'<section class="prose w-full py-12">(.*?)</section>', html, re.DOTALL)
    if not m:
        return html
    # Strip HTML tags
    text = re.sub(r'<[^>]+>', '\n', m.group(1))
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def try_md_source(slug: str) -> str | None:
    """优先尝试 .md 源"""
    url = f'https://redis.io/docs/latest/commands/{slug}/index.md'
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            md = resp.read().decode('utf-8')
            # Strip YAML frontmatter if present
            if md.startswith('---'):
                parts = md.split('---', 2)
                if len(parts) >= 3:
                    md = parts[2]
            return md.strip()
    except Exception:
        return None

# 使用示例
# MD 源：md = try_md_source('info')
# HTML 源：html = fetch_html('https://redis.io/docs/latest/commands/scan/')
```

---

## timeout 与并发策略

- **单个页面超时设置**：INFO 页面 333KB → 10s 足够；SCAN 页面 3.2MB → 设 60s
- **并发限制**：`delegate_task` 最多 3 个子任务并行
- **分批策略**：5 组命令分 2 批（3+2），避免单批超时拖垮全部
- **失败兜底**：单个子任务超时后，拆分成更小的组重新提交

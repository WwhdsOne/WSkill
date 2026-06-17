# Semantic Scholar: 论文发现 & 引用链追踪

> 从一篇已知论文出发，找到几年后更先进的后续工作。
> 免费，无需 API Key，1 req/s 速率限制。

## 核心场景

| 场景 | 方法 |
|------|------|
| 找 A 论文的后续工作（谁引用了它） | `/citations` 端点 |
| 找 A 论文引用了哪些文献 | `/references` 端点 |
| 给定 A，推荐相关论文 | `/recommendations` POST |
| 关键词搜索论文 | `/paper/search` |

## 常用 API 调用

### 1. 查论文详情 + 引用量

```bash
curl -s "https://api.semanticscholar.org/graph/v1/paper/arXiv:2402.03300?fields=title,citationCount, influentialCitationCount,year,abstract"
```

### 2. 找引用 A 论文的工作（谁引用了它）→ 找到后续 B

```bash
curl -s "https://api.semanticscholar.org/graph/v1/paper/arXiv:2402.03300/citations?fields=title,authors,year,citationCount&limit=20"
```

筛选策略：按 `year` 字段过滤出比 A 论文发表年份新的结果。高 `citationCount` 的通常是重要后续工作。

### 3. 推荐系统（不需要引用关系，纯语义相关）

```bash
curl -s -X POST "https://api.semanticscholar.org/recommendations/v1/papers/" \
  -H "Content-Type: application/json" \
  -d '{"positivePaperIds": ["arXiv:2402.03300"], "negativePaperIds": []}'
```

### 4. 关键词搜索

```bash
curl -s "https://api.semanticscholar.org/graph/v1/paper/search?query=scene+generation+diffusion&limit=5&fields=title,year,citationCount,externalIds"
```

## 常见问题

- **Semantic Scholar ID vs arXiv ID**：API 接受 `arXiv:xxxx.xxxxx` 格式，也接受 `DOI:10.xxxx/xxx`
- **汇总输出**：结果通常是 JSON array，用 `python3 -m json.tool` 格式化，或 `python3 -c "import json,sys; ..."` 做精简摘要
- **引文量低的新论文**：可能没有足够的引用链，此时用推荐系统替代引用追踪

## 参考

完整文档见 `arxiv` skill 的 Semantic Scholar 章节。

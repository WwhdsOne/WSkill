---
name: paper-summary
description: 用户丢论文链接/PDF/DOI → 读取全文 → 生成结构化 MD 总结（含 LaTeX 公式 + SVG 图解）→ 打 Obsidian 标签 → 推送至 LearningNotes/paper/
---

# Paper Summary Workflow

## 关联 skill

- **`arxiv`**：提供 arXiv 搜索 + Semantic Scholar API（引用链追踪、推荐系统）。当用户不给直接链接、而是想"从论文 A 找到几年后的改进论文 B"时，需要使用该 skill 的 Semantic Scholar `/citations` 和 `/recommendations` 端点。

## 触发条件

### 直接阅读总结
用户在对话中丢来以下任意一种形式的论文：

- ArXiv 链接（`https://arxiv.org/abs/xxxx.xxxxx`）
- PDF 链接（`https://arxiv.org/pdf/xxxx.xxxxx.pdf`）
- DOI（`10.xxxx/xxxxx`）
- PDF 文件（上传方式）
- 论文标题 + 作者（需要搜索原文）

## 论文发现（前置步骤）

当用户不直接给链接，而是想**从一篇 A 论文找到几年后的更先进的 B 论文**时：

1. 用 `web_search` 或用 `arxiv` skill 的 arXiv API 定位 A 论文的 arXiv ID
2. 用 Semantic Scholar 引用追踪查找后继工作：
   ```
   /citations?fields=title,authors,year,citationCount&limit=20
   ```
   筛选比 A 论文发表年份新的结果，按引用量排序
3. 或者用语义推荐（无需引用关系）：
   ```
   POST /recommendations/v1/papers/
   ```
4. 对每个候选 B 论文，用 `web_extract` 读摘要判断相关性

详细 API 调用见 `references/semantic-scholar-discovery.md`。

> 注意：Semantic Scholar API 免费、1 req/s 限制、无需 API Key。有新特性的论文引文量可能很低，此时推荐系统优于引用追踪。

## 步骤

### 1. 读取全文

根据输入格式选择：

| 类型 | 方法 |
|------|------|
| ArXiv 链接 | `web_extract(urls=["https://arxiv.org/abs/xxxx.xxxxx"])` 提取全文 |
| PDF 链接 | `web_extract(urls=["https://arxiv.org/pdf/xxxx.xxxxx.pdf"])` 提取全文 |
| DOI / 标题 | 先 `web_search` 找到链接，再 `web_extract` |
| 上传 PDF | 用 `terminal` 工具调用 `pdftotext` 或 `pymupdf` 提取文本 |

**超长 PDF（>2M 字符）**：先读摘要和引言给出初步判断，询问用户是否继续深入。

### 2. 理解提取核心内容

从全文中提取以下信息：

- **一句话概括**：这篇论文做了什么
- **动机**：1-3 点，为什么要做，现有方法的痛点
- **方法**：
  - 整体思路
  - 关键模块/组件及其设计理由
  - 训练/推理设置（数据集、loss、推理方式）
  - **核心公式**（1-3 个，用 `$$ ... $$` LaTeX，每个附一两句话说明）
- **关键 Insight**：最有价值的发现或设计
- **值得注意的细节**：实验发现、消融、Limitation
- **评价**：推荐程度（⭐）、一句话判断、可引用句

### 3. 生成 MD 文件

文件路径：`/root/LearningNotes/paper/<年份>-<简短英文标题>.md`

模板：

```markdown
---
tags: [paper, <方向标签>, <年份>]
date: YYYY-MM-DD
source: <链接>
---

# 论文标题

> 一句话概括

## 动机

...

## 方法

...

**关键公式：**
$$ \mathcal{L} = ... $$

> 说明

## 关键 Insight

...

## 图表辅助

![pipeline](images/<文件名前缀>-pipeline.svg)

（如适用）

## 值得注意的细节

...

## 评价

- **推荐程度**：⭐⭐⭐
- **一句话**：
- **可引用**：

## 相关资源

> 搜索并汇总与本论文相关的 GitHub 仓库、实现、后续工作、以及其他资料。

| 类型 | 名称/标题 | 链接 | 说明 |
|------|-----------|------|------|
| GitHub | 官方实现 | `https://github.com/xxx/xxx` | 论文官方代码仓库 |
| GitHub | 第三方复现 | `https://github.com/xxx/xxx` | 更好的 PyTorch 实现 |
| 论文 | 相关工作 A | `https://arxiv.org/abs/xxx` | 做了什么 |
| 项目页 | 项目主页 | `https://xxx.github.io/` | Demo / 数据集 |
| ... | ... | ... | ... |
```

### 搜索策略说明

1. **GitHub 仓库搜索**：用论文标题/缩写 + 关键词在 GitHub 搜（Tavily `site:github.com` 或直接搜 `<论文名> github`）
2. **官方实现**：论文页面通常有 Code 链接，优先用
3. **后续工作**：如果论文有 arXiv ID，用 Semantic Scholar 查引用，挑选引用量高或年份新的后续工作
4. **项目主页**：很多 CV/图形学论文有独立项目页，包含 demo/dataset
5. **相关论文**：相关性高的后续/前驱工作，3-5 篇，附一句话说明

> 资源搜索在写总结之后进行，结果放在 MD 文件末尾。搜索前先看论文原文是否已经提供了 Code/Project 链接，这样最准。

### 4. 生成 SVG 图解（如适用）

条件：论文有清晰的**架构图/流程图/模块关系**

- 风格：手绘风线条，灰/蓝/橙色系
- 存放路径：`/root/LearningNotes/paper/images/<文件名前缀>-pipeline.svg`
- MD 中用相对路径引用
- 纯数学/理论推导论文不强行作图

### 5. Obsidian 标签

YAML frontmatter 中的 `tags` 字段：

- **固定**：`paper`
- **方向标签**：按论文内容自动生成
  - 优先复用 `paper/` 目录下已有 `.md` 文件中出现过的标签（扫描已有文件的 tags 字段）
  - 如果现有标签都不匹配，创建合理的新标签
- **年份标签**：自动
- 每篇 **3-6 个**标签

### 6. 推送

```bash
cd /root/LearningNotes
git add paper/
git commit -m "paper: <论文短标题>"
git push
```

确认推送成功（检查 exit code 和 git log）。

### 7. 告知用户

- 文件名
- 包含哪些内容（总结 + 图）
- 标签
- 已推送，可 `git pull`

## 边界情况

- **超长 PDF**：先给初步摘要判断，问"要继续吗"
- **无架构/纯数学论文**：不画图，只写公式
- **推送失败**：检查网络（可能 GFW 问题），尝试切 SSH 再推
- **标签扫描**：用 `grep -sh ^tags paper/*.md 2>/dev/null` 收集已有标签（`grep -s` 抑制空目录时的错误）。如果第一次运行没有已有标签直接按内容创建新标签

## 注意事项

- 公式用 `$$ ... $$` 块级 LaTeX，Typora 原生渲染
- SVG 用字符串拼接直接写文件（不用外部工具）
- 标签不滥用，保证每个标签都有意义
- 图片名以论文文件名的前缀保持一致

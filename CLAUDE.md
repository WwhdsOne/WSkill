# WSkill 仓库规则

## 新增 Skill 时必须更新 README.md

当你在这个仓库新增一个 skill 目录时，**必须先更新 README.md 再提交**：

1. 新建 skill 目录，写入 `SKILL.md` 及相关文件
2. 在 `README.md` 的 **Skills** 表格中按字母顺序添加一行
3. 然后 `git add -A && git commit && git push`

> 任何新增 skill 但不同步更新 README.md 的提交都是不完整的。

## 目录结构

每个 skill 一个独立目录：

```
<skill-name>/
├── SKILL.md           # 核心定义
├── references/        # 辅助文档（可选）
├── scripts/           # 脚本（可选）
└── templates/         # 模板文件（可选）
```

# WSkill

**WwhdsOne 自建 Hermes Skills 库**

个人开发过程中积累的工具型 Skills 集合。不整合外部内容，不搬运第三方库。

每个 skill 都是实际使用中提炼出来的工作流封装——自用为主，顺手维护。

## 目录

| Skill | 说明 |
|-------|------|
| `clashctl-proxy/` | mihomo/clash 代理管理 — CLI、REST API、自动切节点 |
| `go-modern/` | Go 1.22–1.26 版本变更速查（语言/标准库/工具链） |
| `hertz/` | CloudWeGo Hertz — 高性能 Go HTTP 框架 |
|| `redis-diagnostics/` | 纯原生 Redis 诊断（仅 redis-cli + 内置命令） |
|| `README.md` | 本文件 + 安装到 AI 编程工具的命令 |

## 使用方式

配了 Hermes `external_dirs: ["~/WSkill"]`，`skill_view` 和 `skills_list` 直接可见。
需要更新时本地改完 git push 即可。

## 安装到各 AI 编程工具

将 WSkill 注册到其他 AI 编程 CLI 工具，使其可直接调用这些 skill。

### Claude Code

```bash
# 批量 symlink（全部 skill）
for d in ~/WSkill/*/; do
  name=$(basename "$d")
  [ "$name" = "README.md" ] && continue
  ln -sf "$d" ~/.claude/skills/"$name"
done
```

### OpenClaw

```bash
# 批量 symlink（全部 skill）
for d in ~/WSkill/*/; do
  name=$(basename "$d")
  [ "$name" = "README.md" ] && continue
  ln -sf "$d" ~/.openclaw/skills/"$name"
done
```

### Codex

Codex 无原生 skills 目录，需通过 marketplace 或项目级 `CLAUDE.md` 引入。
将 SKILL.md 内容追加到项目根目录的 `CLAUDE.md` 即可生效。

### OpenCode

OpenCode 无原生 skills 目录。替代方案：

```bash
# 为每个 skill 创建 agent（需 OPENAI_API_KEY）
opencode agent create --path ~/WSkill/<skill-dir> --description "<说明>" --mode subagent
```

或发布为 npm 插件后通过 `opencode plugin` 安装。

> **注意**：Claude Code 和 OpenClaw 的 skills 目录已通过 Hermes 首次配置时自动 setup，通常只需补充 symlink。Codex / OpenCode 的支持取决于后续版本更新。

## 约定

- 每个 skill 一个独立目录，`SKILL.md` + 可选 `references/` 辅助文档
- 不主动合并外部源，不搞聚合

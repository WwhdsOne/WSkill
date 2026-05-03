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
|| `README.md` | 本文件 + 配套 CLI 工具安装命令 |

## 使用方式

配了 Hermes `external_dirs: ["~/WSkill"]`，`skill_view` 和 `skills_list` 直接可见。
需要更新时本地改完 git push 即可。

## 配套 CLI 工具安装

| 工具 | 安装命令 | 说明 |
|------|----------|------|
| OpenCode | `npm i -g opencode-ai` | SST 出品的开源 AI 编程代理 |
| Codex | `npm i -g @openai/codex` | OpenAI 官方编程代理 CLI |
| Claude Code | `npm i -g @anthropic-ai/claude-code` | Anthropic 官方编程代理 CLI |
| OpenClaw | `npm i -g openclaw` | 多通道 AI 网关，可扩展的消息集成 |

```bash
# 一键安装全部
npm i -g opencode-ai @openai/codex @anthropic-ai/claude-code openclaw
```

## 约定

- 每个 skill 一个独立目录，`SKILL.md` + 可选 `references/` 辅助文档
- 不主动合并外部源，不搞聚合

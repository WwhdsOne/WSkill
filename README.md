# WSkill

**WwhdsOne 自建 Hermes Skills 库**

个人开发过程中积累的工具型 Skills 集合。不整合外部内容，不搬运第三方库。

每个 skill 都是实际使用中提炼出来的工作流封装——自用为主，顺手维护。

## 目录

| Skill | 说明 |
|-------|------|
| `redis-diagnostics/` | 纯原生 Redis 诊断（仅 redis-cli + 内置命令） |
| `karpathy-guidelines/` | Karpathy 编码准则（编码前思考/简洁优先/精准修改/目标驱动） |
| `skill-creator/` | Skill 创建与迭代方法论（Anthropic 原版参考） |

## 使用方式

配了 Hermes `external_dirs: ["~/WSkill"]`，`skill_view` 和 `skills_list` 直接可见。
需要更新时本地改完 git push 即可。

## 约定

- 每个 skill 一个独立目录，`SKILL.md` + 可选 `references/` 辅助文档
- 不主动合并外部源，不搞聚合

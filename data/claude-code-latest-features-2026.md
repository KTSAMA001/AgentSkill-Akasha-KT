# Claude Code 最新功能 (2026-06)

**收录日期**：2026-03-10
**来源日期**：2026-06-12
**更新日期**：2026-06-25
**标签**：#ai #tools #reference #claude-code
**来源**：Claude Code 官方 Changelog / What's New / Commands / CLI Reference
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐ (官方文档 + 本机版本交叉验证)
**适用版本**：官方 latest 2.1.176（2026-06-12）；本机验证版本 2.1.111（2026-06-14）

**问题/场景**：

Claude Code 2.1.x 在 2026-04 到 2026-05 频繁更新，需要快速了解当前最新功能、命令变化和对旧记录的影响。

### 概要

截至 2026-06-14，官方 changelog 最新 CLI 版本为 **2.1.176（2026-06-12）**，本机 `claude --version` 为 **2.1.111**。相较 2026-05 的 2.1.142 基线，当前主线已经切到 **Opus 4.8 / Fable 5 / 新模型别名解析 / Fast Mode 默认 Opus 4.8（v2.1.154+）**，认证文档也补充了 **2026-06-15 起订阅计划下 Agent SDK 与 `claude -p` 使用单独月度额度** 的说明。

**解决方案/结论**：

## 版本基线

| 项目 | 结论 |
|------|------|
| 官方 latest | 2.1.176（2026-06-12） |
| 本机版本 | 2.1.111（`claude --version`，2026-06-14） |
| 参考范围 | 官方 changelog 2.1.142 -> 2.1.176；Model Configuration；Fast Mode；Authentication；Models Overview |
| 文档影响 | 旧的 2.1.142 / Opus 4.7 / 本机 2.1.133 基线均需同步修正 |

## 2026-06 高时效变化

| 主题 | 当前结论 |
|------|----------|
| 模型主线 | Anthropic API 上 `opus` 默认解析到 **Opus 4.8**，`sonnet` 解析到 **Sonnet 4.6**；`best` 在有权限时优先走 **Fable 5**，否则回落到最新 Opus；`fable` 成为独立 alias。 |
| Fast Mode | 官方文档确认 **v2.1.154+ 默认 Opus 4.8**，`v2.1.142 ~ v2.1.153` 默认 Opus 4.7；仅支持 Opus 4.8 / 4.7 / 4.6。 |
| 最新 CLI 发布 | `2.1.176`（2026-06-12）新增会话标题按对话语言生成、`footerLinksRegexes`、Bedrock 凭证缓存改进，并修复 `availableModels` 强制、Remote Control、tmux 复制等问题。 |
| 认证与额度 | 官方认证文档新增说明：**从 2026-06-15 起**，订阅计划下 Agent SDK 与 `claude -p` 的使用从单独的月度 Agent SDK credit 扣减。 |

## 当前最值得记住的能力

- 模型 alias：`best` / `fable` / `opus` / `sonnet` / `opus[1m]` / `sonnet[1m]` 现在都有明确的官方解析规则，不能再沿用 2026-05 的旧映射。
- `/fast`：当前默认绑定 Opus 4.8（CLI 2.1.154+），是 Opus 的高速度配置，不是独立模型；且只在 Anthropic API / 订阅 + usage credits 路径可用。
- `claude agents`：统一查看、进入、管理后台会话；2.1.142 新增 `--add-dir`、`--settings`、`--mcp-config`、`--plugin-dir`、`--permission-mode`、`--model`、`--effort`、`--dangerously-skip-permissions` 等分发参数。
- `/goal`：设定完成条件后，Claude 可跨多轮继续推进，适合“直到测试通过/部署完成/PR 处理完”的长任务。
- `/schedule` / `/routines`：云端例行任务，可按计划、GitHub 事件或 API 触发，不依赖本机持续运行。
- `/ultrareview` / `claude ultrareview`：云端多代理代码审查，适合合并前审查关键分支或 PR。
- Windows PowerShell：2.1.126 起 Windows 不再要求 Git Bash；Bash 缺失时使用 PowerShell，且可检测多种 PowerShell 7 安装方式。
- 插件分发：`--plugin-dir` 可加载目录或 `.zip`，`--plugin-url` 可从 URL 拉取插件 zip；根级 `SKILL.md` 插件也能作为 skill 暴露。
- `/config`：2.1.117+ 中 theme/editor/verbose 等配置持久化到 `~/.claude/settings.json`，不再沿用“只在 `~/.claude.json`”的旧结论。

## 命令变化速查

| 命令/标志 | 当前状态 |
|-----------|----------|
| `/cost`、`/stats` | 仍可用，但作为 `/usage` 的入口/别名 |
| `/vim` | 2.1.92 移除，改用 `/config` -> Editor mode |
| `/pr-comments` | 2.1.91 移除；直接让 Claude 查看 PR 评论 |
| `/branch` / `/fork` | `/branch [name]` 是当前会话分支入口；`/fork <directive>` 是后台 forked subagent。2.1.161 以前 `/fork` 曾作为 `/branch` 别名 |
| `/tasks` | 后台任务管理；`/bashes` 为兼容别名 |
| `/background` | 可用 `/bg` 别名，将当前会话转为后台代理 |
| `--enable-auto-mode` | 已移除，用 `--permission-mode auto` |
| `--plugin-url` | 新增，临时从 URL 加载插件 zip |

## 参考链接

- [Claude Code Changelog](https://code.claude.com/docs/en/changelog)
- [Claude Code Model Configuration](https://code.claude.com/docs/en/model-config)
- [Claude Code Fast Mode](https://code.claude.com/docs/en/fast-mode)
- [Claude Code Authentication](https://code.claude.com/docs/en/authentication)
- [Claude Models Overview](https://platform.claude.com/docs/en/about-claude/models/overview)
- [Claude Code Commands](https://code.claude.com/docs/en/commands)
- [Claude Code CLI Reference](https://code.claude.com/docs/en/cli-reference)

### 相关记录

- [Claude Code 完整指南](./claude-code-comprehensive-guide.md) - 当前总览
- [Claude Code 2.1 功能全览](./claude-code-2-1-feature-inventory.md) - 功能域与 flags
- [Claude Code 完整斜杠命令列表](./claude-code-slash-commands.md) - 当前 slash commands
- [Claude Code /config 设置界面配置项说明](./claude-code-config-dialog-settings.md) - `/config` 持久化变化

### 验证记录
- [2026-03-10] 初次记录，来源：官方 CHANGELOG + 博客。
- [2026-05-15] 重写为 2026-05 最新功能摘要。官方 changelog 确认 latest 2.1.142（2026-05-14），本机 `claude --version` 确认为 2.1.133；基于官方 What's New Week 16-19、Commands、CLI Reference 交叉更新。
- [2026-06-14] 时效性复核：官方 changelog 确认 latest 为 2.1.176（2026-06-12），本机 `claude --version` 为 2.1.111；基于 Model Configuration、Fast Mode、Authentication、Models Overview 补充 Opus 4.8 / Fable 5 / alias 解析 / Agent SDK credit 新基线。
- [2026-06-25] 时效性修正：官方 Commands 文档确认 `/branch [name]` 与 `/fork <directive>` 当前语义已分离，官方 CLI Reference 确认 `--fork-session` 是恢复时创建新 session ID 的 flag，需配合 `--resume` 或 `--continue`。

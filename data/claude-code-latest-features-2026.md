# Claude Code 最新功能 (2026-05)

**收录日期**：2026-03-10
**来源日期**：2026-05-14
**更新日期**：2026-05-15
**标签**：#ai #tools #reference #claude-code
**来源**：Claude Code 官方 Changelog / What's New / Commands / CLI Reference
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐ (官方文档 + 本机版本交叉验证)
**适用版本**：官方 latest 2.1.142；本机验证版本 2.1.133

**问题/场景**：

Claude Code 2.1.x 在 2026-04 到 2026-05 频繁更新，需要快速了解当前最新功能、命令变化和对旧记录的影响。

### 概要

截至 2026-05-15，官方 changelog 最新 CLI 版本为 **2.1.142（2026-05-14）**，本机 `claude --version` 为 **2.1.133**。2.1.x 后期的主线变化是：后台代理与 Agent View、云端 Routines、Windows PowerShell 支持、插件分发增强、`/goal` 与 `/ultrareview`、`/config` 持久化迁移、Opus 4.7 `xhigh` effort，以及大量 Windows/MCP/OAuth/内存泄漏修复。

**解决方案/结论**：

## 版本基线

| 项目 | 结论 |
|------|------|
| 官方 latest | 2.1.142（2026-05-14） |
| 本机版本 | 2.1.133（`claude --version`，2026-05-15） |
| 参考范围 | 官方 changelog 2.1.81 -> 2.1.142；What's New Week 16-19 |
| 文档影响 | 旧的 2026-03 功能清单、slash commands、`/config` 存储位置说明均需要更新 |

## 2.1.114 -> 2.1.142 关键新增

| 版本段 | 重点变化 |
|--------|----------|
| 2.1.114-2.1.119 | `/ultrareview` research preview、`/recap`、自定义主题、Web 端重设计、hooks 可调用 MCP tool、`/usage` 合并 `/cost`/`/stats` |
| 2.1.120-2.1.126 | Windows 不再强依赖 Git Bash、`claude auth login` 支持粘贴 OAuth code、`claude project purge`、PR URL 恢复会话、PowerShell 7 自动检测 |
| 2.1.128-2.1.136 | 插件支持 zip/URL 临时加载、Ctrl+R 全项目历史搜索、`worktree.baseRef`、Auto Mode hard deny、`CLAUDE_CODE_PACKAGE_MANAGER_AUTO_UPDATE` |
| 2.1.139-2.1.142 | `claude agents` Agent View、`/goal`、`/scroll-speed`、hook exec-form args、background session flags、Fast Mode 默认 Opus 4.7、插件根级 `SKILL.md` 支持 |

## 当前最值得记住的能力

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
| `/branch` | 会话分支命令，`/fork` 为别名；`CLAUDE_CODE_FORK_SUBAGENT=1` 时 `/fork` 另作 forked subagent |
| `/tasks` | 后台任务管理；`/bashes` 为兼容别名 |
| `/background` | 可用 `/bg` 别名，将当前会话转为后台代理 |
| `--enable-auto-mode` | 已移除，用 `--permission-mode auto` |
| `--plugin-url` | 新增，临时从 URL 加载插件 zip |

## 参考链接

- [Claude Code Changelog](https://code.claude.com/docs/en/changelog)
- [Claude Code What's New Week 19](https://code.claude.com/docs/en/whats-new/2026-w19)
- [Claude Code What's New Week 18](https://code.claude.com/docs/en/whats-new/2026-w18)
- [Claude Code What's New Week 17](https://code.claude.com/docs/en/whats-new/2026-w17)
- [Claude Code What's New Week 16](https://code.claude.com/docs/en/whats-new/2026-w16)
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

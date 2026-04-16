# Claude Code 默认跳过权限配置

**标签**：#claude-code #配置管理 #experience
**来源**：实践总结 + GitHub Issues (#32047, #41526)
**收录日期**：2026-04-16
**来源日期**：2026-04-16
**状态**：✅已验证
**可信度**：⭐⭐⭐⭐
**适用版本**：Claude Code 2.1+

### 概要

通过全局 `settings.json` 配置 `permissions.defaultMode` 为 `bypassPermissions`，使 Claude Code 每次启动默认跳过所有权限检查，无需每次加 `--dangerously-skip-permissions` 参数。

### 内容

#### 权限模式一览

| 模式 | CLI 参数 | 说明 |
|------|----------|------|
| auto | `--permission-mode auto` | 自动批准安全操作，危险操作仍需确认 |
| plan | `--permission-mode plan` | 先出方案，审批后才能执行修改 |
| acceptEdits | `--permission-mode acceptEdits` | 自动批准文件编辑，其他操作仍需确认 |
| bypassPermissions | `--dangerously-skip-permissions` | 跳过所有权限检查（仅限沙箱环境） |

#### 全局默认 bypass 配置

在 `~/.claude/settings.json` 中添加：

```json
{
  "skipDangerousModePermissionPrompt": true,
  "permissions": {
    "defaultMode": "bypassPermissions"
  }
}
```

- `skipDangerousModePermissionPrompt`：跳过进入危险模式的确认提示（仅跳过确认，不跳过权限）
- `permissions.defaultMode`：设置默认权限模式

#### 已知 Bug

全局 `dangerouslySkipPermissions` 或 `defaultMode: "bypassPermissions"` 在部分场景下不完全生效（GitHub Issue #32047, #41526），某些 Bash 命令仍会弹出权限提示。

#### 备选方案

如遇到全局配置不完全生效的情况，可用 shell 别名兜底：

```bash
# ~/.zshrc
alias clauded="claude --dangerously-skip-permissions"
```

### 相关记录

- [claude-code-config-dialog-settings.md](./claude-code-config-dialog-settings.md) - `/config` 设置界面各配置项说明
- [claude-code-comprehensive-guide.md](./claude-code-comprehensive-guide.md) - Claude Code 完整指南

### 验证记录

- [2026-04-16] 初次记录，已实际配置生效

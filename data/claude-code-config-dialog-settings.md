# Claude Code /config 设置界面配置项说明

**标签**：#claude-code #reference #tools
**来源**：实际使用环境截图 + 官方文档
**收录日期**：2026-03-28
**来源日期**：2026-03-28
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐
**适用版本**：Claude Code v2.1.x

### 概要

`/config` 命令打开的设置界面（存储于 `~/.claude.json`，**非** `settings.json`）中各配置项的作用说明。与 `settings.json`（权限、hooks、环境变量等）是两套独立的配置系统。

### 内容

> ⚠️ 这些设置存储在 `~/.claude.json` 中，通过 `/config` 命令或 `claude config set` 修改，**不要**写入 `settings.json`（会触发 schema 验证错误）。

#### 行为控制

| 设置 | 类型 | 默认值 | 作用 |
|------|------|--------|------|
| **Auto-compact** | 开关 | `true` | 上下文窗口快满时自动压缩对话历史，腾出空间继续工作。设为 false 需手动 `/compact` |
| **Show tips** | 开关 | `true` | 等待响应时显示 spinner 提示语（快捷键提示、使用技巧等） |
| **Reduce motion** | 开关 | `false` | 减少终端动画效果，对视觉敏感或光敏用户有用 |
| **Thinking mode** | 开关 | `true` | 启用 extended thinking（深度推理），模型会先进行内部"思考"再输出回答。增加延迟但提升复杂任务质量 |
| **Fast mode** | 开关 | `false` | Opus 4.6 专用加速模式（2.5 倍速，价格更高）。**GLM 代理环境下不适用** |
| **Rewind code (checkpoints)** | 开关 | `true` | 自动保存代码修改快照，按 `Esc+Esc` 可回滚到之前的状态。改代码时建议保持开启 |
| **Verbose output** | 开关 | `false` | 显示每一步的完整工具调用详情（输入、输出、耗时）。日常关闭，排查问题时开启 |

#### 显示

| 设置 | 类型 | 默认值 | 作用 |
|------|------|--------|------|
| **Terminal progress bar** | 开关 | `true` | 长任务（如编译、安装）时在终端显示进度条 |
| **Show turn duration** | 开关 | `true` | 每轮对话完成后显示本轮耗时 |
| **Always copy full response** | 开关 | `false` | `/copy` 时跳过内容选择器，直接复制整个回复到剪贴板 |

#### 文件与更新

| 设置 | 类型 | 默认值 | 作用 |
|------|------|--------|------|
| **Respect .gitignore** | 开关 | `true` | `@` 文件自动补全选择器遵循 `.gitignore` 规则，不显示被忽略的文件 |
| **Auto-update channel** | 选择 | `latest` | 更新频道：`stable`（约一周前的稳定版）/ `latest`（最新版）。注意：`CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1` 会覆盖此设置 |

#### 外观

| 设置 | 类型 | 默认值 | 作用 |
|------|------|--------|------|
| **Theme** | 选择 | Dark mode | 界面主题：Dark mode / Light mode / 高对比度主题等 |

#### 界面未完全显示的更多设置

截图显示 "10 more below"，可能包括：
- **Auto-connect IDE** (`autoConnectIde`) — 启动时自动连接 IDE
- **Auto-install IDE extension** (`autoInstallIdeExtension`) — 自动安装 IDE 扩展
- **Editor mode** (`editorMode`) — 键绑定模式：normal / vim
- **Voice dictation** (`voiceEnabled`) — 语音听写

### 与 settings.json 的区别

| 维度 | `~/.claude.json` (`/config`) | `settings.json` |
|------|------------------------------|-----------------|
| 修改方式 | `/config` 界面 / `claude config set` | 手动编辑 / CLI 标志 |
| 内容 | UI 偏好、外观、行为开关 | 权限、hooks、环境变量、模型 |
| 作用域 | 仅用户全局 | 用户全局 + 项目 + 本地 |
| 版本控制 | 不提交 git | 项目级可提交 git |

### 参考链接

- [Claude Code 官方设置文档](https://code.claude.com/docs/en/settings.md) — 说明两个配置文件的职责划分

### 相关记录

- [claude-code-2.1-feature-inventory.md](./claude-code-2.1-feature-inventory.md) - Claude Code 2.1 功能清单（15 大能力域）
- [claude-code-comprehensive-guide.md](./claude-code-comprehensive-guide.md) - Claude Code 完整指南
- [claude-code-slash-commands.md](./claude-code-slash-commands.md) - 斜杠命令列表

### 验证记录

- [2026-03-28] 初次记录，来源：实际使用环境 `/config` 截图确认 + 官方文档交叉验证

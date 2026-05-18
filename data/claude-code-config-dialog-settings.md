# Claude Code /config 设置界面配置项说明

**标签**：#claude-code #reference #tools
**来源**：实际使用环境截图 + 官方文档
**收录日期**：2026-03-28
**来源日期**：2026-05-14
**更新日期**：2026-05-18
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐
**适用版本**：Claude Code v2.1.25+；2.1.117+ `/config` 持久化行为变化；2.1.142 设置项校验

### 概要
`/config` 命令打开 Claude Code 设置界面。旧版本中大量 UI 偏好存于 `~/.claude.json`；2.1.117 起，主题、编辑器模式、verbose 等 `/config` 变更会持久化到 `~/.claude/settings.json`，并遵循 user / project / local / managed settings 的优先级。

### 内容

> 维护备注：不要再把 `/config` 简化理解为“只写 `~/.claude.json`”。当前版本中可落入 `settings.json` 的配置应按官方 settings schema 维护；会话列表、项目状态等历史/运行态信息仍可能保留在 `~/.claude.json` 一类的全局状态文件中。

#### 登录 / 首次引导状态

Claude Code 的 OAuth 会话、MCP 用户/本地配置、项目信任状态、缓存，以及部分 `/config` 偏好存储在：

```bash
~/.claude.json
```

如果目标是处理“已完成网页登录/首次引导”的状态，不要去 `~/.claude/settings.json` 找。对应字段在 `~/.claude.json` 顶层，例如：

```json
{
  "hasCompletedOnboarding": true
}
```

> 注意：这只表示本地首次引导状态已完成；它不是官方文档中列出的“禁用认证”开关，也不等同于持有可用 OAuth 会话。若要绕过浏览器网页登录改走网关/API，应配置环境变量或 API Key，而不是依赖该字段。

#### 行为控制

| 设置 | 类型 | 默认值 | 作用 |
|------|------|--------|------|
| **Auto-compact** | 开关 | `true` | 上下文窗口快满时自动压缩对话历史，腾出空间继续工作。设为 false 需手动 `/compact` |
| **Show tips** | 开关 | `true` | 等待响应时显示 spinner 提示语（快捷键提示、使用技巧等） |
| **Reduce motion** | 开关 | `false` | 减少终端动画效果，对视觉敏感或光敏用户有用 |
| **Thinking mode** | 开关 | `true` | 启用 extended thinking（深度推理），模型会先进行内部"思考"再输出回答。增加延迟但提升复杂任务质量 |
| **Fast mode** | 开关 | `false` | 快速模式。2.1.142 起默认使用 Opus 4.7；第三方网关/GLM 代理环境下取决于后端是否支持对应模型与 effort |
| **Rewind code (checkpoints)** | 开关 | `true` | 自动保存代码修改快照，按 `Esc+Esc` 可回滚到之前的状态。改代码时建议保持开启 |
| **Verbose output** | 开关 | `false` | 显示每一步的完整工具调用详情（输入、输出、耗时）。日常关闭，排查问题时开启 |

#### 显示

| 设置 | 类型 | 默认值 | 作用 |
|------|------|--------|------|
| **Terminal progress bar** | 开关 | `true` | 长任务（如编译、安装）时在终端显示进度条 |
| **Show turn duration** | 开关 | `true` | 每轮对话完成后显示本轮耗时 |
| **Always copy full response** | 开关 | `false` | `/copy` 时跳过内容选择器，直接复制整个回复到剪贴板 |
| **Focus view / TUI** | 选择 | 视版本而定 | 全屏/聚焦渲染模式，减少长会话滚动干扰；可通过 `/focus`、`/tui` 或 settings 控制 |

#### 文件与更新

| 设置 | 类型 | 默认值 | 作用 |
|------|------|--------|------|
| **Respect .gitignore** | 开关 | `true` | `@` 文件自动补全选择器遵循 `.gitignore` 规则，不显示被忽略的文件 |
| **Auto-update channel** | 选择 | `latest` | 更新频道：`stable`（约一周前的稳定版）/ `latest`（最新版）。注意：`CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1` 会覆盖此设置 |

#### 外观

| 设置 | 类型 | 默认值 | 作用 |
|------|------|--------|------|
| **Theme** | 选择 | Dark mode | 界面主题：Dark / Light / ANSI / 色盲友好主题；2.1.118+ 支持 `~/.claude/themes/` 自定义主题，插件也可携带主题 |

#### 界面未完全显示的更多设置

截图显示 "10 more below"，可能包括：
- **Auto-connect IDE** (`autoConnectIde`) — 启动时自动连接 IDE
- **Auto-install IDE extension** (`autoInstallIdeExtension`) — 自动安装 IDE 扩展
- **Editor mode** (`editorMode`) — 键绑定模式：normal / vim
- **Voice dictation** (`voiceEnabled`) — 语音听写

### 与 settings.json 的关系

| 维度 | `~/.claude.json` / 全局状态 | `~/.claude/settings.json` / settings 层 | 维护判断 |
|------|------------------------------|------------------------------------------|----------|
| 修改方式 | `/config` 界面、`claude config set`、登录/信任流程自动写入 | 手动编辑、CLI flag、managed/project/local settings、部分 `/config` 变更 | 不再使用“`/config` 一律不写 settings”的绝对结论 |
| 内容 | OAuth 会话、MCP 用户/本地配置、项目信任状态、缓存、首次引导状态、部分 UI 偏好 | `env`、permissions、hooks、模型/工具相关设置，以及 2.1.117+ 可持久化的 theme/editor/verbose 等偏好 | 运行态和凭证状态优先查全局状态；工具权限和环境变量优先查 settings |
| 作用域 | 用户全局状态为主 | user / project / local / managed 多来源；CLI flag 通常只影响当前启动 | 同名设置异常时先看 `/status`、`/doctor` 与 settings precedence |
| 版本控制 | 不提交 git | 项目级 settings 可提交 git，本地和个人偏好不应提交 | 仓库内只保留团队共享配置，避免泄露个人 token 或 OAuth 状态 |

### 不用网页登录时的官方路径

如果目标是让 Claude Code CLI 不依赖 Claude.ai 浏览器登录，而是接入本地 Router、LLM Gateway 或第三方 Anthropic-compatible endpoint，应在环境变量中提供凭证：

```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "http://127.0.0.1:3456",
    "ANTHROPIC_AUTH_TOKEN": "***"
  }
}
```

官方认证优先级中，`ANTHROPIC_AUTH_TOKEN` 会作为 `Authorization: Bearer` 发送，适合网关/代理；`ANTHROPIC_API_KEY` 会作为 `X-Api-Key` 发送，适合直连 Claude Console API Key。`apiKeyHelper`、`ANTHROPIC_API_KEY`、`ANTHROPIC_AUTH_TOKEN` 仅适用于终端 CLI 会话，Claude Desktop 和 remote sessions 使用 OAuth。

### 参考链接

- [Claude Code Changelog](https://code.claude.com/docs/en/changelog) - 2.1.117+ `/config` 持久化变化、2.1.142 最新版本
- [Claude Code Commands](https://code.claude.com/docs/en/commands) - `/config`、`/theme`、`/focus`、`/tui` 等命令
- [Claude Code CLI Reference](https://code.claude.com/docs/en/cli-reference) - CLI flag 与 settings 关系
- [Claude Code 官方设置文档](https://docs.anthropic.com/en/docs/claude-code/settings) — 说明两个配置文件的职责划分
- [Claude Code 官方认证文档](https://docs.anthropic.com/en/docs/claude-code/authentication) — 说明认证方式与优先级

### 相关记录

- [claude-code-2-1-feature-inventory.md](./claude-code-2-1-feature-inventory.md) - Claude Code 2.1 功能清单（15 大能力域）
- [claude-code-comprehensive-guide.md](./claude-code-comprehensive-guide.md) - Claude Code 完整指南
- [claude-code-slash-commands.md](./claude-code-slash-commands.md) - 斜杠命令列表

### 验证记录
- [2026-03-28] 初次记录，来源：实际使用环境 `/config` 截图确认 + 官方文档交叉验证
- [2026-05-15] 修正旧结论：官方 2.1.117+ 记录显示 `/config` 的 theme/editor/verbose 等变更会持久化到 `~/.claude/settings.json`，不再沿用“不要写入 settings.json”的绝对说法；同步补充 Opus 4.7 Fast Mode、TUI/Focus、自定义主题等新设置。
- [2026-05-18] 验证 Claude Code v2.1.25 配置分层：`~/.claude.json` 存放 OAuth session、MCP 用户/本地配置、项目状态、缓存及 `hasCompletedOnboarding`；`~/.claude/settings.json` 适合放 `env`、permissions、hooks 等。补充通过 `ANTHROPIC_BASE_URL` + `ANTHROPIC_AUTH_TOKEN`/`ANTHROPIC_API_KEY` 改走 Router/Gateway 的认证路径。
- [2026-05-18] 合并校验：将“`/config` 不写 settings.json”的旧边界与 2.1.117+ 持久化变化合并为分层判断表；保留网页登录/首次引导状态与网关认证路径说明，避免与综合指南和后端模型记录重复展开。

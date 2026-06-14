# Claude Code 完整指南

**标签**：#claude-code #tools #reference
**来源**：官方文档 + 实践经验
**收录日期**：2026-01-30
**来源日期**：2026-06-12
**更新日期**：2026-06-14
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐（官方文档验证）
**适用版本**：Claude Code v2.1.176（官方 latest，2026-06-12）；本机 `claude --version` 为 2.1.111（2026-06-14 验证）

### 概要
Claude Code 是 Anthropic 推出的 AI 编程助手，支持终端 CLI、桌面应用、Web、VS Code 和 JetBrains IDE 五大入口。截至 2026-06-14，官方 latest 为 2.1.176（2026-06-12），本机 `claude --version` 为 2.1.111。当前主线已切到 **Opus 4.8 / Sonnet 4.6 / Fable 5 alias**，Fast Mode 在 `v2.1.154+` 默认绑定 Opus 4.8。

### 内容

## 一、Claude Code 是什么？

Claude Code 是 Anthropic 推出的**终端原生 AI 编程助手**，现已扩展为多平台产品：

| 平台 | 入口 | 特点 |
|------|------|------|
| **CLI** | `claude` 命令 | 终端原生，功能最完整 |
| **Desktop** | Claude 桌面端 "Code" 标签 | 可视化 Diff、实时预览、Computer Use(macOS)、GitHub PR 监控、调度任务 |
| **Web** | claude.ai/code | 浏览器运行，无需本地安装，云端执行 |
| **VS Code** | 扩展市场 | Diff 查看、文件引用、Git Worktree |
| **JetBrains** | 插件市场 | IntelliJ/PyCharm/WebStorm 等 |

**核心定位**：项目级开发助手，而非文件级代码补全工具

## 二、核心优势

| 优势 | 说明 |
|------|------|
| **1M 上下文窗口** | Opus 4.8 / Sonnet 4.6 提供 1M 上下文；Haiku 4.5 为 200K，适合按任务分层使用 |
| **项目级视野** | 扫描整个代码库，全局理解架构 |
| **直接操作** | 编辑文件、运行命令、创建提交 |
| **多代理协调** | Subagents、Agent View、后台任务、Worktree 隔离 |
| **插件生态** | 插件可捆绑 skills、agents、hooks、MCP、LSP，并支持本地目录、zip、URL 临时加载 |
| **Hook 自动化** | 支持命令、HTTP、prompt、agent 及 MCP tool 调用 |
| **跨平台** | CLI + Desktop + Web + VS Code + JetBrains |
| **跨设备** | Remote Control、Mobile push、Web/CLI/桌面会话迁移 |

## 三、安装方式

```bash
# macOS / Linux / WSL
curl -fsSL https://claude.ai/install.sh | bash

# Windows PowerShell
irm https://claude.ai/install.ps1 | iex

# Windows CMD
curl -fsSL https://claude.ai/install.cmd -o install.cmd && install.cmd && del install.cmd

# Homebrew (macOS)
brew install --cask claude-code

# WinGet (Windows)
winget install Anthropic.ClaudeCode

# IDE 扩展
# VS Code / JetBrains / Cursor → 各自扩展市场搜索 "Claude Code"
```

## 四、认证与配置文件分层

Claude Code 认证与配置分散在两类文件中，排查“网页登录验证/首次引导/API 网关接入”时不要混淆：

> 维护备注：本节只保留排障入口级摘要，避免与专题记录重复展开；`/config` 与 settings 边界维护在 `claude-code-config-dialog-settings.md`，模型后端和 LLM Gateway 维护在 `claude-code-backend-models.md`。

| 文件/位置 | 主要内容 | 典型用途 |
|-----------|----------|----------|
| `~/.claude.json` | OAuth session、MCP 用户/本地配置、项目信任状态、缓存、`/config` 偏好 | `/config` 设置、首次引导状态、登录/信任状态 |
| `~/.claude/settings.json` | `env`、permissions、hooks、模型/工具相关设置 | CLI 全局环境变量、权限规则、Hook 自动化 |
| VS Code `settings.json` | `claudeCode.environmentVariables` | 给 VS Code Claude Code 插件注入环境变量 |

如果只是处理首次引导完成状态，字段在 `~/.claude.json` 顶层：

```json
{
  "hasCompletedOnboarding": true
}
```

如果目标是不用 Claude.ai 浏览器网页登录，改走本地 Router、LLM Gateway 或 Anthropic-compatible endpoint，应配置凭证环境变量，而不是寻找 `settings.json` 中的“关闭验证”开关：

```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "http://127.0.0.1:3456",
    "ANTHROPIC_AUTH_TOKEN": "***"
  }
}
```

认证优先级上，`ANTHROPIC_AUTH_TOKEN` 作为 `Authorization: Bearer` 发送，适合网关/代理；`ANTHROPIC_API_KEY` 作为 `X-Api-Key` 发送，适合 Claude Console API Key。上述 API Key / Auth Token / apiKeyHelper 仅适用于终端 CLI 会话；Claude Desktop 和 remote sessions 仍使用 OAuth。

## 五、支持模型

| 模型 | 状态 | 特点 |
|------|------|------|
| **Claude Fable 5** | GA（按账号/组织可用性） | 最难、最长任务优先；`best` 在有权限时会优先选它 |
| **Claude Opus 4.8** | GA | Anthropic API 当前最新 Opus，1M 上下文，复杂推理与 agentic coding 主线 |
| **Claude Sonnet 4.6** | GA | 日常编码主力，1M 上下文，速度与智能平衡 |
| **Claude Haiku 4.5** | GA | 最快，200K 上下文，低成本高吞吐 |
| Claude Opus 4.7 / 4.6 | 仍可见于部分 provider / 迁移场景 | Claude Platform on AWS 或旧 provider alias 下仍可能命中 |
| Claude Sonnet 3.7 / Haiku 3.x | 已退役/不建议 | 旧模型请求可能报错或被路由替代 |

Fast Mode（`/fast`）：研究预览能力，只支持 Opus 4.8 / 4.7 / 4.6。`v2.1.154+` 默认使用 Opus 4.8，`v2.1.142 ~ v2.1.153` 默认使用 Opus 4.7。它要求 Anthropic API 或订阅 + usage credits，不适用于 Bedrock / Vertex / Foundry / Claude Platform on AWS。

## 六、权限模式

| 模式 | 切换 | 适用 |
|------|------|------|
| **默认** | - | 所有操作需手动确认，适合新手 |
| **Plan** | Shift+Tab | 只读探索，生成计划后确认再执行 |
| **Auto** | - | AI 分类器评估每个工具调用 |
| **DontAsk** | - | 自动拒绝权限提示 |
| **AcceptEdits** | - | 自动接受文件编辑 |
| **Bypass** | `--dangerously-skip-permissions` | 跳过所有权限提示（仅 CLI/headless） |

可通过 `/permissions` 配置信任路径和工具规则。

### 全局默认 Bypass 配置

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

> **已知 Bug**：全局 `dangerouslySkipPermissions` 或 `defaultMode: "bypassPermissions"` 在部分场景下不完全生效（GitHub Issue #32047, #41526），某些 Bash 命令仍会弹出权限提示。

**备选方案**：如遇到全局配置不完全生效，可用 shell 别名兜底：

```bash
# ~/.zshrc
alias clauded="claude --dangerously-skip-permissions"
```

## 七、核心功能

### 7.1 代码生成与编辑
自然语言转代码，支持 React/Vue/Svelte/Unity/Python 等 40+ 语言。

### 7.2 调试修复
粘贴错误日志或截图（Windows: `Alt+V`），自动定位并修复。

### 7.3 代码库导航
`@文件路径` 引用文件，扫描整个项目理解架构。

### 7.4 自动化任务
重构、lint 修复、Git 冲突处理、文档生成、测试编写。

### 7.5 Subagents（子代理）
独立的 AI 实例执行特定任务：

| 能力 | 说明 |
|------|------|
| **Worktree 隔离** | `isolation: worktree`，独立 Git 副本，互不冲突 |
| **持久记忆** | `memory: user/project/local`，跨会话知识积累 |
| **后台运行** | `background: true`，不阻塞主对话 |
| **模型选择** | 可指定不同模型（Explore 默认用 Haiku） |
| **工具限制** | 可禁用特定工具（如 Explore 禁止文件修改） |
| **CLI 定义** | `--agents` JSON 或 `/agents` 命令管理 |

内置代理类型：`general-purpose`（全工具）、`Explore`（只读搜索）、`Plan`（架构规划）、`verification`（对抗验证）。

### 7.6 Agent Teams（多代理协调，实验性）
多个 Claude Code 实例作为团队协作：

```bash
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
```

- Team Lead 协调多个 Teammate 并行工作
- 共享任务列表，支持依赖关系
- 同伴间可直接通信（mailbox 系统）
- 通过 Hook 实现质量门控

### 7.7 Hooks（自动化钩子）
20+ 事件，3 种类型：

| 类型 | 说明 |
|------|------|
| `command` | 执行 shell 命令 |
| `prompt` | 单轮 LLM 评估（默认 Haiku） |
| `agent` | 多轮验证（最多 50 轮） |
| `http` | POST 事件到 URL |

关键事件：`UserPromptSubmit`、`PreToolUse`、`PostToolUse`、`InstructionsLoaded`、`ConfigChange`、`CwdChanged`、`FileChanged`、`PreCompact`/`PostCompact`、`SessionEnd`、`SubagentStart`/`SubagentStop`、`TeammateIdle`、`Elicitation`、`PermissionDenied`、`StopFailure` 等。

Hook 可返回 `additionalContext` 注入上下文，支持 `if` 字段按工具名+参数过滤。

### 7.8 Plugins（插件系统）
50+ 官方插件，可捆绑 skills + agents + hooks + MCP：

```
# 官方插件示例
typescript-lsp    — TypeScript 语言服务
security-guidance — 安全审计
context7           — 文档上下文
playwright         — 浏览器自动化
code-review        — 多代理并行 PR 审查
```

安装：`claude plugins add <name>`，管理：`/plugins`。

### 7.9 Skills（技能系统）
自定义提示词模板，frontmatter 控制触发模式：

| 配置 | 效果 |
|------|------|
| 默认 | Claude 自动触发 + 用户 `/skill` 手动触发 |
| `disable-model-invocation: true` | 仅手动触发 |
| `user-invocable: false` | 仅 Claude 自动触发 |

### 7.10 Scheduled Tasks（定时任务）
- CLI：`/loop 5m /review` 或 CronCreate 工具
- Desktop：本地定时（需应用打开）
- Web/Cloud：云端定时（Anthropic 基础设施）

### 7.11 Remote Control（远程控制）
本地会话可通过 `claude.ai/code` 或 Claude 移动端继续，支持跨设备。

### 7.12 Channels（外部集成，预览）
从 Telegram、Discord、iMessage 或自定义 webhook 接收事件推送到会话。

### 7.13 Sandboxing（沙箱隔离）
OS 级文件系统和网络隔离，防止恶意操作。

## 八、交互技巧

| 技巧 | 用法 |
|------|------|
| 文件提及 | `@src/App.tsx` |
| Bash 模式 | `! git status` |
| 多行输入 | `Shift+Enter` |
| 历史搜索 | `Ctrl+R` |
| Plan 模式 | `Shift+Tab` 切换 |
| Fast 模式 | `/fast` 切换 |
| 压缩上下文 | `/compact` |
| 侧边问题 | `/btw <问题>` 无工具单轮回答 |
| Agent 管理 | `/agents` 查看/创建/编辑子代理 |
| 插件管理 | `/plugins` |
| 查看成本 | `/cost` |

## 九、CLAUDE.md 与记忆

### CLAUDE.md 层级

| 层级 | 位置 | 用途 |
|------|------|------|
| 项目 | `项目/CLAUDE.md` | 项目规范（提交到 Git） |
| 用户 | `~/.claude/CLAUDE.md` | 个人偏好 |
| 组织 | 管理设置 | 团队统一 |
| 规则目录 | `.claude/rules/*.md` | 路径特定的细粒度规则 |
| AGENTS.md | `项目/AGENTS.md` | 子代理定义 |

### Auto Memory（自动记忆）
- Claude Code 自动将值得记住的信息写入 `~/.claude/projects/.../memory/`
- 使用 Sonnet 作为廉价选择器，最多选 5 条相关记忆
- MEMORY.md 是索引，单条不超过 150 字符

## 十、MCP 扩展

| 传输方式 | 用途 |
|----------|------|
| stdio | 本地 MCP 服务器 |
| HTTP/SSE | 远程 MCP 服务器 |
| SDK | 程序化连接 |

作用域：`local`（仅本机）、`project`（项目级）、`user`（用户级）。

支持将 Claude Code **本身作为 MCP 服务器**暴露给其他工具。

## 十一、第三方部署

| 平台 | 文档 |
|------|------|
| **Amazon Bedrock** | IAM 认证，Guardrails |
| **Google Vertex AI** | 区域配置，凭证 |
| **Microsoft Foundry** | Azure 预配，RBAC |
| **LLM Gateway** | LiteLLM 等网关配置 |

## 十二、Agent SDK
程序化使用 Claude Code，适用于 CI/CD 自动化：

- GitHub Actions / GitLab CI/CD 自动 PR 审查和 issue 分类
- 构建自定义工作流代理

## 十三、与 VS Code Copilot 对比

| 特性 | VS Code Copilot | Claude Code |
|------|----------------|-------------|
| 定位 | 文件级代码补全 | 项目级开发助手 |
| 上下文 | 单文件为主 | 1M token |
| 核心功能 | 实时补全 | 全局规划、自动化、调试、多代理 |
| 推荐用法 | 搭配使用 | 搭配使用 |

两者是**互补关系**，建议同时使用。

## 十四、新增/不常用功能速查

| 功能 | 说明 |
|------|------|
| Voice Dictation | 语音输入（设置 → Voice Dictation） |
| Output Styles | 自定义输出格式（设置 → Output Styles） |
| Statusline | 可配置状态栏（上下文/Git/费用） |
| Computer Use (CLI) | 终端直接操控屏幕（macOS） |
| Chrome Integration | 浏览器自动化（测试/调试/表单） |
| Checkpointing | 自动追踪 Git 状态，支持回滚 |
| Headless Mode | 非交互模式，结构化输出（CI/CD） |
| Managed Settings | 组织级统一配置下发 |
| Agent View | `claude agents` 统一查看运行中、阻塞和完成的后台会话 |
| Goal | `/goal` 设定完成条件，让 Claude 跨多轮继续推进直到达成目标 |
| Routines | `/schedule` / `/routines` 在云端按计划、GitHub 事件或 API 触发任务 |
| Ultrareview | `/ultrareview` 或 `claude ultrareview` 在云端多代理深度审查 PR/分支 |
| Project Purge | `claude project purge` 清理某项目本地 transcript、任务、历史和配置入口 |
| Plugin URL/Zip | `--plugin-url` 和 `--plugin-dir <zip>` 临时加载插件包 |
| Windows PowerShell | Windows 不再强依赖 Git Bash；可检测并优先使用 PowerShell 7 |

## 十五、最佳实践

1. **善用 CLAUDE.md**：记录项目规范，避免重复解释
2. **合理使用权限模式**：信任场景用 Auto/Bypass，复杂任务用 Plan
3. **配置 .claudeignore**：排除 `node_modules/`、`dist/` 等
4. **利用 Worktree**：子代理用 `isolation: worktree` 实现并行开发
5. **Hook 自动化**：格式化、lint、提交规范自动执行
6. **定期压缩上下文**：`/compact` 或自动压缩
7. **Plugin 生态**：探索官方插件提升效率
8. **Agent Teams**：大型重构用多实例并行
9. **结合 Copilot**：实时补全 + 项目级规划 = 最佳组合

## 十六、常见问题

| 问题 | 解决方案 |
|------|---------|
| 命令未找到 | 检查 PATH，或用 `winget install Anthropic.ClaudeCode` |
| 认证失败 | `/logout` 退出后重新授权 |
| 权限被拒 | `/permissions` 配置信任路径 |
| 性能慢 | `/compact` 压缩上下文，配置 `.claudeignore` |
| 上下文不足 | 使用 1M 上下文模型，或通过 `/context all` / `/compact` 定位高占用来源 |
| Hook 不生效 | 检查 settings.json 中的 hooks 配置 |
| Windows 找不到 Bash | 2.1.126+ 可走 PowerShell；仍异常时检查 PowerShell 7、PATH 和终端权限 |

### 参考链接

- [Claude Code 官方文档](https://code.claude.com/docs/en) — 完整文档（70+ 页面）
- [Claude Code Changelog](https://code.claude.com/docs/en/changelog) — CLI 发布记录
- [Claude Code Commands](https://code.claude.com/docs/en/commands) — 当前 slash commands 参考
- [Claude Code CLI Reference](https://code.claude.com/docs/en/cli-reference) — CLI 子命令与 flags
- [MCP 官方规范](https://modelcontextprotocol.io/)
- [Hooks Reference](https://code.claude.com/docs/en/hooks) — Hook 自动化
- [Plugins Reference](https://code.claude.com/docs/en/plugins-reference) — 插件系统

### 相关记录

- [完整斜杠命令列表](./claude-code-slash-commands.md) — 更多命令用法
- [接入多种模型 (GLM/Bedrock)](./claude-code-backend-models.md) — 模型配置
- [Fork 会话功能](./claude-code-fork-session.md) — 多方案探索
- [2.1 功能清单](./claude-code-2-1-feature-inventory.md) — 功能清单
- [Skill Hook 触发](./claude-code-skill-hook-trigger-boost.md) — 触发率提升
- [源码架构分析](./claude-code-source-architecture.md) — 内部设计原理

### 验证记录
- [2026-01-30] 初次记录，来源：官方文档 + 实践经验整合
- [2026-04-02] 重大更新：基于 code.claude.com 最新文档全面重写。新增 Agent Teams、Plugins、Hooks、Subagents、Desktop/Web/JetBrains 平台、1M 上下文、Remote Control、Channels、Agent SDK、Scheduled Tasks、Sandboxing、Output Styles、Statusline、Voice Dictation 等内容。更新模型信息（Opus 4.6/Sonnet 4.6/Haiku 4.5 GA，旧版退役）。安装方式扩展至 7 种。权限模式从 3 种更新至 5 种。
- [2026-04-17] 合并 claude-code-bypass-permissions.md 独有内容（全局默认 Bypass 配置、已知 Bug #32047/#41526、shell 别名兜底方案）到权限模式章节。删除独立 bypass-permissions 记录，统一维护入口。
- [2026-05-15] 时效性更新：官方 changelog 确认 latest 为 2.1.142（2026-05-14），本机 `claude --version` 为 2.1.133。补充 2.1.114-2.1.142 期间的 Agent View、`/goal`、Routines、`/ultrareview`、插件 zip/url、Windows PowerShell、`claude project purge`、Opus 4.7 Fast Mode 等变化。
- [2026-05-18] 补充 Claude Code v2.1.25 认证与配置分层：`~/.claude.json` 负责 OAuth/首次引导/信任状态，`~/.claude/settings.json` 负责 CLI env/permissions/hooks；改走 Router/Gateway 应配置 `ANTHROPIC_BASE_URL` + `ANTHROPIC_AUTH_TOKEN`/`ANTHROPIC_API_KEY`，不是寻找“关闭网页登录验证”的 settings 开关。同步完成与配置、模型后端专题记录的重复内容边界校验。
- [2026-06-14] 时效性复核：官方 latest 升至 2.1.176（2026-06-12），本机 `claude --version` 为 2.1.111；主线模型切到 Opus 4.8 / Sonnet 4.6，新增 `best/fable` alias 语义，Fast Mode 默认模型更新为 Opus 4.8（v2.1.154+）。

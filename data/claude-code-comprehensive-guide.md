# Claude Code 完整指南

**标签**：#claude-code #tools #reference
**来源**：官方文档 + 实践经验
**收录日期**：2026-01-30
**来源日期**：2026-04-02
**更新日期**：2026-04-02
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐（官方文档验证）
**适用版本**：Claude Code v2.1.88+

### 概要
Claude Code 是 Anthropic 推出的 AI 编程助手，支持终端 CLI、桌面应用、Web 浏览器、VS Code 和 JetBrains IDE 五大平台，提供 1M token 上下文窗口、多代理协调、插件系统、Hook 自动化等能力。

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
| **1M 上下文窗口** | Opus 4.6 / Sonnet 4.6 标准定价（GA） |
| **项目级视野** | 扫描整个代码库，全局理解架构 |
| **直接操作** | 编辑文件、运行命令、创建提交 |
| **多代理协调** | Agent Teams、Subagents、Worktree 隔离 |
| **插件生态** | 50+ 官方插件，可捆绑 skills + hooks + MCP |
| **Hook 自动化** | 20+ 事件类型，prompt/agent/http 三种 Hook |
| **跨平台** | CLI + Desktop + Web + VS Code + JetBrains |
| **跨设备** | Remote Control：本地会话在手机/浏览器继续 |

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

## 四、支持模型

| 模型 | 状态 | 特点 |
|------|------|------|
| **Claude Opus 4.6** | GA | 最智能，自适应思考，1M 上下文，Fast Mode（预览） |
| **Claude Sonnet 4.6** | GA | 接近 Opus 的编码性能，1M 上下文，低 token 消耗 |
| **Claude Haiku 4.5** | GA | 最快，Explore 代理默认 |
| Claude Opus 4.5 / Sonnet 4.5 | GA | 前代 |
| Claude Sonnet 3.7 / Haiku 3.5 | 已退役 | 请求报错 |
| Claude Haiku 3 | 即将退役 | 预计 2026-04-19 |

Fast Mode（`/fast`）：同一 Opus 4.6 模型加速输出，不切换到其他模型。

## 五、权限模式

| 模式 | 切换 | 适用 |
|------|------|------|
| **默认** | - | 所有操作需手动确认，适合新手 |
| **Plan** | Shift+Tab | 只读探索，生成计划后确认再执行 |
| **Auto** | - | AI 分类器评估每个工具调用 |
| **DontAsk** | - | 自动拒绝权限提示 |
| **AcceptEdits** | - | 自动接受文件编辑 |
| **Bypass** | - | 跳过所有权限提示（仅 CLI/headless） |

可通过 `/permissions` 配置信任路径和工具规则。

## 六、核心功能

### 6.1 代码生成与编辑
自然语言转代码，支持 React/Vue/Svelte/Unity/Python 等 40+ 语言。

### 6.2 调试修复
粘贴错误日志或截图（Windows: `Alt+V`），自动定位并修复。

### 6.3 代码库导航
`@文件路径` 引用文件，扫描整个项目理解架构。

### 6.4 自动化任务
重构、lint 修复、Git 冲突处理、文档生成、测试编写。

### 6.5 Subagents（子代理）
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

### 6.6 Agent Teams（多代理协调，实验性）
多个 Claude Code 实例作为团队协作：

```bash
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
```

- Team Lead 协调多个 Teammate 并行工作
- 共享任务列表，支持依赖关系
- 同伴间可直接通信（mailbox 系统）
- 通过 Hook 实现质量门控

### 6.7 Hooks（自动化钩子）
20+ 事件，3 种类型：

| 类型 | 说明 |
|------|------|
| `command` | 执行 shell 命令 |
| `prompt` | 单轮 LLM 评估（默认 Haiku） |
| `agent` | 多轮验证（最多 50 轮） |
| `http` | POST 事件到 URL |

关键事件：`UserPromptSubmit`、`PreToolUse`、`PostToolUse`、`InstructionsLoaded`、`ConfigChange`、`CwdChanged`、`FileChanged`、`PreCompact`/`PostCompact`、`SessionEnd`、`SubagentStart`/`SubagentStop`、`TeammateIdle`、`Elicitation`、`PermissionDenied`、`StopFailure` 等。

Hook 可返回 `additionalContext` 注入上下文，支持 `if` 字段按工具名+参数过滤。

### 6.8 Plugins（插件系统）
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

### 6.9 Skills（技能系统）
自定义提示词模板，frontmatter 控制触发模式：

| 配置 | 效果 |
|------|------|
| 默认 | Claude 自动触发 + 用户 `/skill` 手动触发 |
| `disable-model-invocation: true` | 仅手动触发 |
| `user-invocable: false` | 仅 Claude 自动触发 |

### 6.10 Scheduled Tasks（定时任务）
- CLI：`/loop 5m /review` 或 CronCreate 工具
- Desktop：本地定时（需应用打开）
- Web/Cloud：云端定时（Anthropic 基础设施）

### 6.11 Remote Control（远程控制）
本地会话可通过 `claude.ai/code` 或 Claude 移动端继续，支持跨设备。

### 6.12 Channels（外部集成，预览）
从 Telegram、Discord、iMessage 或自定义 webhook 接收事件推送到会话。

### 6.13 Sandboxing（沙箱隔离）
OS 级文件系统和网络隔离，防止恶意操作。

## 七、交互技巧

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

## 八、CLAUDE.md 与记忆

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

## 九、MCP 扩展

| 传输方式 | 用途 |
|----------|------|
| stdio | 本地 MCP 服务器 |
| HTTP/SSE | 远程 MCP 服务器 |
| SDK | 程序化连接 |

作用域：`local`（仅本机）、`project`（项目级）、`user`（用户级）。

支持将 Claude Code **本身作为 MCP 服务器**暴露给其他工具。

## 十、第三方部署

| 平台 | 文档 |
|------|------|
| **Amazon Bedrock** | IAM 认证，Guardrails |
| **Google Vertex AI** | 区域配置，凭证 |
| **Microsoft Foundry** | Azure 预配，RBAC |
| **LLM Gateway** | LiteLLM 等网关配置 |

## 十一、Agent SDK
程序化使用 Claude Code，适用于 CI/CD 自动化：

- GitHub Actions / GitLab CI/CD 自动 PR 审查和 issue 分类
- 构建自定义工作流代理

## 十二、与 VS Code Copilot 对比

| 特性 | VS Code Copilot | Claude Code |
|------|----------------|-------------|
| 定位 | 文件级代码补全 | 项目级开发助手 |
| 上下文 | 单文件为主 | 1M token |
| 核心功能 | 实时补全 | 全局规划、自动化、调试、多代理 |
| 推荐用法 | 搭配使用 | 搭配使用 |

两者是**互补关系**，建议同时使用。

## 十三、新增/不常用功能速查

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

## 十四、最佳实践

1. **善用 CLAUDE.md**：记录项目规范，避免重复解释
2. **合理使用权限模式**：信任场景用 Auto/Bypass，复杂任务用 Plan
3. **配置 .claudeignore**：排除 `node_modules/`、`dist/` 等
4. **利用 Worktree**：子代理用 `isolation: worktree` 实现并行开发
5. **Hook 自动化**：格式化、lint、提交规范自动执行
6. **定期压缩上下文**：`/compact` 或自动压缩
7. **Plugin 生态**：探索官方插件提升效率
8. **Agent Teams**：大型重构用多实例并行
9. **结合 Copilot**：实时补全 + 项目级规划 = 最佳组合

## 十五、常见问题

| 问题 | 解决方案 |
|------|---------|
| 命令未找到 | 检查 PATH，或用 `winget install Anthropic.ClaudeCode` |
| 认证失败 | `/logout` 退出后重新授权 |
| 权限被拒 | `/permissions` 配置信任路径 |
| 性能慢 | `/compact` 压缩上下文，配置 `.claudeignore` |
| 上下文不足 | 使用 1M 上下文模型（Opus 4.6 / Sonnet 4.6） |
| Hook 不生效 | 检查 settings.json 中的 hooks 配置 |

### 参考链接

- [Claude Code 官方文档](https://code.claude.com/docs/en) — 完整文档（70+ 页面）
- [Claude Code 文档地图](https://code.claude.com/docs/en/claude_code_docs_map.md) — 所有文档页索引
- [MCP 官方规范](https://modelcontextprotocol.io/)
- [Agent Teams 文档](https://code.claude.com/docs/en/agent-teams) — 多代理协调
- [Subagents 文档](https://code.claude.com/docs/en/sub-agents) — 子代理配置
- [Hooks 指南](https://code.claude.com/docs/en/hooks-guide) — Hook 自动化
- [Desktop 文档](https://code.claude.com/docs/en/desktop) — 桌面应用
- [Plugins 文档](https://code.claude.com/docs/en/discover-plugins) — 插件系统

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

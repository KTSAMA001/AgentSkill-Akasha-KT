# Claude Code 2.1 功能全览

**标签**：#claude-code #reference #tools #ai
**来源**：官方文档 + CLI `--help` 输出 + Changelog + 社区实践
**收录日期**：2026-03-25
**来源日期**：2026-03-20（v2.1.81 发布日）
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐⭐ (官方文档 + CLI 实测)
**适用版本**：Claude Code 2.1.81 (2026-03-20)

### 概要

Claude Code 2.1.81 完整功能清单，涵盖 15 大能力域：交互模式、内置工具、多代理、会话管理、非交互/SDK 模式、Git 集成、MCP、Hooks、Plugin、Skill、IDE 集成、Memory、Chrome 集成、结构化输出、CLI 标志与环境变量。

---

### 一、交互模式（Permission Modes）

| 模式 | CLI 参数 | 行为 |
|------|----------|------|
| default | `--permission-mode default` | 每次工具调用需用户确认 |
| auto | `--permission-mode auto` | 自动批准安全操作，危险操作仍需确认 |
| plan | `--permission-mode plan` | 先出方案，审批后才能执行修改 |
| acceptEdits | `--permission-mode acceptEdits` | 自动批准文件编辑，其他操作仍需确认 |
| bypassPermissions | `--dangerously-skip-permissions` | 跳过所有权限检查（仅限沙箱环境） |
| dontAsk | — | 对预批准工具永不询问 |

---

### 二、内置工具（Built-in Tools）

#### 文件操作

| 工具 | 功能 | 备注 |
|------|------|------|
| Read | 读文件、图片、PDF（分页）、Jupyter notebook | 默认 2000 行上限，25K tokens / 256KB |
| Write | 创建/覆盖文件 | UTF-8 only |
| Edit | 精确字符串替换（diff 式） | old_string 必须唯一 |
| NotebookEdit | 编辑 Jupyter notebook 单元格 | 支持 insert / replace / delete |

#### 搜索

| 工具 | 功能 | 备注 |
|------|------|------|
| Glob | 按 glob 模式查找文件 | 返回按修改时间排序的匹配路径 |
| Grep | 基于 ripgrep 的正则内容搜索 | 支持文件类型过滤、上下文行数 |

#### 执行

| 工具 | 功能 | 备注 |
|------|------|------|
| Bash | 执行任意 shell 命令 | 支持后台运行、超时配置、沙箱隔离 |

#### Agent 与任务

| 工具 | 功能 | 备注 |
|------|------|------|
| Agent | 生成子代理 | 可指定类型/模型/worktree 隔离/后台运行 |
| TaskCreate | 创建待办任务 | 支持描述、依赖关系、负责人 |
| TaskUpdate | 更新任务状态 | pending / in_progress / completed / deleted |
| TaskList | 列出所有任务 | 含状态、阻塞关系 |
| TaskGet | 获取任务详情 | 含完整描述和上下文 |
| CronCreate | 创建定时任务 | cron 语法，支持一次性/周期性 |
| CronDelete | 取消定时任务 | — |
| CronList | 列出所有定时任务 | — |

#### 交互

| 工具 | 功能 | 备注 |
|------|------|------|
| AskUserQuestion | 向用户提问 | 支持单选/多选/文本/代码预览 |

#### 会话控制

| 工具 | 功能 | 备注 |
|------|------|------|
| EnterPlanMode | 进入规划模式 | 设计方案后再执行 |
| ExitPlanMode | 退出规划模式 | 提交方案供用户审批 |
| EnterWorktree | 进入 git worktree 隔离 | 创建新分支独立工作 |
| ExitWorktree | 退出 worktree | 可选择 keep / remove |
| Skill | 调用技能 | — |
| WebSearch | 内置网络搜索 | — |

---

### 三、多代理系统（Multi-Agent）

#### SubAgent

| 特性 | 说明 |
|------|------|
| 可用类型 | general-purpose / Explore / Plan / claude-code-guide / glm-plan-* |
| 模型覆盖 | 可指定 sonnet / opus / haiku |
| 后台运行 | `run_in_background: true`，完成后自动通知 |
| Worktree 隔离 | `isolation: "worktree"` 在独立 git 分支工作 |
| 通信 | SendMessage 向已停止代理发消息（自动恢复） |
| 限制 | 嵌套深度有限（建议不超过 2 层），启动有上下文开销 |

#### Agent Teams（tmux 多面板协作）

| 特性 | 说明 |
|------|------|
| 启动方式 | `--worktree --tmux` |
| tmux 模式 | `--tmux=classic` 或 iTerm2 原生面板（默认） |
| 多实例 | 多个 Claude 实例共享/独立工作 |

#### Custom Agents

| 特性 | 说明 |
|------|------|
| 定义位置 | `.claude/agents/*.md` |
| 配置项 | description / prompt / model / tools / effort / hooks / memory |
| CLI 启动 | `--agent <name>` 或 `--agents '<json>'` |
| 列出代理 | `claude agents` 命令 |

---

### 四、会话管理

| 功能 | CLI / 命令 | 说明 |
|------|------------|------|
| 恢复会话 | `--resume [session]` / `-r` | 从任意历史会话恢复 |
| 继续会话 | `--continue` / `-c` | 从最近中断点继续 |
| 分叉会话 | `--fork-session` | 创建会话副本 |
| 会话命名 | `--name <name>` / `/rename` | 自定义标题 |
| 导出 | `/export` | 导出对话记录 |
| 压缩 | `/compact` | 手动触发上下文压缩 |
| PR 恢复 | `--from-pr` | 恢复关联 PR 的会话 |
| 远程控制 | `/remote-control` | 桥接到 claude.ai/code |
| 会话 ID | `--session-id <uuid>` | 使用指定会话 ID |
| 无持久化 | `--no-session-persistence` | 会话不保存（仅 -p 模式） |

---

### 五、非交互 / SDK 模式（Print Mode）

```bash
# 单次问答
claude -p "解释这段代码"

# JSON / 流式 JSON 输出
claude -p "..." --output-format json
claude -p "..." --output-format stream-json --include-partial-messages

# 结构化输出（JSON Schema 校验）
claude -p "..." --json-schema '{"type":"object","properties":{"name":{"type":"string"}}}'

# 预算控制
claude -p "..." --max-budget-usd 1.00

# 指定模型和 effort
claude -p "..." --model haiku --effort low

# 工具白/黑名单
claude -p "..." --tools "Bash,Read"
claude -p "..." --tools ""  # 禁用所有工具
claude -p "..." --disallowed-tools "WebSearch"

# Bare 模式（CI/CD 最轻量，跳过 hooks/LSP/plugin/skill/auto-memory）
claude -p "..." --bare --system-prompt "你是一个代码审查员"

# 流式 JSON 输入
claude -p --input-format stream-json --output-format stream-json

# 回放用户消息
claude -p --input-format stream-json --output-format stream-json --replay-user-messages

# 模型降级（过载时自动 fallback）
claude -p "..." --fallback-model haiku

# 加载外部文件
claude -p "..." --file file_abc:doc.txt file_def:img.png
```

---

### 六、Git 深度集成

| 功能 | 说明 |
|------|------|
| Worktree | `--worktree [name]` 在独立分支隔离开发 |
| Sparse Worktree | `worktree.sparsePaths` 大 monorepo 只检出指定目录 |
| PR 管理 | 通过 gh CLI 创建/查看/管理 PR、添加评论 |
| 自动 commit/push | 内置 git 工作流指导 |
| from-pr | `--from-pr` 恢复关联 PR 的会话 |

---

### 七、MCP（Model Context Protocol）

| 特性 | 说明 |
|------|------|
| 连接方式 | Stdio / SSE / HTTP 三种 |
| OAuth | 内置 OAuth 认证流程 |
| 动态工具发现 | 大量工具时自动延迟加载 |
| Elicitation | 服务器可在任务中途请求结构化输入 |
| @ 引用 | `@` 语法引用 MCP 资源 |
| 插件内置 | 插件可附带 MCP 服务器 |
| 企业管控 | MCP allowlist/denylist |
| Channel | 权限中继到外部通道 |
| 严格模式 | `--strict-mcp-config` 仅使用 --mcp-config 指定的服务器 |

---

### 八、Hooks 系统

#### 会话与对话

| 事件 | 说明 |
|------|------|
| SessionStart | 新会话开始 |
| InstructionsLoaded | CLAUDE.md 和 rules 加载完成 |
| Stop | 主代理停止 |
| StopFailure | API 错误导致 turn 结束 |
| UserPromptSubmit | 用户提交 prompt |
| Notification | 通知事件 |

#### 工具

| 事件 | 说明 |
|------|------|
| PreToolUse | 工具执行前 |
| PostToolUse | 工具执行成功后 |
| PostToolUseFailure | 工具执行失败后 |
| PermissionRequest | 权限请求时 |

#### 代理

| 事件 | 说明 |
|------|------|
| SubagentStart | 子代理启动 |
| SubagentStop | 子代理停止 |
| TeammateIdle | 协作代理空闲 |
| TaskCompleted | 后台任务完成 |

#### 上下文与配置

| 事件 | 说明 |
|------|------|
| PreCompact | 压缩前 |
| PostCompact | 压缩后 |
| ConfigChange | 配置文件变更 |
| Elicitation | MCP elicitation 请求 |
| ElicitationResult | elicitation 响应后 |

#### Worktree 与初始化

| 事件 | 说明 |
|------|------|
| WorktreeCreate | worktree 创建 |
| WorktreeRemove | worktree 移除 |
| Setup | `--init` / `--maintenance` 触发 |

#### Hook 类型

| 类型 | 说明 |
|------|------|
| Command | 执行 shell 命令 |
| HTTP | 发送 HTTP 请求 |
| Prompt | LLM 判断 |
| Agent | 生成代理处理 |

---

### 九、Plugin 系统

| 功能 | 说明 |
|------|------|
| 安装管理 | `claude plugin install/enable/disable/update/uninstall` |
| 市场 | 支持多个市场源（GitHub / Git / npm / 本地） |
| 可包含组件 | Skills + Agents + Hooks + MCP Servers + LSP Servers |
| 热加载 | 修改后无需重启 |
| 验证 | `claude plugin validate` |
| 持久数据 | `${CLAUDE_PLUGIN_DATA}` 跨版本保存 |
| 作用域 | 项目级 / 用户级 / 本地级 |
| 临时加载 | `--plugin-dir <path>` 临时加载插件目录 |

---

### 十、Skill 系统

| 特性 | 说明 |
|------|------|
| 格式 | SKILL.md + YAML frontmatter |
| 自动发现 | `.claude/skills/` 及嵌套目录 |
| 参数传递 | `/skill-name arg1 arg2` |
| Tab 补全 | 输入 `/` 时自动建议 |
| 模型覆盖 | 可为单个 skill 指定不同模型 |
| 独立上下文 | `context: fork` 在子代理中运行 |
| 工具控制 | `allowed-tools` / `disallowed-tools` |
| 触发控制 | `disable-model-invocation` / `user-invocable` |
| 无需重启 | 修改后即时生效 |

---

### 十一、IDE 集成

#### VS Code

| 功能 | 说明 |
|------|------|
| 原生扩展 | 侧边栏 / Secondary Sidebar |
| 多会话 Tab | 多个并发对话 |
| MCP 管理 | 原生对话框管理 MCP 服务器 |
| 插件管理 | 直接在 VS Code 中管理 |
| Teleport | Web ↔ VS Code 会话迁移 |
| 自动连接 | `--ide` 自动连接可用 IDE |

#### JetBrains

| 功能 | 说明 |
|------|------|
| 支持 IDE | IntelliJ IDEA / PyCharm / WebStorm 等 |
| 内置 MCP | IDE 工具暴露给 Claude Code |
| 远程开发 | 支持 WSL 和 Remote Dev |

#### Chrome 扩展

| 功能 | 说明 |
|------|------|
| 浏览器控制 | `--chrome` 启用，导航/点击/填表 |
| 内容提取 | 提取页面文本/数据 |
| 截图/录制 | 截图和 GIF 录制 |
| 控制台 | 浏览器 console 日志 |
| Google Docs | 直接编辑 Google Docs |
| 本地测试 | 测试本地 web 应用 |

---

### 十二、Memory 体系

| 层级 | 位置 | 用途 |
|------|------|------|
| CLAUDE.md | 项目根 / 子目录 / 用户级 | 项目指令、编码规范 |
| Rules | `.claude/rules/*.md` | 路径条件规则 |
| Auto Memory | `.claude/projects/*/memory/` | 自动记忆，跨会话持久化 |
| `/memory` 命令 | — | 查看/编辑/导入/导出记忆 |

---

### 十三、CLI 标志速查

#### 启动

| 标志 | 说明 |
|------|------|
| `--bare` | 最小模式，跳过 hooks/LSP/plugin/skill/auto-memory |
| `--chrome` / `--no-chrome` | 启用/禁用 Chrome 集成 |
| `--brief` | 启用 SendUserMessage 工具 |
| `--agent <name>` | 指定启动代理 |
| `--agents <json>` | 内联定义代理 |
| `--worktree [name]` / `-w` | git worktree 隔离 |
| `--tmux` | tmux 多面板（需配合 --worktree） |
| `--add-dir <dirs>` | 添加额外工作目录 |

#### 会话

| 标志 | 说明 |
|------|------|
| `--resume [value]` / `-r` | 恢复会话 |
| `--continue` / `-c` | 继续最近会话 |
| `--fork-session` | 分叉会话 |
| `--from-pr [value]` | 恢复 PR 关联会话 |
| `--name <name>` / `-n` | 会话名称 |
| `--session-id <uuid>` | 指定会话 ID |

#### 模型与输出

| 标志 | 说明 |
|------|------|
| `--model <model>` | 指定模型 |
| `--effort <level>` | 思考深度 (low/medium/high/max) |
| `--fallback-model <model>` | 过载降级模型 |
| `--print` / `-p` | 非交互模式 |
| `--output-format <fmt>` | text / json / stream-json |
| `--json-schema <schema>` | 结构化输出校验 |
| `--max-budget-usd <amt>` | 预算上限 |

#### 配置

| 标志 | 说明 |
|------|------|
| `--system-prompt <prompt>` | 替换系统提示 |
| `--append-system-prompt <prompt>` | 追加系统提示 |
| `--settings <file-or-json>` | 加载设置 |
| `--mcp-config <configs>` | 加载 MCP 配置 |
| `--setting-sources <sources>` | 控制配置来源 (user,project,local) |
| `--allowedTools` / `--disallowedTools` | 工具白/黑名单 |
| `--tools <tools>` | 限制可用工具 |
| `--permission-mode <mode>` | 权限模式 |

#### 调试

| 标志 | 说明 |
|------|------|
| `--debug [filter]` / `-d` | 调试模式，支持分类过滤 |
| `--debug-file <path>` | 调试日志写入文件 |
| `--verbose` / `-v` | 详细输出 |

#### 其他

| 标志 | 说明 |
|------|------|
| `--betas <betas>` | API 请求附加 beta 头 |
| `--file <specs>` | 启动时下载文件资源 |
| `--ide` | 自动连接 IDE |
| `--disable-slash-commands` | 禁用所有 skill |
| `--strict-mcp-config` | 仅使用指定 MCP 配置 |

---

### 十四、关键环境变量

#### 模型

| 变量 | 说明 |
|------|------|
| `ANTHROPIC_DEFAULT_SONNET_MODEL` | 默认 Sonnet 模型 |
| `ANTHROPIC_DEFAULT_OPUS_MODEL` | 默认 Opus 模型 |
| `ANTHROPIC_DEFAULT_HAIKU_MODEL` | 默认 Haiku 模型 |

#### Bash

| 变量 | 说明 |
|------|------|
| `CLAUDE_BASH_DEFAULT_TIMEOUT_MS` | 默认 bash 超时 |
| `CLAUDE_BASH_MAX_TIMEOUT_MS` | 最大 bash 超时 |
| `CLAUDE_BASH_NO_LOGIN` | 跳过 login shell |
| `CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR` | 冻结工作目录 |

#### 功能开关

| 变量 | 说明 |
|------|------|
| `CLAUDE_CODE_DISABLE_1M_CONTEXT` | 禁用 1M 上下文 |
| `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` | 禁用非必要网络请求 |
| `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS` | 禁用后台任务 |
| `CLAUDE_CODE_DISABLE_CRON` | 禁用 cron 定时任务 |
| `CLAUDE_CODE_SIMPLE` | 简化模式（同 --bare） |
| `CLAUDE_CODE_DISABLE_TERMINAL_TITLE` | 禁止更新终端标题 |

#### 插件

| 变量 | 说明 |
|------|------|
| `CLAUDE_CODE_PLUGIN_SEED_DIR` | 插件种子目录 |
| `CLAUDE_CODE_PLUGIN_CACHE_DIR` | 插件缓存目录 |
| `CLAUDE_CODE_PLUGIN_GIT_TIMEOUT_MS` | 插件 git 超时 |

#### 其他

| 变量 | 说明 |
|------|------|
| `CLAUDE_CODE_TMPDIR` | 覆盖临时目录 |
| `CLAUDE_CODE_SESSIONEND_HOOKS_TIMEOUT_MS` | SessionEnd hooks 超时 |
| `CLAUDE_CODE_EXIT_AFTER_STOP_DELAY` | SDK 模式自动退出延迟 |

---

### 十五、其他能力

| 功能 | 说明 |
|------|------|
| Vim 模式 | 完整 vim 键绑定（motions / operators / text objects） |
| 语音输入 | `/voice` 语音转文字 |
| 自定义状态栏 | `/statusline` 显示 context/git/cost 等 |
| 键盘快捷键 | `/keybindings` 自定义 |
| Loop 定时任务 | `/loop 5m check-deploy` |
| Fast 模式 | `/fast` 同模型更快输出 |
| Budget 控制 | `--max-budget-usd` 限制花费 |
| Doctor 诊断 | `/doctor` 健康检查 |
| 沙箱 | 文件系统 + 网络隔离（Linux/macOS 原生） |
| Computer Use | 桌面 GUI 自动化 |
| 授权管理 | `claude auth login` / `claude setup-token` |
| 更新检查 | `claude update` / `claude doctor` |

---

### 相关记录

- [Claude Code 完整指南](./claude-code-comprehensive-guide.md) - 概述性介绍（无版本标注）
- [Claude Code 最新功能 (2026-03)](./claude-code-latest-features-2026.md) - v2.0.x 更新记录
- [Claude Code 完整斜杠命令列表](./claude-code-slash-commands.md) - 斜杠命令详单
- [Claude Code Fork 会话功能](./claude-code-fork-session.md) - 分叉会话深挖
- [Claude Code Skill 触发模式与 Hook 提升](./claude-code-skill-hook-trigger-boost.md) - Skill 自动触发优化
- [Claude Code 后端模型接入](./claude-code-backend-models.md) - 多模型 LLM Gateway

### 验证记录

- [2026-03-25] 初次记录，来源：`claude --version` 确认 2.1.81，`claude --help` 提取完整 CLI 标志，官方文档交叉校验

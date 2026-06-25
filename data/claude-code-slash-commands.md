# Claude Code 完整斜杠命令列表 (Slash Commands)

**收录日期**：2026-01-30
**来源日期**：2026-05-14
**更新日期**：2026-06-25
**标签**：#ai #tools #reference #claude-code
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐ (官方文档)
**来源**：Claude Code Official Docs
**适用版本**：官方 Commands 文档（2026-06-25 访问）；原清单基线 2.1.142 / 本机验证 2.1.133

**问题/场景**：


### 概要
Claude Code 完整斜杠命令列表 (Slash Commands)

Claude Code 有哪些内置斜杠命令？每个命令的具体作用是什么？如何分类记忆？

**解决方案/结论**：

### 当前内置命令清单（2026-05 更新）

| 命令 | 用途 | 分类 |
|--------|------|------|
| `/add-dir` | 添加额外的工作目录 | 项目管理 |
| `/agents` | 管理自定义 AI 子代理 | 代理管理 |
| `/autofix-pr` | 自动修复 PR 相关问题 | Git/PR |
| `/background` / `/bg` | 将当前会话转入后台代理 | 会话管理 |
| `/batch` | 批量处理多个独立任务 | 自动化 |
| `/branch [name]` | 从当前会话分支探索另一条方案，并切入新分支 | 会话管理 |
| `/fork <directive>` | 生成后台 forked subagent，继承完整会话执行旁路任务并回传结果 | 代理管理 |
| `/btw` | 记录旁路上下文，后续可恢复 | 记忆/上下文 |
| `/chrome` | 配置或启用 Chrome 集成 | 浏览器 |
| `/claude-api` | 管理 Claude API / Developer Platform 相关入口 | 账户/API |
| `/clear` | 清除对话历史 | 会话管理 |
| `/color` | 调整终端颜色显示 | 界面 |
| `/compact [instructions]` | 压缩对话，可选择性地提供焦点说明 | 上下文管理 |
| `/config` | 打开设置界面（配置选项卡） | 配置 |
| `/context` | 将当前上下文使用情况可视化为彩色网格 | 监控 |
| `/copy` | 复制当前或选定回复内容 | 导出 |
| `/cost` | 显示令牌使用统计 | 成本管理 |
| `/debug` | 打开调试相关操作 | 诊断 |
| `/desktop` / `/app` | 与 Claude Desktop / App 入口协作 | 桌面集成 |
| `/diff` | 查看当前改动差异 | Git |
| `/doctor` | 检查您的 Claude Code 安装的健康状况 | 诊断 |
| `/effort` | 调整模型思考努力级别 (low/medium/high/max) | 模型控制 |
| `/exit` | 退出 REPL | 会话管理 |
| `/export [filename]` | 将当前对话导出到文件或剪贴板 | 导出 |
| `/extra-usage` | 查看额外使用量信息 | 使用监控 |
| `/fast` | 切换 Fast Mode | 模型控制 |
| `/feedback` / `/bug` | 提交反馈或错误报告 | 反馈 |
| `/fewer-permission-prompts` | 降低权限提示频率 | 权限管理 |
| `/focus` | 切换聚焦/TUI 展示 | 界面 |
| `/goal` | 设置长任务完成条件 | 任务管理 |
| `/heapdump` | 生成内存诊断信息 | 诊断 |
| `/help` | 获取使用帮助 | 帮助 |
| `/hooks` | 管理工具事件的钩子配置 | 高级配置 |
| `/ide` | 管理 IDE 集成并显示状态 | IDE 集成 |
| `/init` | 使用 `CLAUDE.md` 指南初始化项目 | 项目初始化 |
| `/insights` | 查看会话或使用洞察 | 使用监控 |
| `/install-github-app` | 为存储库设置 Claude GitHub Actions | 集成 |
| `/install-slack-app` | 安装或配置 Slack 集成 | 集成 |
| `/keybindings` | 配置快捷键 | 界面 |
| `/login` | 切换 Anthropic 账户 | 账户管理 |
| `/logout` | 从您的 Anthropic 账户登出 | 账户管理 |
| `/loop` / `/proactive` | 本地循环执行任务 | 自动化 |
| `/mcp` | 管理 MCP 服务器连接和 OAuth 身份验证 | MCP 管理 |
| `/memory` | 编辑 `CLAUDE.md` 内存文件 | 记忆管理 |
| `/mobile` / `/ios` / `/android` | 配置移动端通知/控制 | 远程会话 |
| `/model` | 选择或更改 AI 模型 | 模型选择 |
| `/passes` | 管理多轮 pass/审查流程 | 审查 |
| `/output-style [style]` | 直接设置输出样式或从选择菜单中选择 | 界面 |
| `/permissions` / `/allowed-tools` | 查看或更新权限 | 权限管理 |
| `/plan` | 直接从提示进入计划模式 | 模式切换 |
| `/plugin` | 管理 Claude Code 插件 | 插件管理 |
| `/powerup` | 打开功能升级/能力入口 | 配置 |
| `/privacy-settings` | 查看和更新您的隐私设置 | 隐私 |
| `/radio` | 语音/音频相关入口 | 语音 |
| `/recap` | 生成会话摘要，便于切换设备继续 | 会话管理 |
| `/release-notes` | 查看发布说明 | 版本信息 |
| `/reload-plugins` | 重新加载插件 | 插件管理 |
| `/remote-control` / `/rc` | 开启远程控制 | 远程会话 |
| `/rename <name>` | 重命名当前会话以便于识别 | 会话管理 |
| `/remote-env` | 配置远程会话环境（claude.ai 订阅者） | 远程会话 |
| `/resume [session]` | 按 ID 或名称恢复对话，或打开会话选择器 | 会话管理 |
| `/review` | 请求代码审查 | 代码质量 |
| `/rewind` / `/checkpoint` / `/undo` | 回退对话和/或代码 | 撤销 |
| `/sandbox` | 启用沙箱化 bash 工具，具有文件系统和网络隔离 | 安全 |
| `/schedule` / `/routines` | 管理云端计划任务 | 自动化 |
| `/scroll-speed` | 调整滚动速度 | 界面 |
| `/security-review` | 对当前分支上的待处理更改完成安全审查 | 安全 |
| `/setup-bedrock` | 配置 Amazon Bedrock | 模型/平台 |
| `/setup-vertex` | 配置 Google Vertex AI | 模型/平台 |
| `/simplify` | 简化 UI/输出模式 | 界面 |
| `/skills` | 查看和调用 Skills | Skill |
| `/stats` | 可视化每日使用情况、会话历史、连胜记录和模型偏好 | 统计 |
| `/status` | 打开设置界面（状态选项卡），显示版本、模型、账户和连接性 | 状态查看 |
| `/statusline` | 设置 Claude Code 的状态行 UI | 界面 |
| `/stickers` | 管理或查看贴纸/反馈类入口 | 界面 |
| `/stop` | 停止当前运行中的任务 | 任务管理 |
| `/tasks` / `/bashes` | 列出和管理后台任务 | 任务管理 |
| `/team-onboarding` | 团队初始化/引导入口 | 团队 |
| `/teleport` | 按会话 ID 从 claude.ai 恢复远程会话，或打开选择器（claude.ai 订阅者） | 远程会话 |
| `/terminal-setup` | 为换行安装 Shift+Enter 键绑定（VS Code、Alacritty、Zed、Warp） | 终端设置 |
| `/theme` | 更改颜色主题 | 界面 |
| `/todos` | 列出当前 TODO 项目 | 任务管理 |
| `/t` | 临时禁用思考模式（在提示词中） | 模式切换 |
| `/tui` | 切换全屏终端界面 | 界面 |
| `/ultraplan` | 使用更强规划模式 | 计划 |
| `/ultrareview` | 云端多代理深度审查 | 代码质量 |
| `/upgrade` | 升级或查看升级入口 | 账户/版本 |
| `/usage` | 仅适用于订阅计划：显示计划使用限制和速率限制状态 | 使用监控 |
| `/voice` | 语音输入 | 语音 |
| `/web-setup` | 配置 Web/远程运行环境 | 远程会话 |

MCP server 还可以暴露动态 slash commands：`/mcp__<server>__<prompt>`。

### 已移除/改名命令

| 旧命令/标志 | 当前处理 |
|-------------|----------|
| `/vim` | 2.1.92 移除，改用 `/config` -> Editor mode |
| `/pr-comments` | 2.1.91 移除，直接让 Claude 查看 PR 评论 |
| `/cost`、`/stats` | 仍可用，但主要作为 `/usage` 入口或别名 |
| `/bashes` | 兼容别名，当前更通用的入口是 `/tasks` |
| `/fork` | 2.1.161 以前是 `/branch` 别名；当前官方文档中 `/fork <directive>` 是后台 forked subagent 入口，自己切入会话副本应使用 `/branch` |

#### 会话管理
```
/clear             - 清除对话历史
/resume [id]       - 恢复对话
/branch [name]     - 从当前会话分支并切入新分支
/background /bg    - 转入后台代理
/rename <name>     - 重命名当前会话
/recap             - 生成会话摘要
/export [file]     - 导出当前对话
/exit              - 退出 REPL
```

#### 项目管理
```
/add-dir      - 添加额外的工作目录
/init         - 初始化项目（创建 CLAUDE.md）
```

#### 上下文与记忆
```
/compact [instructions]  - 压缩对话
/context              - 查看上下文使用
/memory              - 编辑 CLAUDE.md
```

#### 代理与任务
```
/agents    - 管理子代理
/fork      - 启动后台 forked subagent
/tasks     - 列出后台任务
/todos     - 列出 TODO 项目
/goal      - 设置完成条件
/loop      - 本地循环任务
/schedule  - 云端例行任务
```

#### 配置与设置
```
/config           - 打开设置界面
/model            - 选择 AI 模型
/permissions       - 查看或更新权限
/privacy-settings  - 隐私设置
/theme            - 更改颜色主题
/output-style     - 设置输出样式
/focus /tui       - 聚焦/全屏界面
/status           - 状态选项卡
/statusline       - 状态行 UI
/terminal-setup   - 终端键绑定
```

#### 集成与工具
```
/ide                 - IDE 集成
/mcp                 - MCP 服务器管理
/plugin              - 插件管理
/install-github-app  - GitHub Actions 集成
/install-slack-app   - Slack 集成
/hooks              - 钩子配置
/chrome             - Chrome 集成
```

#### Git 相关
```
/diff           - 查看当前改动
/review         - 代码审查
/ultrareview    - 云端多代理审查
```

#### 代码质量与安全
```
/review           - 请求代码审查
/security-review  - 安全审查
/ultraplan       - 强规划
```

#### 账户与成本
```
/login     - 切换账户
/logout    - 登出账户
/usage     - 使用统计入口
/cost      - Token 使用统计（兼容入口）
/stats     - 历史统计（兼容入口）
```

#### 诊断与帮助
```
/doctor - 检查安装健康状态
/help   - 获取使用帮助
/feedback /bug - 报告问题
```

#### 模式切换
```
/plan      - 进入计划模式
/sandbox  - 启用沙箱模式
/fast      - 快速模式
```

#### 远程与撤销
```
/rewind      - 回退对话或代码
/remote-env  - 远程会话环境
/teleport     - 恢复远程会话
/remote-control - 远程控制
```

**参考链接**：

- [Claude Code Commands](https://code.claude.com/docs/en/commands)
- [Claude Code Changelog](https://code.claude.com/docs/en/changelog)

### 验证记录
- [2026-01-30] 初次记录，来源：[官方文档](https://code.claude.com/docs/zh-CN/slash-commands)
- [2026-05-15] 更新到官方 2.1.142 命令集。本机 `claude --version` 为 2.1.133；基于官方 Commands 与 Changelog 补充 `/goal`、`/schedule`、`/ultrareview`、`/background`、`/branch`、`/tasks`、`/focus`、`/tui` 等，并标注 `/vim`、`/pr-comments` 的移除和 `/usage` 相关别名变化。
- [2026-06-25] 时效性修正：官方 Commands 文档确认 `/branch [name]` 是当前会话分支入口，`/fork <directive>` 是后台 forked subagent；旧结论“`/fork` 默认等于 `/branch`”仅保留为 2.1.161 以前的版本边界。

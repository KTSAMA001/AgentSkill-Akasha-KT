# Claude Code 完整斜杠命令列表 (Slash Commands)

**收录日期**：2026-01-30
**标签**：#ai #tools #reference #claude-code
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐ (官方文档)
**来源**：Claude Code Official Docs

**问题/场景**：

Claude Code 有哪些内置斜杠命令？每个命令的具体作用是什么？如何分类记忆？

**解决方案/结论**：

### 内置命令完整列表

| 命令 | 用途 | 分类 |
|--------|------|------|
| `/add-dir` | 添加额外的工作目录 | 项目管理 |
| `/agents` | 管理自定义 AI 子代理 | 代理管理 |
| `/bashes` | 列出和管理后台任务 | 任务管理 |
| `/bug` | 报告错误（发送给 Anthropic） | 反馈 |
| `/clear` | 清除对话历史 | 会话管理 |
| `/compact [instructions]` | 压缩对话，可选择性地提供焦点说明 | 上下文管理 |
| `/config` | 打开设置界面（配置选项卡） | 配置 |
| `/context` | 将当前上下文使用情况可视化为彩色网格 | 监控 |
| `/cost` | 显示令牌使用统计 | 成本管理 |
| `/doctor` | 检查您的 Claude Code 安装的健康状况 | 诊断 |
| `/exit` | 退出 REPL | 会话管理 |
| `/export [filename]` | 将当前对话导出到文件或剪贴板 | 导出 |
| `/help` | 获取使用帮助 | 帮助 |
| `/hooks` | 管理工具事件的钩子配置 | 高级配置 |
| `/ide` | 管理 IDE 集成并显示状态 | IDE 集成 |
| `/init` | 使用 `CLAUDE.md` 指南初始化项目 | 项目初始化 |
| `/install-github-app` | 为存储库设置 Claude GitHub Actions | 集成 |
| `/login` | 切换 Anthropic 账户 | 账户管理 |
| `/logout` | 从您的 Anthropic 账户登出 | 账户管理 |
| `/mcp` | 管理 MCP 服务器连接和 OAuth 身份验证 | MCP 管理 |
| `/memory` | 编辑 `CLAUDE.md` 内存文件 | 记忆管理 |
| `/model` | 选择或更改 AI 模型 | 模型选择 |
| `/output-style [style]` | 直接设置输出样式或从选择菜单中选择 | 界面 |
| `/permissions` | 查看或更新权限 | 权限管理 |
| `/plan` | 直接从提示进入计划模式 | 模式切换 |
| `/plugin` | 管理 Claude Code 插件 | 插件管理 |
| `/pr-comments` | 查看拉取请求注释 | Git 集成 |
| `/privacy-settings` | 查看和更新您的隐私设置 | 隐私 |
| `/release-notes` | 查看发布说明 | 版本信息 |
| `/rename <name>` | 重命名当前会话以便于识别 | 会话管理 |
| `/remote-env` | 配置远程会话环境（claude.ai 订阅者） | 远程会话 |
| `/resume [session]` | 按 ID 或名称恢复对话，或打开会话选择器 | 会话管理 |
| `/review` | 请求代码审查 | 代码质量 |
| `/rewind` | 回退对话和/或代码 | 撤销 |
| `/sandbox` | 启用沙箱化 bash 工具，具有文件系统和网络隔离 | 安全 |
| `/security-review` | 对当前分支上的待处理更改完成安全审查 | 安全 |
| `/stats` | 可视化每日使用情况、会话历史、连胜记录和模型偏好 | 统计 |
| `/status` | 打开设置界面（状态选项卡），显示版本、模型、账户和连接性 | 状态查看 |
| `/statusline` | 设置 Claude Code 的状态行 UI | 界面 |
| `/teleport` | 按会话 ID 从 claude.ai 恢复远程会话，或打开选择器（claude.ai 订阅者） | 远程会话 |
| `/terminal-setup` | 为换行安装 Shift+Enter 键绑定（VS Code、Alacritty、Zed、Warp） | 终端设置 |
| `/theme` | 更改颜色主题 | 界面 |
| `/todos` | 列出当前 TODO 项目 | 任务管理 |
| `/usage` | 仅适用于订阅计划：显示计划使用限制和速率限制状态 | 使用监控 |
| `/vim` | 进入 vim 模式以在插入和命令模式之间交替 | 编辑器 |

### 按功能分类

#### 会话管理
```
/clear        - 清除对话历史
/resume [id]  - 恢复对话
/rename <name> - 重命名当前会话
/export [file]  - 导出当前对话
/exit         - 退出 REPL
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
/bashes    - 列出后台任务
/todos     - 列出 TODO 项目
```

#### 配置与设置
```
/config           - 打开设置界面
/model            - 选择 AI 模型
/permissions       - 查看或更新权限
/privacy-settings  - 隐私设置
/theme            - 更改颜色主题
/output-style     - 设置输出样式
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
/hooks              - 钩子配置
```

#### Git 相关
```
/pr-comments      - 查看拉取请求注释
```

#### 代码质量与安全
```
/review           - 请求代码审查
/security-review  - 安全审查
```

#### 账户与成本
```
/login     - 切换账户
/logout    - 登出账户
/cost      - Token 使用统计
/usage     - 计划使用限制
```

#### 诊断与帮助
```
/doctor - 检查安装健康状态
/help   - 获取使用帮助
/bug    - 报告错误
```

#### 模式切换
```
/plan      - 进入计划模式
/sandbox  - 启用沙箱模式
```

#### 远程与撤销
```
/rewind      - 回退对话或代码
/remote-env  - 远程会话环境
/teleport     - 恢复远程会话
```

#### 编辑器模式
```
/vim - 进入 vim 模式
```

**参考链接**：

- [Claude Code 斜杠命令官方文档](https://code.claude.com/docs/zh-CN/slash-commands)

**验证记录**：

- [2026-01-30] 初次记录，来源：[官方文档](https://code.claude.com/docs/zh-CN/slash-commands)

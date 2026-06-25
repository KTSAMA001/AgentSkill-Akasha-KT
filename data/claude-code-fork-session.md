# Claude Code 分支会话与 Fork 会话功能 (Branching Conversation)

**收录日期**：2026-01-30
**来源日期**：2026-06-25（官方 Commands / CLI Reference 当前版本访问）
**更新日期**：2026-06-25
**标签**：#ai #tools #reference #claude-code
**来源**：Claude Code 官方 Commands / CLI Reference / Changelog
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐⭐ (官方文档)
**适用版本**：Claude Code 2.1.161+；历史版本中 `/fork` 曾作为 `/branch` 别名

**问题/场景**：

在复杂任务中想从当前对话点尝试不同方案，但不希望丢失当前会话；或者需要把一个旁路任务交给后台代理并继续当前主线。

### 概要

Claude Code 当前把“分支会话”和“fork 子代理”拆成三个入口：交互会话内用 `/branch [name]` 创建当前会话副本并切入；从历史会话恢复时用 `--resume` 或 `--continue` 搭配 `--fork-session` 生成新的 session ID；`/fork <directive>` 则是后台子代理入口，不再等同于自己切入一个对话副本。

**解决方案/结论**：

不要把 `/branch`、`--fork-session` 和 `/fork` 混用；三者的生命周期和适用场景不同。

| 入口 | 当前用途 | 适用场景 |
|------|----------|----------|
| `/branch [name]` | 在当前交互会话的当前点创建分支并切入新分支；原会话保留，可用 `/resume` 回去 | 自己要尝试另一条方案 |
| `claude --resume <session> --fork-session` | 恢复指定历史会话时创建新的 session ID，而不是复用原会话 | 从旧会话复制一份再继续 |
| `claude --continue --fork-session` | 基于当前目录最近会话创建新的 session ID | 从最近会话复制一份再继续 |
| `/fork <directive>` | 生成后台 forked subagent，继承完整会话执行指令，结果完成后回传当前会话 | 把旁路任务交给后台代理，自己继续主线 |

#### 推荐用法

```bash
# 当前交互会话中：在当前点创建分支并切入
/branch try-render-cache

# 之后从会话列表切回原会话或其他分支
/resume

# 命令行启动时：恢复指定会话并 fork 出新的 session ID
claude --resume auth-refactor --fork-session

# 命令行启动时：基于最近会话 fork 出新的 session ID
claude --continue --fork-session
```

#### 版本边界

- 官方 Commands 文档当前说明：`/branch [name]` 用于“切入一个当前对话副本”；`/fork <directive>` 用于后台 forked subagent。若需要自己进入副本，应使用 `/branch`。
- 官方 CLI Reference 当前说明：`--fork-session` 是恢复会话时创建新 session ID 的启动参数，需与 `--resume` 或 `--continue` 搭配。
- Changelog 记录 2.1.78 曾将 `/fork` 改名为 `/branch` 并保留别名；当前 Commands 文档又将 `/fork <directive>` 定义为后台子代理入口，并注明 2.1.161 以前 `/fork` 是 `/branch` 的别名。因此旧记录里“`/fork` 默认等于 `/branch`”只适用于旧版本语义。

#### 适用场景

| 场景 | 建议入口 | 说明 |
|------|----------|------|
| 想亲自试另一套实现 | `/branch [name]` | 立刻切入分支会话，原会话可恢复 |
| 想从历史会话复制一份 | `--resume <session> --fork-session` | 适合从命名会话或 ID 重新开分支 |
| 想从最近会话复制一份 | `--continue --fork-session` | 不需要先进入交互会话 |
| 想让后台代理并行调查 | `/fork <directive>` | 结果回传当前会话，不会把你切到副本里 |

#### 工作流程

```mermaid
flowchart LR
    A[当前会话] --> B{自己切入副本?}
    B -->|是| C[/branch name/]
    C --> D[新分支会话]
    D --> E[/resume 返回原会话]
    B -->|否，交给后台| F[/fork directive/]
    F --> G[后台子代理]
    G --> H[结果回传当前会话]
```

#### 关键特点

- **独立 session ID**：`/branch` 和 `--fork-session` 都会保留原会话，并创建可单独恢复的新会话。
- **恢复边界清晰**：`--fork-session` 是启动时恢复/继续会话的参数；不要单独运行 `claude --fork-session` 期待复制当前交互会话。
- **`/fork` 语义已变化**：当前版本更适合后台旁路任务；要自己进入分支副本时使用 `/branch`。
- **可回到原会话**：分支后通过 `/resume` 选择原会话或其他分支。

### 参考链接

- [Claude Code Commands](https://code.claude.com/docs/en/commands) - `/branch`、`/fork` 当前语义
- [Claude Code CLI Reference](https://code.claude.com/docs/en/cli-reference) - `--fork-session` 与 `--resume`/`--continue` 搭配
- [Claude Code Changelog](https://code.claude.com/docs/en/changelog) - `/fork`/`/branch` 与 fork session 相关变更
- [GitHub Issue: Clone/duplicate conversation](https://github.com/anthropics/claude-code/issues/12941) - 历史需求背景

### 相关记录

- [Claude Code 2.1 功能全览](./claude-code-2-1-feature-inventory.md) - 会话管理和 CLI flag 总览
- [Claude Code 完整斜杠命令列表](./claude-code-slash-commands.md) - Slash command 语义表
- [Claude Code 最新功能 (2026-06)](./claude-code-latest-features-2026.md) - 高时效变化摘要

### 验证记录

- [2026-01-30] 初次记录，来源：官方文档与 Release Note。
- [2026-06-25] 时效性修正：官方 Commands 文档确认当前 `/branch [name]` 是交互会话分支入口，`/fork <directive>` 是后台 forked subagent；官方 CLI Reference 确认 `--fork-session` 需与 `--resume` 或 `--continue` 搭配，用于恢复时创建新 session ID。同步收窄旧结论“`/fork` 等同分支会话”的适用版本边界。

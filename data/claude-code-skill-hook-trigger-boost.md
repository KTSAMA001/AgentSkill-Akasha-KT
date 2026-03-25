# Claude Code Skill 触发模式与 Hook 提升自动触发率

**标签**：#claude-code #agent-skills #hook #experience
**来源**：实践总结 + 社区研究（Scott Spence 200+ 测试）
**收录日期**：2026-03-25
**来源日期**：2026-03-25
**状态**：✅已验证
**可信度**：⭐⭐⭐⭐
**适用版本**：Claude Code 2.1.x+

### 概要

Claude Code Skill 的主动式/被动式触发模式由 frontmatter 控制，但主动式 skill 自动触发率仅 ~20%。通过 `UserPromptSubmit` hook 注入 forced eval 指令可提升至 ~84%。操作级别的行为区分（如查询自动/记录询问）需通过 SKILL.md 内部规则实现，frontmatter 无法做到。

### 内容

#### Skill 触发模式（frontmatter 控制）

| 配置 | 用户可调用 | Claude 可调用 | 适用场景 |
|------|:---:|:---:|------|
| 默认（无特殊配置） | Yes | Yes | 大多数 skill |
| `disable-model-invocation: true` | Yes | **No** | 有副作用的操作（部署、提交） |
| `user-invocable: false` | **No** | Yes | 纯背景知识 |

关键认知：
- `disable-model-invocation: true` 后，Claude **完全不知道**该 skill 的存在（连 description 都不加载到上下文）
- `user-invocable: false` 只控制 `/` 菜单可见性，不影响 Claude 自动调用

#### 操作级别行为控制

frontmatter 只控制整个 skill 的加载入口，无法区分内部操作。如需区分不同操作的行为（如查询自动执行、记录前询问确认），必须在 SKILL.md 内部规则中控制。

```yaml
# frontmatter 保持默认（主动式）
---
name: my-skill
description: ...
# 不设 disable-model-invocation
# 不设 user-invocable
---

# 内部规则中区分行为
## 规则
- 查询：自动执行，无需用户显式要求
- 记录：必须先展示摘要并征求用户确认
```

#### 主动式自动触发率问题

社区测试数据（Scott Spence, 200+ 测试, Haiku 4.5）：

| 方式 | 成功率 | 说明 |
|------|--------|------|
| 不做干预（纯靠 description） | ~20% | Claude 容易"无视" skill |
| 简单 hook 提示 | ~20% | 被动建议，Claude 容易忽略 |
| **Forced eval hook** | **~84%** | 强制逐步评估，最稳定 |
| **LLM eval hook** | **~80%** | API 预评估，更快更便宜但不稳定 |

#### Forced eval Hook 方案

原理：通过 `UserPromptSubmit` hook，每次用户发消息时注入强制评估指令，让 Claude 必须逐个评估 skill 是否匹配。

Hook 脚本示例：

```bash
#!/bin/bash
echo "MANDATORY - Evaluate AgentSkill-Akasha-KT skill before responding:

Step 1 - EVALUATE: Does the user's message relate to past experiences, previously solved problems, technical knowledge, or questions like 'did we solve this before' / 'how did we do X last time'?
→ If YES: Activate the skill immediately using Skill tool, then respond.
→ If NO: Skip and respond normally.

CRITICAL: The evaluation is WORTHLESS unless you ACTIVATE the skill when it matches."
```

settings.json 配置：

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash ~/.claude/hooks/skill-eval.sh"
          }
        ]
      }
    ]
  }
}
```

注意事项：
- Hook 可针对单个 skill 做强制评估，不必评估所有 skill
- 缺点是每次对话 Claude 会先输出评估过程，增加一些冗余
- 评估成功的核心是**承诺机制**：让 Claude 先写出 YES/NO，再决定是否激活

#### 时效性说明

> **此记录具有时效性**。Claude Code 未来版本可能改进 skill 自动触发机制，使 hook 方案不再必要。截至 Claude Code 2.1.x，主动式 skill 的自动触发仍不够可靠。

可能过时的场景：
- Claude Code 原生改进 skill 触发准确率
- 新增更细粒度的 frontmatter 配置（如操作级别控制）
- skill 上下文加载策略变更

### 关键代码

```yaml
# 前后对比：同一 skill 的不同行为策略

# ❌ 纯主动式（记录也会自动执行，可能记录不必要的内容）
---
name: knowledge-base
description: 知识库管理技能
---

# ✅ 主动式 + 内部行为规则（查询自动，记录询问）
---
name: knowledge-base
description: 知识库管理技能
---
（SKILL.md 内部规则中：查询自动执行，记录必须先询问确认）
```

### 参考链接

- [Extend Claude with skills - Claude Code 官方文档](https://code.claude.com/docs/en/skills) - Skill 触发模式官方说明
- [How to Make Claude Code Skills Activate Reliably - Scott Spence](https://scottspence.com/posts/how-to-make-claude-code-skills-activate-reliably) - 200+ 测试数据来源

### 相关记录

- [claude-code-comprehensive-guide.md](./claude-code-comprehensive-guide.md) - Claude Code 完整指南
- [claude-code-latest-features-2026.md](./claude-code-latest-features-2026.md) - Claude Code 最新功能

### 验证记录

- [2026-03-25] 初次记录，来源：实践配置阿卡西记录 skill + 社区研究

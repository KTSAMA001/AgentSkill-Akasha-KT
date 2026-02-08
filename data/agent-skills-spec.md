# Agent Skills 规范

本文档记录 Agent Skills 开放标准的核心知识。

---

## Agent Skills 概述

**标签**：#ai #knowledge #agent-skills
**来源**：[agentskills.io](https://agentskills.io/specification)
**收录日期**：2026-02-08
**来源日期**：2026-02-08
**状态**：📘 有效
**可信度**：⭐⭐⭐⭐⭐ (官方规范)

### 定义/概念

Agent Skills 是一种开放标准格式，用于定义 AI Agent 可加载的技能包。技能包含指令、脚本和资源，帮助 Agent 执行特定任务。

### 支持的工具

- VS Code Copilot
- Claude Code
- Cursor
- Gemini CLI
- OpenAI Codex
- Goose
- Amp
- 更多...

### 目录结构

```
skill-name/
├── SKILL.md          # 必需 - 核心指令文件
├── scripts/          # 可选 - 可执行脚本
├── references/       # 可选 - 参考文档
└── assets/           # 可选 - 静态资源
```

### SKILL.md 格式

```markdown
---
name: skill-name           # 必需，小写+连字符，最多64字符
description: 描述内容...    # 必需，最多1024字符
license: MIT               # 可选
compatibility: 环境要求    # 可选，最多500字符
metadata:                  # 可选
  author: example-org
  version: "1.0"
allowed-tools: Bash(git:*) # 可选，实验性
---

# 技能指令

详细说明...
```

### 关键点

- **name 字段**：小写字母 + 连字符，不能以 `-` 开头/结尾，不能有连续 `--`
- **description 字段**：描述"做什么"和"何时使用"，帮助 Agent 判断激活时机
- **主文件建议 < 500 行**，详细内容放到 `references/` 目录

### 渐进式加载 (Progressive Disclosure)

| 级别 | 内容 | Token | 加载时机 |
|------|------|-------|----------|
| Level 1 | `name` + `description` | ~100 | 启动时加载所有技能元数据 |
| Level 2 | `SKILL.md` body | < 5000 推荐 | 技能激活时 |
| Level 3 | `scripts/`、`references/` | 按需 | 仅在需要时 |

### 存放位置

| 类型 | 路径 |
|------|------|
| 项目级 | `.github/skills/` 或 `.claude/skills/` |
| 个人级 | `~/.copilot/skills/` 或 `~/.claude/skills/` |

### 相关知识

- [Agent Skills 官方规范](https://agentskills.io/specification)
- [VS Code Agent Skills 文档](https://code.visualstudio.com/docs/copilot/customization/agent-skills)
- [Anthropic Skills 示例](https://github.com/anthropics/skills)
- [GitHub Awesome Copilot](https://github.com/github/awesome-copilot)

---

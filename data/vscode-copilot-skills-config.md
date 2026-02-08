# GitHub Copilot 使用相关经验

> GitHub Copilot 使用相关经验
>
> 包含：Chat、Agent、Custom Instructions、Skills 等

---

## VS Code Copilot 与 Claude Code 共享 Skills 仓库

**日期**：2026-01-30
**标签**：#vscode #tools #experience #copilot
**状态**：✅ 已验证

**问题/场景**：

希望 VS Code Copilot 和 Claude Code 能够共享同一套 Skills 和经验记录系统，避免维护两套配置，实现统一管理。

**解决方案/结论**：

通过**符号链接**让两者共享同一个 Git 仓库中的 Skills 和配置文件。

**配置步骤**：

1. 确认目录结构：
   - VS Code Copilot Skills 目录：`~/.copilot/skills/`
   - Claude Code Skills 目录：`~/.claude/skills/`
   - Claude Code 全局指令：`~/.claude/CLAUDE.md`

2. 克隆技能仓库到两个平台的 skills 目录：
   ```bash
   # VS Code Copilot（目录名可自定义）
   git clone https://github.com/KTSAMA001/AgentSkill-Akasha-KT.git ~/.copilot/skills/akasha-kt
   
   # Claude Code（目录名建议与上面一致）
   git clone https://github.com/KTSAMA001/AgentSkill-Akasha-KT.git ~/.claude/skills/akasha-kt
   ```

   或者使用符号链接共享同一份：
   ```bash
   # 先克隆到一个位置
   git clone https://github.com/KTSAMA001/AgentSkill-Akasha-KT.git ~/.copilot/skills/akasha-kt
   
   # 创建符号链接
   mkdir -p ~/.claude/skills
   ln -sf ~/.copilot/skills/akasha-kt ~/.claude/skills/akasha-kt
   ```

3. 创建符号链接共享全局指令（可选）：
   ```bash
   ln -sf ~/.copilot/CLAUDE.md ~/.claude/CLAUDE.md
   ```

**最终目录结构**：

```
~/.copilot/
├── CLAUDE.md                           # Claude Code 全局指令（可选）
└── skills/
    └── <skill-dir>/                    # 技能目录（独立 Git 仓库）
        ├── SKILL.md                    # 技能入口
        ├── references/                 # 参考文档
        └── data/                       # 记录数据
            ├── experiences/            # 经验数据
            └── knowledge/              # 知识数据

~/.claude/
├── CLAUDE.md -> ~/.copilot/CLAUDE.md   # 符号链接（可选）
├── skills/
│   └── <skill-dir> -> ~/.copilot/skills/<skill-dir>  # 符号链接或独立克隆
└── settings.json                       # Claude Code 设置
```

**关键区别**：

| 特性 | VS Code Copilot | Claude Code |
|------|----------------|-------------|
| Skills 目录 | `~/.copilot/skills/` | `~/.claude/skills/` |
| 全局指令 | `.instructions.md` | `CLAUDE.md` |
| Skills 格式 | 相同（`SKILL.md`） | 相同（`SKILL.md`） |
| 验证命令 | 自动加载 | `/skills` 查看列表 |

**参考链接**：

- [Claude Code Skills 官方文档](https://code.claude.com/docs/en/skills) - 技能创建和配置指南
- [Claude Code Memory 官方文档](https://code.claude.com/docs/en/memory) - CLAUDE.md 配置说明

**验证记录**：

- [2026-01-30] 初次记录，来源：实践总结。配置完成后两边均可正常使用共享的经验记录技能。
- [2026-02-01] 更新：仓库结构调整，每个技能独立成仓库，data 目录移入技能目录内。

**备注**：

- Claude Code 的 Skills 遵循 [Agent Skills](https://agentskills.io/) 开放标准
- 技能目录名由用户 clone 时指定，不硬编码在文档中
- 使用符号链接时，修改任意一边配置后另一边自动生效
- 每个技能是独立的 Git 仓库，便于跨平台同步

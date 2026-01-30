# 🧠 KT's Copilot Agent Skills (Experience Logger)

一个持续学习型的 AI Agent Skill，具备**记忆**、**成长**和**自我修正**能力。

---

## 📑 目录

- [快速开始](#快速开始)
- [⚠️ 重要说明](#重要说明)
- [核心功能](#核心功能)
- [使用指南](#使用指南)
- [知识库结构](#知识库结构)
- [同步与备份](#同步与备份)
- [AI 操作指南](#ai-操作指南)
- [详细说明](#详细说明)

---

## 快速开始

### 安装

```bash
# macOS / Linux
git clone https://github.com/KTSAMA001/KT-s-Agent-Skills.git ~/.copilot

# Windows (PowerShell)
git clone https://github.com/KTSAMA001/KT-s-Agent-Skills.git $HOME\.copilot
```

### 验证

在 AI Chat 中输入：

> "帮我记录一下今天解决的问题"

如果 Agent 能识别并激活 `experience-logger` Skill，即表示安装成功。

### Claude Code 支持（可选）

```bash
mkdir -p ~/.claude/skills
ln -sf ~/.copilot/skills/experience-logger ~/.claude/skills/experience-logger
ln -sf ~/.copilot/CLAUDE.md ~/.claude/CLAUDE.md
```

---

## ⚠️ 重要说明

### 当前仓库状态

| 类型 | 说明 | 适用性 |
|------|------|--------|
| 通用技术经验 | Unity、C#、Shader 等通用解决方案 | ✅ 大部分人可用 |
| 个人/项目经验 | 特定项目配置、个人偏好 | ⚠️ 按需参考 |

**当前 `main` 分支为混合状态**，尚未进行分支隔离。

### 安装前注意事项

⚠️ 请注意：
- 仓库中的经验不一定适用于你的项目，请根据实际情况判断
- 个人/项目特定内容仅供参考
- AI Agent 会基于所有经验进行检索，需自行判断适用性
- **建议 Fork** 本仓库，以便自由修改和管理

### 推荐使用方式

| 方式 | 命令 | 适合人群 |
|------|------|---------|
| 直接使用 | `git clone https://github.com/KTSAMA001/KT-s-Agent-Skills.git ~/.copilot` | 快速体验 |
| Fork 自定义 | 先在 GitHub Fork，然后克隆你的仓库 | 长期使用者（推荐） |
| 选择性克隆 | 克隆后删除不需要的目录 | 只需要部分经验 |

---

## 核心功能

| 功能 | 说明 |
|------|------|
| 📂 结构化存储 | 按领域（Unity, C#, Shader 等）分类存储经验 |
| 🔍 智能检索优先 | 遇到问题优先检索本地已有经验 |
| 🌐 联网自动补全 | 本地无记录时自动搜索最新方案 |
| ☁️ 自动多端同步 | 保存前后自动拉取/推送，确保数据一致 |
| ✅ 经验验证 | 引用时自动验证正确性和时效性 |
| 🔧 智能修正 | 根据反馈自动修正、补充或废弃过时经验 |

---

## 使用指南

### 技能触发方式

| 行为 | 触发方式 | 示例 |
|------|---------|------|
| 记录经验 | 解决后要求记录 | "记录一下"、"保存这个结论" |
| 查找经验 | 遇到问题时自动触发 | "之前是怎么解决的" |
| 网络搜索 | 本地无记录时自动触发 | "上网查一下" |
| 更新经验 | 发现需要补充/改进 | "补充一下" |
| 验证经验 | 引用时检测 / 用户要求 | "检查一下这个经验" |
| 修正经验 | 发现错误 / 用户反馈 | "这个方法不行" |
| 废弃经验 | 完全过时或错误 | "这个已经过时了" |

### 基本用法流程

```
遇到问题 → 检索本地经验 → 找到？→ 回复用户
                         ↓ 未找到
                    联网搜索 → 提供方案 → 是否保存？→ 归档到知识库
```

### 显式记录流程

```
要求记录 → 拉取最新 → 格式化并保存 → 推送到远程 → 完成
```

---

## 知识库结构

所有经验以 Markdown 格式保存在 `experiences/` 目录：

```
experiences/
├── unity/     # Unity 引擎、组件、生命周期
├── csharp/    # C# 语法、.NET 特性
├── shader/    # ShaderLab, HLSL, 渲染管线
├── git/       # 版本控制技巧
├── vscode/    # 编辑器配置与插件
├── python/    # Python 脚本与工具
├── tools/     # Blender, Photoshop 等
└── general/   # 通用算法、架构设计
```

### 经验质量标记

| 标记 | 含义 |
|------|------|
| ✅ 已验证 | 经过实际验证，确认有效 |
| ⚠️ 待验证 | 理论可行但未经实践验证 |
| 🔄 已过时 | 方案已过时，保留供参考 |
| ❌ 已废弃 | 完全错误，不应使用 |
| 🔬 实验性 | 非主流方案，使用需谨慎 |

---

## 同步与备份

### 自动同步

Agent 在记录或更新经验时自动执行：
1. `git pull` - 拉取最新内容
2. 写入 Markdown 文件
3. `git add & commit` - 提交更改
4. `git push` - 推送到远程

### 手动同步

```bash
# 保存更改
cd ~/.copilot
git add .
git commit -m "update: 添加了关于 xxx 的笔记"
git push

# 获取更新
cd ~/.copilot
git pull
```

---

## AI 操作指南

> 供 AI Agent 在帮助用户部署此仓库时参考。

### ⚠️ 安装前必须执行的告知流程

在执行任何安装操作前，AI Agent **必须**向用户展示以下内容并等待确认：

---

> ⚠️ **安装前重要提示**
>
> **仓库现状**：
> - 本仓库的 `main` 分支包含通用技术经验和个人/项目经验混合内容
> - 尚未进行分支隔离
>
> **注意事项**：
> - 仓库中的经验不一定适用于你的项目，请根据实际情况判断
> - 个人/项目特定内容仅供参考
> - 安装后 AI Agent 会基于所有经验进行检索，需自行判断适用性
>
> **请选择安装方式**：
> 1. **直接使用** - 克隆后自行删除不适用的经验
> 2. **Fork 自定义** - 推荐方式，在 GitHub Fork 后管理自己的版本
> 3. **选择性克隆** - 只保留需要的分类目录
> 4. **暂不安装** - 取消安装
>
> 请回复数字或描述你的选择。

---

### 关键路径

| 用途 | 路径 |
|------|------|
| Skills 定义 | `~/.copilot/skills/experience-logger/SKILL.md` |
| 经验数据目录 | `~/.copilot/experiences/` |
| Claude Code 全局指令 | `~/.copilot/CLAUDE.md` |

### 操作原则

1. **修改前先同步**：任何修改前执行 `git pull`
2. **修改后立即推送**：确保多设备数据一致
3. **安装前必须告知**：必须显示仓库现状和注意事项
4. **验证操作结果**：每步操作后检查是否成功

---

## 详细说明

> 以下内容包含详细的架构图和流程说明，供需要深入了解的人参考。如果你只是快速上手，可以忽略本部分。

### 系统架构

```mermaid
flowchart TB
    subgraph User["👤 用户"]
        Q[提问/请求记录]
        FB[反馈/修正请求]
    end

    subgraph Agent["🤖 Copilot Agent"]
        direction TB
        Parse[解析意图]
        Search[检索本地知识库]
        Web[联网搜索]
        Format[格式化答案]
        Save[归档经验]
        Validate[验证经验]
        Correct[修正/废弃]
    end

    subgraph KB["📚 知识库 experiences/"]
        Unity[unity/]
        CSharp[csharp/]
        Shader[shader/]
        Other[...]
    end

    subgraph Sync["☁️ 云端同步"]
        Git[GitHub 仓库]
    end

    Q --> Parse
    Parse --> Search
    Search -->|找到| Validate
    Validate -->|有效| Format
    Validate -->|需修正| Correct
    Search -->|未找到| Web
    Web --> Format
    Format -->|需要保存| Save
    Save --> KB
    Correct --> KB
    KB <--> Git
    Format -->|返回答案| User
    FB --> Validate
```

### 详细使用场景

#### 场景 A：遇到新问题 (检索 + 学习)

```mermaid
flowchart LR
    A[📝 用户提问] --> B{🔍 检索本地知识库}
    B -->|✅ 有记录| C[引用本地文档回复]
    B -->|❌ 无记录| D[🌐 联网搜索]
    D --> E[提供答案]
    E --> F{💾 是否保存?}
    F -->|是| G[归档到知识库]
    G --> H[☁️ 自动同步]
    C --> I[完成]
    F -->|否| I
    H --> I
```

#### 场景 B：显式记录 (归档)

```mermaid
flowchart LR
    A[📝 记录请求] --> B[⬇️ 拉取最新内容]
    B --> C[📋 分析并格式化]
    C --> D[💾 保存到知识库]
    D --> E[⬆️ 推送到远程]
    E --> F[✅ 完成]
```

#### 场景 C：验证与修正 (质量保障)

```mermaid
flowchart TB
    A[🔔 用户反馈] --> B[📍 定位相关经验]
    B --> C{🔍 验证正确性}
    C -->|✅ 经验正确| D[分析使用场景差异]
    C -->|⚠️ 部分正确| E[小幅修正]
    C -->|❌ 确实有误| F{判断修正类型}

    F -->|可修复| G[🔧 重大修正<br/>保留历史记录]
    F -->|已过时| H[🔄 标记废弃<br/>添加替代方案]

    D --> I[补充适用条件说明]
    E --> J[更新验证记录]
    G --> J
    H --> J
    I --> J

    J --> K[☁️ 同步更新]
    K --> L[📢 反馈用户处理结果]
```

#### 场景 D：处理经验冲突

```mermaid
flowchart LR
    A[⚠️ 发现冲突] --> B{🔍 分析原因}
    B -->|场景不同| C[标注适用条件<br/>互相引用]
    B -->|版本差异| D[标注版本范围<br/>推荐新方案]
    B -->|真正矛盾| E[验证后修正<br/>废弃错误记录]
    C --> F[🔗 建立关联]
    D --> F
    E --> F
    F --> G[☁️ 同步更新]
```

### 自动同步详细流程

```mermaid
sequenceDiagram
    participant U as 用户
    participant A as Agent
    participant L as 本地仓库
    participant R as 远程仓库

    U->>A: 请求保存经验
    A->>L: git pull (拉取最新)
    R-->>L: 同步远程更改
    A->>L: 写入 Markdown 文件
    A->>L: git add & commit
    A->>R: git push (推送更改)
    R-->>A: 推送成功
    A->>U: ✅ 保存完成

    Note over A,R: 如遇冲突/网络问题<br/>会提示用户手动处理
```

---

*Created by KT's Copilot Agent*

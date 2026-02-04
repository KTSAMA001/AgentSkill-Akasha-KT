# 🧠 Akasha-KT | 阿卡西记录

> 阿卡西（Akasha）源自古印度哲学，意为"宇宙记忆"——万物经验与知识的永恒档案。

一套持续学习型的 AI Agent Skills，具备**经验记录**、**知识沉淀**和**灵感收集**能力。

## 📦 包含技能

| 技能 | 用途 | 存储位置 | 
|------|------|----------|
| **akasha-kt** | 阿卡西记录 - 经验与知识的记忆中枢 | `data/` |

## 🔄 核心工作流程

### 总体交互流程

```mermaid
flowchart TD
  A[用户输入] --> B{意图识别}
  B -->|提问/求助| C[查找流程]
  B -->|记录请求| D[记录流程]
  B -->|验证/修正| E[验证流程]
  
  C --> C1[检索 data/ 目录]
  C1 -->|找到| C2[展示并应用]
  C1 -->|未找到| C3[网络搜索]
  C3 --> C4[解决问题]
  C4 --> C5{是否记录?}
  C5 -->|是| D
  C5 -->|否| F[结束]
  
  D --> D1{判断内容类型}
  D1 -->|问题方案| D2[记录为经验]
  D1 -->|概念原理| D3[记录为知识]
  D1 -->|创意想法| D4[记录为灵感]
  D2 --> D5[格式化 & 写入]
  D3 --> D5
  D4 --> D5
  D5 --> D6[Git Commit & Push]
  D6 --> F
  
  E --> E1[交叉验证]
  E1 --> E2{验证结果}
  E2 -->|正确| F
  E2 -->|需修正| D5
```

### 经验 vs 知识 vs 灵感 决策树

```mermaid
flowchart LR
  A[待记录内容] --> B{核心问题是什么?}
  
  B -->|"怎么解决? / 怎么做?"| C[经验 Experience]
  B -->|"是什么? / 为什么?"| D[知识 Knowledge]
  B -->|"创意 / 想法 / 灵感"| E[灵感 Ideas]
  
  C --> C1[记录: 问题+方案+验证]
  D --> D1[记录: 定义+原理+要点]
  E --> E1[记录: 想法+可行性+分析]
  
  C1 --> F[data/experiences/]
  D1 --> G[data/knowledge/]
  E1 --> H[data/ideas/]
```

## 🚀 安装

### VS Code Copilot

```bash
# macOS / Linux
# 注：目录名可自定义，默认为仓库名
git clone https://github.com/KTSAMA001/AgentSkill-Akasha-KT.git ~/.copilot/skills/akasha-kt

# Windows (PowerShell)
git clone https://github.com/KTSAMA001/AgentSkill-Akasha-KT.git $HOME\.copilot\skills\akasha-kt
```

### Claude Code

```bash
git clone https://github.com/KTSAMA001/AgentSkill-Akasha-KT.git ~/.claude/skills/akasha-kt
```

## ✅ 验证安装

在 AI Chat 中输入：

> "帮我记录一下今天解决的问题"
> "记一下这个知识点"
> "保存这个创业灵感"

如果 Agent 能识别并激活 `akasha-kt` Skill，即表示安装成功。

## 📂 目录结构

``` /
# 本仓库根目录（目录名由 clone 时指定）
├── README.md           # 本文件
├── SKILL.md            # 核心指令（Agent 识别技能的入口）
├── references/          # 详细文档
│  ├── INDEX.md         # 分类索引
│  ├── OPERATIONS.md    # 操作流程
│  ├── EXAMPLES.md      # 使用示例
│  └── VALIDATION.md    # 验证流程
└── data/
  ├── experiences/      # 经验数据（问题解决方案）
  ├── knowledge/        # 知识数据（概念原理）
  └── ideas/            # 灵感数据（创意想法与创业点子）
```

## ⚠️ 重要说明

### 内容分类

| 类型 | 说明 | 适用性 |
|------|------|--------|
| 通用技术经验 | Unity、C#、Shader 等通用解决方案 | ✅ 大部分人可用 |
| 个人/项目经验 | 特定项目配置、个人偏好 | ⚠️ 按需参考 |
| 知识概念 | 技术原理、定义、理论 | ✅ 通用参考 |
| 创意灵感 | 创业点子、产品想法 | 💡 待验证 |

### 推荐使用方式

| 方式 | 说明 |
|------|------|
| 直接克隆 | 快速体验 |
| Fork 自定义 | 长期使用（推荐） |

## 📄 许可证

MIT License

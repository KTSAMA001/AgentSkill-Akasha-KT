# 记录流程

> 将有价值的内容保存为独立记录文件

---

## 一、流程总览

1. **同步仓库**：`git pull origin main`
2. **确定文件名** → `kebab-case` 自解释命名
3. **全面验证** → 按 [validate.md](./validate.md) 检查（重复检测、正确性、时效性等）
4. **格式化写入** → 按 [record-template.md](../templates/record-template.md) 模板写入 `data/` 目录
5. **打标签** → 确保至少 1 个领域标签 + 1 个类型标签
6. **更新索引** → 同步更新 [INDEX.md](../INDEX.md) 的文件清单和标签索引
7. **提交推送** → Git Commit & Push

---

## 二、文件命名规则

- 格式：`kebab-case`，全小写，连字符分隔
- 要求：自解释，无需依赖目录上下文即可理解内容
- 位置：一律写入 `data/*.md`，**不创建子目录**

### 命名示例
| 内容 | 文件名 |
|------|--------|
| URP 自定义 Renderer Feature | `urp-renderer-feature-custom.md` |
| C# 异步编程踩坑 | `csharp-async-pitfalls.md` |
| Git PAT 认证故障 | `git-pat-credential-fix.md` |
| 明日方舟工业风 UI 分析 | `arknights-ui-industrial-style.md` |
| 3D 美少女智能家具创意 | `idea-3d-girl-smart-furniture.md` |

---

## 三、标签打标

> 标签是唯一的分类机制，务必认真打标。

### 必选标签
| 维度 | 数量 | 预定义值 |
|------|------|----------|
| **领域** | ≥1 | `#unity` `#shader` `#graphics` `#csharp` `#python` `#git` `#ai` `#web` `#design` `#tools` `#vscode` `#social` |
| **类型** | 1 | `#experience` `#knowledge` `#idea` `#reference` `#architecture` |

### 可选标签
| 维度 | 说明 |
|------|------|
| **专项** | 具体技术/主题：`#urp` `#hlsl` `#mcp` `#physics` 等 |
| **自定义** | 按需创建，不受限制 |

### 标签格式
- `#小写英文`，多词用连字符：`#behavior-designer`
- 领域标签可多选（如 Renderer Feature → `#unity` `#shader` `#graphics`）
- 类型标签单选

---

## 四、提取要点清单

根据内容性质，关注以下要点：

### 经验类 (#experience)
- **标题**：一句话概括问题与方案
- **问题描述**：发生的场景、报错信息
- **解决方案**：具体的修复步骤或代码
- **版本环境**：Unity 202x, VS Code xxx
- **参考链接**：StackOverflow, Unity Forum

### 知识类 (#knowledge)
- **标题**：知识点名称
- **定义**：简练的概念解释
- **原理**：底层逻辑或工作机制
- **来源**：官方文档、权威书籍
- **示例**：简单的用法演示

### 创意类 (#idea)
- **标题**：创意名称
- **灵感来源**：触发想法的事件/需求
- **核心想法**：创意的完整描述
- **可行性**：初步评估

---

## 五、索引更新

每次新增/修改记录后，**必须**同步更新 [INDEX.md](../INDEX.md)：

1. **文件清单视图**：在表格中添加一行，填入文件名、标签、状态、简述
2. **标签索引视图**：在该文件所有领域标签分组下添加条目

---

## 六、仓库同步与规范

### Commit 规范
`git commit -m "Type: Subject"`

| 类型 | 格式示例 |
|------|----------|
| **新增记录** | `docs: add [文件名]` |
| **更新内容** | `docs: update [文件名] - [说明]` |
| **修正错误** | `fix: correct [文件名] - [错误]` |
| **系统维护** | `chore: [说明]` |

### 冲突解决
```bash
git pull --rebase origin main
# 解决冲突
git add . && git rebase --continue
git push origin main
```

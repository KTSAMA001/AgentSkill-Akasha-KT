# 记录流程

> 将有价值的内容保存为独立记录文件

---

## 一、流程总览

1. **同步仓库**：`git pull origin main`
2. **确定文件名** → `kebab-case` 自解释命名
3. **全面验证** → 按 [validate.md](./validate.md) 检查（重复检测、正确性、时效性等）
4. **格式化写入** → 按 [record-template.md](../templates/record-template.md) 模板写入 `data/` 目录
5. **保存资源** → 如有图片等资源，按资源文件规范保存至 `assets/` 并使用相对路径引用
6. **打标签** → 确保至少 1 个领域标签 + 1 个类型标签
7. **更新索引** → 更新 [INDEX.md](../INDEX.md) 的文件清单（如有新标签则同步更新标签概览）
8. **提交推送** → Git Commit & Push

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

### 要求
- 每条记录 **至少 2 个标签**
- 查看 [INDEX.md](../INDEX.md) 标签概览，**优先复用已有标签**
- **创建原则**：允许细粒度标签，但需**节制**。仅当某概念具有**复用价值**（预计会有多条记录归属此类）时才创建新标签。对于极低频或一次性的细节概念，依赖全文检索即可。
- 新标签格式：`#小写英文`，多词用连字符：`#behavior-designer`
- 如使用了新标签，**必须**同步更新 [INDEX.md](../INDEX.md) 的索引列表。

### 示例
| 内容 | 标签 |
|------|------|
| URP Renderer Feature 开发经验 | `#unity` `#shader` `#urp` `#renderer-feature` `#experience` |
| PBR 渲染理论 | `#graphics` `#pbr` `#brdf` `#knowledge` |
| Git PAT 认证故障 | `#git` `#credential` `#experience` `#bug` |
| 3D 智能家具创意 | `#idea` `#smart-furniture` |

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

## 五、资源文件处理

> 当记录包含图片、示意图等需要离线保存的资源时，按以下规范处理。

### 适用场景

- 抓取外部文章（知乎、CSDN 等）中的配图
- 技术示意图、架构图、流程图
- UI 截图、效果对比图
- 任何需要离线保存以防链接失效的图片资源

### 存储规范

| 项目 | 规则 |
|------|------|
| **存储位置** | `assets/<record-name>/`（record-name 为记录文件名去掉 `.md`） |
| **文件命名** | `序号-描述.扩展名`，如 `01-retarget-concept.png`、`03-architecture-diagram.png` |
| **序号规则** | 两位数字，按内容出现顺序编号：`01-`、`02-`、`03-` ... |
| **描述规则** | `kebab-case`，简明描述图片内容 |
| **支持格式** | `.png`、`.jpg`、`.gif`、`.svg`、`.webp` |

### 引用方式

在 md 文件中使用**相对路径**引用，**禁止使用绝对路径**：

```markdown
![图片描述 - 补充说明](../assets/<record-name>/01-image-name.png)
```

- `data/xxx.md` → `../assets/xxx/` （上一级再进入 assets）
- alt 文本应包含图片内容描述，便于无图阅读

### 图片资源清单（可选）

当图片较多（≥5 张）时，建议在记录末尾添加资源清单表格：

```markdown
### 图片资源清单

| # | 文件名 | 说明 | 大小 |
|---|--------|------|------|
| 1 | `01-xxx.png` | 描述 | XX KB |
```

### 注意事项

- **不保存**：用户头像、广告图、网站 UI 装饰等非内容图片
- **不保存**：可通过代码/文字精确描述的简单信息
- **需保存**：技术示意图、架构图、效果对比图等对理解内容有重要价值的图片
- 下载图片时需设置合适的 `Referer` 和 `User-Agent` 请求头以避免防盗链

---

## 六、索引更新

每次新增/修改记录后，**必须**同步更新 [INDEX.md](../INDEX.md)：

1. **文件清单**：在表格中添加一行，填入文件名、标签、状态、简述
2. **标签概览**：仅当使用了新标签时，将新标签追加到概览列表中

---

## 七、仓库同步与规范

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

# 记录流程

> 将有价值的内容保存为独立记录文件

---

## 一、流程总览

1. 🔴 **CRITICAL - 同步仓库**：`git pull origin main`
2. 🟡 **IMPORTANT - 确定文件名**：`kebab-case` 自解释命名
3. 🟡 **IMPORTANT - 判断记录类型**：原创整理 **or** 转载存档（见下方「二、记录类型分支」）
4. 🔴 **CRITICAL - 全面验证**：按 [validate.md](./validate.md) 检查（重复检测、正确性、时效性等）
5. 🔴 **CRITICAL - 格式化写入**：按对应类型的写入规范写入 `data/` 目录
6. 🟡 **IMPORTANT - 保存资源**：如有图片等资源，按资源文件规范保存至 `assets/` 并使用相对路径引用
7. 🟡 **IMPORTANT - 打标签**：确保至少 1 个领域标签 + 1 个类型标签
8. 🔴 **CRITICAL - 更新索引**：更新 [INDEX.md](../INDEX.md) 的文件清单（如有新标签则同步更新 tag-registry.md（如新标签））
9. 🔴 **CRITICAL - 提交推送**：Git Commit & Push

### 正式记录原则

- 写入 `data/` 的内容必须一次成型为正式记录，禁止写入草稿、占位符、临时片段或“后续再整理”的半结构化内容。
- 记录流程只负责内容入库与索引同步，不负责修改模板、workflow、字段 schema、索引规则等系统层契约；此类变更必须走 [governance.md](./governance.md)。
- 若当前信息不足以形成正式记录，应先继续整理信息或等待补充，不得通过降低结构要求来完成入库。

### 强制脚本辅助

- 全库结构校验**必须**使用 [validate_records.py](../scripts/validate_records.py) 做只读检查，禁止跳过脚本直接凭人工目测宣称“已验证”。
- 文件清单同步**必须**使用 [regenerate_index.py](../scripts/regenerate_index.py) 重建 `INDEX.md` 的“文件清单”表格，禁止手工逐行维护派生表格。
- 脚本用法与边界**必须**遵循 [scripts/README.md](../scripts/README.md)。

### 强制执行顺序

```bash
python references/scripts/validate_records.py
python references/scripts/regenerate_index.py
python references/scripts/validate_records.py
```

- 第一次校验用于发现结构问题；未执行不得进入后续索引同步步骤。
- 索引重建只负责同步 `INDEX.md` 文件清单，不修正文义问题；禁止把脚本输出误解为“记录内容已经合规”。
- 第二次校验用于确认索引已同步，且没有引入新的结构错误；未完成第二次校验，不得宣称记录流程已闭环完成。

---

## 二、记录类型分支

收到记录请求时，首先判断内容类型并选择对应流程：

### 判断规则

| 条件 | 记录类型 | 写入规范 |
|------|----------|----------|
| 用户要求「转载」「存档」「原文保存」| **转载存档** | 见 [二-B 转载存档流程](#二-b-转载存档流程) |
| 内容来自外部文章且需完整保留 | **转载存档** | 见 [二-B 转载存档流程](#二-b-转载存档流程) |
| 用户自己的经验/知识/创意 | **原创整理** | 见 [三、提取要点清单](#三提取要点清单)，按模板整理 |
| 来自讨论但需要结构化提炼 | **原创整理** | 按模板整理，提炼要点 |

### 🔴 二-B 转载存档流程

> 当用户要求将外部文章（知乎、博客、论坛等）完整转载保存时使用。

**核心原则：保留原文，不改写。**

1. **抓取完整内容**
   - 优先使用 `opencli-rs` 对应站点的 `download` 命令
   - 若 opencli-rs 截断，使用 Chrome AppleScript JS 提取（需用户开启「允许 Apple 事件中的 JavaScript」）
   - 提取 HTML 或纯文本均可，但**必须确保内容完整**，不能截断

2. **下载图片到本地**
   - 从文章中提取所有内容相关图片 URL（排除头像、广告、装饰图）
   - 下载到 `assets/<record-name>/` 目录
   - 命名规则：`序号-描述.扩展名`（如 `01-article-cover.jpg`）
   - 下载时设置 `Referer` 和 `User-Agent` 请求头避免防盗链

3. **写入记录（格式要求）**
   - **元数据块**：使用标准模板（标签、来源、收录日期等）
   - **概要**：1-2 句话概括文章主题（可自行撰写）
   - **内容**：`### 内容` 标题下**完整保留原文**，包括：
     - 原文的标题层级结构（h2、h3 等）
     - 原文的段落文字（不删改、不缩写）
     - 原文的表格（按 Markdown 表格格式还原）
     - 原文的代码块（按对应语言标记还原）
     - 原文的引用块（blockquote）
   - **图片替换**：将原文图片 URL 替换为本地相对路径 `![](../assets/<record-name>/xx.jpg)`
   - **禁止**：
     - ❌ 改写、缩写、概括原文内容
     - ❌ 调整原文结构或顺序
     - ❌ 添加自己的分析或注释（如有补充，放在「### 内容」之外）
     - ❌ 省略任何段落或章节（即使是「不重要的」部分）

4. **参考链接与相关记录**
   - 在 `### 参考链接` 中记录原文 URL
   - 在 `### 相关记录` 中关联相关的阿卡西记录

**格式示例**：

```markdown
# 文章标题

**标签**：#领域标签 #类型标签
**来源**：[来源平台 - 作者名](URL)
**收录日期**：YYYY-MM-DD
**来源日期**：原文发布日期
**状态**：⚠️ 待验证
**可信度**：⭐⭐⭐（说明）

### 概要

一两句话概括文章主题。

### 内容

![封面图](../assets/record-name/01-cover.jpg)

原文内容完整保留在这里，包括标题、段落、表格、代码块、图片引用……

## 原文二级标题

原文段落内容……

![配图](../assets/record-name/02-screenshot.png)

### 参考链接

- [原文标题](URL) - 原文

### 相关记录

- [相关记录](./other-record.md) - 关联说明

### 验证记录

- [YYYY-MM-DD] 初次记录，来源：[说明]
```

**已有参考**：[endfield-rendering-study.md](../../data/endfield-rendering-study.md)、[modified-renderdoc-wuwa-capture.md](../../data/modified-renderdoc-wuwa-capture.md) 是转载存档的标准范例。

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
- 查看 [tag-registry.md](../tag-registry.md)，**优先复用已有标签**
- **创建原则**：允许细粒度标签，但需**节制**。仅当某概念具有**复用价值**（预计会有多条记录归属此类）时才创建新标签。对于极低频或一次性的细节概念，依赖全文检索即可。
- 新标签格式：`#小写英文`，多词用连字符：`#behavior-designer`
- 如使用了新标签，**必须**同步更新 [tag-registry.md](../tag-registry.md) 与 [INDEX.md](../INDEX.md) 的相关内容。

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
2. **标签概览**：仅当使用了新标签时，将新标签添加到 [tag-registry.md](../tag-registry.md)（含维度和说明）
3. **一致性原则**：索引层仅做派生性同步，不得在更新索引时私自改写记录正文含义或新增未走治理流程的结构字段

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

---

## ✅ 完成门控（回复用户前逐项确认）

### 通用项

- [ ] 已执行 `git pull origin main`？
- [ ] 已完成重复检测与正确性验证？
- [ ] 记录已写入 `data/*.md`（非子目录）？
- [ ] 记录是否为正式成品，而不是草稿/临时片段/半结构化内容？
- [ ] 标签数量 ≥ 2（至少 1 个领域 + 1 个类型）？
- [ ] `references/INDEX.md` 已同步更新？
- [ ] 若使用新标签，`references/tag-registry.md` 已同步更新？
- [ ] 已执行 `git commit` 与 `git push`？

### 转载存档额外项

- [ ] 原文内容完整保留，未删改/缩写/调序？
- [ ] 所有内容图片已下载到 `assets/<record-name>/`？
- [ ] 图片引用已替换为本地相对路径？
- [ ] 元数据块包含来源 URL 和来源日期？

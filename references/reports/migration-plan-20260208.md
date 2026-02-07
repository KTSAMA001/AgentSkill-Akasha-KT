# 阿卡西记录系统重构 — 完整迁移计划

**日期**：2026-02-08
**目标**：将整个阿卡西记录系统从"目录层级 + 经验/知识二分法"重构为"扁平 `data/` + 纯标签驱动"。

---

## 阶段一：基础设施重写

### 步骤 1.1 — 创建统一模板

**文件**：`references/templates/record-template.md` (新建)

```markdown
# 记录模板 (Record Template)

> 统一模板，适用于所有类型的记录——经验、知识、创意、参考等，类型通过标签区分。

```markdown
## [标题]

**标签**：#领域标签 #专项标签 #类型标签 #自定义标签
**来源**：[出处 - 实践总结 / 官方文档 / 社区 / 书籍 / URL]
**收录日期**：YYYY-MM-DD
**来源日期**：YYYY-MM-DD（原始内容日期，外部来源必填）
**更新日期**：YYYY-MM-DD（如有更新）
**状态**：✅已验证 | ⚠️待验证 | 📘有效 | 🔄待更新 | 📕已过时 | ❌已废弃 | 🔬实验性 | 💡构想中
**可信度**：⭐⭐⭐⭐⭐(官方) ~ ⭐(待验证)
**适用版本**：[技术名称] X.X+（如适用）

### 概要

[一两句话概括核心内容]

### 内容

[主体内容，格式自由——按内容性质选择最合适的组织方式：
- 经验类：问题/场景 → 解决方案/结论
- 知识类：定义/概念 → 原理/详解 → 关键点
- 创意类：灵感来源 → 核心想法 → 可行性
- 参考类：速查表/API 列表/操作手册]

### 关键代码（如有）

​```语言
// 代码片段
​```

### 参考链接（如有）

- [来源名称](URL) - 简要说明

### 相关记录（如有）

- [相关记录标题](./other-record.md) - 关联说明

### 验证记录

- [YYYY-MM-DD] 初次记录，来源：[说明]
- [YYYY-MM-DD] 验证/更新说明

---
```

---

## 标签维度参考

> 标签是本系统的核心分类机制。每条记录**至少包含 1 个领域标签 + 1 个类型标签**。

| 维度 | 必选 | 说明 | 预定义标签 |
|------|------|------|-----------|
| **领域** | ✅ ≥1 | 技术/学科大类 | `#unity` `#shader` `#graphics` `#csharp` `#python` `#git` `#ai` `#web` `#design` `#tools` `#vscode` `#social` |
| **类型** | ✅ 1个 | 记录的性质 | `#experience` `#knowledge` `#idea` `#reference` `#architecture` |
| **专项** | 可选 | 具体技术/主题 | `#urp` `#hdrp` `#hlsl` `#react` `#mcp` `#physics` `#animation` `#editor` `#ui` `#performance` `#linq` `#async` `#cyberpunk` `#arknights` ... |
| **自定义** | 可选 | 描述性标签 | 按需自由创建，不受限制 |

### 标签使用规则

1. **标签格式**：`#小写英文`，多词用连字符 `#behavior-designer`
2. **领域可多选**：如 URP Renderer Feature 同时属于 `#unity` `#shader` `#graphics`
3. **类型单选**：每条记录只能是一种性质
4. **新标签自由创建**：遇到新领域/专项时直接使用新标签即可，无需审批
5. **索引同步**：使用新标签后需同步更新 [INDEX.md](../INDEX.md) 的标签索引

## 状态标记速查

| 标记 | 含义 | 典型场景 |
|------|------|----------|
| ✅ 已验证 | 经实践确认有效 | 踩坑方案、调试结论 |
| ⚠️ 待验证 | 理论可行但未实测 | 新收录的外部方案 |
| 📘 有效 | 信息准确且当前适用 | 概念原理、API 文档 |
| 🔄 待更新 | 有新版本或变更 | 版本已更新的知识 |
| 📕 已过时 | 不再适用当前环境 | 旧版本 API |
| ❌ 已废弃 | 错误或有风险 | 证伪的方案 |
| 🔬 实验性 | 非主流/试探性方案 | 创新尝试 |
| 💡 构想中 | 创意/灵感阶段 | 产品创意、技术设想 |

## 可信度评级

| 评级 | 说明 |
|------|------|
| ⭐⭐⭐⭐⭐ | 官方规范 / 权威著作 / 学术标准 |
| ⭐⭐⭐⭐ | 官方文档 / 厂商文档 / 实地分析 |
| ⭐⭐⭐ | 社区公认 / 广泛实践验证 |
| ⭐⭐ | 个人经验 / 小范围验证 |
| ⭐ | 来源不明 / 待验证 |

## 相关文档

- 分类索引：[INDEX.md](../INDEX.md)
- 记录流程：[workflows/record.md](../workflows/record.md)
- 查找流程：[workflows/search.md](../workflows/search.md)
- 验证流程：[workflows/validate.md](../workflows/validate.md)
```

### 步骤 1.2 — 重写 SKILL.md

**文件**：`SKILL.md` (覆盖)
**变更**：删除目录结构说明，改为标签分类；删除“经验 vs 知识”表格；更新权限表；更新意图路由；更新记录格式。

### 步骤 1.3 — 重写 record.md

**文件**：`references/workflows/record.md` (覆盖)
**变更**：简化流程（确定文件名 -> 验证 -> 写入 -> 打标签 -> 更新索引）；添加自解释命名规则 (`kebab-case`)；添加强制标签打标步骤；添加索引双视图更新步骤。

### 步骤 1.4 — 重写 search.md

**文件**：`references/workflows/search.md` (覆盖)
**变更**：采用 INDEX.md 标签索引查找；支持全局 grep 关键词匹配。

### 步骤 1.5 — 重写 validate.md

**文件**：`references/workflows/validate.md` (覆盖)
**变更**：统一验证流程；添加标签完整性检查（领域+类型）；简化交叉引用路径。

### 步骤 1.6 — 删除旧模板

**操作**：删除 `references/templates/experience-template.md` 和 `references/templates/knowledge-template.md`。

---

## 阶段二：数据迁移

### 步骤 2.1 — 删除无内容占位符文件 (~30文件)

删除仅含标题无内容的 `.md` 文件，如 `data/experiences/csharp/syntax.md`, `README.md` 等。

### 步骤 2.2 — 迁移并重命名有效文件

将 `experiences/`, `knowledge/`, `ideas/` 下的有效文件移动到 `data/` 根目录，并使用 `kebab-case` 自解释重命名。

**示例映射：**
- `data/experiences/ai/astrbot.md` -> `astrbot-mcp-integration.md`
- `data/knowledge/graphics/rendering-pipeline.md` -> `rendering-pipeline-overview.md`

### 步骤 2.3 — 补全标签元数据

对迁移后的每个文件，修改首部元数据，确保包含 `**标签**` 行，并且至少包含一个领域标签和一个类型标签。

### 步骤 2.4 — 修复交叉引用路径

扫描并替换文件内的相对路径，例如 `](../../knowledge/...` -> `](./...`。

---

## 阶段三：重建 INDEX.md

**文件**：`references/INDEX.md` (覆盖)
**结构**：
1. **参考文档**索引
2. **文件清单**视图（文件、标签、状态、简述），按字母序
3. **标签索引**视图（按标签分组列出文件）

---

## 阶段四：清理与提交

### 步骤 4.1 — 删除空目录
删除 `data/experiences/`, `data/knowledge/`, `data/ideas/`。

### 步骤 4.2 — 验证清单
- 检查 `data/` 下文件数量正确
- 检查引用路径正确
- 检查 INDEX.md 完整

### 步骤 4.3 — Git 提交
提交所有变更。

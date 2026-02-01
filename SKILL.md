---
name: akasha-kt
description: 阿卡西记录 - 经验与知识的记忆中枢。当用户说"记录一下"、"总结经验"、"保存结论"、"记一下这个知识点"、"归档这个问题"时使用此技能。
license: MIT
---

# Akasha-KT 阿卡西记录

## 核心规则

**写入位置**：
- 经验 → `data/experiences/<分类>/*.md`
- 知识 → `data/knowledge/<分类>/*.md`

**权限**：
| 路径 | 操作 |
|------|------|
| `data/**/*.md` | 读/写/新建，删除需确认 |
| `data/**/`（子目录） | 可新建 |
| `references/INDEX.md` | 读/写（分类索引需实时更新） |
| `SKILL.md`、`references/` 其他文件 | 只读 |
| 其他位置 | 禁止 |

**索引维护**：新增分类或文件时，同步更新 `references/INDEX.md`

**禁止**：在 `data/` 外创建数据文件 | 自定义格式 | 操作技能目录外文件

## 触发与操作流程

| 触发词 | 执行 |
|--------|------|
| "之前怎么解决的"、"有没有相关经验"、"查一下记录" | `references/OPERATIONS.md` → **一、查找流程** |
| "记录一下"、"总结经验"、"归档"、"记一下这个知识点" | `references/OPERATIONS.md` → **二、记录流程** |
| "这个不对"、"过时了"、"需要更新" | `references/OPERATIONS.md` → **三、验证流程** |
| 本地未找到相关记录 | `references/OPERATIONS.md` → **1.2 网络搜索** |
| 需确定分类 | `references/INDEX.md` |
| 记录经验 | `references/templates/experience-template.md` |
| 记录知识 | `references/templates/knowledge-template.md` |
| 修正/废弃记录 | `references/VALIDATION.md` |

## 记录格式

> **完整模板**：`references/templates/experience-template.md` | `references/templates/knowledge-template.md`

### 经验（简要）

```
## [标题]
收录/来源/更新日期 | 标签 | 状态(✅⚠️🔄❌🔬) | 适用版本
问题/场景 → 解决方案 → 关键代码 → 参考链接 → 验证记录 → 相关经验/理论基础
```

### 知识（简要）

```
## [标题]
分类 | 关键词 | 来源 | 日期 | 可信度(⭐~⭐⭐⭐⭐⭐) | 状态(📘🔄📕)
定义/概念 → 原理/详解 → 关键点 → 示例 → 相关知识 → 与经验关联
```

### 相互引用

```markdown
# 经验引用知识
**理论基础**：[知识点](../../knowledge/分类/文件.md#anchor)

# 知识引用经验
### 与经验关联
- [经验标题](../../experiences/分类/文件.md#anchor)
```

### 时间字段

| 字段 | 含义 |
|------|------|
| 收录日期 | 整理到本库的日期 |
| 来源日期 | 原始内容发布日期（外部来源必填） |
| 更新日期 | 最近修改日期 |

## 状态标记速查

| 经验 | 知识 | 可信度 |
|------|------|--------|
| ✅已验证 ⚠️待验证 🔄已过时 ❌已废弃 🔬实验性 | 📘有效 🔄待更新 📕已过时 | ⭐⭐⭐⭐⭐官方 → ⭐待验证 |

## 经验 vs 知识

| 类型 | 来源 | 核心问题 | 格式 |
|------|------|----------|------|
| 经验 | 实践、踩坑 | 怎么做/避坑 | 问题→方案→验证 |
| 知识 | 书籍、文档 | 是什么/为什么 | 概念→原理→要点 |

## 详细文档

| 文档 | 路径 | 重要性 |
|------|------|--------|
| **操作流程** | `references/OPERATIONS.md` | ⭐⭐⭐ 必读 |
| 分类索引 | `references/INDEX.md` | ⭐⭐ 查分类时读 |
| 验证流程 | `references/VALIDATION.md` | ⭐⭐ 修正时读 |
| 使用示例 | `references/EXAMPLES.md` | ⭐ 参考 |
| 经验模板 | `references/templates/experience-template.md` | 记录时读 |
| 知识模板 | `references/templates/knowledge-template.md` | 记录时读 |

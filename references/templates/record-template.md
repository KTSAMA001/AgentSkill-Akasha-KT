# 记录模板 (Record Template)

> 统一模板，适用于所有类型的记录——经验、知识、创意、参考等，类型通过标签区分。

```markdown
# [标题]

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

### 图片资源清单（如有，≥5 张图片时建议添加）

| # | 文件名 | 说明 | 大小 |
|---|--------|------|------|
| 1 | `01-xxx.png` | 图片描述 | XX KB |

> 图片存放于 `../assets/<record-name>/`，md 中使用相对路径引用：
> `![描述](../assets/<record-name>/01-xxx.png)`

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
| **领域** | ✅ ≥1 | 技术/学科大类 | 参见 [tag-registry.md](../tag-registry.md)，维度=domain |
| **类型** | ✅ 1个 | 记录的性质 | 参见 [tag-registry.md](../tag-registry.md)，维度=type |
| **专项** | 可选 | 具体技术/主题 | 参见 [tag-registry.md](../tag-registry.md)，维度=specialty |
| **自定义** | 可选 | 描述性标签 | 按需自由创建，不受限制 |

### 标签使用规则

1. **标签格式**：`#小写英文`，多词用连字符 `#behavior-designer`
2. **领域可多选**：如 URP Renderer Feature 同时属于 `#unity` `#shader` `#graphics`
3. **类型单选**：每条记录只能是一种性质
4. **新标签创建**：允许创建细粒度标签，但需**节制**。仅当该概念具有复用价值时才创建，避免标签爆炸。
5. **索引同步**：使用新标签后**必须**同步更新 [INDEX.md](../INDEX.md) 的标签索引，保持闭环。

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

## 元数据字段 Schema

> 此表由 Web 渲染管线自动解析，用于驱动元数据块的识别与渲染。修改字段时同步更新此表。

| 字段名 | key | 渲染类型 | 别名 |
|--------|-----|----------|------|
| 标签 | tags | tag-pills | — |
| 来源 | source | link | — |
| 收录日期 | recordDate | text | 日期 |
| 来源日期 | sourceDate | text | — |
| 更新日期 | updateDate | text | — |
| 状态 | status | status-icon | — |
| 可信度 | credibility | star-rating | — |
| 适用版本 | version | text | — |

## 状态定义

> 此表由 Web 渲染管线自动解析，驱动状态图标渲染与颜色分类。
> **重要**：记录中的状态 Emoji 必须与本表完全一致（精确到 Unicode 码点），不可使用近似或外观相似的 Emoji。

| Emoji | 标签 | 颜色 | SVG | 场景 |
|-------|------|------|-----|------|
| ✅ | 已验证 | success | status-verified | 踩坑方案、调试结论 |
| ⚠️ | 待验证 | warning | status-pending | 新收录的外部方案 |
| 📘 | 有效 | info | status-valid | 概念原理、API 文档 |
| 🔄 | 待更新 | warning | status-update | 版本已更新的知识 |
| 📕 | 已过时 | danger | status-obsolete | 旧版本 API |
| ❌ | 已废弃 | danger | status-deprecated | 证伪的方案 |
| 🔬 | 实验性 | info | status-experimental | 创新尝试 |
| 💡 | 构想中 | info | status-concept | 灵感阶段 |

## Emoji 渲染映射

> 源文件保留 Emoji 以保持 raw markdown 的人类可读性。Web 渲染管线在 sync 阶段自动将 Emoji 转换为对应 SVG 图标。
> 新增 Emoji 使用前须在本表注册映射关系。

| Emoji | SVG 图标 | CSS 类 | 说明 |
|-------|----------|--------|------|
| ✅ | mark-check | inline-icon--check | 推荐/正确标记（正文中） |
| ❌ | mark-cross | inline-icon--cross | 避免/错误标记（正文中） |
| ⚠️ | status-pending | inline-icon--warning | 注意/警告标记（正文中） |
| 🟢 | indicator-green | inline-icon--green | 等级指示：低/好 |
| 🟡 | indicator-yellow | inline-icon--yellow | 等级指示：中 |
| 🟠 | indicator-orange | inline-icon--orange | 等级指示：较高 |
| 🔴 | indicator-red | inline-icon--red | 等级指示：高/差 |
| ⭐ | star-filled | — | 可信度评级（由星级组件整体处理） |

## 相关文档

- 检索边界：`INDEX.md` 与本模板属于系统层文档，仅用于维护规范；知识检索与回答仅允许基于 `data/*.md`。
- 分类索引：[INDEX.md](../INDEX.md)
- 记录流程：[workflows/record.md](../workflows/record.md)
- 查找流程：[workflows/search.md](../workflows/search.md)
- 验证流程：[workflows/validate.md](../workflows/validate.md)

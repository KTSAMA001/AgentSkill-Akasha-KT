# VitePress 动态侧边栏标签 + 分类索引页自动生成

**收录日期**：2026-02-07
**标签**：#tools #web #experience #vitepress
**来源**：KTSAMA 实践经验
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐ (实践验证)

**问题/场景**：

VitePress 站点的侧边栏类目名称和各 section（经验/知识/灵感）的 index.md 首页都是手写硬编码的，每次新增分类都要手动改多处代码。

**解决方案/结论**：

### 1. 动态侧边栏标签

sidebar.ts 中原本用 CATEGORY_LABELS 映射表（20+ 条）将目录名翻译为中文。重构为：

- SPECIAL_LABELS：仅保留 7 条特殊映射（3 个顶级带 emoji + 4 个缩写如 ai->AI, csharp->C#）
- getCategoryLabel(dirName, dirPath?)：优先级为 SPECIAL_LABELS -> index.md frontmatter title -> h1 标题 -> 目录名美化

自动从 index.md 的 frontmatter title 或 h1 读取标签，新增分类只需创建含标题的 index.md 即可。

### 2. 分类索引页从 INDEX.md 元数据自动生成

sync-content.mjs 中新增：

- parseIndexMd()：解析阿卡西记录仓库的 references/INDEX.md 表格（格式：| 目录 | 中文名 | 描述 | 文件 |）
- generateCategoryIndexes()：为 experiences/knowledge/ideas 各自动生成 index.md，包含标题、描述、分类表格
- INDEX.md 是唯一的元数据来源，新增分类只需修改这一个文件

**验证记录**：

- 2026-02-07 动态侧边栏标签生效，所有分类名称正确显示
- 2026-02-07 三个 section 的 index.md 均从 INDEX.md 自动生成，表格内容一致

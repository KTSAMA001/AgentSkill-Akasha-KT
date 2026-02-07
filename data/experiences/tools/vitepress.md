# VitePress 站点开发经验

> VitePress 静态站点生成器相关经验
> 
> 包含：主题定制、侧边栏、favicon、CSS 特效、SPA 路由等

---

## VitePress 动态侧边栏标签 + 分类索引页自动生成

**收录日期**：2026-02-07
**标签**：#vitepress #sidebar #动态生成 #INDEX.md
**状态**：✅ 已验证

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

---

## Safari SVG Favicon 兼容性

**收录日期**：2026-02-07
**标签**：#favicon #safari #svg #png #兼容性
**状态**：⚠️ 待验证

**问题/场景**：

自定义 SVG favicon 在 Chrome 正常显示，但 Safari（尤其 HTTP 站点）不显示 SVG favicon，仍用默认图标。

**解决方案/结论**：

Safari 对 SVG favicon 支持不佳，特别是 HTTP（非 HTTPS）站点。需要提供 PNG 回退：

1. 使用 rsvg-convert（macOS 通过 homebrew 安装 librsvg）转换 SVG 为 PNG：
   - rsvg-convert -w 32 -h 32 favicon.svg -o favicon-32.png
   - rsvg-convert -w 180 -h 180 favicon.svg -o apple-touch-icon.png

2. HTML head 中同时提供 SVG + PNG + Apple Touch Icon

3. VitePress 的 public/ 目录下的文件需要清除 .vitepress/cache 和 .vitepress/dist 后重新构建才会生效

**验证记录**：

- 2026-02-07 SVG favicon 部署后 Chrome 正常显示，Safari 待验证

---

## VitePress SPA 路由中 position:fixed 伪元素泄漏

**收录日期**：2026-02-07
**标签**：#vitepress #css #position-fixed #spa
**状态**：⚠️ 待验证

**问题/场景**：

在 .VPHome::after 上使用 position:fixed 实现全屏暗角（vignette）效果。VitePress 的 SPA 路由切换后，用户从首页导航到其他页面时，固定定位的遮罩残留在页面上方覆盖内容。

**解决方案/结论**：

将 position:fixed 改为 position:absolute。absolute 定位相对于 .VPHome 元素本身，当 VitePress SPA 路由卸载首页内容时，伪元素随之消失，不会残留。

规则：VitePress 页面级装饰伪元素不要用 position:fixed，只用 absolute。全局级效果（如 body::before 噪点）可以用 fixed，因为 body 始终存在。

**验证记录**：

- 2026-02-07 修改后推送，待验证非首页是否还有残留

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

---

## 全站 Emoji 替换为 SVG 图标的完整流程 {#emoji-to-svg}

**收录日期**：2026-02-07
**标签**：#vitepress #svg #图标 #emoji #设计系统
**状态**：✅ 已验证

**问题/场景**：

站点多处使用 emoji 作为图标（例如 🎮Unity 开发、📝经验、📚知识等），在不同平台/浏览器上 emoji 渲染不一致，且无法用 CSS 精确控制颜色和尺寸，不符合工业风设计语言。

**解决方案/结论**：

### 涉及改动位置清单

| 文件 | 改动内容 |
|------|----------|
| `public/icons/*.svg` | 新增 10 个 SVG 图标文件 |
| `index.md` | features icon 改为 `{ src: /icons/xxx.svg, width: 48, height: 48 }` |
| `Dashboard.vue` | `{{ stat.icon }}` 文本插值 → `<img :src="stat.icon">` |
| `CategoryGrid.vue` | `<span>{{ item.icon }}</span>` → `<img :src="item.icon">` |
| `sync-content.mjs` | SECTION_CONFIG/stats 的 icon 从 emoji 改为 SVG 路径 |
| `sidebar.ts` | SPECIAL_LABELS 中 emoji 前缀（📝经验→经验）移除 |
| `custom.css` | 新增 `.VPFeature .VPImage` 的 filter 着色规则 |

### SVG 图标设计规范

最终采用 Lucide 图标库的设计标准：
- **画布**：24×24 viewBox
- **笔触**：`stroke-width="2"`、`stroke-linecap="round"`、`stroke-linejoin="round"`
- **填充**：`fill="none"`、`stroke="currentColor"`
- **风格**：简洁几何线条，不使用 fill 填充块

初版（1.5px square-cap）在小尺寸下显得粗糙，按 Lucide 规范重绘后明显提升。

**验证记录**：

- 2026-02-07 10 个 SVG 图标全部替换，三处组件渲染正常，构建通过

---

## `<img>` 标签的 SVG 无法继承 CSS color，需用 filter 着色 {#img-svg-color-filter}

**收录日期**：2026-02-07
**标签**：#css #svg #filter #currentColor #img
**状态**：✅ 已验证

**问题/场景**：

SVG 内部使用 `stroke="currentColor"` 期望继承父元素的 CSS `color` 属性。但当 SVG 通过 `<img src="xxx.svg">` 加载时，`currentColor` 解析为默认黑色（`#000`），因为 `<img>` 标签创建了独立的文档上下文，**不继承**外部 CSS 属性。

**解决方案/结论**：

### 方案对比

| 方案 | 优点 | 缺点 |
|------|------|------|
| **CSS filter（采用）** | 不改 HTML 结构，兼容 `<img>` | 颜色是近似值，非精确 |
| 内联 SVG | 完全支持 currentColor | 需改为 Vue 组件，增加复杂度 |
| SVG 中硬编码颜色 | 最简单 | 无法响应主题切换 |

### CSS filter 近似 #FF6B2B 橙色的参数

```css
filter: invert(48%) sepia(89%) saturate(1600%) hue-rotate(3deg) brightness(101%) contrast(103%);
```

该 filter 链将黑色 SVG 笔触转换为近似 `#FF6B2B` 的橙色。原理：
1. `invert` 将黑色翻转为白色
2. `sepia` 添加棕色调
3. `saturate` + `hue-rotate` 调整到目标色相
4. `brightness` + `contrast` 微调明度

**验证记录**：

- 2026-02-07 Dashboard、CategoryGrid、VPFeature 三处图标均正常显示橙色

---

## VitePress VPFeature 图标 HTML 结构（无 .icon 包裹层） {#vpfeature-icon-structure}

**收录日期**：2026-02-07
**标签**：#vitepress #VPFeature #css选择器 #html结构
**状态**：✅ 已验证

**问题/场景**：

在 `index.md` 的 features 中使用 `icon: { src: /icons/xxx.svg }` 格式，在 custom.css 中用 `.VPFeature .icon img` 选择器为图标添加 CSS filter 着色。但线上图标始终是黑色（filter 不生效）。

**解决方案/结论**：

VitePress 对 `{ src: '...' }` 格式的 feature icon 生成的 HTML 结构是：

```html
<article class="box" data-v-bd37d1a2>
  <img class="VPImage" src="/icons/xxx.svg" width="48" height="48">
  <h2 class="title">...</h2>
</article>
```

**关键发现**：`<img>` 直接位于 `.box` 内部，**没有** `.icon` 中间包裹层。因此 `.VPFeature .icon img` 选择器完全匹配不到。

正确选择器应为：

```css
.VPFeature .VPImage {
  filter: invert(48%) sepia(89%) saturate(1600%) hue-rotate(3deg) brightness(101%) contrast(103%);
}
```

**教训**：不要凭想象写 CSS 选择器，用 DevTools 或 `curl` + 分析实际渲染的 HTML 结构后再写。

**验证记录**：

- 2026-02-07 修正选择器后 MODULES 区域 6 个图标全部变为橙色

---

## 侧边栏自定义高亮竖条与文字间距 {#sidebar-padding-left}

**收录日期**：2026-02-07
**标签**：#vitepress #sidebar #css #间距
**状态**：✅ 已验证

**问题/场景**：

为侧边栏 `.item::before` 添加了 3px 宽的橙色高亮竖条（`left: 0`），但竖条与右侧文字之间几乎没有间距，视觉上挤在一起。

**解决方案/结论**：

给 `.VPSidebar .VPSidebarItem .item` 添加 `padding-left: 12px !important`，让文字与竖条之间保持 12px 的呼吸空间。

需要 `!important` 是因为 VitePress 默认样式对 `.item` 有自己的 padding 定义。

**验证记录**：

- 2026-02-07 间距修复后侧边栏视觉明显改善

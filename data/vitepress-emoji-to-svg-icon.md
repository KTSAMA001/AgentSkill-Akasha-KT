# 全站 Emoji 替换为 SVG 图标的完整流程 {#emoji-to-svg}

**收录日期**：2026-02-07
**标签**：#tools #web #experience #vitepress
**来源**：KTSAMA 实践经验
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐ (实践验证)

**问题/场景**：

站点多处使用 emoji 作为图标（例如 🎮Unity 开发、📝经验、📚知识等），在不同平台/浏览器上 emoji 渲染不一致，且无法用 CSS 精确控制颜色和尺寸，不符合工业风设计语言。

**解决方案/结论**：

### 涉及改动位置清单

| 文件 | 改动内容 |
|------|----------|
| `public/icons/*.svg` | 新增 10 个 SVG 图标文件 |
| `index.md` | features icon 改为 `{ src: /icons/xxx.svg, width: 48, height: 48 }` |
| `Dashboard.vue` | 文本插值 stat.icon → img 标签 :src 绑定 |
| `CategoryGrid.vue` | span 文本插值 item.icon → img 标签 :src 绑定 |
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

# img 标签的 SVG 无法继承 CSS color，需用 filter 着色 {#img-svg-color-filter}

**收录日期**：2026-02-07
**标签**：#tools #web #experience #vitepress
**来源**：KTSAMA 实践经验
**状态**：✅ 已验证

**问题/场景**：

SVG 内部使用 `stroke="currentColor"` 期望继承父元素的 CSS `color` 属性。但当 SVG 通过 img 标签加载时，`currentColor` 解析为默认黑色（`#000`），因为 img 标签创建了独立的文档上下文，**不继承**外部 CSS 属性。

**解决方案/结论**：

### 方案对比

| 方案 | 优点 | 缺点 |
|------|------|------|
| **CSS filter（采用）** | 不改 HTML 结构，兼容 img 标签 | 颜色是近似值，非精确 |
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

# VitePress VPFeature 图标 HTML 结构（无 .icon 包裹层） {#vpfeature-icon-structure}

**收录日期**：2026-02-07
**标签**：#tools #web #experience #vitepress
**来源**：KTSAMA 实践经验
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

**关键发现**：img 元素直接位于 `.box` 内部，**没有** `.icon` 中间包裹层。因此 `.VPFeature .icon img` 选择器完全匹配不到。

正确选择器应为：

```css
.VPFeature .VPImage {
  filter: invert(48%) sepia(89%) saturate(1600%) hue-rotate(3deg) brightness(101%) contrast(103%);
}
```

**教训**：不要凭想象写 CSS 选择器，用 DevTools 或 `curl` + 分析实际渲染的 HTML 结构后再写。

**验证记录**：

- 2026-02-07 修正选择器后 MODULES 区域 6 个图标全部变为橙色

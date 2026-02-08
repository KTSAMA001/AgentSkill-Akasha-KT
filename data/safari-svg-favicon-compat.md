# Safari SVG Favicon 兼容性

**收录日期**：2026-02-07
**标签**：#tools #web #experience #vitepress
**来源**：KTSAMA 实践经验
**状态**：⚠️ 待验证
**可信度**：⭐⭐⭐ (待验证)

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

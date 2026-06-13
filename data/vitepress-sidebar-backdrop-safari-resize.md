# VitePress Sidebar Backdrop 与 Safari Resize 问题

**标签**：#web #vitepress #experience #ui #macos #troubleshooting
**来源**：KTSAMA 实践经验
**收录日期**：2026-02-07
**来源日期**：2026-02-07
**更新日期**：2026-06-13
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐ (实践验证)
**适用版本**：VitePress 1.x + Safari（原记录未注明精确版本）

### 概要

VitePress `VPBackdrop` 在 sidebar 断点和 Safari 窗口 resize 场景下会暴露遮罩残留或重绘延迟问题。最终方案不是扩大覆盖层，而是让 Backdrop 透明化，仅保留点击关闭热区，并把层级感交给 sidebar 自身阴影。

### 内容

#### VPBackdrop 遮罩断点不匹配

窄屏时打开 sidebar 后，如果窗口尺寸跨过断点，可能出现 Backdrop 遮罩残留。

原记录确认的问题边界：

- sidebar 在 960px 切换为桌面常驻模式。
- `.VPBackdrop` 的 CSS `display: none` 断点在 1280px。
- sidebar 的 JS 控制逻辑没有 resize 监听来自动关闭状态。

修复方式是把 VPBackdrop 隐藏断点对齐到 960px：

```css
@media (min-width: 960px) {
  .VPBackdrop {
    display: none !important;
  }
}
```

#### Safari position: fixed resize 重绘延迟

`VPBackdrop` 使用 `position: fixed; inset: 0` 覆盖视口。Safari 拉伸窗口时，fixed 元素的尺寸重绘跟不上窗口变化速度，导致遮罩右下角边缘短暂漏出内容。

曾尝试用超大 box-shadow 替代依赖元素尺寸的覆盖：

```css
.VPBackdrop {
  box-shadow: 0 0 0 200vmax var(--vp-backdrop-bg-color) !important;
}
```

该方案已废弃：box-shadow 覆盖范围理论上足够，但实测 Safari 拉伸窗口时，box-shadow 的重绘同样存在延迟，仍会漏出边缘。

#### 最终方案：去掉遮罩视觉效果

VPBackdrop 遮罩在 Safari resize 时，无论用 background、box-shadow 还是 backdrop-filter，只要存在有视觉效果的全屏覆盖层，就会因 fixed 元素重绘延迟暴露边界瑕疵。

最终方案：

1. VPBackdrop 设为 `background: transparent`，仅保留作为点击热区关闭 sidebar 的功能。
2. sidebar 本身添加阴影，用投影表达层级感。

```css
.VPBackdrop {
  background: transparent !important;
  box-shadow: none !important;
}

@media (max-width: 959px) {
  .VPSidebar {
    box-shadow: 4px 0 24px rgba(0, 0, 0, 0.3) !important;
  }
}
```

核心思路：覆盖层的边界问题不可能通过纯 CSS 覆盖层完美解决，因此去掉视觉遮罩边界。

#### 原始残留片段

原聚合记录第 15 条含有一段明显乱码，围绕“窄屏时点开 sidebar”和“960px/1280px 断点不匹配”展开。语义已由本记录“VPBackdrop 遮罩断点不匹配”小节承载，乱码原文不再扩散到正文结论中，待后续二次整理时可回看原始聚合记录或 worker patch。

### 关键代码

见“内容”中的 `.VPBackdrop` 和 `.VPSidebar` CSS 片段。

### 相关记录

- [VitePress 宝塔 Nginx 部署 403/404 与 cleanUrls 刷新修复](./vitepress-nginx-deploy-403-cleanurls.md) - 同一 VitePress 站点的部署问题。

### 验证记录

- [2026-02-07] VPBackdrop 遮罩残留问题确认为 VitePress 断点不匹配 bug，已添加 CSS 修复。
- [2026-02-07] box-shadow 200vmax 方案实测仍会在 Safari resize 时漏出边缘，标记为已废弃。
- [2026-02-07] 最终方案“去掉遮罩视觉效果 + sidebar 阴影”已验证。
- [2026-06-13] 结构维护：从旧聚合记录拆分，未重新验证原技术结论；原第 15 条乱码片段已窄化归档为待二次整理残留。

---

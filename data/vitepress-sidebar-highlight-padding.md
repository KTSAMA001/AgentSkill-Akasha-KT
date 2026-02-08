# 侧边栏自定义高亮竖条与文字间距 {#sidebar-padding-left}

**收录日期**：2026-02-07
**标签**：#tools #web #experience #vitepress
**来源**：KTSAMA 实践经验
**状态**：✅ 已验证

**问题/场景**：

为侧边栏 `.item::before` 添加了 3px 宽的橙色高亮竖条（`left: 0`），但竖条与右侧文字之间几乎没有间距，视觉上挤在一起。

**解决方案/结论**：

给 `.VPSidebar .VPSidebarItem .item` 添加 `padding-left: 12px !important`，让文字与竖条之间保持 12px 的呼吸空间。

需要 `!important` 是因为 VitePress 默认样式对 `.item` 有自己的 padding 定义。

**验证记录**：

- 2026-02-07 间距修复后侧边栏视觉明显改善

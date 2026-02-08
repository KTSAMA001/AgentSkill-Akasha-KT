# VitePress SPA 路由中 position:fixed 伪元素泄漏

**收录日期**：2026-02-07
**标签**：#tools #web #experience #vitepress
**来源**：KTSAMA 实践经验
**状态**：⚠️ 待验证
**可信度**：⭐⭐⭐ (待验证)

**问题/场景**：

在 .VPHome::after 上使用 position:fixed 实现全屏暗角（vignette）效果。VitePress 的 SPA 路由切换后，用户从首页导航到其他页面时，固定定位的遮罩残留在页面上方覆盖内容。

**解决方案/结论**：

将 position:fixed 改为 position:absolute。absolute 定位相对于 .VPHome 元素本身，当 VitePress SPA 路由卸载首页内容时，伪元素随之消失，不会残留。

规则：VitePress 页面级装饰伪元素不要用 position:fixed，只用 absolute。全局级效果（如 body::before 噪点）可以用 fixed，因为 body 始终存在。

**验证记录**：

- 2026-02-07 修改后推送，待验证非首页是否还有残留

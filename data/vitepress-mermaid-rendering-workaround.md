# VitePress Mermaid 渲染兼容方案

**标签**：#web #vitepress #experience #markdown #troubleshooting
**来源**：KTSAMA 实践经验
**收录日期**：2026-02-07
**来源日期**：2026-02-07
**更新日期**：2026-06-13
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐ (实践验证)
**适用版本**：VitePress 1.6.4 + vitepress-plugin-mermaid 2.0.17 对比自定义 Mermaid 组件方案

### 概要

`vitepress-plugin-mermaid@2.0.17` 与 VitePress 1.6.4 存在兼容性问题，可能导致依赖解析异常和白屏。最终方案是卸载插件，使用自定义客户端 Mermaid 组件，并在 markdown fence 规则中拦截 `mermaid` 代码块。

### 内容

#### 插件兼容性问题

原始判断曾认为 VitePress 默认不渲染 Mermaid，需要引入 `vitepress-plugin-mermaid`。后续实践更正：`vitepress-plugin-mermaid@2.0.17` 与 VitePress 1.6.4 存在严重兼容性问题。

典型表现：

- 启动时报 `Failed to resolve dependency: vitepress > @vue/devtools-api, present in 'optimizeDeps.include'`。
- 页面白屏，客户端 JS 无法加载。
- 即使手动安装 `@vue/devtools-api` 和 `@vueuse/core` 也无法解决。

最终方案：

- 卸载 `vitepress-plugin-mermaid`。
- 改用客户端 Mermaid 组件。
- 在 VitePress 主题中注册为全局组件。

#### Mermaid 代码块自动渲染

单独注册 `<Mermaid code="...">` 全局组件不够，标准的 markdown fenced code block 不会被拦截。

方案是在 VitePress `markdown.config` 中重写 `fence` 规则：

- 拦截 `info === 'mermaid'` 的代码块。
- 将 Mermaid 内容 Base64 编码后传给 `<MermaidRenderer>` 组件。
- 客户端再解码并渲染。

注意：`atob()` 不支持 UTF-8 多字节字符（中文），解码时必须用 `TextDecoder`。

### 关键代码

```javascript
const binary = atob(encoded)
const bytes = Uint8Array.from(binary, c => c.charCodeAt(0))
const code = new TextDecoder('utf-8').decode(bytes)
```

### 相关记录

- [VitePress 宝塔 Nginx 部署 403/404 与 cleanUrls 刷新修复](./vitepress-nginx-deploy-403-cleanurls.md) - VitePress 静态站部署问题。
- [Akasha Web 同步脚本与 Git 部署坑](./akasha-web-sync-git-deploy-pitfalls.md) - 构建执行与本地依赖调用策略。

### 验证记录

- [2026-02-07] `vitepress-plugin-mermaid` 导致白屏，已移除并改用客户端组件方案。
- [2026-02-07] Mermaid 代码块渲染：markdown-it fence 拦截 + Base64 传参 + TextDecoder 解码，中文流程图正常显示。
- [2026-06-13] 结构维护：从旧聚合记录拆分，未重新验证原技术结论。

---

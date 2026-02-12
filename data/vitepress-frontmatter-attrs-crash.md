# VitePress 构建失败：markdown-it-attrs 与 Frontmatter 冲突

**标签**：#vitepress #bug #experience #web
**来源**：实践总结
**收录日期**：2026-02-13
**状态**：✅已验证
**可信度**：⭐⭐⭐⭐⭐
**适用版本**：VitePress 1.x

### 概要

在 VitePress 构建过程中（`npm run docs:build`），如果文档包含自定义 ID 语法（如 `{#id}`）且该语法被意外写入 Frontmatter（如 title 字段），会导致 `markdown-it-attrs` 插件抛出 `Error in pattern 'end of block'` 错误，造成构建失败。

### 内容

#### 问题现象
在项目中添加包含 LaTeX 公式和自定义 ID Header 的文档后，运行构建指令失败：
```
Error: markdown-it-attrs: Error in pattern 'end of block' at ...
```
最初误判为 LaTeX 公式（`$$`）导致，实际上是由于同步脚本错误处理了 Markdown 内容。

#### 根因分析
1.  **同步脚本逻辑**：项目使用自定义脚本从外部仓库同步 Markdown 文件。脚本会提取正文的第一个 H1 标题作为 Frontmatter 的 `title` 字段。
    - 原文标题：`# Title {#custom-id}`
    - 提取后 Frontmatter：`title: Title {#custom-id}`
2.  **插件冲突**：`markdown-it-attrs` 插件用于解析 `{}` 形式的属性。当它在 Frontmatter 的元数据字段（如 title）中遇到这种语法时，与 VitePress 的内部解析流程发生冲突，导致正则表达式匹配失败并抛出异常。
3.  **合法性对比**：
    - ✅ **正文中**：`# My Header {#my-id}` 是合法的，插件能正确转换。
    - ❌ **Frontmatter 中**：`title: My Header {#my-id}` 是危险的，应仅包含纯文本。

#### 解决方案
修改同步脚本（`scripts/sync-content.mjs`），在写入 Frontmatter 前，使用正则表达式清洗标题文本，移除 Markdown 扩展语法。

### 关键代码

修复前的逻辑（导致 Crash）：
```javascript
// 假设 contentTitle = "# My Title {#my-id}"
frontmatter.title = contentTitle;
```

修复后的逻辑（清洗数据）：
```javascript
// 移除结尾的 {#...} 锚点语法
const cleanHeading = (text) => text.replace(/\s*\{#[^}]+\}$/g, '').trim();

frontmatter.title = cleanHeading(contentTitle); 
// 结果: "My Title" (安全)
```

### 相关记录
无

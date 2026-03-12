# ClaudeMem Smart Tools Windows 修复

**标签**：#tools #windows #mcp #experience #bug
**来源**：实践总结
**收录日期**：2026-03-12
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐ (源码分析 + 实践验证)
**适用版本**：claude-mem 10.5.5 (Windows)

> ⚠️ **时效性说明**：此修复针对 claude-mem 10.5.5 版本。后续版本可能已修复此问题，升级插件后请先验证 Smart 工具是否正常工作。若正常则无需应用此修复。

### 概要

ClaudeMem 插件的 Smart 工具（smart_outline, smart_search, smart_unfold）在 Windows 上返回 "Could not parse" 错误。根因是 tree-sitter CLI 调用参数不兼容，修改 `mcp-server.cjs` 使用预编译的 `.node` 文件即可修复。

### 内容

#### 问题描述

调用 smart_outline 等 Smart 工具时，无论文件内容如何，均返回：
```
Could not parse xxx. File may use an unsupported language or be empty.
```

#### 根因分析

1. `mcp-server.cjs` 使用 `-p` 参数传递 grammar 源码目录给 tree-sitter CLI
2. tree-sitter CLI 在 Windows 上无法编译 grammar（需要 C 编译器如 MSVC/GCC/Clang）
3. 但预编译的 `.node` 文件已存在于 `node_modules/*/prebuilds/win32-x64/` 目录中

#### 解决方案

修改 `mcp-server.cjs` 中的 `Qy` 函数，优先使用 `-l` 参数指定预编译的 `.node` 文件：

### 关键代码

```javascript
// 文件位置: mcp-server.cjs 第 102 行附近
// 原代码
o=["query","-p",r,e,...t]

// 修复后：先查找预编译.node文件，有的话用-l，没有才用-p
s=function(e){try{let t=Hy.resolve("tree-sitter-"+(e==="tsx"?"typescript":e)+"/package.json"),n=(0,Wt.dirname)(t),o=process.platform==="win32"?"win32-x64":"linux-x64",i=(0,Wt.join)(n,"prebuilds",o,"tree-sitter-"+(e==="tsx"?"typescript":e)+".node");return(0,It.existsSync)(i)?i:null}catch{return null}}(e),o=s?["query","-l",s,"--lang-name",e,...t]:["query","-p",r,e,...t]
```

### 关键文件位置

| 文件 | 路径 |
|------|------|
| 修复文件 | `C:\Users\admin\.claude\plugins\cache\thedotmack\claude-mem\10.5.5\scripts\mcp-server.cjs` |
| 备份文件 | `mcp-server.cjs.bak`（同目录） |
| 预编译文件 | `node_modules/tree-sitter-*/prebuilds/win32-x64/*.node` |

### 支持的语言

javascript, typescript, tsx, python, go, rust, ruby, java, c, cpp

### 参考链接

- [tree-sitter CLI 文档](https://tree-sitter.github.io/tree-sitter/using-parsers)

### 验证记录

- [2026-03-12] 初次记录，来源：Windows 10 环境下调试分析
- [2026-03-12] 验证 smart_outline/smart_search/smart_unfold 均正常工作

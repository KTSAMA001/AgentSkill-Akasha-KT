# ClaudeMem Windows 修复记录 (v10.5.5 → v12.1.5)

**标签**：#tools #windows #mcp #experience #bug #cross-platform
**来源**：实践总结 + 源码分析
**收录日期**：2026-03-12
**来源日期**：2026-04-17
**更新日期**：2026-04-17
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐⭐ (多版本源码分析 + 实际修复验证)
**适用版本**：claude-mem 12.1.5 (Windows, tree-sitter 0.26.7)

### 概要

ClaudeMem 插件 v12.1.5 的 MCP server 在 Windows 上存在两个 Bug：语法错误导致整个 MCP server 无法启动，以及 Smart 工具的 tree-sitter 调用方式与 CLI 0.26.7 不兼容。两者均需手动修复，且 `claude plugins update` 后会被覆盖。

### 内容

---

## Bug 1：MCP server 语法错误（整个插件不可用）

### 问题描述

MCP server 启动时报 `SyntaxError: Unexpected token '}'`，导致所有 6 个工具（smart_outline/smart_search/smart_unfold/search/timeline/get_observations）全部不可用。

### 根本原因

`mcp-server.cjs` 中 `JO()` 函数（minified 的 `getTreeSitterBin`）将 `if` 语句与三元运算符混用，缺少关闭括号和语句体：

```javascript
// 代码结构（简化）
function JO(){
  if(Di) return Di;
  try{
    let t = path.join(dirname(pkgJson), "tree-sitter");
    if(existsSync(t) || existsSync(t+".exe") ? (existsSync(t+".exe") && (t=t+".exe"), Di=t, t) : 0
    //                                                            ↑ if 缺少 ) 和 {body}
  }catch{}
  return Di="tree-sitter", Di;
}
```

### 修复方案

将三目运算符改为正确的 `if...{...}` 结构：

```javascript
// 修复后
if(existsSync(t) || existsSync(t+".exe")){
  if(existsSync(t+".exe")) t = t+".exe";
  return Di=t;
}
```

---

## Bug 2：Smart 工具 tree-sitter 调用不兼容

### 问题描述

`smart_outline` 返回 "Could not parse xxx. File may use an unsupported language or be empty."。

### 根本原因

`ab()` 函数使用 `tree-sitter query -p <grammar-dir>` 调用 tree-sitter CLI。但在 **tree-sitter 0.26.7** 中，`-p`（`--grammar-path`）意味着 `--rebuild`，会尝试从 C 源码编译 grammar。Windows 上无 C 编译器时必然失败。

```javascript
// 原始代码
o = ["query", "-p", grammarDir, queryFile, sourceFile]
```

### 修复方案

添加两个辅助函数，改用 `--lib-path` 指向预编译 `.node` 文件 + `--lang-name` 指定语言：

```javascript
// MP(): 从 grammar 目录向上查找预编译 .node 文件
function MP(grammarDir){
  for(let dir of [grammarDir, dirname(grammarDir)]){
    let prebuildsPath = join(dir, "prebuilds", platform+"-"+arch);
    try{
      let nodeFile = readdirSync(prebuildsPath).find(f => f.endsWith(".node"));
      if(nodeFile) return join(prebuildsPath, nodeFile);
    }catch{}
  }
  return null;
}

// ML(): 从路径提取语言名称
// 子目录包 (tree-sitter-typescript/typescript) → basename = "typescript"
// 根目录包 (tree-sitter-python) → 去掉 "tree-sitter-" 前缀 = "python"
function ML(grammarDir){
  let base = basename(grammarDir);
  return base.startsWith("tree-sitter-") ? base.slice(11) : base;
}

// 修改后的调用
let libPath = MP(grammarDir), langName = ML(grammarDir);
o = libPath
  ? ["query", "--lib-path", libPath, "--lang-name", langName, queryFile, ...sourceFiles]
  : ["query", "-p", grammarDir, queryFile, ...sourceFiles]; // fallback
```

### 兼容性说明

| 平台 | 是否需要此修复 | 原因 |
|------|---------------|------|
| Windows | 需要 | 通常无 C 编译器，`-p --rebuild` 必然失败 |
| macOS | 通常不需要 | Xcode Command Line Tools 提供 clang |
| Linux | 通常不需要 | gcc/build-essential 常见 |

v12.1.5 捆绑 tree-sitter CLI 0.26.7 + 24 种语言的 grammar 包，其中 23 种有 `win32-x64` 预编译 `.node` 文件。仅 `@derekstride/tree-sitter-sql` 缺失（只有 `src/` C 源码）。

---

## 历史版本：v10.5.5 的问题

### Memory 工具 inputSchema 为空（已在 v12.1.5 修复）

v10.5.5 中 `search`/`timeline` 的 `inputSchema.properties` 为空 `{}`，Claude Code 的 MCP 客户端无法传递参数。v12.1.5 已内置正确的 properties 定义，无需手动修复。

### v10.5.5 Smart 工具记录修正

之前记录称"原始代码使用 `-p` 参数是正确的"、"tree-sitter 使用 DLL 缓存"。此结论基于较旧版本的 tree-sitter CLI 行为。在 v12.1.5 捆绑的 tree-sitter 0.26.7 中，`-p` 实际触发 `--rebuild`，缓存机制不适用于此场景。

### 关键文件位置

| 文件 | 路径 |
|------|------|
| MCP 服务器 (v12.1.5) | `~/.claude/plugins/cache/thedotmack/claude-mem/12.1.5/scripts/mcp-server.cjs` |
| tree-sitter CLI | 同上 `node_modules/tree-sitter-cli/tree-sitter.exe` (v0.26.7) |
| TS parser 预编译 | 同上 `node_modules/tree-sitter-typescript/prebuilds/win32-x64/tree-sitter-typescript.node` |
| Worker | 同上 `scripts/worker-service.cjs` (port 37777) |
| tree-sitter config | `%APPDATA%/tree-sitter/config.json` |

### 注意事项

- `claude plugins update` 会覆盖修复，需重新应用
- 文件加密软件（如 E-SafeNet）会阻止 Smart 工具解析文件，测试时使用 `%TEMP%` 目录
- 修改 `mcp-server.cjs` 后需重启 Claude Code 才能生效

### 参考链接

- [GitHub Issue #1247](https://github.com/nichochar/claude-mem/issues/1247) - Windows smart tools bugs

### 相关记录

### 验证记录
- [2026-03-12] 初次记录，v10.5.5 Memory 工具 inputSchema 修复
- [2026-03-12] v10.5.5 Smart 工具分析（部分结论已被 v12.1.5 修正）
- [2026-04-16] 升级至 v12.1.5，发现 MCP server 语法错误和 tree-sitter 不兼容
- [2026-04-17] 修复两个 Bug，全部 6 个工具通过 MCP server 直接测试验证通过

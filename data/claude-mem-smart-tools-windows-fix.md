# ClaudeMem MCP 工具修复记录

**标签**：#tools #windows #mcp #experience #bug
**来源**：实践总结 + 源码分析
**收录日期**：2026-03-12
**更新日期**：2026-03-12
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐⭐ (重新验证 + 源码分析)
**适用版本**：claude-mem 10.5.5 (Windows)

### 概要

ClaudeMem 插件的 MCP 工具在 Windows 上存在两类问题：Smart 工具解析失败和 Memory 工具参数传递失败。

### 内容

---

## 问题一：Memory 工具参数传递失败

### 问题描述

调用 `search` 和 `timeline` 工具时，报错：
```
Error: Either query or filters required
```

即使正确传递了参数，工具仍报告参数缺失。

### 根本原因

MCP 工具的 `inputSchema.properties` 为空 `{}`：
```javascript
// 原始代码（有问题）
inputSchema: { type: "object", properties: {}, additionalProperties: !0 }
```

虽然设置了 `additionalProperties: true`，但 **Claude Code 的 MCP 客户端不识别这种模式**，导致参数无法传递给工具。

### ✅ 修复方案

在 `mcp-server.cjs` 中为 `search` 和 `timeline` 工具添加正确的 `properties` 定义。

**修复位置**：`mcp-server.cjs` 第 137 行附近

**search 工具 properties**：
```javascript
properties: {
  query: { type: "string", description: "Search query string" },
  limit: { type: "number", description: "Maximum number of results" },
  project: { type: "string", description: "Project name to search in" },
  type: { type: "string", description: "Filter by observation type" },
  obs_type: { type: "string", description: "Filter by observation subtype" },
  dateStart: { type: "string", description: "Start date filter" },
  dateEnd: { type: "string", description: "End date filter" },
  offset: { type: "number", description: "Pagination offset" },
  orderBy: { type: "string", description: "Sort order" }
}
```

**timeline 工具 properties**：
```javascript
properties: {
  anchor: { type: "number", description: "Observation ID to center timeline around" },
  query: { type: "string", description: "Query to find anchor automatically" },
  depth_before: { type: "number", description: "Number of results before anchor" },
  depth_after: { type: "number", description: "Number of results after anchor" },
  project: { type: "string", description: "Project name" }
}
```

### 验证结果

```bash
# search 工具测试
mcp__plugin_claude-mem_mcp-search__search(query="tree-sitter", limit=5)
# ✅ 返回: Found 8 result(s) matching "tree-sitter"

# timeline 工具测试
mcp__plugin_claude-mem_mcp-search__timeline(query="MCP server", depth_before=2, depth_after=2)
# ✅ 返回: Timeline for query: "MCP server"
```

---

## 问题二：Smart 工具解析失败

### 问题描述

调用 smart_outline 等 Smart 工具时，返回：
```
Could not parse xxx. File may use an unsupported language or be empty.
```

#### ❌ 错误的修复方案（不要使用）

之前的记录建议用 `-l` 参数加载 `.node` 文件，这是**错误的**：
- `.node` 文件是 Node.js native addon（使用 N-API）
- tree-sitter CLI 的 `-l` 参数需要的是原生动态库（.dll/.so）
- 两者格式不兼容，CLI 无法加载 `.node` 文件

#### ✅ 正确的分析

1. **原始代码使用 `-p` 参数是正确的**
   ```javascript
   o=["query","-p",r,e,...t]
   ```

2. **tree-sitter CLI 的缓存机制**
   - tree-sitter CLI 会在首次使用时编译 grammar
   - 编译后的 DLL 缓存在 `%LOCALAPPDATA%\tree-sitter\lib\` 目录
   - 后续调用会自动使用缓存的 DLL，无需重复编译

3. **如果 Smart 工具不工作，检查以下几点**：
   - tree-sitter CLI 是否正确安装（检查 `node_modules/tree-sitter-cli/tree-sitter.exe`）
   - 缓存目录是否存在 DLL 文件
   - MCP 服务器是否需要重启以加载代码更改

### 关键文件位置

| 文件 | 路径 |
|------|------|
| MCP 服务器 | `C:\Users\admin\.claude\plugins\cache\thedotmack\claude-mem\10.5.5\scripts\mcp-server.cjs` |
| tree-sitter CLI | `node_modules/tree-sitter-cli/tree-sitter.exe` |
| **DLL 缓存** | `%LOCALAPPDATA%\tree-sitter\lib\*.dll` |

### 验证命令

```bash
# 检查 tree-sitter CLI 是否可用
"C:\Users\admin\.claude\plugins\cache\thedotmack\claude-mem\10.5.5\node_modules\tree-sitter-cli\tree-sitter.exe" --version

# 检查 DLL 缓存
ls "$LOCALAPPDATA/tree-sitter/lib/"

# 测试解析
"C:\...\tree-sitter.exe" parse -p "C:\...\node_modules\tree-sitter-javascript" "test.js"
```

### 注意事项

- **文件加密软件干扰**：如果系统有 E-SafeNet 等加密软件，新创建的文件可能被加密，导致解析失败。测试时请使用 `%TEMP%` 目录
- **MCP 服务器重启**：修改 `mcp-server.cjs` 后需要重启 MCP 服务器才能生效

### 验证记录

- [2026-03-12] 初次记录 Smart 工具修复，方案错误（`.node` 文件不能被 CLI 加载）
- [2026-03-12] 确认 Smart 工具原始 `-p` 参数方案正确，tree-sitter 使用 DLL 缓存
- [2026-03-12] 发现 Memory 工具 `search`/`timeline` 的 inputSchema.properties 为空导致参数无法传递
- [2026-03-12] 修复 `search`/`timeline` 工具的 properties 定义，验证通过
- [2026-03-12] **全部 8 个 MCP 工具验证通过**：search, timeline, smart_outline, smart_search, smart_unfold, get_observations, __IMPORTANT

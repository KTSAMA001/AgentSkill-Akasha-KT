# Unity 严格变体匹配下 Shader Graph Enum 关键字报"variant not found"

**标签**：#unity #shader #shader-variants #urp #experience #bug #vr
**来源**：实践排查 + Unity 官方论坛 + Unity Issue Tracker
**收录日期**：2026-03-18
**更新日期**：2026-03-18
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐（实践验证 + 官方帖子 + Issue Tracker 交叉验证）
**适用版本**：Unity 2022.1+（重点核对：2022.3.8f1 ~ 2022.3.39f1）

### 概要
在 Unity 2022.3.x（Meta Quest / Android / Vulkan）平台，开启 `PlayerSettings.strictShaderVariantMatching` 后，Shader Graph 中使用 `multi_compile_local` 的 Enum 关键字（如 `_DISPLAYMODE_NORMAL _DISPLAYMODE_SP1`）会持续报 `variant not found` 错误。画面显示正常，但控制台不断刷错。关闭严格匹配后错误消失。  
本记录已按官方帖子与 Issue Tracker 对齐到版本维度：**“strict 下报 variant not found”是一个问题族，不同版本修复的是不同子问题。你在 2022.3.39f1 遇到的这类，并不被已修复的 Deferred 子问题覆盖。**

### 内容

#### 问题现象

```
Shader Graphs/<业务Shader>, subshader 0, pass 0, stage all: variant FOG_EXP2 STEREO_MULTIVIEW_ON not found
```

- 画面完全正常，但控制台持续刷错
- 仅在 `strictShaderVariantMatching = true` 时出现
- 关闭严格匹配后不再报错，画面无任何变化

#### 根因分析

Shader Graph 的 Enum 关键字生成的 pragma 为：

```hlsl
#pragma multi_compile_local _DISPLAYMODE_NORMAL _DISPLAYMODE_SP1
```

该声明**没有 `_` 空白占位符**，意味着不存在"全关"变体（即没有任何 `_DISPLAYMODE_*` 被启用时的变体）。

Unity 员工在官方帖说明 strict 模式查找逻辑为：取材质关键词与全局关键词（引擎也可能额外开启一些），做 OR 后按 pass mask 查找目标变体。  
当关键词组缺少 `_` 空白入口时，会出现“请求到了全关组合，但该组合并不存在”的情况，最终触发 `variant not found`。

#### 版本差异与问题分型（关键）

| 分型 | 典型报错 | 官方 ID / 结论 | 影响版本（公开信息） | 与本记录关系 |
|------|----------|----------------|----------------------|--------------|
| A. URP Deferred 内部 shader 在 strict 下报错 | `Hidden/Universal Render Pipeline/StencilDeferred ... variant ... not found` | `UUM-58537`，**Fixed** | Found: `2022.3.15f1`；Fixed: `2022.3.19f1` | **不同问题**，已在较早 2022.3 补丁修复 |
| B. Dynamic Branches 与 strict 兼容问题 | 开启 strict + dynamic branch 时 magenta / 变体失败 | `UUM-34873`，**Fixed** | Found: `2022.2.18f1`；Fixed in `2022.3.X` | **不同问题**，是 dynamic branch 路径 |
| C. Standard Shader 在 strict 下报 `<no keywords>` 变体缺失 | `Shader Standard ... variant not found` | `UUM-47817`，**Won't Fix** | Found: `2022.3.8f1` 等 | 与本问题同属“strict 下请求组合与变体产物不一致”问题族 |
| D. `multi_compile(_local)` 组无 `_` 入口导致组合不存在 | strict 下持续报缺失，关闭 strict 后画面正常 | 论坛答复 + `IN-53232`（社区反馈 Won't Fix） | 在 2022.3 线上持续可见 | **本记录核心问题** |

#### 覆盖到 Unity 2022.3.39f1 的结论

- `2022.3.39f1` 晚于 `2022.3.19f1`，因此 **A 类（UUM-58537）修复已包含**。
- 你当前报错模式属于 **D 类**（关键词组无 `_` 空白入口 + strict 精确匹配），与 A 类不是同一根因。
- 因此“某些 strict 问题在早版本已修复”与“你在 2022.3.39f1 仍报此错”并不冲突。

#### 两种模式下的行为

| 模式 | 行为 | 结果 |
|------|------|------|
| `strictShaderVariantMatching = false`（默认） | 模糊匹配，静默 fallback 到最接近的变体（第一个关键字 `_DISPLAYMODE_NORMAL`） | 画面正常，无报错 |
| `strictShaderVariantMatching = true` | 精确匹配失败，报 variant not found | 画面仍正常（fallback 机制依然工作），但持续刷错 |

#### 为什么画面一直正常

Unity 的模糊匹配机制对 `multi_compile` 组内"全关"的情况，会自动 fallback 到**该组第一个关键字对应的变体**。这个行为在严格匹配模式下同样生效（报错后仍使用 fallback 结果渲染）。

#### Unity 官方态度

- Unity 员工 `aleksandrk`：  
  - “这通常意味着该变体根本不存在；检查是否有 directive 没有 `_` 入口。”  
  - strict 下查找基于“材质关键词 + 全局关键词（含引擎启用关键词）”。
- 论坛里“在更早版本已修复”的引用，指向的是 **UUM-58537（Deferred 内部 shader）**，不是对所有 strict 报错类型的总修复。
- Unity 员工后续也明确：closest variant 选择规则不保证稳定、可能变化；理想上应使用 strict 来暴露配置问题。

#### 对 854664/33 的解读（避免误读）

- 33 楼里的 “It could be.” 是对“是否可能是 bug 且已修复”的泛化回答，不是“你当前所有报错类型都已修复”的结论。
- 同楼层核心信息其实是 strict 的查找逻辑说明（关键词 OR + pass mask）。
- 是否“已修”必须回到具体 Issue ID 判断；不同 ID 覆盖不同路径。

#### 容易混淆的排查方向（已排除）

| 方向 | 为什么不是 |
|------|-----------|
| 材质 `m_ValidKeywords` 丢失 | 编辑器下完全正确，非材质数据问题 |
| AB 构建序列化丢关键词 | 删 Library + 全量重建无效 |
| SVC 变体收集遗漏 | SVC 收集结果正确 |
| 运行时脚本清除关键词 | 无相关脚本逻辑 |
| Shader 替换流程 | 不涉及 |

### 解决方案

**方案 A（推荐）：关闭严格变体匹配**

`PlayerSettings.strictShaderVariantMatching = false`

这是 Unity 的默认设置。画面一直正常，关闭后只是不再暴露这个"引擎内部请求全关变体"的行为。

**方案 B：Shader 层面加 `_` 空白入口**

将 pragma 从：
```hlsl
#pragma multi_compile_local _DISPLAYMODE_NORMAL _DISPLAYMODE_SP1
```
改为：
```hlsl
#pragma multi_compile_local _ _DISPLAYMODE_NORMAL _DISPLAYMODE_SP1
```

但 Shader Graph 的 Enum 类型**不直接支持**添加 `_` 入口，需要通过以下方式之一：
- 使用 `IPreprocessShaders` 回调注入
- 直接修改 Shader Graph 生成的 HLSL 代码
- 改用手写 Shader 替代 Shader Graph

注意：此方案会多编译一组"全关"变体，增加变体总量。

### 参考链接

- [Unity 官方论坛 - Strict shader variant matching](https://discussions.unity.com/t/strict-shader-variant-matching/854664) - Unity 员工发布的功能说明与社区讨论
- [官方帖 #10（无 `_` 入口会导致变体不存在）](https://discussions.unity.com/t/strict-shader-variant-matching/854664/10)
- [官方帖 #33（strict 查找逻辑说明）](https://discussions.unity.com/t/strict-shader-variant-matching/854664/33)
- [官方帖 #37（用户引用 2022.3.19f1 修复）](https://discussions.unity.com/t/strict-shader-variant-matching/854664/37)
- [官方帖 #39（closest 规则不保证稳定）](https://discussions.unity.com/t/strict-shader-variant-matching/854664/39)
- [Unity Issue Tracker - UUM-58537（Deferred strict 报错，已修复）](https://issuetracker.unity3d.com/issues/sahder-errors-in-player-when-strict-shader-variant-matching-is-enabled-and-the-rendering-path-is-set-to-deferred)
- [Unity Issue Tracker - UUM-34873（Dynamic Branches + strict，已修复）](https://issuetracker.unity3d.com/issues/dynamic-branches-do-not-work-with-strict-variant-matching)
- [Unity Issue Tracker - UUM-47817（Standard strict 报错，Won't Fix）](https://issuetracker.unity3d.com/issues/shader-standard-errors-in-player-when-strict-shader-variant-matching-is-enabled)
- [Unity 文档 - PlayerSettings.strictShaderVariantMatching](https://docs.unity3d.com/2022.3/Documentation/ScriptReference/PlayerSettings-strictShaderVariantMatching.html) - API 说明
- [Unity 文档 - Using shader keywords with C# scripts](https://docs.unity3d.com/2022.3/Documentation/Manual/shader-keywords-scripts.html) - 关键词管理与运行时行为说明

### 相关记录

- [Shader 变体编译知识](./shader-variants-compile.md) - Shader 变体的基础编译机制
- [VR 变体收集器架构](./vr-variant-collector-architecture.md) - 变体收集流程
- [Unity Shader 变体工具](./unity-shader-variants-tool.md) - 变体管理工具

### 验证记录
- [2026-03-18] 初次记录。在某 VR 项目（Unity 2022.3.39f1 / Android(Vulkan)）中完整排查确认。关闭 `strictShaderVariantMatching` 后错误消失，画面无变化。联网查阅 Unity 官方论坛确认为引擎已知行为（Won't Fix）。
- [2026-03-18] 增补版本分型调查：核对 `UUM-58537`（Fixed in 2022.3.19f1）、`UUM-34873`（Fixed in 2022.3.X）、`UUM-47817`（Won't Fix），并对齐官方帖 #33/#37 语境，明确 2022.3.39f1 仍可能命中“无 `_` 入口”问题族。

---

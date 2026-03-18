# Unity 严格变体匹配下 Shader Graph Enum 关键字报"variant not found"

**标签**：#unity #shader #shader-variants #urp #experience #bug #vr
**来源**：实践排查 + Unity 官方论坛 + Unity Issue Tracker
**收录日期**：2026-03-18
**更新日期**：2026-03-18
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐（实践验证 + 官方员工确认）
**适用版本**：Unity 2022.1+（strictShaderVariantMatching 引入版本起）

### 概要

在 Unity 2022.3.x（Meta Quest / Android / Vulkan）平台，开启 `PlayerSettings.strictShaderVariantMatching` 后，Shader Graph 中使用 `multi_compile_local` 的 Enum 关键字（如 `_DISPLAYMODE_NORMAL _DISPLAYMODE_SP1`）会持续报 `variant not found` 错误。画面显示完全正常，但控制台不断刷错。关闭严格匹配后错误消失。**根因是 Enum 关键字没有 `_` 空白入口，而 Unity 引擎内部会请求"全关"变体。**

### 内容

#### 问题现象

```
Shader Graphs/Ljdl_Role_01, subshader 0, pass 0, stage all: variant FOG_EXP2 STEREO_MULTIVIEW_ON not found
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

Unity 引擎内部在某些渲染路径（初始化、shader 预加载、特定 pass 首次编译等）中，会用**不携带材质 local keyword** 的状态去查找变体。此时请求的变体组合为 `FOG_EXP2 STEREO_MULTIVIEW_ON`（仅全局关键字），但这个组合在编译产物中不存在。

#### 两种模式下的行为

| 模式 | 行为 | 结果 |
|------|------|------|
| `strictShaderVariantMatching = false`（默认） | 模糊匹配，静默 fallback 到最接近的变体（第一个关键字 `_DISPLAYMODE_NORMAL`） | 画面正常，无报错 |
| `strictShaderVariantMatching = true` | 精确匹配失败，报 variant not found | 画面仍正常（fallback 机制依然工作），但持续刷错 |

#### 为什么画面一直正常

Unity 的模糊匹配机制对 `multi_compile` 组内"全关"的情况，会自动 fallback 到**该组第一个关键字对应的变体**。这个行为在严格匹配模式下同样生效（报错后仍使用 fallback 结果渲染）。

#### Unity 官方态度

- Unity 员工 `aleksandrk` 在官方论坛确认：**"This often means the variant doesn't exist at all. Are there any directives that don't have an underscore? These need one of the keywords to be enabled."**
- 社区用户用最简场景（新项目 + 默认 Cube + Standard Shader）复现了同类问题，提交 Bug（IN-53232），Unity 关为 **Won't Fix**
- Unity 官方立场：该功能设计为诊断工具，URP/HDRP 下"应该"正常工作，但对没有 `_` 入口的 keyword set 确实会产生此类报错

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
- [Unity Issue Tracker - Dynamic Branches do not work with Strict Variant Matching](https://issuetracker.unity3d.com/issues/dynamic-branches-do-not-work-with-strict-variant-matching) - 相关已修复 Bug
- [Unity 文档 - PlayerSettings.strictShaderVariantMatching](https://docs.unity3d.com/2022.3/Documentation/ScriptReference/PlayerSettings-strictShaderVariantMatching.html) - API 说明
- [Unity 文档 - Using shader keywords with C# scripts](https://docs.unity3d.com/2022.3/Documentation/Manual/shader-keywords-scripts.html) - 关键词管理与运行时行为说明

### 相关记录

- [Shader 变体编译知识](./shader-variants-compile.md) - Shader 变体的基础编译机制
- [VR 变体收集器架构](./vr-variant-collector-architecture.md) - 变体收集流程
- [Unity Shader 变体工具](./unity-shader-variants-tool.md) - 变体管理工具

### 验证记录

- [2026-03-18] 初次记录。在 dlxb_vr 项目（Unity 2022.3.39f1 / Meta Quest / Vulkan）中完整排查确认。关闭 `strictShaderVariantMatching` 后错误消失，画面无变化。联网查阅 Unity 官方论坛确认为引擎已知行为（Won't Fix）。

---

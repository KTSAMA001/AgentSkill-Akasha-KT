# URP RenderFeature 使用 LightMode 筛选额外 Pass 的机制

**标签**：#unity #shader #graphics #urp #srp #renderer-feature #npr #knowledge
**来源**：本次 URP RendererFeature 描边机制调研；Unity 官方文档；URP 14.0.12 包源码核对
**收录日期**：2026-07-07
**来源日期**：2026-07-07
**更新日期**：2026-07-07
**状态**：📘 有效
**可信度**：⭐⭐⭐⭐ (官方文档与 URP 源码核对；具体项目 Shader 仍需 Editor/Frame Debugger 回归)
**适用版本**：Unity 2022.3+ / URP 14+；Render Objects Renderer Feature；ScriptableRenderContext.DrawRenderers

### 概要

URP 的 Render Objects / 自定义 RendererFeature 在批量绘制对象时，`ShaderTagId` / `Pass Names` 匹配的是 ShaderLab Pass 的 `LightMode` tag value，而不是 `Pass { Name "..." }`。因此，额外描边 Pass 的推荐协议是给 Pass 写自定义 `LightMode`，再由 RenderFeature 在合适的渲染时机额外绘制它；如果使用 `overrideMaterial`，原 ShaderTag 只是在筛选“哪些原材质有资格被重画”。

### 内容

#### 1. `ShaderTagId` 匹配的不是 Pass Name

在 URP/SRP 的 `DrawRenderers` 路径里，`DrawingSettings` 接收的 `ShaderTagId` 表面 API 名称容易让人误会，但它实际用于匹配 Shader Pass 的 `LightMode` tag value：

```shaderlab
Pass
{
    Name "RoleOutline"                 // 不是 DrawRenderers 的批量筛选目标
    Tags { "LightMode" = "RoleOutline" } // 这是 ShaderTagId/Pass Names 会匹配的值
}
```

`Pass { Name "..." }` 更适合这些用途：

- `UsePass` 引用某个命名 Pass。
- `Material.FindPass("Name")` 或 pass index 定位。
- Frame Debugger / ShaderLab 可读性与调试标识。

它不是 URP Render Objects Inspector 的 `Pass Names` 字段，也不是 `context.DrawRenderers` 这类批量绘制路径的过滤字段。批量筛选应使用 `Tags { "LightMode" = "..." }`。

#### 2. Render Objects 的 Pass Names 本质是 LightMode 列表

URP 内置 Render Objects Renderer Feature 会把 Inspector 里的 `Pass Names` 转为一组 `ShaderTagId`，再交给 `DrawingSettings`。Unity 官方文档也把这个字段描述为匹配 shader pass 的 `LightMode` Pass Tag。

URP Forward Renderer 默认主绘制通常会识别一组内置 LightMode，例如：

- `SRPDefaultUnlit`
- `UniversalForward`
- `UniversalForwardOnly`

自定义 `LightMode`，例如 `RoleOutline`、`HairShadowDepth`、`CharacterMask`，不会自动被 URP 默认主绘制消耗；它们需要由 Render Objects 或自定义 RendererFeature 在指定 `RenderPassEvent` 主动绘制。

`SRPDefaultUnlit` 有一个额外注意点：未写 `LightMode` 的 Pass 会默认落到这个值。它可以被用来画额外 Pass，但也可能被默认不透明绘制路径捞到，导致语义不清。工程上更推荐为 Feature 专用 Pass 写明确的自定义 `LightMode`。

#### 3. 描边场景里的两种合法模型

第一种是统一材质重画模型：

- 角色本体由 URP 默认管线绘制。
- RendererFeature 再按 Layer、Rendering Layer、Render Queue 等对象条件筛选一批 Renderer。
- `DrawingSettings.overrideMaterial` 指向一个独立描边材质。
- `ShaderTagId` 只是确保原材质存在某个可匹配 Pass，让对象能进入这次 `DrawRenderers`。

这种模式适合交互高亮、选中描边、统一外轮廓等效果。它的缺点是原角色 Shader 内没有描边上下文，描边参数、Mask、平滑法线约定和材质属性往往要另行管理。此时把 `shaderTags` 当作“哪些 shader 支持描边”的白名单可以工作，但语义上比较绕。

第二种是角色 Shader 自带额外 Pass 模型：

- 主体 Pass 使用 `LightMode = UniversalForwardOnly` 或 `UniversalForward`，交给 URP 默认主绘制。
- 描边 Pass 使用自定义 `LightMode = RoleOutline`。
- Render Objects / 自定义 RendererFeature 的 `Pass Names` 填 `RoleOutline`。
- 不使用 `overrideMaterial`，直接绘制原 Shader 的描边 Pass。

这种模型更适合角色材质本身就需要决定描边宽度、颜色、Mask、法线通道、深度偏移等规则的场景。它也更接近“URP 下用 RendererFeature 恢复多 Pass 绘制”的本来用途。

#### 4. 同样的 Shader 计算，默认管线绘制和 RenderFeature 绘制仍可能不同

即使两个 Pass 里复用了同一段 HLSL 光照计算，只要绘制入口不同，最终结果仍可能受以下因素影响：

- 绘制时机不同：例如 `BeforeRenderingOpaques`、`AfterRenderingOpaques`、`AfterRenderingSkybox` 会看到不同的深度、颜色和中间纹理状态。
- Render State 不同：`ZWrite`、`ZTest`、`Cull`、`Blend`、`Stencil`、ColorMask 等状态决定片元是否可见以及如何合成。
- 过滤条件不同：Layer、Rendering Layer、Render Queue、Sorting Criteria、camera type 过滤都会改变被绘制对象集合。
- Override 不同：使用 `overrideMaterial` 后，实际运行的是 override 材质的 shader/pass，不再是原角色 shader 的对应 pass。
- 目标不同：自定义 Pass 可能写入相机颜色、深度、临时 RT、mask RT 或 stencil，而不是默认相机目标。

所以“同样的 shader 计算”只保证局部代码一致，不保证渲染结果必然一致。判断时要同时看 Pass Tag、Render State、RenderPassEvent、RenderTarget 与 FilteringSettings。

#### 5. 推荐配置

用内置 Render Objects 激活角色 Shader 中的额外描边 Pass 时，可以按下面配置：

```text
Event: AfterRenderingOpaques
Queue: Opaque
Layer Mask: 角色所在 Layer
Pass Names: RoleOutline
Override Mode: None
Depth/Stencil: 按描边 Pass 自己的状态决定
```

对应 Shader 结构：

```shaderlab
Pass
{
    Name "UniversalForwardOnly"
    Tags { "LightMode" = "UniversalForwardOnly" }
    // 主体渲染
}

Pass
{
    Name "RoleOutline"
    Tags { "LightMode" = "RoleOutline" }
    Cull Front
    ZWrite Off
    ZTest LEqual
    // 反面外扩描边
}
```

如果写自定义 RendererFeature，核心代码形态是：

```csharp
var shaderTags = new List<ShaderTagId>
{
    new ShaderTagId("RoleOutline")
};

var drawingSettings = RenderingUtils.CreateDrawingSettings(
    shaderTags,
    ref renderingData,
    SortingCriteria.CommonOpaque);

context.DrawRenderers(
    renderingData.cullResults,
    ref drawingSettings,
    ref filteringSettings);
```

### 关键代码

RenderFeature 选额外 Pass 的关键不是 Pass Name，而是 `LightMode`：

```shaderlab
Pass
{
    Name "MyPassName"
    Tags { "LightMode" = "MyFeaturePass" }
}
```

```csharp
new ShaderTagId("MyFeaturePass")
```

### 参考链接

- [Unity Manual - Render Objects Renderer Feature](https://docs.unity3d.com/Manual/urp/renderer-features/renderer-feature-render-objects.html) - 官方说明 Render Objects 的过滤、Pass Names 与 Override Material。
- [Unity Manual - ShaderLab Pass tags in URP](https://docs.unity3d.com/Manual/urp/urp-shaders/urp-shaderlab-pass-tags.html) - 官方说明 `LightMode` Pass Tag 如何被 URP 识别。
- [Unity Manual - Custom render pass workflow in URP](https://docs.unity3d.com/Manual/urp/renderer-features/custom-rendering-pass-workflow-in-urp.html) - 官方说明自定义 RendererFeature / RenderPass 如何注入 URP 渲染流程。
- [Unity Scripting API - ScriptableRenderContext.DrawRenderers](https://docs.unity3d.com/ScriptReference/Rendering.ScriptableRenderContext.DrawRenderers.html) - API 示例使用 `LightMode` Pass Tag value 选择几何绘制。
- [Cyanilux - Custom Renderer Features](https://www.cyanilux.com/tutorials/custom-renderer-features/) - 社区实践中也按 Queue、LayerMask 与 Shader Pass `LightMode` tags 筛选对象。

### 相关记录

- [URP Renderer Feature 开发要点](./urp-renderer-feature-guide.md) - RendererFeature 基础与多 Pass 迁移背景。
- [Unity URP 多方案描边方案对比](./unity-urp-outline-scheme.md) - 描边方案选型，可与本文的 LightMode Pass 机制结合。
- [URP 屏幕空间刘海阴影 RenderFeature](./urp-renderfeature-screen-space-hair-shadow.md) - 已使用 `ShaderTagId` 匹配 Pass `LightMode` 的相邻实践。
- [URP 反面外扩描边的裁剪空间等宽改造经验](./urp-backface-outline-equal-width.md) - 描边 Pass 内部顶点外拓算法的相邻记录。
- [URP 核心 Renderer / Pass / Feature 架构](./urp-core-renderer-pass-feature-architecture.md) - 理解 Renderer、Pass、Feature 分工的背景记录。

### 验证记录

- [2026-07-07] 初次记录。已执行阿卡西 `git pull origin main`，完成 data 目录重复检测；确认已有记录覆盖 URP RendererFeature、描边方案和 ShaderTagId 相邻经验，但没有单独记录 `LightMode` 与 `Pass Name` 的筛选边界。
- [2026-07-07] 官方核对：Unity Render Objects、URP ShaderLab Pass Tags、Custom Render Pass Workflow 与 DrawRenderers API 文档均指向 `LightMode` Pass Tag value 作为 SRP/URP 绘制选择依据。
- [2026-07-07] 源码核对：URP 14.0.12 的默认 Forward DrawObjectsPass 使用 `SRPDefaultUnlit`、`UniversalForward`、`UniversalForwardOnly`；RenderObjectsPass 会把配置的 Pass Names 转成 `ShaderTagId` 列表后创建 DrawingSettings。
- [2026-07-07] 脱敏审查：本记录只保留通用 URP/Shader 机制和匿名化配置示例；未写入具体项目名、本机绝对路径、内部资源名或未公开业务上下文。项目内新增示例 Shader 仅做源码静态检查，尚未完成 Unity Editor 导入编译、Render Objects Inspector 配置验证或 Frame Debugger 逐帧确认。

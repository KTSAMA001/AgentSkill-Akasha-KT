# URP 屏幕空间刘海阴影 RenderFeature

**标签**：#shader #unity #experience #urp #npr #renderer-feature #post-processing
**来源**：Unity_URP_Learning
**来源日期**：2024-08-08
**收录日期**：2026-02-07
**更新日期**：2026-06-13
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐ (代码验证)
**适用版本**：Unity 2022.3+ / URP 14.0+

### 概要

屏幕空间刘海阴影通过 URP RenderFeature 将脸部与头发深度信息写入自定义 RT，再由脸部 Shader 采样以形成风格化投影。

### 内容

在 NPR 卡通渲染中，需要实现屏幕空间的刘海在脸上的投影效果（Screen Space Hair Shadow），利用 RenderFeature 将头发的深度信息投射到脸部区域。

#### 整体思路

利用自定义 RenderFeature 在渲染不透明物体之前：

1. 先将脸部模型的深度写入自定义 RT（`_HairSoildColor`）。
2. 再将头发模型的深度/颜色叠加写入同一 RT。
3. 后续渲染阶段中，脸部 Shader 采样此 RT 实现阴影效果。

#### 多 Layer + 多 Pass 分离

```csharp
// 脸部和头发使用不同 Layer
public LayerMask faceLayer;
public LayerMask hairLayer;

// 三次绘制：
// 1. 脸部深度（Pass 0, DepthOnly ShaderTag）
context.DrawRenderers(cullResults, ref draw1, ref faceFiltering);

// 2. 头发深度（Pass 0, UniversalForward ShaderTag）
context.DrawRenderers(cullResults, ref draw2, ref hairFiltering);

// 3. 头发简单颜色（Pass 1）— 用于阴影投射
context.DrawRenderers(cullResults, ref draw3, ref hairFiltering);
```

#### 配套 Shader (SSHS.shader)

三个 Pass 分别处理不同功能：

- **FaceDepthOnly**：仅写深度 (`ColorMask 0, ZWrite On`)。
- **HairSimpleColor**：输出头发深度到颜色 (`return float4(1, depth, 0, 1)`)。
- **DepthMaskColor**：输出纯色遮罩 (`return float4(1, 0, 0, 1)`)。

#### 关键踩坑点

- 注意 `ConfigureTarget` + `ConfigureClear` 在 `OnCameraSetup` 中设置。
- 临时 RT 需在 `OnCameraCleanup` 中释放。
- 使用 `ShaderTagId` 匹配 Pass 的 `LightMode` 标签。

### 参考链接

- [Unity_URP_Learning/RenderFeature](https://github.com/KTSAMA001/Unity_URP_Learning/tree/main/Assets/Products/RenderFeature) - 完整源码。

### 相关记录

- [URP 屏幕空间描边 RenderFeature 实现](./urp-renderfeature-screen-space-outline.md) - 类似的 RenderFeature 模式。

### 验证记录

- [2026-02-07] 从 Unity_URP_Learning 仓库整合。
- [2026-06-13] 结构维护：从旧聚合记录拆分，未重新验证原技术结论。

# URP 中 GrabPass 替代方案 (GrabColor RenderFeature) {#grab-color-renderfeature}

**收录日期**：2026-02-07
**来源日期**：2024-08-08
**标签**：#shader #unity #experience #urp #srp-batcher #renderer-feature
**来源**：Unity_URP_Learning
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐ (代码验证)
**适用版本**：Unity 2022.3+ / URP 14.0+

**问题/场景**：

URP 不支持内置管线的 `GrabPass`，需要在后续 Shader 中读取当前帧的屏幕颜色（如折射、扭曲、描边等效果），需要找到替代方案。

**解决方案/结论**：

### 1. 使用 RenderFeature 抓取颜色缓冲

创建 `GrabColorRenderPassFeature`，在合适时机将相机颜色缓冲 Blit 到全局纹理 `_KTGrabTex`。

### 2. 核心代码

```csharp
public override void OnCameraSetup(CommandBuffer cmd, ref RenderingData renderingData)
{
    RenderTextureDescriptor desc = renderingData.cameraData.cameraTargetDescriptor;
    desc.depthBufferBits = 0;  // 不需要深度
    RenderingUtils.ReAllocateIfNeeded(ref _grabRT, desc);
    cmd.SetGlobalTexture("_KTGrabTex", _grabRT.nameID);
}

public override void Execute(...)
{
    Blitter.BlitCameraTexture(cmd, cameraColorTarget, _grabRT);
}
```

### 3. Scene View 兼容

需要为 Game View 和 Scene View 分别维护独立的 RTHandle，防止互相干扰：

```csharp
#if UNITY_EDITOR
if (SceneView.currentDrawingSceneView)
    Blitter.BlitCameraTexture(cmd, scene_cameraColorTag, _grabRT_SceneView);
else
    Blitter.BlitCameraTexture(cmd, cameraColorTag, _grabRT_GameView);
#else
    Blitter.BlitCameraTexture(cmd, cameraColorTag, _grabRT_GameView);
#endif
```

### 4. 在 Shader 中使用

```hlsl
TEXTURE2D(_KTGrabTex);
SAMPLER(sampler_KTGrabTex);

half4 frag(Varyings i) : SV_Target
{
    float4 screenColor = SAMPLE_TEXTURE2D(_KTGrabTex, sampler_KTGrabTex, i.texcoord);
    // ... 使用屏幕颜色进行后续处理
}
```

### 5. 关键踩坑点

- 抓取的 RT 的 `depthBufferBits` 设为 0，仅需颜色数据
- `SetupRenderPasses` 中获取 `renderer.cameraColorTargetHandle`
- 必须在 `Dispose` 中释放 RTHandle
- `renderPassEvent` 应在 `AfterRenderingSkybox` / `AfterRenderingOpaques`

**参考链接**：

- [Unity_URP_Learning/RenderFeature](https://github.com/KTSAMA001/Unity_URP_Learning/tree/main/Assets/Products/RenderFeature) - 完整源码

**验证记录**：

- [2026-02-07] 从 Unity_URP_Learning 仓库整合

**相关经验**：

- [屏幕空间描边 SSOutLine RenderFeature](./npr-rendering-outline.md#ss-outline-renderfeature) — 依赖此 GrabColor 功能

# URP ForwardRenderer Setup 流程

**标签**：#unity #graphics #knowledge #urp #srp #rendering-pipeline
**来源**：TaTa 仓库 - URP-analysis/urp-analysis.md
**收录日期**：2026-01-31
**来源日期**：2020-11-05
**更新日期**：2026-06-13
**状态**：📘 有效
**可信度**：⭐⭐⭐⭐ (源码分析 + 实践验证)
**适用版本**：URP 源码分析记录对应版本（原记录未注明精确包版本）

### 概要

`ForwardRenderer` 初始化内置 Pass 与渲染目标，并在 `Setup()` 中判断阴影、深度、后处理和 RendererFeature 等条件，再按顺序 `EnqueuePass` 形成相机渲染队列。

### 内容

#### ForwardRenderer 初始化

ForwardRenderer 继承自 ScriptableRenderer，初始化时创建各种 Pass：

```csharp
public ForwardRenderer(ForwardRendererData data) : base(data)
{
    // 内置材质
    Material blitMaterial = CoreUtils.CreateEngineMaterial(data.shaders.blitPS);
    Material copyDepthMaterial = CoreUtils.CreateEngineMaterial(data.shaders.copyDepthPS);
    Material screenspaceShadowsMaterial = CoreUtils.CreateEngineMaterial(data.shaders.screenSpaceShadowPS);

    // 初始化各种 Pass
    m_MainLightShadowCasterPass = new MainLightShadowCasterPass(RenderPassEvent.BeforeRenderingShadows);
    m_AdditionalLightsShadowCasterPass = new AdditionalLightsShadowCasterPass(RenderPassEvent.BeforeRenderingShadows);
    m_DepthPrepass = new DepthOnlyPass(RenderPassEvent.BeforeRenderingPrepasses, ...);
    m_RenderOpaqueForwardPass = new DrawObjectsPass("Render Opaques", ...);
    m_DrawSkyboxPass = new DrawSkyboxPass(RenderPassEvent.BeforeRenderingSkybox);
    m_RenderTransparentForwardPass = new DrawObjectsPass("Render Transparents", ...);
    m_PostProcessPass = new PostProcessPass(RenderPassEvent.BeforeRenderingPostProcessing, ...);
    m_FinalBlitPass = new FinalBlitPass(RenderPassEvent.AfterRendering, blitMaterial);

    // RenderTexture
    m_CameraColorAttachment.Init("_CameraColorTexture");
    m_CameraDepthAttachment.Init("_CameraDepthAttachment");
    m_DepthTexture.Init("_CameraDepthTexture");
}
```

#### 默认渲染顺序

URP 默认渲染逻辑与 Built-in 管线相近：

1. ShadowMap Pass：绘制阴影贴图。
2. Opaque Pass：绘制不透明物体。
3. Skybox Pass：绘制天空盒。
4. Transparent Pass：绘制透明物体。
5. PostProcess Pass：后处理。

#### URP vs Built-in 的核心区别

| 特性 | Built-in | URP |
|------|----------|-----|
| 渲染流程 | 封装，难以修改 | 完全暴露，可定制 |
| Shadow Pass | 固定 | 可自定义 shader |
| RenderTexture 格式 | 固定 | 可自定义通道含义 |
| 扩展性 | 有限 | Renderer Feature 插件系统 |

#### ForwardRenderer.Setup() 流程

```csharp
public override void Setup(ScriptableRenderContext context, ref RenderingData renderingData)
{
    // 1. 判断是否需要各种 Pass
    bool mainLightShadows = m_MainLightShadowCasterPass.Setup(ref renderingData);
    bool requiresDepthPrepass = cameraData.requiresDepthTexture && !CanCopyDepth(...);
    bool postProcessEnabled = cameraData.postProcessEnabled;

    // 2. 创建 RenderTarget
    if (intermediateRenderTexture)
        CreateCameraRenderTarget(context, ref cameraData);

    // 3. 添加 RendererFeature 的 Pass
    for (int i = 0; i < rendererFeatures.Count; ++i)
        rendererFeatures[i].AddRenderPasses(this, ref renderingData);

    // 4. 按顺序 EnqueuePass
    if (mainLightShadows) EnqueuePass(m_MainLightShadowCasterPass);
    if (requiresDepthPrepass) EnqueuePass(m_DepthPrepass);
    if (postProcessEnabled) EnqueuePass(m_ColorGradingLutPass);

    EnqueuePass(m_RenderOpaqueForwardPass);
    EnqueuePass(m_DrawSkyboxPass);
    EnqueuePass(m_RenderTransparentForwardPass);

    if (postProcessEnabled) EnqueuePass(m_PostProcessPass);
    EnqueuePass(m_FinalBlitPass);
}
```

### 关键代码

见“内容”中的 `ForwardRenderer` 初始化与 `ForwardRenderer.Setup()` 片段。

### 相关记录

- [URP 渲染入口与 RenderSingleCamera 流程](./urp-render-entry-render-single-camera-flow.md) - 相机渲染入口如何调用 Renderer。
- [URP Renderer Feature 扩展点要点](./urp-renderer-feature-extension-points.md) - 自定义 Pass 注入 `Setup()` 阶段的实践要点。
- [CommandBuffer 在 URP 中的角色](./urp-commandbuffer-role-in-urp.md) - Pass 执行中的命令录制与提交。

### 验证记录

- [2026-04-15] 结构修复：补齐模板必填章节，未改动原结论。
- [2026-06-13] 结构维护：从旧聚合记录拆分，未重新验证原技术结论。

---

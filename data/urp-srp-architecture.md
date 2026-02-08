# URP / SRP 知识
本文档记录 Unity SRP/URP 的核心概念与常用扩展点，偏"原理 + 工程要点"。

---

## SRP（Scriptable Render Pipeline）是什么

**标签**：#unity #graphics #knowledge #urp #srp
**来源**：Unity 官方文档 - Scriptable Render Pipeline
**收录日期**：2026-01-30
**来源日期**：-
**状态**：📘 有效
**可信度**：⭐⭐⭐⭐⭐ (官方文档)

- SRP 是 Unity 的可编程渲染管线体系：用 C# 组织"何时画什么、用哪些 render states/targets、执行顺序"。
- 与内置管线相比，SRP 更强调"可定制的 render loop"和更明确的渲染阶段划分。

---

## URP 的核心结构（工程视角）

**标签**：#unity #graphics #knowledge #urp #srp
**来源**：Unity 官方文档 - Universal Render Pipeline、URP 源码分析
**来源日期**：-
**收录日期**：2026-01-30
**状态**：📘 有效
**可信度**：⭐⭐⭐⭐⭐ (官方文档 + 源码验证)

常见理解方式：

- `ScriptableRenderer`：一次 Camera 渲染的"调度者/编排者"，决定 Pass 的队列与执行。
- `ScriptableRenderPass`：真正执行渲染工作的单元（绘制、Blit、设置 RT、清屏等）。
- `ScriptableRendererFeature`：把自定义 Pass 注入到 Renderer 的扩展点（更像插件入口）。

---

## URP 源码分析 - 入口与渲染流程

**标签**：#unity #graphics #knowledge #urp #srp
**来源**：TaTa 仓库 - URP-analysis/urp-analysis.md
**来源日期**：2020-11-05
**状态**：📘 有效
**收录日期**：2026-01-31
**可信度**：⭐⭐⭐⭐ (源码分析 + 实践验证)

### 入口文件

URP 入口文件：`UniversalRenderPipelineAsset.cs`

核心初始化：
- `CreatePipeline()` 函数创建渲染管线
- 默认 Renderer 为继承自 `ScriptableRenderer` 的 `ForwardRenderer`
- 初始化 `UniversalRenderPipeline`

### UniversalRenderPipeline 初始化

```csharp
public UniversalRenderPipeline(UniversalRenderPipelineAsset asset)
{
    SetSupportedRenderingFeatures();
    
    // 初始化 Shader 全局变量
    PerFrameBuffer._GlossyEnvironmentColor = Shader.PropertyToID("_GlossyEnvironmentColor");
    PerFrameBuffer._Time = Shader.PropertyToID("_Time");
    // ... 更多变量
    
    PerCameraBuffer._InvCameraViewProj = Shader.PropertyToID("_InvCameraViewProj");
    PerCameraBuffer._WorldSpaceCameraPos = Shader.PropertyToID("_WorldSpaceCameraPos");
    // ... 更多变量
    
    Shader.globalRenderPipeline = "UniversalPipeline,LightweightPipeline";
}
```

### 每帧渲染流程 - Render()

Unity 每帧自动调用 `Render()` 函数：

```csharp
protected override void Render(ScriptableRenderContext renderContext, Camera[] cameras)
{
    BeginFrameRendering(renderContext, cameras);
    
    GraphicsSettings.lightsUseLinearIntensity = (QualitySettings.activeColorSpace == ColorSpace.Linear);
    GraphicsSettings.useScriptableRenderPipelineBatching = asset.useSRPBatcher;
    SetupPerFrameShaderConstants();
    
    SortCameras(cameras);  // 按深度排序
    foreach (Camera camera in cameras)
    {
        BeginCameraRendering(renderContext, camera);
        RenderSingleCamera(renderContext, camera);  // 核心！
        EndCameraRendering(renderContext, camera);
    }
    
    EndFrameRendering(renderContext, cameras);
}
```

### 关键函数 - RenderSingleCamera

```csharp
public static void RenderSingleCamera(ScriptableRenderContext context, Camera camera)
{
    // 1. 获取裁剪参数
    camera.TryGetCullingParameters(out var cullingParameters);
    
    // 2. 初始化相机数据
    InitializeCameraData(settings, camera, additionalCameraData, out var cameraData);
    SetupPerCameraShaderConstants(cameraData);
    
    // 3. 获取 Renderer
    ScriptableRenderer renderer = additionalCameraData.scriptableRenderer;
    
    // 4. 标准渲染流程
    CommandBuffer cmd = CommandBufferPool.Get(tag);
    
    renderer.Clear();
    renderer.SetupCullingParameters(ref cullingParameters, ref cameraData);
    context.ExecuteCommandBuffer(cmd);
    cmd.Clear();
    
    var cullResults = context.Cull(ref cullingParameters);
    InitializeRenderingData(settings, ref cameraData, ref cullResults, out var renderingData);
    
    renderer.Setup(context, ref renderingData);
    renderer.Execute(context, ref renderingData);
    
    context.ExecuteCommandBuffer(cmd);
    CommandBufferPool.Release(cmd);
    context.Submit();
}
```

### 标准 Unity 渲染流程总结

1. **清空 renderer，setup 裁剪数据**
2. **执行裁剪** - `context.Cull(ref cullingParameters)`
3. **初始化渲染数据** - `InitializeRenderingData()`
4. **Renderer 设置和执行** - `renderer.Setup()` + `renderer.Execute()`
5. **执行并释放 CommandBuffer**
6. **提交渲染命令** - `context.Submit()`

---

## URP 源码分析 - ForwardRenderer

**标签**：#unity #graphics #knowledge #urp #srp
**来源**：TaTa 仓库 - URP-analysis/urp-analysis.md
**来源日期**：2020-11-05
**状态**：📘 有效
**收录日期**：2026-01-31
**可信度**：⭐⭐⭐⭐ (源码分析 + 实践验证)

### ForwardRenderer 初始化

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

### 默认渲染顺序

URP 默认渲染逻辑与 Build-in 管线一致：

1. **ShadowMap Pass** - 绘制阴影贴图
2. **Opaque Pass** - 绘制不透明物体
3. **Skybox Pass** - 绘制天空盒
4. **Transparent Pass** - 绘制透明物体
5. **PostProcess Pass** - 后处理

### URP vs Build-in 的核心区别

| 特性 | Build-in | URP |
|------|----------|-----|
| 渲染流程 | 封装，难以修改 | 完全暴露，可定制 |
| Shadow Pass | 固定 | 可自定义 shader |
| RenderTexture 格式 | 固定 | 可自定义通道含义 |
| 扩展性 | 有限 | Renderer Feature 插件系统 |

### ForwardRenderer.Setup() 流程

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

### CommandBuffer 说明

- 每次绘制都是一次命令
- 多个绘制命令可以 push 到同一个 CommandBuffer
- 执行 CommandBuffer 时，GPU 按顺序执行命令
- 可用于定制自己想要的渲染效果

---

## Renderer Feature 的要点

**标签**：#unity #graphics #knowledge #urp #srp
**来源**：Unity 官方文档 - Custom Renderer Feature、URP 工程实践
**来源日期**：-
**状态**：📘 有效
**收录日期**：2026-01-30
**可信度**：⭐⭐⭐⭐⭐ (官方文档 + 实践验证)

- 关注 Pass 插入时机（`RenderPassEvent`）：不同时机影响与后处理、透明队列、深度纹理等的交互。
- 关注 RT 分配/释放：临时 RT、RTHandles、分辨率变化、Camera stacking 等都会影响资源生命周期。
- 关注排序与依赖：Pass 之间的输入输出（深度、颜色、mask RT）要明确，避免隐式依赖。

---

## CommandBuffer（命令录制）在 URP 中的角色

**标签**：#unity #graphics #knowledge #urp #srp
**来源**：Unity 官方文档 - CommandBuffer、URP 源码分析
**来源日期**：-
**收录日期**：2026-01-30
**状态**：📘 有效
**可信度**：⭐⭐⭐⭐⭐ (官方文档 + 源码验证)

- RenderPass 通常会构建命令并提交执行；命令过多会带来 CPU 开销。
- 建议在关键 Pass 上加 profiling（CPU/GPU）点，确认瓶颈位置。

---

## 关联知识

- 渲染管线基础：./rendering-pipeline-overview.md
- 色彩空间：./color-space-gamma-linear.md
- 色带与抖动（Color Banding / Dithering）：./color-banding-dither.md

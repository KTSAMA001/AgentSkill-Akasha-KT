# URP 渲染入口与 RenderSingleCamera 流程

**标签**：#unity #graphics #knowledge #urp #srp #rendering-pipeline
**来源**：TaTa 仓库 - URP-analysis/urp-analysis.md
**收录日期**：2026-01-31
**来源日期**：2020-11-05
**更新日期**：2026-06-13
**状态**：📘 有效
**可信度**：⭐⭐⭐⭐ (源码分析 + 实践验证)
**适用版本**：URP 源码分析记录对应版本（原记录未注明精确包版本）

### 概要

URP 的每帧渲染入口从 Pipeline Asset 创建管线开始，经 `Render()` 遍历相机，再由 `RenderSingleCamera()` 完成裁剪、渲染数据初始化、Renderer setup/execute 和提交命令。

### 内容

#### 入口文件

URP 入口文件：`UniversalRenderPipelineAsset.cs`

核心初始化：

- `CreatePipeline()` 函数创建渲染管线。
- 默认 Renderer 为继承自 `ScriptableRenderer` 的 `ForwardRenderer`。
- 初始化 `UniversalRenderPipeline`。

#### UniversalRenderPipeline 初始化

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

#### 每帧渲染流程 - Render()

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

#### 关键函数 - RenderSingleCamera

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

标准 Unity 渲染流程总结：

1. 清空 renderer，setup 裁剪数据。
2. 执行裁剪：`context.Cull(ref cullingParameters)`。
3. 初始化渲染数据：`InitializeRenderingData()`。
4. Renderer 设置和执行：`renderer.Setup()` + `renderer.Execute()`。
5. 执行并释放 CommandBuffer。
6. 提交渲染命令：`context.Submit()`。

### 关键代码

见“内容”中的 `UniversalRenderPipeline`、`Render()` 与 `RenderSingleCamera()` 片段。

### 相关记录

- [URP 核心 Renderer/Pass/Feature 架构](./urp-core-renderer-pass-feature-architecture.md) - Renderer/Pass/Feature 的角色划分。
- [URP ForwardRenderer Setup 流程](./urp-forward-renderer-setup-flow.md) - `renderer.Setup()` 内部组织 Pass 的方式。

### 验证记录

- [2026-04-15] 结构修复：补齐模板必填章节，未改动原结论。
- [2026-06-13] 结构维护：从旧聚合记录拆分，未重新验证原技术结论。

---

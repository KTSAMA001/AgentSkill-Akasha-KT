# URP Renderer Feature 开发要点

**收录日期**：2026-01-31
**更新日期**：2026-08-03
**标签**：#shader #unity #experience #urp #srp-batcher #renderer-feature
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐ (实践验证)
**来源**：Technical_Artist_Technotes/关于SRP、URP
**适用版本**：Unity 2022.3 / URP 14 兼容模式；Unity 6 Render Graph 路线请参阅跨版本指南

**问题/场景**：


### 概要
URP Renderer Feature 在 Unity 2022.3 / URP 14 兼容模式下的开发要点，重点是 `Execute + CommandBuffer + RTHandle` 路线。Unity 6 仍使用 Renderer Feature 注入 Pass，但 Pass 主体应迁移为 Render Graph 的 `RecordRenderGraph`；两代 API 的完整映射见相关记录中的跨版本指南。

如何在 URP 中自定义 Renderer Feature？有哪些常见的踩坑点？

**核心概念**：

### 1. 什么是 Renderer Feature

在本记录对应的 URP 14 兼容模式中，Renderer Feature 通常创建并注入一个或多个围绕 **CommandBuffer 操作**组织的 `ScriptableRenderPass`。它允许向 URP Renderer 添加额外渲染阶段，自定义渲染顺序、渲染对象、材质等。

**本质**：在渲染任务列表中插入、调整渲染任务

> 版本边界：Renderer Feature 是“创建、配置和注入 Pass”的入口，并不等于 CommandBuffer 本身。Unity 6 Render Graph 路线仍可使用同一个 Feature 外壳，但 Pass 内改为声明资源依赖和延迟执行。

### 2. 为什么需要 Renderer Feature

**URP 默认主绘制的限制**：Forward Renderer 的默认 DrawObjectsPass 只会在一组受支持的 `LightMode` Pass 中选择并绘制，例如 `SRPDefaultUnlit`、`UniversalForward`、`UniversalForwardOnly`。自定义 `LightMode` 或额外 Pass 不会自动参与主绘制。

**传统多 Pass 的正确迁移方式**：URP 不是不能做多次绘制，而是需要通过 Render Objects / 自定义 RendererFeature 在合适的 `RenderPassEvent` 再次 `DrawRenderers`，并用 Pass 的 `LightMode` tag 选择额外 Pass。
```shaderlab
Pass 1: 主体 Pass，LightMode = UniversalForwardOnly，由 URP 默认管线绘制
Pass 2: 描边 Pass，LightMode = RoleOutline，由 Render Objects / RendererFeature 额外绘制
```

**解决方案**：使用 Renderer Feature 在指定渲染阶段添加新的绘制 Pass；若只是统一材质高亮，可使用 `overrideMaterial`，若希望角色 Shader 自带描边上下文，则优先让角色 Shader 提供自定义 `LightMode` 的描边 Pass。

### 3. CommandBuffer 基本流程

```csharp
public override void Execute(ScriptableRenderContext context, ref RenderingData renderingData)
{
    // 1. 申请 CommandBuffer（指定名称，对应 Frame Debugger 中的任务名）
    CommandBuffer cmd = CommandBufferPool.Get("MyFeatureName");
    
    // 2. 设置相机、光照等信息
    Camera camera = renderingData.cameraData.camera;
    
    // 3. 添加绘制命令
    cmd.DrawMesh(mesh, matrix, material);
    // 或 cmd.DrawRenderer(renderer, material);
    
    // 4. 执行 CommandBuffer
    context.ExecuteCommandBuffer(cmd);
    
    // 5. 释放 CommandBuffer
    CommandBufferPool.Release(cmd);
}
```

### 4. 常见踩坑点

#### 4.1 部分物体不被渲染

**原因**：Render Layer Mask 设置问题

```csharp
// 在 FilteringSettings 中设置 LayerMask
FilteringSettings filteringSettings = new FilteringSettings(
    RenderQueueRange.opaque,
    layerMask: 1 << targetLayer  // 只渲染指定 Layer
);
```

#### 4.2 批处理失效

**原因1**：Shader 属性未放入 CBUFFER
```hlsl
// 所有属性都要在 CBUFFER 中声明
CBUFFER_START(UnityPerMaterial)
    half4 _Color;
CBUFFER_END
```

**原因2**：未知问题 → 尝试重新烘焙场景光照

#### 4.3 Frame Debugger 中 Pass 名称不对

**原因**：CommandBuffer 申请时的名称就是 Frame Debugger 中显示的任务名

```csharp
// 这个名称会显示在 Frame Debugger 中
CommandBuffer cmd = CommandBufferPool.Get("SurfaceOutline");
```

### 5. 官方 Renderer Feature 参考

| Feature | 功能 |
|---------|------|
| Render Objects | 在指定时机用指定材质渲染指定 Layer 的物体 |
| Decal | 贴花系统 |
| Screen Space Shadows | 屏幕空间阴影映射（需手动添加，非默认） |
| SSAO | 屏幕空间环境光遮蔽 |

### 6. ScriptableRenderPass 关键方法

```csharp
public class MyRenderPass : ScriptableRenderPass
{
    // 配置渲染目标
    public override void OnCameraSetup(CommandBuffer cmd, ref RenderingData renderingData) { }
    
    // 执行渲染（核心方法）
    public override void Execute(ScriptableRenderContext context, ref RenderingData renderingData) { }
    
    // 清理资源
    public override void OnCameraCleanup(CommandBuffer cmd) { }
}
```

### 7. ScriptableRendererFeature 基本结构

```csharp
public class MyRendererFeature : ScriptableRendererFeature
{
    MyRenderPass m_RenderPass;
    
    public override void Create()
    {
        m_RenderPass = new MyRenderPass();
        m_RenderPass.renderPassEvent = RenderPassEvent.AfterRenderingOpaques;
    }
    
    public override void AddRenderPasses(ScriptableRenderer renderer, ref RenderingData renderingData)
    {
        renderer.EnqueuePass(m_RenderPass);
    }
}
```

### 相关记录

- [Unity URP 跨版本渲染扩展：Renderer Feature、兼容模式与 Render Graph](./urp-renderer-feature-render-graph-versioned-guide.md) - 对比 Unity 2022.3 / URP 14 与 Unity 6 的扩展入口、Pass 主体、资源生命周期和迁移方法。
- [URP RenderFeature 使用 LightMode 筛选额外 Pass 的机制](./urp-renderfeature-lightmode-pass-filtering.md) - 补充说明 `ShaderTagId`、Render Objects `Pass Names` 与 ShaderLab `LightMode` / `Pass Name` 的边界。

### 验证记录
- [2026-01-31] 从 Technical_Artist_Technotes 整理提取
- [2026-07-07] 修正：收窄“URP 不支持传统多 Pass”的旧表述。准确边界是默认主绘制不会自动绘制任意额外 Pass；Render Objects / 自定义 RendererFeature 可通过 Pass 的 `LightMode` tag 额外绘制，从而实现 URP 下的多次绘制。
- [2026-08-03] 版本收窄：明确本文代码属于 Unity 2022.3 / URP 14 兼容模式；补充 Renderer Feature 与 CommandBuffer、Render Graph 的层级边界，并关联跨版本迁移指南。

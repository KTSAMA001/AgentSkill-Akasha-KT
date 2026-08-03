# Unity URP 跨版本渲染扩展：Renderer Feature、兼容模式与 Render Graph

**标签**：#unity #graphics #knowledge #urp #renderer-feature #rendering-pipeline
**来源**：Unity URP 14 / Unity 6 官方文档、Unity Learn、Unity 官方技术文章与社区实践交叉整理
**来源日期**：2022-2026（跨版本资料）
**收录日期**：2026-08-03
**更新日期**：2026-08-03
**状态**：📘 有效
**可信度**：⭐⭐⭐⭐⭐（Unity 官方手册、官方培训与官方技术文章交叉验证）
**适用版本**：Unity 2019.3+ 的 URP Renderer Feature 概念；代码重点对比 Unity 2022.3 / URP 14 与 Unity 6 / URP 17+

### 概要

Renderer Feature 与 Render Graph 不是互相替代的两套方案：前者负责创建、配置并把自定义 `ScriptableRenderPass` 注入 URP，后者负责在 Pass 内声明资源读写、建立依赖并调度执行。Unity 2022.3 / URP 14 主要使用 `Execute + RTHandle`；Unity 6 仍保留 Renderer Feature 作为常用注入入口，但 Pass 主体应迁移为 `RecordRenderGraph + TextureHandle`。

### 内容

#### 一、先把四个容易混淆的层级分开

```text
ScriptableRendererFeature
  负责配置、创建 Pass、选择相机、EnqueuePass
                │
                ▼
ScriptableRenderPass
  表示插入 URP 帧循环的一段渲染工作
                │
       ┌────────┴────────┐
       ▼                 ▼
兼容模式 Execute()     Render Graph RecordRenderGraph()
直接录制命令           声明资源与任务，稍后由图系统执行
                │
                ▼
Shader Pass
  最终由渲染 Pass 通过 ShaderTagId、材质或全屏绘制选中并执行
```

- `ScriptableRendererFeature` 是 URP Renderer Data 上的插件入口。它常用 `Create` 初始化材质和 Pass，用 `AddRenderPasses` 把 Pass 加入当前相机的队列，并在 `Dispose` 释放长期资源。
- `ScriptableRenderPass` 是真正的渲染阶段单元，负责对象重绘、Blit、Compute、Mask、后处理等工作。
- `Render Graph` 是 Pass 和资源的声明、依赖分析与调度系统。它不会取代 Feature，也不会取代 Shader。
- `Shader Pass` 是 ShaderLab 中的具体 GPU 程序。URP 执行的是渲染 Pass，渲染 Pass 再选择并调用匹配的 Shader Pass。

因此，“Unity 6 不再使用 Renderer Feature，改用 Render Graph”是错误理解。更准确的说法是：**Unity 6 中仍可由 Renderer Feature 注入 ScriptableRenderPass，但 Pass 的实现由立即式 `Execute` 转向声明式 `RecordRenderGraph`。**

#### 二、版本演进

| Unity / URP | 扩展入口 | Pass 主体 | 资源方式 | 定位 |
|---|---|---|---|---|
| Unity 2019.3-2021 LTS / URP 7-12 | `ScriptableRendererFeature` | `Execute` | `RenderTargetIdentifier`、`GetTemporaryRT` 等旧 API | 早期 Renderer Feature，API 随版本变化较多 |
| Unity 2022.3 / URP 14 | `ScriptableRendererFeature` | `Execute` | `RTHandle`、`RenderingUtils.ReAllocateIfNeeded`、`Blitter` | 旧式路线较成熟，仍需手动管理生命周期和执行顺序 |
| Unity 6 / URP 17+ | `ScriptableRendererFeature` 或 `RenderPipelineManager` | `RecordRenderGraph` | `TextureHandle`、显式读写声明、图管理帧内资源 | 新功能推荐路线，URP 可分析并优化整个帧图 |
| Unity 6 Compatibility Mode | `ScriptableRendererFeature` | `Execute` | 与 URP 14 接近 | 用于旧项目和第三方资产迁移，不是新功能的长期目标 |

Unity 6 的 URP Graphics Settings 中可以启用 `Compatibility Mode (Render Graph Disabled)` 继续运行未迁移的旧 Pass。Unity 官方已明确说明：不使用 Render Graph 的路径不再继续开发或改进，新图形功能应使用 Render Graph。

#### 三、跨版本差异速查

| 关注点 | Unity 2022.3 / URP 14 兼容模式 | Unity 6 Render Graph |
|---|---|---|
| Feature 生命周期 | `Create` / `AddRenderPasses` / `SetupRenderPasses` / `Dispose` | 基本保留；Feature 仍负责创建与注入 Pass |
| 每帧入口 | `Execute(ScriptableRenderContext, ref RenderingData)` | `RecordRenderGraph(RenderGraph, ContextContainer)` |
| 相机和帧数据 | `RenderingData`、`CameraData` | `UniversalRenderingData`、`UniversalCameraData`、`UniversalResourceData` |
| 相机颜色目标 | `cameraColorTargetHandle` | `UniversalResourceData.activeColorTexture` / `cameraColor`，具体字段以 URP 小版本为准 |
| 临时纹理 | 持有 `RTHandle` 并 `ReAllocateIfNeeded`，在 Feature 销毁时释放 | 帧内纹理使用 `TextureHandle`，由图系统决定实际创建、复用和销毁 |
| 外部/跨帧纹理 | 长期 `RTHandle` 或 `RenderTexture` | 先持有外部资源，再通过 `ImportTexture` 导入当前图 |
| 纹理输入 | 通过 Shader 全局属性、材质或 Blit 源隐式使用 | `builder.UseTexture(handle, AccessFlags.Read)` |
| 颜色输出 | `ConfigureTarget`、Blitter 的 destination | `SetRenderAttachment` 或 `AddBlitPass` 的 destination |
| 深度输出 | `ConfigureTarget(color, depth)` | `SetRenderAttachmentDepth` |
| 对象绘制 | `DrawingSettings + FilteringSettings + DrawRenderers` | `RendererListHandle + UseRendererList + DrawRendererList` |
| 多 Pass 关系 | 主要靠入队顺序和全局纹理约定 | 通过 `TextureHandle` 读写形成显式依赖 |
| 调试 | Frame Debugger、Profiler、RenderDoc | 以上工具加 Render Graph Viewer 和有效性检查 |

Unity 6 的字段名和 helper API 在 6.x 小版本间仍可能调整，复制代码前必须用当前安装包的官方文档和 IDE 类型提示核对，不能只看“Unity 6”这一大版本标签。

#### 四、什么时候使用哪一种扩展方式

1. **先看内置 Renderer Feature 是否足够**：Render Objects、Full Screen Pass、Decal、SSAO 等能满足需求时，优先使用内置功能，减少自定义生命周期和升级成本。
2. **需要 Inspector 配置、固定注入点或多个协作 Pass**：使用自定义 `ScriptableRendererFeature`。这是对象重绘、Mask、描边、自定义后处理和多级 RT 链最常见的入口。
3. **Unity 2022.3 / 已锁版本项目**：可以继续维护 `Execute + RTHandle`，但必须明确这是 URP 14 风格，不要把代码无条件复制到 Unity 6 Render Graph 路径。
4. **Unity 6 新功能**：保留 Feature 外壳，在 `ScriptableRenderPass.RecordRenderGraph` 中实现资源声明和执行函数。
5. **需要代码级全局注入而不依赖 Renderer Data 资产**：可以评估 `RenderPipelineManager` 事件。它是另一种注入入口，但不会免除资源依赖、相机筛选和多相机生命周期设计。
6. **仅为迁移旧命令而暂时需要 `SetRenderTarget` 等 API**：可以使用 `AddUnsafePass`，但应视为迁移桥梁。Unsafe Pass 会削弱 Render Graph 的依赖分析、Pass 合并和带宽优化能力。

#### 五、Unity 2022.3 / URP 14 的执行模型

旧式 Pass 的思路是“在当前时机直接录制命令”：

```text
Feature.Create
  └─ 创建材质和 Pass

每个相机：
Feature.AddRenderPasses
  └─ renderer.EnqueuePass(pass)

Pass.OnCameraSetup
  └─ 根据相机描述符分配或调整 RTHandle

Pass.Execute
  └─ 获取 CommandBuffer
  └─ DrawRenderers / Blitter / DispatchCompute
  └─ ExecuteCommandBuffer

Feature.Dispose
  └─ 释放材质和长期 RTHandle
```

这种模式直观，但 Pass 间依赖经常隐藏在全局纹理名、执行顺序和手工 RT 生命周期里。开发者必须自己处理分辨率变化、Camera Stack、XR、动态分辨率、同一 RT 读写和释放时机。

#### 六、Unity 6 Render Graph 的执行模型

`RecordRenderGraph` 的作用不是马上向 GPU 发命令，而是描述：

- 这个 Pass 是 Raster、Compute 还是 Unsafe；
- 读取哪些纹理、缓冲或 RendererList；
- 写入哪些颜色和深度附件；
- 执行阶段需要哪些 `PassData`；
- 真正执行时调用哪个 `SetRenderFunc`。

```text
Feature.AddRenderPasses
  └─ 仍然 EnqueuePass

Pass.RecordRenderGraph
  ├─ 从 ContextContainer 获取当前帧数据
  ├─ 创建或取得 TextureHandle / RendererListHandle
  ├─ AddRasterRenderPass / AddComputePass / AddUnsafePass
  ├─ 声明 UseTexture / SetRenderAttachment / UseRendererList
  └─ SetRenderFunc

Render Graph 编译与执行
  ├─ 分析依赖
  ├─ 剔除无最终用途的 Pass
  ├─ 复用生命周期不重叠的资源
  ├─ 尝试合并兼容的 Native Render Pass
  └─ 按正确顺序执行命令
```

`PassData` 只能放执行函数真正需要的数据。`RecordRenderGraph` 和实际执行之间存在延迟，执行函数不应依赖随后可能改变的临时局部状态。

#### 七、Render Graph 带来的收益与边界

**可获得的收益**：

- 根据读写关系自动建立 Pass 顺序，而不是只依赖人工约定；
- 未被最终结果使用的 Pass 和临时资源可以被剔除；
- 生命周期不重叠的帧内纹理有机会复用底层内存；
- 兼容的 Raster Pass 有机会合并为 Native Render Pass，减少移动端 Tile Load/Store；
- Render Graph Viewer 可以显示 Pass、资源、读写关系、被剔除 Pass 和无法合并的原因；
- 有效性检查能更早发现未声明资源、非法读写和错误附件用法。

**不能自动解决的问题**：

- Render Graph 不会减少 Shader 本身的采样数、循环次数或 overdraw；
- 错误的注入点仍会读到错误阶段的颜色、深度或透明结果；
- 同一个 Raster Pass 内不能随意更换 RenderTarget，也不能把同一纹理同时作为普通采样输入和颜色输出；
- `TextureHandle` 通常只对当前帧、当前 Render Graph 有效，不能作为跨帧缓存直接保存；
- 使用 `AllowPassCulling(false)`、全局状态或 Unsafe Pass 会限制图系统优化，应只在确有外部副作用时启用；
- 多相机、Camera Stack、Scene View、XR 和动态分辨率仍需要显式筛选与测试。

#### 八、常见效果如何迁移

| 效果 | URP 14 思路 | Unity 6 Render Graph 思路 |
|---|---|---|
| 重绘指定对象 | `DrawRenderers` + `DrawingSettings` + `FilteringSettings` | 创建 `RendererListHandle`，`UseRendererList` 后 `DrawRendererList` |
| 全屏后处理 | 相机颜色 → 临时 `RTHandle` → 相机颜色 | `activeColorTexture` → 新 `TextureHandle`，用 `AddBlitPass`，再更新当前相机颜色引用 |
| 深度/Mask RT | Feature 持有 RTHandle，Pass 手动配置目标 | Pass 创建帧内 TextureHandle，并把它声明为颜色或深度附件 |
| 多级 Bloom/Blur | Feature 持有 RTHandle 数组并手动 ping-pong | 每级创建 TextureHandle，用显式读写关系连接多个 Pass |
| 跨 Pass 纹理 | 全局纹理名或共享 RTHandle | 在同一图中传递 TextureHandle；需要全局可见时使用官方的 pass 后全局纹理机制 |
| 跨帧历史纹理 | 长期 RTHandle / RenderTexture | 持有外部 RTHandle，并在每帧 ImportTexture；自行负责跨帧尺寸和释放 |
| 旧 API 迁移 | 直接使用 CommandBuffer | 短期可放入 Unsafe Pass，长期应拆成可声明依赖的 Raster/Compute Pass |

#### 九、推荐迁移步骤

1. 升级 Unity 6 后先确认项目是否因旧自定义 Pass 或第三方资产启用了 Compatibility Mode。
2. 枚举所有 `ScriptableRendererFeature`、`ScriptableRenderPass.Execute`、`OnCameraSetup`、`ConfigureTarget`、`GetTemporaryRT`、`RTHandle` 和自定义 Blit。
3. 先保留 `ScriptableRendererFeature` 的配置、`Create`、相机筛选和 `AddRenderPasses`；迁移重点放在 Pass 内部。
4. 把 `RenderingData` 的读取映射到 `ContextContainer` 中对应的 `Universal*Data`。
5. 把帧内临时 RT 改为 `TextureHandle`；只有外部、跨帧或跨相机资源才保留 RTHandle 并导入图。
6. 为每个 Pass 明确列出输入、颜色输出、深度输出、RendererList 和外部副作用。
7. 把同一纹理的读写拆为 source/destination 两个 Handle；需要改变 RenderTarget 时拆成第二个 Pass。
8. 对象绘制迁移到 RendererList；全屏复制优先使用 `RenderGraphUtils.AddBlitPass` 或官方 Blitter 模式。
9. 尽量消除 Unsafe Pass 和无条件 `AllowPassCulling(false)`，否则无法充分获得图优化收益。
10. 使用 Render Graph Viewer 检查被剔除 Pass、资源生命周期、Pass 合并和 break reason，再用 Frame Debugger / RenderDoc 核对实际像素结果。
11. 最后覆盖 Game View、Scene View、Camera Stack、动态分辨率、XR Single Pass Instanced 和目标真机性能。

#### 十、迁移时最容易出现的误区

- **误区：Feature 被 Render Graph 取代。** Feature 仍是常用注入和配置入口，Render Graph 改变的是 Pass 如何描述与执行。
- **误区：`TextureHandle` 就是新的长期 RT 对象。** 它通常是当前帧图中的逻辑句柄，跨帧资源仍需外部所有者。
- **误区：把所有旧命令塞进 Unsafe Pass 就完成迁移。** 这只能恢复功能，不能获得完整的资源分析和 Pass 合并收益。
- **误区：Render Graph 会自动解决所有性能问题。** 它优化资源和调度，不会替代 Shader、overdraw、分辨率和采样设计。
- **误区：同为 Unity 6，网上代码都可直接复制。** URP 17 的小版本 API、字段名和 helper 仍可能变化，必须按项目实际 package 版本核对。
- **误区：只看 Game View 有结果就算迁移完成。** 多相机、Scene View、XR、Camera Stack 和最终真机带宽才是完整验证范围。

### 关键代码

#### Unity 2022.3 / URP 14 兼容模式骨架

```csharp
public sealed class ExampleFeature : ScriptableRendererFeature
{
    [SerializeField] Shader shader;
    Material material;
    ExamplePass pass;

    public override void Create()
    {
        CoreUtils.Destroy(material);
        material = CoreUtils.CreateEngineMaterial(shader);
        pass = new ExamplePass(material)
        {
            renderPassEvent = RenderPassEvent.BeforeRenderingPostProcessing
        };
    }

    public override void AddRenderPasses(
        ScriptableRenderer renderer,
        ref RenderingData renderingData)
    {
        renderer.EnqueuePass(pass);
    }

    protected override void Dispose(bool disposing)
    {
        CoreUtils.Destroy(material);
    }
}

public sealed class ExamplePass : ScriptableRenderPass
{
    readonly ProfilingSampler profilingSampler = new("Example Pass");

    public override void Execute(
        ScriptableRenderContext context,
        ref RenderingData renderingData)
    {
        CommandBuffer cmd = CommandBufferPool.Get("Example Pass");
        using (new ProfilingScope(cmd, profilingSampler))
        {
            // DrawRenderers、Blitter 或 DispatchCompute。
            // 临时 RTHandle 的申请、读写分离与生命周期由代码负责。
        }

        context.ExecuteCommandBuffer(cmd);
        CommandBufferPool.Release(cmd);
    }
}
```

#### Unity 6 Render Graph 全屏 Pass 骨架

```csharp
public sealed class ExampleFeature : ScriptableRendererFeature
{
    ExamplePass pass;

    public override void Create()
    {
        pass = new ExamplePass
        {
            renderPassEvent = RenderPassEvent.BeforeRenderingPostProcessing
        };
    }

    public override void AddRenderPasses(
        ScriptableRenderer renderer,
        ref RenderingData renderingData)
    {
        renderer.EnqueuePass(pass);
    }
}

public sealed class ExamplePass : ScriptableRenderPass
{
    readonly Material material;

    public ExamplePass(Material material)
    {
        this.material = material;
    }

    public override void RecordRenderGraph(
        RenderGraph renderGraph,
        ContextContainer frameData)
    {
        UniversalResourceData resources =
            frameData.Get<UniversalResourceData>();

        if (resources.isActiveTargetBackBuffer)
            return;

        TextureHandle source = resources.activeColorTexture;
        TextureDesc destinationDesc = renderGraph.GetTextureDesc(source);
        destinationDesc.name = "Example Destination";
        destinationDesc.clearBuffer = false;
        destinationDesc.depthBufferBits = DepthBits.None;

        TextureHandle destination = renderGraph.CreateTexture(destinationDesc);

        var parameters = new RenderGraphUtils.BlitMaterialParameters(
            source,
            destination,
            material,
            0);

        renderGraph.AddBlitPass(parameters, "Example Pass");

        // 让后续 URP Pass 继续使用新颜色，避免再做一次写回 Blit。
        resources.cameraColor = destination;
    }
}
```

以上骨架用于说明职责分层，不是跨所有 URP 17 小版本原样可编译的兼容层。`DepthBits` 命名空间、`UniversalResourceData` 字段和 Blit helper 应以项目实际安装的 URP 包为准。

### 参考链接

- [URP 14：创建自定义 Renderer Feature](https://docs.unity.cn/Packages/com.unity.render-pipelines.universal@14.0/manual/renderer-features/create-custom-renderer-feature.html) - Unity 2022.3 / URP 14 的 `Create`、`AddRenderPasses` 与 `Execute` 示例。
- [Unity 6：URP 自定义渲染 Pass 工作流](https://docs.unity3d.com/6000.0/Documentation/Manual/urp/renderer-features/custom-rendering-pass-workflow-in-urp.html) - Renderer Feature 仍负责创建并注入 Pass，Pass 使用 Render Graph API。
- [Unity 6：使用 Render Graph 编写 Render Pass](https://docs.unity3d.com/6000.0/Documentation/Manual/urp/render-graph-write-render-pass.html) - `RecordRenderGraph`、PassData、资源声明和执行函数。
- [Unity 6：在 Render Graph Pass 中使用纹理](https://docs.unity3d.com/6000.0/Documentation/Manual/urp/render-graph-read-write-texture.html) - `UseTexture`、`SetRenderAttachment` 与同纹理读写限制。
- [Unity 6：在 Render Graph 中绘制对象](https://docs.unity3d.com/6000.0/Documentation/Manual/urp/render-graph-draw-objects-in-a-pass.html) - RendererList 的官方用法。
- [Unity 6：Compatibility Mode](https://docs.unity3d.com/6000.0/Documentation/Manual/urp/compatibility-mode.html) - 旧式 Pass 路径的定位和维护边界。
- [Unity 6：Unsafe Pass](https://docs.unity3d.com/6000.0/Documentation/Manual/urp/render-graph-unsafe-pass.html) - 使用旧 API 的迁移桥梁及优化代价。
- [Unity 6：Render Graph Viewer](https://docs.unity3d.com/6000.0/Documentation/Manual/urp/render-graph-view.html) - 图结构、Pass 剔除、资源与合并原因分析。
- [Unity Learn：Using the Render Graph System to Create Custom Render Features](https://learn.unity.com/tutorial/use-render-graph-system-create-custom-render-features-ls) - Unity 官方实战课程和示例工程。
- [Unity 官方技术文章：Implementing Renderer Features with Render Graph](https://discussions.unity.com/t/understanding-urp-implementing-renderer-features-with-render-graph/1712280) - Unity 6000.3 中 Feature、RendererList 和 Render Graph 的完整描边案例。
- [Cyanilux：Custom Renderer Features](https://www.cyanilux.com/tutorials/custom-renderer-features/) - 跨版本社区实践参考；具体 API 仍应以项目安装的 URP 官方文档为准。

### 相关记录

- [SRP / URP 与 Renderer Feature 概览](./srp-urp-renderer-feature-overview.md) - SRP、URP 与 Renderer Feature 的概念入口。
- [URP 核心 Renderer / Pass / Feature 架构](./urp-core-renderer-pass-feature-architecture.md) - Renderer、Pass 与 Feature 的职责分层。
- [URP Renderer Feature 开发要点](./urp-renderer-feature-guide.md) - Unity 2022.3 / URP 14 兼容模式的实践要点。
- [URP RenderFeature 使用 LightMode 筛选额外 Pass 的机制](./urp-renderfeature-lightmode-pass-filtering.md) - 对象重绘时 ShaderTagId 与 LightMode 的边界。
- [URP RenderFeature 自定义后处理完整案例](./urp-renderfeature-postprocess-case-dual-kawase-bloom.md) - 旧式 RTHandle 多级后处理案例，可作为迁移样本。
- [Unity 6.3 LTS 完整迁移指南](./unity6-migration-guide.md) - Unity 6 工程整体迁移背景。
- [URP 屏幕空间描边 RenderFeature 实现](./urp-renderfeature-screen-space-outline.md) - 深度 Mask、颜色抓取和全屏合成的数据流案例。

### 验证记录

- [2026-08-03] 初次记录。基于 Unity 2022.3 / URP 14 与 Unity 6 官方手册、Unity Learn 官方课程、Unity 官方技术文章交叉验证，并以 Cyanilux 跨版本实践补充工程边界。确认 Renderer Feature 在 Unity 6 中仍是常用注入入口，Render Graph 主要改变 ScriptableRenderPass 的资源声明与执行模型。

---

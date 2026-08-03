# URP 屏幕空间描边 RenderFeature 实现

**标签**：#shader #unity #experience #urp #npr #renderer-feature #post-processing
**来源**：KTSAMA 实践经验
**来源日期**：2024-08-08
**收录日期**：2026-02-07
**更新日期**：2026-08-03
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐ (实践验证)
**适用版本**：Unity 2022.3 / URP 14 兼容模式实现；Unity 6+ 新功能优先迁移到 Render Graph

### 概要

URP 屏幕空间描边可通过“目标物体深度值 Mask → 相机颜色副本 → 全屏边缘检测与合成”的数据流实现，并通过 Volume 控制描边参数。深度值 Mask 与二值 Mask 的能力不同；最终合成必须避免把 Shader 正在采样的同一纹理子资源同时作为颜色输出。

### 内容

在 URP 中实现全屏屏幕空间描边效果，需要：

1. 基于深度 Mask 的边缘检测。
2. 通过 Volume 后处理系统控制参数（描边宽度、颜色）。
3. 支持 Scene View 和 Game View 同时工作。

#### 多 RenderFeature 协作

描边需要三个 RenderFeature 协同工作：

1. **SSDepthMaskPassFeature**：将目标物体的深度写入独立 RT (`_DepthMaskColor`)。
2. **GrabColorRenderPassFeature**：抓取当前帧颜色缓冲到 `_KTGrabTex`。
3. **SSOutLinePassFeature**：读取深度 Mask 和颜色，执行边缘检测并输出。

#### 三阶段数据流

这三个阶段按生产者与消费者关系排列：

1. **生成目标物体深度值 Mask**：按 Layer、Rendering Layer 或 ShaderTag 筛选目标 Renderer，把它们的深度标量写入 `_DepthMaskColor`。这里通常是“用颜色通道保存深度值”的颜色 RT，`depthBufferBits` 可以为 0；它不等同于把目标区域统一写成 1，也不一定是真正的深度附件。
2. **保存合成前的相机颜色**：把当前相机颜色复制到 `_KTGrabTex`。这张纹理是最终合成的原画面输入，也让后续 Pass 不必一边采样相机颜色、一边向同一个相机颜色子资源写入。
3. **边缘检测与合成**：全屏 Pass 同时读取 `_DepthMaskColor` 与 `_KTGrabTex`，通过邻域深度差得到描边因子，将描边颜色与原画面混合后写入独立临时颜色 RT，最后再写回相机颜色。

如果项目只需要区分“角色内/角色外”，也可以使用二值 Mask：目标区域为 1、背景为 0。二值 Mask 适合做形态学意义上的内外描边，但不能表达同一目标内部的深度不连续；深度值 Mask 则可以利用邻域深度差识别轮廓和部分内部遮挡边界。

二值 Mask 的常见表达是：

```text
外描边 = dilate(mask) - mask
内描边 = mask - erode(mask)
```

只在角色原有几何覆盖范围内运行的角色 Shader 通常只能输出内描边，因为轮廓外没有角色片元可供着色。外描边需要全屏 Pass、外扩几何，或其他能够覆盖轮廓外像素的绘制方式。

#### 自定义 Volume 组件

通过继承 `VolumeComponent` + `IPostProcessComponent` 实现后处理面板控制：

```csharp
[VolumeComponentMenu("KTSAMA_PostProcessing/ScreenSpaceOutLine")]
public class SSOutLineVolume : VolumeComponent, IPostProcessComponent
{
    public BoolParameter isEnabled = new BoolParameter(false);
    public FloatParameter _edgeWidth = new FloatParameter(4, true);
    public ColorParameter _edgeColor = new ColorParameter(Color.white, true);

    public bool IsActive() => isEnabled.value;
    public bool IsTileCompatible() => false;
}
```

#### 边缘检测算法（Shader 端）

8 方向深度采样对比，提取边缘：

```hlsl
// 8方向偏移采样深度 Mask
float d1 = SAMPLE_TEXTURE2D(_DepthMaskColor, sampler, uv + _InsiteEdgeWidth * float2( 1,-1) * f).r;
float d2 = SAMPLE_TEXTURE2D(_DepthMaskColor, sampler, uv + _InsiteEdgeWidth * float2(-1, 1) * f).r;
// ... 共 8 个方向 + 原点

float maxDepth = max(d1, max(d2, max(d3, ...)));
float outline = saturate(maxDepth - depthOrigin);
float3 result = lerp(screenColor, _EdgeColor, outline);
```

上式适用于当前记录的深度编码与清屏约定。若项目使用不同的背景值、深度编码或 reversed-Z 比较方向，应相应调整 `max/min` 与差值方向，并对结果做阈值和 `saturate` 处理，不能把固定符号直接套到所有管线。

#### 多方向偏移采样的伪影

四向或八向偏移采样本质上是用有限采样核近似膨胀、腐蚀或深度梯度。描边宽度增大后，尖角、细线和相邻轮廓容易出现：

- 尖角被压圆或沿采样方向形成不均匀厚度；
- 同一细小结构的两侧轮廓互相覆盖，表现为重复边或“重影”；
- 偏移没有按纹素尺寸换算时，分辨率、动态分辨率或 XR 眼纹理变化会改变实际宽度；
- 只使用少量固定方向时，斜边和轴向边的覆盖不同，产生方向性锯齿。

基础修正是用 `texelSize * widthInPixels` 计算 UV 偏移，并对深度差设置稳定阈值。宽描边或高质量尖角通常需要增加采样方向、使用可分离膨胀/模糊，或改用距离场、Jump Flood 等能显式估计到轮廓距离的方法；代价是额外采样、Pass 或中间纹理。

#### RenderFeature 中读取 Volume 参数

```csharp
public override void Create()
{
    _volumeStack = VolumeManager.instance.stack;
    ssol = _volumeStack.GetComponent<SSOutLineVolume>();
    setting.ssol = ssol;
}

public override void AddRenderPasses(...)
{
    if (ssol.isEnabled.value)
        renderer.EnqueuePass(m_ScriptablePass);
}
```

#### 关键踩坑点

- 使用 `RTHandle` + `RenderingUtils.ReAllocateIfNeeded` 管理临时 RT（而非旧的 `GetTemporaryRT`）。
- 当 Shader 把某纹理作为采样输入时，不能同时把同一纹理子资源作为当前颜色输出。兼容模式下通常用临时 RT 做 ping-pong；Render Graph 中应声明独立的输入、输出 `TextureHandle`，让图系统管理资源状态与生命周期。
- API 调用中 source 与 destination 出现同一个 handle，并不能单独证明发生了原地读写。例如 Shader 实际采样 `_CameraOpaqueTexture` 或 `_BlitTexture` 的独立颜色副本时，输出仍可指向相机颜色；判断风险要看 Shader 真正绑定并采样的底层资源。
- `renderPassEvent` 时机很重要：描边应在 `AfterRenderingSkybox` 之后执行。
- Scene View 兼容需区分处理 `SceneView.currentDrawingSceneView`。
- Unity 6 的官方文档已说明兼容模式渲染路径不再继续开发或改进；新功能应优先使用 Render Graph，旧的 `Execute`/手工 RTHandle 路线主要用于 Unity 2022.3 / URP 14 和迁移期兼容。

### 参考链接

- [Unity_URP_Learning/RenderFeature](https://github.com/KTSAMA001/Unity_URP_Learning/tree/main/Assets/Products/RenderFeature) - 完整源码。
- [可盖大人 Bilibili](https://www.bilibili.com/read/cv29054886/) - RTHandle 用法参考。
- [Unity 6：在兼容模式下编写 Scriptable Render Pass](https://docs.unity3d.com/cn/current/Manual/urp/renderer-features/write-a-scriptable-render-pass.html) - 官方临时 RT 与双阶段 Blit 示例，并说明新功能优先使用 Render Graph。
- [Unity URP 15：全屏 Blit 示例](https://docs.unity3d.com/Packages/com.unity.render-pipelines.universal@15.0/manual/renderer-features/how-to-fullscreen-blit.html) - 展示通过 `ConfigureInput(Color)` 读取独立颜色纹理的情况。
- [Microsoft：Direct3D 资源绑定限制](https://learn.microsoft.com/en-us/windows/win32/api/d3d10/nf-d3d10-id3d10device-omsetrendertargets) - 同一子资源不能在一次渲染操作中同时读写。

### 相关记录

- [屏幕空间刘海阴影 RenderFeature](./urp-renderfeature-screen-space-hair-shadow.md) - 类似的多 Layer / 多 Pass RenderFeature 模式。
- [URP Renderer Feature 开发要点](./urp-renderer-feature-guide.md) - 通用 RenderFeature 模式。
- [URP 中 GrabPass 替代方案](./urp-grabpass-alternative.md#grab-color-renderfeature) - 依赖 GrabColor 功能。
- [Renderer Feature 的要点](./urp-renderer-feature-extension-points.md) - SRP/URP 架构理论基础。

### 验证记录

- [2026-02-07] 从 Unity_URP_Learning 仓库整合，实际项目运行验证。
- [2026-06-13] 结构维护：从旧聚合记录拆分，未重新验证原技术结论。
- [2026-08-03] 结合每日问答与 Unity/Microsoft 官方资料复核：补充三阶段生产消费关系、二值 Mask 与深度值 Mask 的区别、内外描边覆盖范围、多方向偏移采样的尖角伪影、同一纹理子资源读写限制，以及 Unity 6 Render Graph 的版本边界；原实现主干保持有效。

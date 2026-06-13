# URP 屏幕空间描边 RenderFeature 实现

**标签**：#shader #unity #experience #urp #npr #renderer-feature #post-processing
**来源**：KTSAMA 实践经验
**来源日期**：2024-08-08
**收录日期**：2026-02-07
**更新日期**：2026-06-13
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐ (实践验证)
**适用版本**：Unity 2022.3+ / URP 14.0+

### 概要

URP 屏幕空间描边可通过深度 Mask、GrabColor 和后处理描边 Pass 多个 RenderFeature 协作实现，并通过 Volume 控制描边参数。

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
float outline = maxDepth - depthOrigin;
float3 result = lerp(screenColor, _EdgeColor, outline);
```

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
- `Blitter.BlitTexture` 需先 Blit 到临时 RT 再 Blit 回相机颜色，不能直接读写同一 RT。
- `renderPassEvent` 时机很重要：描边应在 `AfterRenderingSkybox` 之后执行。
- Scene View 兼容需区分处理 `SceneView.currentDrawingSceneView`。

### 参考链接

- [Unity_URP_Learning/RenderFeature](https://github.com/KTSAMA001/Unity_URP_Learning/tree/main/Assets/Products/RenderFeature) - 完整源码。
- [可盖大人 Bilibili](https://www.bilibili.com/read/cv29054886/) - RTHandle 用法参考。

### 相关记录

- [屏幕空间刘海阴影 RenderFeature](./urp-renderfeature-screen-space-hair-shadow.md) - 类似的多 Layer / 多 Pass RenderFeature 模式。
- [URP Renderer Feature 开发要点](./urp-renderer-feature-guide.md) - 通用 RenderFeature 模式。
- [URP 中 GrabPass 替代方案](./urp-grabpass-alternative.md#grab-color-renderfeature) - 依赖 GrabColor 功能。
- [Renderer Feature 的要点](./urp-renderer-feature-extension-points.md) - SRP/URP 架构理论基础。

### 验证记录

- [2026-02-07] 从 Unity_URP_Learning 仓库整合，实际项目运行验证。
- [2026-06-13] 结构维护：从旧聚合记录拆分，未重新验证原技术结论。

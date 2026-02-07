# NPR 渲染经验

> 非真实感渲染 (Non-Photorealistic Rendering) 相关经验
>
> 包含：卡通渲染、描边、屏幕空间刘海阴影等风格化渲染技术

---

## 屏幕空间描边 SSOutLine RenderFeature 实现 {#ss-outline-renderfeature}

**收录日期**：2026-02-07
**来源日期**：2024-08-08
**标签**：#RenderFeature #描边 #屏幕空间 #后处理 #VolumeComponent #NPR
**状态**：✅ 已验证
**适用版本**：Unity 2022.3+ / URP 14.0+

**问题/场景**：

在 URP 中实现全屏屏幕空间描边效果，需要：
1. 基于深度 Mask 的边缘检测
2. 通过 Volume 后处理系统控制参数（描边宽度、颜色）
3. 支持 Scene View 和 Game View 同时工作

**解决方案/结论**：

### 1. 多 RenderFeature 协作

描边需要三个 RenderFeature 协同工作：
1. **SSDepthMaskPassFeature** — 将目标物体的深度写入独立 RT (`_DepthMaskColor`)
2. **GrabColorRenderPassFeature** — 抓取当前帧颜色缓冲到 `_KTGrabTex`
3. **SSOutLinePassFeature** — 读取深度 Mask 和颜色，执行边缘检测并输出

### 2. 自定义 Volume 组件

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

### 3. 边缘检测算法（Shader 端）

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

### 4. RenderFeature 中读取 Volume 参数

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

### 5. 关键踩坑点

- 使用 `RTHandle` + `RenderingUtils.ReAllocateIfNeeded` 管理临时 RT（而非旧的 `GetTemporaryRT`）
- `Blitter.BlitTexture` 需先 Blit 到临时 RT 再 Blit 回相机颜色，不能直接读写同一 RT
- `renderPassEvent` 时机很重要：描边应在 `AfterRenderingSkybox` 之后执行
- Scene View 兼容需区分处理 `SceneView.currentDrawingSceneView`

**参考链接**：

- [Unity_URP_Learning/RenderFeature](https://github.com/KTSAMA001/Unity_URP_Learning/tree/main/Assets/Products/RenderFeature) - 完整源码
- [可盖大人 Bilibili](https://www.bilibili.com/read/cv29054886/) - RTHandle 用法参考

**验证记录**：

- [2026-02-07] 从 Unity_URP_Learning 仓库整合，实际项目运行验证

**相关经验**：

- [URP Renderer Feature 开发要点](./urp.md#urp-renderer-feature-开发要点) — 通用 RenderFeature 模式
- [URP 中 GrabPass 替代方案](./urp.md#grab-color-renderfeature) — 依赖 GrabColor 功能

**理论基础**：

- [Renderer Feature 的要点](../../knowledge/unity/urp.md#renderer-feature-的要点)

---

## 屏幕空间刘海阴影 SSHS RenderFeature {#sshs-renderfeature}

**收录日期**：2026-02-07
**来源日期**：2024-08-08
**标签**：#RenderFeature #刘海阴影 #NPR #屏幕空间 #卡通渲染 #URP
**状态**：✅ 已验证
**适用版本**：Unity 2022.3+ / URP 14.0+

**问题/场景**：

在 NPR 卡通渲染中，需要实现屏幕空间的刘海在脸上的投影效果（Screen Space Hair Shadow），利用 RenderFeature 将头发的深度信息投射到脸部区域。

**解决方案/结论**：

### 1. 整体思路

利用自定义 RenderFeature 在渲染不透明物体之前：
1. 先将脸部模型的深度写入自定义 RT（`_HairSoildColor`）
2. 再将头发模型的深度/颜色叠加写入同一 RT
3. 后续渲染阶段中，脸部 Shader 采样此 RT 实现阴影效果

### 2. 多 Layer + 多 Pass 分离

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

### 3. 配套 Shader (SSHS.shader)

三个 Pass 分别处理不同功能：
- **FaceDepthOnly**：仅写深度 (`ColorMask 0, ZWrite On`)
- **HairSimpleColor**：输出头发深度到颜色 (`return float4(1, depth, 0, 1)`)
- **DepthMaskColor**：输出纯色遮罩 (`return float4(1, 0, 0, 1)`)

### 4. 关键踩坑点

- 注意 `ConfigureTarget` + `ConfigureClear` 在 `OnCameraSetup` 中设置
- 临时 RT 需在 `OnCameraCleanup` 中释放
- 使用 `ShaderTagId` 匹配 Pass 的 `LightMode` 标签

**参考链接**：

- [Unity_URP_Learning/RenderFeature](https://github.com/KTSAMA001/Unity_URP_Learning/tree/main/Assets/Products/RenderFeature) - 完整源码

**验证记录**：

- [2026-02-07] 从 Unity_URP_Learning 仓库整合

**相关经验**：

- [屏幕空间描边 SSOutLine RenderFeature](#ss-outline-renderfeature) — 类似的 RenderFeature 模式

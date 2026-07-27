# VR 静态云天空与动态闪电的分离合成

**标签**：#unity #shader #vr #rendering #experience
**来源**：方案设计与 Unity Shader 实践总结；Unity XR Single-Pass Instanced/Multiview 规范
**收录日期**：2026-07-27
**来源日期**：2026-07-27
**状态**：⚠️ 待验证
**可信度**：⭐⭐⭐（Shader 编译与桌面视角验证通过，尚缺目标头显真机双眼和动态闪电回归）
**适用版本**：Unity 2021.3+；OpenXR/Meta XR 的 Single-Pass Instanced 或 Multiview

### 概要

云形静态而闪电动态时，不应把闪电时序烘进基础天空。基础半八面体纹理只保存无闪电云层；闪电保存为同映射下的场景线性能量增量和区域控制，运行时按闪烁曲线合成。VR 两眼共享同一组天空纹理，Shader 只为每眼建立正确的裁剪空间和渲染层，不复制天空资源。

### 内容

#### 数据职责分离

推荐把数据分成：

- `BaseSky(direction)`：无闪电、包含静态云和静态太阳的场景线性天空。
- `LightningDelta(direction)`：闪电照亮云层后相对基础天空增加的能量，而不是一张已经 Tone Mapping 的完整天空。
- `RegionMask(direction)`：控制多个闪电区域的空间范围。
- `FlashCurve(t)`：运行时的快速上升、衰减、复闪和随机时序。

应先在线性 HDR 空间合成，再做 Tone Mapping：

```text
skyLinear = baseSky + lightningDelta * regionMask * flashCurve
output = ToneMap(skyLinear)
```

如果先把两张图各自压成 LDR 再混合，高亮很容易剪白，云后透光也会失去能量关系。

#### 两种运行时方案

##### 方案 A：严格一次采样、受限但便宜

基础 LogRGB 使用 RGB，Alpha 保存一个标量闪电透光/能量 Mask。运行时用统一闪电颜色和程序化方向区域控制多个位置：

- 优点：平时和闪电时都只采同一张纹理一次。
- 缺点：只有一个标量能量通道，多区域不能完全独立保存不同颜色和复杂光照增量；区域重叠时控制能力有限。

适用于固定闪电色、闪电位置相互分离、重点追求最低采样成本的移动 VR。

##### 方案 B：基础纹理 + 闪电增量纹理

第二张半八面体纹理保存 RGB 闪电能量增量，可在一张图中烘焙多处候选闪电，再用程序化角域 Mask 选择区域。

- 平静天气使用只采基础纹理的材质/Shader 变体。
- 闪电发生时切换到额外采样增量纹理的材质。
- 优点：颜色、云内散射和多处闪电的还原更好。
- 缺点：闪电期间每眼增加一次纹理采样；如果用普通动态分支，编译器/GPU 未必能省掉未走分支的采样，使用独立材质或明确变体更可靠。

对于闪电事件稀疏的场景，方案 B 的平均成本通常可控，也是更容易获得高质量“云后发光透出”效果的方案。

#### 闪电区域 Mask

半八面体 UV 可直接用于预烘焙 Mask，但运行时按世界方向做球面角域判断更稳定：

```hlsl
float AngularRegionMask(float3 direction, float3 centerDirection, float radiusRadians)
{
    float angle = acos(clamp(dot(direction, centerDirection), -1.0, 1.0));
    return 1.0 - smoothstep(radiusRadians * 0.75, radiusRadians, angle);
}
```

多区域可分别乘独立闪烁曲线，再取最大值或做能量相加。需要避免在半八面体正方形 UV 上直接用普通圆形距离，因为映射不同位置的角尺度不均匀。

#### VR 双眼适配

天空方向和纹理内容对双眼相同，不需要左右眼纹理。运行时 Shader 需要补齐 Unity Stereo/Instancing 宏：

```hlsl
struct Attributes
{
    float4 positionOS : POSITION;
    UNITY_VERTEX_INPUT_INSTANCE_ID
};

struct Varyings
{
    float4 positionCS : SV_POSITION;
    float3 direction : TEXCOORD0;
    UNITY_VERTEX_OUTPUT_STEREO
};

Varyings Vert(Attributes input)
{
    Varyings output;
    UNITY_SETUP_INSTANCE_ID(input);
    UNITY_INITIALIZE_OUTPUT(Varyings, output);
    UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(output);
    output.positionCS = UnityObjectToClipPos(input.positionOS);
    output.direction = input.positionOS.xyz;
    return output;
}

float4 Frag(Varyings input) : SV_Target
{
    UNITY_SETUP_STEREO_EYE_INDEX_POST_VERTEX(input);
    // 左右眼使用同一 direction->UV 公式和同一纹理资源。
}
```

同时使用 `#pragma multi_compile_instancing`。这解决的是每眼矩阵、实例 ID 和渲染层路由，不会自动保证项目的 Shader Variant 收集/剔除策略正确。

#### 真机验证清单

1. Quest Multiview 与 PCVR Single-Pass Instanced 至少各验证一次目标路径。
2. 检查左右眼太阳、云边和半八面体地平线是否完全同向，无单眼丢失。
3. 检查 Shader Variant 构建后仍保留 `STEREO_MULTIVIEW_ON` / `STEREO_INSTANCING_ON` 相关变体。
4. 闪电高亮在线性空间合成后再 Tone Mapping，检查是否出现单眼剪白或色带。
5. 使用 GPU Profiler/RenderDoc 确认平静材质没有意外执行闪电增量采样。

### 参考链接

- [Unity: Single-pass instanced rendering and custom shaders](https://docs.unity3d.com/Manual/SinglePassInstancing.html) - 自定义 Shader 的 Stereo/Instancing 宏。
- [Unity: Single-pass stereo rendering](https://docs.unity3d.com/Manual/SinglePassStereoRendering.html) - Unity XR 单通道立体渲染背景。

### 相关记录

- [半八面体单图 HDR 天空的编码、采样与色带治理](./hemi-octahedral-hdr-sky-texture.md) - 基础天空和闪电增量共用的方向编码。
- [VR 相机壳体特效：不使用后处理的全屏替代方案](./vr-camera-shell-effects-without-post-processing.md) - 移动 VR 中避免全屏后处理的相关取舍。
- [VR Shader 变体收集器架构](./vr-variant-collector-architecture.md) - Multiview/Instancing 变体保留与预热。

### 验证记录

- [2026-07-27] 静态基础天空的 VR Stereo/Instancing 宏已加入运行时 Shader，Unity ShaderUtil 返回 0 条编译消息；左右眼共享单张纹理的结构已完成。动态闪电增量纹理、区域时序和目标头显双眼效果尚未实现与真机验证，因此保留“待验证”状态。

---

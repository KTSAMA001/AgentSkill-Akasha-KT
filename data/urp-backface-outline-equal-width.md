# URP 反面外扩描边的裁剪空间等宽改造经验

**标签**：#shader #unity #experience #urp #npr #renderer-feature #hlsl
**来源**：项目实践整理；参考阿卡西记录 [少前2-PBR+NPR角色渲染笔记](./zhihu-pbr-npr-character-rendering.md)
**来源日期**：2026-07-07
**收录日期**：2026-07-07
**更新日期**：2026-07-07
**状态**：⚠️ 待验证
**可信度**：⭐⭐⭐（源码层改造和静态检查通过；Unity 导入、材质回归和真机画面仍需验证）
**适用版本**：Unity 2022.3+ / URP 14+；反面外扩描边；平滑法线可写入 TANGENT 或其他顶点通道

### 概要

反面外扩描边想获得稳定屏幕宽度时，不应再用世界距离、NDC 深度、衰减和最大宽度等经验参数互相抵消，而应直接在裁剪空间按 `clipW` 放大 XY 偏移，以抵消透视除法造成的近大远小。远距离仍建议保留一个 `MaxPerspectiveConstrain` 上限，让超远物体回到透视变细，避免小物体整块变成描边色。

### 内容

#### 适用场景

该经验适用于“反面剔除 + 顶点沿平滑法线外扩”的角色描边。顶点通道中需要有可连续的平滑法线；如果项目把平滑法线写在 `TANGENT.xyz`，顶点阶段应把 `TANGENT` 当作描边法线使用，而不是当作普通切线使用。

旧实现常见写法是：先把顶点沿相机方向或法线方向移动，再把裁剪空间顶点转成 NDC/屏幕坐标，然后叠加一组由 `distance`、`posCS.w`、`depthFactor`、`distanceAttenuation`、`DistanceScale`、`MaxOutline` 共同决定的屏幕偏移。这个做法能在某个距离段“看起来差不多等宽”，但本质是用多个非线性因素抵消透视变化，离开调参距离后就会出现近处、远处宽度不一致，甚至深度推移影响描边位置的问题。

#### 推荐实现

核心做法是在裁剪空间中偏移 `posCS.xy`：

1. `positionOS` 先转世界，再转裁剪空间，得到 `posCS`。
2. 平滑法线转世界后，用 `UNITY_MATRIX_VP` 当方向变换到裁剪空间方向。
3. 归一化前先把 X 乘以屏幕宽高比，归一化后再除回去，避免宽屏下描边横向拉伸或压扁。
4. 偏移量乘以当前顶点的 `clipW`，这样透视除法后屏幕宽度保持稳定。
5. 对 `clipW` 只做远端上限限制，避免极远处仍保持同样屏幕宽度导致模型被描边色糊成一团。
6. “往里推”只改 `posCS.z`，不要再移动世界坐标或 `xy`，否则深度修正会污染描边宽度和位置。

#### 参数语义

- `_Thickness`：描边基础宽度。它不是直接像素值，而是进入 `width = _Thickness * 0.001` 后参与裁剪空间偏移的艺术参数。
- `_Correction`：深度修正量，只用于把描边顶点写入更深的 clip/zBuffer 位置，隐藏正面刘海、眼眶、嘴部等内部杂线；它不应该参与 `xy` 外扩。
- `_MaxPerspectiveConstrain`：远距离等宽上限。小于该上限的距离段近似等宽；超过后不再继续按真实 `clipW` 放大，描边会随透视逐渐变细，从而避免远处小物体整块变成描边色。
- `_MinPerspectiveConstrain`：通常可先移除。近端最小值会强行放大近相机物体的 `clipW` 下限，容易让“等宽”语义变成另一种调参补偿；只有确认近裁剪附近描边过细且确实需要艺术保护时再加回。
- `_DistanceScale`、`_MaxOutline`：属于旧算法的拟合参数。迁移到裁剪空间等宽后不应继续作为主算法参数保留，可以放到 legacy 对比 shader 中做 A/B。

#### 为什么旧算法做不到真正等宽

真正的等宽关键是：顶点最终经过 `ndc.xy = clip.xy / clip.w`，所以如果希望屏幕上的偏移不随距离变化，写入 `clip.xy` 的偏移必须与 `clip.w` 同步放大。

旧算法没有直接利用这个透视关系，而是混合了几类量：

- 世界空间距离 `distance` 不等价于裁剪空间 `w`，尤其在相机投影、视角和物体位置变化时会出现偏差。
- `ndc.z` 或深度因子是投影后的非线性量，把它乘进宽度会让近远变化更难预测。
- `distanceAttenuation` 和 `DistanceScale` 是互相拉扯的经验项，一个试图随距离放大，一个又试图随距离衰减。
- `MaxOutline` 只能截断过宽结果，不能保证截断前后的宽度连续或正确。
- 若缺少 aspect 修正，法线方向在宽屏下归一化会破坏投影矩阵已经包含的横向比例。
- 如果“往里推”通过移动世界坐标实现，会改变后续距离、深度和投影位置，导致深度修正反过来影响宽度。

因此旧算法只能通过参数拟合某个视距范围，在远近变化、FOV 变化、宽高比变化或模型局部法线变化时仍会露出宽度不一致的问题。

#### 维护建议

主实现中只保留 `_Thickness`、`_Correction`、`_MaxPerspectiveConstrain` 这三个实际语义清晰的参数；若需要对比或回滚，可以额外保存一份完整 legacy shader。legacy shader 不应 include 新的核心描边函数，否则后续公共 include 更新会让对比基准失效。

在 VR/XR 或 Single Pass Instanced 场景里，最终仍需要用目标设备验证 `_ScreenParams`、投影矩阵和材质实例参数是否符合预期。源码层静态检查只能确认公式、属性名和调用签名一致，不能替代 Unity Shader 编译和画面回归。

### 关键代码

```hlsl
float4 CalculateOutlinePosition(
    float3 positionOS,
    float3 smoothNormalOS,
    float thickness,
    float correction,
    float maxPerspectiveConstrain)
{
    float3 positionWS = TransformObjectToWorld(positionOS);
    float3 normalWS = normalize(TransformObjectToWorldNormal(smoothNormalOS));
    float4 posCS = TransformWorldToHClip(positionWS);

    float4 normalCS = mul(UNITY_MATRIX_VP, float4(normalWS, 0.0));
    float aspect = _ScreenParams.x / max(_ScreenParams.y, 1.0);
    float2 outlineDirCS = normalCS.xy;
    outlineDirCS.x *= aspect;
    float outlineLenSq = dot(outlineDirCS, outlineDirCS);
    outlineDirCS = outlineLenSq > 1e-6 ? outlineDirCS * rsqrt(outlineLenSq) : float2(0.0, 0.0);
    outlineDirCS.x /= aspect;

    float constrainedClipW = min(posCS.w, max(maxPerspectiveConstrain, 1e-4));
    posCS.xy += outlineDirCS * max(thickness, 0.0) * 0.001 * constrainedClipW;

    if (correction > 0.0)
    {
        float targetDepth = max(posCS.w + correction, 1e-4);
        float targetClipZ = -targetDepth * UNITY_MATRIX_P[2][2] + UNITY_MATRIX_P[2][3];
        float targetNdcZ = targetClipZ / targetDepth;
        posCS.z = targetNdcZ * posCS.w;
    }

    return posCS;
}
```

如果模型存在法线方向退化，实际工程代码可在 `normalize(outlineDirCS)` 前加长度保护，避免零向量归一化产生异常。

### 参考链接

- [少前2-PBR+NPR角色渲染笔记](./zhihu-pbr-npr-character-rendering.md) - 原始外部文章的本地留档，其中“6：描边”记录了 `clipW` 等宽描边、aspect 修正和深度修正思路。

### 相关记录

- [URP 屏幕空间描边 RenderFeature 实现](./urp-renderfeature-screen-space-outline.md) - 另一条屏幕空间描边路线，适合与反面外扩路线对比。
- [深度偏移边缘光](./depth-offset-rim-light.md) - 同一篇少前2文章中的等宽边缘光与深度对比思路。
- [Amplify Shader Editor 架构与实现机制解析](./amplify-shader-editor-architecture.md) - 如果描边 shader 由 ASE 管理，需要注意 shader 文件尾部图数据与生成代码的关系。

### 验证记录

- [2026-07-07] 初次记录。来源为一次 Unity URP 反面外扩描边实践整理；已完成阿卡西 `git pull origin main`、重复检测和写入前结构校验。工程侧完成源码层静态检查，但未完成 Unity Editor 导入编译、材质 Inspector 回归和 VR 设备画面验证，因此状态保持为待验证。



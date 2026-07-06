# 深度偏移边缘光

**标签**：#graphics #shader #npr #post-processing #knowledge
**来源**：[少前2-PBR+NPR角色渲染笔记 - 知乎](https://zhuanlan.zhihu.com/p/2054250788315255997)
**收录日期**：2026-07-06
**来源日期**：2026-01（文章发布月份，精确日期未知）
**更新日期**：2026-07-06
**状态**：⚠️ 待验证
**可信度**：⭐⭐⭐（社区实践，文章已公开发布，未亲自验证）
**适用版本**：Unity URP / 任何支持深度图采样和视图空间法线的渲染管线

### 概要

基于**视图空间法线 XY 外拓 + 深度图对比**的屏幕空间边缘光方法。核心思路：在视图空间沿法线 XY 方向偏移顶点位置，采样深度图获取偏移点的深度，与原始顶点深度做对比——深度差大于阈值即为边缘。相比传统 NdotV 边缘光，该方法**以实际几何遮挡关系判定边缘**，能避免法线方向导致的内部轮廓误触发，且宽度在屏幕空间保持一致。

### 内容

---

## 一、原理

### 核心思路

边缘光不看法线角度，看几何遮挡——"这个像素是否在物体的几何边缘处？"

在视图空间中，法线的 **XY 分量**恰好指向物体的"外侧"方向。沿法线 XY 偏移一小段距离后，去采样深度图中的实际深度，通过深度差判断是否在边缘：

| 对比维度 | 🟢 内部像素 | 🔴 边缘像素 |
|---------|------------|------------|
| **几何位置** | 物体内部，四周被同一物体包围 | 物体轮廓处，一侧是物体、另一侧是背景 |
| **法线 XY 方向** | 指向相邻的同一物体表面 | 指向物体外侧（背景或远处物体） |
| **偏移后采样点落在** | 同一物体上 | 背景 / 其他远处物体上 |
| **偏移点深度 vs 原始深度** | `offsetDepth ≈ ndcW`（几乎相等） | `offsetDepth >> ndcW`（偏移点远得多） |
| **深度差** | ≈ 0 | >> 阈值 |
| **判定结果** | 不是边缘 → `rimMask = 0` | **是边缘** → `rimMask = 1` |

> **一句话**：法线在视图空间 XY 的指向就是"物体外侧的方向"，外拓后如果深度突然变远，说明已经"掉出"了物体——这正好说明原始像素在物体的几何边缘上。

### 为什么只偏移 XY、不移 Z？

视图空间中：XY 平面 = 屏幕横纵方向，Z = 深度方向。法线 XY 分量正是物体在屏幕平面上"向外"的方向。如果同时偏移 Z，会改变采样距离从而引入非边缘因素的深度差异，破坏判定准确性。

---

## 二、实现步骤

### 第 1 步：获取视图空间法线

```hlsl
half3 N_VS = TransformWorldToViewNormal(N);
```

### 第 2 步：沿法线 XY 方向偏移顶点位置

```hlsl
float3 offsetPositionVS = float3(
    positionVS.xy + N_VS.xy * (_RimLightWidth / 100.0),
    positionVS.z   // Z 不变
);
```

`_RimLightWidth` 控制偏移距离，即边缘光的宽度。

### 第 3 步：投影偏移点到屏幕空间

```hlsl
float4 offsetPositionCS  = TransformWViewToHClip(offsetPositionVS);
float4 offsetPositionNDC = offsetPositionCS * 0.5;
offsetPositionNDC.xy = float2(
    offsetPositionNDC.x,
    offsetPositionNDC.y * _ProjectionParams.x   // 平台差异 Y 翻转
) + offsetPositionNDC.w;
offsetPositionNDC.zw = offsetPositionCS.zw;
float2 offsetScreenPos = offsetPositionNDC.xy / offsetPositionNDC.w;
```

目的：拿到偏移后的屏幕 UV 坐标，用于采样 `_CameraDepthTexture`。

### 第 4 步：采样深度 + 对比

```hlsl
float offsetDepth = SAMPLE_TEXTURE2D(
    _CameraDepthTexture, sampler_CameraDepthTexture, offsetScreenPos
).r;
float offsetLinearEyeDepth = LinearEyeDepth(offsetDepth, _ZBufferParams);
float depthDifference = offsetLinearEyeDepth - ndcW;
// ndcW = 当前顶点 clipSpace.w = 当前顶点的视图空间深度
```

对比结果：

| 场景 | offsetLinearEyeDepth | ndcW | depthDifference | 结论 |
|------|---------------------|------|:---:|------|
| 内部像素 | ≈ ndcW | 当前深度 | ≈ 0 | 不是边缘 |
| 边缘像素 | 背景深度（远） | 当前深度（近） | > 阈值 | **是边缘** ✅ |

### 第 5 步：smoothstep 出边缘 Mask

```hlsl
float rimMask = smoothstep(0, _RimLightThreshold / 100.0, depthDifference);
```

`_RimLightThreshold` 控制判定为边缘的最小深度差，小于阈值不发光，大于阈值平滑过渡。

### 第 6 步（可选）：受光面判定

```hlsl
float NoL = saturate(dot(light.direction, N));
float lightMask = pow(NoL, _LightMaskPow_Rim);
rimMask = lerp(0.0, rimMask, lightMask);
```

仅在受光面显示边缘光，背光面边缘光消失，更符合物理直觉。

---

## 三、与传统 NdotV 方案的对比

| 维度 | 传统 NdotV Rim | 深度偏移 Rim |
|------|:---:|:---:|
| 判定依据 | 法线角度（NdotV） | 实际几何遮挡（深度差） |
| 内部轮廓误触发 | ❌ 常见（凹面也会亮） | ✅ 不会（内部无深度差） |
| 边缘宽度一致性 | ❌ 依赖法线分布 | ✅ 屏幕空间等宽 |
| 对法线质量的敏感度 | 高（broken normal 导致断裂） | 低（深度图 > 法线） |
| 实现复杂度 | 极简（一行） | 中等（需深度图采样 + 多次坐标变换） |
| 适用场景 | 简单特效、快速原型 | 高品质角色渲染、要求精确边缘 |

---

## 四、注意事项

1. **深度图必须可用**：URP 需开启 `Depth Texture`（在 Universal Render Pipeline Asset 中勾选）
2. **偏移距离适度**：`_RimLightWidth` 过大可能导致相邻物体被误判为背景；过小则边缘光太窄
3. **背景像素**：如果偏移后采样到天空盒（远裁面），`LinearEyeDepth` 会返回特大值，自然被判定为边缘，这是预期行为
4. **半透明物体**：需注意深度图中半透明物体可能不写入深度，导致采样穿透
5. **宽高比修正**：如果需要严格等宽，应在法线变换时做 aspect 修正（类似描边处理），本方案为简化版本未包含

---

### 参考链接

- [少前2-PBR+NPR角色渲染笔记](https://zhuanlan.zhihu.com/p/2054250788315255997) — 原始文章
- [仿原神卡通渲染：NDC简介与等宽屏幕空间边缘光原理](https://zhuanlan.zhihu.com/p/165316070) — 文章中引用的参考资料

### 相关记录

- [SDF 有符号距离场](./sdf-signed-distance-field.md) — 脸部 SDF 阴影/高光，同属 NPR 渲染技术栈

### 验证记录

- [2026-07-06] 初次记录，来源：知乎专栏《少前2-PBR+NPR角色渲染笔记》分析整理

# 基于图像的间接光照 IBL

**标签**：#graphics #knowledge #pbr #brdf #cook-torrance
**来源**：Unity_URP_Learning 仓库实践 + Unity 官方文档
**来源日期**：2024-08-08
**收录日期**：2026-02-07
**更新日期**：2026-06-13
**状态**：📘 有效
**可信度**：⭐⭐⭐⭐ (实践验证)

### 概要

Image-Based Lighting 使用环境贴图提供间接漫反射与间接镜面反射，常与预过滤 Reflection Probe 和 BRDF LUT 近似结合。

### 内容

Image-Based Lighting (IBL) 使用环境贴图作为光源，为物体提供间接光照（漫反射 + 镜面反射）。

#### 间接漫反射

通过球谐函数 (Spherical Harmonics) 采样环境光：

```hlsl
float3 diffuse_InDirect = SampleSH(N) * albedo * kd;
```

#### 间接镜面反射

使用预过滤的环境贴图（Reflection Probe）+ 预计算的 BRDF LUT：

```hlsl
// 根据粗糙度选择 mip 级别
float mip = roughness * (1.7 - 0.7 * roughness) * UNITY_SPECCUBE_LOD_STEPS;

// 采样反射探针
float4 cubeMapColor = SAMPLE_TEXTURECUBE_LOD(unity_SpecCube0,
    samplerunity_SpecCube0, reflectDirWS, mip);
float3 envSpecular = DecodeHDREnvironment(cubeMapColor, unity_SpecCube0_HDR);

// BRDF 近似（UE4 Black Ops II 方法）
float2 env_brdf = EnvBRDFApprox(roughness, NV);
float3 specular_InDirect = envSpecular * (F * env_brdf.r + env_brdf.g);
```

关键点：

- `mip = roughness * (1.7 - 0.7*roughness) * UNITY_SPECCUBE_LOD_STEPS` 将粗糙度映射到 mip 级别。
- `FresnelSchlickRoughness` 需额外考虑粗糙度对菲涅尔的影响。
- `EnvBRDFApprox` 是 UE4 提出的高效 BRDF 查找表近似方法。
- 草渲染等特殊情况下，可在暗部添加 `pow(diffuse, lerp(0.8,1,...))` 防止纯黑。

### 关键代码

见“间接漫反射”和“间接镜面反射”中的 HLSL 片段。

### 相关记录

- [Cook-Torrance BRDF 模型](./pbr-cook-torrance-brdf-theory.md) - IBL 中的镜面项仍基于 BRDF 近似。

### 验证记录

- [2026-04-15] 结构修复：补齐模板必填章节，未改动原结论。
- [2026-06-13] 结构维护：从旧聚合记录拆分，未重新验证原技术结论。

# 基于物理的渲染（Physically Based Rendering）相关原理与概念

> 基于物理的渲染（Physically Based Rendering）相关原理与概念

---

## Cook-Torrance BRDF 模型 {#cook-torrance-brdf}

**标签**：#graphics #knowledge #pbr #brdf #cook-torrance
**来源**：Unity_URP_Learning 仓库实践 + 学术论文
**来源日期**：2024-08-08
**收录日期**：2026-02-07
**可信度**：⭐⭐⭐⭐⭐ (学术论文 + 实践验证)
**状态**：📘 有效

### 定义/概念

PBR 的核心公式为 **反射率方程 (Reflectance Equation)**：

```
Lo(p, ωo) = ∫ fr(p, ωi, ωo) · Li(p, ωi) · (n · ωi) dωi
```

其中 `fr` 为 BRDF 函数。Cook-Torrance BRDF 将反射分为**漫反射项**和**镜面反射项**：

```
fr = kd · f_lambert + ks · f_cook-torrance
```

- `f_lambert = albedo / π`（朗伯漫反射）
- `f_cook-torrance = D · G · F / (4 · (N·V) · (N·L))`

### 原理/详解

#### D - 正态分布函数 (Normal Distribution Function)

使用 **GGX/Trowbridge-Reitz** 分布，描述微表面法线的统计分布：

```hlsl
float D_DistributionGGX(float3 N, float3 H, float Roughness)
{
    float a = Roughness * Roughness;
    float a2 = a * a;
    float NH = saturate(dot(N, H));
    float NH2 = NH * NH;
    float nominator = a2;
    float denominator = (NH2 * (a2 - 1.0) + 1.0);
    denominator = PI * denominator * denominator;
    return nominator / max(denominator, 0.00001);
}
```

**要点**：粗糙度越大，微平面法线分布越分散，高光越模糊。

#### G - 几何遮蔽函数 (Geometry Function)

使用 **Schlick-GGX** 近似，描述微表面的自遮蔽和自阴影：

```hlsl
// 直接光照 G 项（k = (r+1)²/8）
float GeometrySchlickGGX_D(float NV, float Roughness)
{
    float r = Roughness + 1.0;
    float k = r * r / 8;
    float nominator = NV;
    float denominator = k + (1.0 - k) * NV;
    return nominator / max(denominator, 0.00001);
}

// 间接光照 G 项（k = r²/2）
float GeometrySchlickGGX_I(float NV, float Roughness)
{
    float r = Roughness;
    float k = r * r / 2;
    float nominator = NV;
    float denominator = k + (1.0 - k) * NV;
    return nominator / max(denominator, 0.00001);
}
```

**Smith 方法**将 G 拆分为视线方向和光照方向两部分的乘积：

```hlsl
float G = GeometrySchlickGGX(NdotV, roughness) * GeometrySchlickGGX(NdotL, roughness);
```

**要点**：
- 直接光照与间接光照（IBL）使用**不同的 k 值**
- 直接光照 `k = (roughness + 1)² / 8`
- 间接光照 `k = roughness² / 2`

#### F - 菲涅尔方程 (Fresnel Equation)

使用 **Schlick 近似**，描述不同视角下反射与折射的比例：

```hlsl
float3 F_FresnelSchlick(float NV, float3 F0)
{
    return F0 + (1 - F0) * pow(1 - NV, 5);
}
```

**要点**：
- `F0` 为基础反射率：金属约 0.5~1.0，非金属统一约 0.04
- 掠射角（NV→0）时，所有材质反射率趋近 1.0

### 关键点

- PBR = 微表面理论 + 能量守恒 + 菲涅尔效应
- 直接光和间接光（IBL）使用不同的 G 项参数
- ACES ToneMapping 用于将 HDR 结果映射到 LDR 显示范围
- `F0 = lerp(0.04, albedo, metallic)` 统一金属与非金属工作流
- 防止分母为零：所有除法都应使用 `max(denominator, 0.00001)`

### 示例

完整的直接光 PBR 计算：

```hlsl
float3 PBR_Direct_Light(float3 albedo, Light lightData, float3 N, float3 V,
                        float metallic, float roughness, float ao)
{
    float3 L = normalize(lightData.direction);
    float3 F0 = lerp(0.04, albedo, metallic);
    float3 H = normalize(V + L);
    float NV = saturate(dot(N, V));
    float NL = saturate(dot(N, L));

    float  D = D_DistributionGGX(N, H, roughness);
    float  G = G_GeometrySmith_Direct_Light(N, V, L, roughness);
    float3 F = F_FresnelSchlick(NV, F0);

    float3 kd = (1 - F) * (1 - metallic);
    float3 diffuse  = (kd * albedo) / PI;
    float3 specular = (D * G * F) / (4 * max(NV * NL, 0.000001));

    return (diffuse + specular) * NL * lightData.color * ao;
}
```

### 相关知识

- [渲染管线基础](./rendering-pipeline-overview.md)
- [色彩空间](./color-space-gamma-linear.md)
- [HLSL 语法](./hlsl-syntax-semantics.md)

### 与经验关联

- 实践验证：[自定义 PBR Shader 在 URP 中的实现](./pbr-custom-shader-urp.md#custom-pbr-urp) — 基于此理论的完整 URP 实现
- 实践验证：[GPU 草渲染 PBR 光照](./gpu-grass-large-scale-rendering.md#gpu-grass-compute-shader) — 草渲染中的 PBR 变体

---

## 间接光照与 IBL {#ibl}

**标签**：#graphics #knowledge #pbr #brdf #cook-torrance
**来源**：Unity_URP_Learning 仓库实践 + Unity 官方文档
**来源日期**：2024-08-08
**收录日期**：2026-02-07
**可信度**：⭐⭐⭐⭐ (实践验证)
**状态**：📘 有效

### 定义/概念

Image-Based Lighting (IBL) 使用环境贴图作为光源，为物体提供间接光照（漫反射 + 镜面反射）。

### 原理/详解

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

### 关键点

- `mip = roughness * (1.7 - 0.7*roughness) * UNITY_SPECCUBE_LOD_STEPS` 将粗糙度映射到 mip 级别
- `FresnelSchlickRoughness` 需额外考虑粗糙度对菲涅尔的影响
- `EnvBRDFApprox` 是 UE4 提出的高效 BRDF 查找表近似方法
- 草渲染等特殊情况下，可在暗部添加 `pow(diffuse, lerp(0.8,1,...))` 防止纯黑

### 相关知识

- [Cook-Torrance BRDF 模型](#cook-torrance-brdf)

---

## ACES Tone Mapping {#aces-tonemapping}

**标签**：#graphics #knowledge #pbr #brdf #cook-torrance
**来源**：Unity_URP_Learning 仓库 / ACES 标准
**来源日期**：2024-08-08
**收录日期**：2026-02-07
**可信度**：⭐⭐⭐⭐⭐ (工业标准)
**状态**：📘 有效

### 定义/概念

ACES (Academy Color Encoding System) Tone Mapping 是一种将 HDR 渲染结果映射到 LDR 显示范围的色调映射函数。

### 原理/详解

```hlsl
float3 ACESToneMapping(float3 x)
{
    float a = 2.51;
    float b = 0.03;
    float c = 2.43;
    float d = 0.59;
    float e = 0.14;
    return saturate((x * (a * x + b)) / (x * (c * x + d) + e));
}
```

### 关键点

- 拟合曲线近似电影工业中的 ACES RRT+ODT 变换
- 自带 `saturate` 保证输出在 [0,1] 范围
- 保留暗部细节同时压缩高光区域
- 已被广泛用于游戏和影视行业

### 相关知识

- [色带与抖动](./color-banding-dither.md)
- [色彩空间](./color-space-gamma-linear.md)

---

# Cook-Torrance BRDF 模型

**标签**：#graphics #knowledge #pbr #brdf #cook-torrance
**来源**：Unity_URP_Learning 仓库实践 + 学术论文
**来源日期**：2024-08-08
**收录日期**：2026-02-07
**更新日期**：2026-06-13
**状态**：📘 有效
**可信度**：⭐⭐⭐⭐⭐ (学术论文 + 实践验证)

### 概要

Cook-Torrance BRDF 将 PBR 反射拆为漫反射项与微表面镜面反射项，通过 D/G/F 三项描述法线分布、几何遮蔽和菲涅尔效应。

### 内容

PBR 的核心公式为 **反射率方程 (Reflectance Equation)**：

```text
Lo(p, ωo) = ∫ fr(p, ωi, ωo) · Li(p, ωi) · (n · ωi) dωi
```

其中 `fr` 为 BRDF 函数。Cook-Torrance BRDF 将反射分为**漫反射项**和**镜面反射项**：

```text
fr = kd · f_lambert + ks · f_cook-torrance
```

- `f_lambert = albedo / π`（朗伯漫反射）
- `f_cook-torrance = D · G · F / (4 · (N·V) · (N·L))`

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

粗糙度越大，微平面法线分布越分散，高光越模糊。

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

关键区别：

- 直接光照与间接光照（IBL）使用不同的 k 值。
- 直接光照 `k = (roughness + 1)² / 8`。
- 间接光照 `k = roughness² / 2`。

#### F - 菲涅尔方程 (Fresnel Equation)

使用 **Schlick 近似**，描述不同视角下反射与折射的比例：

```hlsl
float3 F_FresnelSchlick(float NV, float3 F0)
{
    return F0 + (1 - F0) * pow(1 - NV, 5);
}
```

关键点：

- `F0` 为基础反射率：金属约 0.5 到 1.0，非金属统一约 0.04。
- 掠射角（`NV` 趋近 0）时，所有材质反射率趋近 1.0。
- `F0 = lerp(0.04, albedo, metallic)` 可统一金属与非金属工作流。
- 防止分母为零：所有除法都应使用 `max(denominator, 0.00001)` 或相近保护值。

### 关键代码

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

### 相关记录

- [基于图像的间接光照 IBL](./pbr-image-based-lighting-ibl.md) - Cook-Torrance 间接光照的环境贴图侧实现。
- [渲染管线基础](./rendering-pipeline-stages.md) - PBR 所在的整体渲染管线上下文。
- [色彩空间](./color-space-gamma-linear.md) - PBR 计算涉及的 Gamma/Linear 色彩空间基础。
- [HLSL 语法](./hlsl-semantics-basics.md) - 代码片段使用的 HLSL 基础。
- [自定义 PBR Shader 在 URP 中的实现](./pbr-custom-shader-urp.md#custom-pbr-urp) - 基于此理论的完整 URP 实现。
- [GPU 草渲染 PBR 光照](./gpu-grass-large-scale-rendering.md#gpu-grass-compute-shader) - 草渲染中的 PBR 变体。

### 验证记录

- [2026-04-15] 结构修复：补齐模板必填章节，未改动原结论。
- [2026-06-13] 结构维护：从旧聚合记录拆分，未重新验证原技术结论。

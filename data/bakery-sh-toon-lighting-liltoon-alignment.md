# Bakery SH 对齐 lilToon 的 Toon 化采样与暗部回填实践

**标签**：#unity #shader #graphics #urp #npr #hlsl #experience
**来源**：实践总结（已脱敏）
**收录日期**：2026-07-01
**来源日期**：2026-07-01
**更新日期**：2026-07-02
**状态**：⚠️ 待验证
**可信度**：⭐⭐⭐（已完成源码审查和 ShaderGraph 配置核对，尚未完成 Unity 重新导入/编译验证）
**适用版本**：Unity URP ShaderGraph + Bakery SH/RNM；具体 Unity 与 Bakery 版本未绑定

### 概要

在卡通渲染项目中，直接把 Bakery SH 按表面法线作为间接漫反射使用，容易把角色或场景的暗部推向连续、写实的 PBR 观感。实践方案是在原 `BakerySH_float` 外新增 Toon 包装层：仍复用 Bakery 的 SH 解码、Geomerics 亮度修正、非负 clamp 和抗振铃能力，但把采样方向改成“环境主方向 + 主光方向”的风格化方向，并拆分为亮侧补偿与暗部回填信号。

### 内容

#### 问题背景

- Bakery SH/RNM 提供了有方向性的烘焙环境光，直接用 `normalWorld` 采样会得到较连续的物理漫反射渐变。
- Toon/NPR 目标更重视可控色阶、阴影色板和主光明暗边界；因此 SH 不应直接决定最终颜色。
- 目标不是抛弃 Bakery SH，而是把 Bakery SH 转成 Toon 可用的“亮侧补偿”和“暗侧回填强度”。

#### 脱敏边界

本记录已脱敏处理：

- 不记录真实项目名、内部场景名、完整目录、分支名、截图临时路径、用户本机路径。
- 不记录 ShaderGraph 的 GUID、ObjectId、Slot ObjectId 等内部资产标识。
- 文件名只保留通用实现单元：`BakeryToonDecodeLightmap.hlsl`、`BakeryDecodeLightmap.hlsl`。
- ShaderGraph 只记录节点语义、端口名、默认值和连接关系，不记录资产内部序列化 ID。

#### 设计原则

1. **原 Bakery 解码不重写**：`BakerySH_float` 仍是唯一 SH 采样入口，避免丢失 Bakery 原有抗振铃和非负保护。
2. **不按最终表面法线直接采 SH**：先从 RNM/L1 或 Unity SH L1 估算环境主方向，再和主光方向合成 Toon 采样方向。
3. **对齐 lilToon 的正反方向采样思想**：正向采样作为亮侧环境补偿，反向采样作为暗侧环境回填。
4. **SH 只给强度，不接管色相**：阴影色仍由 Toon 色板或项目已有阴影逻辑决定。
5. **ShaderGraph 输出分级**：`toonLightSH` 和 `toonFillLuma` 是常规输出；`toonFillSH` 与 `toonDirectionWS` 更偏调试或高级接线。

#### 数据流

```text
Bakery L0 + RNM/L1 或 Unity SH L1
→ 估算环境主方向 envDir
→ 与主光方向 mainDir 按权重混合
→ directionScale 削弱方向性
→ BakerySH_float(正向采样) 得到 toonLightSH
→ BakerySH_float(反向采样) 得到 toonFillSH
→ toonFillSH 压成 toonFillLuma，作为暗部回填遮罩
```

#### ShaderGraph 节点配置（脱敏）

| 项 | 配置 |
|---|---|
| Custom Function 文件 | `BakeryToonDecodeLightmap.hlsl` |
| 函数名 | `BakeryToonSH`（ShaderGraph 填无精度后缀；实际 HLSL 函数为 `BakeryToonSH_float`） |
| 输入 | `L0`、`normalWorld`、`lightmapUV`、`mainLightDirWS`、`mainLightColor`、`directionScale`、`envDirectionWeight`、`mainDirectionWeight` |
| 输出 | `toonLightSH`、`toonFillSH`、`toonDirectionWS`、`toonFillLuma` |
| 主光连接 | `mainLightDirWS` 接主光方向，`mainLightColor` 接主光颜色 |
| 默认参数 | `directionScale = 0.666666`，`envDirectionWeight = 1.0`，`mainDirectionWeight = 1.0` |
| 常规接线建议 | `toonLightSH` 少量参与亮面补偿；`toonFillLuma` 接 Lerp/Remap/Smoothstep 做暗部回填遮罩 |
| 不建议直接使用 | `toonFillSH` 不直接当最终颜色；`toonDirectionWS` 是方向向量，通常只用于调试 |

#### 输出端口语义

| 输出 | 语义 | 推荐用法 | 直接接最终颜色的风险 |
|---|---|---|---|
| `toonLightSH` | 正向 Toon 采样得到的亮侧环境信号 | 少量加到亮面或主光强度 | 权重过大会让亮面被烘焙环境染色 |
| `toonFillSH` | 反向 Toon 采样得到的暗侧环境信号 | 可转亮度或做 RGB 回填强度 | 它仍是环境能量，不是美术阴影色 |
| `toonDirectionWS` | 环境方向与主光方向合成出的 Toon 采样方向 | 调试、方向可视化、高级 Rim/Spec 参考 | 它是方向，不是颜色 |
| `toonFillLuma` | `toonFillSH` 的非负亮度 | 作为 Lerp 的 `T` 或 Remap 输入 | 需要限制强度，否则暗部可能过亮 |

#### 注释版实现说明
#### BakeryToonDecodeLightmap.hlsl 注释版说明（脱敏，省略空行）

> 下面按代码出现顺序保留有实现语义的代码与预处理行；空行不再单独说明，纯结构花括号只保留代码本身。

```hlsl
// 说明：包含保护宏，防止该包装文件在同一 Shader 编译单元里重复展开。
#ifndef BAKERY_TOON_DECODE_LIGHTMAP_INCLUDED
#define BAKERY_TOON_DECODE_LIGHTMAP_INCLUDED
// 说明：引入原 Bakery 解码文件；设计取舍是复用原 BakerySH_float，不重写 SH 解码和抗振铃逻辑。
#include "BakeryDecodeLightmap.hlsl"
// Bakery SH 的卡通化包装层。
// 原始 BakerySH_float 仍然是唯一的 SH 采样入口，这样可以继续复用 Bakery 内部
// Geomerics 亮度修正和非负 clamp，避免把振铃/负光照问题重新引入卡通流程。
// 本文件只负责改造采样方向，并把采样结果整理成 Toon 光照需要的亮侧与暗侧信号。
// 所有归一化保护共用这个阈值，避免无方向环境光或黑光场景产生 NaN。
// 说明：定义安全阈值；后续 SafeNormalize 使用它判断向量长度是否可靠。
#define BAKERY_TOON_EPSILON 1e-6f
// 保留符号的亮度，用于从 RGB L1 系数中提取“方向性”；符号不能丢，否则环境主方向会被抹平。
// 说明：实现带符号亮度：使用 Rec.709 亮度权重从 RGB 中提取标量，同时保留负值方向信息。
float BakeryToonSignedLuminance(float3 color)
{
    // 说明：实现带符号亮度：使用 Rec.709 亮度权重从 RGB 中提取标量，同时保留负值方向信息。
    return dot(color, float3(0.2126729f, 0.7151522f, 0.0721750f));
}
// 非负亮度用于输出给 ShaderGraph 做暗部回填遮罩，避免负值影响 Lerp/Saturate 这类节点。
// 说明：实现非负亮度：先对 RGB 做 max(0)，再复用带符号亮度函数。
float BakeryToonPositiveLuminance(float3 color)
{
    // 说明：实现非负亮度：先对 RGB 做 max(0)，再复用带符号亮度函数。
    return BakeryToonSignedLuminance(max(color, float3(0.0f, 0.0f, 0.0f)));
}
// 带回退值的安全归一化。方向长度过小时回退到法线或默认向上方向，保证预览和极端光照下稳定。
// 说明：实现安全归一化：长度足够时用 rsqrt 归一化，长度过小时返回 fallback。
float3 BakeryToonSafeNormalize(float3 value, float3 fallback)
{
    // 说明：实现安全归一化：长度足够时用 rsqrt 归一化，长度过小时返回 fallback。
    float lenSq = dot(value, value);
    return lenSq > BAKERY_TOON_EPSILON ? value * rsqrt(lenSq) : fallback;
}
// 从 Bakery 的 RNM/L1 或 Unity Light Probe 的 L1 系数估算环境主方向。
// 这里不按表面法线直接取 SH，而是先得到一个“环境方向提示”，后续再和主光方向合成 Toon 采样方向。
// 说明：声明环境主方向估算函数；输入是 L0 和 lightmapUV，输出是用于 Toon 采样方向合成的方向提示。
float3 BakeryToonGetSHDirection(float3 L0, float2 lightmapUV)
{
// 说明：编译分支：存在烘焙 lightmap 时优先使用 Bakery RNM/L1 数据。
#ifdef LIGHTMAP_ON
    // 说明：从三张 RNM 纹理读取归一化 L1 方向分量，并从 0..1 还原到 -1..1。
    float3 nL1x = SAMPLERNM(_RNM0, lightmapUV).rgb * 2.0f - 1.0f;
    float3 nL1y = SAMPLERNM(_RNM1, lightmapUV).rgb * 2.0f - 1.0f;
    float3 nL1z = SAMPLERNM(_RNM2, lightmapUV).rgb * 2.0f - 1.0f;
    // 说明：按 BakerySH_float 的语义用 L0 放大重建 L1x/L1y/L1z，保留 Bakery 烘焙强度。
    float3 L1x = nL1x * L0 * 2.0f;
    float3 L1y = nL1y * L0 * 2.0f;
    float3 L1z = nL1z * L0 * 2.0f;
    // 将彩色 L1 合并成单一方向轴，但保留正负方向性。
    // 这一步复用 BakerySH_float 的 L1 重建语义，只是不在这里评估最终表面法线；
    // 卡通渲染会用后面合成出的风格化方向来采样。
    // 说明：返回环境方向提示：分别取 L1x/L1y/L1z 的带符号亮度作为方向向量三个分量。
    return float3(
        BakeryToonSignedLuminance(L1x),
        BakeryToonSignedLuminance(L1y),
        BakeryToonSignedLuminance(L1z)
    );
// 说明：编译分支：没有 lightmap 时进入 Unity Light Probe 回退路径。
#else
    // Light Probe 回退路径。Unity 将 RGB 三组 L1 分开存储，这里按亮度权重合成一个环境主方向。
    // 说明：用 unity_SHAr/Ag/Ab 三组 L1 按亮度权重合成环境主方向。
    return unity_SHAr.xyz * 0.2126729f
         + unity_SHAg.xyz * 0.7151522f
         + unity_SHAb.xyz * 0.0721750f;
// 说明：结束 LIGHTMAP_ON 条件编译。
#endif
}
// 合成 Toon SH 的采样方向。
// 环境方向提供场景归属感，主光方向提供卡通明暗的视觉主导；两个权重用于按项目美术需求调节占比。
// 说明：声明 ShaderGraph 可调用的 Toon 方向函数；输入包括 Bakery SH、主光和权重，输出合成方向与实际采样方向。
void BakeryToonDirection_float(
    float3 L0,
    float3 normalWorld,
    float2 lightmapUV,
    float3 mainLightDirWS,
    float3 mainLightColor,
    float directionScale,
    float envDirectionWeight,
    float mainDirectionWeight,
    out float3 toonDirectionWS,
    // 说明：声明 ShaderGraph 可调用的 Toon 方向函数；输入包括 Bakery SH、主光和权重，输出合成方向与实际采样方向。
    out float3 sampleDirectionWS)
{
    // 说明：把 normalWorld 归一化成 fallbackNormal；法线不可用时回退到世界向上。
    float3 fallbackNormal = BakeryToonSafeNormalize(normalWorld, float3(0.0f, 1.0f, 0.0f));
    // 说明：估算并安全归一化环境方向；环境方向无效时回退到 fallbackNormal。
    float3 envDir = BakeryToonSafeNormalize(BakeryToonGetSHDirection(L0, lightmapUV), fallbackNormal);
    // mainLightDirWS 使用 URP 的 surface-to-light 约定，也就是通常用于 dot(normalWS, light.direction) 的方向。
    // 说明：安全归一化主光方向；主光方向无效时回退到 fallbackNormal。
    float3 mainDir = BakeryToonSafeNormalize(mainLightDirWS, fallbackNormal);
    // 说明：计算主光亮度，并 clamp 到非负，避免负主光影响方向混合权重。
    float mainLum = max(BakeryToonSignedLuminance(mainLightColor), 0.0f);
    // 说明：将环境方向权重限制为非负，避免权重反相造成不可控方向。
    float envWeight = max(envDirectionWeight, 0.0f);
    // 说明：将主光权重限制为非负，并乘主光亮度，使主光越亮方向影响越明显。
    float mainWeight = max(mainDirectionWeight, 0.0f) * mainLum;
    // 说明：合成 Toon 方向：envDir 和 mainDir 按权重混合后安全归一化，失败则回退到 envDir。
    toonDirectionWS = BakeryToonSafeNormalize(envDir * envWeight + mainDir * mainWeight, envDir);
    // 对齐 lilToon 的思路：采样前削弱方向长度，让结果更像风格化亮侧/暗侧提示，而不是物理漫反射渐变。
    // 说明：输出实际采样方向：对 toonDirectionWS 乘 saturate(directionScale)，默认可取 0.666666。
    sampleDirectionWS = toonDirectionWS * saturate(directionScale);
}
// 主要入口：输出亮侧 SH、暗侧 SH、调试方向和暗侧亮度遮罩。
// 常规材质里优先使用 toonLightSH 和 toonFillLuma；toonFillSH/toonDirectionWS 主要用于调试或高级接线。
// 说明：声明 ShaderGraph 主入口；输入与方向函数一致，输出亮侧 SH、暗侧 SH、调试方向和暗侧亮度。
void BakeryToonSH_float(
    float3 L0,
    float3 normalWorld,
    float2 lightmapUV,
    float3 mainLightDirWS,
    float3 mainLightColor,
    float directionScale,
    float envDirectionWeight,
    float mainDirectionWeight,
    out float3 toonLightSH,
    out float3 toonFillSH,
    out float3 toonDirectionWS,
    // 说明：声明 ShaderGraph 主入口；输入与方向函数一致，输出亮侧 SH、暗侧 SH、调试方向和暗侧亮度。
    out float toonFillLuma)
{
    // 说明：声明内部采样方向变量，不直接暴露给最终颜色。
    float3 sampleDirectionWS;
    // 说明：调用方向合成函数，把输入参数转换成 toonDirectionWS 和 sampleDirectionWS。
    BakeryToonDirection_float(
        L0,
        normalWorld,
        lightmapUV,
        mainLightDirWS,
        mainLightColor,
        directionScale,
        envDirectionWeight,
        mainDirectionWeight,
        toonDirectionWS,
        sampleDirectionWS
    );
    // 正反两个方向分别模拟 lilToon 的亮侧 SH 和暗侧 SH。
    // 两次采样都继续走 BakerySH_float，保证 Bakery 的抗振铃处理仍然生效。
    // 说明：用正向 sampleDirectionWS 采样 BakerySH_float，得到亮侧环境/补光信号 toonLightSH。
    BakerySH_float(L0, sampleDirectionWS, lightmapUV, toonLightSH);
    // 说明：用反向 sampleDirectionWS 采样 BakerySH_float，得到暗侧环境/回填信号 toonFillSH。
    BakerySH_float(L0, -sampleDirectionWS, lightmapUV, toonFillSH);
    // 说明：对亮侧 SH 做非负保护，避免异常负值传到亮面。
    toonLightSH = max(toonLightSH, float3(0.0f, 0.0f, 0.0f));
    // 说明：对暗侧 SH 做非负保护，避免负值污染暗部回填遮罩。
    toonFillSH = max(toonFillSH, float3(0.0f, 0.0f, 0.0f));
    // 说明：将暗侧 SH 压成非负亮度，提供 ShaderGraph 中更稳定的单通道回填遮罩。
    toonFillLuma = BakeryToonPositiveLuminance(toonFillSH);
}
// 可选的 lilToon 风格合成模板。
// 这个函数只演示推荐合成边界：SH 负责亮侧补偿和暗部回填强度，最终阴影色仍由调用方的美术色板决定。
// 说明：声明可选的 lilToon 风格合成函数；输入包括 albedo、阴影色、toonBand、主光、SH 与限制参数。
void BakeryToonLighting_float(
    float3 albedo,
    float3 shadowColor,
    float toonBand,
    float3 mainLightColor,
    float3 toonLightSH,
    float3 toonFillSH,
    float directSHWeight,
    float shadowEnvStrength,
    float lightMinLimit,
    float lightMaxLimit,
    out float3 color,
    out float3 lightColor,
    // 说明：声明可选的 lilToon 风格合成函数；输入包括 albedo、阴影色、toonBand、主光、SH 与限制参数。
    out float3 indirectColor)
{
    // 亮侧：主光颜色叠加少量 Toon SH，再做上下限约束，避免烘焙环境把卡通亮面打爆。
    // 说明：计算 lightColor：主光颜色叠加 toonLightSH * directSHWeight。
    lightColor = mainLightColor + toonLightSH * max(directSHWeight, 0.0f);
    // 说明：对 lightColor 做 clamp，避免烘焙环境把卡通亮面打爆或压得过低。
    lightColor = clamp(
        lightColor,
        float3(lightMinLimit, lightMinLimit, lightMinLimit),
        float3(lightMaxLimit, lightMaxLimit, lightMaxLimit)
    );
    // 说明：计算亮侧颜色：albedo 乘受限后的 lightColor。
    float3 directColor = albedo * lightColor;
    // 说明：计算阴影基底：由调用方的 shadowColor 乘 lightColor，保持阴影色板主导权。
    float3 shadowBase = shadowColor * lightColor;
    // 说明：计算回填遮罩：toonFillSH 乘 shadowEnvStrength 后 saturate。
    float3 fillMask = saturate(toonFillSH * max(shadowEnvStrength, 0.0f));
    // 暗侧：SH 只作为回填强度，把阴影色轻微推回固有色；最后限制暗侧不超过亮侧，维持卡通层级。
    // 说明：把 shadowBase 按 fillMask 往 albedo 回填，模拟暗部环境提亮。
    indirectColor = lerp(shadowBase, albedo, fillMask);
    // 说明：用 min 限制 indirectColor 不超过 directColor，维持卡通亮暗层级。
    indirectColor = min(indirectColor, directColor);
    // 说明：用 toonBand 在暗侧与亮侧之间插值，得到最终合成颜色。
    color = lerp(indirectColor, directColor, saturate(toonBand));
}
// 说明：结束包装文件包含保护。
#endif
```

#### BakeryDecodeLightmap.hlsl 顶部 include guard 注释版说明（脱敏，省略空行）

> 这里只记录新增 include guard 与原文件头部相关的有意义行；空行不再单独说明。

```hlsl
// 为 Bakery ShaderGraph 工具函数补充包含保护。
// Toon 包装层会 include 本文件，而旧 Bakery Custom Function 节点也可能继续直接引用它；
// 这个守卫用于支持新旧节点短期并存，避免同一编译单元里重复定义函数。
// 说明：include guard 开始，避免重复包含原 Bakery 解码文件。
#ifndef BAKERY_DECODE_LIGHTMAP_INCLUDED
// 说明：定义 include guard 宏。
#define BAKERY_DECODE_LIGHTMAP_INCLUDED
//#define NOURP
//#define SURFACE
// 说明：原 Bakery 的 SURFACEANALYSIS 条件编译逻辑，记录中仅说明其仍保持原样。
#if defined(SURFACE) && defined(SHADER_TARGET_SURFACE_ANALYSIS)
#define SURFACEANALYSIS
#endif
```
### 关键代码

核心不是重写 SH，而是改采样方向后继续走 Bakery：

```hlsl
BakerySH_float(L0,  sampleDirectionWS, lightmapUV, toonLightSH);
BakerySH_float(L0, -sampleDirectionWS, lightmapUV, toonFillSH);
```

方向合成的关键是把环境方向与主光方向合成，再按 lilToon 思路削弱方向性：

```hlsl
toonDirectionWS = BakeryToonSafeNormalize(envDir * envWeight + mainDir * mainWeight, envDir);
sampleDirectionWS = toonDirectionWS * saturate(directionScale);
```

暗部回填的推荐边界是“强度来自 SH，色相来自项目色板”：

```hlsl
float3 fillMask = saturate(toonFillSH * max(shadowEnvStrength, 0.0f));
indirectColor = lerp(shadowBase, albedo, fillMask);
indirectColor = min(indirectColor, directColor);
```

### 参考链接

- [Bakery GPU Lightmapper 官方文档](https://geom.io/bakery/wiki/) - Bakery 光照烘焙与 SH/RNM 背景。
- [lilToon 官方仓库](https://github.com/lilxyzw/lilToon) - Toon SH 正反方向采样与暗部环境回填思路的参考来源。

### 相关记录

- [ASE Shader 架构与 Bakery 光照集成最佳实践](./ase-shader-bakery-integration.md) - 记录 Bakery SH 参数外置、ShaderGraph 封装与 Include 路径实践，本记录在此基础上补充 NPR/Toon 化处理。
- [基于图像的间接光照 IBL](./pbr-image-based-lighting-ibl.md) - 说明 PBR 中 `SampleSH(N) * albedo` 的间接漫反射定位，本记录强调该做法在 Toon 中需要再处理。

### 验证记录

- [2026-07-02] 修正：按维护阅读习惯将逐行表格改为“代码块 + 说明注释”形式；删除空行等无实现语义行的说明，保留有实现语义的 HLSL/预处理行和脱敏边界。

- [2026-07-01] 初次记录。来源为一次 Unity URP + Bakery + ShaderGraph 的实践实现整理；已执行阿卡西 `git pull origin main`、重复检测和写入前结构校验。
- [2026-07-01] 脱敏审查：原始上下文包含真实工程名、本机绝对路径、内部场景资源路径、ShaderGraph 序列化 ID 和截图临时路径；正式记录已统一移除或泛化，仅保留通用文件名、函数名、端口语义和可复用 HLSL 逻辑。
- [2026-07-01] 正确性边界：已基于当前 HLSL 源码逐行读取并记录实现意图，已核对 ShaderGraph 节点语义配置；尚未在 Unity 编辑器中完成重新导入、ShaderGraph 编译或画面对比，因此状态标记为“⚠️ 待验证”。


# FractalMiner 终末地角色 shader 纹理通道分析

**标签**：#unity #shader #graphics #texture #npr #rendering #knowledge
**来源**：FractalMiner 仓库源码分析
**收录日期**：2026-05-20
**来源日期**：2026-05-20
**更新日期**：2026-05-20
**状态**：📘 有效
**可信度**：⭐⭐⭐⭐（基于本地 shader 源码采样点和属性声明；未做实际贴图像素或 RenderDoc 帧验证）
**适用版本**：FractalMiner 当前 HGRP CharacterNPR Fix shader；终末地逆向学习参考

### 概要

FractalMiner 当前可读的终末地 CharacterNPR Fix shader 中，纹理通道用途可以通过 shader 属性声明、采样点和通道赋值关系直接分析出来。但这些结论描述的是“shader 期望如何使用纹理”，不是“某个角色实际贴图每个通道画了什么”，后者仍需实际贴图或 RenderDoc 帧捕获验证。

### 内容

#### 结论边界

当前结论分三层：

- **代码直接证明**：shader 中明确将某个采样通道赋给固定语义。例如 `_MetallicGlossMap.r/g/b/a` 分别进入 `metallic/specScale/shadowMask/smoothness`，`_SDFLightmap.x + .y` 作为 SDF 值，`.z` 参与 SDF 法线还原。
- **属性命名与代码用途共同确认**：例如 `_FurDirMap` 属性名写明 `RG=Direction, B=Density, A=Length`，代码中也使用 `x/y` 做毛发方向扰动，`z` 做密度，`w` 做长度。
- **代码分支可见但缺少资产验证**：例如 `_BaseMap.a` 在身体、头发、眼睛、毛发、VFX 中可承担 alpha、clip、遮罩或散射混合等不同职责，需要结合实际材质开关和贴图像素确认具体角色用法。

因此，这张表应作为“源码层 shader contract”使用，而不是最终资产通道规范。后续细看时，应优先用实际贴图、材质 keyword、RenderDoc draw call 和帧内绑定纹理来复核。

#### 当前仓库依据

本次分析主要参考以下文件：

- `Assets/Project/EndField/HGRP/HGRP_CharacterNPR_Fix.shader`
- `Assets/Project/EndField/HGRP/HGRP_CharacterNPR_Skin_Fix.shader`
- `Assets/Project/EndField/HGRP/HGRP_CharacterNPR_Hair_Fix.shader`
- `Assets/Project/EndField/HGRP/HGRP_CharacterNPR_Eye_Fix.shader`
- `Assets/Project/EndField/HGRP/HGRP_CharacterNPR_Fur_Fix.shader`
- `Assets/Project/EndField/HGRP/HGRP_CharacterNPR_VFX_Fix.shader`
- `Assets/Project/EndField/HGRP/HGRP_CharacterNPR_OverlayShadow_Fix.shader`
- `Assets/Project/EndField/HGRP/CustomAOSample.hlsl`

当前仓库的 `Assets/Project/EndField/HGRP` 下主要是 shader 和原始压缩包，没有完整材质和贴图资产；当前工程也未挂完整 HGRP 渲染管线。因此这份记录不声称已经验证了原游戏实际贴图内容。

#### 纹理通道用途表

| 纹理 | R | G | B | A |
|---|---|---|---|---|
| `_BaseMap` | 基色 R | 基色 G | 基色 B | alpha、clip、半透、眼部散射或遮罩等，取决于 shader 分支 |
| `_ShadowLutTex` | 暗部 LUT 输出色 | 暗部 LUT 输出色 | 暗部 LUT 输出色 | 当前 Fix 代码基本未使用 |
| `_MetallicGlossMap` | metallic | specular scale | shadow mask | smoothness |
| `_BumpMap` | DXT5nm normal X 的一部分，和 A 相乘 | normal Y | 当前 Fix 代码基本未使用 | DXT5nm normal X 的另一部分 |
| `_DiffRampMap` | ramp 色 | ramp 色 | ramp 色 | ramp 明暗/阴影权重 |
| `_SpecRampMap` | 高光 ramp 色 | 高光 ramp 色 | 高光 ramp 色 | 当前 Fix 代码基本未使用 |
| `_OutlineMask` | 描边宽度权重 | 描边 Z 偏移权重 | 当前 Fix 代码基本未使用 | 当前 Fix 代码基本未使用 |
| `_SDFLightmap` | SDF 阈值分量 1 | SDF 阈值分量 2，与 R 相加 | SDF 侧向法线标量 | 当前 Fix 代码基本未使用 |
| `_SDFMask` | face rim/面部区域权重 | SDF 法线与模型法线混合，也影响 spec gate | face/skin rim scale 分区 | 皮肤特殊高光/相机门控 |
| `_EmotionMap` | 表情贴图色 | 表情贴图色 | 表情贴图色 | 表情混合 mask |
| `_HighlightMap` | 视角偏移高光色 | 视角偏移高光色 | 视角偏移高光色 | 当前 Fix 代码基本未使用 |
| `_SplitNormalMap` | 头发漫反射 normal X | 头发漫反射 normal Y | 头发高光 normal X | 头发高光 normal Y |
| `_StrokeMap` | 头发各向异性高光偏移 | 当前 Fix 代码基本未使用 | 当前 Fix 代码基本未使用 | 当前 Fix 代码基本未使用 |
| `_LineMap` | 发丝线状高光遮罩 | 当前 Fix 代码基本未使用 | 当前 Fix 代码基本未使用 | 当前 Fix 代码基本未使用 |
| `_MatcapTex` | 眼部 Matcap 色 | 眼部 Matcap 色 | 眼部 Matcap 色 | Matcap 强度/混合 |
| `_FurMap` | 毛发噪声/覆盖裁切 | 当前 Fix 代码基本未使用 | 当前 Fix 代码基本未使用 | 当前 Fix 代码基本未使用 |
| `_FurDirMap` | 毛发 U 方向扰动 | 毛发 V 方向扰动 | 毛发密度 | 毛发长度 |
| `_FurDyeMap` | 毛发染色色 | 毛发染色色 | 毛发染色色 | 当前 Fix 代码基本未使用 |
| `_VFXSpecialMainTex` | 可作为 alpha 或颜色 | 颜色 | 颜色 | 可作为 alpha |
| `_VFXSpecialBlendTex` | UV 扰动/溶解驱动 | tint 权重参与 | tint 权重参与 | blend factor |
| VFX `_MainTex` | 可作为 alpha 或颜色 | 颜色 | 颜色 | 可作为 alpha |
| VFX `_MaskTex` | 可作为 alpha 或颜色因子 | 颜色因子 | 颜色因子 | 可作为 alpha |
| VFX `_BlendTex` | 叠加色 | 叠加色 | 叠加色 | 叠加强度 |
| VFX `_DisturbTex1` | 普通扰动；normal 模式下参与 X | normal 模式 Y | 当前 Fix 代码基本未使用 | normal 模式 X 乘子 |
| VFX `_NormalMap` | DXT5nm normal X 的一部分 | normal Y | 当前 Fix 代码基本未使用 | DXT5nm normal X 的另一部分 |
| `_CustomAOTexture` | Ground Truth AO | Alchemy AO | 无 | 无 |

#### 复核建议

后续继续细看时，建议按以下顺序验证：

1. 先确认材质 keyword：例如 `_SDFLIGHTMAP`、`_NORMALMAP`、`_DIFF_RAMP_ON`、`_SPECULAR_NORMALMAP`、`_STROKE_ON`、`_MATCAP_ON`、`_CHARACTER_VFX_SPECIAL` 是否启用。
2. 再用实际贴图查看各通道内容：对照灰度图判断通道是否符合 shader contract，例如金属度、阴影遮罩、SDF、法线、毛发密度等。
3. 用 RenderDoc 确认帧内绑定：同名 texture slot 可能被不同材质绑定不同用途纹理，必须以 draw call 实际绑定为准。
4. 对表中“当前 Fix 代码基本未使用”的通道保持谨慎：这些通道可能在原始 HGRP shader、其他变体、工具链或未移植功能中使用。

### 关键代码

`_MetallicGlossMap` 的通道语义属于代码直接证明：

```hlsl
float4 mgSample = SAMPLE_TEXTURE2D(_MetallicGlossMap, sampler_MetallicGlossMap, uv);
metallic   = mgSample.r;
specScale  = mgSample.g;
shadowMask = mgSample.b;
smoothness = mgSample.a;
```

`_SDFLightmap` 的 R/G/B 用途属于代码直接证明：

```hlsl
float4 sdfSample = SAMPLE_TEXTURE2D_LOD(_SDFLightmap, sampler_SDFLightmap, sdfUV, 0);
float sdfValue = sdfSample.x + sdfSample.y;
float sdfNx_base = 1.0 - 2.0 * sdfSample.z;
```

`_SplitNormalMap` 的 RG/BA 分流属于代码直接证明：

```hlsl
float4 nrmSmp = SAMPLE_TEXTURE2D(_SplitNormalMap, sampler_SplitNormalMap, uv);
float dnRawX = nrmSmp.x * 2.0 - 1.0;
float dnRawY = nrmSmp.y * 2.0 - 1.0;
float snRawX = nrmSmp.z * 2.0 - 1.0;
float snRawY = nrmSmp.w * 2.0 - 1.0;
```

### 参考链接

- [ShiyumeMeguri/FractalMiner](https://github.com/ShiyumeMeguri/FractalMiner) - 当前分析对应的公开仓库来源。
- [Bilibili：终末地 全角色+动画+Shader逆向还原](https://www.bilibili.com/video/BV1Eu9BBuExe/) - 本次调查中的公开展示视频。

### 相关记录

- [终末地—渲染学习](./endfield-rendering-study.md) - 终末地角色渲染整体流程和脸部 SDF 分析。
- [SDF 有向距离场学习笔记](./sdf-signed-distance-field.md) - 脸部 SDF 光照相关基础概念。

### 验证记录

- [2026-05-20] 初次记录，来源：对 FractalMiner 仓库当前 CharacterNPR Fix shader 的源码采样点、属性声明和本次对话结论整理。

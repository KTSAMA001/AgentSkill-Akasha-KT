# FractalMiner 终末地角色 shader 纹理通道分析

**标签**：#unity #shader #graphics #texture #npr #rendering #knowledge #arknights-endfield
**来源**：FractalMiner 仓库源码分析
**收录日期**：2026-05-20
**来源日期**：2026-05-20
**更新日期**：2026-05-25
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

#### 纹理通道用途表（细化版）

阅读这张表时要注意：这里说的“未使用”，只表示当前可读 Fix shader 中没有看到该通道参与最终计算；它不排除原始 HGRP 变体、未移植功能、工具链或其他材质版本会使用该通道。

##### 基础颜色与暗部颜色

`_BaseMap`

- RGB：基础颜色，也就是 albedo/base color。身体、皮肤、头发、眼睛和毛发 shader 都会先取 `baseSample.rgb` 再乘 `_BaseColor.rgb`。
- A：不是全局固定语义。常见用途包括透明度、alpha clip、半透合成、眼部散射或遮罩混合。具体含义必须看当前材质启用的 shader 和 keyword。
- 复核方式：看采样后变量是否叫 `baseAlpha`、是否进入 `clip()`、是否参与 `lerp()` 或 Blend。

`_ShadowLutTex`

- RGB：暗部颜色 LUT 的输出色。代码把 albedo 转到类似 sRGB 的坐标后，用 R/G/B 计算 2D LUT 坐标，再采样 LUT 得到 shadow color。
- A：当前 Fix shader 中没有看到参与计算。
- 注意：这不是一张普通灰度阴影图，而是“基色到暗部色”的查色表；它控制阴影色相，而不是单纯控制阴影强度。

##### 材质参数与 ramp

`_MetallicGlossMap`

- R：`metallic`，金属度。
- G：`specScale`，高光强度缩放。
- B：`shadowMask`，阴影遮罩或暗部参与权重。
- A：`smoothness`，光滑度；代码里再转成 `roughness = 1 - smoothness`。
- 这是最明确的通道打包之一，属性名也写成 `RGBA: Metal,Spec,Shadow,Smooth`。

`_DiffRampMap`

- RGB：漫反射 ramp 颜色，用来给明暗过渡染色。
- A：ramp 明暗权重。代码里常命名为 `rampA`，参与阴影/亮部混合、环境色混合或 view ramp 合并。
- 注意：RGB 不只是直接乘到基色上，部分 shader 会做色度提取和亮度守恒，避免 ramp 染色把整体亮度压坏。

`_SpecRampMap`

- RGB：高光 ramp 颜色，常用于风格化高光或头发各向异性高光上色。
- A：当前 Fix shader 中没有看到参与计算。

##### 普通法线与压缩法线

`_BumpMap`

- 源码读法：`normalX = sample.r * sample.a * 2 - 1`，`normalY = sample.g * 2 - 1`，`normalZ = sqrt(1 - normalX^2 - normalY^2)`。
- R：参与 normal X 解包。不能单独理解成“X 通道”，因为代码把 R 和 A 相乘后才得到 X。
- G：normal Y。
- B：当前 Fix shader 中没有看到参与计算。
- A：参与 normal X 解包。常见 DXT5nm/BC3nm 法线压缩中，X 主要放在 A，R 可能作为兼容乘子；RG/BC5 类贴图中，X 可能主要在 R，A 可能接近 1。
- 注意：这类法线贴图只显式存 X/Y，Z 是运行时用单位向量关系重建出来的。表述时应写成“R 和 A 共同解包 normal X”，不要写成“R 是一半 X、A 是另一半 X”。

VFX `_NormalMap`

- 源码读法与 `_BumpMap` 类似：`normalX = sample.r * sample.a * 2 - 1`，`normalY = sample.g * 2 - 1`，Z 由 X/Y 重建。
- R：参与 normal X 解包。
- G：normal Y。
- B：当前 Fix shader 中没有看到参与计算。
- A：参与 normal X 解包。
- 注意：这是 VFX shader 自己的 normal map，不是角色本体 `_BumpMap`。

##### 描边控制

`_OutlineMask`

- R：描边宽度权重。值越高，通常描边越接近材质设定的 `_OutlineWidth`。
- G：描边沿视深方向的偏移权重，配合 `_OutlineOffsetZ` 使用，用来缓解轮廓线穿插或遮挡问题。
- B：当前 Fix shader 中没有看到参与计算。
- A：当前 Fix shader 中没有看到参与计算。

##### 脸部 SDF 与表情

`_SDFLightmap`

- R：SDF 阈值分量 1。
- G：SDF 阈值分量 2。当前 Fix shader 用 `R + G` 得到 `sdfValue`，不是只用单独 R 通道。
- B：SDF 侧向法线标量。代码把 B 从 `[0,1]` 映射为近似 `[-1,1]` 的 X 方向，再结合脸朝向重建平面 SDF 法线。
- A：当前 Fix shader 中没有看到参与计算。
- 注意：这张图同时服务“脸部明暗切线”和“脸部风格化法线”，不是普通 lightmap。

`_SDFMask`

- R：face rim 或面部区域权重，代码中参与 `rimModifier`。
- G：SDF 法线与模型法线的混合权重，也参与若干 spec gate。值越偏向一侧，越依赖 SDF 法线或模型法线。
- B：脸部/身体 rim scale 分区，代码中用于在 `_FaceRimOffScale` 和 `_SkinRimOffScale` 之间插值。
- A：皮肤特殊高光或相机门控，代码中参与 `skinAmt` 一类计算。
- 注意：这张 mask 控制多个脸部风格化分支，不能只理解成“脸部阴影遮罩”。

`_EmotionMap`

- RGB：表情贴图色，用 2x2 图集偏移按 `_EmotionIndex` 采样。
- A：表情混合 mask，和 `_EmotionBlend` 一起决定表情图覆盖基础色的程度。

`_HighlightMap`

- RGB：视角偏移高光色。代码根据视线方向对 UV 做偏移后采样，用来做嘴唇、脸部小高光等始终跟随视角变化的假高光。
- A：当前 Fix shader 中没有看到参与计算。

##### 头发

`_SplitNormalMap`

- R：头发漫反射 normal X。
- G：头发漫反射 normal Y。
- B：头发高光 normal X。
- A：头发高光 normal Y。
- 注意：它不是 DXT5nm 的 R/A 共同解 X。这里 RG 是一套 diffuse normal，BA 是另一套 specular normal；两套法线分开是为了让头发阴影形体和发丝高光可以有不同走向。

`_StrokeMap`

- R：头发各向异性高光偏移。代码把它从 `[0,1]` 映射到 `[-1,1]`，再影响 Kajiya-Kay 式发丝高光的切线偏移。
- G/B/A：当前 Fix shader 中没有看到参与计算。

`_LineMap`

- R：线状高光遮罩或发丝高光线条权重，参与 `_SPECULAR_LINE` 分支。
- G/B/A：当前 Fix shader 中没有看到参与计算。

##### 眼睛

`_MatcapTex`

- RGB：眼部 Matcap 色，用视空间法线生成 matcap UV 后采样，提供虹膜/晶体感的伪环境反射。
- A：Matcap 强度或混合因子，代码里和 `_MatcapColor`、漫反射强度一起形成 `matcapContrib`。

##### 毛发 shell

`_FurMap`

- R：毛发噪声/覆盖度，参与 shell 层的 cutoff 和 alpha clip，决定每层毛发哪里保留、哪里被裁掉。
- G/B/A：当前 Fix shader 中没有看到参与计算。

`_FurDirMap`

- R：毛发 U 方向扰动，从 `[0,1]` 映射到 `[-1,1]` 后影响 shell 采样 UV。
- G：毛发 V 方向扰动，从 `[0,1]` 映射到 `[-1,1]` 后影响 shell 采样 UV。
- B：毛发密度或阴影相关密度值，代码中作为 `furDirZ`。
- A：毛发长度，顶点阶段读取后影响 shell 沿法线外扩距离。

`_FurDyeMap`

- RGB：毛发染色图，代码中做类似 screen blend 的染色混合。
- A：当前 Fix shader 中没有看到参与计算。

##### 角色特殊 VFX

`_VFXSpecialMainTex`

- RGB：特效主颜色；当 `_UseVFXMainTexAsAlpha = 1` 时，RGB 会被退化为白色因子，不再提供颜色。
- R：在 `_UseVFXMainTexAsAlpha = 1` 时作为 alpha。
- A：在 `_UseVFXMainTexAsAlpha = 0` 时作为 alpha。
- 注意：R/A 哪个是 alpha 由开关决定，不能脱离材质参数判断。

`_VFXSpecialBlendTex`

- R：UV 扰动来源，也可能参与溶解或过渡阈值。
- RGB：特效 tint 权重或颜色参与项，具体取决于分支。
- A：blend factor，控制特效主纹理与角色颜色的混合强度。

##### 通用 VFX shader

VFX `_MainTex`

- RGB：主颜色；当 `_UseMainTexAsAlpha = 1` 时，RGB 会被替换为白色因子，颜色主要来自 tint。
- R：当 `_UseMainTexAsAlpha = 1` 时作为 alpha。
- A：当 `_UseMainTexAsAlpha = 0` 时作为 alpha。

VFX `_MaskTex`

- RGB：颜色因子；当 `_UseMaskTexAsAlpha = 1` 时，RGB 不再调色，只把 mask 当 alpha 用。
- R：当 `_UseMaskTexAsAlpha = 1` 时作为 mask alpha。
- A：当 `_UseMaskTexAsAlpha = 0` 时作为 mask alpha。

VFX `_BlendTex`

- RGB：额外叠加色，乘顶点色和 `_BlendTint.rgb` 后加到最终颜色上。
- A：blend 强度，和当前 combined alpha、顶点 alpha、`_BlendTint.a` 一起得到 `blendFactor`。

VFX `_DisturbTex1`

- 普通扰动模式：R 生成扰动值；如果 `_Bi_Disturb = 1`，R 会从 `[0,1]` 重映射到 `[-1,1]`。这个扰动值可同时影响 U/V，具体强度由 `_DisturbUIntensity1` 和 `_DisturbVIntensity1` 控制。
- normal 模式：R 和 A 共同参与 X 方向扰动，G 参与 Y 方向扰动，B 当前未见参与。
- 注意：它既可以当普通灰度扰动图，也可以当类似法线扰动图，取决于 `_DisturbTex1Normal`。

##### 屏幕空间 AO

`_CustomAOTexture`

- R：Ground Truth AO factor。值接近 1 表示无遮挡，接近 0 表示强遮蔽。
- G：Alchemy AO factor。值接近 1 表示无遮挡，接近 0 表示强遮蔽。
- B/A：无。注释中明确说 renderer 发布的是单张 RG8 纹理。
- 注意：AO 不是直接乘黑，而是由 `ApplyCustomAO` 按材质自己的 shadowColor 插值，这样角色暗部颜色仍保持 NPR 色相。

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

`_BumpMap` 的 normal X/Y/Z 解包方式属于代码直接证明。这里的重点是 R 和 A 共同参与 X，Z 不从贴图读取，而是由 X/Y 重建：

```hlsl
float4 nrmSmp = SAMPLE_TEXTURE2D(_BumpMap, sampler_BumpMap, uv);
float nrmX = (nrmSmp.x * nrmSmp.w * 2.0 - 1.0) * _BumpScale;
float nrmY = (nrmSmp.y * 2.0 - 1.0) * _BumpScale;
float nrmZ = max(sqrt(1.0 - saturate(nrmX*nrmX + nrmY*nrmY)), 1e-16);
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
- [2026-05-20] 修正：将原先过短的 RGBA 表扩展为细化说明，补充 `_BumpMap`/VFX 法线贴图的 R*A 解包逻辑、normal Z 重建方式，以及各类 mask/ramp/VFX 纹理的读取条件和注意事项。
- [2026-05-25] 修正：补充 #arknights-endfield 标签，便于按明日方舟：终末地相关 shader/纹理拆解检索。

# 终末地—渲染学习

**标签**：#rendering #shader #pbr #knowledge #zhihu
**来源**：[知乎 - 稻草人](https://zhuanlan.zhihu.com/p/2013370672647268314)
**收录日期**：2026-03-31
**来源日期**：编辑于 2026-03-23（福建）
**状态**：📘 有效
**可信度**：⭐⭐⭐（社区实践，AI辅助整理，附 GitHub 原图）
**适用版本**：通用渲染技术（终末地项目实践）

### 概要
系统分析了《终末地》项目的角色渲染流程，以脸部渲染为核心深入解读 shader 效果实现，涵盖渲染管线整体梳理、角色渲染细节、特殊效果说明等。附有大量渲染对比图和 AI 绘制的流程图，原图在 GitHub 上可查。

### 内容

​

目录

## 1.前言

本文仅作为学习记录!以下内容纯属虚构！该文只对大概的渲染流程梳理一下，然后主要分析一下角色渲染，其他可能顺带一些东西...需要注意相当一部分为AI整理，仅供参考

原图在github上

[https://github.com/Straw1997/Document/tree/main/%E7%9F%A5%E4%B9%8E/%E7%BB%88%E6%9C%AB%E5%9C%B0%E2%80%94%E6%B8%B2%E6%9F%93%E5%AD%A6%E4%B9%A0github.com/Straw1997/Document/tree/main/%E7%9F%A5%E4%B9%8E/%E7%BB%88%E6%9C%AB%E5%9C%B0%E2%80%94%E6%B8%B2%E6%9F%93%E5%AD%A6%E4%B9%A0](https://link.zhihu.com/?target=https%3A//github.com/Straw1997/Document/tree/main/%25E7%259F%25A5%25E4%25B9%258E/%25E7%25BB%2588%25E6%259C%25AB%25E5%259C%25B0%25E2%2580%2594%25E6%25B8%25B2%25E6%259F%2593%25E5%25AD%25A6%25E4%25B9%25A0)

ps: 原本是想都看下的，结果只看了一个脸就把我掏空了(这里只是对shader效果进行解读，并不是按照正常编写思维进行)。其余部分直接就展示AI绘制的流程图吧，除非有重要的特殊效果需要进行说明....(歪理)主要还是脸是渲染核心，其他内容都大差不差: )

## 2.粗略的渲染流程大纲

![](../assets/endfield-rendering-study/01-img-1.jpg)

P1.渲染流程图

可以看到整体为[延迟渲染](https://zhida.zhihu.com/search?content_id=271090831&content_type=Article&match_order=1&q=%E5%BB%B6%E8%BF%9F%E6%B8%B2%E6%9F%93&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3NzUwOTEwMjAsInEiOiLlu7bov5_muLLmn5MiLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNzEwOTA4MzEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.Pz6Oiim0LHzUwabhwLguPSqiP02xq4SWdTyZkgBcMqo&zhida_source=entity)，角色在最后再通过前向渲染再绘制一次，以用于满足特殊的光照效果。而在写Gbuffer时角色也是完整绘制，可能是为了后续计算GTAO等效果所需要。

### 2.1GBuffer

![](../assets/endfield-rendering-study/02-img-2.jpg)

P2.GBuffer

主要分为5个GBuffer，比较有意思的是他貌似会单独计算一个潮湿的粗糙度，然后在计算延迟光照时根据遮罩进行切换雨|晴天

## 前向渲染

![动图封面](../assets/endfield-rendering-study/03-动图封面.jpg)

前向渲染

可以看到角色为前向渲染(不透明物体的描边为不透明渲染)，前面的额发以及相关描边属于半透，额发阴影、眼睛的睫毛阴影等都是单独的网格绘制，下面只对几个几个比较重要的部位进行简单介绍，因为shader过长，这里只会挑着说，另外有很多trick，我只能按照我自己的想法进行猜测了...

## 脸

![动图封面](../assets/endfield-rendering-study/04-动图封面.jpg)

脸部渲染

![](../assets/endfield-rendering-study/05-img-5.jpg)

脸渲染流程图

这是个超级shader，为了减少变体，这里包含很多计算，通过分支进行区分的，可能并不属于脸，而是在其他材质效果上开启，但是这里依然在这里列出来，后面有效果重复的话将不进行重复说明，顺序的话将按照shader的计算顺序进行说明

![](../assets/endfield-rendering-study/06-img-6.jpg)

脸部纹理

### 基色

![](../assets/endfield-rendering-study/07-img-7.jpg)

基色纹理

先采样基色纹理，然后将uv缩小映射到4宫格内采样对应的表情纹理，进行混合。

```
// 基础色 + 表情叠层（_47 为表情图集，_m28 为当前帧索引）
vec4  baseColorSample    = texture(sampler2D(baseTex, _53), uv, _15._m38);
float expressionFrame    = _44._m28;
//x = (expressionFrame % 2) * 0.5 -> 0或0.5
//y =  0, 0.5, 1.0...
vec2  expressionOffset   = vec2((expressionFrame - 2.0 * trunc(expressionFrame / 2.0)) * 0.5,
                                    floor(expressionFrame * 0.5) * 0.5);
vec4  expressionSample   = texture(sampler2D(expressionTex, _53), expressionOffset + vec2(0.5) * uv, _15._m38);
vec3  albedoLinear       = mix(baseColorSample.xyz * _44._m20.xyz, expressionSample.xyz,
                                   vec3(expressionSample.w * _44._m29));
```

| expressionFrame | expressionOffset |
| --- | --- |
| 0 | (0, 0) |
| 1 | (0.5, 0) |
| 2 | (0, 0.5) |
| 3 | (0.5, 0.5) |

之后转到srgb再去采样LUT进行校色，得到暗部环境光颜色，以供后续进行lerp

![](../assets/endfield-rendering-study/08-img-8.jpg)

脸LUT

![](../assets/endfield-rendering-study/09-img-9.jpg)

脸部Lut校色

### [菲尼尔假次表面](https://zhida.zhihu.com/search?content_id=271090831&content_type=Article&match_order=1&q=%E8%8F%B2%E5%B0%BC%E5%B0%94%E5%81%87%E6%AC%A1%E8%A1%A8%E9%9D%A2&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3NzUwOTEwMjAsInEiOiLoj7LlsLzlsJTlgYfmrKHooajpnaIiLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNzEwOTA4MzEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.4DCvq3-5rWpCmng6Pd_JEO4E8rRsX41nAtaLYfvYkTI&zhida_source=entity)

![](../assets/endfield-rendering-study/10-img-10.jpg)

脸遮罩纹理

他这里使用菲尼尔来对基色添加一个假次表面效果，用来增加层次感，计算流程：

1. 取相机前向量->转到脸局部空间->取xz进行归一化(压扁)->取z值作为阈值进行光照计算(相机面向角色时值为1)
2. 计算菲尼尔，然后叠加各种遮罩控制，进行基色与次表面颜色插值

计算观察角度

```
// 1. 构建 世界->局部空间 的转换矩阵 (WorldToLocal Matrix)
// 用局部坐标系的三个世界轴向构建矩阵（在 GLSL 中按列填入等价于转置/求逆）
mat3 WorldToLocalMatrix = mat3(InstanceMatrix.Row0.xyz, 
                               InstanceMatrix.Row1.xyz, 
                               InstanceMatrix.Row2.xyz);

// 2. 提取真正的“摄像机前向/视线方向” (Camera Forward)
// _m1 是 Inverse View Matrix (相机到世界变换)，提取其第三根轴即为相机的 Z 轴
vec3 CameraForwardWS = vec3(0.0, 0.0, 1.0) * InverseViewMatrix;

// 3. 将相机的视线方向转换到头部的【局部空间】
vec3 CameraForwardLocal = WorldToLocalMatrix * CameraForwardWS;

// 4. 将局部视线投影到水平面 (XZ平面)，并归一化
vec2 CameraForwardXZ = normalize(CameraForwardLocal.xz);

// 5. 提取视线与脸部正前方的对齐度
// 注：在 vec2(x, z) 中，.y 实际上提取的是原本的 Z 分量。
// 如果 FaceForward=1，说明玩家正看着角色的脸；接近0说明在看侧脸。
float ViewAlignFactor = CameraForwardXZ.y;
```

计算菲尼尔次表面

```
// 1. 视角遮罩 (View Front Mask): 看正脸时为 1.0, 侧面为 0.5, 背面为 0.0
float ViewFrontMask = clamp(ViewAlignFactor + 0.5, 0.0, 1.0);

//    结合maskTex的控制，决定是否强制开启遮罩 (maskTex.g = 1 时无视视角全开)
float FresnelMask = maskTex.r * mix(ViewFrontMask, 1.0, maskTex.g);

// 2. 边缘强度参数 (从材质B蒙版中插值获取两个预设强度)
float EdgeIntensity = mix(Global_FresnelStrength_Min, Global_FresnelStrength_Max, maskTex.b);

// 3. 计算最终的菲涅尔权重
float NdotV = clamp(dot(normalWS, viewDirWS), 0.0, 1.0);
float FresnelWeight = clamp(0.85 * (1.0 - NdotV) * FresnelMask * EdgeIntensity, 0.0, 1.0);

// 4. 计算漫反射底色 (Diffuse Base Color)
//    TintColor (_44._m30) 通常是一个偏肉色/红色的环境染色，用于模拟次表面散射(SSS)
vec3 TintColor = _44._m30.xyz;

//    如果位于模型边缘(FresnelWeight 趋近 1)，则在漫反射上叠乘染色
//    如果不在边缘(趋近 0)，则直接使用原始贴图色 Albedo
vec3 DiffuseBaseColor = mix(AlbedoLinear, AlbedoLinear * TintColor, FresnelWeight);

// 5. 提取材质 A 控制的高光增量系数
float BaseSpecBoost = mix(0.0, Global_SpecBoost, maskTex.g);
```

通过计算和贴图可以知道，他这里主要是想要玩家正对脸，并且只有脸的侧面有这种菲尼尔次表面效果，下面是开启和关闭效果

![动图封面](../assets/endfield-rendering-study/11-动图封面.jpg)

菲尼尔次表面

### 拍扁的法线方向

将脸部法线y值进行拍扁，以便在后续采样环境光照时只考虑水平方向的影响

```
// 计算一个以锚点为中心的圆形法线
Vector3 objectGroundOrigin = Vector3(matRow0WS.w, kObjectGroundY, matRow2WS.w);
Vector3 fragToOriginXZ = fragPosWS - objectGroundOrigin;
fragToOriginXZ.y = 0.000061;
Vector3 upBiasedDirWS = SafeNormalize(fragToOriginXZ);

// 将原有的世界空间法线 (normalWS) “压平”，使其几乎平行于 XZ 地平面
Vector3 flattenedNormal = Normalize( Vector3(normalWS.x, 0.000061, normalWS.z) );

// 在“圆形偏平法线”和“扁平化法线(具有结构)”之间进行线性插值
Vector3 mixedNormal = Lerp(upBiasedDirWS, flattenedNormal, maskTex.g);
Vector3 blendedLightNormalWS = Normalize(mixedNormal);
```

面部使用圆形的偏平法线以用来忽视鼻子、眼窝处因为网格结构导致的奇怪问题，其他地方保持原有的法线结构

![](../assets/endfield-rendering-study/12-img-12.jpg)

拍扁法线

### 环境光

环境光为三层精度的[SH混合](https://zhida.zhihu.com/search?content_id=271090831&content_type=Article&match_order=1&q=SH%E6%B7%B7%E5%90%88&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3NzUwOTEwMjAsInEiOiJTSOa3t-WQiCIsInpoaWRhX3NvdXJjZSI6ImVudGl0eSIsImNvbnRlbnRfaWQiOjI3MTA5MDgzMSwiY29udGVudF90eXBlIjoiQXJ0aWNsZSIsIm1hdGNoX29yZGVyIjoxLCJ6ZF90b2tlbiI6bnVsbH0.iirt0vBm61lsEE8vVQ8GLHVCBFF_nQLM2cm1J4kkods&zhida_source=entity)，通过上面拍扁的法线进行采样，之后进行一些颜色调整，这里并不是研究的重点就快速略过了，这里就主要看一下对取到SH环境光后进行的特殊处理

```
// 1. 转换到 HSV 空间
vec3 hsv = RGBToHSV(envLit);
float hue = hsv.x; // 色相 (0.0 到 1.0，0.5 代表青蓝色)
float sat = hsv.y; // 原始饱和度
float val = hsv.z; // 原始亮度 (即 RGB 中的最大值 Max(R,G,B))

// ==========================================
// 基于色相（冷暖）的饱和度压制
// ==========================================

// 计算当前光照颜色距离“纯正天蓝色 (0.5)”有多近
float distToBlue = abs(hue - 0.5);

// 依据冷暖色调，动态计算一个“饱和度限制”
float satLimit = mix(0.35, 0.70, smoothstep(0.35, 0.45, distToBlue));

// 亮度越暗饱和度越低
satLimit = satLimit * clamp(val, 0.0, 1.0);

// 得到最终的饱和度：取原始饱和度与上限之间的最小值
float finalSat = min(sat, satLimit);

// 注意：这里并没有使用原始的 val！
// 而是用一个非线性公式：V = 2 / (2 - S) 强行构造了一个新的亮度乘子。
// 让越鲜艳的颜色，自带越强的自发光提亮感。
float finalVal = 2.0 / (2.0 - finalSat);

// 2. 将调整后的参数重新组合，转回 RGB 空间
vec3 finalColorTint = HSVToRGB(vec3(hue, finalSat, finalVal));

// 最终输出这个被“整形”过的环境光底色
envShapedColor = finalColorTint;
```

可以看到主要是转到[HSV空间](https://zhida.zhihu.com/search?content_id=271090831&content_type=Article&match_order=1&q=HSV%E7%A9%BA%E9%97%B4&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3NzUwOTEwMjAsInEiOiJIU1bnqbrpl7QiLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNzEwOTA4MzEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.Kwuqtsx_7W-DqaAar2n8ziKLGp6csJ2MLpmTKI82mTE&zhida_source=entity)进行调整，然后再转回rgb

- 色相：无变化
- 饱和度：根据色相限制冷暖色的饱和度，并且冷色系颜色饱和度压的更低。越暗的颜色饱和度越低。
- 亮度：越鲜艳的颜色亮度越高，最低亮度为1

下面是通过SD连出来的颜色变化效果，可以更直观的观察，上面是调色后的，前半段是颜色对比，后半段是饱和度对比

[](https://vdn6.vzuu.com/LD/8884f674-2407-11f1-b995-4ea12e914639-v8_f2_t1_yOU22EXX.mp4?pkey=AAW1MjzAEzqxu4NAArard1Ll_ELDcJPalsYG4FIQilpSq2kJ1zYg29-eJzLaEto1HbSqn_Pz4NNo5tTOM1UhxuLQ&bu=da4bec50&c=avc.8.0&expiration=1774925422&f=mp4&pu=e59e796c&v=ks6&pf=Web&pt=zhihu)

![](../assets/endfield-rendering-study/13-img-13.jpg)

00:15

SH色相-饱和度

[](https://vdn6.vzuu.com/LD/279b50b2-240a-11f1-a88a-e211675657f2-v8_f2_t1_FsKmpoLv.mp4?pkey=AAXVzxpNQ9XRNu459Inxfoh_0LZ9sKiva7zxaY4wTJHrl3skSrvHdNOgDuFj6lyPZsy-N-c0nMvqD6eG5wcDNS3u&bu=da4bec50&c=avc.8.0&expiration=1774925422&f=mp4&pu=e59e796c&v=ks6&pf=Web&pt=zhihu)

![](../assets/endfield-rendering-study/14-img-14.jpg)

00:23

SH亮度-饱和度

可以看到是个挺神奇的变换，主要是降低了对比度，并一直让颜色保持亮色

因为当前这帧不是在一个场景中，所以没有走那个分支(SH)，直接是外面传的一个环境光颜色(白色)，这里就不展示了

### 雨痕

![](../assets/endfield-rendering-study/15-img-15.jpg)

雨痕纹理

这里脸部效果比较弱，丝袜的效果是比较强烈的，不过核心算法应该是一样的，这里用脸进行说明

![](../assets/endfield-rendering-study/16-img-16.jpg)

脸部雨痕效果

就这样加上刘海、后处理，脸部效果基本看不见了...

核心逻辑为

1. 根据天气等因素决定是否绘制雨痕
2. 根据时间采样两张纹理得到雨痕法线、遮罩等信息
3. 构建计算AO、法线、粗糙度、遮罩传递给下一部分

```
float minWetness    = InstanceData.minWetness;      // 强制的最低湿度 (比如一直下雨，至少是湿的)
float waterLevelY   = InstanceData.waterLevelHeight;// 环境水坑/水面的绝对高度 (Y坐标)
float waterMult     = InstanceData.waterMultiplier; // 水位线影响的强度权重
float baseWetness   = InstanceData.baseWetness;     // 当前物体基础湿度

// 计算像素距离水面的高度差，算出湿度
float heightWetness = smoothstep(-0.20, 0.15, waterLevelY - fragPosWS.y) * waterMult;
float wetnessMask = max(minWetness, heightWetness);

// 准备好最终要输出给光照计算的变量
float finalAO;          // AO
vec3  finalNormalWS;    // 最终光照法线
float wetLayerMask;     // 湿润层强度掩码
float finalRoughness;   // 最终粗糙度
float finalSpecBoost;   // 高光增强倍数

// 判定：如果物体哪怕只有一点点湿 (>0.01)
if ((baseWetness + wetnessMask) > 0.01)
{
    // 实际潮湿强度
    float wetnessStrength = max(baseWetness, wetnessMask);

    // --- 动画：采样滚动的雨水波纹贴图 ---
    float timePhase = GlobalTime * 0.8;
    
    // 采样当前时刻的水波纹 (xy: 水滴法线, z: 水滴流痕, w: 水滴遮罩)
    vec4 rippleData1 = tex2D(RippleTexture, uv + vec2(0.0, fract(timePhase)));
    
    // 采样极短时间偏移后的波纹权重 (相差 0.005，用于)
    float rippleWeight2 = tex2D(RippleTexture, uv + vec2(0.0, fract(timePhase + 0.005))).w;
    
    // 采样物体本身的“易湿蒙版” (比如衣服褶皱处比平整处更容易积存水纹)
    float surfaceWetMask = tex2D(WetSurfaceTexture, uv).z;

    // --- 获取采样两次时间的水波覆盖范围 ---
    float rippleCoverage2 = rippleWeight2 * surfaceWetMask;
    float rippleCoverage1 = rippleData1.w * surfaceWetMask;
    
    // 重建法线
    vec2 rippleNormalXY = rippleData1.xy * 2.0 - 1.0;
    vec3 rippleNormal = vec3(rippleNormalXY, 0.0);
    rippleNormal.z = sqrt(max(1e-16, 1.0 - clamp(dot(rippleNormalXY, rippleNormalXY), 0.0, 1.0)));
    
    // 算出水波的总覆盖面积和水波痕迹
    float wetCoverage = clamp(rippleCoverage2 + rippleCoverage1, 0.0, 1.0) * wetnessStrength;
    float wetnessTraces = (rippleData1.z * surfaceWetMask) * wetnessStrength;

    // --- 【物理属性篡改】 ---
    
    // rippleUpFacing通过两次时间遮罩的插值，去lerp法线y，可以得到水滴上面是白的，部分水滴下面也是白的，用于辅助构建后面的ao
    // 1. AO：
    float rippleUpFacing = mix(smoothstep(0.0, 0.8, rippleNormalXY.y * 0.5 + 0.5), 1.0, clamp(rippleCoverage2 - rippleCoverage1, 0.0, 1.0));
    float rippleAO = mix(mix(1.0, 0.8, rippleUpFacing), 0.9, mask.g);
    finalAO = baseAO * mix(1.0, wetAlphaMod, wetCoverage);
    
    // 2. 法线
    finalNormalWS = normalize(TBN_Matrix * rippleNormal) * facingSign;
    
    wetLayerMask = clamp(wetCoverage + wetnessTraces, 0.0, 1.0);
    
    // 3. 粗糙度接管：积水表面非常光滑，强行锁死在 0.3
    finalRoughness = 0.3;
    
    // 4. 高光接管：水的反射率极强，将高光强度拉高，最高可达原始的 3.0 倍
    finalSpecBoost = mix(baseSpecBoost, 3.0, clamp(wetCoverage * 2.0 + wetnessTraces, 0.0, 1.0) * wetnessStrength);
}
else
{
    // 如果是干燥的，使用材质原始的物理属性
    finalAO        = baseAO;
    finalNormalWS  = originalNormalWS;         // 保留模型原有的法线
    wetLayerMask   = 0.0;
    finalRoughness = 1.0 - originalSmoothness; // 粗糙度 = 1 - 光滑度
    finalSpecBoost = baseSpecBoost;            // 保持原本的高光强度
}
```

比较不好理解的是计算AO的部分，这里给出中间参数输出图辅助理解

![](../assets/endfield-rendering-study/17-img-17.jpg)

雨痕计算过程效果

鼻子那部分来自基色图的alpha，因为脸部各种遮罩的原因导致没有几个水滴

### [SDF法线](https://zhida.zhihu.com/search?content_id=271090831&content_type=Article&match_order=1&q=SDF%E6%B3%95%E7%BA%BF&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3NzUwOTEwMjAsInEiOiJTREbms5Xnur8iLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNzEwOTA4MzEsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.YY1Mr9VLqS6_hBjZE1jg9zwcFUGCQL1MUzXyqPibQ2w&zhida_source=entity)

![](../assets/endfield-rendering-study/18-img-18.jpg)

脸SDF纹理

计算sdf法线以供后续光照使用，可以避免因脸部网格结构导致的一些问题，使光照更加平滑

```
float eps = 6.103515625e-05; // 避免方向完全落在 XZ 平面导致数值不稳定

// 灯光为两个光照信息的混合
// 主光转到物体空间，再压扁 Y：只保留水平朝向来驱动 SDF 图左右镜像
vec3 dirLightInObj   = objectToWorld * dirLightDir;
vec3 dirLightFlat    = vec3(dirLightInObj.x, eps, dirLightInObj.z);
vec3 dirLightXZNorm  = normalize(dirLightFlat);

// 光从物体右侧来则不改 UV，从左侧来则水平翻转 UV，使同一张对称 SDF 左右通用
float isLightFromRight = float(dirLightXZNorm.x > 0.0);
vec2 sdfUV = uv;
if (isLightFromRight < 0.5)
{
    sdfUV.x = 1.0 - uv.x;
}
vec4 sdfSample = textureLod(sampler2D(sdfTex, sdfSamp), sdfUV, 0.0);

// 从 SDF 贴图 .z 解出侧向标量 [0,1]→[-1,1]；与 UV 镜像配套的一支取反
float sdfXZRaw;
if (isLightFromRight > 0.5)
{
    sdfXZRaw = sdfSample.z * 2.0 - 1.0;
}
else
{
    sdfXZRaw = 1.0 - sdfSample.z * 2.0;
}

// 物体空间计算法线，再转到世界空间
vec3 nObj      = normalize(vec3(sdfXZRaw, eps, 1.0 - abs(sdfXZRaw)));
vec3 sdfNormLS = nObj * objectToWorld;

float lenSq  = dot(sdfNormLS, sdfNormLS);
float invLen = inversesqrt(max(lenSq, 1.17549435e-38));
vec3 sdfNormWS = sdfNormLS * invLen;

// 根据脸部遮罩和物体法线进行混合
vec3 blendedShadingNormalWS = normalize(mix(sdfNormWS, normalWS, maskTex.g));
```

可以看到整体就是根据灯光方向取到SDF，然后直接把这个值当作局部空间x、z的值进行归一化得到法线。转成法线的好处就是后面可以直接和本身法线进行混合(通过面部遮罩)，也可以天然的解决常规sdf中脖子与脸的接缝问题，并且在计算一些光照时可以避免因脸部网格结构所造成的问题(碎块)，拥有众多好处。

![](../assets/endfield-rendering-study/19-img-19.jpg)

sdf法线

### 漫反射

![](../assets/endfield-rendering-study/20-img-20.jpg)

脸Ramp纹理

和常规的二游一样，在做脸部漫反射时采用SDF+Ramp的形式，在计算SDF光照时核心算法依然是取到灯光方向在脸Z轴(正脸)的值，然后通过smoothsetp去映射SDF的值,最后再去采样ramp纹理

1. 计算灯光方向在脸Z轴(正脸)的值，并根据逆光进行一些调整(这里并没有开启)
2. 根据光照值动态计算smoothsetp范围，侧光时过渡范围大，正面/背光时过渡范围小
3. 拿到的值映射到-1~1，根据面部遮罩与身体其他部位通过nl计算的地方进行混合
4. 采样ramp，并提取饱和度

```
// ==========================================================
// 1. 动态阴影偏移计算 (逆光平滑修正)
// ==========================================================
float lightZ            = dirLightXZNorm.z;
float isLookingBack     = clamp(-dot(lightDirXZ, faceForwardXZ), 0.0, 1.0);
float isLightBehind     = clamp(-lightZ, 0.0, 1.0);

// 修正权重：仅在逆光 + 侧背光时触发
float correctionBlend   = isLookingBack * isLightBehind * (1.0 - Param_CorrectionDisable);

// 线性映射 vs 抛物线映射 (-0.5*z^2 + z + 0.5)
float curveCenter       = -lightZ * (lightZ * 0.5 - 1.0) + 0.5; 
float biasCenter        = mix(lightZ, curveCenter, correctionBlend) * 0.5;

// ==========================================================
// 2. 面部 SDF 阈值步进 (卡渲核心)
// ==========================================================
float biasRange         = clamp(0.5 - biasCenter, 0.001, 0.999);
float sdfVal            = (sdfSample.r + sdfSample.g) * 0.5;

// 动态滑动窗口 [Lo, Hi] 决定阴影边缘软硬
float stepLo            = max(2.0 * biasRange - 1.0, 0.0);
float stepHi            = min(2.0 * biasRange, 1.0);

// 0~1 的纯卡渲阴影：SDF平滑切割 + 亮部推移偏移量
float toonShadow_01     = smoothstep(stepLo, stepHi, sdfVal) + max(biasCenter, 0.0);

// ==========================================================
// 3. 材质混合与 Ramp 映射 
// ==========================================================
// 将卡渲 [0,1] 扩展到 [-1,1] 以对齐其他部位点乘
float toonShadow_11     = toonShadow_01 * 2.0 - 1.0; 
float physNdotL         = clamp(dot(normalWS, dirLightDir) + Param_NdotLOffset, -1.0, 1.0);

// maskTex.g (脸部遮罩) 决定使用sdf阴影还是 NdotL
float finalShadowU_11   = mix(toonShadow_11, physNdotL, maskTex.g);

// 映射回 [0,1] 采样 Ramp 渐变图，并提取饱和度供后续
vec4 rampColor          = textureLod(rampTex, vec2(finalShadowU_11 * 0.5 + 0.5, 0.5), 0.0);
float toonRampAlpha = toonRamp.w;//ramp的亮度
float rampChroma        = max(max(rampColor.r, rampColor.g), rampColor.b) 
                        - min(min(rampColor.r, rampColor.g), rampColor.b);
```

他这里sdf值来自于两个通道用于提高精度，以避免出现色带的精度问题，另外一个比较特殊的就是他这里smoothsetp过渡范围，是根据灯光方向动态变化的，侧光的话基本相当于没有二分了，也有利于解决阴阳脸问题

![](../assets/endfield-rendering-study/21-img-21.jpg)

sdf过渡范围

然后接下来就是从ramp拿到的值，以及之前计算的AO、阴影等进行颜色的混合

1. 计算整合各种阴影、AO遮罩
2. 对暗部环境光颜色进行调整(对AO等暗部区域提高饱和度等)
3. 通过之前计算的阴影以及ramp亮度等对暗部颜色和亮部颜色进行混合
4. 根据之前得到的ramp的饱和度进行染色
5. 对最后染色得到的颜色进行最后的矫正，具有不同分支

```
// ==========================================================
// 1. 遮蔽与蒙版 (Occlusion Masks)
// ==========================================================
// 核心受光蒙版：综合AO、半透、卡渲阴影图，找到最暗的瓶颈 (1=完全受光，0=完全阴影)
float litMask = min(min(shadowOccFactor, surfaceAlpha), toonRampAlpha); 
// 基础环境遮蔽 (AO)
float aoMask  = surfaceAlpha * shadowOccFactor; 

// ==========================================================
// 2. 卡渲阴影底色推导 (Shadow Base Color)
// ==========================================================
// 提取较暗的环境光，并提升20%饱和度，防止二次元阴影发灰
// envDiffuseScaledDim来源自BaseColor Lut校色 再调整后
float dimLuma = Luminance(envDiffuseScaledDim);
vec3 saturatedDimEnv = mix(vec3(dimLuma), envDiffuseScaledDim, 1.2);

// 计算阴影区环境光混合因子 (受AO、材质蒙版影响)
float shadowEnvFactor = clamp(surfaceAlpha * (mix(1.0, aoMask, maskTex.g)) + toonRampAlpha, 0.0, 1.0);
// 算出阴影区特有的底色
vec3 shadowColor = mix(saturatedDimEnv, envDiffuseScaled, shadowEnvFactor);

// 基础漫反射：受光区用贴图原本颜色，阴影区用算出的环境阴影色
vec3 diffAlbedo = mix(shadowColor, diffuseColor, litMask);

// ==========================================================
// 3. Ramp 染色与亮度守恒 (Tinting & Luminance Conservation)
// ==========================================================
// 将 Ramp 贴图带颜色的部分(如红晕)染进底色
vec3 tintedAlbedo = diffAlbedo * mix(vec3(1.0), toonRampColor, toonRampChroma);

// --- 方案A：室内/无主光渲染 ---
// 贴图提纯饱和度后，与环境光做AO混合，产生柔和插画感
vec3 saturatedDiffuse = mix(vec3(Luminance(diffuseColor)), diffuseColor, 1.2);
vec3 indoorAlbedo = mix(envDiffuseScaled, saturatedDiffuse, aoMask);

// --- 方案B：室外/有主光渲染 ---
// 亮度守恒：无论 Ramp 怎么染色，强行把亮度倍率拉回到染色前的水平
float targetLuma = Luminance(diffAlbedo);
float currentLuma = max(Luminance(tintedAlbedo), 0.001);
vec3 outdoorAlbedo = tintedAlbedo * clamp(targetLuma / currentLuma, 0.0, 1.5);

// ==========================================================
// 4. 输出最终漫反射 (Final Albedo)
// ==========================================================
vec3 finalAlbedo = mix(indoorAlbedo, outdoorAlbedo, dirLightMask);
```

可以看到核心算法还是根据得到亮度值进行插值暗部和亮部颜色，这里并没有使用ramp直接乘上去，而是根据饱和度只称中间有颜色变化的区域，进行染色，以避免破坏之前定义好的亮部暗部颜色。然后最后还要进行一个根据所在环的境颜色矫正。下面是粗暴的直接修改了灯光方向，进行的三个阶段的效果对比

![](../assets/endfield-rendering-study/22-img-22.jpg)

脸部漫反射计算对比

他这里并没有考虑垂直方向的法线(根据y值进行插值)，所以也只能做水平方向的光照，不能360°。不过话又说回来，按理说如果如果计算sdf法线的话，直接采样计算就好了，并不需要根据灯光方向进行切换

### 高光

![](../assets/endfield-rendering-study/23-img-23.jpg)

脸嘴唇自发光纹理

接着是高光部分的计算

1. 计算高光公式使用的半角向量(根据不同情况进行调整)
2. 通用高光公式计算高光
3. 根据视线偏移采样自发光纹理
4. 根据之前计算的雨痕法线采样matcap得到雨痕高光
5. 进行直接光照混合

```
// ==========================================================
// 1. 间接光高光遮罩 (防止阴影里出现诡异的高光)
// ==========================================================
// 根据室内外，决定高光该受 shadowAO 压制还是受 卡渲阴影 压制
float specMask = mix(shadowAO, tripleMin3f, dirLightMask);
// 高光染色：让高光带上环境光的颜色，且在暗部适当衰减
vec3 specTint = indirectLight * (specMask * 0.5 + 0.5) * Param_SpecBoost;

// ==========================================================
// 2. 二次元“虚拟太阳” (Fake Sun) 核心科技
// ==========================================================
// 不完全依赖真实太阳！强行造一个绑定在角色面朝向(Z轴)的光源
vec3 fakeSunDir = vec3(objAxisZ_WS.x, mix(0.5, dirLightDir.y, dirLightMask), objAxisZ_WS.z);

// 混合真实光、虚拟光和视线，算出一个“魔改版”的半角向量 (Half-Vector)
vec3 stylizedHalfDir = normalize(
    (dirLightDir * dirLightMask) + // 真实光 (室外才有)
    (fakeSunDir * 2.0) +           // 虚拟光 (权重极大，把高光钉在正面)
    (viewDirWS * (2.0 + dirLightMask)) // 视线拉扯 (让高光随镜头轻微游动)
);

// ==========================================================
// 3. 极简版 GGX 高光计算
// ==========================================================
float NdotH = dot(shadedNormalWS, stylizedHalfDir);
float NdotV = clamp(dot(shadedNormalWS, viewDirWS), 0.0, 1.0);

// 计算法线分布函数 (GGX NDF)，决定高光的光斑形状
float rough4 = roughness2 * roughness2;
float NDF_Denom = ((NdotH * rough4 - NdotH) * NdotH) + 1.0;
float D = rough4 / (NDF_Denom * NDF_Denom);

// 舍弃了复杂的物理几何遮蔽(G)，用极简公式输出高光强度 (限制最高亮度为20)
float specIntensity = clamp(D * 0.5 / (2.0 * NdotV + roughness2 + 0.0001), 0.0, 20.0);
vec3 finalGGX = specF0 * specIntensity * specTint;

// ==========================================================
// 4. 视线偏移自发光 
// ==========================================================
// 用视线角度去偏移 UV 采样，使得自发光跟随视角变动，假高光
vec2 parallaxUV = uv + (ViewDir_ObjectSpace.xy * Param_Intensity);
vec3 emissiveColor = texture(emissiveTex, parallaxUV).rgb * specTint;

// ==========================================================
// 5. 湿身/汗水/雨水层高光 (MatCap 技术)
// ==========================================================
vec3 wetSpecular = vec3(0.0);
if (isWet) {
    // 把世界法线转到屏幕/相机空间，映射为 0~1 的 UV 坐标
    vec2 matcapUV = (normalize(shadedNormalWS * ViewMatrix).xy * 0.5) + 0.5;
    // 去采样一张预渲染的水光贴图 (Matcap)
    wetSpecular = texture(rainMaskTex, matcapUV).w * shadowOccFactor * wetIntensity;
}

// ==========================================================
// 6. 终极光照合成
// ==========================================================
// 最终颜色 = (漫反射底色 * 间接光) + 高光 + 自发光 + 水光
vec3 FinalColor = (indirectLight * finalAlbedo) + finalGGX + emissiveColor + wetSpecular;
```

可以看到高光计算的核心公式依然是熟知的那一套(略微简化)，比较有意思的是计算高光的半角矢量会根据情况进行改变，让他始终保持在一个最佳观测高光的角度，因为这里是脸部 其实这里没有高光效果。

另外一个就是在采样自发光的时候，计算了一个根据视角的偏移，可以用于模拟假高光，例如他这个角色的嘴唇高光，会始终存在并跟着视角移动。

![动图封面](../assets/endfield-rendering-study/24-动图封面.jpg)

高光叠加效果

### 边缘光与颜色调整

这里计算了边缘光、第二次sdf光照(单独光发向)、以及饱和度调整

1. 根据亮度计算饱和度提升值
2. 构造两种边缘光方式(1 - nv)与额外灯光方向打边缘光，并进行混合遮罩得到边缘光
3. 使用之前sdf光照相同的逻辑，计算另一个光源的侧光
4. 提高饱和度，叠加边缘光、侧光

```
// ==========================================================
// 1. 亮部饱和度提升 (HDR Vibrance)
// ==========================================================
float preFogLum = Luminance(preFogColor); // 计算当前像素亮度
// 只有亮度超过 0.5 的地方才会产生 vibranceBoost，越亮饱和度越高
float vibranceBoost = clamp(preFogLum - 0.5, 0.0, 0.5); 

// ==========================================================
// 2. 构造二次元专属“侧边轮廓光”方向 (Rim Light Direction)
// ==========================================================
// 魔法：用角色面朝向(Z轴) 和 屏幕控制向量 叉乘，凭空捏造一个专门打亮侧脸的光源
vec3 rimLightDir = normalize(cross(objAxisZ_WS, vec3(Param_RimDir.xy, 0.0)));
float fresnel = 1.0 - abs(dot(viewDirWS, blendedShadingNormalWS)); // 掠射角边缘判定
float isSideView = smoothstep(0.9, 1.0, abs(objAxisZ_osAlignY));   // 判断摄像机是否在看角色侧面

// ==========================================================
// 3. 边缘光形状计算
// ==========================================================
// 模式 A ：基于 Fresnel 边缘和侧视权重
float rimFalloffA = smoothstep(Param_RimSoft.x, Param_RimSoft.y, fresnel) * isSideView;

// 模式 B ：如果背对光源，强制给予边缘光 (由脸部边缘光遮罩控制)
float rimFalloffB = max(isSideView, float(dot(objAxisZ_WS, rimLightDir) < -0.01)) * maskTex.w;

// 根据材质参数(RimMode)混合 A 模式和 B 模式
float rimMask = mix(rimFalloffA, rimFalloffB, Param_RimModeSwitch);

// ==========================================================
// 4. 边缘光着色与遮蔽剔除
// ==========================================================
// 剔除底部的边缘光(防穿帮)，剔除阴影、AO
float rimGeomMask = min(min(RimUpAttenuation, surfaceAlpha), shadow);
// 边缘光颜色 = 光色 * 形状 * 遮蔽 * 假NdotL * (基础色与灰色的混合)
vec3 rimContrib = RimColor * rimMask * rimGeomMask * RimDiffuseBase * RimNdotL;

// ==========================================================
// 5. 计算第二次漫反射，用于侧光
// ==========================================================
// 复用之前的 SDF 面部逻辑，但使用另外一个光源方向
float secondShadowStep = smoothstep(secondBiasLo, secondBiasHi, sdfValue);
float secondShadowUV_11 = (secondShadowStep + max(secondBiasCenter, 0.0)) * 2.0 - 1.0;

// 额外光源的侧光
float secondShadowWeight = smoothstep(-0.5, 0.5, secondShadowUV_11) * (1.0 - maskTex.g);
vec3 secondShadowContrib = SecondShadowColor * secondShadowWeight * diffuseColor;

// ==========================================================
// 6. 最终复合输出
// ==========================================================
// 把原本的颜色和高亮度饱和度混合，加上轮廓光，加上另外一光源侧光
vec3 vibranceColor = mix(vec3(preFogLum), preFogColor, vec3(vibranceBoost^2 + 1.0));
vec3 preClusterColor = vibranceColor + rimContrib + secondShadowContrib;
```

这里比较神奇的是计算了一个复杂的边缘光，并通过遮罩、阴影等方式进行限制，然后又计算了一个与之前sdf工作方式一样的额外灯光方向的侧光。需要注意的是对于这帧脸来说 边缘光是没有什么效果的(因为阴影、遮罩)，并且提高饱和度是根据亮度来的，这里也没有效果

![](../assets/endfield-rendering-study/25-img-25.jpg)

边缘光、侧光等

另外blendedShadingNormalWS是前面根据sdfTex.b构建出来的法线，使用他来计算的边缘光。所以并不会出现脸、鼻子等结构出现的不可控的光照效果，使得整体光照平滑

### 额外光源

这里会更具不同类型进行不同的计算，例如只计算漫反射、高光之类的，用来达成各种各样的打光需求，因为我对这个并不是很感兴趣，下面的伪代码我没有进行严格的审查

```
// ==========================================================
// 局部多光源累加模块 (二次元魔改光照核心)
// ==========================================================
vec3 finalLightAccum = BaseAmbientColor;

for (each active_light in cluster) {
    // 1. 计算通用衰减 (距离、范围、遮罩等)
    float attenuation = CalculateLightAttenuation(light);
    if (attenuation <= 0.0) continue;

    // 提取当前灯光的美术配置类型
    int lightType = light.Type; 

    // 初始化标准 PBR 参数
    vec3  diffuseAlbedo = Albedo;
    float NdotL         = clamp(dot(Normal, LightDir), 0.0, 1.0);
    float specWeight    = 1.0; 
    
    // ---------------------------------------------------------
    // 2. 【核心特色】：根据灯光类型，强行魔改物理定律
    // ---------------------------------------------------------
    switch(lightType) {
        
        case 0: // 【标准光源】(主光/普通点光)
            // 魔法：加入半朗伯 (Half-Lambert) 偏移
            // 让光照越过明暗交界线，包裹住角色身体，避免二次元脸上出现死黑切角
            NdotL = clamp(dot(Normal, LightDir) * 0.5 + 0.5, 0.0, 1.0);
            break;

        case 1: // 【角色轮廓光】(Rim Light)
            // 魔法：引入面部 Ramp 贴图的 Alpha 参与夹角计算
            // 专为角色的外轮廓勾勒出漂亮的亮边
            NdotL = CalculateStylizedRimNdotL(Normal, LightDir, ViewDir, RampAlpha);
            break;

        case 2: // 【纯高光补光灯】(Specular Only)
            // 魔法：强行把漫反射颜色归零！
            // 作用：专门用来给眼球、武器刃口打高光斑，但绝不照亮周围的皮肤/布料
            diffuseAlbedo = vec3(0.0); 
            break;

        case 3: // 【植被透光】(Foliage 透射光)
            // 魔法：无视物体的真实法线，用世界Z轴硬算出一个垂直的切线方向
            vec3 fakeTangent = -normalize(cross(ObjectZ, cross(ObjectZ, LightDir)));
            NdotL = clamp(dot(Normal, fakeTangent), 0.0, 1.0);
            
            // 魔法：草地不需要油腻的物理高光，直接关闭
            specWeight = 0.0; 
            break;
    }

    // ---------------------------------------------------------
    // 3. 高光计算与最终叠加
    // ---------------------------------------------------------
    vec3 specularColor = vec3(0.0);
    
    // Type 3 (植被) 被特权豁免了高光计算
    if (lightType != 3) {
        // 计算标准的 GGX 高光，并乘以刚才决定的权重
        specularColor = CalculateGGX_BRDF(Normal, LightDir, ViewDir) * specWeight;
    }

    // 汇总：(漫反射 + 高光) * 灯光颜色 * 衰减
    vec3 currentLightResult = light.Color * attenuation;
    finalLightAccum += currentLightResult * (diffuseAlbedo * NdotL + specularColor);
}
```

![动图封面](../assets/endfield-rendering-study/26-动图封面.jpg)

额外光补光效果

### 最后的效果调整

这里还有一个效果调整，应该适用于在战斗之类时开启，让角色颜色标记、强描边显示之类的特效效果，所以这里草草略过

```
vec3 tonemappedColor;

// 引擎开关：是否激活该角色的专属风格化调色
if (EnableStylizedGrading > 0.5) 
{
    // ==========================================
    // 第一步：经典的 BSC（亮度、饱和度、对比度）与染色
    // ==========================================
    
    // 1. 饱和度 (Saturation): _44._m14
    // 将颜色的灰度值与原色混合。参数=0是纯黑白，=1是原色，>1是超饱和
    vec3 satColor = mix(vec3(Luminance(localLight)), localLight, Param_Saturation);
    
    // 2. 对比度 (Contrast): _44._m15
    // 将 0.5（中性灰）与当前颜色混合。参数>1时，亮的地方更亮，暗的地方更暗
    vec3 contrastColor = mix(vec3(0.5), satColor, Param_Contrast);
    
    // 3. 亮度乘数 (Brightness): _44._m13
    vec3 brightColor = contrastColor * Param_Brightness;
    
    // 4. 全局滤镜染色 (Tint Overlay): _44._m22
    // 用一个带 Alpha 的纯色，强行覆盖/混合当前的画面（比如进入狂暴状态时整个角色泛红）
    vec3 gradedColor = mix(brightColor, Param_TintColor.rgb, Param_TintColor.a);

    // ==========================================
    // 第二步：视角边缘光叠加 (View-based Fresnel Rim)
    // ==========================================
    
    // 计算视线与法线的夹角（Fresnel效应：越看向边缘，值越接近 1）
    float fresnel = 1.0 - clamp(viewDotShadingN, 0.0, 1.0);
    
    // 利用平滑步进(smoothstep)和宽度参数(_44._m16)切出一条锐利的亮边
    float rimShape = smoothstep(1.0 - Param_RimWidth, 1.0, fresnel) * fresnelMask;
    
    // 边缘光颜色(_44._m23) * 形状 * 边缘光强度(_44._m17)
    vec3 extraRim = Param_RimColor * rimShape * Param_RimIntensity;

    // 最终输出：调好色的底图 + 强加的边缘发光
    tonemappedColor = gradedColor + extraRim;
}
else
{
    // 如果开关没开，老老实实输出前面算好的光照结果
    tonemappedColor = localLightAccumColor;
}
```

### 雾效等其他效果

也是草草略过

```
// 如果引擎开启了雾效
if (EnableFog) 
{
    // ==========================================
    // 1. 基础消光（Extinction）：光线穿过空气时被挡住的程度
    // ==========================================
    // 基于片元高度 (Y) 和 摄像机距离 (viewDist)，用指数衰减公式计算
    vec3 fogExtinction = CalculateExponentialExtinction(fragPosWS.y, viewDist);
    
    // ==========================================
    // 2. 雾气密度积分（双层高度雾模型）
    // ==========================================
    vec3 fogInscatter;      // 雾的内散射颜色（雾本身的颜色）
    float fogTransparency;  // 穿过雾的透明度
    
    if (EnableVolumetricFog) 
    {
        // 【模式A：带体积雾贴图的高级雾】
        // 沿视线方向计算两层不同高度的指数雾密度
        float layerADensity = CalcLayerDensity(HeightA_Params);
        float layerBDensity = CalcLayerDensity(HeightB_Params);
        float baseFogDensity = clamp(layerADensity + layerBDensity, 0.0, 1.0);
        
        // 核心：生成伪随机噪声 (LCG Dither)，偏移采样坐标，防止雾效出现色带(Banding)
        vec3 ditherOffset = GenerateLCGNoise(pixelX, pixelY);
        
        // 采样 3D 体积雾贴图（包含云隙光、局部浓雾等数据）
        vec4 volFogSample = texture3D(VolFogTexture, UVW + ditherOffset);
        
        // 混合基础高度雾和 3D 体积雾
        fogInscatter = volFogSample.rgb + BaseFogColor * (1.0 - baseFogDensity) * volFogSample.a;
        fogTransparency = volFogSample.a * baseFogDensity;
    }
    else 
    {
        // 【模式B：简单双层指数高度雾】
        float layerADensity = CalcLayerDensity(HeightA_Params);
        float layerBDensity = CalcLayerDensity(HeightB_Params);
        float totalDensity = clamp(layerADensity + layerBDensity, 0.0, 1.0);
        
        fogInscatter = BaseFogColor * (1.0 - totalDensity);
        fogTransparency = totalDensity;
    }

    // ==========================================
    // 3. 物理大气散射计算 (瑞利散射 + 米氏散射)
    // ==========================================
    // 视线和太阳的夹角
    float viewDotSun = dot(-viewDirWS, SunDir);
    
    // 瑞利散射 (Rayleigh Phase)：模拟天空的蓝色，基于视角与太阳夹角
    float rayleighPhase = 0.0596 * (1.0 + viewDotSun^2);
    
    // 米氏散射 (Mie Phase)：使用 HG 相位函数，模拟太阳周围极其耀眼的光晕 (Halo)
    float miePhase = CalculateHenyeyGreenstein(viewDotSun, MieG_Factor);
    
    // 混合瑞利、米氏和环境光散射
    vec3 atmScatter = RayleighColor * rayleighPhase + AmbientScatter + MieColor * miePhase;

    // ==========================================
    // 4. 终极合成公式
    // ==========================================
    vec3 foggedColor = 
        // A. 角色原本的颜色，被空气遮挡后的剩余量
        (Color * fogExtinction * fogTransparency) + 
        // B. 大气散射的光（天光/太阳光晕）打进雾里，被你看到的量
        (atmScatter * (1.0 - fogExtinction) * fogTransparency) + 
        // C. 雾气本身的固有色（体积雾/高度雾积累）
        fogInscatter;

    finalColor = foggedColor;
}
else
{
    // 如果没开雾效，直接输出刚才算好的角色颜色
    finalColor = Color;
}
```

## 眼睛(略)

![](../assets/endfield-rendering-study/27-img-27.jpg)

眼睛流程图

## 头发(略)

![](../assets/endfield-rendering-study/28-img-28.jpg)

头发流程图

## 丝袜(略)

![](../assets/endfield-rendering-study/29-img-29.jpg)

丝袜流程图

## 后处理

后处理都压缩在一个pass里全部完成，包括一些锐化之类的，这里只对效果明显的后处理进行简单的说明

![动图封面](../assets/endfield-rendering-study/30-动图封面.jpg)

后处理

### 后处理前

![](../assets/endfield-rendering-study/31-img-31.jpg)

后处理前

### +色调映射ARRI LogC3

![](../assets/endfield-rendering-study/32-img-32.jpg)

色调映射

色调映射使用ARRI LogC3，先通过公式将线性颜色转换到LogC3，然后再去采样一张LUT完成色调映射

$$C\_{out} = \text{clamp} \left( 0.244161 \cdot \log\_{10} \big( \max(C\_{in} \cdot E \cdot 5.5555558 + 0.047996, 0) \big) + 0.386036,\ 0,\ 1 \right)$$

### +Bloom

![](../assets/endfield-rendering-study/33-img-33.jpg)

色调映射+Bloom

Bloom混合时的伪代码，sharpenedColor为原图

```
// ========== 阶段 8：Bloom 强度计算 ==========
bloomTexture     = sample(bloomTex, uv)
maxLuminance     = max(sharpenedColor.r, sharpenedColor.g, sharpenedColor.b)
bloomAmount      = clamp(maxLuminance - threshold, 0, maxAmount)   // 超出阈值的亮度

// ========== 阶段 10：Bloom 混合 ==========

// Step 1: 从锐化结果中抽出 Bloom 贡献
bloomLuminance   = max((CurveParam * bloomAmount) * bloomAmount, maxLuminance - threshold)
bloomFactor      = bloomLuminance / max(maxLuminance, 1e-4)
colorWithoutBloom = sharpenedColor * (1 - bloomFactor * bloomScale)

// Step 2: 处理 Bloom 纹理
bloomAdjusted    = pow(bloomTex, 0.33) * 1.494 - 0.7;
bloomSelect      = (bloomTexture > 0.3) ? bloomAdjusted : bloomTexture
bloomWeighted    = bloomSelect * bloomTint

// Step 3: 叠加 Bloom
colorWithBloom   = colorWithoutBloom + bloomWeighted

// Step 4: 混合开关
colorMixed       = lerp(sharpenedColor, colorWithBloom, bloomMix)
```

### +暗角

![](../assets/endfield-rendering-study/34-img-34.jpg)

色调映射+Bloom+暗角

```
// ========== 暗角计算 ==========

// Step 1: 归一化坐标（以中心为原点，0~1）
offset     = abs(uv - center) * lerp(scale, 1.0, mode)
coordX     = offset.x * lerp(1.0, 1.5 * clamp(scale * 1.05, 0, 1), mode)
coordY     = clamp(offset.y * lerp(1.0, scale * 2.0, mode) + max(scale - 2.8, 0) * 5.0, 0, 1)

// Step 2: 宽高比修正
coordX     = coordX * lerp(lerp(1.0, aspectRatio, aspectFlag), aspectRatio * 0.5625, mode)
coord      = clamp(coordX, coordY, 0, 1)

// Step 3: 径向遮罩（中心 1，边缘 0）
distSq     = coord.x * coord.x + coord.y * coord.y
mask       = pow(clamp(1.0 - distSq, 0, 1), falloff)

// Step 4: 应用暗角（边缘插值到 tint，中心保持白）
tint       = lerp(edgeTint, white, mask)
output     = color * tint
```

---

### 图片资源清单

| 序号 | 文件名 | 说明 | 大小 |
|------|--------|------|------|
| 01 | 01-img-1.jpg | img-1 | 1861KB |
| 02 | 02-img-2.jpg | img-2 | 2738KB |
| 03 | 03-动图封面.jpg | 动图封面 | 73KB |
| 04 | 04-动图封面.jpg | 动图封面 | 35KB |
| 05 | 05-img-5.jpg | img-5 | 533KB |
| 06 | 06-img-6.jpg | img-6 | 1050KB |
| 07 | 07-img-7.jpg | img-7 | 176KB |
| 08 | 08-img-8.jpg | img-8 | 31KB |
| 09 | 09-img-9.jpg | img-9 | 409KB |
| 10 | 10-img-10.jpg | img-10 | 630KB |
| 11 | 11-动图封面.jpg | 动图封面 | 35KB |
| 12 | 12-img-12.jpg | img-12 | 242KB |
| 13 | 13-img-13.jpg | img-13 | 14KB |
| 14 | 14-img-14.jpg | img-14 | 7KB |
| 15 | 15-img-15.jpg | img-15 | 1183KB |
| 16 | 16-img-16.jpg | img-16 | 148KB |
| 17 | 17-img-17.jpg | img-17 | 397KB |
| 18 | 18-img-18.jpg | img-18 | 922KB |
| 19 | 19-img-19.jpg | img-19 | 208KB |
| 20 | 20-img-20.jpg | img-20 | 178KB |
| 21 | 21-img-21.jpg | img-21 | 36KB |
| 22 | 22-img-22.jpg | img-22 | 633KB |
| 23 | 23-img-23.jpg | img-23 | 169KB |
| 24 | 24-动图封面.jpg | 动图封面 | 112KB |
| 25 | 25-img-25.jpg | img-25 | 581KB |
| 26 | 26-动图封面.jpg | 动图封面 | 35KB |
| 27 | 27-img-27.jpg | img-27 | 618KB |
| 28 | 28-img-28.jpg | img-28 | 546KB |
| 29 | 29-img-29.jpg | img-29 | 440KB |
| 30 | 30-动图封面.jpg | 动图封面 | 23KB |
| 31 | 31-img-31.jpg | img-31 | 202KB |
| 32 | 32-img-32.jpg | img-32 | 213KB |
| 33 | 33-img-33.jpg | img-33 | 208KB |
| 34 | 34-img-34.jpg | img-34 | 208KB |


---

### 参考链接

- [原文 - 知乎](https://zhuanlan.zhihu.com/p/2013370672647268314)

### 验证记录
- [2026-03-31] 璃使用 playwright+stealth 抓取全文+图片，保存到阿卡西记录

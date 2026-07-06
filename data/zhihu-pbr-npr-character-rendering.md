# 少前2-PBR+NPR角色渲染笔记

**标签**：#graphics #shader #npr #pbr #rendering #unity #urp #reference
**来源**：[知乎专栏](https://zhuanlan.zhihu.com/p/2054250788315255997)
**收录日期**：2026-07-06
**来源日期**：2026-01（文章发布月份，精确日期未知）
**状态**：⚠️ 待验证
**可信度**：⭐⭐⭐（社区公开文章，作者有实际项目验证）

### 概要

《少前2》角色卡通渲染方案的技术笔记，涵盖 PBR+NPR 混合渲染的 8 个模块：风格化 PBR 光照、脸部 SDF 阴影与高光、头发高光与刘海处理、眼睛多层结构、黑丝材质、等宽描边与修正、深度偏移边缘光、GT Tonemapping。每个模块均附代码实现和效果对比图。

### 内容

---

​

目录

收起

1：风格化PBR光照

2：脸部

3：头发

4：眼睛

5：黑丝

6：描边

7：边缘光

8：Tonemapping

参考资料：

看了不少讲角色卡通渲染的文章，这里也记录下我自己的实现，包括一些细节上的改进和思考。

效果视频：[bilibili.com/video/BV1ouTD69E2E](https://link.zhihu.com/?target=https%3A//www.bilibili.com/video/BV1ouTD69E2E)

效果图：

![](../assets/zhihu-pbr-npr-character-rendering/01-image.jpg)

效果图

---

主要思路就是PBR+[NPR](https://zhida.zhihu.com/search?content_id=277813574&content_type=Article&match_order=1&q=NPR&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODM1MTUwOTEsInEiOiJOUFIiLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNzc4MTM1NzQsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.hBcM_mMgyUl_TcTiT97otLFrCEEIRbS6vCaAlEwZWxs&zhida_source=entity)，大致有如下几个要点：

**1：风格化PBR光照：**直接光漫反射、直接光镜面反射、间接光漫反射、间接光镜面反射

**2：脸部：**基于SDF的阴影和高光

**3：头发：**头发高光、刘海投影、刘海半透

**4：眼睛：**高光、暗角、视差

**5：黑丝：**边缘厚度、各向异性GGX高光

**6：描边：**裁剪空间等宽描边、局部描边修正

**7：边缘光：**基于深度的等宽边缘光

**8：[Tonemapping](https://zhida.zhihu.com/search?content_id=277813574&content_type=Article&match_order=1&q=Tonemapping&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODM1MTUwOTEsInEiOiJUb25lbWFwcGluZyIsInpoaWRhX3NvdXJjZSI6ImVudGl0eSIsImNvbnRlbnRfaWQiOjI3NzgxMzU3NCwiY29udGVudF90eXBlIjoiQXJ0aWNsZSIsIm1hdGNoX29yZGVyIjoxLCJ6ZF90b2tlbiI6bnVsbH0.koEmEWMmhEscw0B7tIK29jhLVxGoqUdEdr6MzPsWi5M&zhida_source=entity)**

下面一一介绍

## 1：风格化PBR光照

角色身上的衣服、皮肤等都基于被美术"调教"过的PBR光照实现。

讲PBR理论基础的文章已经有很多了，这里就不展开了，具体可以看这个系列文章：[理论 - LearnOpenGL CN](https://link.zhihu.com/?target=https%3A//learnopengl-cn.github.io/07%2520PBR/01%2520Theory/)

这里主要贴一下Cook-Torrance反射率方程：

![](../assets/zhihu-pbr-npr-character-rendering/02-image.jpg)

Cook-Torrance反射率方程

**直接光漫反射：通过对上述方程中的NdotL进行Ramp贴图重映射，美术就可以控制漫反射的颜色过渡和明暗：**

```
float NoL = saturate(dot(N, L));
float2 rampUV = float2(NoL, 0.125);
half3 NoL_ramp = SAMPLE_TEXTURE2D(_ToonRamp, sampler_ToonRamp, rampUV).rgb;
```

效果：

![](../assets/zhihu-pbr-npr-character-rendering/03-image.jpg)

左边开了Ramp，右边没开，注意脖子

其中一张Ramp贴图：

![](../assets/zhihu-pbr-npr-character-rendering/04-image.jpg)

第四行：用于直接光Diffuse，第三行：用于直接光Specular

**直接光镜面反射：这里我的做法是 通过对Cook-Torrance BRDF镜面反射部分的D项进行归一化然后重映射到Ramp，美术就可以控制高光的渐变效果。**

这里的D项使用的是Trowbridge-Reitz GGX：

![](../assets/zhihu-pbr-npr-character-rendering/05-image.jpg)

Trowbridge-Reitz GGX

根据上述公式可得当NdotH = 1时，**D**为峰值：**D***max* = 1 / *πα*2，**D***normalized = **D** \* πα*2：

```
float d = NoH * NoH * (params.roughness2 - 1.0h) + 1.00001f;
float D_normalized = (params.roughness2 * params.roughness2) / (d * d);
float2 rampSpecUV = float2(D_normalized, 0.375);
half3 D_normalized_ramp = SAMPLE_TEXTURE2D(_ToonRamp, sampler_ToonRamp, rampSpecUV).rgb;
half3 specularTerm = D_normalized_ramp / params.roughness2 * v_term;
```

注意代码中没用到*π，因为我用的是*Mobile版BRDF（移动端性能更优）

效果：

![](../assets/zhihu-pbr-npr-character-rendering/06-image.jpg)

注意手臂上的高光。左：普通GGX，中：我修改后的，右：官方的

**间接光漫反射、间接光镜面反射：这两个我并没有在代码层面做特殊处理，使用的是普通的[SH+IBL](https://zhida.zhihu.com/search?content_id=277813574&content_type=Article&match_order=1&q=SH%2BIBL&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODM1MTUwOTEsInEiOiJTSCtJQkwiLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjoyNzc4MTM1NzQsImNvbnRlbnRfdHlwZSI6IkFydGljbGUiLCJtYXRjaF9vcmRlciI6MSwiemRfdG9rZW4iOm51bGx9.-CHecCWAFCPJeS4nkm59vaJ5FvLBVZTTIz6yedavsao&zhida_source=entity)。**

## 2：脸部

脸部阴影和高光是通过一张SDF图算出来的，贴图如下：

![](../assets/zhihu-pbr-npr-character-rendering/07-image.jpg)

R：阴影阈值 G&B：鼻头嘴唇的高光阈值 A：阴影Mask

**阴影计算方式：用角色forward向量和光照方向进行点积算出光照在脸部左右两个半球内的衰减值。用角色left向量和光照方向进行点积算出光照当前位于哪个半球内，用于反转U坐标。最后把采样得到的阴影阈值和光照衰减值做个smoothstep即可：**

```
float lightAtten = 1 - (dot(L, forward) * 0.5f + 0.5f);
float2 sdfuv = float2(dot(L, left) > 0 ? uv1.x : 1 - uv1.x, uv1.y);
half4 sdf = SAMPLE_TEXTURE2D(_SDF, sampler_SDF, sdfuv);
float faceShadowThresholdMin = lightAtten - _ShadowSmoothness;
float faceShadowThresholdMax = lightAtten + _ShadowSmoothness;
float faceShadow = smoothstep(faceShadowThresholdMin, faceShadowThresholdMax, sdf.r) * sdf.a;
```

**高光计算方式：同时对G通道和B通道做step，然后取两者交集，就能模拟出鼻头嘴唇的高光位移效果，不得不说很妙：**

```
float2 specUV = float2(1 - sdfuv.x, sdfuv.y);
half4 specSdf = SAMPLE_TEXTURE2D(_SDF, sampler_SDF, specUV);
half specArea1 = step(lightAtten, specSdf.g);
half specArea2 = step(1 - lightAtten, specSdf.b);
half specArea = specArea1 * specArea2;
```

效果：

[](https://vdn6.vzuu.com/LD/67236bee-73aa-11f1-b168-220ecaa5f889-v8_f2_t1_4hX9HKe9.mp4?pkey=AAW5_LEhEU5zRoOFkNunIQlvTee05FFJMsNXHLu64swI0Y_1J-9GVGVDwJ54pU0OIojdxhn_A1kfqmoaESh98Jtb&bu=da4bec50&c=avc.8.0&expiration=1783349492&f=mp4&pu=e59e796c&v=ks6&pf=Web&pt=zhihu)

![](../assets/zhihu-pbr-npr-character-rendering/08-image.jpg)

00:05

脸部阴影+鼻头和嘴唇高光点

## 3：头发

头发的漫反射没什么特别，值得一提的是模型做了球形法线映射，这样可以让光影保持干净：

![](../assets/zhihu-pbr-npr-character-rendering/09-image.jpg)

刘海的球形法线

**头发高光：**

首先看下头发高光所使用到的贴图和UV排布：

![](../assets/zhihu-pbr-npr-character-rendering/10-image.jpg)

头发高光贴图和UV排布

高光的处理方式也很简单，利用美术预先画好的贴图，用第二套UV去采样，然后顺着世界空间视线的Y方向对UV的V进行一个偏移，以此来达到高光随着视线上下移动的效果。注意这里需要把UV都打直，这样高光才能沿着头发上下移动。最后再用NdotH作为高光的Mask：

```
float specOffsetV = -V.y * _SpecOffsetSpeed + _SpecOffset;
half3 specularColor = SAMPLE_TEXTURE2D(_SpecularMap, sampler_SpecularMap, float2(uv1.x, uv1.y + specOffsetV)).rgb * _SpecColor;
float specIntensity = saturate(_SpecMinIntensity + pow(NoH, _SpecViewRange));
specularColor *= specIntensity;
```

效果如下：

[](https://vdn6.vzuu.com/SD/0743edea-76e1-11f1-96aa-5eee7a70f1d7-v8_f2_t1_m6aWcALi.mp4?pkey=AAV5PNBiXC-BrUcS_7jOR2rOs9TyKuzIDiIAjshXCYWglmppc9lSMbcns12ojriglFjZtiiujnIReoPdyh3buhGV&bu=da4bec50&c=avc.8.0&expiration=1783349492&f=mp4&pu=e59e796c&v=ks6&pf=Web&pt=zhihu)

![](../assets/zhihu-pbr-npr-character-rendering/11-image.jpg)

00:09

头发高光

**刘海投影：**

增加一个刘海Pass作为投影，用视图空间光照方向XY对投影进行偏移，只输出模板值。然后再增加一个脸部Pass用于绘制投影，只对投影模板值相同区域绘制就行了。这里有一点需要注意，刘海投影Pass做完XY偏移后，再加个视图空间+Z方向的偏移，确保刘海不会被脸剔除掉，效果如下：

[](https://vdn6.vzuu.com/SD/b60c580e-76ef-11f1-bd86-468f946f9aaa-v8_f2_t1_EVnCYv3d.mp4?pkey=AAX8dgShlweTwgGRlLTmX37DeCeTsv_i8HUU9v3XPoVnGPSENOcnvToMh01mp4X8Io9tzlyRnmkLuQ-yO2ndU64G&bu=da4bec50&c=avc.8.0&expiration=1783349492&f=mp4&pu=e59e796c&v=ks6&pf=Web&pt=zhihu)

![](../assets/zhihu-pbr-npr-character-rendering/12-image.jpg)

00:13

刘海投影

**刘海半透：**

在绘制眉毛、眼睫毛等需要透视效果的物体时，写入一个特定模板值。然后刘海的Forward Pass绘制时，只绘制不等于该模板值的片元。最后再增加一个透明刘海Pass，只绘制等于该模板值的片元就行了，效果如下：

![](../assets/zhihu-pbr-npr-character-rendering/13-image.jpg)

刘海半透

## 4：眼睛

眼睛一共有4层组成，分别是眼白，眼球，高光，阴影。眼白没什么特别的，主要看后面3层

贴图：

![](../assets/zhihu-pbr-npr-character-rendering/14-image.jpg)

左：眼球 右：高光和阴影

模型：

![](../assets/zhihu-pbr-npr-character-rendering/15-image.jpg)

从左到右分别是眼球，高光，阴影

**眼球透视：**

可以看到眼球的mesh是内凹结构，高光的mesh是外凸结构，两者贴合后，旋转视角时自然就会有眼球高光的透视效果。

**眼球高光：**

利用 混合模式：Blend One One 做了一次颜色叠加。

**眼球阴影：**

利用 混合模式：Blend DstColor Zero 做了一次正片叠底。

效果：

![](../assets/zhihu-pbr-npr-character-rendering/16-image.jpg)

眼白+眼球+高光+阴影

## 5：黑丝

这里我基于标准Cook-Torrance BRDF，做了以下两处改进：

**边缘厚度：**

通过改变 albedo 的边缘颜色来模拟黑丝边缘遮光的效果，增强边缘厚度感：

```
half3 Albedo(half3 baseColor, half3 N, half3 V)
{
    #if _EDGECOLOR_ON
        half NoV = saturate(dot(N, V));
        half edgeWeight = saturate(pow(1.0h - NoV, _EdgeColorRange) * _EdgeColorIntensity);
        half3 edgeColor = lerp(half3(1,1,1), _EdgeColor, edgeWeight);
        return baseColor * edgeColor;
    #else
        return baseColor;
    #endif
}
```

效果对比：

![](../assets/zhihu-pbr-npr-character-rendering/17-image.jpg)

左：未开边缘偏色 右：开启边缘偏色

**黑丝高光：**

采用各向异性GGX，来模拟黑丝上的拉丝高光效果：

```
inline float D_GGXaniso(float ax, float ay, float NoH, float3 H, float3 X, float3 Y)
{
    float XoH = dot(X, H);
    float YoH = dot(Y, H);
    float d = XoH * XoH / (ax * ax) + YoH * YoH / (ay * ay) + NoH * NoH;
    return 1 / max(HALF_MIN, ax * ay * d * d);
}

float ax = max(params.roughness * (1.0 + _AnisotropyIntensity), HALF_MIN_SQRT); 
float ay = max(params.roughness * (1.0 - _AnisotropyIntensity), HALF_MIN_SQRT);
float3 perturbedT = SafeNormalize(params.T.xyz - params.N * dot(params.T.xyz, params.N));
float3 perturbedB = cross(params.N, perturbedT) * params.T.w;
float D = D_GGXaniso(ax, ay, NoH, halfDir, perturbedT, perturbedB);
```

效果：

![](../assets/zhihu-pbr-npr-character-rendering/18-image.jpg)

黑丝上的各向异性GGX高光

## 6：描边

**描边基础实现：顶点沿平滑法线外扩，确保描边不会断裂，同时基于裁剪空间做透视抵消，确保描边是等宽的。**

具体细节：通过提前乘clipW来抵消透视除法带来的近粗远细，同时对clipW做了一个clamp限制，效果就是在一段固定的距离内等宽，超出这个距离会回归到透视，以此保证物体很远或者很近时描边看着不会太粗或者太细。需要注意屏幕宽高不一致带来的描边拉伸，原因是法线通过投影矩阵变换后，x分量已经做了一次除aspect的操作，此时如果对法线做normalize，就会使除aspect失效，结果就是经过屏幕坐标映射后，描边会被横向拉宽或者压扁，解决办法是先乘aspect再normalize最后再除aspect，代码如下：

```
float3 averageNormalCS = TransformWorldToHClipDir(averageNormalWS);
                
//消除屏幕宽高不一致导致的描边拉伸
float aspect = _ScreenParams.x / _ScreenParams.y;
averageNormalCS.x *= aspect;
averageNormalCS = normalize(averageNormalCS);
averageNormalCS.x /= aspect;

float width = _Width * 0.001;

// 对clipW做一个clamp限制，用来实现一定范围内的透视约束
float clipW = clamp(o.vertex.w, _MinPerspectiveConstrain, _MaxPerspectiveConstrain);
o.vertex.xy += averageNormalCS.xy * width * clipW;
```

未做描边修正的效果如下：

![](../assets/zhihu-pbr-npr-character-rendering/19-image.jpg)

未做描边修正的效果

看起来还不错，但是仔细看头部，会发现刘海、眼眶、嘴巴部分会有一些杂乱的描边出现，下面说一下修正方法。

**描边修正方法：将描边整体“往里推”。**

这里我并没有使用通过顶点色控制描边粗细来达到局部擦除，因为这种方法可能会存在一些问题，比如对前刘海局部进行擦除后，虽然人物正面朝摄像机时刘海的描边确实看不到了，但是当人物侧面对着摄像机时，刘海处的描边可能还是看不到，因为被永久擦除了，而我们希望的是正面时看不到，侧面时能看到。

这里我的做法是通过增加顶点在zBuffer中的深度值，把它“埋进”后面的实体中，这样当角色侧身对着相机时，由于后面没有实体，所以描边会重新出现：

```
float targetDepth = o.vertex.w + _Correction * 0.1 * v.color.r;
float targetClipZ = -targetDepth * UNITY_MATRIX_P[2][2] + UNITY_MATRIX_P[2][3];
float targetNdcZ = targetClipZ / targetDepth;
o.vertex.z = targetNdcZ * o.vertex.w;
```

代码也很简单，只要手动计算出最终的zBuffer中的深度值就行了。效果如下：

![](../assets/zhihu-pbr-npr-character-rendering/20-image.jpg)

描边修正

这里我只是简单的将头部Mesh的顶点色统一给了1来做的深度偏移，想要精确控制的话可以手动刷顶点色。

## 7：边缘光

可以考虑给角色再加一个边缘光，这里我采用的是基于深度对比的等宽边缘光，原理：

在视图空间中，对顶点的xy沿着法线的xy方向做一定量的偏移，将偏移后的顶点变换到屏幕空间，然后采样深度图，将深度图中的深度和偏移前顶点的深度做一个对比，如果深度差大于某个阈值，就认为该点位于“边缘”。

```
half3 N_VS = TransformWorldToViewNormal(N);
float3 offsetPositionVS = float3(positionVS.xy + N_VS.xy * (_RimLightWidth / 100.0), positionVS.z);
        
//将偏移后的顶点变换到屏幕空间
float4 offsetPositionCS = TransformWViewToHClip(offsetPositionVS);
float4 offsetPositionNDC = offsetPositionCS * 0.5f;
offsetPositionNDC.xy = float2(offsetPositionNDC.x, offsetPositionNDC.y * _ProjectionParams.x) + offsetPositionNDC.w;
offsetPositionNDC.zw = offsetPositionCS.zw;
float2 offsetScreenPos = offsetPositionNDC.xy / offsetPositionNDC.w;

//计算深度差
float offsetDepth = SAMPLE_TEXTURE2D(_CameraDepthTexture, sampler_CameraDepthTexture, offsetScreenPos).r;
float offsetLinearEyeDepth = LinearEyeDepth(offsetDepth, _ZBufferParams);
float depthDifference = offsetLinearEyeDepth - ndcW;
float rimMask = smoothstep(0, (_RimLightThreshold / 100.0), depthDifference);
```

效果如下：

![](../assets/zhihu-pbr-npr-character-rendering/21-image.jpg)

基于深度差的等宽边缘光

可以再做一个光源方向的判定，让受光面显示边缘光，背光面边缘光消失：

```
float NoL = saturate(dot(light.direction, N));
float lightMask = pow(NoL, _LightMaskPow_Rim);

rimMask = lerp(0.0, rimMask, lightMask);
```

效果如下：

![](../assets/zhihu-pbr-npr-character-rendering/22-image.jpg)

受光面显示边缘光，背光面边缘光消失

## 8：Tonemapping

为了将HDR映射到LDR来保留更多的色阶变化，需要在后处理阶段做一次Tonemapping。

Tonemapping的算法有很多，这里我采用的是[GT Tonemapping](https://zhida.zhihu.com/search?content_id=277813574&content_type=Article&match_order=1&q=GT+Tonemapping&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODM1MTUwOTEsInEiOiJHVCBUb25lbWFwcGluZyIsInpoaWRhX3NvdXJjZSI6ImVudGl0eSIsImNvbnRlbnRfaWQiOjI3NzgxMzU3NCwiY29udGVudF90eXBlIjoiQXJ0aWNsZSIsIm1hdGNoX29yZGVyIjoxLCJ6ZF90b2tlbiI6bnVsbH0.xck4G4XCzMwFxy9ca0feRraG2ms7rWJtfBTlJYw5osg&zhida_source=entity)：[GT Tonemap](https://link.zhihu.com/?target=https%3A//www.desmos.com/calculator/gslcdxvipg%3Flang%3Dzh-CN)

```
float GTTonemapCurve(float x)
{
    float P = 1;
    float a = 1; 
    float m = 0.22;
    float l = 0.4;
    float c = 1.33;
    float l0 = (P - m) * l / a;
    float L_x = m + a * (x - m);
    float T_x = m * pow(x / m, c);
    float S0 = m + l0;
    float S1 = m + a * l0;
    float C2 = a * P / (P - S1);
    float S_x = P - (P - S1) * exp(-(C2 * (x - S0) / P));
    float w0_x = 1 - smoothstep(0.0, m, x);
    float w2_x = x <= m + l0 ? 0 : 1;
    float w1_x = 1 - w0_x - w2_x;

    float f_x = T_x * w0_x + L_x * w1_x + S_x * w2_x;
    return f_x;
}

half3 GranTurismoTonemap(half3 input)
{
    return half3(GTTonemapCurve(input.r), GTTonemapCurve(input.g), GTTonemapCurve(input.b));
}
```

下面是几种Tonemapping的效果对比：

![](../assets/zhihu-pbr-npr-character-rendering/23-image.jpg)

从左到右分别是：None、Neutral、ACES、GT

至此，全篇完，感谢观看。

## **参考资料：**

[少女前线2：追放 vepley角色渲染分析还原](https://zhuanlan.zhihu.com/p/663968812)

[仿原神卡通渲染：NDC简介与等宽屏幕空间边缘光原理](https://zhuanlan.zhihu.com/p/714177282)

[二次元角色卡通渲染—面部篇](https://zhuanlan.zhihu.com/p/411188212)

[【Unity URP】卡通渲染中的刘海投影·改](https://zhuanlan.zhihu.com/p/416577141)

---

### 参考链接

- [原文 - 知乎专栏](https://zhuanlan.zhihu.com/p/2054250788315255997)
- [参考资料1 - 少女前线2：追放 vepley角色渲染分析还原]()
- [参考资料2 - 仿原神卡通渲染：NDC简介与等宽屏幕空间边缘光原理](https://zhuanlan.zhihu.com/p/165316070)
- [参考资料3 - 二次元角色卡通渲染—面部篇]()
- [参考资料4 - Unity URP 卡通渲染中的刘海投影·改]()

### 相关记录

- [深度偏移边缘光](./depth-offset-rim-light.md) — 从本文第 7 节提取的独立技术分析

### 验证记录

- [2026-07-06] 学习用途本地留档，来源：知乎专栏文章离线保存

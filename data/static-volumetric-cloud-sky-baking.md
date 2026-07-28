# 静态体积云天空的高质量离线烘焙

**标签**：#unity #graphics #shader #rendering #experience
**来源**：项目实现与 Unity 编辑器实测（主体）；Guerrilla Games Horizon/Nubis 与 EA Frostbite 公开技术资料（理论和方案参照）
**收录日期**：2026-07-27
**来源日期**：2015-08 / 2016-07 / 2026-07-27（实践验证）
**更新日期**：2026-07-28
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐（公开技术资料 + Unity 编辑器内多视角实践验证）
**适用版本**：Unity 2021.3+；Built-in/URP 天空盒路径

### 概要

当云形、天气和时间段只需要离散预设时，可以把体积云的高成本密度与光照积分完全移到 Editor。当前实现用球壳定义云层，在 Shader 中程序化计算 Gradient FBM、Worley、天气覆盖率、Beer–Lambert 消光、双叶 Henyey–Greenstein、Powder 与四阶多重散射近似，再把结果按 128×128 瓦片写入一张 HDR 半八面体母图。发布阶段转换为单张 LogRGB 纹理，Player 只保留一次二维采样。

本文重点记录可复现的原理、实现链路、参数关系、失败模式和验证边界；Horizon/Nubis/Frostbite 是理论与设计参照，不代表当前代码逐行复刻这些引擎。

### 内容

#### 记录定位与来源边界

本文主体是当前项目实现与 Unity 编辑器实测。公开资料提供了 Perlin–Worley 密度、天气控制、相位函数和多重散射近似等设计依据，但当前实现采用程序化噪声、固定垂直剖面和一组经过项目调试的经验系数。引用这些资料不能等同于“完整复刻 Horizon/Nubis/Frostbite”。

#### 端到端实现链路

~~~text
ScriptableObject 烘焙参数
    ↓ 归一化、单位和输出目录检查
离线烘焙 Material
    ↓ 每个 128×128 瓦片执行体积积分
RGBAHalf 线性 HDR 瓦片
    ↓ 按整图像素位置写回
完整半八面体 RGBAHalf 母图
    ├─ 可选：导出 EXR 母版
    └─ LogRGB 编码为 8-bit PNG
            ↓ Unity 导入
       Linear / Mipmap / Clamp / Trilinear / Android ASTC 4×4
            ↓
       运行时天空 Shader：一次 Texture2D 采样
~~~

必须把“体积云求解”“方向到二维布局”“HDR 有限位深编码”“运行时 Tone Mapping”看成四个独立层次。某一层出现接缝、色带或过曝时，应先定位发生阶段，而不是改另一层掩盖问题。

#### 适用边界

该方案适合以下目标：

- 云形、天气状态与时间段是离散预设，不要求连续实时演化。
- 太阳可以作为静态天空的一部分；闪电等瞬态发光单独叠加。
- 离线烘焙优先追求画质，运行时优先追求低采样和低带宽。

如果运行时需要连续改变云量、太阳高度、风场或云层自阴影，应改用实时/半实时体积云，而不是把大量状态硬烘焙成纹理集合。

#### 云层几何：使用球壳而不是平面层

##### 坐标和单位

- 行星半径、相机海拔、云底、云顶和最大步进距离统一以千米计。
- 行星中心位于世界原点；相机位于 (0, planetRadius + cameraAltitude, 0)。
- 输出只覆盖上半球，下半球由运行时地面色和地平线雾处理。
- 当前求交逻辑假设相机位于云底以下。相机进入云层或高于云顶时，必须改写区间选择。

##### 为什么平面层在地平线失真

射线接近平行于平面时，与平面层的交点距离会急剧增加，常见结果是地平线云被拉成无限厚带、步长随方向剧烈变化，并依赖任意的最大距离截断。

球壳使用两个同心球：

~~~text
Rbottom = Rplanet + cloudBottomAltitude
Rtop    = Rplanet + cloudTopAltitude
~~~

地平线附近的路径仍会增长，但受到有限球壳几何约束，曲率和尺度更可信。

##### 射线—球体求交

射线为 p(t) = o + t d，其中 d 已归一化。代入 |p|² = r²：

~~~text
b = dot(o, d)
c = dot(o, o) - r²
Δ = b² - c
tNear = -b - sqrt(Δ)
tFar  = -b + sqrt(Δ)
~~~

Δ < 0 表示没有交点。当前相机在内球下方，所以云段起点取云底球的远交点，终点取云顶球的远交点；若行星表面先于云底被击中，则该方向不积分云。最后把终点限制为 start + maximumMarchDistance。

这种写法是“地面观察天空”的专用简化。通用球壳算法必须根据相机位于内球、壳层或外球三种情况分别选择有效区间。

#### 密度建模

当前密度不是采样一张预生成的 3D Perlin–Worley 纹理，而是在每个 Ray March 样本中直接计算 Gradient Noise、FBM 和 Worley F1。这对实时渲染非常昂贵，但符合“只在 Editor 离线运行”的目标。

##### 径向高度和固定垂直剖面

~~~text
radialHeight = |worldPosition| - (Rplanet + cloudBottom)
layerThickness = cloudTop - cloudBottom
h = radialHeight / layerThickness
~~~

h <= 0 或 h >= 1 时密度为零。当前高度函数：

~~~text
baseRise    = smoothstep(0.00, 0.12, h)
topFalloff  = 1 - smoothstep(0.62, 1.00, h)
heightShape = saturate(baseRise * topFalloff)
~~~

它让云底在前 12% 厚度内长出，62% 高度后逐渐衰减到云顶。当前不是可编辑 Cloud Profile 曲线；要制作积云、层云等明显不同垂直结构，需要把这些固定阈值参数化或改为剖面纹理。

##### 局部噪声坐标与浮点精度

直接把约 6371 km 的世界 Y 坐标送进噪声，会把巨大常量带入浮点运算。当前实现把 Y 改成局部径向高度：

~~~hlsl
float3 localPosition = float3(
    worldPosition.x,
    radialHeight + cloudBottomAltitude,
    worldPosition.z) + noiseOffset;
~~~

基础噪声的 Y 频率再乘 3.25，避免只有数千米厚的云层在垂直方向变化不足而形成竖墙。X/Z 仍是观察点附近的局部平面坐标，因此该噪声适合地表天空，不是完整行星尺度、严格无极点的球面天气参数化。

##### 基础形状：Gradient FBM + Worley

1. Gradient Noise 每个格子计算 8 个角点梯度，并用五次 Hermite 曲线插值。
2. FBM 叠加 4 个 octave：频率每阶约乘 2.03，振幅乘 0.5。
3. Worley F1 搜索相邻 3×3×3 共 27 个格子的最近特征点。
4. 使用 1 - WorleyF1 得到团块内部，再与 FBM 混合。

当前组合近似为：

~~~text
perlinWorley = saturate(
    lerp(perlin,
         lerp(1 - worleyF1, 1, perlin),
         0.32))
~~~

这借鉴了 Perlin–Worley 的造型思路，但具体噪声实现、频率和 0.32 混合系数属于当前项目。

##### 天气覆盖率

天气噪声只使用 X/Z，固定频率为 0.012，并叠加 3 个 octave：

~~~text
localCoverage = saturate(
    coverage + (weather - 0.5) * coverageVariation)

threshold = 1 - localCoverage
density = saturate(
    (perlinWorley - threshold) / max(localCoverage, 0.04))
~~~

- coverage 决定基础云量，即哪些区域能生成云。
- coverageVariation 决定不同方向的晴区/阴区差异。
- densityMultiplier 不参与这里的形状阈值；它稍后控制已有云体的光学厚度。

因此“总体云量”和“密度倍率”不可混为一谈。想增加云块却只提高密度倍率，通常只会让现有云更黑。

##### 高频细节侵蚀

只有基础密度大于 0.001 时才计算高频细节：

~~~text
edgeWeight = saturate(1 - density)
density = saturate(
    density
    - (1 - detail)
    * detailErosion
    * (0.35 + edgeWeight))
~~~

薄边的 edgeWeight 更高，因此侵蚀优先发生在轮廓。朝太阳的阴影步进会关闭高频细节，降低离线成本并让自阴影更平滑；这也意味着阴影不会还原所有细碎云边。

#### 光照模型

##### Beer–Lambert 和前向合成

一个视线步长 ds 内：

~~~text
sigmaT = density * densityMultiplier
stepT  = exp(-sigmaT * ds)
alpha  = 1 - stepT
~~~

从近到远合成：

~~~text
L += Tview * Lsample * alpha
Tview *= stepT
~~~

当 Tview < 0.002 时提前退出，因为后续样本贡献已很小。

##### 朝太阳的阴影步进

每个有效视线样本再朝太阳方向走 lightSteps 次：

~~~text
opticalDepth += baseDensity * densityMultiplier * lightStep
Tlight = exp(-opticalDepth)
~~~

阴影步进从每段中点采样，不计算高频侵蚀，并在 opticalDepth > 12 时提前退出。它嵌套在视线步进内部，是主要离线成本来源之一。

##### 双叶 Henyey–Greenstein

~~~text
HG(μ, g) = (1 - g²) /
           (4π * (1 + g² - 2gμ)^(3/2))
~~~

μ = dot(viewDirection, sunDirection)。当前实现混合正 g 的前向叶和负 g 的后向叶：

~~~text
phase = lerp(
    HG(μ, forwardG),
    HG(μ, backwardG),
    backwardWeight)
~~~

forwardG 越接近 1，太阳附近银边越集中；backwardWeight 用于补充背向太阳观察时的响应。

##### 四阶多重散射近似

当前代码不是严格路径追踪，而是累加 4 个逐渐变宽、能量逐渐降低的相位叶：

~~~text
energy₀ = 1
transmittance₀ = Tlight
g₀ = userG

每一阶：
scatter += DualPhase(μ, g) * transmittance * energy
energy *= 0.52 * multipleScatteringStrength
transmittance = transmittance^0.62
g *= 0.55
~~~

它能恢复厚云内部被单次散射丢失的柔和能量，但不能当作物理准确的高阶散射解。代码中的 0.52、0.62、0.55 和直射光整体倍率均是经验参数。

##### 环境光与 Powder

环境光根据云样本归一化高度在 0.18～0.62 之间插值，再乘用户的环境云颜色。当前实现没有单独的地面反弹光项。虽然烘焙参数会把 groundColor 传给 Shader，但半八面体烘焙方向不会低于地平线，所以该值目前不影响发布的上半球纹理；运行时下半球使用天空材质自己的 GroundColor。

~~~text
powder = 1 - exp(-sigmaT * ds * 2)
powderFactor = lerp(
    1,
    max(0.25, powder * 2),
    powderStrength)
~~~

powderStrength > 1 时 lerp 会外插，可能快速推高受光能量，因此 1～2 区间应视为强艺术参数而不是物理范围。

##### 太阳圆盘和柔光

~~~text
sunAngle = acos(dot(viewDirection, sunDirection))
disc = 1 - smoothstep(radius - edgeWidth, radius, sunAngle)
glowRadius = max(radius * 12, 0.25°)
glow = exp2(-(sunAngle / glowRadius)²) * 0.12
~~~

sunAngularRadiusDegrees = 0.27° 约等于真实太阳角半径；提高到 0.5°～2° 可获得卡通化大太阳，并同步扩大外围柔光。

#### 子像素采样与步进抖动

每个输出纹素重复 samplesPerPixel 次完整积分。每次使用不同随机种子：

1. 在半八面体 UV 内加入小于一个纹素的二维偏移，改善方向域边缘锯齿。
2. 在首个视线步内使用随机 jitter，打散固定步长形成的层纹。
3. 对所有子样本求平均。

这不是时序抗锯齿，因为所有样本在同一次离线烘焙中完成；不会引入运行时历史缓冲或运动向量。

#### 瓦片化避免 TDR

##### 成本为什么会爆炸

最坏成本近似为：

~~~text
C ≈ texelCount * samplesPerPixel *
    [viewSteps * densityCost
     + viewSteps * cloudHitRate *
       (lightSteps * shadowDensityCost + phaseCost)]
~~~

一次密度计算内部又包含多 octave Gradient Noise 和 27 邻域 Worley。分辨率翻倍时纹素数变为 4 倍；提高子样本会重复整套积分；光照步则嵌套在有效视线样本内。

Windows TDR 监控的是一次 GPU 工作长时间无响应，而不是整项任务总耗时。一次全图 Draw 可能触发 watchdog；拆成小 Draw 后，总任务仍然很重，但每次提交更容易保持在可接受时长内。

##### 当前瓦片实现

- 每块临时 RenderTexture 使用 ARGBHalf、Linear。
- CPU 汇总纹理使用 RGBAHalf。
- BakeUvScaleOffset 把瓦片局部 UV 还原到整图 UV。
- 随机种子使用整图像素坐标，而不是瓦片局部坐标。
- 每块读回后写入完整 HDR 纹理。
- 所有瓦片共用完全相同的云、太阳和曝光参数。

128×128 是当前机器实测稳定值，不是所有 GPU 的通用常数。如果瓦片使用局部 UV 或局部随机种子，会在边界出现方向断裂、噪声重复或采样相位跳变。

#### 推荐调参顺序

##### 先理解质量成本

| 参数 | 主要影响 | 增大后的收益 | 主要代价/风险 |
|---|---|---|---|
| 分辨率 | 方向域空间细节 | 云边更清晰、太阳更圆 | 像素数按平方增长 |
| 视线步数 | 云体积分 | 轮廓和远处层次稳定 | 近似线性增加主循环 |
| 光照步数 | 自阴影 | 光穿透和厚度更细致 | 嵌套在有效视线样本内 |
| 每像素子样本 | 空间/步进抗噪 | 减少层纹和细线锯齿 | 重复整套积分 |
| 最大步进距离 | 地平线覆盖 | 避免远处云被截断 | 视线步数固定时会增大单步长度，可能降低积分精度；不一定增加循环次数 |

| 阶段 | 分辨率 | 视线步 | 光照步 | 子样本 | 用途 |
|---|---:|---:|---:|---:|---|
| 快速构图 | 512 | 96 | 10 | 1～2 | 云量、噪声、太阳位置 |
| 质量评估 | 1024 | 192 | 20～24 | 4 | 多视角检查 |
| 最终候选 | 2048 | 256～384 | 24～32 | 4～8 | 仅在前一级确有不足时使用 |

最终候选不是默认值。先测单瓦片耗时和显存，再决定是否提高。

##### 调参顺序

1. 固定低成本质量档，避免画质参数掩盖构图变化。
2. 调总体云量和区域变化，确定晴/阴分布。
3. 调基础噪声频率，确定大云团尺度。
4. 调细节频率和侵蚀，确定云边。
5. 调云底、云顶和密度倍率，确定厚度与压迫感。
6. 调太阳方向、颜色、角半径。
7. 调前/后向散射、环境光、Powder、多重散射。
8. 最后提高视线步、光照步、子样本和分辨率。

每次只改变一组职责相近的参数，并使用新输出名保留 A/B 结果。

##### 常见失败与定位

| 现象 | 优先检查 | 原因 |
|---|---|---|
| 整片阴天、几乎无结构 | 总体云量、区域变化 | 阈值过低使基础噪声大面积通过 |
| 云有多少不变，只是更黑 | 密度倍率 | 密度倍率改变消光，不改变主要覆盖范围 |
| 云边碎成噪点 | 细节频率、侵蚀、分辨率 | 细节超过输出纹素可表达频率 |
| 地平线云被切断 | 最大步进距离、球壳区间 | 积分范围过短 |
| 出现固定层纹 | 视线步数、首步 jitter | 步长过大且采样相位固定 |
| 自阴影块状 | 光照步数、阴影密度 | 光方向积分分辨率不足 |
| 太阳附近剪白 | 太阳 HDR 强度、散射、Tone Mapping | 峰值过高而肩部不足 |
| 单次高质量烘焙崩溃 | 瓦片尺寸、单 Draw 时长 | 可能触发 Windows TDR |
| 瓦片边界可见 | 全局 UV、全局像素种子 | 瓦片错误地使用局部坐标 |

#### 验证方式

静态天空不能只看一个镜头。画面至少检查：

- 迎光：太阳圆盘、高光肩部、云边剪白。
- 侧光：云体结构和中间调层次。
- 背光：环境光是否过灰或暗部死黑。
- 天顶：平滑渐变、量化色带和噪声。
- 地平线四个象限：半八面体边缘、雾带和远处截断。

工程侧还需要检查：

- Shader 编译消息为零。
- 高质量烘焙不再触发 TDR。
- 输出纹理尺寸、Linear、Mip、Clamp、平台压缩设置正确。
- 瓦片边界在颜色和噪声相位上连续。
- 运行时天空仍保持预期采样次数。

#### 实现检查清单

- [ ] 参数单位统一，保存前归一化太阳方向并夹紧步数。
- [ ] 相机位于当前球壳求交逻辑支持的位置。
- [ ] 烘焙 RenderTexture 和 CPU 母图都使用线性 HDR 格式。
- [ ] 瓦片使用整图 UV 与整图像素种子。
- [ ] HDR 母图先完成，再进入发布编码。
- [ ] 发布纹理的编码参数与运行时解码参数一致。

#### 当前实现的明确限制

- 大气背景是地平线色—天顶色渐变，不是完整物理大气散射。
- 多重散射、Powder 和能量系数均为艺术近似。
- 阴影步进省略高频细节，不能还原所有细碎自阴影。
- 没有单独地面反弹光，也没有场景几何参与云层遮挡。
- 烘焙参数中的 groundColor 当前不影响上半球输出；它不是云底反弹光参数。
- 噪声坐标适合局部地表观察，不是完整行星球面天气系统。
- 闪电局部光、动态云影和真机 VR 双眼属于后续模块。

### 关键代码

~~~hlsl
float RaySphereFar(float3 origin, float3 direction, float radius)
{
    float b = dot(origin, direction);
    float c = dot(origin, origin) - radius * radius;
    float discriminant = b * b - c;
    return discriminant >= 0.0 ? -b + sqrt(discriminant) : -1.0;
}
~~~

```hlsl
// 省略边界检查后的核心前向合成；函数名对应当前实现。
float stepLength = (endDistance - startDistance) / max((float)viewSteps, 1.0);
float transmittance = 1.0;

for (int i = 0; i < viewSteps && transmittance > 0.002; i++)
{
    float density = SampleDensity(samplePosition, true);
    if (density > 0.001)
    {
        float sigmaT = density * densityMultiplier;
        float stepT = exp(-sigmaT * stepLength);
        float alpha = 1.0 - stepT;
        float lightT = LightTransmittance(samplePosition);
        float3 direct = sunColor *
            MultipleScatteringLighting(lightT, cosineTheta) * 3.5;
        float3 lighting = direct * powderFactor + ambient;
        accumulatedLight += transmittance * lighting * alpha;
        transmittance *= stepT;
    }
    samplePosition += rayDirection * stepLength;
}
```

### 参考链接

- [The Real-time Volumetric Cloudscapes of Horizon: Zero Dawn](https://advances.realtimerendering.com/s2015/The%20Real-time%20Volumetric%20Cloudscapes%20of%20Horizon%20-%20Zero%20Dawn%20-%20ARTR.pdf) - Perlin–Worley 云密度与实时体积云基础。
- [Nubis: Authoring Real-Time Volumetric Cloudscapes with the Decima Engine](https://www.guerrilla-games.com/read/nubis-authoring-real-time-volumetric-cloudscapes-with-the-decima-engine) - 云层创作与天气控制。
- [SIGGRAPH 2016 Course: Physically Based Shading in Theory and Practice](https://blog.selfshadow.com/publications/s2016-shading-course/) - Frostbite《Physically Based Sky, Atmosphere and Cloud Rendering》课程入口及原始演示文稿。

### 相关记录

- [半八面体单图 HDR 天空的编码、采样与色带治理](./hemi-octahedral-hdr-sky-texture.md) - HDR 母图之后的方向布局、编码、导入和发布链路。
- [色带（Color Banding）与抖动（Dithering）知识](./color-banding-dither.md) - 静态天空平滑渐变的输出量化问题。
- [URP 天空盒 Shader 机制与常见问题](./urp-skybox-notes.md) - Unity 天空盒渲染路径注意事项。

### 验证记录

- [2026-07-27] 在 Unity 编辑器中完成 512×512、192 视线步、24 光照步、4 子样本的瓦片化烘焙，并从迎光、侧光、背光、天顶四个方向检查；高负载单 Draw 曾触发编辑器/GPU 故障，改为 128×128 瓦片后稳定完成。
- [2026-07-28] 原理与实现过程扩写：按当前 Shader/C# 实现补齐球壳求交、密度公式、光照积分、多重散射近似、子像素采样、瓦片化、成本模型、参数关系、失败诊断和实现限制。明确公开资料是理论参照，当前程序化噪声与经验常数属于项目实现。
- [2026-07-28] 参数语义复核：确认固定视线步数下，增大最大步进距离主要会增大单步长度而非循环次数；确认 groundColor 当前不会进入上半球烘焙结果，也不是云底反弹光参数，已在正文标明。
- [2026-07-28] 来源性复核：原 EA Frostbite PDF 直链返回 404，改用可访问的 SIGGRAPH 2016 课程索引；该页面仍提供 Frostbite 原始演示文稿。

---

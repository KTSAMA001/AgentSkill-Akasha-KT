# 半八面体单图 HDR 天空的编码、采样与色带治理

**标签**：#graphics #shader #hdr #performance #experience
**来源**：项目实现与 Unity 编辑器实测（主体）；GDC 2022《Advanced Weather System for Mobile Game: 'Dark Area'》（方案启发与外部参照）；JCGT 单位向量编码论文；Khronos 色彩传递函数规范；Arm ASTC 官方指南
**收录日期**：2026-07-27
**来源日期**：2014 / 2022 / 2026-07-27（实践验证）
**更新日期**：2026-07-27
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐（公开编码理论 + Unity 编辑器内实现与多视角验证）
**适用版本**：Unity Shader Model 3.0+；移动端 ASTC 平台

### 概要

只需要上半球天空时，可把方向映射到一张铺满正方形的半八面体二维纹理。运行时使用一次普通 `Texture2D` 采样；HDR 数据以逐通道 LogRGB 编码到 8-bit PNG，优先把码值分给天空常见的中低亮度，再在 Tone Mapping 后加入低幅度屏幕空间抖动，分别治理源纹理量化和最终输出量化造成的色带。

### 内容

#### 记录定位与来源层级

本文是项目实现与验证记录，不是《暗区突围》GDC 演讲的内容复述。项目最初参考该分享中的半八面体天空、体积云缓存和有限位深压缩思路，随后围绕自身的静态天空需求完成了编码方案对比、Unity 资产导入、运行时采样、风格化调色和色带治理。

文中的结论按来源分为三层：

1. **项目实践结论**：平方根 RGB 与逐通道 LogRGB 的对比、`range = 8` 与 `K = 16` 的验证起点、ASTC 4×4 设置、Tone Mapping 后低幅度 Dither，以及迎光、侧光、背光、天顶四类视角检查。这些内容构成本文主体。
2. **GDC 方案启发**：半八面体参数化、将体积云结果缓存到二维纹理、面向旧设备的 RGBA8 压缩、预曝光与 Gamma 压缩。它们用于说明技术路线的来源背景，不代表本文逐项复刻了《暗区突围》的实现。
3. **公开理论依据**：八面体方向编码、非线性颜色传递、8-bit 量化、ASTC 块压缩和 Tone Mapping，用于解释项目中观察到的 LogRGB、色带与等高线现象。

因此，本文不能被概括为“《暗区突围》体积云方案”：它记录的是受该分享启发后，在不同生命周期和资产约束下完成的一套项目实现。

#### 数据表示与处理链路

这套方案包含两个相互独立的问题：

1. **半八面体映射**：把头顶整个上半球的方向摊平到一张正方形纹理，解决方向数据的二维布局问题。
2. **HDR 编码**：先压缩数值范围，写入每通道只有 256 个整数档位的纹理，运行时再解码，解决高动态范围颜色的有限位深存储问题。

完整数据流如下：

```text
场景线性 HDR 颜色 c
    ↓ 非线性编码（平方根或 LogRGB）
0～1 编码值 e
    ↓ 8-bit 量化：q = round(255 * e)
纹理中的整数码值 q（0～255）
    ↓ 采样并反向解码
近似还原的 HDR 颜色 ĉ
    ↓ Color Grading / Tone Mapping
0～1 显示颜色
    ↓ 低幅度 Dither 后输出
屏幕像素
```

编码只改变有限码值的分配方式，不会把 8-bit 变成更高精度。一旦两个原始颜色被量化成同一个整数码值，后续步骤无法恢复它们原来的差异。

#### 半八面体映射的定位

Cubemap 虽然包含六个面，但一次 cubemap 查询通常仍是一次纹理采样，不能错误表述为“每像素采六次”。选择半八面体单图的真正收益是：

- 只保存当前需求中的上半球，减少无用下半球数据。
- 使用常规二维纹理资产、导入设置和 `tex2D` 路径。
- 四条正方形边统一对应地平线，便于用窄雾带处理映射边缘。
- 基础天空、闪电增量和区域遮罩可复用完全一致的方向到 UV 公式。

代价是不同方向的纹素面积不均匀，且边角/边缘附近需要特别检查过滤与 mipmap 行为。

#### 上半球方向到正方形

对单位方向 `n`，先限制 `n.y >= 0`，再做 L1 归一化。将 XZ 平面上的菱形旋转/剪切到正方形：

```hlsl
float2 EncodeHemiOctahedron(float3 n)
{
    // 本纹理只保存上半球；下半球由地面或地平线雾单独处理。
    n.y = max(n.y, 0.0);

    // L1 归一化把单位半球压到八面体表面；epsilon 避免零方向除零。
    float invL1 = rcp(max(abs(n.x) + n.y + abs(n.z), 1e-5));
    float2 diamond = n.xz * invL1;

    // 把 XZ 菱形旋转/剪切成正方形，再从 -1～1 映射到纹理 UV 的 0～1。
    float2 square = float2(
        diamond.x + diamond.y,
        diamond.x - diamond.y);
    return square * 0.5 + 0.5;
}
```

参数和中间变量：

- `n`：从相机指向天空的单位方向，`x/z` 是水平方向，`y` 是向上分量。
- `invL1`：`1 / (|x| + y + |z|)`；不是亮度，而是方向映射所需的 L1 归一化系数。
- `diamond`：上半球在二维平面上的菱形坐标。
- `square`：将菱形变换后的正方形坐标。
- 返回值：可直接用于 `Texture2D` 采样的 0～1 UV。

运行时下半球可以直接输出地面/雾色，不需要采天空纹理。

#### 为什么平方根 RGB 仍可能出现大块色带

##### 平方根编码的完整定义

对 RGB 三个通道分别执行：

```text
e = sqrt(saturate(c / R))
q = round(255 * e)
ĉ = R * (q / 255)^2
```

各参数含义：

| 符号 | 含义 | 取值与边界 |
|---|---|---|
| `c` | 要保存的场景线性 HDR 颜色；实际是 RGB 三个通道分别计算 | 非负，可以大于 1；它不是已经做过 sRGB/Gamma 编码的屏幕颜色 |
| `R` | `Range`，预先选定的最大可表示 HDR 值，不是 Red 红通道 | 必须与 `c` 使用相同单位；`c > R` 时会被截到 `R` |
| `e` | 尚未量化的编码值 | 0～1 浮点数 |
| `q` | 真正写进单个 8-bit 通道的整数码值 | 只能是 0～255，共 256 档 |
| `ĉ` | 从纹理码值解码出来的近似 HDR 颜色 | 通常与原始 `c` 有少量量化误差 |

`saturate(x)` 等价于把 `x` 限制到 0～1。它必须明确存在，否则 `c > R` 时编码值会超过纹理可存范围。

##### 暗部码值分配

以下以 `R = 8` 展示码值分配。该值仅用于计算示例，不代表《暗区突围》GDC 分享公开了这个固定参数。

| 原始线性值 `c` | 直接线性编码的 8-bit 码值 | 平方根编码的 8-bit 码值 | 平方根解码结果 `ĉ` |
|---:|---:|---:|---:|
| `0.001` | `0` | `3` | `0.001107` |
| `0.01` | `0` | `9` | `0.009965` |
| `0.5` | `16` | `64` | `0.503929` |
| `2.0` | `64` | `128` | `2.015717` |
| `8.0` | `255` | `255` | `8.0` |

线性编码时，`c = 0.01` 已经小到会被舍入为码值 0；平方根编码把它提升到码值 9，因此保住了暗部差异。代价是亮部可用档位变少：在 `R = 8` 时，平方根解码后的相邻档位间距从最暗处约 `0.000123`，逐渐增大到最亮处约 `0.0626`；线性编码的档位间距则始终约为 `8 / 255 = 0.0314`。

因此平方根编码不是增加精度，而是**把一部分亮部精度搬给暗部**。

##### 为什么 HDR 范围越大，码阶越容易被看见

平方根编码在颜色 `c` 附近的解码档位间距，可近似写成：

```text
Δc ≈ 2 * sqrt(c * R) / 255
```

`R` 越大，同一个中间亮度附近的档位间距也越大。固定的 256 个码值需要覆盖更宽的数值范围，因此每个档位代表的 HDR 数值区间会增大。

##### 等高线的形成过程

原本连续的天空渐变可能在量化后变成平台：

```text
原始：0.480  0.485  0.490  0.495  0.500
量化：0.472  0.472  0.504  0.504  0.504
```

大片相邻像素拥有完全相同的值，平台边界连起来就像地图等高线。天空和云层具有大面积、低频、平滑渐变，又缺少细碎纹理掩盖误差，所以比石头、树叶更容易暴露这种问题。

高饱和调色还会放大 RGB 通道相对亮度的偏差。三个通道分别量化时，某个通道可能先跨过码阶，使原本轻微的亮度台阶同时变成色相断层。

Tone Mapping 的作用是把 HDR 映射到显示范围。它通常会压缩高光，**不能笼统说成总会放大量化误差**；更准确的说法是：曝光、颜色分级、局部斜率较高的 Tone Mapping 区间与最终显示量化结合后，可能让已有台阶变得更醒目。Tone Mapping 也无法恢复源纹理已经丢失的差异。

如果再使用较激进的 ASTC 块尺寸，块内端点量化会进一步减少有效梯度。单纯提高最终抖动只能把输出码阶变成颗粒，无法恢复源纹理已经丢失的层次。

#### LogRGB 编解码

对每个 RGB 通道独立使用可调对数曲线：

```text
encoded = log2(1 + color * K) / log2(1 + range * K)
decoded = (2^(encoded * log2(1 + range * K)) - 1) / K
```

参数含义：

- `color`：输入的场景线性 HDR RGB，与上一节的 `c` 相同，逐通道处理。
- `range`：最大可表示 HDR 值，与上一节的 `R` 相同。
- `K`：曲线弯曲强度。`K` 越大，越多码值会分给中低亮度，但高亮区的绝对精度也会相应减少。
- `encoded`：写入纹理前的 0～1 编码值。
- `decoded`：运行时恢复出的近似场景线性 HDR 值。

平方根是固定指数的幂函数；这里的 LogRGB 用 `K` 提供可调曲率，更适合在多个曝光档位之间分配有限码值。本文的 LogRGB 指 RGB 三通道各自取对数，不是使用共享亮度通道的 RGBM/RGBD 变体。

一组经过静态天空验证的起点是：

- `range = 8`
- `K = 16`
- PNG 以线性数据导入（关闭 sRGB）
- Mipmap 开启，Wrap Mode 为 Clamp，Filter Mode 为 Trilinear
- Android 使用 ASTC 4×4 高质量压缩

LogRGB 不使用 Alpha 作为整块亮度乘数，因此不会像 RGBM/RGBD 那样让 Alpha 的块压缩误差成倍放大三个颜色通道。代价是双线性/三线性过滤发生在对数域，并且运行时需要 `exp2` 解码；对于静态天空的一次采样，这通常是可接受取舍。

#### 色带必须分两级处理

1. 源纹理量化：使用更合适的 HDR 编码与压缩格式，保证进入 Tone Mapping 前仍有足够层次。
2. 最终显示量化：Tone Mapping 后按屏幕像素加入约 `1/255` 量级的零均值抖动，打散规律码阶。

抖动不是提高精度，而是改变误差形态。源纹理仍有明显等高线时，不应继续无限提高抖动强度。

两级问题可以这样区分：

- 如果色带会跟随天空纹理、改变采样方向后边界仍贴在云上，优先检查源纹理编码和 ASTC 压缩。
- 如果源 HDR 纹理平滑，而色带主要在后处理或最终屏幕上出现，优先检查 Tone Mapping、Color Grading、LUT 精度和最终输出 Dither。

#### 风格化 Tone Mapping 的注意点

卡通感不必等同于离散亮度分档。大面积天空采用硬色阶很容易把量化误差和 Mach band 放大。更稳定的方式是：

- 在线性场景空间连续调整阴影、中间调、高光的颜色倾向。
- 使用连续、保色相的高光肩部把 HDR 压入显示范围。
- 最后加入低幅度输出抖动。

这能产生冷阴影、青蓝中间调、暖高光的卡通配色，同时保留云体连续层次。

#### 运行时成本

上半球每眼的核心成本为：

- 一次 `Texture2D` 采样。
- 半八面体方向编码的少量 ALU。
- 三通道 `exp2` LogRGB 解码。
- 可选 Tone Mapping 和无纹理的屏幕空间抖动。

下半球不采纹理。VR 两眼共享同一纹理资源，但每眼仍会执行自己的那一次像素采样。

#### 《暗区突围》GDC 分享与项目实现的边界

GDC 2022 的《Advanced Weather System for Mobile Game: 'Dark Area'》可以直接支持以下思路：

- 使用半八面体参数化优化上半球天空与 SkyViewLUT。
- 把体积云 Ray Marching 结果缓存到 `512×512` 二维纹理并分帧更新。
- 为旧设备把半浮点缓存进一步压到 RGBA8。
- 将散射结果除以相位函数，并通过预计算曝光和 Gamma 压缩降低存储范围。

这些内容解释了项目方案的技术启发来源，但本文的实现和验证范围更进一步。公开资料只明确到了“Gamma 压缩”，没有确认其具体指数一定是 `1/2`，也没有公开 `sqrt(c / R)` 中 `R` 的固定值。因此：

- `sqrt(c / R)` 应视为解释非线性 HDR 编码的具体平方根模型和本地对比方案，不能写成 GDC 原公式。
- `LogRGB + ASTC 4×4 + Tone Mapping 后 Dither` 是本文的核心项目实践结论，不是《暗区突围》的公开原方案；LogRGB、色带与等高线治理内容必须作为正文保留。
- GDC 的动态体积云缓存方案与本文的静态天空资产方案目标相近，但生命周期不同，不能混写为同一套实现。

### 关键代码

```hlsl
float3 DecodeLogRgb(float3 encoded, float hdrRange, float logCurve)
{
    // hdrRange 必须与离线编码端一致；不一致会整体改变亮度并破坏量化分配。
    float logRange = log2(1.0 + hdrRange * logCurve);
    return (exp2(encoded * logRange) - 1.0) / logCurve;
}

float InterleavedGradientNoise(float2 pixelPosition)
{
    // 使用屏幕像素坐标，让输出抖动打散最终显示码阶而不黏在天空 UV 上。
    return frac(52.9829189 * frac(dot(
        pixelPosition,
        float2(0.06711056, 0.00583715))));
}
```

### 参考链接

- [GDC Vault - Advanced Weather System for Mobile Game: 'Dark Area'](https://www.gdcvault.com/play/1027586/Advanced-Graphics-Summit-Advanced-Weather) - 《暗区突围》移动端动态天气、半八面体天空与体积云缓存方案的原始演讲页面。
- [腾讯魔方引擎专家 GDC 分享整理](https://www.sohu.com/a/539980724_204824) - 演讲内容的中文整理，包含 `512×512` 半八面体缓存、RGBA8、预曝光和 Gamma 压缩描述。
- [A Survey of Efficient Representations for Independent Unit Vectors](https://jcgt.org/published/0003/02/01/) - 八面体单位向量编码综述与误差分析。
- [Khronos Data Format Specification](https://registry.khronos.org/DataFormat/specs/1.4/dataformat.1.4.html) - 线性颜色、非线性传递函数与量化前后解释的规范背景。
- [Arm Adaptive Scalable Texture Compression User Guide](https://developer.arm.com/-/media/Arm%20Developer%20Community/PDF/ASTC_User_Guide_102162_0002_01.pdf) - ASTC 块、颜色端点、插值权重和量化机制。
- [Unreal Engine: Color Grading and the Filmic Tonemapper](https://dev.epicgames.com/documentation/en-us/unreal-engine/color-grading-and-the-filmic-tonemapper-in-unreal-engine) - 场景线性颜色分级与 Filmic Tone Mapping 的职责划分。
- [High Dynamic Range Color Grading and Display in Frostbite](https://www.ea.com/frostbite/news/high-dynamic-range-color-grading-and-display-in-frostbite) - HDR 调色与显示映射背景。

### 相关记录

- [色带（Color Banding）与抖动（Dithering）知识](./color-banding-dither.md) - 输出量化和抖动的通用原理。
- [ACES Tone Mapping](./aces-tone-mapping.md) - 可选的连续 HDR 到 LDR 映射。
- [URP 天空盒 Shader 机制与常见问题](./urp-skybox-notes.md) - Unity 天空盒路径注意事项。

### 验证记录

- [2026-07-27] 先后对比无 Tone Mapping、ACES、连续风格化调色、平方根 RGB 与 LogRGB；从迎光、侧光、背光和天顶检查。LogRGB + ASTC 4×4 导入设置 + Tone Mapping 后低幅度抖动消除了太阳光晕和天顶的大块等高线，运行时 Shader 静态审计保持一次 `tex2D`。移动设备上的实际 ASTC 解码画质仍需随目标机型回归。
- [2026-07-27] 完整性与来源性修正：补全平方根编码的编码、8-bit 量化与解码公式，解释 `c`、`R`、`e`、`q`、`ĉ`、`K` 等参数，并加入 `R = 8` 数值示例。外部复核确认《暗区突围》GDC 2022 分享公开支持半八面体缓存、RGBA8、预曝光与 Gamma 压缩，但未确认 `sqrt(c / R)` 是其原始公式；已将平方根和 LogRGB 明确标为本地解释/实践方案。Tone Mapping 表述收紧为“可能经组合处理使台阶更可见”，不再笼统称其总会放大量化误差。
- [2026-07-27] 来源层级修正：明确本文以项目实现与 Unity 编辑器实测为主体，《暗区突围》GDC 仅作为半八面体缓存与有限位深压缩的方案启发。保留并强化 LogRGB、ASTC、源纹理色带、最终输出等高线和 Dither 的项目实践结论，避免将文章误读为 GDC 内容复述。

---

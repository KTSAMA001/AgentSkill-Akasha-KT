# 半八面体单图 HDR 天空的编码、采样与色带治理

**标签**：#graphics #shader #hdr #performance #experience
**来源**：项目实践总结；JCGT 单位向量编码论文；Unity 纹理压缩与色带工程实践
**收录日期**：2026-07-27
**来源日期**：2014 / 2026-07-27（实践验证）
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐（公开编码理论 + Unity 编辑器内实现与多视角验证）
**适用版本**：Unity Shader Model 3.0+；移动端 ASTC 平台

### 概要

只需要上半球天空时，可把方向映射到一张铺满正方形的半八面体二维纹理。运行时使用一次普通 `Texture2D` 采样；HDR 数据以逐通道 LogRGB 编码到 8-bit PNG，优先把码值分给天空常见的中低亮度，再在 Tone Mapping 后加入低幅度屏幕空间抖动，分别治理源纹理量化和最终输出量化造成的色带。

### 内容

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
    n.y = max(n.y, 0.0);
    float invL1 = rcp(max(abs(n.x) + n.y + abs(n.z), 1e-5));
    float2 diamond = n.xz * invL1;
    float2 square = float2(
        diamond.x + diamond.y,
        diamond.x - diamond.y);
    return square * 0.5 + 0.5;
}
```

运行时下半球可以直接输出地面/雾色，不需要采天空纹理。

#### 为什么平方根 RGB 仍可能出现大块色带

把 HDR 线性颜色 `c` 编成 `sqrt(c / R)`，比直接线性量化更照顾暗部，但当 HDR 范围较大、天空中间调很平滑、随后又进行高饱和调色与 Tone Mapping 时，8-bit 码阶仍可能被放大成等高线。

如果再使用较激进的 ASTC 块尺寸，块内端点量化会进一步减少有效梯度。单纯提高最终抖动只能把输出码阶变成颗粒，无法恢复源纹理已经丢失的层次。

#### LogRGB 编解码

对每个 RGB 通道独立使用可调对数曲线：

```text
encoded = log2(1 + color * K) / log2(1 + range * K)
decoded = (2^(encoded * log2(1 + range * K)) - 1) / K
```

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

### 关键代码

```hlsl
float3 DecodeLogRgb(float3 encoded, float hdrRange, float logCurve)
{
    float logRange = log2(1.0 + hdrRange * logCurve);
    return (exp2(encoded * logRange) - 1.0) / logCurve;
}

float InterleavedGradientNoise(float2 pixelPosition)
{
    return frac(52.9829189 * frac(dot(
        pixelPosition,
        float2(0.06711056, 0.00583715))));
}
```

### 参考链接

- [A Survey of Efficient Representations for Independent Unit Vectors](https://jcgt.org/published/0003/02/01/) - 八面体单位向量编码综述与误差分析。
- [Unreal Engine: Color Grading and the Filmic Tonemapper](https://dev.epicgames.com/documentation/en-us/unreal-engine/color-grading-and-the-filmic-tonemapper-in-unreal-engine) - 场景线性颜色分级与 Filmic Tone Mapping 的职责划分。
- [High Dynamic Range Color Grading and Display in Frostbite](https://www.ea.com/frostbite/news/high-dynamic-range-color-grading-and-display-in-frostbite) - HDR 调色与显示映射背景。

### 相关记录

- [色带（Color Banding）与抖动（Dithering）知识](./color-banding-dither.md) - 输出量化和抖动的通用原理。
- [ACES Tone Mapping](./aces-tone-mapping.md) - 可选的连续 HDR 到 LDR 映射。
- [URP 天空盒 Shader 机制与常见问题](./urp-skybox-notes.md) - Unity 天空盒路径注意事项。

### 验证记录

- [2026-07-27] 先后对比无 Tone Mapping、ACES、连续风格化调色、平方根 RGB 与 LogRGB；从迎光、侧光、背光和天顶检查。LogRGB + ASTC 4×4 导入设置 + Tone Mapping 后低幅度抖动消除了太阳光晕和天顶的大块等高线，运行时 Shader 静态审计保持一次 `tex2D`。移动设备上的实际 ASTC 解码画质仍需随目标机型回归。

---

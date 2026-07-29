# 半八面体单图 HDR 天空的编码、采样与色带治理

**标签**：#graphics #shader #hdr #performance #experience
**来源**：项目实现与 Unity 编辑器实测（主体）；GDC 2022《Advanced Weather System for Mobile Game: 'Dark Area'》（方案启发与外部参照）；JCGT 单位向量编码论文；Khronos 色彩传递函数规范；Arm ASTC 官方指南
**收录日期**：2026-07-27
**来源日期**：2014 / 2022 / 2026-07-27（实践验证）
**更新日期**：2026-07-29
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐（公开编码理论 + Unity 编辑器内实现与多视角验证）
**适用版本**：Unity Shader Model 3.0+；移动端 ASTC 平台

### 概要

只需要上半球天空时，可把方向映射到一张铺满正方形的半八面体二维纹理。基础 HDR 天空以逐通道 LogRGB 编码到 RGBA8 的 RGB，Alpha 可保存一个同映射、独立可控的标量瞬态响应；需要覆盖更宽雷暴区域时，再用第二张 LogRGBA 保存四个可线性组合的固定闪电传输单元。两张纹理合计提供五个位置明显不同的单元，平静帧只采基础纹理，非零闪电帧增加一次 Basis 采样。Tone Mapping 后加入低幅度屏幕空间抖动，分别治理源纹理量化和最终输出量化造成的色带。

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
    ↓ c' = clamp(c, 0, range)
截断到可表示范围的 c'
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

编码只改变有限码值的分配方式，不会把 8-bit 变成更高精度。一旦两个原始颜色被量化成同一个整数码值，后续步骤无法恢复它们原来的差异；超过 range 的高光也会在编码前永久截断。

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

##### 烘焙端的逆映射

运行时需要“方向 → UV”，烘焙端则需要“每个 UV → 天空方向”。两端必须互为逆变换：

~~~hlsl
float3 DecodeHemiOctahedralDirection(float2 uv)
{
    float2 square = uv * 2.0 - 1.0;
    float2 diamond = 0.5 * float2(
        square.x + square.y,
        square.x - square.y);
    float y = max(0.0, 1.0 - abs(diamond.x) - abs(diamond.y));
    return normalize(float3(diamond.x, y, diamond.y));
}
~~~

逆映射先把正方形旋转回 L1 菱形，再用 1 - |x| - |z| 恢复向上分量。最后 normalize 是必要的，因为 L1 表面不是单位球面。

##### 五个基准方向

| 天空方向 | UV | 几何含义 |
|---|---|---|
| (0, 1, 0) | (0.5, 0.5) | 天顶在正方形中心 |
| (-1, 0, 0) | (0, 0) | 一个地平线基准方向 |
| (0, 0, 1) | (1, 0) | 一个地平线基准方向 |
| (0, 0, -1) | (0, 1) | 一个地平线基准方向 |
| (1, 0, 0) | (1, 1) | 一个地平线基准方向 |

正方形四条边全部落在地平线，四个角对应四个水平主方向。最小单元测试应验证这五个点以及随机方向的 encode→decode 夹角误差。

##### 分布畸变与边界

该映射连续，但纹素在球面上的立体角不均匀。中心、边缘和角落代表的方向面积不同，所以：

- 同一像素宽度在不同方向不等于同一角度。
- 不能直接在正方形 UV 上用普通圆形距离定义等角闪电区域。
- 四边使用 Clamp 可以把越界过滤限制在地平线，不应设置 Repeat。
- 靠近地平线的 Mip 和过滤必须从四个象限检查，不能只看天顶。

运行时下半球可以直接输出地面/雾色，不需要采天空纹理。

#### HDR 存储方案为什么需要对比

| 方案 | 存储 | 主要优点 | 主要问题 |
|---|---|---|---|
| FP16 RGB/RGBA | 半浮点纹理 | 精度和过滤最直接 | 移动端内存、带宽更高 |
| 线性 RGB8 | 每通道线性量化 | 解码几乎免费 | 暗部和中间调精度不足 |
| 平方根 RGB8 | 每通道平方根 | 暗部优于线性 | 曲线固定，亮部档位下降 |
| RGBM/RGBD | RGB + 共享倍率 | 常见 HDR 压缩方式 | Alpha 误差会共同影响 RGB，过滤和块压缩敏感 |
| 逐通道 LogRGB | RGB 各自 log1p | 曲率可调，不依赖 Alpha 倍率 | exp2 ALU，过滤发生在对数域 |

当前基础路径目标是“普通 2D 纹理、平静帧一次采样、移动 ASTC、静态天空平滑渐变”，因此最终选择逐通道 LogRGB。闪电路径使用第二张同 UV 的 LogRGBA，但只在瞬态贡献非零时启用。它不是所有 HDR 纹理的普遍最优解。

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
c = clamp(color, 0, range)
encoded = log2(1 + c * K) / log2(1 + range * K)
q = round(255 * encoded)
decoded = (2^((q / 255) * log2(1 + range * K)) - 1) / K
```

参数含义：

- `color`：输入的场景线性 HDR RGB，与上一节的 `c` 相同，逐通道处理。
- `range`：最大可表示 HDR 值，与上一节的 `R` 相同。
- `K`：曲线弯曲强度，量纲是颜色单位的倒数，使 color × K 为无量纲量。`K` 越大，越多码值会分给中低亮度，但高亮区的绝对精度也会相应减少。
- `encoded`：写入纹理前的 0～1 编码值。
- `decoded`：运行时恢复出的近似场景线性 HDR 值。

平方根是固定指数的幂函数；这里的 LogRGB 用 `K` 提供可调曲率，更适合在多个曝光档位之间分配有限码值。对数底数本身不影响归一化比值；实现选择 log2/exp2 是为了与 GPU 指令对应。本文的 LogRGB 指 RGB 三通道各自取对数，不是使用共享亮度通道的 RGBM/RGBD 变体。

一组经过静态天空验证的起点是：

- `range = 8`
- `K = 16`
- PNG 以线性数据导入（关闭 sRGB）
- Mipmap 开启，Wrap Mode 为 Clamp，Filter Mode 为 Trilinear
- Android 使用 ASTC 4×4 高质量压缩

##### range = 8、K = 16 的量化示例

| 原始值 | 8-bit 码值 q | 解码值 | 绝对误差 | 下一码阶间距 |
|---:|---:|---:|---:|---:|
| 0.001 | 1 | 0.001203 | +0.000203 | 0.001226 |
| 0.01 | 8 | 0.010294 | +0.000294 | 0.001401 |
| 0.1 | 50 | 0.099577 | -0.000423 | 0.003118 |
| 0.5 | 115 | 0.496890 | -0.003110 | 0.010763 |
| 1.0 | 149 | 1.006866 | +0.006866 | 0.020576 |
| 2.0 | 183 | 1.981771 | -0.018229 | 0.039334 |
| 4.0 | 219 | 3.997295 | -0.002705 | 0.078114 |
| 8.0 | 255 | 8.000000 | 0 | — |

表格说明 LogRGB 仍然只有 256 档，只是让低亮度档位更密、亮部档位更疏。码值和误差取决于具体的四舍五入规则，表中用于说明量级，不应作为跨工具逐 bit 一致性的保证。

##### 如何选择 range 和 K

1. 先保留 EXR 母版，统计每通道或亮度的最大值、99.9% 分位和太阳核心峰值。
2. 决定哪些极端高光允许截断，再把 range 设在所需峰值之上；range 不是越大越好。
3. 固定 range 后扫描多组 K，用最终 Tone Mapping 后的加权误差和多视角截图比较。
4. 天空中间调权重应高于极少数太阳核心像素，否则会为了不重要的峰值牺牲整片天空精度。
5. 编码端和运行时材质必须保存同一组 range/K；任一侧不一致都会整体改变亮度。

当前 range = 8、K = 16 是一个经过本场景验证的起点，不是跨项目常量。

RGBM/RGBD 常见解码形态包含 rgb × multiplier × range，Alpha 或共享倍率的误差会连带改变三个颜色通道，并随 range 缩放。LogRGB 不使用这种共享倍率，误差主要局限在各通道自身；但它并不会消除 ASTC 的端点、权重和块量化误差。

##### 对数域过滤和 Mipmap 偏差

当前纹理由 Unity 在编码后的 LogRGB 上生成 Mip，并在对数域执行双线性/三线性过滤。由于 log1p 是凹函数：

~~~text
decode(average(encode(c))) <= average(c)
~~~

高反差区域的过滤结果会比“先在线性 HDR 中平均、再编码”略暗，太阳边缘和高亮云边最容易观察到这种偏差。

可选取舍：

- 当前实现接受该偏差，以换取普通 PNG、自动 Mip 和一次采样链路。
- 如果远处 Mip 的亮度偏差不可接受，可离线在线性 HDR 空间生成每级 Mip，再逐级 LogRGB 编码并写入支持自定义 Mip 的纹理资产。
- 如果天空始终以固定、接近零的 LOD 采样，也可评估关闭 Mipmap；但要重新检查 VR 旋转时的闪烁和缓存稳定性。

运行时还需要三通道 exp2 解码。一次采样并不等于零成本，只是相较额外纹理读取更偏向 ALU。

#### Unity 资产实现过程

##### CPU 编码

1. GPU 瓦片先汇总成线性的 RGBAHalf HDR 母图。
2. 可选用 EXR 保存未编码母版。
3. CPU 对 RGB 每个通道执行 clamp + LogRGB。
4. 写入 RGBA32 Texture2D，再 EncodeToPNG。
5. RGB 保存基础 LogRGB；Alpha 独立保存第一条闪电路径的 LogR 标量响应，作为无第二张 Basis 纹理时的一采样兼容路径。

~~~csharp
float clamped = Mathf.Clamp(value, 0.0f, hdrRange);
float encoded = Mathf.Log(
    1.0f + clamped * logCurve,
    2.0f) / Mathf.Log(
    1.0f + hdrRange * logCurve,
    2.0f);
~~~

##### 导入设置

| 设置 | 当前值 | 原因 |
|---|---|---|
| Texture Type | Default | 作为普通二维天空数据 |
| sRGB Texture | 关闭 | 编码值不是显示 sRGB 颜色 |
| Alpha Source | Input Texture Alpha | Alpha 保存独立 LogR 标量响应，不是透明度或 RGBM 倍率 |
| Alpha Is Transparency | 关闭 | 数据通道不得做透明边缘扩张或预乘解释 |
| Mipmap | 开启 | 降低远处/旋转采样闪烁 |
| Wrap | Clamp | 四边都是地平线，不允许跨边 Repeat |
| Filter | Trilinear | 在 Mip 间平滑过渡 |
| Read/Write | 关闭 | Player 不需要 CPU 读取 |
| Android | ASTC 4×4，Quality 100 | 优先保留平滑渐变质量 |

sRGB 必须关闭。若错误开启，硬件采样会先做 sRGB→Linear 转换，运行时再按 LogRGB 解码，相当于叠加了不匹配的非线性变换。

##### ASTC 4×4 内存量级

ASTC 每块固定 128 bit。4×4 即 8 bit/像素，不论源 PNG 是 RGB 还是 RGBA：

| 分辨率 | 基础级 | 含完整 Mip 约值 |
|---:|---:|---:|
| 512² | 256 KiB | 341 KiB |
| 1024² | 1 MiB | 1.33 MiB |
| 2048² | 4 MiB | 5.33 MiB |

这些是 GPU 压缩纹理近似值，不含 Unity 资产数据库、PNG 文件和平台打包开销。ASTC 6×6 体积更小，但当前平滑天空实测更容易暴露块和梯度问题，因此改用 4×4。

#### 基础 LogRGBA 与闪电 Basis LogRGBA 的双纹理契约

当前发布链路把“基础天空”和“事件型辅助数据”分开。这里的 Alpha/RGBA 都是线性可加的标量传输响应，不是透明度、RGBM 倍率、规则区域 Mask 或四张完整天空：

| 纹理 | 通道 | 解码后语义 | 生命周期 |
|---|---|---|---|
| 基础 LogRGBA | RGB | 无闪电静态天空 HDR 出射辐亮度 | 所有上半球像素 |
| 基础 LogRGBA | A | 一个独立固定闪电单元的标量体积传输响应 | 闪电峰值和短尾迹；也支持无第二张纹理的一采样兼容模式 |
| 闪电 Basis LogRGBA | RGBA | 另外四个固定闪电单元的标量体积传输响应 | 仅非零闪电贡献期间 |

五个单元共享同一重建公式：

~~~text
L(direction, t)
  = Lstatic(direction)
  + LightningColor
    * (BaseA(direction) * BasePulse(t)
       + dot(BasisRGBA(direction), PulseRGBA(t)))
~~~

RGBA 是一次纹理读取得到四个数，不是四次采样；但独立的第二张纹理仍使闪电帧从一次采样变为两次。每个单元保存一个完整且固定的空间造型。动漫式多样性优先来自 one-hot 选择不同单元、远隔单元接力或两个远隔单元同时点亮，而不是在同一小区域内混入难以察觉的相邻微变形。

旧资产需要版本化解释：早期 schema 可能让基础 Alpha 与 Basis R 保存同一位置，运行时只能按四个独立单元计数；新 schema 才允许基础 Alpha 与 RGBA 分别保存五个不同位置。迁移代码不能仅看“有 Alpha”就假设它一定是第五单元，必须比较 metadata/schema 与中心方向。

离线求解器还可以输出一张散射阶诊断纹理，其通道约定为：

| 诊断通道 | 语义 |
|---|---|
| R | Direct，观察方向直接看到有限半径发光路径的贡献 |
| G | Single，一次真实体积散射 |
| B | Multiple，两次及以上体积散射 |
| A | Combined，Direct + Single + Multiple |

这张 `Orders` 诊断纹理不是运行时四位置 Basis；把它误绑到 Basis 槽位会把四种散射阶当成四处闪电，时序与空间语义都会错误。正式打包时应先为每个固定单元选定同一传输量，再分别写入 Base A 与 Basis RGBA。

四通道适合保存能被同一滤波、Mip 和线性组合规则处理的数据，不应随意混装深度、类别 ID、法线和极值 Mask。闪电传输响应本身已经包含云体和光源共同决定的空间支撑，默认不再乘规则球形 RegionMask；额外 Mask 会在高亮时暴露原型边缘，并把本应沿相连云体传播的能量硬切断。

若未来需要层感知卡通调色，可试验低分辨率、关键字可选的 CloudAux RGBA，四通道统一保存不同云型的视线积分软光学厚度。它只能作为连续 LUT/调色权重，不能替代闪电传输基；在 A/B 证明画质收益且真机验证三次采样成本前，不应升级为常驻契约。

#### 色带必须分两级处理

1. 源纹理量化：使用更合适的 HDR 编码与压缩格式，保证进入 Tone Mapping 前仍有足够层次。
2. 最终显示量化：Tone Mapping 后按屏幕像素加入以 `1/255` 为实现尺度的零均值抖动，打散规律码阶。

抖动不是提高精度，而是改变误差形态。源纹理仍有明显等高线时，不应继续无限提高抖动强度。

当前 Shader 在项目线性颜色空间中直接加入该扰动，然后再由渲染目标执行显示传递。因此“1/255”不严格等于一个最终 sRGB code；暗部和亮部经过 OETF 后的实际码值变化不同。若需要严格按显示码值抖动，应在 OETF 之后处理，或按传递函数导数缩放幅度。

两级问题可以这样区分：

- 如果色带会跟随天空纹理、改变采样方向后边界仍贴在云上，优先检查源纹理编码和 ASTC 压缩。
- 如果源 HDR 纹理平滑，而色带主要在后处理或最终屏幕上出现，优先检查 Tone Mapping、Color Grading、LUT 精度和最终输出 Dither。

#### 风格化 Tone Mapping 的注意点

卡通感不必等同于离散亮度分档。大面积天空采用硬色阶很容易把量化误差和 Mach band 放大。更稳定的方式是：

- 在线性场景空间连续调整阴影、中间调、高光的颜色倾向。
- 使用连续、保色相的高光肩部把 HDR 压入显示范围。
- 最后加入低幅度输出抖动。

这能产生冷阴影、青蓝中间调、暖高光的卡通配色，同时保留云体连续层次。

当前连续风格化映射的实现顺序是：

1. 从场景线性亮度构造平滑的阴影、中间调和高光权重。
2. 连续混合三组 Tint，而不是把亮度量化成固定档位。
3. 调整饱和度。
4. 用指数肩部 `mappedLuma = 1 - exp(-luma * compression)` 压缩 HDR。
5. 按亮度比率缩放 RGB，尽量保持色相。
6. 在最终输出前加入屏幕空间 Dither。

它仍是项目艺术映射，不是 ACES 标准变换。None/ACES/StylizedColor 三个模式应保留用于诊断：如果色带在 None 中已存在，根因更可能在源纹理；只在某个映射模式中显著，则继续检查该映射的局部斜率和颜色调整。

#### 运行时成本

平静上半球每眼的核心成本为：

- 一次 `Texture2D` 采样。
- 半八面体方向编码的少量 ALU。
- 三通道 `exp2` LogRGB 解码。
- 可选 Tone Mapping 和无纹理的屏幕空间抖动。

下半球不采纹理。VR 两眼共享同一纹理资源，但每眼仍会执行自己的那一次像素采样。

运行时上半球实际顺序：

~~~text
天空方向
  → 绕 Y 轴旋转
  → 半八面体方向编码
  → tex2D 一次
  → LogRGB 解码
  → 地平线窄雾带混合
  → Exposure
  → None / ACES / StylizedColor
  → 屏幕空间 Dither
  → 输出
~~~

非零闪电峰值和短尾迹会启用第二张 RGBA Basis 采样；黑场、冷却和普通天气恢复基础一次采样。运行时动态开启的 Basis 本地关键字必须确保 Player 构建保留开/关两个变体；参考实现使用 `multi_compile_local`，避免正式材质默认关闭关键字时把 ON 变体裁掉。

Single-Pass Instanced/Multiview 减少的是提交和双眼组织成本，不会让两眼共用同一次像素着色。左右眼共享纹理资产，但每眼覆盖的像素仍各自采样。

#### 问题诊断决策表

| 现象 | 最可能阶段 | 验证方式 |
|---|---|---|
| 等高线跟随云纹理方向 | HDR 编码或压缩 | 查看 EXR/未压缩图，切换平台压缩 |
| 只有 Android 明显 | ASTC 块与码率 | 对比 ASTC 4×4、6×6、无压缩 |
| 只有某 Tone Map 明显 | 映射局部斜率/调色 | 切换 None、ACES、StylizedColor |
| 太阳边缘 Mip 后变暗 | 对数域过滤 | 强制 LOD 0 或关闭 Mip A/B |
| 整体亮度完全不对 | range/K 不一致或 sRGB 错误 | 对比材质参数和 Importer |
| 地平线四边有缝 | Clamp、方向映射、雾带 | 检查四象限和五个基准方向 |
| 增大 Dither 后只剩噪点 | 源纹理已丢精度 | 停止加 Dither，修编码/压缩 |

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

| 维度 | 《暗区突围》公开方案 | 当前项目实现 |
|---|---|---|
| 生命周期 | 天气缓慢变化，缓存分帧更新并交换 RT | Editor 一次性静态烘焙 |
| 天空/云布局 | 半八面体 SkyViewLUT 与 512×512 云缓存 | 单张上半球半八面体资产 |
| 原始缓存 | 主流设备半浮点；旧设备尝试 RGBA8 | RGBAHalf 母图，可选 EXR |
| 有限位深压缩 | 除相位函数、预曝光、Gamma 压缩 | clamp + 逐通道 LogRGB |
| 运行时更新 | 棋盘、切片、重投影、双 RT | 不更新，只采样静态纹理 |
| 色带治理 | 公开整理未给出本文完整链路 | LogRGB、ASTC 4×4、连续 Tone Map、Dither |

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

- [静态体积云天空的高质量离线烘焙](./static-volumetric-cloud-sky-baking.md) - LogRGB 编码前的 HDR 体积云母图生成过程。
- [VR 静态云天空与动态闪电的分离合成](./vr-static-sky-lightning-compositing.md) - 基础天空、闪电增量和双眼共享纹理的后续设计。
- [色带（Color Banding）与抖动（Dithering）知识](./color-banding-dither.md) - 输出量化和抖动的通用原理。
- [ACES Tone Mapping](./aces-tone-mapping.md) - 可选的连续 HDR 到 LDR 映射。
- [URP 天空盒 Shader 机制与常见问题](./urp-skybox-notes.md) - Unity 天空盒路径注意事项。

### 验证记录

- [2026-07-27] 先后对比无 Tone Mapping、ACES、连续风格化调色、平方根 RGB 与 LogRGB；从迎光、侧光、背光和天顶检查。LogRGB + ASTC 4×4 导入设置 + Tone Mapping 后低幅度抖动消除了太阳光晕和天顶的大块等高线，运行时 Shader 静态审计保持一次 `tex2D`。移动设备上的实际 ASTC 解码画质仍需随目标机型回归。
- [2026-07-27] 完整性与来源性修正：补全平方根编码的编码、8-bit 量化与解码公式，解释 `c`、`R`、`e`、`q`、`ĉ`、`K` 等参数，并加入 `R = 8` 数值示例。外部复核确认《暗区突围》GDC 2022 分享公开支持半八面体缓存、RGBA8、预曝光与 Gamma 压缩，但未确认 `sqrt(c / R)` 是其原始公式；已将平方根和 LogRGB 明确标为本地解释/实践方案。Tone Mapping 表述收紧为“可能经组合处理使台阶更可见”，不再笼统称其总会放大量化误差。
- [2026-07-27] 来源层级修正：明确本文以项目实现与 Unity 编辑器实测为主体，《暗区突围》GDC 仅作为半八面体缓存与有限位深压缩的方案启发。保留并强化 LogRGB、ASTC、源纹理色带、最终输出等高线和 Dither 的项目实践结论，避免将文章误读为 GDC 内容复述。
- [2026-07-28] 正确性复核与实现扩写：确认新增的 GDC 来源边界、平方根量化数值和 Tone Mapping 收窄表述正确；修正 LogRGB 公式，显式加入 clamp 与 8-bit 量化。补充半八面体逆映射和五个基准方向、LogRGB 误差表、range/K 选择方法、对数域过滤与 Mip 偏差、Unity CPU 编码和导入链路、ASTC 内存量级、线性空间 Dither 限制、运行时顺序和诊断决策表。
- [2026-07-28] 双纹理契约更新：基础发布纹理由 RGB24 调整为 LogRGBA，Alpha 保存第一条闪电路径的 LogR 兼容响应；新增第二张四通道闪电传输基。验证 1024×1024 基础与 Basis 均为 Linear、Mip、Clamp、不可读、Android ASTC 4×4；平静/黑场一次采样，非零峰值/短尾迹两次采样。补充动态关键字 Player 变体保留和可选 CloudAux RGBA 的适用边界。Quest 真机 ASTC、双眼和 GPU 抓帧仍未覆盖。
- [2026-07-29] 正确性与数据契约修正：将 Base A + Basis RGBA 明确为五个可独立布局的固定闪电单元，并保留旧 schema 中 Base A/Basis R 重复时只能按四单元计数的兼容边界。新增 `Orders` 诊断纹理的 Direct/Single/Multiple/Combined 通道语义，禁止把散射阶纹理误当四位置 Basis。根据夜间多视角实践撤销默认 RegionMask 建议：传输响应本身决定空间支撑，规则 Mask 会产生原型软边并切断相连云体受光。Quest 真机双眼、构建变体与 GPU 采样数仍待验证。

---

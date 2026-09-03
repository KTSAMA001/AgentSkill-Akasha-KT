# Unity HLSL 单次噪声采样的 UV 滚动与程序化 Warp 流动

**标签**：#unity #shader #graphics #hlsl #texture #math #knowledge
**来源**：实践总结（Unity 2022.3 LTS / URP 14.0.12 自定义 HLSL 流动效果与数学推导）
**收录日期**：2026-09-03
**状态**：📘 有效
**可信度**：⭐⭐⭐⭐
**适用版本**：Unity 2022.3 LTS；Universal Render Pipeline 14.0.12

### 概要

在不使用多相 FlowMap 采样的前提下，可以让一张灰度纹理先按 UV 持续滚动，再通过沿指定方向传播的正弦位移场进行拉伸和压缩，最后只采样一次噪声纹理并经过一次 Ramp 映射，形成具有方向感的流动自发光。本文解释该方法的完整数据流、每个向量与公式的数学含义、时间和速度单位、交叉相位产生不规则感的机制，以及 UV 折叠、纹理过滤和长时间运行的边界。

### 内容

#### 1. 问题、目标与方法边界

单纯使用 `uv + time * speed` 平移纹理，轮廓不会发生形变，视觉上容易像一张贴纸匀速滑过。标准多相 FlowMap 可以制造更明显的流体感，但通常需要额外的方向纹理、重复采样和相位混合。当目标平台更在意纹理采样次数，且所需效果是沿主方向拉伸、压缩的能量流而非物理可信的流体时，可以改用“基础滚动 + 程序化 Warp”。

这套方法的端到端路径是：

```text
第二套 UV
  -> Tiling/Offset
  -> 有界的基础滚动
  -> 程序化方向 Warp
  -> 一次灰度噪声采样
  -> 一次 Ramp 颜色映射
  -> 写入指定 Mask 的自发光区域
```

这里的“单次采样”特指每个片元只读取一次被流动的灰度噪声纹理。Ramp 仍然是另一次纹理读取，因此 Flow 部分总计包含一次 Noise 采样和一次 Ramp 采样。它不是 FlowMap，也不会模拟质量守恒、旋涡或真实速度场。

#### 2. 符号与参数单位

先把第二套 UV 经过纹理的 Tiling/Offset：

```hlsl
float2 noiseUV = uv2 * _NoiseMap_ST.xy + _NoiseMap_ST.zw;
```

下文使用这些符号：

| 符号 | 对应参数 | 数学含义与单位 |
|---|---|---|
| $\mathbf{u}$ | `noiseUV` | 经过 Tiling/Offset 的二维纹理坐标 |
| $t$ | `_TimeParameters.x` | 当前实现使用的经过时间，单位为秒 |
| $\mathbf{v}_s$ | `scrollVector` | 基础滚动向量，方向是滚动方向，长度是 UV/秒 |
| $\mathbf{v}_w$ | `warpVector` | Warp 控制向量；方向是 Warp 轴，长度是相位周期/秒 |
| $\mathbf{d}$ | `warpDirection` | `warpVector` 的单位方向 |
| $F$ | `warpFrequency` | 主波空间频率，单位为周期/UV |
| $A$ | `warpStrength` | 主波最大位移，单位为 UV |
| $I$ | `warpIrregularity` | 不规则调制比例，无量纲，通常取 0 到 1 |
| $D$ | `warpIrregularDensity` | 交叉相位的空间密度，近似为周期/UV |

一个重要的语义边界是：`scrollVector` 的长度直接表示纹理坐标每秒移动多少；`warpVector` 的长度表示 Warp 相位每秒推进多少个周期，并不直接等于 Warp 波形每秒在 UV 空间移动多少。

#### 3. 基础滚动：时间乘速度就是持续累加

```hlsl
float2 scrollOffset = frac(t * scrollVector);
float2 scrolledUV = noiseUV + scrollOffset;
```

时间 $t$ 本身持续增长，所以

$$
\mathbf{o}_s(t)=t\mathbf{v}_s
$$

就是从零开始对恒定速度进行累加后的位移。这与口语中的“`uv + time * direction`，时间自行累加，所以纹理持续运动”完全一致；乘法负责把“秒”换算成“UV 位移”，并不是用乘法替代时间累加。

HLSL 的 `frac(x)` 定义为 $x-\lfloor x\rfloor$，逐分量把结果限制在 $[0,1)$。因此代码实际使用：

$$
\mathbf{o}_s(t)=\operatorname{frac}(t\mathbf{v}_s)
$$

当纹理 Wrap Mode 为 Repeat 时，相差整数的 UV 会采到同一位置，所以 `frac(t * scrollVector)` 与不取 `frac` 的持续滚动在采样意义上等价。它把传给采样器的偏移限制在一个周期内，避免 UV 偏移本身无限增大。负方向同样成立，因为负数经过 `frac` 后会映射到等价的 Repeat 坐标。

这一等价关系依赖 Repeat 和可接受的纹理接缝；Clamp 模式不成立。`frac` 也不能消除无限运行时全局时间变量自身的浮点精度下降，因为乘法发生在取小数之前。需要支持极长运行时间时，应由脚本向 Shader 传入周期性回绕的时间，而不是期待片元着色器保存跨帧累加状态。

#### 4. 从 Warp 向量拆出方向与相位速度

```hlsl
float warpLengthSq = dot(warpVector, warpVector);
float2 warpDirection = warpVector * rsqrt(max(warpLengthSq, 0.000001));
float warpSpeed = sqrt(warpLengthSq);
```

向量长度平方是：

$$
\lVert\mathbf{v}_w\rVert^2=\mathbf{v}_w\cdot\mathbf{v}_w=x^2+y^2
$$

`rsqrt(x)` 返回 $1/\sqrt{x}$，所以：

$$
\mathbf{d}=\mathbf{v}_w\frac{1}{\sqrt{\mathbf{v}_w\cdot\mathbf{v}_w}}
=\frac{\mathbf{v}_w}{\lVert\mathbf{v}_w\rVert}
$$

这与 `normalize(warpVector)` 的数学结果相同。显式写成 `dot + rsqrt` 不是算法上的必需，而是为了明确加入接近零向量的下限保护，并复用同一个长度平方计算 `warpSpeed`。具体 GPU 编译器也可能把 `normalize` 优化为相近指令，因此不能只凭源码写法断言哪种一定更快。

归一化的目的，是让 Warp 方向只负责方向，让向量长度单独负责相位推进速度。如果直接把原向量用于投影，增大向量长度会同时改变空间频率、时间速度，甚至后续位移幅度，参数会发生难以预测的耦合。

当 `warpVector` 为零或极小时，`max` 可避免除零；此时方向和速度平滑趋近于零，最终 Warp 位移也因乘上近零方向而消失。

#### 5. `dot`：把二维 UV 投影为沿 Warp 轴的一维坐标

```hlsl
float warpCoordinate = dot(noiseUV, warpDirection);
float2 crossDirection = float2(-warpDirection.y, warpDirection.x);
float crossCoordinate = dot(noiseUV, crossDirection);
```

设 $\mathbf{d}=(d_x,d_y)$，那么：

$$
s=\mathbf{u}\cdot\mathbf{d}=u_xd_x+u_yd_y
$$

$s$ 表示二维 UV 点沿 Warp 方向的有符号一维位置。所有 $s$ 相同的 UV 点会得到相同主相位，因此形成与 $\mathbf{d}$ 垂直的等相位条带。通过这个投影，一条一维正弦函数就能作用在二维纹理上。

垂直方向

$$
\mathbf{p}=(-d_y,d_x)
$$

是把单位方向旋转 90 度得到的，因此 $\mathbf{d}\cdot\mathbf{p}=0$。第二次投影

$$
q=\mathbf{u}\cdot\mathbf{p}
$$

给出横跨主 Warp 轴的位置，后续用它让不同横向位置获得不同调制，避免所有像素只形成完全规则的平行条带。

#### 6. 主相位：频率、时间与正负号如何决定传播

代码先用“周期”表示相位，进入 `sin` 前再乘 $2\pi$：

```hlsl
float basePhaseCycles = warpCoordinate * warpFrequency - t * warpSpeed;
float baseWave = sin(basePhaseCycles * 6.2831853);
```

对应公式：

$$
\phi_0(s,t)=2\pi(Fs-wt)
$$

其中 $w=\lVert\mathbf{v}_w\rVert$，单位为周期/秒。观察一个固定波峰，也就是令 $Fs-wt=C$：

$$
s(t)=\frac{w}{F}t+\frac{C}{F},\qquad \frac{ds}{dt}=\frac{w}{F}
$$

因此减号让波峰沿 $+\mathbf{d}$ 方向推进，空间推进速度是 $w/F$ UV/秒。若改成 $Fs+wt$，固定相位会沿 $-\mathbf{d}$ 移动。这里的加减号只决定传播朝向，不代表数值应该递增还是递减。

这也解释了为什么 `warpSpeed` 不是直接的 UV/秒：它是时间相位速率，必须除以空间频率才能得到波形在 UV 上的推进速度。当 $F=0$ 时只剩全域同步变化，不再存在可定义的空间传播速度；需要行进波时应使用大于零的频率。

#### 7. 用两组交叉相位打散规则横条

单一正弦波会产生固定间隔的规则条带。可以构造两组方向、频率和时间符号不同的连续相位：

```hlsl
float phaseA =
    warpCoordinate * (irregularDensity * 0.37)
    + crossCoordinate * (irregularDensity * 0.73)
    - t * (warpSpeed * 0.61);

float phaseB =
    warpCoordinate * (irregularDensity * 0.83)
    - crossCoordinate * (irregularDensity * 0.29)
    + t * (warpSpeed * 0.23);

float waveA = sin(phaseA * 6.2831853);
float waveB = sin(phaseB * 6.2831853);
```

两组相位都同时依赖纵向坐标 $s$ 和横向坐标 $q$，但使用不同系数，并让时间项以不同速度、不同符号运动。它们的干涉会形成持续变化的斜向交错区域。这里的常数不是随机数生成器，而是人为选择的非整齐比例；输出仍然完全确定、连续且可重复。

随后用两组波调制主波的相位和强度：

```hlsl
float phaseVariation = waveA * waveB * (irregularity * 0.25);
float strengthVariation =
    lerp(1.0, 0.45 + 0.55 * (waveA * 0.5 + 0.5), irregularity);

float warpOffset =
    sin((basePhaseCycles + phaseVariation) * 6.2831853)
    * warpStrength
    * strengthVariation;
```

相位扰动为：

$$
\Delta c=0.25I\sin(2\pi c_A)\sin(2\pi c_B)
$$

它改变局部波峰的位置和间距。强度调制为：

$$
m=\operatorname{lerp}\left(1,\ 0.45+0.55\left(0.5\sin(2\pi c_A)+0.5\right),\ I\right)
$$

当 $I=0$ 时，$\Delta c=0$ 且 $m=1$，退化为规则主波；当 $I=1$ 时，$m$ 的范围约为 $[0.45,1]$。最终标量位移是：

$$
e=A\,m\,\sin\left(2\pi(Fs-wt+\Delta c)\right)
$$

这种方法用额外 ALU 换取非规则感，不增加噪声纹理采样。它只能产生确定性的伪不规则形变，并不等于真正的随机噪声或二维流场。

#### 8. 合成最终采样坐标

```hlsl
float2 sampleUV =
    noiseUV
    + frac(t * scrollVector)
    + warpDirection * warpOffset;
```

对应：

$$
\mathbf{u}'=\mathbf{u}+\operatorname{frac}(t\mathbf{v}_s)+\mathbf{d}e
$$

三部分职责彼此独立：

- `noiseUV` 决定原始纹理坐标和 Tiling/Offset；
- `scrollVector` 只负责整张纹理持续平移；
- `warpDirection * warpOffset` 只负责沿 Warp 轴进行局部拉伸和压缩。

因为主波的投影坐标和最终位移都沿 $\mathbf{d}$，这是纵向 Warp：它改变沿流动轴的局部采样密度。如果目标是左右摆动或蛇形弯曲，应使用独立的位移方向；那是另一种视觉契约，不能与这里的“沿轴拉伸压缩”混为一谈。

最终颜色链可以写成：

```hlsl
float noise = SAMPLE_TEXTURE2D(_NoiseMap, sampler_NoiseMap, sampleUV).r;
float3 flowColor = SAMPLE_TEXTURE2D(_Ramp, sampler_Ramp, float2(noise, 0.5)).rgb;
float3 finalEmission = originalEmission * (1.0 - mask) + flowColor * tint * mask;
```

先完成坐标运动，再采样一次 Noise，之后才对采样结果做一次 Ramp 映射。Mask 颜色、基础色调制和自发光合成属于应用层，可以替换；它们不改变 Warp 的坐标数学。

#### 9. UV 折叠与“像多层重影”的边界

先忽略不规则调制，只看沿 Warp 轴的一维映射：

$$
s'=s+A\sin(2\pi(Fs-wt))
$$

它对原坐标的导数是：

$$
\frac{ds'}{ds}=1+2\pi AF\cos(2\pi(Fs-wt))
$$

若希望映射始终保持同一方向、不发生局部反转，则规则波情况下应满足：

$$
2\pi\lvert AF\rvert<1
$$

当该乘积大于 1，部分区域的导数可能小于零，同一小段纹理会被反向采样，出现明显拉伸、重复或类似多层重影的单帧形变。这不是历史帧残留，而是当前帧 UV 映射发生折叠。若美术目标需要强烈扭曲，折叠也可以是有意效果；若希望流动连续清晰，应优先同时约束 `Strength × Frequency`，而不是只降低其中一个参数。

加入相位和强度调制后，导数还包含调制项的空间变化，上式只是不规则版本的基础风险估算，不能作为完整的严格上界。需要工程级无折叠保证时，应推导全部调制项的最大导数，或直接限制最终位移场梯度。

#### 10. 纹理导入和时间采样造成的视觉问题

滚动灰度纹理使用 Point 过滤时，采样结果会在像素格之间离散跳变。运动期间这些跳变可能被观察成拖影、闪烁或一层层残留；它不一定意味着帧缓冲真的累积了历史图像。在一次实际材质调试中，把 Noise 的 Filter Mode 从 Point 改为 Bilinear 后，编辑器中的这类观感明显减轻，支持“纹理采样阶跃”是主要诱因之一。

这条经验不能替代对 TAA、Motion Blur、相机堆叠或其他时域后处理的排查；不同项目仍需分别验证。常见导入检查包括：

- 使用 Repeat Wrap，保证滚动跨越整数 UV 后继续循环；
- 流动纹理通常先试 Bilinear，只有明确需要像素风格时才使用 Point；
- 缩小时根据画面稳定性决定是否使用 Mipmap；
- 灰度 Noise 若作为数值场使用，应明确决定 Linear 或 sRGB 导入，因为 sRGB 解码会改变数值分布，不能无意识沿用颜色贴图设置；
- 纹理自身若不无缝，Repeat 仍会暴露接缝。

#### 11. 性能特征与取舍

在 Flow 编译关键字开启时，这套片元计算新增的主要工作包括：

- 一次灰度 Noise 纹理采样；
- 一次 Ramp 纹理采样；
- 三次 `sin`；
- 一次 `rsqrt`、一次 `sqrt`、若干 `dot`、乘加和插值；
- 不需要片元阶段运行时分支，也不需要多相 Noise/FlowMap 采样。

它用 ALU 换取纹理带宽和采样次数的减少，是否更快取决于目标 GPU、分辨率、Overdraw、纹理缓存命中率、Shader 其他部分及编译结果。没有 GPU Profiler、RenderDoc 或真机数据时，只能描述指令结构，不能声称已经获得具体性能收益。

#### 12. 常见误解

1. **“时间应该累加，为什么代码却在相乘？”**

   时间变量已经由引擎累加；`time * velocity` 是把累计时间换算为累计位移。

2. **“为什么不直接 `normalize`？”**

   可以。显式 `dot + rsqrt` 的主要价值是零向量保护和复用长度平方，不代表必然更快。

3. **“为什么投影必须使用单位方向？”**

   单位方向让 `Frequency` 保持周期/UV，让向量长度只控制时间相位。否则向量长度会同时缩放空间坐标，造成多个参数耦合。

4. **“相位为什么使用减法？”**

   `Fs - wt` 沿正方向传播，`Fs + wt` 沿负方向传播；正负号是传播方向约定。

5. **“Warp 和 Scroll 是不是同一件事？”**

   不是。Scroll 是整个采样域的刚性平移；Warp 是不同位置获得不同偏移，从而局部改变采样密度。

6. **“不规则交错是不是随机噪声？”**

   不是。它是几组确定性连续正弦的干涉，重复输入必然得到重复输出。

#### 13. 采用检查清单

适合采用这套方法的条件：

- 目标是风格化能量、火焰、翅膀纹路等方向性拉伸流动；
- 有独立 UV 集合可控制流动区域的铺法；
- 希望减少同一噪声纹理的多相采样，并能接受更多 ALU；
- 不需要真实二维速度场、旋涡或物理流体行为；
- 可以针对目标纹理调节 `ScrollVector`、`WarpVector`、频率、强度和不规则密度。

落地时按以下顺序调试：

1. 先把 Warp 强度设为零，只验证第二套 UV、Repeat 和基础滚动方向；
2. 把不规则度设为零，只调主 Warp 的方向、相位速度、频率和强度；
3. 用 $2\pi\lvert AF\rvert$ 检查是否进入明显折叠区；
4. 再增加不规则度与不规则密度，观察横向交错是否符合目标；
5. 最后接入 Ramp、Mask 和颜色调制，避免把坐标问题与颜色问题混在一起；
6. 在目标设备上用实际材质、覆盖率和分辨率进行 GPU 验证。

### 关键代码

```hlsl
float2 BuildScrolledWarpUV(
    float2 noiseUV,
    float timeSeconds,
    float2 scrollVector,
    float2 warpVector,
    float warpStrength,
    float warpFrequency,
    float irregularity,
    float irregularDensity)
{
    float warpLengthSq = dot(warpVector, warpVector);
    float2 warpDirection = warpVector * rsqrt(max(warpLengthSq, 0.000001));
    float warpSpeed = sqrt(warpLengthSq);

    float warpCoordinate = dot(noiseUV, warpDirection);
    float2 crossDirection = float2(-warpDirection.y, warpDirection.x);
    float crossCoordinate = dot(noiseUV, crossDirection);

    float basePhaseCycles = warpCoordinate * warpFrequency - timeSeconds * warpSpeed;
    float phaseA =
        warpCoordinate * (irregularDensity * 0.37)
        + crossCoordinate * (irregularDensity * 0.73)
        - timeSeconds * (warpSpeed * 0.61);
    float phaseB =
        warpCoordinate * (irregularDensity * 0.83)
        - crossCoordinate * (irregularDensity * 0.29)
        + timeSeconds * (warpSpeed * 0.23);

    float waveA = sin(phaseA * 6.2831853);
    float waveB = sin(phaseB * 6.2831853);
    float phaseVariation = waveA * waveB * (irregularity * 0.25);
    float strengthVariation =
        lerp(1.0, 0.45 + 0.55 * (waveA * 0.5 + 0.5), irregularity);
    float warpOffset =
        sin((basePhaseCycles + phaseVariation) * 6.2831853)
        * warpStrength
        * strengthVariation;

    return noiseUV
        + frac(timeSeconds * scrollVector)
        + warpDirection * warpOffset;
}
```

### 验证记录

- [2026-09-03] 对 Unity 2022.3 LTS、URP 14.0.12 自定义 HLSL 实现完成静态链路核对和数学推导；确认使用第二套 UV、独立 Scroll/Warp、一次 Noise 采样、一次 Ramp 采样和 Mask 自发光合成。
- [2026-09-03] 材质调试中观察到 Noise 从 Point 改为 Bilinear 后，编辑器运动时的残影/跳变观感明显改善；该项为交互式视觉观察，没有保存同机位逐帧 A/B 数据。
- [2026-09-03] 尚未执行目标 VR 设备 GPU Profiling、不同纹理的系统参数扫描、长期运行精度测试或完整材质回归；文中的性能结论仅限静态指令结构，视觉质量仍依赖纹理和参数。

---

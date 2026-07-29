# 静态体积云天空的高质量离线烘焙

**标签**：#unity #graphics #shader #rendering #experience
**来源**：项目实现与 Unity 编辑器实测（主体）；Guerrilla Games Horizon/Nubis、EA Frostbite、Dobashi 2007、Fattal 2009 与 NOAA/NSSL 公开资料（理论、求解器和现实视觉参照）
**收录日期**：2026-07-27
**来源日期**：2007 / 2009 / 2015-08 / 2016-07 / 2026-07-29（实践验证）
**更新日期**：2026-07-29
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐（静态云链路已多视角验证；闪电传输参考解已通过数值收敛，最终球面视觉仍待验收）
**适用版本**：Unity 2021.3+；Built-in/URP 天空盒路径

### 概要

当云形、天气和时间段只需要离散预设时，可以把体积云的高成本密度与光照积分完全移到 Editor。静态天空用球壳云层、程序化密度、Beer–Lambert 消光、Henyey–Greenstein 相位、Powder 与多重散射近似生成 HDR 半八面体母图；动态云后闪电则在同一静态密度体上，为若干固定发光路径离线求传输响应。快速标量扩散只能形成低频灯罩，不能作为真实参考；当前参考解采用保留方向、遮挡、云边界逃逸和散射阶的反向逐纹素 Monte Carlo。发布阶段仍只输出基础 LogRGBA 与第二张 Basis LogRGBA，Player 平静帧一次采样，非零闪电帧两次采样。

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
    ├─ RGB：静态天空 LogRGB
    └─ A：一个独立固定闪电单元的 LogR 响应
            ↓ Unity 导入
       Linear / Mipmap / Clamp / Trilinear / Android ASTC 4×4
            ↓
       另外四个固定闪电单元离线求解并打包为 LogRGBA Basis
            ↓
       运行时天空 Shader：平静一次采样，非零闪电两次采样
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

#### 静态云体到闪电传输基的离线积分

太阳是远距离定向光；云后闪电是位于介质内部的局部发光路径。两者不能只靠替换光照方向：局部源还需要距离衰减、源到碰撞点的云内透射、观察方向相位函数、云边界逃逸和多次散射。

##### 现实夜间图像给出的视觉门槛

NOAA/NSSL、NWS 与 NASA 夜间图像中，典型云内闪不是一个被高斯模糊放大的中心圆斑，而是同时具有：

1. 小范围高亮核心；若放电通道没有被云完全遮挡，还会出现更细、更硬的可见主干。
2. 沿相连云体扩展的大片较弱响应，亮度随光学距离分层衰减。
3. 云褶皱、厚云暗缝和局部遮挡对亮区进行切割；扩大覆盖不能以抹掉这些结构为代价。
4. 没有云介质的方向不产生“云体散射响应”。附近零散云仍可能被照亮，因为光可以从放电路径传播到这些云胞；若没有单独绘制 Direct/主干，无云间隙中看不到电弧是正确的数据职责结果。

因此视觉验收必须在天空球多视角完成，半八面体展开方图只能用于数值、接缝和方向分布诊断，不能单独证明“像闪电”。

##### 从辐射传输方程理解传输 Basis

稳态参与介质中的方向辐亮度满足：

~~~text
dL(x, wo) / ds
  = -sigma_t(x) * L(x, wo)
    + sigma_s(x) * integral_Omega[p(wi -> wo) * L(x, wi) dwi]
    + Q(x, wo)
~~~

固定云密度、消光、散射反照率和相位函数后，方程对发光源项 `Q` 线性。可以分别求若干固定闪电路径 `Q_i` 的响应 `Basis_i(direction)`，运行时再按脉冲强度线性组合；无需保存完整三维动态云，也不需要每帧重走体积。

##### 快速局部光近似的用途与边界

构图阶段可以把弯折折线离散成点源，对观察射线中的每个云样本 `x` 计算：

~~~text
r_j          = distance(x, p_j)
T_source_j   = exp(-integral_{p_j -> x}(sigma_t ds))
source_j     = Energy_j * T_source_j / (r_j^2 + radius^2)
single_j     = source_j * Phase(view, p_j -> x)
Basis_i      = integral_view(T_view * sigma_s * sum_j(single_j) ds)
~~~

它能快速验证放电路径位置、有限半径、第一阶遮挡和视线合成，但经验性的高阶散射项容易退化为各向同性模糊。实践中还测试过三维标量 Jacobi 光场：有限半径源、云内消光、按密度差抑制串光的双边权重确实把 5% 受光面积从约 `3.63%` 扩大到 `22.19%`，但高频结构比从约 `0.0567` 降到 `0.0241`。结果成为更宽、更平的“灯罩”，而不是被云胞暗缝切割的真实响应。

这说明单标量扩散在每次迭代中已经丢失传播方向；继续扫描迭代次数、gain、密度指数或边缘锐度只能改变灯罩宽度，不能恢复被压掉的角向信息。标量 Jacobi 可保留作有意的低频艺术补光或控制变量，不能再承担完整闪电传输参考解。

##### 反向逐纹素 Monte Carlo 参考解

当前参考求解器直接对最终半八面体纹素追踪观察者路径，保留方向、遮挡和散射阶：

1. 用与正式云烘焙一致的程序化密度生成三维体素快照；`sigma_t = density * extinction`。连接透射对该三线性体素表示求解，不冒充对原始连续噪声的解析精确解。
2. 每个体素 cell 根据局部最大密度建立 majorant，观察者路径用 cell DDA 和 delta/null-collision tracking 采样真实碰撞。
3. 每个半八面体纹素从观察者沿纹素中心方向发射相同预算的相机路径；纹素立体角单独计算，用于能量统计。
4. 在每次真实碰撞处，对连续闪电折线执行 next-event estimation。折线按“线段长度 × 局部功率”采样位置，源到碰撞点的透射用 cell DDA 与二点 Gauss–Legendre 积分。
5. 后续散射方向按 Henyey–Greenstein 相位函数重要性采样；throughput 累积单散射反照率，高阶路径使用 Russian roulette 保持期望能量。
6. 另行估计观察者直接看到发光路径的 Direct，输出 Direct、Single、Multiple 和 Combined 四种诊断量。检查“云体被照亮”时应先观察 `Single + Multiple`，把 Direct/可见电弧作为独立职责。
7. 原始参考探针关闭球面 Tent 重建和引导降噪，避免用空间平滑制造虚假的跨种子一致结构。

有限半径采用稳定参考软核：

~~~text
geometricTerm = 1 / (distanceSquared + sourceRadiusSquared)
~~~

它统一用于 Direct 和 NEE，能限制零半径线源附近的重尾方差；它是有限半径的平滑近似，不冒充严格采样发光圆柱。一次对照中 Combined 峰值由 `0.025981` 降至 `0.003668`，约下降 `7.1` 倍，近源孤立火花不再支配自动曝光。

大行星坐标还暴露了一个可复用边界问题：观察者位于约数千千米的坐标值上，而云底只高出约一千米。单精度 AABB 的 `center ± extent / 2` 消减可能把下边界抬高亚米级，使观察者被误判在体积外并得到零碰撞。密度体底部保留约 `0.01 km` 的真空入口余量，并用真实行星尺度回归测试覆盖该条件，比任意上移相机更可靠。

##### 散射阶诊断与正式五单元打包

诊断 EXR 的通道约定是：

~~~text
R = Direct
G = Single
B = Multiple
A = Combined
~~~

它不是运行时四位置 Basis。正式输出应对五个固定闪电单元分别求同一种标量响应：一个写入基础 LogRGBA 的 A，另外四个写入 Basis LogRGBA 的 RGBA。固定介质下传输对源功率线性，所以同一通道可以离线叠加多个始终共享时序的源；需要独立时序的区域仍必须占独立通道。

四通道必须共享同一线性、滤波、Mip 和归约语义。把总光学厚度、前表面深度、AO、类别 ID 混装进自动 Mip 的 Basis 纹理会因归约规则不同而失真；二维积分密度也不能恢复任意新光源所需的三维深度顺序。可选 CloudAux 应另设低分辨率纹理，并只保存同类连续量。

##### 当前数值收敛证据与视觉门禁

以下探针保持同一云体、有限半径、确定性连接透射，关闭 Direct 艺术预览、Tent 和降噪：

| 检查 | 结果 | 结论 |
|---|---|---|
| 64²、1024 spp、O24、两个独立种子 | Combined 能量差约 `1.20%`；原始像素相关 `0.908`；1 px 统计邻域相关 `0.989` | 广域低频结构跨种子成立 |
| 两种子 5% 支撑与质心 | `40.77% / 41.50%`；质心差约 `0.23 px` | 不是中心模糊或少量盐粒偶然扩散 |
| NEE 连接数 `2 -> 8` | 连接数增至四倍，RSE 中位数仅约 `0.634 -> 0.598` | 当前主要瓶颈不是简单增加 NEE 数 |
| 最大阶 `12 -> 24` | Combined 能量增加约 `1.35%`；硬截断由 `1229` 降至 `8` | 参考探针采用 O24 |
| 128²、1024 spp、O24 | `16,777,216` 条路径；Combined 能量约 `0.000137781`；RSE 中位数约 `0.2502` | 数值参考已进入可做球面视觉检查的阶段 |
| 水平半域 `64 km -> 96 km` | Combined 能量差约 `0.33%` | 规则方形观感不是局部密度盒裁切造成 |

这些数据证明估计器开始收敛，不证明最终画面已经像真实闪电。下一门禁是把 128² 的 `Single + Multiple` 投回测试天空球，从雷源中心、左右偏转和上视角分别捕获 Idle、峰值与响应调试图，并检查：云胞暗缝是否保留、远端是否分层响应、无云区是否泄漏、是否仍像均匀雾罩，以及半八面体接缝/规则边界是否可见。通过后才值得运行第二个 128² 高样本种子、升至发布分辨率并批量求五单元。

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
| 质量评估 | 1024 | 192 | 20～24 | 4 | 多视角与事件型 Basis 检查 |
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
- 快速局部光近似已经生成过可运行的 Base A + Basis RGBA 五单元资产；反向 Monte Carlo 目前只完成单个代表单元的数值参考与 128² 原始输出，尚未完成天空球视觉门禁、五单元正式打包和发布分辨率终稿。
- 可见闪电主干、动态云影和任意运行时光源不在本模块范围内；无云方向需要看到电弧时，应由独立三维主干或经过明确权衡的 Direct 层承担。
- Quest 真机 ASTC 通道误差、双眼画面、构建变体和 1/2 次采样 GPU 成本仍需目标设备验证。

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
- [Dobashi et al. 2007: A fast rendering method for clouds illuminated by lightning taking into account multiple scattering](https://doi.org/10.1007/s00371-007-0146-3) - 预计算云体闪电 Basis Intensities，并在运行时线性组合直接光与多重散射响应。
- [Fattal 2009: Participating media illumination using light propagation maps](https://doi.org/10.1145/1477926.1477933) - 以 Discrete Ordinates 保留传播方向，并讨论 false scattering 与 ray effect；用于说明标量扩散丢失角向信息的边界，不代表当前实现复刻该算法。
- [NOAA/NSSL Severe Weather 101: Lightning](https://www.nssl.noaa.gov/education/svrwx101/lightning/) - 闪电类型与现实云内放电参照入口。
- [Unity Volumetric Clouds Volume Override reference](https://github.com/Unity-Technologies/Graphics/blob/master/Packages/com.unity.render-pipelines.high-definition/Documentation~/volumetric-clouds-volume-override-reference.md) - Cloud Map/LUT 通道打包和数据纹理关闭 sRGB 的官方参考。
- [Arm ASTC Format Overview](https://github.com/ARM-software/astc-encoder/blob/main/Docs/FormatOverview.md) - 128-bit 固定块、通道共享权重与 dual-plane 边界。

### 相关记录

- [半八面体单图 HDR 天空的编码、采样与色带治理](./hemi-octahedral-hdr-sky-texture.md) - HDR 母图之后的方向布局、编码、导入和发布链路。
- [色带（Color Banding）与抖动（Dithering）知识](./color-banding-dither.md) - 静态天空平滑渐变的输出量化问题。
- [URP 天空盒 Shader 机制与常见问题](./urp-skybox-notes.md) - Unity 天空盒渲染路径注意事项。
- [VR 静态云天空与动态闪电的分离合成](./vr-static-sky-lightning-compositing.md) - 五单元数据契约、运行时时序、RegionMask 边界与双眼路径。

### 验证记录

- [2026-07-27] 在 Unity 编辑器中完成 512×512、192 视线步、24 光照步、4 子样本的瓦片化烘焙，并从迎光、侧光、背光、天顶四个方向检查；高负载单 Draw 曾触发编辑器/GPU 故障，改为 128×128 瓦片后稳定完成。
- [2026-07-28] 原理与实现过程扩写：按当前 Shader/C# 实现补齐球壳求交、密度公式、光照积分、多重散射近似、子像素采样、瓦片化、成本模型、参数关系、失败诊断和实现限制。明确公开资料是理论参照，当前程序化噪声与经验常数属于项目实现。
- [2026-07-28] 参数语义复核：确认固定视线步数下，增大最大步进距离主要会增大单步长度而非循环次数；确认 groundColor 当前不会进入上半球烘焙结果，也不是云底反弹光参数，已在正文标明。
- [2026-07-28] 来源性复核：原 EA Frostbite PDF 直链返回 404，改用可访问的 SIGGRAPH 2016 课程索引；该页面仍提供 Frostbite 原始演示文稿。
- [2026-07-28] 1024 与闪电编码闭环更新：完成 1024×1024、192 视线步、20 太阳光步、4 子样本的正式静态云烘焙，并为四条相邻闪电路径生成快速近似 LogRGBA 传输基。四通道编码最大码值均低于 167、没有 255 饱和纹素；基础与 Basis 导入契约均通过 Unity 检查。该结果证明编码和运行时组合可用，不再作为闪电传播形态已经真实的证据。
- [2026-07-29] 正确性与求解器重大修正：现实夜间图片复核确认旧 16 图主要扩大、模糊中心光团，缺少大片相连云体的分层响应与暗缝切割。三维标量 Jacobi/双边扩散虽扩大 5% 受光面积，却进一步降低高频结构，正式退出完整传输主线。实现有限半径反向逐纹素 Monte Carlo 参考解，并修复大行星坐标下观察者落在密度 Bounds 外的问题。64²/1024 spp 双种子在能量、空间相关、支撑面积与质心上收敛；O24、128²/1024 spp 和 64/96 km 域对照通过数值门禁。最终天空球多视角、第二个 128² 高样本种子、五单元打包与 Quest 真机仍明确列为未验证。

---

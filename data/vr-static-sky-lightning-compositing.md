# VR 静态云天空与动态闪电的分离合成

**标签**：#unity #shader #vr #rendering #experience
**来源**：Unity Shader、控制器与离线传输实践总结；Unity XR Single-Pass Instanced/Multiview 规范；Dobashi 2007、Jarosz 2008、Fattal 2009、Kulla 2012、SVGF 2017、Herholz 2019 与 NOAA/NSSL 现实参照
**收录日期**：2026-07-27
**来源日期**：2007 / 2008 / 2009 / 2012 / 2017 / 2019 / 2026-07-29（实践验证）
**更新日期**：2026-07-29
**状态**：⚠️ 待验证
**可信度**：⭐⭐⭐⭐（数据契约、控制器、桌面多视角与参考解数值收敛已有实践证据；首轮 128² 球面视觉门禁已明确失败，改进估计器与目标头显仍待验收）
**适用版本**：Unity 2021.3+；OpenXR/Meta XR 的 Single-Pass Instanced 或 Multiview

### 概要

云形静态而闪电动态时，不应把闪电时序烘进基础天空。基础半八面体纹理的 RGB 保存无闪电云层，Base A 与第二张 Basis RGBA 保存五个位置明显不同、形状固定的标量云内闪传输响应；运行时只动态编排脉冲、位置和组合。传输响应自身定义空间影响，默认不再叠规则 RegionMask。VR 两眼共享同一组纹理资产和同一脉冲状态，Shader 仍为每眼执行正确的方向采样，不复制资源也不假设两眼共享片元结果。

### 内容

#### 记录定位与当前完成度

本文记录已经落地的数据/运行时架构，以及仍在推进的高质量离线传输参考解。必须明确区分“功能已实现”“数值参考收敛”和“最终视觉/真机已通过”：

| 模块 | 当前状态 | 已有证据 |
|---|---|---|
| 静态云半八面体纹理 | 已实现 | Editor 多视角截图、一次采样静态审计 |
| LogRGB 解码与 Tone Mapping | 已实现 | Shader 编译、导入设置与色带 A/B |
| VR Stereo/Instancing 宏 | 已实现但未上目标头显 | Shader 编译与桌面路径通过 |
| Base A + Basis RGBA 五单元契约 | 已实现 | Base A 独立位置、RGBA 四个额外位置；旧重复通道有兼容语义 |
| 快速局部光 Basis | 已实现但形态被现实参照否决 | Night/Dusk 多视角、时序和编码可用；远场仍像平滑灯罩 |
| 反向逐纹素 Monte Carlo 参考 | 数值门禁通过、首轮球面视觉门禁失败 | 有限半径、双种子、O24、128²与体积域对照曾通过数值检查；投回天空球后暴露径向/竖向条纹、盐粒与锥形亮罩 |
| 多区域闪烁控制器 | 已实现，自动选择仍需回归 | 单单元、跨区接力、双区同闪和混合模式；72/90 Hz 手动关键帧通过 |
| 最终五单元高分辨率资产 | 未完成 | 等待代表单元球面视觉通过后再批量生成 |
| Quest/PCVR 双眼回归 | 未验证 | 需要目标设备、构建变体与 GPU 抓帧 |

因此本文仍保持“待验证”。控制器和双纹理合成已经不是纸面设计，但也不能用“代码能点亮云”替代“多帧像闪电、球面多角度像云内闪、目标头显双眼一致”三项最终门禁。

#### 设计目标与约束

- 云形和基础天空静态，不做运行时体积 Ray March。
- 闪电亮度和时序动态，可快速主闪、衰减和复闪。
- 闪电要表现为云内/云后能量透出，而不是在 LDR 天空上叠一块白色 UI。
- 移动 VR 平静帧尽量保持一次天空纹理采样。
- 左右眼共享同一天空资产；Stereo 只负责每眼矩阵和渲染层。
- 雷暴区域应由多个固定单元覆盖；多样性主要来自选择、接力和组合，而不是在一个小区域里反复做难以察觉的微变形。
- 云体传输响应与可见闪电主干分工：没有云的方向可以没有散射响应，但需要看到电弧时必须另设 Direct 或三维主干。

#### 数据职责分离

推荐把数据分成：

- `BaseSkyRGB(direction)`：无闪电、包含静态云和静态太阳的场景线性天空。
- `BaseCell(direction)`：基础纹理 Alpha 中的一个独立标量闪电传输单元。
- `BasisCellsRGBA(direction)`：第二张纹理中的另外四个标量传输单元。
- `PulseBase(t)` 与 `PulseRGBA(t)`：运行时快速主闪、复闪、持续电流尾迹及空间事件编排。
- `VisibleBolt/Direct`：可选的可见放电通道；不与云体多重散射响应混为一张四位置纹理。

应先在线性 HDR 空间合成，再做 Tone Mapping：

```text
skyLinear
  = BaseSkyRGB
    + LightningColor
      * (BaseCell * PulseBase + dot(BasisCellsRGBA, PulseRGBA))
output = ToneMap(skyLinear)
```

如果先把两张图各自压成 LDR 再混合，高亮很容易剪白，云后透光也会失去能量关系。

##### 为什么保存“增量”而不是完整亮天图

设无闪电 HDR 天空为 B，第 i 个固定闪电单元完全点亮后的 HDR 天空为 Si：

~~~text
Di = max(Si - B, 0)
~~~

运行时：

~~~text
L = B + LightningColor * Σ(Basis_i(direction) * Pulse_i(t))
output = ToneMap(L)
~~~

- `Basis_i` 只保存第 i 个固定单元带来的正向能量，避免把静态天空重复存一遍。
- `Pulse_i(t)` 是该单元当前脉冲；同一事件可 one-hot、依次点亮或同时点亮两个远隔单元。
- 空间支撑已经由源位置、云密度、遮挡和散射共同烘进 `Basis_i`，不再需要通用规则 Mask。
- max(..., 0) 适合纯发光增量；若设计包含闪电时压暗环境或有符号颜色变化，则需要有符号格式或把环境变化拆成单独参数。

##### 高质量闪电增量如何离线生成

真正的“云后透光”不只是二维光斑。离线烘焙时应对闪电局部光再做一次云内散射：

1. 用当前太阳/环境光烘焙基础天空 B。
2. 把闪电建模为具有有限半径的连续折线路径，定义位置、长度、分支、功率和半径。
3. 在与基础天空一致的静态密度体上求源到碰撞点透射、Henyey–Greenstein 相位、观察者透射和多次散射。
4. 分开输出 Direct、Single、Multiple 和 Combined 诊断阶；评估“云被照亮”时先看 Single + Multiple，可见主干由 Direct/三维对象另行负责。
5. 为五个固定位置分别得到同类标量响应，一个写入 Base A，另外四个写入 Basis RGBA。
6. 使用与基础天空相同的半八面体方向、旋转、地平线和 Linear/Clamp/Mip 约定，但可为闪电响应单独拟合 Log 编码范围。

快速视线积分适合构图，三维标量 Jacobi 适合低频补光；高质量参考应保留传播方向。当前实践使用反向逐纹素 Monte Carlo、连续折线 NEE、delta/null-collision、确定性连接透射和散射阶分离。若只烘二维径向 Mask 或把单标量场反复扩散，覆盖会变宽，但云胞暗缝和方向性会被抹成灯罩。

##### 多处候选如何放进两张纹理

固定介质下传输对源功率线性，因此可以按运行时时序需求打包：

- 永远共享同一时序的多个发光路径可以在离线阶段相加到一个标量单元。
- 需要独立选择或错峰的区域必须占不同通道；RGBA 是一次采样取得四个响应，不是四次采样。
- 当前契约使用 Base A + Basis RGBA 共五个固定单元，覆盖一片较宽雷暴扇区。普通事件 one-hot 选择单元，跨区事件在远隔单元间接力，双区事件同时点亮两个远隔单元。
- 旧 schema 若让 Base A 与 Basis R 保存同一中心，只能按四个独立单元计数；迁移时不得把重复通道当第五处闪电。
- 若五种独立时序仍不足，才考虑额外纹理/数组；不能把更多候选相加后再指望 RegionMask 分离重叠贡献。

离线 `Orders` 诊断纹理的 RGBA 表示 Direct/Single/Multiple/Combined，不是四个位置。正式绑定前必须检查 metadata/schema，避免把散射阶误当空间单元。

#### 三种运行时数据方案

##### 方案 A：基础 RGB + Base A，一次采样单单元

基础 LogRGBA 的 RGB 保存静态天空，A 保存一个固定闪电单元。该单元发生事件时仍只需一次纹理采样：

- 优点：平静和该单元闪电时都是一次采样，最适合极限带宽路径。
- 缺点：只能独立控制一个空间响应；不能用程序化 Mask 把一个已经联合的传输场无损拆成多个位置。
- 适用：固定过场、只有一个主要雷区，或作为没有第二张 Basis 纹理时的兼容路径。

##### 方案 B：Base A + Basis RGBA，五单元双纹理

第二张同映射 LogRGBA 保存四个额外固定单元，是当前默认架构：

- 平静/黑场只采基础纹理；Basis 脉冲非零时增加第二次采样。
- 一次 Basis 采样同时取得四个响应，随后只需四项点积；一个事件点亮一个还是两个单元都不增加采样数。
- 五个位置可以覆盖较宽雷暴扇区，同时保持每个造型固定、可重复和动漫式可读。
- 缺点是峰值帧每眼增加一次纹理读取；必须保留关键字开/关构建变体，并用目标设备抓帧验证真实采样数。

##### 方案 C：基础完整天空与点亮完整天空交叉淡入

~~~text
L = lerp(BaseSky, LitSky, flashCurve)
~~~

它最容易制作，但重复保存大量基础颜色；多天气、多时间段、多闪电位置会快速扩张资产数量。两张完整天空必须分别解码后在线性 HDR 空间混合，不能直接插值 Log 码值。它适合少量固定过场，不适合可组合雷暴系统。

##### 选择表

| 目标 | 推荐 |
|---|---|
| 单一固定雷区且严格一次采样 | 方案 A |
| 宽雷暴区域、固定动漫造型、峰值允许第二次采样 | 方案 B |
| 只有一个固定点亮状态、制作效率优先 | 方案 C |
| 超过五个区域且全部需要独立时序 | 增加同语义纹理/数组并重新评估带宽 |

#### 为什么不再把 RegionMask 作为默认层

`Basis_i(direction)` 已经是“固定源 i 经云体遮挡、散射和视线透射后，在该观察方向产生多少能量”。它不是一张等待 Mask 塑形的均匀光层。再乘规则圆形/球形 RegionMask 会带来三个问题：

1. Mask 边缘与云密度无关。强度升高后，原本看不出的平滑圆边会成为明显原型轮廓。
2. 相连云体可能跨越人工半径；Mask 会把本应衰减传播到远端云胞的能量硬切断，只剩中心区域变亮、变糊。
3. 联合传输场中的多个重叠源不能靠 Mask 重新分离。关闭某一处时仍可能留下已经在离线阶段相加的贡献。

没有云的方向不显示云体闪光、周围零散云却有响应，并不说明缺少 Mask。原因通常是当前 Basis 只保存介质散射：无云处 `sigma_s = 0`，而旁边云胞仍能收到光。若艺术目标要求在无云间隙看见闪电，应增加独立可见主干/Direct，而不是把云体响应 Mask 扩到空域。

RegionMask 仍可用于调试、紧急艺术裁剪或选择一张明显过宽的旧联合资产，但它不应成为新高质量 Basis 的组成部分。确需使用时，应在世界方向上做宽而连续的角域权重，并明确它是艺术限制而非物理传播；不要在半八面体 UV 上画普通圆，因为映射各处角尺度不均匀。

#### 闪电时序与运行时状态机

单个正弦波通常不像闪电。现实观感既有一两个显示帧内迅速出现/消失的短击，也有因多次回击、持续电流、云内散射和相机曝光而显得衰减较慢的事件。风格化实现应同时提供“短促多回击”和“带慢尾迹的持续事件”，而不是让所有闪电共用一个对称曲线。

当前状态机按秒推进，在 72 Hz 与 90 Hz 下只做显示帧量化，不把时长写死成帧数：

~~~text
Idle
  → SelectSpatialEvent（选择单元与空间模式）
  → PrimaryAttack（通常 1～2 个显示帧内快速上升）
  → PrimaryDecay（非对称快速衰减）
  → OptionalRestrikeDelay
  → RestrikeAttack / RestrikeDecay（零到多次）
  → OptionalPersistentCurrent（较弱、较慢的尾迹）
  → Cooldown
  → Idle
~~~

空间事件使用固定造型而不是邻路微混合：

- `SingleCell`：one-hot 点亮一个单元，最清晰、最常用。
- `CrossRegionSequence`：同一次雷暴在两个远隔单元间先后接力。
- `DualCellCluster`：两个远隔单元同时点亮，表现整片雷暴区活跃。
- `Mixed`：按权重选择上述模式，不改变单元内部形状。

早期“主通道 92% + 相邻通道 8%”只产生难以察觉的局部微变形，同时让事件长期集中在一个小区域，已不再作为默认策略。若动漫风格要求每次闪电造型固定，固定 Basis 恰好是优势；多样性应放在位置、事件组合和节奏上。

运行时参数职责应分组，避免把扩大范围、增加事件数和改变脉冲形状混为一谈：

| 参数组 | 典型参数 | 实际作用 |
|---|---|---|
| 全局事件频率 | 事件目标间隔、间隔随机幅度、全局最短间隔 | 决定整片雷暴区多久触发一次事件；不改变单次亮区大小 |
| 空间长期分布 | Base A/R/G/B/A 活跃权重、空间模式权重 | 决定长期更常使用哪些位置和组合；不改变某单元内部传输 |
| 复用保护 | 同单元最短复用间隔 | 避免连续事件总落在同一位置；必须检查事件涉及的每个单元，而不只是主单元 |
| 单次脉冲 | Attack、Decay、回击数量/间隔/倍率、持续电流强度/时长 | 决定多帧形态；不改变云体空间响应 |
| 双区组合 | 第二单元强度 | 决定 DualCellCluster 中远端单元相对亮度；仍保持总 HDR 不提前 saturate |
| 可复现性 | 随机种子 | 固定测试序列，便于 72/90 Hz 和参数 A/B 对照 |

每个固定单元还拥有独立离线参数：

| 参数 | 含义与可见影响 |
|---|---|
| 方位、仰角、云内深度 | 决定放电路径位于雷暴区何处、嵌入哪层云；是扩大雷暴覆盖的首要参数 |
| 垂直长度 | 决定主通道纵向跨度；过短像点光，过长可能穿出云层 |
| 路径抖动、主路漂移 | 控制固定折线的细小弯折与总体偏移；只影响造型，不应承担区域随机化 |
| 分支强度、分支张角 | 控制侧枝可见度和展开程度；过大会抢走云体受光主体 |
| 源半径 | 控制有限半径软核与近源方差；不是屏幕空间模糊半径 |
| Direct 强度/半径 | 控制观察者直接看到的发光主干；关闭时无云处没有电弧，但云体仍可发光 |
| 参考功率 | 线性缩放该单元整体能量；最终仍需与 Tone Mapping 一起检查过曝 |
| 高阶散射与最大传播范围 | 控制远端多次散射近似或求解域；不能替代增加更多空间单元，也不能靠数值增大修复错误求解器 |
| 散射各向异性 | 控制能量沿方向传播的偏好；标量扩散已丢失方向时，单独调整该参数无法恢复真实结构 |

控制器应保存当前阶段、阶段时间、参与单元、峰值强度、颜色和随机种子，并只把已经求好的 `BasePulse + PulseRGBA` 上传给 Shader。复杂随机和状态机不应在每个像素执行。

天空材质建议在运行时实例化，避免直接修改项目资产；多个相机共用时还要明确参数是全局天气状态还是相机局部状态。自动状态机回归必须覆盖“所有单元都在冷却”“双区第二单元也在冷却”和“旧资产存在重复中心”三种边界，不能仅以手动关键帧通过代替。

如果使用 Shader keyword/独立材质来省掉平静帧的第二次采样，应在闪电开始和结束时切换，而不是每帧反复切换关键字。

#### VR 双眼适配

天空方向和纹理内容对双眼相同，不需要左右眼纹理。运行时 Shader 需要补齐 Unity Stereo/Instancing 宏：

```hlsl
struct Attributes
{
    float4 positionOS : POSITION;
    UNITY_VERTEX_INPUT_INSTANCE_ID
};

struct Varyings
{
    float4 positionCS : SV_POSITION;
    float3 direction : TEXCOORD0;
    UNITY_VERTEX_OUTPUT_STEREO
};

Varyings Vert(Attributes input)
{
    Varyings output;
    UNITY_SETUP_INSTANCE_ID(input);
    UNITY_INITIALIZE_OUTPUT(Varyings, output);
    UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(output);
    output.positionCS = UnityObjectToClipPos(input.positionOS);
    output.direction = input.positionOS.xyz;
    return output;
}

float4 Frag(Varyings input) : SV_Target
{
    UNITY_SETUP_STEREO_EYE_INDEX_POST_VERTEX(input);
    // 左右眼使用同一 direction->UV 公式和同一纹理资源。
}
```

同时使用 `#pragma multi_compile_instancing`。这解决的是每眼矩阵、实例 ID 和渲染层路由，不会自动保证项目的 Shader Variant 收集/剔除策略正确。

##### 为什么两眼可以共享同一天空纹理

静态天空按“观察方向”索引，并假设位于无限远。左右眼只相差约一个 IPD 的位置，远处云层产生的视差通常远小于纹理角分辨率，所以两眼可使用相同 direction→UV 和同一纹理资源。

需要区分：

- 共享纹理资源：只在显存保存一份天空资产。
- 共享采样结果：并不会发生。两眼覆盖的像素仍各自执行片元 Shader。
- Single-Pass：主要减少 CPU 提交和组织开销，不会自动把双眼像素成本减半。

如果闪电实体或云体接近玩家到能产生明显双眼视差，应把近距离闪电主干、粒子或局部体积光作为三维对象单独渲染；天空纹理只承担远场云层响应。

##### 宏链职责

| 宏 | 位置 | 作用 |
|---|---|---|
| UNITY_VERTEX_INPUT_INSTANCE_ID | 顶点输入 | 接收实例/眼索引数据 |
| UNITY_SETUP_INSTANCE_ID | 顶点函数开头 | 初始化当前实例 |
| UNITY_VERTEX_OUTPUT_STEREO | 顶点输出 | 为 Stereo 路由保留字段 |
| UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO | 顶点函数 | 写入每眼输出信息 |
| UNITY_SETUP_STEREO_EYE_INDEX_POST_VERTEX | 片元函数 | 恢复当前眼索引 |

当前 Shader 还使用 multi_compile_instancing。构建时必须确认项目的 Shader Variant 剔除工具没有删除 STEREO_MULTIVIEW_ON / STEREO_INSTANCING_ON 所需变体。

#### 面向当前项目的实现步骤

##### 阶段 1：用现实参照定义单单元门槛

1. 选择夜间云内闪图片，分离“小亮核、大片相连云响应、云褶皱暗缝、可见主干”四项职责。
2. 固定一个代表放电路径和一份静态夜间云体；先只比较空间传输，不同时扫描 Tone Mapping、颜色和时序。
3. 分开保存 Direct、Single、Multiple、Combined；检查无云区、远端云胞和云层遮挡。
4. 拒绝只让中心变大、变糊的候选，即使其功能上已经实现“云后发光”。

##### 阶段 2：先做数值参考，再做视觉合成

1. 为有限半径、真实观察者入口、真空/纯吸收和散射阶分类建立数值自检。
2. 使用两个独立随机种子比较能量、空间相关、支撑面积、质心和高方差比例；禁止只看自动曝光 PNG。
3. 做最大散射阶与求解域 A/B，排除硬截断和体积盒裁切。
4. 参考图关闭 Tent/降噪；只有原始结构跨种子成立后才允许视觉重建。

##### 阶段 3：天空球多角度门禁（首轮已失败）

1. 将高样本 `Single + Multiple` 临时编码成与正式 Shader 一致的 LogRGBA 标量响应，不带 Direct。
2. 克隆运行时天空材质，在 `finally`/等价清理路径中恢复相机、天空材质和临时对象。
3. 至少捕获雷源中心、左右各偏转约 15°、上视约 12°；每个角度同时保留 Idle、峰值和响应调试图。
4. 检查暗缝、远端分层、无云泄漏、均匀雾罩、半八面体接缝和规则边界。
5. 只有该门禁通过，才运行第二个 128² 高样本种子、升发布分辨率和批量五单元。

首轮门禁使用排除 Direct 的 `Single + Multiple`，从雷源中心、左右各约 15° 和上视约 12° 四个方向分别保存 Idle、峰值和响应调试图，共 12 图。对应 128² 响应有 `13,020` 个正值纹素，P99.5 为 `0.0005930066`、最大值为 `0.00350952`；相对峰值的 5% / 18% 支撑分别约为 `9.729%` / `3.418%`，仅 2 个编码值发生裁切。这些数字说明响应并非空图，却不能证明视觉结构正确。

视觉上，低分辨率原始高方差被放大成明显径向/竖向条纹和盐粒，并形成宽大的锥形亮罩；四个方向都无法确认云胞暗缝、褶皱和远端分层。因此该门禁判定为失败：不运行第二个 128² 高样本种子，不升发布分辨率，也不批量生成五单元。普通模糊、Tent、增亮曝光或更强 Tone Mapping 都不能把这份失败结果改称参考真值。

##### 阶段 3B：先改源采样估计器，再重做球面门禁

1. 将当前“线段长度 × 局部功率”的源位置提案保留为基线，新增按碰撞点条件化的软逆平方/等角提案，并用完整混合 PDF 重新加权，避免改变期望能量。
2. 先做单线段 PDF 归一化、无偏均值和方差自检，再以相同种子做 64² A/B；同时比较能量置信区间、RSE、峰值、空间支撑与耗时。
3. 只有 64² 明显降方差且均值一致，才重做 128² 四方向球面门禁；详细推导与候选算法边界见相关的静态云烘焙记录。
4. 若局部 NEE 改进仍不足，再评估伴随场体积路径引导或 Beam Radiance；SVGF/à-trous 只能作为原始结构成立后的重建候选，不能替代参考解。

##### 阶段 4：五单元发布与状态机

1. 用同一物理量分别写入 Base A 与 Basis RGBA，禁止把 Orders 散射阶图误当位置 Basis。
2. 为五个单元保存独立位置、路径、分支、源半径、功率和传播参数；metadata 与运行时计数必须版本化。
3. 验证 SingleCell、CrossRegionSequence、DualCellCluster、Mixed，以及每个参与单元的复用保护。
4. 在 Night、Dusk 和 Day 中检查同一空间响应；夜间承担真实性主判，其他时间段检查过曝、黑块和色偏。
5. 验证 Log 编码、ASTC Alpha、Tone Mapping 与 Dither，不用更强模糊掩盖传输问题。

##### 阶段 5：VR 和构建

1. 保留 Stereo/Instancing 宏。
2. 检查 Android/Quest 构建中的实际 Shader Variant。
3. 在双眼中检查太阳、云边、闪电中心和地平线方向一致。
4. 用 GPU 工具确认采样数、纹理格式和分支行为。

#### 性能模型

| 状态 | 每眼纹理采样 | 数据能力 |
|---|---:|---|
| 平静、黑场、冷却 | 1 次基础 LogRGBA | 静态 RGB；Base A 数据随同读取但脉冲为零 |
| 只使用 Base A 的兼容事件 | 1 次 | 一个独立标量响应 |
| 任意 Basis RGBA 单元非零 | 2 次 | Base A + RGBA 共五个独立标量响应 |
| 双区同时点亮或四通道混合 | 仍为 2 次 | 只增加点积 ALU，不增加纹理读取 |
| 再增加第三张辅助数据 | 3 次 | 必须在真机 A/B 后才能常驻 |

动态 uniform 分支不保证省掉纹理读取。若平静成本是硬约束，优先使用明确 Shader 变体/材质路径，并通过抓帧确认。Single-Pass Instanced/Multiview 减少提交与组织成本，不会让左右眼共享同一次片元采样。

#### 真机验证清单

1. Quest Multiview 与 PCVR Single-Pass Instanced 至少各验证一次目标路径。
2. 检查左右眼太阳、云边和半八面体地平线是否完全同向，无单眼丢失。
3. 检查 Shader Variant 构建后仍保留 `STEREO_MULTIVIEW_ON` / `STEREO_INSTANCING_ON` 相关变体。
4. 闪电高亮在线性空间合成后再 Tone Mapping，检查是否出现单眼剪白或色带。
5. 使用 GPU Profiler/RenderDoc 确认平静材质没有意外执行闪电增量采样。
6. 快速转头时检查半八面体 Mip、闪电 Basis 和 Dither 是否产生双眼闪烁。
7. 检查基础与增量使用不同 range/K 时，两个解码参数是否分别正确。
8. 检查运行时克隆材质，避免退出 Play Mode 后污染天空资产。

#### 常见失败与定位

| 现象 | 原因 | 修正 |
|---|---|---|
| 闪电只让中心变大、变糊 | 标量扩散/后处理模糊代替方向传输 | 对照现实图；检查 raw Single/Multiple，改用保留方向的参考解 |
| 受光范围扩大但像均匀灯罩 | 高阶标量场抹掉云胞暗缝 | 停止扫 gain/迭代；保留角向传输、遮挡和边界逃逸 |
| 无云处不亮，旁边零散云发光 | Basis 只保存云体散射，未绘制 Direct 主干 | 若需要电弧，单独增加 Direct/三维主干；不要用 Mask 填空域 |
| 高亮后出现模糊圆形原型边缘 | 仍乘规则 RegionMask | 移除默认 Mask，让 Basis 自身决定空间支撑 |
| 闪电一亮整片天空变灰 | 在 LDR 或编码域混合 | 两张图分别解码后在线性 HDR 合成 |
| 平静帧仍有两次采样 | 动态分支未省略采样 | 使用独立材质/变体并抓帧确认 |
| 多区域关闭一个仍残光 | 联合增量图中候选重叠 | 改独立通道、数组或多纹理 |
| 每次总落在同一区域 | 活跃权重、空间模式或复用保护错误 | 用固定种子记录事件；逐个检查所有参与单元的冷却 |
| 展开图出现规则方形边界 | 半八面体展开观感或体积域裁切 | 先做求解域 A/B，再投回天空球多视角判断 |
| 夜晚/黄昏云出现异常黑块 | HDR 负值/NaN、Log 解码、Tone Map 暗部或压缩问题 | 逐级检查 raw HDR、编码前后、ASTC 与最终输出，不用提亮掩盖 |
| 多帧像呼吸灯而不像闪电 | 对称正弦或所有事件共用同一衰减 | 使用快速 Attack、多回击、可选持续电流尾迹，并在 72/90 Hz 回放 |
| 只有一只眼显示 | Stereo 宏或变体缺失 | 检查宏链和构建剔除 |
| 双眼位置略不同 | 近距离闪电被当无限远天空 | 近场主干/体积光改为三维渲染 |
| 高亮剪白并出现色带 | 峰值、Tone Map、输出量化 | 保留 HDR 合成、压肩部并检查 Dither |

### 参考链接

- [Unity 2022.3: Single-pass instanced rendering and custom shaders](https://docs.unity3d.com/2022.3/Documentation/Manual/SinglePassInstancing.html) - 自定义 Shader 的 Stereo/Instancing 宏。
- [Unity 2022.3: Single-pass stereo rendering](https://docs.unity3d.com/2022.3/Documentation/Manual/SinglePassStereoRendering.html) - Unity XR 单通道立体渲染背景。
- [Dobashi et al. 2007: A fast rendering method for clouds illuminated by lightning taking into account multiple scattering](https://doi.org/10.1007/s00371-007-0146-3) - 离线预计算闪电 Basis Intensities 并在线性运行时组合的公开依据。
- [Jarosz et al. 2008: The Beam Radiance Estimate for Volumetric Photon Mapping](https://doi.org/10.1111/j.1467-8659.2008.01153.x) - 整条相机束收集光子可降低逐点体积光子估计噪声，但核估计引入空间偏差，只作为后备候选。
- [Fattal 2009: Participating media illumination using light propagation maps](https://doi.org/10.1145/1477926.1477933) - 保留传播方向的离散方向方法，以及 false scattering/ray effect 边界；用于解释标量扩散的局限。
- [Kulla & Fajardo 2012: Importance Sampling Techniques for Path Tracing in Participating Media](https://doi.org/10.1111/j.1467-8659.2012.03148.x) - 用等角/Cauchy 提案匹配近光源的 `1/r²` 弱奇异项，并与其他提案通过 MIS 组合；当前线源条件化方案是基于同一数学结构的适配，不是对论文算法的原样复刻。
- [Schied et al. 2017: Spatiotemporal Variance-Guided Filtering](https://doi.org/10.1145/3105762.3105770) - 依赖时域积累、方差和深度/法线/ID 引导；用于约束降噪的证据边界。
- [Herholz et al. 2019: Volume Path Guiding Based on Zero-Variance Random Walk Theory](https://doi.org/10.1145/3230635) - 联合指导碰撞距离、散射方向、Russian roulette 与 splitting，说明只优化局部 NEE 仍可能留下高阶残余方差。
- [NOAA/NSSL Severe Weather 101: Lightning](https://www.nssl.noaa.gov/education/svrwx101/lightning/) - 现实闪电类型和云内放电参照入口。

### 相关记录

- [静态体积云天空的高质量离线烘焙](./static-volumetric-cloud-sky-baking.md) - 球壳云、局部光近似、标量扩散反证和反向 Monte Carlo 参考解。
- [半八面体单图 HDR 天空的编码、采样与色带治理](./hemi-octahedral-hdr-sky-texture.md) - Base A + Basis RGBA 数据契约、方向编码、Log 编码与采样成本。
- [VR 相机壳体特效：不使用后处理的全屏替代方案](./vr-camera-shell-effects-without-post-processing.md) - 移动 VR 中避免全屏后处理的相关取舍。
- [VR Shader 变体收集器架构](./vr-variant-collector-architecture.md) - Multiview/Instancing 变体保留与预热。

### 验证记录

- [2026-07-27] 静态基础天空的 VR Stereo/Instancing 宏已加入运行时 Shader，Unity ShaderUtil 返回 0 条编译消息；左右眼共享单张纹理的结构已完成。动态闪电增量纹理、区域时序和目标头显双眼效果尚未实现与真机验证，因此保留“待验证”状态。
- [2026-07-28] 原理与实现过程扩写：明确基础天空、VR 宏、闪电增量和真机验证的完成状态；补充局部闪电离线散射、增量定义、多候选重叠限制、三种存储方案、无 acos 球面 Mask、闪电状态机、双眼共享纹理原理、宏职责、性能模型、分阶段实现步骤和失败诊断。动态闪电仍未实现，状态不提升。
- [2026-07-29] 实现状态重大更新：完成 Base A + Basis RGBA 五固定单元契约、one-hot 单单元、跨区接力、双区同闪和混合状态机；移除默认 8% 邻路微混合。Night/Dusk 桌面多视角、72/90 Hz 多回击/持续尾迹、Log 编码和 Shader 模块编译已有证据；自动单元冷却、目标构建与真机双眼仍需回归。
- [2026-07-29] 正确性修正：现实夜间图像表明旧测试主要是中心光团变宽、变糊，不足以证明云内闪真实。规则 RegionMask 会在高亮时暴露原型边缘并切断远端相连云体，正式撤销其默认推荐。补充“无云处没有散射响应、附近零散云仍可受光、可见电弧由 Direct/三维主干负责”的数据职责解释。
- [2026-07-29] 离线参考验证：三维标量 Jacobi/双边扩散因灯罩化被淘汰；有限半径反向逐纹素 Monte Carlo 的 64² 双种子、O24、128² 高样本与 64/96 km 求解域对照通过数值门禁。最终 128² 天空球多角度、第二高样本种子、五单元发布分辨率和 Quest/PCVR 真机尚未完成，因此状态继续保持“⚠️ 待验证”。
- [2026-07-29] 球面视觉门禁与论文复核：完成正确 128² `Single + Multiple` 响应的四方向 Idle/峰值/Debug 共 12 图检查。虽然数值响应非空且仅 2 个编码裁切纹素，画面仍出现径向/竖向条纹、盐粒和锥形亮罩，无法确认云胞暗缝、褶皱及远端分层，首轮球面门禁判定失败。依据 Kulla–Fajardo 的等角采样、Herholz 的体积路径引导、Jarosz 的 Beam Radiance 与 SVGF 的引导边界，下一步确定为先验证无偏的源条件化 NEE，不以滤波掩盖 raw 方差。

---

# VR 静态云天空与动态闪电的分离合成

**标签**：#unity #shader #vr #rendering #experience
**来源**：方案设计与 Unity Shader 实践总结；Unity XR Single-Pass Instanced/Multiview 规范
**收录日期**：2026-07-27
**来源日期**：2026-07-27
**更新日期**：2026-07-28
**状态**：⚠️ 待验证
**可信度**：⭐⭐⭐（Shader 编译与桌面视角验证通过，尚缺目标头显真机双眼和动态闪电回归）
**适用版本**：Unity 2021.3+；OpenXR/Meta XR 的 Single-Pass Instanced 或 Multiview

### 概要

云形静态而闪电动态时，不应把闪电时序烘进基础天空。基础半八面体纹理只保存无闪电云层；闪电保存为同映射下的场景线性能量增量和区域控制，运行时按闪烁曲线合成。VR 两眼共享同一组天空纹理，Shader 只为每眼建立正确的裁剪空间和渲染层，不复制天空资源。

### 内容

#### 记录定位与当前完成度

本文同时包含“已经实现的静态天空 VR 适配”和“尚未实现的动态闪电设计”。必须明确区分：

| 模块 | 当前状态 | 已有证据 |
|---|---|---|
| 静态云半八面体纹理 | 已实现 | Editor 多视角截图、一次采样静态审计 |
| LogRGB 解码与 Tone Mapping | 已实现 | Shader 编译、导入设置与色带 A/B |
| VR Stereo/Instancing 宏 | 已实现但未上头显 | Unity ShaderUtil 0 编译消息 |
| 闪电增量烘焙 | 未实现 | 仅有数据和算法设计 |
| 多区域闪烁控制器 | 未实现 | 仅有状态机设计 |
| Quest/PCVR 双眼回归 | 未验证 | 需要目标设备 |

因此本文状态保持“待验证”，不能因为基础天空 Shader 编译通过就把动态闪电或真机 VR 标为已完成。

#### 设计目标与约束

- 云形和基础天空静态，不做运行时体积 Ray March。
- 闪电亮度和时序动态，可快速主闪、衰减和复闪。
- 闪电要表现为云内/云后能量透出，而不是在 LDR 天空上叠一块白色 UI。
- 移动 VR 平静帧尽量保持一次天空纹理采样。
- 左右眼共享同一天空资产；Stereo 只负责每眼矩阵和渲染层。
- 多处闪电可以独立控制时序，但需要明确相互重叠时的数据代价。

#### 数据职责分离

推荐把数据分成：

- `BaseSky(direction)`：无闪电、包含静态云和静态太阳的场景线性天空。
- `LightningDelta(direction)`：闪电照亮云层后相对基础天空增加的能量，而不是一张已经 Tone Mapping 的完整天空。
- `RegionMask(direction)`：控制多个闪电区域的空间范围。
- `FlashCurve(t)`：运行时的快速上升、衰减、复闪和随机时序。

应先在线性 HDR 空间合成，再做 Tone Mapping：

```text
skyLinear = baseSky + lightningDelta * regionMask * flashCurve
output = ToneMap(skyLinear)
```

如果先把两张图各自压成 LDR 再混合，高亮很容易剪白，云后透光也会失去能量关系。

##### 为什么保存“增量”而不是完整亮天图

设无闪电 HDR 天空为 B，第 i 个闪电候选完全点亮后的 HDR 天空为 Si：

~~~text
Di = max(Si - B, 0)
~~~

运行时：

~~~text
L = B + Σ(Di * Mi(direction) * Fi(t))
output = ToneMap(L)
~~~

- Di 只保存闪电带来的正向能量，避免把静态天空重复存一遍。
- Mi 是空间区域 Mask。
- Fi(t) 是独立闪烁曲线。
- max(..., 0) 适合纯发光增量；若设计包含闪电时压暗环境或有符号颜色变化，则需要有符号格式或把环境变化拆成单独参数。

##### 高质量闪电增量如何离线生成

真正的“云后透光”不只是二维光斑。离线烘焙时应对闪电局部光再做一次云内散射：

1. 用当前太阳/环境光烘焙基础天空 B。
2. 把闪电建模为点光、线段链或多个发光球，定义位置、颜色、半径和衰减。
3. 对每个云样本计算到闪电发光体的方向和距离。
4. 沿“云样本 → 闪电”方向积分云密度，得到局部光透射率。
5. 乘距离衰减、局部相位函数和云样本的视线消光。
6. 得到完整点亮天空 Si，再计算增量 Di。
7. 使用与基础天空相同的半八面体方向和 HDR 编码。

如果只烘一张二维径向 Mask，再用统一颜色相乘，能得到便宜的闪光，但不能还原局部光在云体内被遮挡、扩散和染色的结构。

##### 多处候选能否放在一张增量图

- 候选区域互不重叠时，可把多个 Di 相加到一张增量图，再用球面区域 Mask 分别选择。
- 候选重叠时，一张 RGB 增量图无法恢复每个 Di 的独立贡献；关闭其中一个闪电仍可能残留另一个候选的能量。
- 需要完全独立控制时，应使用多通道标量响应、Texture2DArray、增量图集或多张纹理，并重新评估采样成本。

#### 三种运行时方案

##### 方案 A：严格一次采样、受限但便宜

基础 LogRGB 使用 RGB，Alpha 保存一个标量闪电透光/能量 Mask。运行时用统一闪电颜色和程序化方向区域控制多个位置：

- 优点：平时和闪电时都只采同一张纹理一次。
- 缺点：只有一个标量能量通道，多区域不能完全独立保存不同颜色和复杂光照增量；区域重叠时控制能力有限。

适用于固定闪电色、闪电位置相互分离、重点追求最低采样成本的移动 VR。

当前发布纹理是 RGB24、Importer Alpha Source=None，所以方案 A 还没有实现。要采用它，必须同时修改：

- 烘焙输出改为 RGBA32，并在 Alpha 写入云响应或闪电能量标量。
- Importer 改为从输入读取 Alpha。
- 运行时一次采样读取 rgba，RGB 解 LogRGB，A 作为闪电响应。
- 重新验证 ASTC RGBA 的块压缩和 Alpha 梯度。

单个 Alpha 只能表达一个标量场。它适合“统一闪电颜色 × 多个程序化区域”，不适合多个候选各自拥有完整 RGB 散射。

##### 方案 B：基础纹理 + 闪电增量纹理

第二张半八面体纹理保存 RGB 闪电能量增量，可在一张图中烘焙多处候选闪电，再用程序化角域 Mask 选择区域。

- 平静天气使用只采基础纹理的材质/Shader 变体。
- 闪电发生时切换到额外采样增量纹理的材质。
- 优点：颜色、云内散射和多处闪电的还原更好。
- 缺点：闪电期间每眼增加一次纹理采样；如果用普通动态分支，编译器/GPU 未必能省掉未走分支的采样，使用独立材质或明确变体更可靠。

对于闪电事件稀疏的场景，方案 B 的平均成本通常可控，也是更容易获得高质量“云后发光透出”效果的方案。

##### 方案 C：基础完整天空与点亮完整天空交叉淡入

~~~text
L = lerp(BaseSky, LitSky, flashCurve)
~~~

它最容易制作，但存在明显缺点：

- 需要解码两张完整天空后在线性空间混合；直接混合 LogRGB 码值是错误的。
- LitSky 重复保存大量基础颜色，资产利用率低。
- 多个闪电状态会快速增加纹理数量。
- 独立控制多个区域仍需额外 Mask。

方案 C 适合少量固定过场，不适合可组合的天气系统。

##### 三种方案的选择表

| 目标 | 推荐 |
|---|---|
| 平静和闪电都严格一次采样、统一闪电色 | 方案 A |
| 优先高质量云内散射，闪电期间允许第二次采样 | 方案 B |
| 只有一个固定点亮状态、制作效率优先 | 方案 C |
| 多候选重叠且要完全独立 | 多通道/数组/多纹理，不能假装一张图足够 |

#### 闪电区域 Mask

半八面体 UV 可直接用于预烘焙 Mask，但运行时按世界方向做球面角域判断更稳定。移动 VR 中不需要为此执行 acos，可以直接比较夹角余弦：

```hlsl
float AngularRegionMask(
    float3 direction,
    float3 centerDirection,
    float radiusRadians,
    float edgeSoftness)
{
    float outerCos = cos(radiusRadians);
    float safeSoftness = clamp(edgeSoftness, 1e-3, 1.0);
    float innerCos = cos(radiusRadians * (1.0 - safeSoftness));
    float directionCos = dot(direction, centerDirection);
    return smoothstep(outerCos, innerCos, directionCos);
}
```

因为小角度对应更大的余弦值，所以 smoothstep 的下界是外圈 cos、上界是内圈 cos。centerDirection 必须归一化；edgeSoftness 用极小正数代替严格的 0，避免 smoothstep 两条边相等。

多区域可分别乘独立闪烁曲线：

- 取 max：避免重叠区域能量翻倍，适合把多个 Mask 当选择器。
- 直接相加：符合多个独立光源能量相加，但要保留 HDR，不能提前 saturate。
- 归一化加权：适合一张联合增量图，但不再严格保持物理能量。

不要在半八面体正方形 UV 上直接用普通圆形距离，因为映射不同位置的角尺度不均匀。

#### 闪电时序与运行时状态机

单个正弦波通常不像闪电。更可控的状态机：

~~~text
Idle
  → PrimaryAttack（快速上升）
  → PrimaryDecay（较慢衰减）
  → OptionalRestrikeDelay
  → RestrikeAttack / RestrikeDecay
  → Cooldown
  → Idle
~~~

每个候选区域保存：

- 当前阶段和阶段时间。
- 峰值强度、颜色和随机种子。
- 是否复闪、复闪间隔和衰减倍率。
- 方向中心、角半径和边缘柔度。

运行时只上传已经求好的 pulse 值，不应在每个像素里执行复杂随机状态机。天空材质建议在运行时实例化，避免直接修改项目资产；多个相机共用时还要明确参数是全局天气状态还是相机局部状态。

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

##### 阶段 1：定义可验证的单闪电

1. 在烘焙参数中增加一个局部闪电发光体。
2. 烘焙基础 B 和单候选 Si。
3. 输出 EXR 检查 Di = max(Si - B, 0) 是否只含闪电增量。
4. 使用一个固定球面 Mask 和手动 pulse 验证线性合成。
5. 确认 Tone Mapping 前后没有剪白和色带。

##### 阶段 2：选择发布数据

- 若采用方案 A：把基础发布纹理改为 RGBA，Alpha 写标量响应。
- 若采用方案 B：为闪电增量建立独立 LogRGB 半八面体纹理。
- 为基础和增量保存相同的映射、range/K、旋转约定和地平线边界规则。
- 若基础与增量峰值差异很大，允许使用不同 range/K，但运行时必须分别解码。

##### 阶段 3：多区域和状态机

1. 添加 2～4 个方向区域参数。
2. 每个区域使用独立 pulse。
3. 明确区域重叠使用 max 还是能量相加。
4. 实现 Idle/Attack/Decay/Restrike/Cooldown。
5. 平静材质与闪电材质分开，验证平静帧没有第二次采样。

##### 阶段 4：VR 和构建

1. 保留 Stereo/Instancing 宏。
2. 检查 Android/Quest 构建中的实际 Shader Variant。
3. 在双眼中检查太阳、云边、闪电中心和地平线方向一致。
4. 用 GPU 工具确认采样数、纹理格式和分支行为。

#### 性能模型

| 状态 | 方案 A | 方案 B |
|---|---|---|
| 平静帧 | 每眼 1 次基础采样 | 使用平静材质时每眼 1 次 |
| 闪电帧 | 每眼仍 1 次 RGBA 采样 | 每眼基础 + 增量共 2 次 |
| 多区域 | 主要增加 ALU/常量 | 若共用一张增量图仍是 2 次；独立图会继续增加 |
| 数据能力 | 单标量响应 | 完整 RGB 增量 |

动态 uniform 分支不保证省掉纹理读取。若平静成本是硬约束，优先使用不同 Shader 变体或不同天空材质，并通过抓帧确认。

#### 真机验证清单

1. Quest Multiview 与 PCVR Single-Pass Instanced 至少各验证一次目标路径。
2. 检查左右眼太阳、云边和半八面体地平线是否完全同向，无单眼丢失。
3. 检查 Shader Variant 构建后仍保留 `STEREO_MULTIVIEW_ON` / `STEREO_INSTANCING_ON` 相关变体。
4. 闪电高亮在线性空间合成后再 Tone Mapping，检查是否出现单眼剪白或色带。
5. 使用 GPU Profiler/RenderDoc 确认平静材质没有意外执行闪电增量采样。
6. 快速转头时检查 Mask、Mip 和 Dither 是否产生双眼闪烁。
7. 检查基础与增量使用不同 range/K 时，两个解码参数是否分别正确。
8. 检查运行时克隆材质，避免退出 Play Mode 后污染天空资产。

#### 常见失败与定位

| 现象 | 原因 | 修正 |
|---|---|---|
| 闪电像二维白斑 | 只叠 Mask，没有烘局部散射 | 烘焙点亮天空并保存增量 |
| 闪电一亮整片天空变灰 | 在 LDR 或编码域混合 | 两张图分别解码后在线性 HDR 合成 |
| 平静帧仍有两次采样 | 动态分支未省略采样 | 使用独立材质/变体并抓帧确认 |
| 多区域关闭一个仍残光 | 联合增量图中候选重叠 | 改独立通道、数组或多纹理 |
| Mask 在不同方向大小不一 | 用半八面体 UV 圆距离 | 改用方向 dot 的球面角域 |
| 只有一只眼显示 | Stereo 宏或变体缺失 | 检查宏链和构建剔除 |
| 双眼位置略不同 | 近距离闪电被当无限远天空 | 近场主干/体积光改为三维渲染 |
| 高亮剪白并出现色带 | 峰值、Tone Map、输出量化 | 保留 HDR 合成、压肩部并检查 Dither |

### 参考链接

- [Unity 2022.3: Single-pass instanced rendering and custom shaders](https://docs.unity3d.com/2022.3/Documentation/Manual/SinglePassInstancing.html) - 自定义 Shader 的 Stereo/Instancing 宏。
- [Unity 2022.3: Single-pass stereo rendering](https://docs.unity3d.com/2022.3/Documentation/Manual/SinglePassStereoRendering.html) - Unity XR 单通道立体渲染背景。

### 相关记录

- [静态体积云天空的高质量离线烘焙](./static-volumetric-cloud-sky-baking.md) - 基础云和未来局部闪电散射共用的球壳、密度与光照积分。
- [半八面体单图 HDR 天空的编码、采样与色带治理](./hemi-octahedral-hdr-sky-texture.md) - 基础天空和闪电增量共用的方向编码。
- [VR 相机壳体特效：不使用后处理的全屏替代方案](./vr-camera-shell-effects-without-post-processing.md) - 移动 VR 中避免全屏后处理的相关取舍。
- [VR Shader 变体收集器架构](./vr-variant-collector-architecture.md) - Multiview/Instancing 变体保留与预热。

### 验证记录

- [2026-07-27] 静态基础天空的 VR Stereo/Instancing 宏已加入运行时 Shader，Unity ShaderUtil 返回 0 条编译消息；左右眼共享单张纹理的结构已完成。动态闪电增量纹理、区域时序和目标头显双眼效果尚未实现与真机验证，因此保留“待验证”状态。
- [2026-07-28] 原理与实现过程扩写：明确基础天空、VR 宏、闪电增量和真机验证的完成状态；补充局部闪电离线散射、增量定义、多候选重叠限制、三种存储方案、无 acos 球面 Mask、闪电状态机、双眼共享纹理原理、宏职责、性能模型、分阶段实现步骤和失败诊断。动态闪电仍未实现，状态不提升。

---

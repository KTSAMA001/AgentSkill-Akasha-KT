# 静态体积云天空的高质量离线烘焙

**标签**：#unity #graphics #shader #rendering #experience
**来源**：项目实现与 Unity 编辑器实测（主体）；Guerrilla Games Horizon/Nubis、EA Frostbite、Unity Graphics 文档与 Arm ASTC 资料（体积云、编码和平台格式参照）
**收录日期**：2026-07-27
**来源日期**：2015-08 / 2016-07 / 2026-07-31（实践验证）
**更新日期**：2026-08-11
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐（球壳云、LogRGB、导入和运行时采样已有实践证据；当前 32/16/8 动态短瓦片、全尺寸 staging、分帧限载与逐项缓存已完成一个 512 厚云配置的实际烘焙和多视角检查，但当前实现尚未重新完成 1024 与目标移动 VR 设备验收，空白工程完全重写也未独立验证）
**适用版本**：已验证环境为 Unity 2022.3.62f3 / URP 14；其他 Unity、Built-in 或 URP 版本需重新验证 Shader 编译、纹理导入和天空盒路径

### 概要

当云形、天气和时间段只需要离散预设时，可以把体积云的高成本密度与光照积分完全移到 Editor。静态天空使用球壳云层、程序化密度、Beer–Lambert 消光、Henyey–Greenstein 相位、Powder 与多重散射近似生成 HDR 半八面体母图，再编码为一张运行时单次采样的 LogRGB 纹理。本文只记录静态体积云烘焙的原理、实现、参数、输出、复现和验收，不承担瞬态照明或动态事件的算法说明。

本文重点记录可复现的原理、实现链路、参数关系、失败模式和验证边界；Horizon/Nubis/Frostbite 是理论与设计参照，不代表当前代码逐行复刻这些引擎。

### 内容

#### 记录定位与来源边界

本文主体是一次 Unity 项目实践及其编辑器证据。公开资料提供了 Perlin–Worley 密度、天气控制、相位函数和多重散射近似等设计依据，但实践实现采用程序化噪声、固定垂直剖面和一组经验系数。引用这些资料不能等同于“完整复刻 Horizon/Nubis/Frostbite”，本次实践中的失败或限制也不能直接推广为同类算法在其他实现中普遍不可用。

2026-08-11 的 WebGL2 统一后端实践进一步确认：本文的“4 个经验多重散射补偿 lobe”、Unity Runner、动态短瓦片和缓存字段都属于这套 Unity 工具的具体合同，不能直接外推到另一实现。这里的 4 指补偿项数量，并非辐射传输方程严格求解到第四次物理散射。跨实现可以复用球壳、Beer–Lambert、全局像素坐标和质量不降级原则，但必须分别记录经验 lobe 数、源项图、样本序列、Kernel 身份和验证环境。

阅读本文时应区分四个证据层级。文中的操作步骤只以“当前工具合同”为准；历史结果只能说明它实际发生过，不能替代当前源码回归：

| 层级 | 含义 | 本文如何表述 |
|---|---|---|
| 当前工具合同 | `Settings Inspector → Baker Window → Runner → Bake Shader → 编码/导入 → 时间戳对照场景` | 菜单、开关、按钮、输出命名和参数语义按当前源码描述，是本文的实际操作入口 |
| 当前源码已验范围 | 32/16/8 动态短瓦片、全尺寸 staging、分帧限载、暂停/恢复/取消和逐项线性传输缓存；一个 512 厚云配置已实际完成 | 证明当前提交、回读和缓存链路可承担 512；不能外推为所有参数或 1024 已通过 |
| 历史高分辨率证据 | 固定 128 瓦片阶段完成过 512/1024 烘焙与多视角检查 | 可支持球壳云、HDR、编码和采样思路；1024 仍只是历史实现证据 |
| 候选扩展 | 2048、更高步数、目标设备格式与空白工程移植 | 只记录门禁与风险，不写成已经完成 |

#### 端到端实现链路

~~~text
ScriptableObject 烘焙参数
    ↓ 归一化、单位、输出目录与依赖指纹检查
线性传输缓存
    ├─ 命中：直接复用 Base RGB Half
    └─ 未命中：离线烘焙 Material
          ↓ 按工作量选择 32×32 / 16×16 / 8×8 动态短瓦片执行体积积分
       ARGBHalf 线性 HDR 瓦片
          ↓ GPU CopyTexture 汇总到全尺寸 staging RT
       每个 Pass 最终一次完整 ReadPixels
          ↓
完整半八面体 RGBAHalf CPU 母图
    ├─ 可选：导出 EXR 母版
    └─ RGB：静态天空 LogRGB
            ↓ Unity 导入
       Linear / Mipmap / Clamp / Trilinear / Android ASTC 4×4
            ↓
       运行时天空 Shader：上半球一次纹理采样
~~~

必须把“体积云求解”“方向到二维布局”“HDR 有限位深编码”“运行时 Tone Mapping”看成四个独立层次。某一层出现接缝、色带或过曝时，应先定位发生阶段，而不是改另一层掩盖问题。

#### 适用边界

该方案适合以下目标：

- 云形、天气状态与时间段是离散预设，不要求连续实时演化。
- 最多一个太阳可以作为静态天空的一部分，并随该天气/时间段固定烘焙。
- 离线烘焙优先追求画质，运行时优先追求低采样和低带宽。

如果运行时需要连续改变云量、太阳高度、风场或云层自阴影，通常应优先评估实时或半实时体积云；离散状态仍可继续烘焙，但应先计算资产数量、切换方式和内存成本，而不是把这一判断写成对所有项目都成立的绝对规则。

#### 静态体积云烘焙复现 SOP

这一节是本记录的可执行入口，目标是完成“静态云 + 背景天空 + 最多一个太阳”的独立闭环。动态事件不属于本文实现范围；需要时从文末“相关记录”进入对应专题。

##### 复现完成的判定

以下条件必须同时成立，才能称为“静态体积云烘焙已复现”：

1. Unity 脚本与 Shader 编译为 0 error；不能用旧缓存或粉色材质代替。
2. 能创建一份烘焙参数资产，并明确保存云层、太阳、质量和输出参数。
3. Editor 能从参数资产生成一张上半球半八面体 LogRGB PNG；选择导出母版时，还应生成线性 HDR EXR。
4. PNG 的导入设置为 Linear、Clamp、Trilinear、Mip On；运行时解码参数与烘焙时编码参数一致。
5. 运行时天空 Shader 对上半球只采样这张纹理一次，并能在 Unity 天空盒中正确显示；下半球由单独的地平线/地面颜色处理。
6. 至少检查迎光、侧光、背光、天顶和四个地平线象限，没有明显映射接缝、瓦片边界、方向翻转、异常纯黑块或 NaN/Inf 造成的彩色坏点。
7. 使用下方参数快照和当前工具至少完成 128 冒烟并得到非空云层；若要声称某组参数达到正式画质，还必须完成该配置的 512 多视角验收。当前实现已有一个厚云配置的 512 证据，但不能替代其他天气、时间段或参数组合自己的门禁；历史 1024 结果也不能替代当前实现重验。

##### 环境与前置条件

- 已实测环境：Unity 2022.3.62f3、URP 14、Linear Color Space、Windows Editor D3D11。
- 烘焙 Shader 只在 Editor 执行，可以限制到桌面 Editor 图形 API；Android/VR Player 使用另一份轻量天空 Shader，不应编译离线体积积分循环。
- 项目必须允许 Editor 脚本调用 `AssetDatabase`、`TextureImporter`、`Graphics.Blit`、`Graphics.CopyTexture`、`ReadPixels` 和 `EncodeToEXR`；交互模式还会在平台支持时使用 `GraphicsFence` 或 `AsyncGPUReadback` 作为非阻塞完成信号。
- 建议先确认当前 GPU/驱动稳定。一次 Draw 过重导致 D3D 设备重置后，不要在同一 Editor 进程内反复重试；先重启 Unity，再降低单次提交负载。
- 所有颜色都按线性 HDR 值理解。颜色选择器中大于 1 的值不是已经 Tone Map 后的屏幕颜色。

##### 最小文件和职责

目录名可以按项目规范调整，但职责不能缺失：

~~~text
StaticCloudSkyBaker/
├─ Editor/
│  ├─ StaticCloudSkyBakeSettings.cs       # ScriptableObject 参数、单位、范围和归一化
│  ├─ StaticCloudSkyBakeSettingsEditor.cs # Inspector 分组、天气/时段按钮、太阳读取和成本提示
│  ├─ StaticCloudSkyBakerWindow.cs         # 选择参数资产并触发静态烘焙
│  ├─ StaticCloudSkyBakeRunner.cs          # 瓦片渲染、HDR 汇总、LogRGB 编码、导入与 metadata
│  ├─ InteractiveBakeSession.cs            # 分帧限载、GPU 完成信号、暂停/恢复/取消（职责示例名）
│  ├─ TransportCache.cs                    # Base 与逐单元线性 Half 传输缓存（职责示例名）
│  ├─ MaterialMetadataBinder.cs            # 纹理与材质隐藏解码合同同步（职责示例名）
│  └─ StaticCloudSkyTestSceneBuilder.cs    # 绑定最新纹理并生成验收场景
└─ Shaders/
   ├─ StaticCloudSkyBake.shader            # Editor-only 体积积分，输出线性 RGBAHalf
   └─ HemiOctahedralStaticSky.shader       # Player 天空盒，半八面体采样、LogRGB 解码和 Tone Mapping
~~~

第一次实现时保持以下依赖方向：参数资产 → Runner → Bake Shader → HDR 母图 → 编码/导入 → Runtime Shader → 测试场景。运行时 Shader 不得反向依赖 Editor 程序集；Bake Shader 不应被加入 Player 的常用材质或运行时资源引用。

##### 参数资产必须包含的静态字段

字段名可按代码风格修改，但必须保存同等语义。所有距离统一用千米：

| 分组 | 字段 | 单位/范围 | 作用与约束 |
|---|---|---|---|
| 输出 | `textureResolution` | 16～4096 像素 | 单张正方形半八面体纹理的宽和高 |
| 输出 | `outputFolder` / `outputName` | 资产相对路径/文件前缀 | 输出必须位于允许的模块目录；同名结果使用唯一文件名，避免静默覆盖对照 |
| 输出 | `exportHdrExrMaster` | bool | 保留线性 HDR 真值，用于重新编码、调色和定位色带 |
| 输出 | `reuseTransportCache` | bool | 按依赖指纹复用完整三维积分后的线性 Half 结果；关闭时强制全量 GPU 烘焙，缓存不进入 Player 或版本库 |
| 球壳 | `planetRadius` | km，≥1000 | 行星曲率；地球近似值为 6371 |
| 球壳 | `cameraAltitude` | km，≥0 | 当前简化要求相机低于云底 |
| 球壳 | `cloudBottomAltitude` | km | 必须高于相机至少约 0.05 km |
| 球壳 | `cloudTopAltitude` | km | 必须高于云底；差值是云层厚度 |
| 球壳 | `maximumMarchDistance` | km，≥10 | 只截断积分距离，不会自动增加视线步数 |
| 造型 | `coverage` | 0～1 | 基础云量，控制“哪些地方有云” |
| 造型 | `coverageVariation` | 0～1 | 天气噪声对不同方向云量阈值的扰动 |
| 造型 | `baseNoiseScale` | >0 | 大云团空间频率；越大越碎 |
| 造型 | `detailNoiseScale` | >0 | 云边侵蚀频率 |
| 造型 | `detailErosion` | 0～1 | 云边高频侵蚀强度 |
| 造型 | `densityMultiplier` | >0 | 已有云体的光学厚度，不负责增加覆盖区域 |
| 造型 | `noiseOffset` | km 空间向量 | 平移同一套程序化噪声，生成另一种固定云形 |
| 天空 | `sunDirection` | 单位向量 | 从观察点指向太阳；保存前必须归一化 |
| 天空 | `sunColor` | 线性 HDR | 同时影响太阳圆盘和直射云光 |
| 天空 | `zenithColor` / `horizonColor` | 线性 HDR | 无云背景的天顶—地平线渐变 |
| 天空 | `ambientCloudColor` | 线性 HDR | 背光和厚云仍能获得的低频环境能量 |
| 天空 | `forwardScattering` | 0～0.999 | HG 前向叶；过高会在太阳附近形成尖峰 |
| 天空 | `backwardScattering` | -0.999～0 | HG 后向叶 |
| 天空 | `backwardWeight` | 0～1 | 双叶相位函数的后向叶占比 |
| 天空 | `powderStrength` | 0～2 | 受光边蓬松近似；过高会发白 |
| 天空 | `multipleScatteringStrength` | 0～2 | 4-lobe 经验多重散射补偿能量；过高会冲淡体积层次 |
| 天空 | `sunAngularRadiusDegrees` | 0.02°～2° | 太阳圆盘视半径；真实太阳约 0.27°，卡通圆盘可先试 0.5°～0.8° |
| 天空 | `sunGlowAngularRadiusDegrees` | 0°～20° | 外围光晕角半径；0 关闭光晕，与圆盘大小独立，不能用它代替圆盘尺寸 |
| 质量 | `viewSteps` | 8～384 | 每个子样本的视线 Ray March 步数 |
| 质量 | `lightSteps` | 2～128 | 太阳遮光步数下限，不是固定最终步数 |
| 质量 | `maximumLightStepLength` | 0.25～8 km | 太阳斜路径的最大物理步长；最终步数取 `max(lightSteps, ceil(distance/maxStep))` |
| 质量 | `samplesPerPixel` | 1～16 | 每纹素重复整套积分的抖动子样本数 |

保存或开始烘焙前执行归一化：限制分辨率和步数；保证 `cameraAltitude < cloudBottomAltitude < cloudTopAltitude`；把零长度太阳方向恢复为已知默认值，否则归一化；把所有频率、密度和最大距离限制为正数。归一化既应在 `OnValidate` 中执行，也应在 Runner 入口再次执行，避免脚本调用绕过 Inspector。

当前自定义 Inspector 的显示顺序是“输出 → 球体与云层（千米） → 云层造型 → 太阳与天空 → 闪电传输响应（离线烘焙） → 离线质量”。复现纯静态云时，第五组的总开关保持关闭，其余组按下列方式使用：

- “天气构图起点”中的 `稀疏积云`、`破碎雷雨云`、`层叠风暴云` 会成组改写覆盖率、密度、噪声和高度等云形字段；按钮还会更新同一参数资产中本文不使用的附加字段。点击后仍要保存参数资产并记录最终静态字段，不能只记录按钮名称。
- “时间段起点”中的 `正午`、`黄昏 / 蓝调`、`深夜` 会成组改写太阳和背景/环境颜色；它们是起点，不是统一美术标准。
- 太阳可用方位角、仰角直接编辑，也可从 Directional Light 读取。Unity 灯光的照射方向是 Transform 的正向，工具保存的却是“观察点指向太阳”的方向，因此读取公式为 `-light.transform.forward`；非 Directional Light 应拒绝。
- `sunAngularRadiusDegrees` 直接控制太阳圆盘视半径，`sunGlowAngularRadiusDegrees` 单独控制外围光晕；调整太阳大小时改前者，不要用 Bloom、光晕半径或提高 `sunColor` 冒充尺寸变化。
- Inspector 的成本提示用于解释当前参数的估算工作量和瓦片档位，不是画质评分，也不是烘焙输出。

##### 从零实现顺序

按以下次序实现和单独验证；不要先写完整高质量循环再一次性排错。

1. **半八面体方向逆映射**：让正方形中心得到 `(0,1,0)`，四边中点得到 `±X/±Z` 地平线方向，四角也落在地平线上。使用后文 `HemiOctahedralDirection` 公式。
2. **纯背景天空**：先关闭云密度，仅输出 `BackgroundSky(direction)`。确认太阳方向、太阳角半径、天顶和四个地平线方向正确，且正方形四边投回天空球时连续。
3. **球壳求交**：实现 `RaySphereNear`、`RaySphereFar` 和 `GetCloudSegment`。用地面观察者验证天顶、斜上方和地平线方向的 `start < end`；向下方向应先命中行星并拒绝云积分。
4. **密度函数**：实现 Gradient Noise、4-octave FBM、Worley F1、天气覆盖率、固定高度剖面和高频侵蚀。先输出灰度密度积分，不加光照；确认 `coverage` 改变占地范围，`densityMultiplier` 不改变密度形状。
5. **视线消光**：加入 `sigmaT = density * densityMultiplier`、`stepT = exp(-sigmaT*ds)` 和前向 alpha 合成。此时可以只用常量白色照明，验证厚云更不透明、薄云仍透出背景。
6. **太阳遮光**：每个有效视线样本沿 `sunDirection` 积分光学厚度。先检查行星遮挡：太阳在局部地平线以下时必须返回 0，不能穿过行星采到远侧云壳。
7. **相位与近似多重散射**：加入双叶 HG、Powder、4 个经验补偿 lobe 和环境光。每加入一项都保留开关或数值 0 的回退路径，便于定位过曝或死黑。
8. **子像素与首步抖动**：随机种子必须来自整图纹素坐标和样本序号。瓦片局部坐标只能负责输出位置，不能改变方向或随机相位。
9. **瓦片渲染与 HDR 汇总**：Bake Shader 每次只渲染一个短瓦片到 `ARGBHalf` RenderTexture；主路径用 `CopyTexture` 写入全尺寸 staging RT，每个 Pass 结束时只完整 `ReadPixels` 一次。瓦片必须使用 full resolution、global pixel/UV 和全局样本序列，不能在每个局部瓦片重新开始方向或随机相位。只有平台不支持区域复制或 staging 创建失败时才逐瓦片同步回读，全部数据完成后只 `Apply` 一次。
10. **LogRGB 编码与导入**：先从完整 HDR 母图测量 RGB 最大值，再拟合编码范围、量化到 8-bit PNG，写入 metadata 并配置 importer。
11. **运行时天空与测试场景**：运行时按世界/天空方向编码半八面体 UV，采样一次、解码 LogRGB，再执行曝光和 Tone Mapping。最后生成独立场景做球面多视角验收。

每一阶段的最小测试都通过后再进入下一阶段。若密度灰度阶段已经有接缝，不能靠 Tone Mapping 或 Dither 修复；若 EXR 正确而 PNG 有色带，应检查编码/导入，不要重新调云密度。

##### 当前工具的起始参数快照

下表是白天风暴云的历史可用参数快照，字段仍对应当前参数资产。它适合作为实现与排错起点，不是唯一美术答案，也不是对当前源码高分辨率结果的自动背书。当前窗口没有独立的“静态 LogRGB 模式”下拉框；第一次运行应关闭“烘焙云内闪电响应”，由该开关选择纯静态输出。

| 参数 | 值 | 参数 | 值 |
|---|---:|---|---:|
| `planetRadius` | 6371 | `cameraAltitude` | 0.1 |
| `cloudBottomAltitude` | 1.3 | `cloudTopAltitude` | 8.2 |
| `maximumMarchDistance` | 500 | `coverage` | 0.58 |
| `coverageVariation` | 0.40 | `baseNoiseScale` | 0.075 |
| `detailNoiseScale` | 0.52 | `detailErosion` | 0.34 |
| `densityMultiplier` | 1.45 | `noiseOffset` | (17, 5, -23) |
| `sunDirection` | normalize(0.42124453, 0.5616594, 0.71210384) | `sunColor` | (5.0, 4.45, 3.7) |
| `zenithColor` | (0.055, 0.14, 0.32) | `horizonColor` | (0.56, 0.67, 0.82) |
| `ambientCloudColor` | (0.32, 0.42, 0.58) | `forwardScattering` | 0.72 |
| `backwardScattering` | -0.22 | `backwardWeight` | 0.18 |
| `powderStrength` | 0.65 | `multipleScatteringStrength` | 0.50 |
| `sunAngularRadiusDegrees` | 0.27 | `exportHdrExrMaster` | 首次复现开启 |

质量分三个门槛递进，不要直接从最高档开始：

| 阶段 | 分辨率 | 视线步 | 太阳最少步 | 最大太阳步长 | 子样本 | 用途 |
|---|---:|---:|---:|---:|---:|---|
| 冒烟 | 128 | 64 | 8 | 4 km | 1 | 验证非空、方向、输出和导入，不评价最终画质 |
| 构图/回归 | 256 | 96 | 10 | 2 km | 1 | 调覆盖率、噪声尺度、太阳方向与色调 |
| 最低正式判断 | 512 | 128 | 12 | 2 km | 2 | 多视角、接缝、色带、异常黑块与时间段判断 |
| 高质量候选 | 1024 | 192 | 20 | 2 km | 4 | 历史固定瓦片阶段曾完成；当前源码必须在 512 通过后再独立重验 |

质量档与当前证据不能混写：

| 实现阶段 | 已有证据 | 仍需验证 |
|---|---|---|
| 历史固定 128×128 瓦片 | 512/1024 静态天空和多视角结果 | 只作为历史画质和参数参照，不证明当前瓦片代码正确 |
| 当前 32/16/8 动态瓦片源码 | 低负载跨瓦片检查，以及一个当前厚云配置的 512 实际烘焙、最终单次回读和多视角检查 | 新天气/参数仍按 128→256→512 递进；1024 放在对应 512 通过之后 |
| 2048 与更高步数 | 尚无本次实践证据 | 需要单变量升级、耗时、设备稳定性、输出 hash 和多视角截图 |

因此，2048、384 视线步、64 太阳步和 8 子样本都只是更高成本候选。当前 512 证据只覆盖已记录的厚云配置；即使历史版本曾完成 1024，新的天气、质量参数或传输实现也不能跳过 128/512 回归直接继承“已验证高质量”的结论。

##### 黄昏与夜间复现

保持云几何、噪声和密度不变，只覆盖下列字段，即可验证同一云体在不同时段的离线光照。这样能把“云形变化”和“光照变化”分开：

| 时段 | `sunDirection` | `sunColor` | `zenithColor` | `horizonColor` | `ambientCloudColor` | `maximumLightStepLength` |
|---|---|---|---|---|---|---:|
| 白天 | (0.42124453, 0.5616594, 0.71210384) | (5, 4.45, 3.7) | (0.055, 0.14, 0.32) | (0.56, 0.67, 0.82) | (0.32, 0.42, 0.58) | 2.0 |
| 黄昏 | (0.54961544, 0.09993008, 0.8294196) | (3.2, 1.25, 0.55) | (0.025, 0.055, 0.16) | (0.62, 0.20, 0.09) | (0.18, 0.16, 0.25) | 1.5 |
| 夜间 | (-0.19950187, -0.24937734, 0.9476339) | (0.015, 0.020, 0.035) | (0.004, 0.010, 0.035) | (0.015, 0.025, 0.060) | (0.05, 0.08, 0.18) | 2.0 |

方向写入前都要归一化。黄昏太阳斜路径更长，因此最大太阳步长收紧到 1.5 km；夜间太阳方向在局部地平线以下时，云的可见层次主要来自 `ambientCloudColor`，不应让直射光穿过行星。夜间或黄昏出现局部纯黑时，按“EXR 线性母版 → LogRGB PNG → Tone Mapping 后画面”的顺序定位，不能直接提高环境光掩盖 NaN、负值或解码错误。

##### Unity 中的实际操作顺序

已有本模块时，按以下步骤操作；从零实现者应先完成上面的文件职责和后文核心函数，再从第 1 步验证：

1. 等待 Unity 完成 Domain Reload，确认 Console 没有 C# 或 Shader error。
2. 从项目的静态体积云天空烘焙菜单打开窗口。若还没有参数资产，点击“创建默认参数资产”；也可以从 Create 菜单创建同类型参数资产。
3. 在窗口中选择参数资产。第一次复现复制“当前工具的起始参数快照”，或者先按天气/时段按钮生成起点，再逐项记录最终字段；不要直接修改团队共用预设。
4. 关闭“烘焙云内闪电响应”。当前窗口没有独立的“静态 LogRGB 模式”下拉框；输出模式由这个开关决定。按需打开“同时导出 HDR EXR 母版”，并为输出名称使用新的唯一前缀。
5. 先使用 128 冒烟档。此时窗口按钮应显示“烘焙单张半八面体 LogRGB 天空”；点击后进度条按瓦片推进，Console 应报告 Base pass 的瓦片尺寸、Draw 数和估算单片元工作量。
6. 成功后应至少得到 `<name>_HemiOct_LogRGB.png`；打开 EXR 时还得到 `<name>_HemiOct_HDR.exr`。
7. 选中 PNG 检查 importer 和 `userData` metadata，再从项目工具菜单创建时间戳对照场景。纯静态结果使用时间戳入口；要求附加瞬态数据的固定验收入口不属于本文复现流程。
8. 打开对照场景，确认 Camera 为 Skybox 清屏，`RenderSettings.skybox` 绑定运行时半八面体天空材质，材质的 `_SkyTexture` 指向刚生成的 PNG。
9. 检查中心、左右、背面、天顶和四个地平线象限。冒烟档只判断链路；当前源码按 128 → 256 → 512 递进，512 多视角通过后才考虑 1024。
10. 每次提高质量只修改分辨率/步数/子样本，不同时改云形和 Tone Mapping。保留上一级输出与截图，避免“更慢但无法知道改善来自哪里”。

##### 输出、编码与导入契约

静态烘焙的正确数据流是：

~~~text
Bake Shader 线性 HDR float
    → ARGBHalf 短瓦片
    → RGBAHalf 整图母图
    ├─ 可选 ZIP Float EXR（线性真值）
    └─ 逐通道 Log 编码 + 8-bit 量化 → PNG
          → Unity 以数据纹理导入
          → Runtime Shader 按 metadata 解码
~~~

天空 RGB 的自动范围：

~~~text
observedMaximum = max(整图所有 RGB)
R = clamp(max(0.0625, observedMaximum * 1.10), 0.0625, 32)
K = 16
encoded = log2(1 + clamp(linear, 0, R) * K) / log2(1 + R * K)
quantized = round(saturate(encoded) * 255) / 255
decoded = (2^(quantized * log2(1 + R*K)) - 1) / K
~~~

`R` 必须随纹理写入 metadata；运行时不能假定所有白天、黄昏和夜间共用固定范围 8。夜间独立拟合较小范围，能把更多 8-bit 码值分给暗部渐变。若 `observedMaximum > 32`，PNG 会裁切极端值，应降低不合理的 HDR 强度或保留 EXR/改用更高精度发布格式，不能只调曝光隐藏裁切。

PNG 导入断言：

| 项目 | 必须值 | 原因 |
|---|---|---|
| Texture Type | Default | 它是自定义数据纹理，不是普通颜色贴图或 Sprite |
| sRGB | Off | Log 编码必须在线性数值上解码，不能再经过 sRGB 转换 |
| Alpha Source | From Input | 纯静态 LogRGB 不赋予 A 事件语义；启用瞬态响应时，基础 LogRGBA 的 A 保存第一个固定单元的最终标量响应，不能当透明度或共享 HDR 倍率 |
| Alpha Is Transparency | Off | 禁止透明边缘颜色处理 |
| Mip Maps | On | 降低远处/低分辨率采样闪烁 |
| Wrap Mode | Clamp | 正方形四边是地平线，不允许普通 Repeat 跨边混合 |
| Filter Mode | Trilinear | 平滑 Mip 过渡 |
| Editor 压缩 | Uncompressed | 作为编码真值，便于区分 8-bit 量化和平台块压缩 |
| Android | ASTC 4×4，质量 100 | 当前移动发布约定；仍需目标设备复核 |
| Read/Write | Off | 写入和 metadata 完成后关闭 CPU 读取 |

metadata 至少保存：schema 版本、`skyHdrRange`、`skyLogCurve`、RGB 线性最大值、地平线颜色和地面颜色。测试场景或材质生成器必须从 importer metadata 读取实际范围；解析失败时可以使用明确的兼容默认值，但要报警，不能静默把夜间纹理按白天范围解码。

##### 动态瓦片策略与 TDR 边界

瓦片大小不是画质参数。当前 Runner 按一次片元内部的最坏嵌套工作量选择提交粒度：

~~~text
solarShadowWork = 128                  # 低太阳角的 Shader 上限
perViewStep = 7 + solarShadowWork      # 静态 Base：密度/环境近似 + 太阳遮光
perPixelWork = samplesPerPixel * viewSteps * perViewStep

perPixelWork <= 160000  → 32×32
perPixelWork <= 640000  → 16×16
otherwise               → 8×8
~~~

这只是保守的 TDR 风险分档，不是总耗时预测，也不保证任何极端参数绝不触发设备重置。每个瓦片必须使用整图 UV、整图纹素坐标和相同参数；若瓦片边界可见，优先检查 `_BakeUvScaleOffset`、全局随机种子和最后一行/列的非整瓦片尺寸，不要改云噪声掩盖拼接错误。

##### Staging、分帧限载与最终回读

当前主路径保持短瓦片 Draw，但不再让 CPU 对每个瓦片执行同步 `ReadPixels`：

1. 每个瓦片先渲染到短生命周期 `ARGBHalf` RenderTexture。
2. 用 `CopyTexture` 把瓦片复制到全尺寸、同格式的 staging RT；这一步不扩大单个 Draw 的体积积分工作量。
3. 交互模式每批只提交少量瓦片。Background / Balanced / Full Speed 分别以 1 / 2 / 8 个瓦片为一批，目标占空约为 25% / 45% / 100%。
4. 支持异步计算的平台用 `GraphicsFence`；不支持异步计算但支持异步回读的平台，请求 staging 的一个小区域作为 CPU 可见完成信号。该小区域只承担栅栏职责，不是最终像素来源。
5. 所有瓦片完成后，对全尺寸 staging 只做一次完整 `ReadPixels`，再统一 `Apply(false, false)`。
6. 平台不支持区域复制、staging 创建失败或完成信号不可用时，才回退逐瓦片同步读回。

分帧会话支持暂停、恢复和取消。暂停表示不再提交新的 GPU 批次，已经提交的工作仍需正常完成；取消必须释放临时 RT、异步请求和未发布的输出。限载与异步回读改善的是编辑器可响应性和 CPU/GPU 强制同步，不会减少体积积分总量，也不能把单次高质量任务变成实时算法。

当前一个 512 厚云配置使用 32×32 瓦片、每 Pass 256 个 Draw、Balanced 45% 目标占空并完成最终单次读回；这是本机单次配置证据，不是跨设备耗时基准，也不代表当前 1024 已通过。

##### 线性传输缓存与失效边界

缓存保存的是“完整三维程序云积分得到的二维方向线性 Half 传输”，而不是可任意查询的三维云体，也不是运行时已经 Tone Map 的普通颜色截图。静态 Base RGB 与每个瞬态标量槽独立存储；缓存未命中时仍会重新查询完整的球壳、程序噪声、密度和光照。这样可以复用特定视点、天气、光照和单元参数下的昂贵积分，但不能从缓存反推出云密度或零成本支持新的三维光源位置。

缓存键应至少包含 Unity/图形平台/色彩空间、烘焙 Shader 与 Runner 依赖指纹、分辨率、云层几何与密度、太阳/环境光、质量参数。基础 Base 键有意排除瞬态单元、输出文件名和 Log 编码；因此只改输出名、编码 Range/Curve 或 EXR 开关时可直接复用线性结果。参数不变时全命中可以是 0 个 GPU Pass，但仍需扫描峰值、重新编码、导入和写 metadata。

需要区分“参数依赖拆分”和“代码依赖失效”：只改某个瞬态单元参数时，可以只重算该标量；只改太阳参数时，可以只重算 Base。但 Bake Shader 或 Runner 源码变化会通过依赖指纹保守地使相关缓存失效，即使修改看起来只属于某一分支。缓存 payload 写入前还必须完成整图回读、有限值检查、Header/SHA 校验，并通过临时文件原子替换，避免取消或崩溃留下可误命中的半成品。

##### 运行时天空绑定

运行时 Shader 对方向 `direction` 执行：

1. 若 `direction.y < 0`，直接在地平线色和地面色之间插值，不采上半球纹理。
2. 否则把方向投影到半八面体 UV，采样 `_SkyTexture` 一次。
3. 用该纹理 metadata 的 `skyHdrRange` 和 `skyLogCurve` 解码 RGB。
4. 在解码后的线性 HDR 上执行曝光、Tone Mapping 和低幅度最终输出 Dither。

VR 左右眼共享同一纹理和同一材质参数，但每眼仍通过 Unity stereo 宏得到自己的天空方向。顶点/片元入口至少包含 `UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO` 与 `UNITY_SETUP_STEREO_EYE_INDEX_POST_VERTEX`；“共享纹理”不等于复用单眼片元结果。

Tone Mapping 不是烘焙正确性的组成部分。先用 None/线性调试查看 EXR/解码真值，再比较 ACES 和风格化映射。只有线性真值正确时，才处理“更卡通”的色调压缩；否则 Tone Mapping 会把错误压暗或把量化台阶变得更显眼。

##### 材质复用：纹理与 metadata 必须原子同步

天空材质可以跨场景复用，纹理也不与某个场景永久绑定；真正的约束是“一张烘焙纹理及其 metadata 必须作为完整合同绑定”。除了 `_SkyTexture`，材质还需要同步：

- 天空的 HDR Range 与 Log Curve；
- 若存在附加瞬态纹理，则包括其 HDR Range、Log Curve、配对引用、有效通道数与中心方向；
- 地平线颜色与下半球颜色。

这些字段属于数据解码合同，不是曝光或美术滑杆。若只在普通材质 Inspector 中把白天天空换成夜间纹理，旧的隐藏 Range/Curve 仍会参与解码，夜景可能在 Tone Mapping 前被放大数十倍。把另一份正常材质的全部参数复制过来之所以能恢复，通常只是顺带复制了正确的隐藏合同，并不说明天空盒与场景绑定。

推荐让自定义材质 Inspector 在纹理变更时先解析 importer `userData`，校验 schema 和配对资源，再用一次 Undo 操作原子同步全部隐藏字段；如果 metadata 缺失、无效或配对资源丢失，应拒绝替换并显示错误。曝光、Tone Mapping、饱和度、闪电颜色和动画状态仍属于美术/运行时参数，不应被天气 metadata 静默覆盖。

##### 测试场景与截图矩阵

最小验收场景包含：

- 一台 HDR Camera，Clear Flags/Skybox 正确，初始位置代表烘焙观察点。
- 一份只引用本次输出的天空材质；不要让旧材质、全局 Volume、Bloom、自动曝光或 TAA 干扰第一次验收。
- 一个可选的 Directional Light 参考物体，其方向仅用于对照烘焙太阳；运行时云光已经写进纹理，不靠它重新照亮云。
- 一个地面/标尺参考，帮助判断地平线与旋转，但不能遮住天空主要区域。

建议每个时间段保存以下矩阵：

| 方向 | None/线性 | ACES | 风格化 | 主要观察点 |
|---|---:|---:|---:|---|
| 迎光中心 | 必须 | 必须 | 必须 | 太阳尺寸、剪白、云边高光肩部 |
| 左/右各约 90° | 必须 | 可选 | 必须 | 侧光体积、噪声重复、瓦片缝 |
| 背光 | 必须 | 可选 | 必须 | 环境光层次、死黑和厚云暗部 |
| 天顶 | 必须 | 必须 | 必须 | 渐变色带、子样本噪点、映射中心 |
| 四个地平线象限 | 必须 | 可选 | 必须 | 半八面体四边连续、远端截断、黑块 |

白天通过不能替代黄昏和夜间；不同 Tone Mapping 也不能互相替代。检查“异常黑块”时必须同时看线性/None 与最终映射：线性已经为黑说明烘焙/解码问题，只有最终映射为黑才进入曝光、曲线和颜色分级排查。

##### 复现记录模板

每次声称某个档位“通过”时，至少记录：

~~~text
Unity / Render Pipeline / Graphics API:
参数资产或参数快照：
输出分辨率、viewSteps、lightSteps、maximumLightStepLength、spp：
实际瓦片大小与 Draw 数：
烘焙耗时：
PNG / EXR 文件名与 SHA-256：
Importer：Linear / Mip / Clamp / Filter / 平台格式：
metadata：schema / skyHdrRange / skyLogCurve / skyLinearMax：
截图：迎光 / 左 / 右 / 背光 / 天顶 / 地平线四象限：
Console 编译错误、警告和设备重置：
结论：通过 / 失败；失败发生在求解、映射、编码、导入、解码还是 Tone Mapping：
~~~

该模板的目的不是堆日志，而是保证另一个人能知道“输入是什么、输出是哪一份、经过什么解码、看过哪些角度”。没有参数快照和输出身份的截图，不能作为可复现证据。

##### 常见失败的最短定位路径

| 现象 | 先检查 | 不要先做 |
|---|---|---|
| 整张纯黑 | Bake Shader 是否找到、球壳是否有有效区间、HDR 母图最大值 | 提高 Tone Mapping 曝光 |
| 只有背景无云 | `coverage`、高度剖面、密度灰度调试、相机是否低于云底 | 只提高 `densityMultiplier` |
| 云覆盖太少 | `coverage` 与 `coverageVariation` | 把云密度调得更黑 |
| 云像竖墙/条纹 | 局部高度坐标、Y 频率、viewSteps 与首步 jitter | 用屏幕模糊 |
| 地平线被截断 | `maximumMarchDistance`、球壳求交、方向是否先命中行星 | 只提高分辨率 |
| 太阳附近过曝 | EXR 峰值、`sunColor`、前向散射、太阳角半径、Tone Mapping 肩部 | 关闭 HDR 或把所有颜色压到 0～1 |
| 黄昏/夜间黑块 | EXR → PNG → None → 最终映射逐层对照；检查 NaN/负值和 metadata range | 直接抬亮环境光掩盖 |
| 平滑天空出现色阶 | EXR 是否平滑、Log 范围是否过大、sRGB 是否关闭、最终输出位深/Dither | 增加云光照分层 |
| 正方形内出现直线缝 | 全局 UV、全局随机种子、最后一块尺寸和纹理写入偏移 | 改噪声 offset 碰运气 |
| Unity/GPU 无响应 | Console 的实际瓦片、单片元工作量、是否设备已 reset | 在同一故障进程继续最高质量重试 |

##### 文档复现边界

本 SOP 的 Inspector 顺序、菜单、开关、按钮、输出命名、编码范围、导入设置和运行时解码均已对照当前源码；当前 32/16/8 动态瓦片、staging 和分帧会话已经完成一个厚云配置的 512 实际烘焙与多视角检查，但该证据不能外推到其他天气、质量参数或 1024。本文允许使用现有模块的人建立独立静态烘焙闭环，也给出了从零实现时不可缺失的组件、公式、顺序和验收门禁。

仍需明确：当前没有在一份全新的空白 Unity 工程中，仅凭本文重新手写全部样板代码并做第二次独立验收。因此已验证的是核心链路和已留证的具体实现快照；“当前源码的所有 512 配置或 1024 已通过”以及“任意 Unity 版本的空白工程复制后必然一次编译通过”都不在已验证范围。复现到其他版本时，应把编译差异和改动写入验证记录，而不是扩大本文的适用版本声明。

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

##### 4-lobe 经验多重散射补偿

当前代码不是严格路径追踪，而是累加 4 个逐渐变宽、能量逐渐降低的相位叶：

~~~text
energy₀ = 1
transmittance₀ = Tlight
g₀ = userG

每个经验 lobe：
scatter += DualPhase(μ, g) * transmittance * energy
energy *= 0.52 * multipleScatteringStrength
transmittance = transmittance^0.62
g *= 0.55
~~~

它能恢复厚云内部被单次散射丢失的柔和能量，但不能当作物理准确的第四次散射解。代码中的 0.52、0.62、0.55 和直射光整体倍率均是经验参数。

##### 环境光与 Powder

环境光根据云样本归一化高度在 0.32～0.68 之间插值，再乘用户的环境云颜色。当前实现没有单独的地面反弹光项。虽然烘焙参数会把 groundColor 传给 Shader，但半八面体烘焙方向不会低于地平线，所以该值目前不影响发布的上半球纹理；运行时下半球使用天空材质自己的 GroundColor。

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
glowRadius = max(independentGlowRadius, 0.001°)
glow = exp2(-(sunAngle / glowRadius)²) * 0.12
~~~

`sunAngularRadiusDegrees = 0.27°` 约等于真实太阳角半径；提高到 0.5°～2° 可获得卡通化大太阳。圆盘半径与外围光晕角半径是两个独立参数：放大圆盘不会自动扩大已经校准的柔光，光晕设为 0 时完全关闭。这样既能解决 Game 视图中真实角半径只有数像素、看起来像亮点的问题，也不会为了让圆盘可读而把半个天空一起变亮。

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

##### 当前瓦片实现与证据边界

- 每块临时 RenderTexture 使用 ARGBHalf、Linear。
- CPU 汇总纹理使用 RGBAHalf。
- BakeUvScaleOffset 把瓦片局部 UV 还原到整图 UV。
- 随机种子使用整图像素坐标，而不是瓦片局部坐标。
- 主路径把每块复制到全尺寸 staging，整个 Pass 最终只完整读回一次；不支持时才逐块回读。
- 所有瓦片共用完全相同的云、太阳和曝光参数。

当前 Runner 按单片元嵌套工作量在 32×32、16×16、8×8 中动态选择瓦片，阈值分别为 160000 和 640000；静态 Base 按低太阳角可能达到的 128 遮光步做保守估算。当前短瓦片、staging 与交互会话已完成一个 512 厚云配置的实际执行和多视角检查；固定 128×128 瓦片阶段的 1024 仍只能保留为历史参照，不能证明当前代码已通过 1024。

短瓦片只降低一次 Draw 触发 Windows TDR 的概率，不保证极端参数永不超时，也不改变总工作量。这个结论只针对一次提交的风险模型，并不否定其他降低 GPU 超时风险的方法。如果瓦片使用局部 UV 或局部随机种子，仍会在边界出现方向断裂、噪声重复或采样相位跳变。

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
| 冒烟/构图 | 128～256 | 64～96 | 8～10 | 1 | 云量、噪声、太阳位置和链路检查 |
| 正式判断 | 512 | 128 | 12 | 2 | 多视角、接缝、色带与异常黑块；当前已有一个厚云配置通过执行门禁，新配置仍需独立验收 |
| 高质量候选 | 1024 | 192 | 20～24 | 4 | 历史固定瓦片阶段已有实践结果；当前动态瓦片需要独立重验 |
| 更高候选 | 2048 | 256～384 | 24～32 | 4～8 | 仅在前一级确有不足且设备预算允许时评估 |

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
- 在记录的目标机器上，所选正式质量档完成且未发生设备重置；同时记录瓦片尺寸、总耗时和图形 API。历史实现成功不能替代当前瓦片代码的回归。
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
- 动态云影、场景局部光和任意运行时天气变化不在本记录范围内；需要这些能力时应采用实时或半实时体积云方案。
- 线性传输缓存不保存可任意查询的全局三维云体，也不能支持未包含在键中的新视点或新光照；缓存 miss 仍执行完整程序云积分。
- 当前短瓦片、staging 和分帧会话只有已记录配置的 512 实践证据；当前实现的 1024 仍需在对应 512 通过后独立重验。
- Quest 真机 ASTC RGB 误差、双眼天空方向、构建变体和单次采样 GPU 成本仍需目标设备验证。

### 关键代码

以下片段是静态-only 最小实现中跨文件最容易不一致的部分。字段、常数和函数名可以重命名，但 CPU 编码与 GPU 解码、Bake 逆映射与 Runtime 正映射、全图 UV 与瓦片 UV 的数学必须成对一致。

#### 半八面体正反映射

```hlsl
// Bake：正方形 UV -> 上半球方向。中心为天顶，四条边为地平线。
float3 HemiOctahedralDirection(float2 uv)
{
    float2 square = uv * 2.0 - 1.0;
    float2 diamond = 0.5 * float2(
        square.x + square.y,
        square.x - square.y);
    float y = max(0.0, 1.0 - abs(diamond.x) - abs(diamond.y));
    return normalize(float3(diamond.x, y, diamond.y));
}

// Runtime：上半球方向 -> 正方形 UV。与上式互为同一坐标约定。
float2 EncodeHemiOctahedron(float3 direction)
{
    direction.y = max(direction.y, 0.0);
    float invL1 = rcp(max(
        abs(direction.x) + direction.y + abs(direction.z),
        1e-5));
    float2 diamond = direction.xz * invL1;
    float2 square = float2(
        diamond.x + diamond.y,
        diamond.x - diamond.y);
    return square * 0.5 + 0.5;
}
```

最小单元测试应验证：`uv=(0.5,0.5)` 得到天顶；四边中点分别得到四个水平轴；对一组归一化上半球方向执行 `Direction(Encode(d))`，夹角误差应接近浮点误差。若要旋转天空，应在编码前绕世界 Y 轴旋转方向，不能旋转正方形 UV。

#### 程序化密度参考实现

```hlsl
float3 Hash33(float3 value)
{
    value = frac(value * float3(0.1031, 0.1030, 0.0973));
    value += dot(value, value.yxz + 33.33);
    return frac((value.xxy + value.yxx) * value.zyx);
}

float GradientNoise(float3 position)
{
    float3 cell = floor(position);
    float3 local = frac(position);
    float3 blend = local * local * local *
        (local * (local * 6.0 - 15.0) + 10.0);
    float values[8];

    [unroll]
    for (int corner = 0; corner < 8; corner++)
    {
        float3 offset = float3(
            corner & 1,
            (corner >> 1) & 1,
            (corner >> 2) & 1);
        float3 gradient = normalize(
            Hash33(cell + offset) * 2.0 - 1.0 + 1e-4);
        values[corner] = dot(gradient, local - offset);
    }

    float x00 = lerp(values[0], values[1], blend.x);
    float x10 = lerp(values[2], values[3], blend.x);
    float x01 = lerp(values[4], values[5], blend.x);
    float x11 = lerp(values[6], values[7], blend.x);
    float y0 = lerp(x00, x10, blend.y);
    float y1 = lerp(x01, x11, blend.y);
    return saturate(lerp(y0, y1, blend.z) * 0.85 + 0.5);
}

float Fbm(float3 position, int octaveCount)
{
    float result = 0.0;
    float amplitude = 0.5;
    float totalAmplitude = 0.0;
    float3 octavePosition = position;

    [unroll]
    for (int octave = 0; octave < 5; octave++)
    {
        if (octave >= octaveCount) break;
        result += GradientNoise(octavePosition) * amplitude;
        totalAmplitude += amplitude;
        octavePosition = octavePosition * 2.03 + float3(13.7, 7.1, 19.3);
        amplitude *= 0.5;
    }
    return result / max(totalAmplitude, 1e-4);
}

float WorleyF1(float3 position)
{
    float3 baseCell = floor(position);
    float3 local = frac(position);
    float minimumDistanceSquared = 10.0;

    [unroll]
    for (int z = -1; z <= 1; z++)
    [unroll]
    for (int y = -1; y <= 1; y++)
    [unroll]
    for (int x = -1; x <= 1; x++)
    {
        float3 neighbor = float3(x, y, z);
        float3 featurePoint = neighbor + Hash33(baseCell + neighbor);
        float3 delta = featurePoint - local;
        minimumDistanceSquared = min(
            minimumDistanceSquared,
            dot(delta, delta));
    }
    return saturate(sqrt(minimumDistanceSquared));
}

float HeightProfile(float h)
{
    float baseRise = smoothstep(0.0, 0.12, h);
    float topFalloff = 1.0 - smoothstep(0.62, 1.0, h);
    return saturate(baseRise * topFalloff);
}

float SampleDensity(float3 worldPosition, bool includeDetail)
{
    float radialHeight = length(worldPosition) -
        (_PlanetRadius + _CloudBottomAltitude);
    float thickness = _CloudTopAltitude - _CloudBottomAltitude;
    float h = radialHeight / max(thickness, 1e-3);
    if (h <= 0.0 || h >= 1.0) return 0.0;

    // 避免把约 6371 km 的行星半径直接送入噪声。
    float3 localPosition = float3(
        worldPosition.x,
        radialHeight + _CloudBottomAltitude,
        worldPosition.z) + _NoiseOffset;

    float3 basePosition = localPosition * _BaseNoiseScale;
    basePosition.y *= 3.25;
    float perlin = Fbm(basePosition, 4);
    float worley = 1.0 - WorleyF1(basePosition * 0.72 + 11.7);
    float perlinWorley = saturate(lerp(
        perlin,
        lerp(worley, 1.0, perlin),
        0.32));

    float weather = Fbm(
        float3(localPosition.x, 0.0, localPosition.z) * 0.012 + 37.0,
        3);
    float localCoverage = saturate(
        _Coverage + (weather - 0.5) * _CoverageVariation);
    float density = saturate(
        (perlinWorley - (1.0 - localCoverage)) /
        max(localCoverage, 0.04));
    density *= HeightProfile(h);

    if (includeDetail && density > 0.001)
    {
        float3 detailPosition = localPosition * _DetailNoiseScale + 73.1;
        detailPosition.y *= 1.8;
        float detail = Fbm(detailPosition, 3);
        float edgeWeight = saturate(1.0 - density);
        density = saturate(
            density - (1.0 - detail) * _DetailErosion *
            (0.35 + edgeWeight));
    }
    return density;
}
```

#### 球壳区间与前向积分

```hlsl
float RaySphereNear(float3 origin, float3 direction, float radius)
{
    float b = dot(origin, direction);
    float c = dot(origin, origin) - radius * radius;
    float discriminant = b * b - c;
    return discriminant >= 0.0 ? -b - sqrt(discriminant) : -1.0;
}

float RaySphereFar(float3 origin, float3 direction, float radius)
{
    float b = dot(origin, direction);
    float c = dot(origin, origin) - radius * radius;
    float discriminant = b * b - c;
    return discriminant >= 0.0 ? -b + sqrt(discriminant) : -1.0;
}

bool GetCloudSegment(
    float3 origin,
    float3 direction,
    out float startDistance,
    out float endDistance)
{
    float bottomRadius = _PlanetRadius + _CloudBottomAltitude;
    float topRadius = _PlanetRadius + _CloudTopAltitude;
    startDistance = RaySphereFar(origin, direction, bottomRadius);
    endDistance = RaySphereFar(origin, direction, topRadius);
    if (startDistance < 0.0 || endDistance <= startDistance) return false;

    float planetHit = RaySphereNear(origin, direction, _PlanetRadius);
    if (planetHit > 0.0 && planetHit < startDistance) return false;

    startDistance = max(0.0, startDistance);
    endDistance = min(
        endDistance,
        startDistance + _MaximumMarchDistance);
    return endDistance > startDistance;
}

float3 IntegrateStaticCloud(
    float3 origin,
    float3 direction,
    float jitter,
    out float transmittance)
{
    float startDistance;
    float endDistance;
    transmittance = 1.0;
    if (!GetCloudSegment(
            origin,
            direction,
            startDistance,
            endDistance))
        return 0.0;

    float ds = (endDistance - startDistance) /
        max((float)_ViewSteps, 1.0);
    float distanceAlongRay = startDistance + ds * jitter;
    float3 accumulatedLight = 0.0;
    float cosineTheta = dot(direction, _SunDirection);

    [loop]
    for (int i = 0; i < MAX_VIEW_STEPS; i++)
    {
        if (i >= _ViewSteps || transmittance < 0.002) break;
        float3 position = origin + direction * distanceAlongRay;
        float density = SampleDensity(position, true);
        if (density > 0.001)
        {
            float sigmaT = density * _DensityMultiplier;
            float stepT = exp(-sigmaT * ds);
            float alpha = 1.0 - stepT;
            float powder = 1.0 - exp(-sigmaT * ds * 2.0);
            float powderFactor = lerp(
                1.0,
                max(0.25, powder * 2.0),
                _PowderStrength);

            float lightT = LightTransmittance(position);
            float3 direct = _SunColor.rgb *
                MultipleScatteringLighting(lightT, cosineTheta) * 3.5;

            float radialHeight = length(position) -
                (_PlanetRadius + _CloudBottomAltitude);
            float h = saturate(radialHeight /
                (_CloudTopAltitude - _CloudBottomAltitude));
            float ambientVisibility = AmbientSkyVisibility(position);
            float ambientHeight = lerp(0.32, 0.68, h);
            float ambientDiffusion = lerp(
                0.72,
                1.0,
                sqrt(saturate(ambientVisibility)));
            float3 ambient = _AmbientCloudColor.rgb *
                ambientHeight * ambientDiffusion;

            accumulatedLight += transmittance *
                (direct * powderFactor + ambient) * alpha;
            transmittance *= stepT;
        }
        distanceAlongRay += ds;
    }
    return accumulatedLight;
}
```

`LightTransmittance`、`AmbientSkyVisibility` 和 `MultipleScatteringLighting` 的完整数学与常数见前文“光照模型”。实现时要保留两个关键边界：太阳射线先命中行星时返回 0；阴影步数按最大物理步长自适应并限制在 Shader 上限内。环境光是独立低频项，不能把被行星遮挡的直射太阳强行设为非零。

#### CPU LogRGB 编码与 GPU 解码

```csharp
static byte EncodeLogChannel(float linear, float range, float curve)
{
    float safe = Mathf.Clamp(linear, 0.0f, range);
    float logRange = Mathf.Log(1.0f + range * curve, 2.0f);
    float encoded = Mathf.Log(1.0f + safe * curve, 2.0f) / logRange;
    return (byte)Mathf.Clamp(
        Mathf.RoundToInt(Mathf.Clamp01(encoded) * 255.0f),
        0,
        255);
}

static float FitSkyRange(Color[] pixels)
{
    float maximum = 0.0f;
    foreach (Color p in pixels)
        maximum = Mathf.Max(maximum, p.r, p.g, p.b);
    return Mathf.Clamp(
        Mathf.Max(0.0625f, maximum * 1.10f),
        0.0625f,
        32.0f);
}
```

```hlsl
float DecodeLogChannel(float encoded, float range, float curve)
{
    float logRange = log2(1.0 + range * curve);
    return (exp2(encoded * logRange) - 1.0) / curve;
}

float3 DecodeLogRgb(float3 encoded, float range, float curve)
{
    return float3(
        DecodeLogChannel(encoded.r, range, curve),
        DecodeLogChannel(encoded.g, range, curve),
        DecodeLogChannel(encoded.b, range, curve));
}
```

编码后应在 CPU 立即做一次 8-bit round-trip 测试：对 0、暗部代表值、1、接近范围上限和超过范围的值分别编码/解码，确认单调、非负、上限裁切符合预期。不要用 `Color32` 的 sRGB 语义做额外转换；这里的 byte 是自定义数值编码。

#### 动态瓦片与导入设置

下面的 `ResolveTileSize` 对应当前动态短瓦片实现。当前已有一个厚云配置的 512 执行证据，但这不是 1024 或任意参数组合已通过的证明。导入设置属于另一条数据契约，应分别验证，不能因为 importer 正确就推导瓦片渲染正确。

```csharp
static int ResolveTileSize(int samplesPerPixel, int viewSteps)
{
    long perPixelWork =
        (long)Mathf.Max(samplesPerPixel, 1) *
        Mathf.Max(viewSteps, 1) *
        (7 + 128); // 静态 Base 的保守最坏太阳遮光预算
    if (perPixelWork <= 160000) return 32;
    return perPixelWork <= 640000 ? 16 : 8;
}

static void ConfigureRuntimeTexture(
    string assetPath,
    int resolution,
    string metadataJson)
{
    var importer = (TextureImporter)AssetImporter.GetAtPath(assetPath);
    importer.textureType = TextureImporterType.Default;
    importer.sRGBTexture = false;
    importer.alphaSource = TextureImporterAlphaSource.FromInput;
    importer.alphaIsTransparency = false;
    importer.mipmapEnabled = true;
    importer.streamingMipmaps = false;
    importer.wrapMode = TextureWrapMode.Clamp;
    importer.filterMode = FilterMode.Trilinear;
    importer.textureCompression = TextureImporterCompression.Uncompressed;
    importer.isReadable = false;
    importer.maxTextureSize = Mathf.Clamp(
        Mathf.NextPowerOfTwo(resolution),
        32,
        4096);

    var android = importer.GetPlatformTextureSettings("Android");
    android.name = "Android";
    android.overridden = true;
    android.maxTextureSize = importer.maxTextureSize;
    android.format = TextureImporterFormat.ASTC_4x4;
    android.compressionQuality = 100;
    importer.SetPlatformTextureSettings(android);
    importer.userData = metadataJson;
    importer.SaveAndReimport();
}
```

每个瓦片渲染前设置 `(tileWidth/fullResolution, tileHeight/fullResolution, pixelX/fullResolution, pixelY/fullResolution)` 形式的 `_BakeUvScaleOffset`。Bake Shader 用 `globalUv = input.uv * scale + offset` 求方向和整图随机种子；主路径把瓦片用 `CopyTexture` 写入 staging 的全局像素位置，批次间用 Fence 或小区域异步回读等待，所有瓦片结束后才对 staging 完整 `ReadPixels` 一次。只有 fallback 才使用 `ReadPixels(sourceRect, pixelX, pixelY, false)` 逐瓦片写入。

~~~text
for each tile:
    Blit(tileMaterial → tileARGBHalf)
    CopyTexture(tileARGBHalf → fullSizeStaging, globalPixelOffset)
after each interactive batch:
    wait GraphicsFence or tiny AsyncGPUReadback fence
after all tiles in pass:
    ReadPixels(fullSizeStaging → RGBAHalf CPU texture) once
~~~

### 参考链接

- [The Real-time Volumetric Cloudscapes of Horizon: Zero Dawn](https://advances.realtimerendering.com/s2015/The%20Real-time%20Volumetric%20Cloudscapes%20of%20Horizon%20-%20Zero%20Dawn%20-%20ARTR.pdf) - Perlin–Worley 云密度与实时体积云基础。
- [Nubis: Authoring Real-Time Volumetric Cloudscapes with the Decima Engine](https://www.guerrilla-games.com/read/nubis-authoring-real-time-volumetric-cloudscapes-with-the-decima-engine) - 云层创作与天气控制。
- [SIGGRAPH 2016 Course: Physically Based Shading in Theory and Practice](https://blog.selfshadow.com/publications/s2016-shading-course/) - Frostbite《Physically Based Sky, Atmosphere and Cloud Rendering》课程入口及原始演示文稿。
- [Unity Volumetric Clouds Volume Override reference](https://github.com/Unity-Technologies/Graphics/blob/master/Packages/com.unity.render-pipelines.high-definition/Documentation~/volumetric-clouds-volume-override-reference.md) - Cloud Map/LUT 通道打包和数据纹理关闭 sRGB 的官方参考。
- [Arm ASTC Format Overview](https://github.com/ARM-software/astc-encoder/blob/main/Docs/FormatOverview.md) - 128-bit 固定块、通道共享权重与 dual-plane 边界。

### 相关记录

- [WebGL2 体积云的统一积分后端：从实时预览到渐进收敛与离线烘焙](./webgl2-unified-volumetric-cloud-rendering.md) - 另一套实现中预览/烘焙 KernelSet 统一、3-lobe 经验多重散射补偿、浏览器冷编译、渐进累计和地平线分层的纠错记录。
- [半八面体单图 HDR 天空的编码、采样与色带治理](./hemi-octahedral-hdr-sky-texture.md) - HDR 母图之后的方向布局、编码、导入和发布链路。
- [色带（Color Banding）与抖动（Dithering）知识](./color-banding-dither.md) - 静态天空平滑渐变的输出量化问题。
- [URP 天空盒 Shader 机制与常见问题](./urp-skybox-notes.md) - Unity 天空盒渲染路径注意事项。
- [VR 静态云天空与动态闪电的分离合成](./vr-static-sky-lightning-compositing.md) - 静态天空完成后的瞬态照明、传输响应、运行时时序与双眼路径；相关内容不在本文展开。

### 验证记录

- [2026-07-27] 在 Unity 编辑器中完成 512×512、192 视线步、24 光照步、4 子样本的瓦片化烘焙，并从迎光、侧光、背光、天顶四个方向检查；高负载单 Draw 曾触发编辑器/GPU 故障，改为 128×128 瓦片后稳定完成。
- [2026-07-28] 原理与实现过程扩写：按当前 Shader/C# 实现补齐球壳求交、密度公式、光照积分、多重散射近似、子像素采样、瓦片化、成本模型、参数关系、失败诊断和实现限制。明确公开资料是理论参照，当前程序化噪声与经验常数属于项目实现。
- [2026-07-28] 参数语义复核：确认固定视线步数下，增大最大步进距离主要会增大单步长度而非循环次数；确认 groundColor 当前不会进入上半球烘焙结果，也不是云底反弹光参数，已在正文标明。
- [2026-07-28] 来源性复核：原 EA Frostbite PDF 直链返回 404，改用可访问的 SIGGRAPH 2016 课程索引；该页面仍提供 Frostbite 原始演示文稿。
- [2026-07-28] 1024 静态链路闭环：完成 1024×1024、192 视线步、20 太阳光步、4 子样本的正式静态云烘焙；LogRGB 编码、基础纹理导入和运行时解码均通过 Unity 检查。
- [2026-07-30] 完整性、时效性与结构一致性复核：补入复现完成条件、环境边界、最小文件职责、字段语义、从零实现顺序、白天/黄昏/夜间参数、分级质量门槛、Unity 操作、输出/LogRGB/Importer/metadata 契约、运行时单采样与 VR stereo 要求、截图矩阵、复现记录模板和失败定位；记录边界严格收窄为静态体积云，空白工程完全重写仍列为未独立验证。
- [2026-07-30] 当前工具流程复核：以当前 `Settings Inspector → Baker Window → Runner → Bake Shader → LogRGB/EXR → 时间戳对照场景` 为唯一操作主线，校准菜单、开关、按钮、天气/时段预设、太阳方向与角半径、输出命名和动态瓦片职责。32/16/8 动态瓦片目前只有 48² 低负载连续性证据；历史固定瓦片阶段的 512/1024 结果只作参照，不写成当前源码已经通过，也不把当前未验证范围外推为同类算法的普遍限制。
- [2026-07-31] 正确性、时效性与结构一致性更新：当前 32/16/8 短瓦片已改为全尺寸 staging 主路径，每个 Pass 最终只完整回读一次；编辑器分帧会话支持 Background/Balanced/Full Speed 限载、暂停/恢复/取消，以及 GraphicsFence 或小区域 AsyncGPUReadback 完成信号。一个当前厚云配置完成 512 实际烘焙和多视角检查，证明该配置的 512 提交与回读链路成立，但不外推为 1024 或所有天气已通过。
- [2026-07-31] 缓存与材质合同更新：新增 Base RGB 与逐单元线性 Half 传输缓存，明确它复用完整三维积分结果而非从二维颜色反推云数据；补充参数级失效、源码依赖指纹、有限值/SHA 校验和原子提交边界。修正基础 Alpha 语义：纯静态 LogRGB 不赋予 A 事件语义，启用瞬态响应时 Base A 保存固定单元标量。记录“只换纹理会保留旧隐藏 Log 解码参数并导致夜景异常过亮”的根因，明确纹理、metadata、配对资源与地平线颜色必须原子同步。当前 1024、目标设备 ASTC、双眼与 GPU 抓帧仍待验证。
- [2026-08-11] 跨实现边界纠错：新增 WebGL2 统一体积云论文链接，明确本记录使用 4 个经验补偿 lobe，而不是严格第四次物理散射；Unity 动态短瓦片也是具体工具实现，不是通用固定算法。补充瓦片必须保持 full resolution、global pixel/UV 与全局样本序列；性能调度不得通过局部坐标重置或静默降低正式采样预算来换取稳定。

---

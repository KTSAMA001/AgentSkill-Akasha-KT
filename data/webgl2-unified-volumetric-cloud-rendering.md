# WebGL2 体积云的统一积分后端：从实时预览到渐进收敛与离线烘焙

**标签**：#graphics #shader #rendering #skybox #experience
**来源**：单文件 WebGL2 体积云原型现存 R6.2、R6.3、R6.6、R6.10、R6.11、R6.13、R6.19～R6.24 固定快照与源码差分，辅以 Chromium 浏览器运行、渐进预览和正式烘焙实测
**收录日期**：2026-08-11
**来源日期**：2026-08-03～2026-08-11
**更新日期**：2026-08-11
**状态**：⚠️ 待验证
**可信度**：⭐⭐⭐⭐（统一 KernelSet、渐进累计和无浮点混合 SPP 保真已有源码与浏览器证据；地平线根因与修正有源码证据但用户侧视觉验收未闭环；R6.4～R6.5、R6.7～R6.9、R6.12、R6.14～R6.18 缺少可信固定快照，真实 Edge file:// 冷启动、多 GPU/驱动和高分辨率正式烘焙仍待完整回归）
**适用版本**：WebGL2 / GLSL ES 3.00；Chromium 系浏览器；实现基线为 R6.24 Full-Exact Split KernelSet

### 概要

高质量体积云在 Web 端最危险的优化，不是“算得太慢”，而是为了尽快看到画面而悄悄换掉了求解器：实时预览使用 Minimal，渐进预览使用 Compat，正式烘焙再使用 Full。三条路径即使共享同一组 UI 参数，也会因为密度、遮蔽、相位、多重散射和环境光公式不同而得到不同的天空。

本文记录一条经过多次失败才收敛的工程路线：把预览、渐进和烘焙约束为同一个不可变 Canonical KernelSet，所有正式结果共享同一密度函数、光照源项、云—空气传输、低差异样本序列与最终质量预算；性能差异只允许来自 RenderPlan，例如分辨率、瓦片、分帧调度和显示策略。复杂单体 Shader 不再以非等价 Compat 降级，而是拆成数学等价、可独立链接的源项 Kernel，再由唯一 transport 合成。

这里的 “Full-Exact” 只表示：在相同 snapshot、正式分辨率、global pixel、sample index 和积分质量下，拆分图保留本实现原 Full 积分器全部已启用源项、实数公式与参数语义。GPU 结果必须用静态公式合同和数值回归共同证明，只要求在规定输入域及容差内等价，不承诺逐 bit 相同；它也不表示无偏 Monte Carlo 真值或云微物理参考解。当前太阳多重散射使用 3 个经验补偿 lobe，Powder、地面反弹、银河与极光照云也包含工程系数。

统一后端的一致性边界止于曝光和 Tone Mapping 之前的场景线性 HDR 辐亮度、透射状态与有效云遮蔽。屏幕预览的 ACES、显示抖动和 sRGB 转换，与正式资产的线性 Half、EXR 或 LogRGB 编码属于独立观察/发布合同；做视觉对比时，两侧必须使用同一观察变换。

### 内容

#### 1. 研究问题与完成标准

目标不是让 Web 页面勉强显示一朵云，而是同时满足四条合同：

1. **算法统一**：实时预览、最终渐进预览和正式烘焙引用同一个 KernelSet；不能只比较最后一个 transport Program。
2. **质量不降级**：正式烘焙请求的 View/Light/Ambient/Atmosphere 步数、Sun Cone 和 SPP 必须兑现；缺少扩展时更换累计方法，不能把 SPP 静默改成 1。
3. **交互可用**：冷启动和参数交互期间必须有明确、平滑、与当前状态一致的显示；不能发布 placeholder Weather、自检目标或还没经过云区间的纯空气 partial。
4. **失败可恢复**：Shader 链接超时或 context lost 后必须停止 GPU 提交；不能在同一受损 context 上继续编译第二个大型 fallback，导致刷新后连 WebGL2 都不可用。

“统一”应以可观察断言定义，而不是 UI 文案：

```text
previewKernelSet === canonicalKernelSet
progressiveKernelSet === canonicalKernelSet
offlineKernelSet === canonicalKernelSet
requestedSpp === actualSpp
compatFallbackAllowedForBake === false
```

最终渐进预览与正式烘焙还应满足：

```text
snapshotHash 相同
calibrationKey 相同
kernelGraphHash 相同
sampleSequence 相同
最终质量参数相同
```

只有 RenderPlan 可以不同：屏幕分辨率、Hemi-Oct 资产分辨率、瓦片大小、每帧提交批次、取消与导出方式。

#### 2. 证据层级与复现边界

本文区分四类证据，避免把“源码存在”误写成“运行通过”：

| 证据 | 已确认内容 | 不能外推的内容 |
|---|---|---|
| 现存 R6.2～R6.24 固定快照与源码差分 | 巨型 Program、早期多 Pass、采样相位、夜间环境、雾、预览状态机、后端选择、Kernel 图、累计和失效策略的真实演化 | 缺失版本不能靠后续注释补成完整事实；源码存在也不能单独证明目标 GPU 会链接或画面正确 |
| Chromium localhost 运行 | KernelSet 完成、Weather、含云预览、视角交互、正式烘焙和 context 状态 | 不能代替 Edge file://、其他 ANGLE 后端或移动 GPU |
| 强制无浮点混合烘焙 | 请求 2 SPP 时实际仍为 2，ping-pong 路径可用 | 尚未覆盖所有质量档和 4/8 SPP 高分辨率结果 |
| 用户提供的 Edge 错误与截图 | 单体 Shader 链接空日志、超时、context lost 和刷新后 WebGL2 不可用确实发生 | 不能提供助手侧完整 edge://gpu、驱动缓存或 GPU 进程时间线 |

曾提供的 Main 决策会话在本次维护中由应用读取接口返回错误，未登录的浏览器页面也不能访问其内容，因此本文没有把“已完整读取该会话”写成证据。版本源码、当前会话中保留的决策与实测日志已用于重建历史；待会话接口恢复后应补做一次逐轮审计。

#### 3. 版本演化：从巨型 Program 到统一 KernelSet

##### 3.1 证据边界

版本号不是证据。当前能直接检查的固定快照为 R6.2、R6.3、R6.6、R6.10、R6.11、R6.13、R6.19、R6.20、R6.21、R6.22、R6.23 和 R6.24。另有一个文件名写作 R6.7、但页面标题、眉标和介绍全部自称 R6.6 的快照；它只能视为“R6.6 未命名变体”，不能据此证明真正的 R6.7 做过什么。

R6.1、R6.4～R6.5、真正的 R6.7、R6.8～R6.9、R6.12、R6.14～R6.18 没有可信本地快照。后续源码注释对 R6.1 的回顾属于**回溯证据**，而不是 R6.1 原始实现；后续版本介绍声称“延续 R6.12”只能证明作者当时如此描述，不能恢复 R6.12 的全部改动。任何补齐这些空白的叙述都必须引用 Main 会话原文或对应源码，不能靠版本号连续性猜测。

##### 3.2 早期驱动稳定性与多 Pass 根系

| 版本 | 可直接核验的选择 | 暴露出的边界 | 沉淀下来的结论 |
|---|---|---|---|
| R6.1（仅有 R6.2/R6.3 注释回顾） | 先链接 legacy 巨型 Program，再链接近似重复的 compact joint Program | Windows ANGLE/D3D11 会在第二次大链接时返回空日志失败 | 同一页面里连续链接两个大型近重复 Shader 会放大驱动失败风险；该结论仍需 R6.1 原始快照补证 |
| R6.2 | 启动只链接裁剪后的独立联合传输 Program；旧 A/B 后端按需懒加载；错误报告加入 Program/Vertex/Fragment log、GL error、context lost 和能力上限；启动自检已做真实 HDR/LDR readback | `#drawCore` 仍可按状态选择 joint 或 legacy，故“共用绘制入口”不等于永远同后端；无 float blend 时 bake 仍把请求 SPP 降为 1 | 后端裁剪必须从入口可达性和启用 feature 出发；启动诊断必须保留驱动空日志与 context 状态；真实 draw/readback 是必要门禁，但不能替代质量等价和 SPP 兑现 |
| R6.3 | 用 MRT 状态把相机射线按真实顺序拆成 front-air、cloud-air interval、back-air 多个短 Pass；不再把约 96 个视线步及嵌套光照塞进一个片元 main | 启动仍按 Full→Compat→Minimal 选一个成功 tier，三种输出在同一会话虽复用所选 Program，却可能整体降级；无 float blend 时仍降为 1 SPP | 当前 Full-Exact Split 的思想根系在 R6.3；R6.23/R6.24 是把同一原则进一步应用到光照源项。多 Pass 状态共享与算法质量等价是两条独立合同 |
| R6.4～R6.5 | 无可信快照 | 无法判断 R6.3 到 R6.6 之间每项公式在何时变化 | 保留空白，等待源码或 Main 会话补证 |
| R6.6 | 保持多 Pass 联合传输；将云区间的随机位置改为邻近方向共享的空间连续分层偏移，并用确定性的 Cranley–Patterson 旋转稳定光照相位；加入 KHR 异步轮询和几何 Hemi-Oct 地平线重建 | 为首屏速度改成 Minimal 先显示、后台 Full→Compat 升级，而 Full/Compat/Minimal 的最大光步分别为 32/32/16，热切换必然改变质量；固定至少 5°/约 10 texel 的地平线重建也埋下宽带风险 | 噪声相关结构和求解公式同样重要；渐进随机数必须稳定。可见优先调度可以保留，但不得靠热切换到非等价求解器实现 |
| 名为 R6.7 的 R6.6 变体 | 内嵌 title/眉标/介绍仍为 R6.6，State/Air/Full/Compat/Minimal 源码哈希也与 R6.6 相同；差异集中在 Preview/Composite，例如像素足迹太阳盘、composite-only 夜光补偿和新的 ground preview | 文件名、内嵌版本和日期顺序互相矛盾；composite-only 补光不是云积分 Kernel 内源项 | 只能记为“R6.6 派生的显示层修订候选”，不授予完整 R6.7 的历史语义 |

##### 3.3 夜间照明、地平线介质与预览状态机

| 版本 | 可直接核验的选择 | 后来暴露的问题 | 当前结论 |
|---|---|---|---|
| R6.8～R6.9 | 无可信快照 | 无法精确定位夜间环境模型在哪一版引入 | 等待源码或 Main 会话补证 |
| R6.10 | 真正执行方向与相位一致的银河/极光夜空环境照云：方向辐照度进入 `extendedNightEnvironmentAtCloud`，随后加入云源项；把 `horizonHaze` 解释为世界空间指数高度雾，实时合成、烘焙预览和下半球都按世界空间射线处理 | 银河/极光照云当时尚未完成能量标定；一个参数同时承担物理传输与接缝观感，后来容易被错误调成宽亮带 | 环境照明必须进入同一体积传输并接受标定；物理近地介质与 Hemi-Oct 显示重建必须分离 |
| R6.11 | 稳定版真实禁用未经标定的极光与银河云重照：正式扩展环境函数返回零、Aurora 绑定强制为零；仍保留银河背景、月光照云和世界空间高度雾 | 遗留 uniform/辅助函数仍在源码里，证明“搜索到函数名”不等于 feature 进入正式执行路径 | 关闭未验证源项是合法的全后端一致 feature 决策；不能用设备相关 Compat 偷偷删源项 |
| R6.12 | 无可信快照；R6.13 只声明其余研究路径延续 R6.12 | 无法恢复 R6.12 的具体实现差分 | 等待源码或 Main 会话补证 |
| R6.13 | 真正修复预览质量状态机：112/144/180 px 交互基线先种入 360/720/920 px 全尺寸目标，再按地平线优先的水平条带逐步更新；revision 失效与 `cancelRefinement` API 可取消在途精炼，但没有独立取消按钮；扩展夜间照云在该快照中也已恢复执行 | 分辨率从低到高和条带逐块替换仍是多级重算，不天然等于样本逐步累计；缺少 R6.12，不能断言夜间照云恰在 R6.13 首次恢复 | 真渐进必须定义可信样本、累计历史和样本序列；“画面逐块出现”或“由糊变清”不能替代数值累计 |
| R6.14～R6.18 | 无可信快照 | 无法判断 R6.13 的预览状态机如何演化到 R6.19 三后端分叉 | 等待源码或 Main 会话补证 |

地平线参数的语义漂移尤其值得警惕：R6.3 UI 把它称为“地平线多散射填充”，用于补偿 RGB 单次散射近似的低空暗部；R6.10 以后则称为“近地高度雾/地平线衔接”，控制世界空间指数介质的近地消光。这里的“统一”也只能写成共享世界空间定义与边界语义：例如 R6.13 主合成与 preview 仍使用不同的基础消光系数和积分实现，并非逐参数、逐 evaluator 数值相同。相同字段名和默认值不代表相同物理模型。迁移参数时必须记录单位、公式、参与的积分路径和显示阶段，不能只复制滑杆数值。

##### 3.4 后端统一及其反复失败

| 版本 | 当时的选择 | 后来暴露的问题 | 当前结论 |
|---|---|---|---|
| R6.19 | 启动用 Minimal，渐进优先 Compat，烘焙 Full-first；Full/Compat 均失败再回 Minimal | 预览与烘焙并非同一算法；缺少浮点混合时正式 SPP 降为 1 | 只能作为交互原型，不能宣称预览代表正式结果 |
| R6.20 | 渐进转而复用 offline Program，试图实现 single-solver | 启动仍是独立 Minimal；offline 仍允许 Compat/Minimal；“对象共享”不能保证落到 Full | 统一必须同时约束候选质量等价性和失败策略 |
| R6.21 | 建立 Canonical Program，三种 plan 都调用 ensureCanonical | 约 6 万字符的单体 Full 给 ANGLE/驱动造成长链接；Compat 仍被当作等价 fallback | 入口统一不等于数学统一，也不等于驱动可承受 |
| R6.22 | 加入异步编译等待、Full→Compat 共同回退 | Full 超时后在同一 context 继续提交近似同样巨大的 Compat；发生 context lost，刷新后浏览器进入无 WebGL2 状态；烘焙仍可能降 SPP | 超时/context lost 必须成为本 context epoch 的粘性失败，禁止二次大型编译 |
| R6.23 | 拆成五单元 Full-Exact KernelSet，禁止 Compat，加入无扩展 ping-pong 累计 | 单体银河源仍包含八条云光学深度路径，冷链接可超过 30 秒；启动自检复用显示目标，曾把 placeholder Weather 噪点发布到主画面 | 拆分要按驱动 IR fan-out，而不只按源码字符数；自检资源必须私有 |
| R6.24 | 银河拆为 Exposure、Rays 0～2、Rays 3～5；七单元有界并发；显示与可信累计分离 | 当前仍有真实 Edge file:// 和跨 GPU 验证缺口 | 这是当前可维护基线，不是终局真值 |

这条完整演进链给出六个反直觉结论：

- **“更短的源码”不一定更容易链接。** 驱动会内联函数；一次 main 调用八条 `cloudOpticalDepth` 路径，比字符数更能决定 IR 展开压力。
- **“同一个 ensure 函数”不等于同一算法。** 如果候选列表包含非等价 Compat，运行结果仍会因设备不同而漂移。
- **“能看到画面”不等于渐进。** 显示旧缓存、自检图、纯空气 partial 或降低步数的最终图，都可能制造“正在收敛”的假象。
- **“编译/链接成功”不等于后端可用。** 至少要完成真实 draw、FBO 检查、有限值 readback 和云 alpha/RGB 语义检查。
- **“更多随机”不一定更平滑。** 邻近方向使用互不相关的深度 hash 会破坏非线性光照的空间连续性；稳定的分层相位通常比逐像素白噪声更可靠。
- **“同名参数”不等于同一含义。** 地平线填充、参与介质和显示接缝是三层问题，不能因为都叫 haze 就共享一个经验结论。

#### 4. Canonical 数据流

当前端到端链路是：

```text
Weather / 3D Noise / 参数快照
    ↓
密度函数 sampleCloud(p, detailWeight, lodBias)
    ↓
密度柱校准：目标光学厚度 τ → extinctionScale
    ↓
同一云壳区间与同一分层采样位置
    ↓
六个源项 Kernel
    ├─ Sun + Ground + Multiple
    ├─ Sky + Moon Ambient
    ├─ Galaxy Exposure
    ├─ Galaxy Rays 0..2
    ├─ Galaxy Rays 3..5
    └─ Aurora
    ↓
唯一 Cloud + Air Transport（4 MRT 状态）
    ↓
同一 Composite
    ├─ 交互透视基线（display-only）
    ├─ Hemi-Oct 渐进累计
    └─ Hemi-Oct 正式瓦片烘焙
    ↓
Preview 方向重投影 / ACES / 输出编码
```

源项拆分并没有让太阳、天空、银河各自独立改变云密度。每个源项 Kernel 都必须调用同一 `r63PrepareCloudInterval`：同一投影方向、区间索引、sampleIndex、LOD、detailWeight、边界细化和 `sampleCloud`。否则把一个 Shader 拆成多个 pass 后，各 pass 会在不同空间位置求光，合成结果不再等价。

#### 5. 云层几何：球壳和有限区间

云层由以行星中心为原点的内外两个球面限定：

```text
R_inner = R_planet + H_bottom
R_outer = R_planet + H_top
```

观察射线分别与内外球求交，再根据相机处于云层下方、内部或上方选择有效的 `[t_start, t_end]`。这比平面层更适合地平线：平面层在视线趋近水平时交距趋于无穷，球壳的曲率则给出有限、可解释的远端。

实现仍要额外限制最大积分距离。这里的限制是 RenderPlan 的物理/性能边界，不应改写密度或光照公式；当远端被截断时，诊断应先检查云壳区间与 `maxCloudDistanceKm`，而不是提高曝光。

#### 6. 密度不是一个噪声值

`sampleCloud` 返回的不只是 `density`，还保留：

- `baseDensity`：未被高频侵蚀前的宏观体积；
- `coreDensity`：受保护的液态水核心；
- `detailRemoval`：细节侵蚀量；
- `regionalCoverage`：Weather Map 提供的区域覆盖；
- `profile`：垂直剖面；
- `organization`：云团组织度；
- `farHorizon`：远端 LOD/形态混合权重。

一个可维护的概念式是：

```text
macro = remap(baseNoise + weatherBias, coverageThreshold, 1)
shaped = macro × verticalProfile(height, cloudType, organization)
detail = erosion(detailNoise, curl, footprintLOD)
density = preserveCore(shaped) - detail
```

Weather 必须是世界空间确定函数。相机旋转只能改变方向到 Hemi-Oct 的重投影，不能改变世界中云的随机相位；否则旋转一下视角，噪点与云形都会重置，方向缓存失去意义。

光学密度对核心和薄壳采用不同权重：

```glsl
core  = clamp(coreDensity, 0, density);
shell = max(density - core, 0);
rhoOptical = core + shell * shellWeight;
```

这样提高目标光学厚度时，先加强云体核心，而不是把所有被侵蚀的薄丝同时变成不透明雾。

#### 7. 光学厚度校准与缓存失效

UI 中的“目标光学厚度”不能直接当作每公里消光系数。当前流程先用低分辨率 Hemi/顶视柱积分估计密度柱分布，再用参考分位数求：

```text
extinctionScale = targetTau / referenceColumnKm
tau_ray = ∫ rhoOptical(p) × extinctionScale ds
T = exp(-tau_ray)
```

校准 key 只应包含会改变密度柱的字段：seed、Weather、云底/云顶、覆盖率、形态、噪声/侵蚀、LOD、密度模型、目标 τ、Kernel revision/source hash。下列字段不应触发重新校准：

- 曝光、Tone Mapping、诊断显示；
- 太阳/月亮方向和颜色；
- 光照强度、银河、极光；
- 相机 yaw/pitch/FOV 和画布尺寸。

光照变化需要重置辐亮度累计，但可以复用密度柱；曝光和相机变化连辐亮度累计也不应重置，只做 display 或方向重投影。

#### 8. 云—空气联合传输

每个主视线区间同时处理空气和云。设：

- `σ_air`：Rayleigh、Mie、Ozone 与浅层近地介质的总消光；
- `σ_cloud`：云光学密度乘校准后的消光尺度；
- `q_air`：空气源项系数；
- `L_cloud`：太阳、月亮、环境、银河、极光、地面反弹等云内入射辐亮度近似；
- `T_view`：到当前区间前的视线透射率。

当前离散步使用解析常系数积分：

```text
σ_total = σ_air + σ_cloud
F = (1 - exp(-σ_total Δs)) / max(σ_total, ε)
ΔL_air   = T_view × q_air × F
ΔL_cloud = T_view × (σ_cloud L_cloud) × F
T_view  *= exp(-σ_total Δs)
L       += ΔL_air + ΔL_cloud
```

这比“先画天空，再 alpha 混云”更重要：空气会衰减云光，云也改变总透射，地平线长路径必须在同一积分中处理。Composite 已经得到线性 HDR 的物理合成结果，因此显示端再把 underlay 按云 Alpha 混一次会双重计算背景和消光。

4 MRT 状态分别保存总辐亮度/云透射、总透射/深度统计、空气辐亮度/局部密度和纯空气透射/云权重。诊断必须说明每个通道语义，不能只看 RGB 是否非零。

#### 9. 光照源项及其工程性质

##### 9.1 太阳与月亮直射

直射项使用双叶 Henyey–Greenstein 相位：

```text
phase = dualHG(dot(view, light), g_forward, g_backward, backwardWeight)
L_direct = L_light_at_cloud × T_light × phase × edgeResponse
```

`T_light` 由从云点沿光方向的光学深度步进得到。太阳还可以用有限锥采样近似软阴影；这项在 Compat 中曾被删除，所以 Compat 不能作为 Full 的质量等价 fallback。

Powder/银边项是经验增强，不是额外能量守恒散射阶：

```text
powder = 1 - exp(-rhoOptical × extinctionScale × Δs × k)
edge = 1 + powder × pow(T_light, a) × silverStrength
```

它应受开关和强度控制；过大时会把任何薄层都变成白边。

##### 9.2 三个经验太阳多重散射补偿 lobe

当前 WebGL Full 积分器在单散射项之外迭代 3 个经验补偿 lobe；每个 lobe 缩小 HG 的各向异性、软化太阳透射并衰减能量：

```text
scale_n  = 2^-n
phase_n  = dualHG(mu, g_forward scale_n, g_backward scale_n, w)
softT_n  = T_sun^(0.60^n)
energy_1 = 0.34
energy_(n+1) = 0.43 energy_n
L_ms += L_sun × softT_n × phase_n × energy_n, n=1..3
```

月光另加一个较弱的高阶近似。这个模型用于恢复厚云内部能量和方向层次，不是对辐射传输方程严格求解到“第三次散射”；旧 Unity 工具所谓“四阶”同样是 4 个经验补偿 lobe。数字表示补偿项数量，不是可跨实现搬运的物理散射阶数。

##### 9.3 天空环境与云壳暴露

环境光不能是一个对所有非零密度样本都相同的常量。当前模型先估计向上和侧向天空可见度，再按云层高度调制：

```text
visibility = 0.74 exp(-tau_up) + 0.26 exp(-tau_side)
L_ambient = lowFrequencySky × visibility × ambientStrength × heightResponse
```

历史上的常量月光半球补光会把厚云核心整体抬成灰蓝色，并使夜间预览与烘焙能量不一致。修正后的月光环境项同时受 `visibility`、局部密度形成的壳层暴露、归一化高度与月亮半球关系约束。

##### 9.4 地面反弹

地面反弹按局部上方向、太阳/月亮高度、云层高度和地面反照率给出低频项。它只是一次工程近似，不等同于场景 GI。夜间对地面色做去饱和可以抑制不合理染色，但应在 Canonical 源项中统一，而不能只改预览。

##### 9.5 银河与极光

银河照云使用六个固定方向，权重为：

```text
0.20, 0.18, 0.16, 0.16, 0.14, 0.16
```

每项包含低频银河辐亮度、双叶 HG 和沿该方向的云可见度。公共 envelope 包含夜间权重、天空可见度响应、云层顶部暴露与边缘暴露。极光使用自己的方向辐照度，但复用同一天空可见度与暴露逻辑。

#### 10. 为什么拆 Shader，怎样保持等价

R6.22 的 Full/Compat 片元源码约为 6.2 万/5.6 万字符，驱动返回空链接日志并不代表没有问题；ANGLE 或底层驱动可能在链接/优化阶段超时或失去 context。Compat 只少量缩短源码，却删掉太阳锥、环境可见度和完整多重散射，既没有显著降低 IR 压力，也破坏了质量合同。

R6.24 使用七个程序：

1. `sun-ground-multiple-source`
2. `sky-moon-ambient-source`
3. `galaxy-exposure`
4. `galaxy-rays-012`
5. `galaxy-rays-345`
6. `aurora-source`
7. `cloud-air-transport`

银河拆分解决的是 IR fan-out：原单元会在一个 main 中展开两条 ambient visibility 和六条方向 visibility，共八条嵌套光学深度路径。拆分后 Exposure 最多两条，两组 Rays 各三条；transport 只读取最终源项纹理。

Galaxy Exposure 把公共 envelope 写到 RGBA32F 的 Alpha；两组方向把未乘 envelope 的 RGB 通过 ping-pong 累加，transport 最后只乘一次：

```text
raw.rgb = sum(ray_0 ... ray_5)
raw.a   = night × visibilityResponse × topExposure × edgeExposure
L_galaxy = raw.rgb × TAU × strength × 0.34 × raw.a
```

一次真实回归曾把每组 `raySource` 先乘 `raw.a`，transport 又乘一次，得到 `E²`。当 `E` 很小时会把银河照云额外压暗几十倍。正确原则是“方向项先求和，公共 envelope 恰好乘一次”。

拆分后的浮点加法结合顺序和中间纹理舍入可能与单体 Full 不完全相同，因此合同是 **规定输入域与容差内的公式等价**，不是 bit-identical。六个单方向 Kernel 按原顺序 ping-pong 可以更接近原运算顺序，但跨 Program 优化和纹理落地仍不能提供位级保证，且 pass 数与显存会继续增加。

#### 11. KernelSet 身份比 Program 别名更可靠

只比较 `progressiveCloudProgram === offlineCloudProgram` 会漏掉 source Kernel。当前做法把完整图冻结：

```js
canonicalKernelSet = Object.freeze({
  revision,
  graph,
  sourcePrograms,
  transportProgram,
  samplerBudget,
  formulaEquivalentWithinFloat32: true,
});

previewKernelSet = canonicalKernelSet;
progressiveKernelSet = canonicalKernelSet;
offlineKernelSet = canonicalKernelSet;
```

正式烘焙只能接受已通过静态公式门禁和数值回归的 KernelSet；运行时写死 `qualityEquivalent === true` 只能表达意图，不能自证等价。门禁至少包括可达函数/常数/feature 静态合同、同输入单 sample 线性 HDR oracle，以及最终 N-SPP 的误差统计。非等价 Compat 可以保留为独立调试/低端展示模式，但必须用不同名称、不同资产合同和显眼水印；不能悄悄成为 bake fallback。

当前 transport 需要 11 个片元纹理单元，银河累加 pass 需要 4 个；初始化时必须门禁 `MAX_TEXTURE_IMAGE_UNITS >= 11`，同时要求至少 4 个 draw buffers 与 color attachments。

#### 12. 真正的渐进：可信样本和显示样本分离

渐进预览的可信历史只能接收**完整样本**：

```text
sample_0 完成 → accum_1 = sample_0
sample_1 完成 → accum_2 = (1/2) accum_1 + (1/2) sample_1
...
sample_n 完成 → accum_(n+1) = n/(n+1) accum_n + 1/(n+1) sample_n
```

当前 interval 内还没完成的 partial 是截断积分。它可以显示进度，但不能写回平均历史，否则每次分帧批次都会以不同权重污染结果。显示降噪同样必须 display-only。

“从噪点逐渐清晰”应由完整样本数增加产生，而不是在同一个样本里逐步拉长积分距离伪装成 SPP。推荐发布规则：

- 没有完整样本时，可显示当前 partial，但要标注 incomplete；
- 已有稳定平均时，继续显示 stable，待当前样本完整后再切换；
- 阶段切换保留上一阶段 stable，直到新阶段首个完整样本；
- 最终可信阶段继承正式质量的 View/Light/Ambient/Atmosphere/Sun Cone；早期低分辨率/低步数阶段只能叫 provisional。RenderPlan 可以设置不同停止 SPP，但用于一致性比较时，双方前 N 个完整样本必须相同。

R6.24 使用 prefix-stable Halton(2,3) 低差异序列。只有在 snapshot、正式 Hemi 分辨率、投影映射和 jitter 语义相同的前提下，样本身份才由 `(globalPixel, sampleIndex)` 唯一决定；渐进与正式烘焙的前 N 个完整样本必须相同。增加目标 SPP 不改变已有前缀，但 Halton 数列相同本身不足以证明像素样本相同。

当观察的是同一个 Hemi-Oct 方向缓存时，相机 yaw/pitch/FOV、显示画布尺寸和曝光只是观察变化，应重投影而不是清空 sampleCount。相机位置、Hemi 源分辨率、云密度、Weather、seed、太阳/月亮、模块和质量会改变积分输入，必须按依赖层级重置。

#### 13. 正式烘焙：扩展缺失不能降低 SPP

错误实现常写成：

```js
actualSpp = hasFloatBlend ? requestedSpp : 1;
```

这会让不同设备得到不同质量资产。正确做法是在没有 `EXT_float_blend` 时切换累计方法：每个完整样本写 `bakeSampleTarget`，再用两个 RGBA16F 累计目标做 running average；全部 SPP 完成后复制到正式 target。

```text
有 float blend：每样本按 1/SPP 加法累计
无 float blend：sample RT + accum A/B ping-pong running average
共同约束：actualSpp = requestedSpp
```

当前 128²、2 SPP 已在两条路径完成，强制无扩展时仍报告实际 2 SPP，指标与浮点加法路径接近。尚需补做 4/8 SPP、更高分辨率和跨 GPU 容差测试。

瓦片只允许改变提交区域和调度。方向、随机相位和 LOD 必须使用 full resolution 与 global pixel 坐标；若每个 tile 从局部 `(0,0)` 重新开始，瓦片边界会出现重复噪声、相位跳变和错误 Hemi-Oct 方向。

#### 14. 冷启动和 context lost

`KHR_parallel_shader_compile` 只能让应用轮询完成状态，不能保证驱动在某个时间内成功，也不能保证查询最终 `LINK_STATUS` 不阻塞。安全策略是：

1. 为每个 Program 记录 submitted、complete、linked、耗时、源码 hash/字符数和 context epoch；
2. KHR 轮询超时时，应用可选择不再用 `LINK_STATUS` 强制同步等待；真正 `gl.isContextLost()` 后禁止继续查询 Program 状态、ACTIVE_UNIFORMS 或能力上限；
3. 删除仍可安全删除的句柄，停止新提交；
4. 将失败记为当前 context epoch 的 sticky failure；
5. context lost 事件取消渐进、烘焙、定时器和 Worker 到 GPU 的后续上传；
6. 不在同一 context 上编译第二个大型 fallback。

七个 Kernel 使用有界并发：支持 KHR 时最多同时挂起两个 Program 编译请求，否则串行。KHR 不创建 JS Worker；这里的并发只是应用提交多个 Program 后非阻塞轮询完成状态。其目的不是让七个程序同时压入驱动，而是让最长的太阳源与较小 Kernel 有限重叠。一次带源码 nonce 的 Chromium 冷编译约 22.6 秒；同环境 warm reload 中，display-only partial-source provisional 约 2.5 秒可用，完整 KernelSet 约 3.8 秒可用。数字只描述该次环境，不能写成跨设备预算。

#### 15. 启动显示状态机

Weather Worker 未完成时，1×1 placeholder 纹理不是合法云数据。启动自检曾复用 `bootstrapTarget`：自检把 placeholder 云噪点画进同一对象，之后只恢复显示指针，像素内容却已经被覆盖，于是出现全屏高噪点高曝光。

正确状态机是：

| Kernel | Weather | 允许显示 |
|---|---|---|
| 未完成 | 未完成 | 当前相机的平滑空气/地面 underlay |
| 已完成 | 未完成 | 仍是 underlay；自检只能写私有 target |
| 未完成 | 已完成 | underlay 或缺失源显式填零的 display-only partial-source provisional；不得称 Full-Exact |
| 已完成 | 已完成 | 当前状态 Canonical 首样本，随后可信渐进累计 |

Underlay 要关闭 clouds、milkyWay、aurora 和 stars，使用确定性 midpoint 空气采样；它不进入后续随机累计。启动自检必须拥有独立 target 和 state pool，readback 后销毁，永不写 `displayLiveTarget`。

当 KernelSet 正在构建时，可以发布“已链接源项 + transport，缺失源显式填零”的 partial-source provisional baseline，但必须醒目标为非 Full-Exact，只用于显示、不写 progressive/bake history；不可变 KernelSet 仍要等全部七个程序完成后才发布。

#### 16. 地平线：物理浅层介质和显示接缝不是同一个问题

地平线宽亮带有两个独立放大器。

##### 16.1 物理近地介质过密

旧默认：

```text
scaleHeight = 0.42～0.60 km
baseExtinction(haze=1, groundHaze=1) = 1.10 / (1 + 2.50) ≈ 0.314 km^-1
```

这更接近浓天气雾，会在长水平路径上产生巨大散射和消光，洗白数度上方的天空。当前修正：

```text
scaleHeight = 0.12～0.18 km
baseExtinction(haze) = 0.080 haze / (1 + 0.80 haze)
baseExtinction(haze=1, groundHaze=1) ≈ 0.044 km^-1
```

同一个工程基础消光系数经过高度场等模型项后，同时进入消光、光照透射和入射散射，避免只有颜色没有消光的假雾带。因为空间单位使用 km，它在该实现中按 `km^-1` 参与积分；这不表示它是实测气象参数。该介质在 Canonical 预览与烘焙中共享，不能只在屏幕后处理里修。

##### 16.2 Hemi-Oct 显示滤波支撑过宽

旧 Preview 把地平线最后一圈 texel 用固定 2.4°～5° 的 smoothstep 混到上方天空。按当前近地平线方向的估算，128² Hemi-Oct 源纹素约为 0.74°；实际八面体映射纹素立体角随方向变化，不能把这个数当作全图常量。固定 5° 支撑仍会把一个高亮边缘纹素扩成明显宽带。

显示修正由实际 footprint 决定：

```text
previewPixelAngle = verticalFov / screenHeight
sourceTexelAngle ≈ 1.65 / min(sourceWidth, sourceHeight)
seamSupport = max(1.35 previewPixelAngle, 1.05 sourceTexelAngle)
regularWeight = smoothstep(0.50 seamSupport, 1.25 seamSupport, elevation)
```

当前公式在指定 128² 近地平线样本上把“约 1° 内结束”作为目标，而不是 Hemi-Oct 的普遍解析结论；必须用 atlas 与球面预览的同方向数值对照验收。该修正只属于 Preview 重采样，不修改 HDR Hemi-Oct 烘焙内容。物理雾负责真实长路径，footprint filter 只负责上下半球采样接缝；把两者合并成一条固定颜色宽雾带，会重复能量并掩盖真正问题。

#### 17. 诊断顺序：先证明云在哪一层消失

当最终画面“只有天空没有云”时，不应立即提高密度或曝光。按以下顺序隔离：

1. `cloudOpacity`：云密度与 `sigmaCloud` 是否非零；
2. source target RGB：太阳/环境/银河/极光各源纹理是否在 transport 前非零；
3. `netCloudIntegratedRadiance = L_total - L_airOnly`：经过 transport 的云净积分辐亮度是否非零；
4. `totalTransmittance = T_total` 与 `T_cloud_relative = T_total / max(T_airOnly, ε)`：云是否在空气透射之外继续衰减背景；
5. 线性 HDR final：云辐亮度与被消光背景的净差；
6. ACES/曝光后 final：是否只是 Tone Mapping 吞掉对比；
7. display target kind/revision：是否显示了 underlay、自检、旧 revision 或 incomplete partial。

只验证 RGB 非零不够：纯空气本来就有 RGB。至少同时检查云 opacity/coverage、KernelSet revision、Weather seed、sampleCount 与 target revision。

诊断视图自身也要避免重复语义。例如两个模式都显示 `L_total - L_airOnly`，并不能区分源纹理能量和 transport 后净贡献；直接显示 `T_total` 也不是 cloud-only 透射。更有用的是：

```text
netCloud = (L_total - L_air) + (T_total - T_air) × background
relativeCloudT = T_total / max(T_air, ε)
```

诊断模式应绕过或固定 Tone Mapping scale，否则“看不见”仍可能只是显示曲线。

##### 来自旧烘焙器决策史的交叉门禁

可访问的早期静态云烘焙器线程还提供了三条可复用的反例，它们不是 WebGL 专属，却直接影响本文的验收设计：

- “能找到 Kernel/Program”不等于真实执行可用。某 Unity 传播 Kernel 只有在第一次真实 Dispatch 时才因驱动无法展开循环而失败；迁移到 WebGL2 后，原则是执行适合当前后端的最小真实 GPU submission，例如 draw、同步、readback 和有限值检查，而不是照搬 Compute API 或 TDR 阈值。
- 持久缓存如果不包含 Shader、Runner、Kernel graph 和算法 revision 的源码指纹，修改算法后仍会命中旧线性传输，几秒钟得到一张“成功结果”。这种 warm hit 不能用于评价新算法。
- 会话不能只依据调度器走到末尾就报告 Completed。Program 无效、GPU error、context lost、readback 非有限值和输出 SPP 不足，都必须使正式结果失败并禁止导出。

同一线程还曾发现密度顺序错误：在那套 Unity 密度 remap 中，先乘垂直剖面再用 `1-coverage` 高阈值裁切，会把大多数非核心体素清空。该工具最终采用 coverage 塑造宏观占据→垂直剖面→高频边界侵蚀，这是**该密度模型的合同顺序**，不是所有体积云公式的普遍定理；另一种归一化或 remap 完全可能需要不同顺序。

#### 18. 资源和性能取舍

拆分 Kernel 的代价是真实存在的：从五个 interval draw 增到七个，银河多一个 RGBA32F scratch；在 512²、1024²、2048² 下，一张 RGBA32F 约为 4、16、64 MiB。正式 bake 的 4 MRT 状态、sample 和 ping-pong 累计也会增加峰值显存。

因此优化顺序应是：

1. 缩短单次 GPU 提交和 Shader IR；
2. 有界编译并发和分帧 batch；
3. 完成阶段后尽快释放 scratch；
4. 仅在严格保持 global coordinate 契约时做 tile-local target；
5. 最后才考虑降低分辨率或样本预算，而且只能作为显式 RenderPlan，不得伪装成正式质量。

性能优化不能删除当前启用的密度/光照项。如果设备无法运行 Full-Exact，应明确报告“不支持正式烘焙”，而不是输出一张看似成功但算法不同的资产。

#### 19. 实现骨架

```js
async function ensureCanonicalKernelSet(snapshot, onProgress) {
  if (canonicalKernelSet) return canonicalKernelSet;
  if (stickyCompileFailure) throw stickyCompileFailure;

  const graph = [
    sunGroundMultipleSource,
    skyMoonAmbientSource,
    galaxyExposure,
    galaxyRays012,
    galaxyRays345,
    auroraSource,
    cloudAirTransport,
  ];

  const programs = await boundedCompile(graph, hasKHR ? 2 : 1);
  assertContextAlive();

  canonicalKernelSet = Object.freeze({
    revision: sourceHash(graph),
    graph: Object.freeze(graph.map(x => x.name)),
    programs: Object.freeze(programs),
    qualityEquivalent: true,
  });

  previewKernelSet = progressiveKernelSet = bakeKernelSet = canonicalKernelSet;
  return canonicalKernelSet;
}

function accumulateCompleteSample(previous, sample, completedCount, out) {
  // partial 与 denoise 目标禁止传入这里。
  drawRunningAverage(previous, sample, out, completedCount);
}

async function bake(plan, requestedSpp) {
  const actualSpp = requestedSpp;
  for (let i = 0; i < actualSpp; i++) {
    renderAllTilesWithGlobalCoordinates(i, sharedJitter(i));
    if (!hasFloatBlend) pingPongAverageCompletedSample(i);
  }
  assert(actualSpp === requestedSpp);
}
```

#### 20. 验证矩阵

##### 20.1 静态门禁

- [ ] Preview/Progressive/Bake 的 KernelSet 对象严格相同。
- [ ] Graph 包含全部源项和 transport；静态公式/feature 合同与数值 oracle 通过后才允许 bake，不能只信 `qualityEquivalent=true` 声明。
- [ ] transport 最大 sampler unit 小于设备 `MAX_TEXTURE_IMAGE_UNITS`。
- [ ] final progressive 的全部积分质量字段等于正式 quality preset。
- [ ] 前 8 个 progressive jitter 与 bake jitter 逐项相同。
- [ ] partial/denoise/self-test target 从不成为可信 sample。
- [ ] `requestedSpp === actualSpp` 不依赖 `EXT_float_blend`。
- [ ] density calibration key 排除曝光、相机和纯光照字段。

##### 20.2 浏览器冷启动

- [ ] 每次把唯一 nonce 注入活跃 GLSL uniform/表达式，不能只改 URL 或注释。
- [ ] 记录浏览器、GPU、驱动、ANGLE 后端、KHR、context epoch 和逐 Kernel 时间。
- [ ] Weather 人为延迟 10 秒时，拖动/滚轮始终显示平滑 underlay。
- [ ] 自检前后 display target kind 不变，自检 target 从未发布。
- [ ] 任一 Kernel 超时后不再提交 fallback，context 不被二次伤害。

##### 20.3 渐进与交互

- [ ] 完成全部 front-air、cloud intervals、back-air 并 composite 的首个完整 sample 后，才写入可信累计；任何 partial 发布都必须标注 incomplete。
- [ ] SPP 单调增加，噪声随完整样本平均下降。
- [ ] 相同 Hemi 源下旋转/FOV/显示画布 resize/exposure 不改变 revision 和 sampleCount；相机位置或 Hemi 源分辨率变化必须失效。
- [ ] 连续拖 coverage 时当前状态基线及时变化；停手后重启可信累计。
- [ ] 改太阳重置辐亮度累计但复用密度校准；改 coverage 重新校准。

##### 20.4 正式烘焙一致性

- [ ] 同 snapshot、quality、resolution、sampleIndex、jitter 下比较 progressive raw sample 与 bake tile sample。
- [ ] RGBA16F 建议起始像素门槛：`absError <= 2e-3 || relError <= 5e-3`；另记录近零像素、亮度分位和最大误差，最终按设备分布调整。
- [ ] 强制无 float blend 时 2/4/8 SPP 全部兑现，并与 float blend 路径在半浮点容差内。
- [ ] 取消、中途切换视图和 context lost 不留下可导出的半成品。

##### 20.5 地平线

- [ ] 对同一 Hemi-Oct HDR 比较 atlas 与球面预览；atlas 窄而球面宽说明是显示滤波。
- [ ] 指定 128² 测试方向上，display seam 以约 1° 内结束为目标；2°以上与 atlas 同方向采样差异小于目标容差。其他方向与分辨率按实际 footprint 重测。
- [ ] 关闭近地介质后仍无采样缝；增加 haze 只改变物理长路径，不创建固定颜色横带。
- [ ] 四个地平线象限、日出/白天/夜间分别检查。

#### 21. 已证伪做法

- ❌ 为首屏速度使用不同 Minimal/Compat 求解器，却把它叫作正式预览。
- ❌ Full 链接失败后在同一 context 立即编译另一个大型 Compat。
- ❌ 没有 float blend 时把正式 SPP 改成 1。
- ❌ 把 incomplete interval 或显示降噪结果写进累计历史。
- ❌ 参数变化后长期显示旧 revision 的“稳定图”。
- ❌ 用 placeholder Weather 运行自检并复用主显示 target。
- ❌ 用固定 2.4°～5° 宽雾/滤波带掩盖 Hemi-Oct 地平线接缝。
- ❌ 只比较 transport Program，忽略 source Kernel 是否一致。
- ❌ 因为拆成多个 pass 就声称 bit-identical；至少要做同输入数值容差比较。

#### 22. 当前未验证范围

- 真实 Microsoft Edge `file://`、全新 GPU 进程和 cache-resistant nonce 的完整冷启动。
- Intel、AMD、NVIDIA 以及移动 WebGL2/ANGLE 的跨驱动 Kernel 链接分布。
- 512² 以上正式资产的 4/8 SPP float 与 ping-pong 对照。
- 最终 progressive raw Hemi 与 bake tile path 的自动像素级对比工具。
- 长时间 context restore；当前安全策略以停止提交并提示重载为主。
- Main 决策会话逐轮复读；本次应用接口失败，待恢复后需要补审历史假设。

#### 23. 固定快照清单

下表用于说明本文究竟审过哪些构建。哈希针对原始单文件 HTML；重名副本 R6.2 `(1)` 与 R6.6 `(1)` 分别和原文件完全同哈希，因此不重复列出。文件名中的日期不是实现完成时间的严格证明，只用于识别现存文件。

| 内嵌版本 | 字节数 | SHA-256 | 证据备注 |
|---|---:|---|---|
| R6.2 | 1,960,537 | `70E694950204AF2A988BDBD44C9D6F9B01B7BAE355445AAECBEE3F20BCA1DAC4` | 有两个完全相同副本 |
| R6.3 | 2,028,397 | `5CD4219CE68668FC4E399D102D16BF950004F80CA12AC91F1FA1837DE302A404` | 多 Pass/MRT 根系的直接快照 |
| R6.6 | 2,047,510 | `19502D28AA7C4DBDEA4BEFE1F67DDF1ED70E2C804145AA50C1304B7B0F91D16B` | 有两个完全相同副本 |
| R6.6 未命名变体 | 2,052,372 | `51FBB97622872E074C1D2A09EA292C9BEF5A0C2459071C6A5D125EF138D16EBD` | 文件名写 R6.7，但 HTML 内三处版本标识均为 R6.6 |
| R6.10 | 2,096,603 | `A13974F90F8156EB422FA132B38D27DB2F0AD203B8D07CC915DF764B322E8758` | 夜间环境与世界空间高度雾 |
| R6.11 | 2,093,752 | `5F99153B0CC74655268E03A313C901A5D2BCCB1D44AB65EC7F79D1A411DF5CC8` | 稳定版收回未标定夜间照云实验 |
| R6.13 | 2,123,904 | `80B7384A31487B055E6EFDB96C35DC41101FDD5499B29E6CF35B6D2C7E7ACE59` | 预览质量状态机修复 |
| R6.19 | 2,158,569 | `153CA6B705CABFC0D85EF6744C988493AE1DD8D1E47B61046BC05E51614DEB30` | Minimal/Compat/Full 分叉基线 |
| R6.20 | 2,161,502 | `125335A10BD59ADB279C7AFC0AE65D08CB6415AC068B87E5B83120643D9005F8` | single-solver 过渡 |
| R6.21 | 2,108,768 | `1DF1F009F4FA6019B15F6D75D4214FE3534679A09CADABB26C12D1B4E298B68E` | 单体 Canonical 过渡 |
| R6.22 | 2,122,740 | `3532B250A88BA929FF6D9DB0E5A796B70F67CEDC6F5FAC223FC6C7945D931AFA` | Full/Compat 冷链接失败样本 |
| R6.23 | 2,164,893 | `5F14AF612BDEAE59DE854811BA3078EAB10E0C2F725F2A55C599355663F66AE2` | 五单元 Full-Exact Split |
| R6.24 | 2,186,268 | `79902BF66F79E41F149475A07C12FDBA584D5821D7B1A4B10A6733B7231DB71A` | 七单元当前基线 |

### 关键代码

关键公式和伪代码已随各章节给出。实现时最重要的维护备注是：拆分 pass 只能改变调度，不得让各源项使用不同的密度样本、区间位置、LOD 或随机序列。

### 相关记录

- [静态体积云天空的高质量离线烘焙](./static-volumetric-cloud-sky-baking.md) - Unity Editor 离线烘焙、球壳密度、瓦片和资产链路；其中 4 个经验补偿 lobe 是该工具的实现，不是本文 WebGL 3-lobe 合同。
- [半八面体单图 HDR 天空的编码、采样与色带治理](./hemi-octahedral-hdr-sky-texture.md) - Hemi-Oct 映射、HDR 编码和运行时采样；地平线接缝应采用 footprint 滤波并与物理介质分层。
- [色带（Color Banding）与抖动（Dithering）知识](./color-banding-dither.md) - Tone Mapping 与有限位深输出的显示问题。

### 验证记录

- [2026-08-11] 完成独立静态复核并收窄证据等级：KernelSet 对象身份不再自证数学等价；Full-Exact 限定为线性 HDR/透射域的公式与容差合同；“三阶/四阶”改称 3/4 个经验补偿 lobe；partial-source baseline 明确为非 Full-Exact；地平线源码修改与用户侧视觉验收分开记录。
- [2026-08-11] 核验 R6.2、R6.3、R6.6、R6.10、R6.11、R6.13 固定快照的内嵌标题、介绍、执行路径与关键注释；确认 R6.3 已建立 front-air/cloud-air/back-air MRT 多 Pass，R6.6 已处理空间采样相位，R6.10～R6.11 发生夜间照云能力收放和地平线参数语义转移，R6.13 修复全尺寸/条带/取消式预览状态机。
- [2026-08-11] 计算现存快照 SHA-256，确认 R6.2 与 R6.6 的括号副本分别完全相同；确认名为 R6.7 的文件内嵌版本仍是 R6.6，因此不把它当作真正 R6.7 的直接证据。
- [2026-08-11] 对比 R6.19～R6.24 源码，确认从 Minimal/Compat/Full 三路径演化到七单元不可变 Canonical KernelSet；确认 R6.19～R6.22 在缺少浮点混合时会把正式 SPP 降为 1，R6.23～R6.24 改为 RGBA16F ping-pong 累计。
- [2026-08-11] Chromium localhost 实测完成声明为 Full-Exact 的七单元 KernelSet、Weather、含云渐进预览、真实视角拖动和 128²/2 SPP 正式烘焙；拖动视角时 revision 与 sampleCount 保持，未出现 context lost。该测试证明执行链可用，不单独证明拆分图数值等价，自动 oracle 仍待补齐。
- [2026-08-11] 强制禁用浮点混合扩展路径，确认 requested SPP 2、actual SPP 2，累计模式为 RGBA16F ping-pong running average；与浮点加法路径指标接近。
- [2026-08-11] R6.24 当前固定快照已在源码层修正银河公共 exposure 被平方的问题：方向源项先累加，transport 只乘一次 envelope；并已实现私有启动显示门禁、较浅近地介质和 footprint 驱动 Hemi-Oct 接缝。用户侧地平线观感与跨方向数值验收尚未完成，因此不把“宽亮带已视觉闭环”写成已验证事实。
- [2026-08-11] 带活跃 GLSL nonce 的 Chromium 冷编译约 22.6 秒；warm reload 中 display-only partial-source provisional 约 2.5 秒、完整 KernelSet 约 3.8 秒。该测量不外推到 Edge file:// 或其他 GPU。
- [2026-08-11] 尝试读取用户提供的 Main 决策会话时，应用接口连续返回错误；本文改用版本源码、当前会话决策与运行证据重建历史，并把会话逐轮复读列为未验证范围。
- [2026-08-11] 补读可访问的早期静态云烘焙器历史线程，加入真实 Dispatch/readback 门禁、源码指纹缓存失效、失败会话禁止标记 Completed，以及 coverage→vertical profile→detail erosion 的密度构造顺序；这些作为跨实现反例，不替代当前 WebGL 源码验证。

---

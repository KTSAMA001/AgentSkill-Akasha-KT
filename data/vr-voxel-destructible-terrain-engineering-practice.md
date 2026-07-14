# VR 体素可破坏地形工程实践与验证

**标签**：#unity #graphics #experience #vr #physics #collider #compute-shader #performance
**来源**：Nintendo 官方访谈与公开专利、GDC 开发者演讲、已上市游戏开发者资料、原始等值面算法论文、Unity 官方文档、成熟体素中间件/开源实现、Unity Editor 实验与用户现场复现
**收录日期**：2026-06-25
**来源日期**：1995-2026（公开资料）+ 2026-07-14（本地实验复核）
**更新日期**：2026-07-14
**状态**：🔬 实验性
**可信度**：⭐⭐⭐⭐（权威数据、碰撞一致性和公开算法边界有一手资料与 Editor 实验支持；Nintendo 商品精确实现、完整自适应内核和 Quest Android IL2CPP 性能仍未验证）
**适用版本**：Unity 2022.3+/Unity 6 的局部可破坏体积地形；Meta Quest、PCVR 和其他引擎需要分别做目标设备/物理后端验收

### 概要

平滑、可挖、支持洞穴的地形应把 Density/SDF 作为唯一权威状态；视觉、碰撞、碎屑清理、存档和网络都从同一 revision 派生。当前更可信的生产候选不是“先生成均匀高密三角网格再简化”，也不是半套 one-vertex-per-cell Dual Contouring，而是：细格拓扑与多分量候选 → Nintendo-style SVO 受约束合并 → 最终叶节点构面 → 完整几何审计 → 近场 Visual/Collider 同 revision 原子发布。Corrected MC33 适合作为细格拓扑 oracle 或稳健的非自适应替代主链；Transvoxel 只解决 2:1 LOD 接缝。Compute Shader 只有在渲染和碰撞都留在体积域时才能绕开 MeshCollider cooking；在 Unity PhysX MeshCollider 架构中，它不能直接消除主要碰撞成本。Quest 真机尚未验收，因此本记录保持实验性。

### 内容

## 1. 当前可复用结论

适合 VR 局部挖掘的系统边界是固定物理范围的 `DigVolume`，而不是默认把整张开放世界全部体素化。功能范围、采样精度、网格密度和碰撞覆盖必须分别表达：

```text
固定物理范围 DigVolume
  -> CPU Persistent Narrow-band Density + Material
  -> Brush CSG 修改 Density
  -> 第二物理范围内的 solid 连通域清理并写回 Density
  -> dirty micro-brick / Chunk 调度
  -> FineTopology + FineComponents
  -> 受约束 Adaptive Hierarchy
  -> Final Leaf Connector
  -> 几何与 Chunk seam 审计
  -> immutable SurfaceRevision
  -> 近场 Visual + Collider 共用最终几何
  -> Worker Collider Bake
  -> whole-dirty-batch 原子发布
```

核心原则：

- **Density/SDF 是唯一权威数据。** 不直接雕刻已发布 Mesh，也不让 Collider Mesh 反向成为几何事实源。
- **碎屑先在 Density 层处理。** 无价值小实体写空；有玩法价值的碎块显式转换为独立对象。
- **平面低面与拓扑正确分层处理。** 细格 topology 先正确表达多分量，再由层级合并决定哪些区域可以变粗。
- **Visual/Collider 的异步是计算异步，不是语义分叉。** 任一可见帧只能观察到完整旧 revision 或完整新 revision。
- **Collider locality 比独立降采样更优先。** 只在玩家、手、动态刚体和关键 AI 周围维护碰撞，远处可以没有 Collider。
- **Editor 指标只作相对回归。** Quest Android IL2CPP 的 p50/p95、热降频、队列积压和稳定帧率是独立验收门。
- **公开专利不是商品源码。** 可迁移其数据流和约束，不能宣称已一比一复原 Nintendo 的内部实现。

## 2. 公开证据分层

### 2.1 Nintendo 官方确认的商品事实

[Nintendo Ask the Developer](https://www.nintendo.com/jp/interview/aaaca/02.html) 明确确认《咚奇刚 蕉力全开》：

- 地形和敌人内部使用 voxel；目标是让玩家看不出方块感。
- 每个 voxel 可以带 material，material 关联外观与玩法性质。
- 地形可按 voxel 破坏，地下可以存在真实空腔。
- 三轴分辨率同时翻倍会带来约八倍数据/处理规模；Switch 2 的内存和处理能力使大体积地形与 60 FPS 目标成为可能。

官方访谈没有公开具体 polygonizer、Chunk 尺寸、线程模型、Compute Shader、Collider cooking 或发布事务。

### 2.2 Nintendo SVO 构网专利实施例

[US 12,597,199](https://patents.justia.com/patent/12597199) 公开的可迁移流程是：

1. voxel 保存 `0..255` Density，并用参考阈值区分实体和空气。
2. 跨越八个相邻 voxel 的细格同时含阈值两侧样本时，生成候选顶点。
3. 顶点可依据 XYZ Density 差插值，并结合预存或 Density 邻域求得的 normal。
4. 候选顶点进入 Sparse Voxel Octree；每级尝试合并相邻 `2×2×2` 顶点区域。
5. 合并必须检查形状误差、空腔保持、多顶点可表达性和材质兼容；不能用一个顶点表达的局部必须保留子节点。
6. 层级选择结束后，才连接最终叶节点形成三角形或四边形。
7. 编辑只更新发生变化的局部区域。

这里先生成的是候选顶点/层级记录，不是完整高密度三角 Mesh。专利没有出现 `Dual Contouring`、`QEF` 或 `MC33` 名称，因此不能把任意自适应 QEF 实现称为 Nintendo 算法复原。

### 2.3 判定 Mesh、小碎屑和玩法碎块

- 同一 SVO 专利允许 display mesh 与 determination mesh 读取相同层级数据；判定 Mesh 可以使用更宽误差，也可以与显示 Mesh 同形或只在玩家附近生成。它没有公开商品中的精确选级和原子发布实现。
- [US 2025/0242264](https://patents.justia.com/patent/20250242264) 公开在局部第二范围内检查实体连通性，以 voxel 数或 Density 总和判断小区域，确认不连接范围外主体后把对应 Density 写空再重建。
- [US 2025/0245929](https://patents.justia.com/patent/20250245929) 公开把有玩法价值的移除体积转为独立 sub-voxel object；可拆分、过滤过大/过小碎片，并在需要时写回主 voxel 数据。
- [US 2025/0242250](https://patents.justia.com/patent/20250242250) 把裂纹/痕迹作为可重新投影到当前地形的独立 polygon 层，说明表面视觉细节不必全部进入主拓扑或 Collider。

可复用分层：

```text
无玩法价值的小孤岛 -> Density 清空 -> Visual/Collider 一起消失
有玩法价值的碎块   -> 独立 sub-volume/object
裂纹、拳印、湿痕   -> 随地形重新投影的视觉覆盖层
```

## 3. 已上市案例与成熟实现

| 案例 | 公开架构 | 可迁移经验 | 不可直接推断 |
|---|---|---|---|
| Bananza | Density/material + 候选顶点 + 专利 SVO 约束合并 | 多分量不可表达时拒绝合并；同源层级；Density 层碎屑 | 商品精确 polygonizer、QEF、线程、Collider 参数 |
| Astroneer | signed Density → Marching Cubes → dirty Chunk | 修改 Density，不改 Mesh；局部重建；附近碰撞 | 任意自适应平面简化 |
| No Man's Sky | voxel region、LOD、后台 polygonize/physics/nav 流水线 | 边界 overlap、优先级、任务阶段分离 | 运行时挖掘的完整 DC/QEF 和原子发布 |
| Claybook | GPU 多级 SDF、稀疏 tile、直接 SDF 碰撞 | GPU/async compute 在体积域内有效 | 无改引擎条件下直接用于 Unity MeshCollider |
| Teardown | object-local voxel volume + GPU 体素渲染 + CPU voxel physics | 所有派生结构来自同一权威体积 | 换一个 Mesher 即可移植到 Unity |
| Minecraft/Bedrock | 离散 block + cube/empty/AABB collision | 拓扑稳定、低成本 | 平滑 Bananza 风格地形 |

### 3.1 Astroneer

[开发者公开说明](https://www.gamedeveloper.com/design/what-i-astroneer-i-s-devs-learned-while-leaving-early-access) 明确写出 signed Density、Marching Cubes、修改 voxel data、只对受影响 Chunk 重新 polygonize，并由结果生成可见几何和碰撞。[官方多人技术文章](https://blog.astroneer.space/p/day-1-multiplayer-and-beyond/) 说明只为玩家附近地形生成碰撞。

这是最清晰的已上市 correctness baseline：稳定 polygonizer、局部 Chunk 和碰撞空间范围控制可以独立于“平面尽可能少面”的目标。

### 3.2 No Man's Sky

[Hello Games GDC 演讲](https://www.gdcvault.com/play/1024265/Continuous_World_Generation_in__No_Man_s_Sky_) 展示从 voxel density、polygonization 到 physics mesh、navmesh 和内容布置的后台流水线，以及区域/LOD/边界处理。值得复用的是边界输入一致、阶段化 Job、距离和粗细优先级；公开资料不足以证明某个自研 DC 变体天然无洞或适合当前 Unity 动态 Collider。

### 3.3 Claybook 与 Teardown

[Claybook GDC 技术资料](https://media.gdcvault.com/gdc2018/presentations/Aaltonen_Sebastian_GPU_Based_Clay.pdf) 公开多级 8-bit SDF、稀疏 `8×8×8` tile、indirect dispatch、async compute 以及对 UE WorldCollision 的直接 SDF 碰撞修改。它说明 GPU 获益最大的前提是避免把权威结果回读成 CPU 三角 Mesh。

Teardown 作者公开的[权威体素状态](https://blog.voxagon.se/2020/11/18/teardown-quicksave.html)和[体素渲染结构](https://blog.voxagon.se/2018/10/17/from-screen-space-to-voxel-space.html)支持“一个权威 voxel volume，渲染/物理/剔除结构均可重建”的原则，但其自研渲染与物理不能等价为 Unity 插件式 Mesher 替换。

### 3.4 Godot Voxel Tools 与 Voxel Plugin

[Godot Voxel Tools](https://github.com/Zylann/godot_voxel) 是可审计的成熟参考。其[平滑地形文档](https://voxel-tools.readthedocs.io/en/latest/smooth_terrain/)采用 SDF 和 Transvoxel；`VoxelLodTerrain` 公开 `16/32` voxel mesh block、collision LOD、collision update delay、threaded update、GPU generation 和 visual/collision block 调试。它证明 micro-brick、LOD transition 和碰撞调度应作为独立工程层。

[Voxel Plugin runtime sculpting 文档](https://docs.voxelplugin.com/knowledgebase/blueprints/runtime-edits-and-sculpting) 把当前运行时雕刻明确标为实验性，区分同步 hitch 与异步可见延迟，并说明尚不支持自动检测/掉落悬空碎块。[Collision/Navmesh Invokers](https://docs.voxelplugin.com/knowledgebase/blueprints/collision-navmesh-and-invokers) 只在 invoker 周围生成碰撞和导航。这说明成熟中间件也没有一个算法自动覆盖构网、Collider、碎块、网络和存档。

### 3.5 证据不足的产品

Animal Company、Deep Rock Galactic 等产品可以证明某种可破坏表现存在，但未找到足够一手 Density、polygonizer、Collider 和线程资料。不得从画面反推它们采用 SDF、Marching Cubes、Dual Contouring 或 MeshCollider。

## 4. 等值面算法保证边界

“闭合”“2-manifold”“与插值场拓扑一致”和“几何无自交”不是同一性质。

| 算法 | 闭合/裂缝 | 2-manifold/拓扑 | 无自交 | 直接自适应 | 适用判断 |
|---|---:|---:|---:|---:|---|
| Corrected MC33 | 条件保证 | 与 regular 三线性等值面一致 | 在一致、非退化输入下较强 | 否 | 稳健细格 oracle/非自适应主链 |
| Transvoxel | 只保证 2:1 LOD transition | 继承基础构面器 | 无独立保证 | 仅离散 LOD | 接缝层，不是通用修洞算法 |
| Uniform Surface Nets | 条件成立 | 多分量不保证 | 不保证 | 否 | one vertex per cell 有复杂局部限制 |
| 原始 Adaptive DC | 论文目标为 crack-free | 可非流形/改拓扑 | 不保证 | 是 | 不能直接当生产完整保证 |
| Manifold DC | 闭合 | 满足完整条件时 2-manifold | 论文明确仍可相交 | 是 | 需要完整 cycles/vertex tree/Euler 门 |
| Intersection-Free Octree Contouring | 是 | 一般多分量能力受限 | 保证 | 是 | 单顶点 cell 限制，不能与 MDC 保证直接相加 |
| Nintendo SVO 专利实施例 | 商品表现支持，专利未给形式证明 | 提供空腔/多顶点门 | 未给形式证明 | 是 | 需要项目自行验证 connector 与几何嵌入 |

### 4.1 Corrected MC33

[2019 Corrected MC33](https://jcgt.org/published/0008/03/01/paper.pdf) 使用正确 face/interior tests，使每个 Cell 输出与三线性插值等值面拓扑一致。保证依赖：

- 相邻 Cell/Chunk 使用完全相同的边界 Density。
- `density == iso` 有全局一致 tie policy。
- 共享边交点有确定性插值与 owner 规则。
- 输入为 regular、非退化情形。
- 使用正确内部测试；不能直接采用已知存在 `10.1`、`13.5.2` 错误的旧实现/LUT。

MC33 不会自动降低平面三角密度。它解决的是细格可靠性，不是自适应。

### 4.2 Adaptive 与 Manifold Dual Contouring

[Dual Contouring of Hermite Data](https://www.cs.rice.edu/~jwarren/papers/dualcontour.pdf) 确实能先在 Octree 上聚合 Hermite/QEF、最后生成自适应结果，不必先生成完整高密三角 Mesh。但原始算法可能非流形、改变拓扑，QEF 顶点也可能越出合法局部体积。

[Manifold Dual Contouring](https://people.engr.tamu.edu/schaefer/research/dualsimp_tvcg.pdf) 不是给普通 DC 增加几个检查：它需要细层完整 topology cycles、同 Cell 多分量/多顶点、独立 vertex tree、自底向上聚类、Euler characteristic 与 Cell 边交点约束。论文可证明闭合 2-manifold 和 genus 条件，但仍明确承认可能有相交多边形。

因此，半套 single-owner DC/QEF 即使固定轨迹 `open=0`，也不能据此宣称多分量、无翻折或无自交。

### 4.3 Transvoxel

[Transvoxel](https://transvoxel.org/) 用 transition cells 连接分辨率相差 2 倍的相邻区域。它不解决：

- 基础 Marching Cubes 的 Cell 内部歧义。
- 不同 Density revision 混合发布造成的时域裂缝。
- 同一 LOD 内平面三角形过密。
- 基础算法的流形或无自交问题。

## 5. 推荐的单一生产候选

### 5.1 模块职责

```text
DensityAuthority
  -> DensityConnectivityCleanup
  -> FineTopology
  -> FineComponents
  -> AdaptiveHierarchy
  -> LeafConnector
  -> CandidateValidator
  -> SurfaceRevision
  -> ColliderBake
  -> BatchPublisher
```

- **DensityAuthority**：Persistent narrow-band Density/material、Brush、halo、revision 和存档/网络事实源。
- **DensityConnectivityCleanup**：只处理实体连通域；触碰搜索边界或预算截断时保守保留。
- **FineTopology**：用 corrected MC33 规则/测试 oracle 判定细 Cell 的 face/interior topology；不在生产中生成第二套 fallback Mesh。
- **FineComponents**：同一 Cell 每个独立表面分量拥有独立 cycle、Hermite 约束和候选，禁止静默压成单 owner。
- **AdaptiveHierarchy**：Nintendo-style SVO 自底向上 collapse；误差、空腔、多分量/多顶点可表达性、边界交点和材质任一失败即保留子节点。
- **LeafConnector**：只从最终叶和组件连接表面；跨层/跨 Chunk 规则必须确定且可验证。
- **CandidateValidator**：发布前统一检查组合拓扑、几何嵌入、Density 方向、Chunk seam 和容量。
- **SurfaceRevision**：不可变最终顶点/索引/材质/hash；Visual/Collider 从同一对象派生。
- **BatchPublisher**：整个 dirty-set 完成和 Collider bake 后，在同一安全点原子切换。

### 5.2 为什么 MC33 是 oracle 而不是兼容分支

细格 MC33 可以回答“同一三线性 Cell 中有哪些表面分量和连接关系”，为自适应 collapse 提供正确基线。运行时同时保留 MC33 Mesh 和自适应 Mesh 会形成两套生产路径、不同性能和失败语义，因此不推荐把它作为每个 Chunk 的动态 fallback。

候选自适应内核失败时，应继续显示上一份合法 SurfaceRevision，并记录失败语料；不能删掉失败三角，也不能临时切换旧高密算法掩盖缺陷。如果自适应路径长期无法通过门槛，应整体替换为唯一的 `corrected MC33 + micro-brick + 2:1 balanced LOD/Transvoxel` 主链。

## 6. Visual 与 Collider 一致性

### 6.1 近场合同

默认采用比公开专利最低要求更严格的近场语义：

```text
ActiveSurface(N) = Visual(N) + Collider(N)

PendingSurface(N+1):
  build/validate final geometry
  -> upload visual and collider from same vertex/index stream
  -> worker bake collider
  -> preflight entire dirty batch
  -> atomic publish all members
```

- 等待新 revision 时继续使用完整旧 pair。
- 新 Brush 产生更新 revision 时，可取消过时候选，但不能拆开已经发布的 pair。
- 空 Chunk 同时关闭 Renderer 与 Collider。
- 逐 Chunk pair 相等仍不够；还必须检查 pair 是否落后权威 Density，以及同一 edit 的全部 dirty members 是否整体提交。

### 6.2 远场与更简 Collider

优先选择“远处无 Collider、近处同几何”，而不是“全世界维护独立低精度 Collider”。

只有目标设备证明近场同几何仍超预算时，才研究从同一 SVO revision 选更粗判定叶；必须同时满足：

- 双向表面距离/最大误差有明确上限。
- 空腔、洞口、薄壁、材质/玩法边界不丢失。
- 可通行性和抓取/接触语义有回归测试。
- Visual/Collider revision 和 dirty-batch 仍原子一致。

固定 `colliderSampleStep > 1` 的独立 polygonization 会改变拓扑和完成进度，不作为默认方案。

## 7. Collider 性能策略

[Unity `MeshCollider.sharedMesh`](https://docs.unity3d.com/2023.2/Documentation/ScriptReference/MeshCollider-sharedMesh.html) 说明顶点、索引或三角改变后碰撞形状会重建。[Unity Mesh cooking 指南](https://docs.unity3d.com/Manual/physics-optimization-cpu-mesh-cooking-options.html) 建议使用低面、闭合、干净、无退化的 Mesh，并说明 cooking time 与运行时查询性能存在取舍。

优化顺序：

1. 将重构和碰撞单元拆为可独立更新的 `8³`/`16³` micro-brick，实际尺寸由目标设备 p95 决定。
2. 只在 player/tool/dynamic-body physics bubble 内维护 Collider。
3. 合并连续笔刷的 dirty bricks，取消过时候选。
4. 复用 Mesh、Native 和 scratch 缓冲；使用 Worker `Physics.BakeMesh` 与 A/B Collider。
5. 主线程只执行最短的最终提交，不在每个 Job 完成时逐块切换可见状态。
6. 输入几何永久通过清洁度回归前，不通过关闭 cleaning/welding 掩盖坏三角。

Collider cooking 是独立成本域。三角减少不自动等于 bake 峰值解决；必须分别记录 meshing worker、upload、bake、main-thread swap、端到端 latency 和队列积压。

## 8. 多线程与时域分帧

推荐流水线：

```text
Brush + Density cleanup
  -> dirty brick classify/count
  -> FineTopology/FineComponents
  -> SVO merge
  -> prefix/emit final geometry
  -> geometry validation
  -> visual upload
  -> collider bake
  -> atomic batch publish
```

可并行的工作：

- 不相邻或输入 snapshot 固定的 dirty bricks。
- active-cell classify/count、候选生成、部分层级误差计算。
- 多个独立 Collider mesh 的 worker bake（不得并发 Bake 同一个 Mesh）。

必须串行或有明确 barrier 的工作：

- Density cleanup 完成后才能取得该 revision 的 meshing snapshot。
- 跨 brick/Chunk 的共享边界与层级 ownership 决策。
- 整批 preflight 与 active pair 交换。

连续动作可以跨多个游戏帧修改 Density，后台构建也可以跨帧；“分帧”不能解释为发布一半 Mesh 或让 Collider 追赶 Visual。即时反馈可以使用粒子、遮罩、裂纹覆盖层和工具动画，但正式地形几何仍等待完整 SurfaceRevision。

## 9. Compute Shader 的适用边界

适合 GPU 的阶段：

- Density brush mirror 或大量 brush 批处理。
- active-cell classify/count、prefix scan、visual emit。
- normal/material baking、远场 culling、indirect draw。
- 纯视觉预览、粒子、痕迹或 debug volume。

在 Unity MeshCollider 架构中，正式 GPU 网格仍需：

```text
GPU mesh -> AsyncGPUReadback -> CPU Mesh -> Physics.BakeMesh -> MeshCollider
```

这保留了最贵的 PhysX cooking，并增加 GPU/CPU revision 同步与移动端带宽。Compute Shader 不提供拓扑正确性，也不自动降低平面三角密度；这些性质仍由所选构面算法决定。

只有项目愿意采用 Claybook/Teardown 类直接 SDF/voxel collision，并接受自定义物理/引擎集成时，GPU resident 权威体积才可能真正绕开 MeshCollider cooking。该路线属于独立架构项目，不是当前 Mesher 优化开关。

## 10. 参数与 GUI 语义

面板应先指定功能物理范围，再独立配置精度：

- **体积中心/尺寸（m）**：决定可挖功能范围。
- **采样 Cell 数或每米采样数**：只改变 `cellSize`、细节能力、内存和构网成本，不改变体积尺寸。
- **micro-brick/Chunk Cell 数**：只改变重建和调度粒度。
- **最大层级叶尺寸（m）**：限制平坦区域可合并到的物理尺度，不改变 Brush 或 DigVolume 范围。
- **几何误差（m）**：层级 collapse 的软画质阈值。
- **空腔、多分量、边界、材质门**：正确性硬约束，不是可任意关闭的画质选项。
- **碎屑搜索 padding（m）、最大 extent（m）、最大体积（m³）**：物理语义独立于采样精度。
- **每帧调度预算**：只改变候选完成时间，不改变最终几何判定。

GUI 应显示派生值：Cell Size、总样本/内存、brick 数、当前/待发布 Density revision、Visual/Collider revision、authority lag、各队列长度、Raw/Final/Collider 三角、Worker/Main/Wall/Bake 的 last/median/p95，以及 `Editor Relative` 或 `Quest Device` 证据徽标。

## 11. 必须通过的正确性门

### 11.1 细格与层级

- MC33 `256` masks、符号反转、旋转、`10.1`、`13.5.2` 和退化 tie policy。
- 同一 fine Cell 内多个独立表面分量拥有独立 cycle/候选。
- 每次 SVO collapse 验证误差、空腔、边界交点、组件数量/可表达性和 material。
- 相邻 Chunk 使用相同 Density revision、halo、共享边插值和 owner 规则。

### 11.2 最终几何

每个候选必须检查：

- `open edge = 0`
- `nonmanifold edge = 0`
- `winding mismatch = 0`
- `duplicate/degenerate triangle = 0`
- `vertex-link` 每个闭合顶点恰为一个简单环
- 非相邻三角 `proper intersection = 0`
- 共面正面积 overlap = 0
- Density 两侧方向和 iso 距离在定义容差内
- Chunk seam/T-junction = 0

候选失败时整 revision 拒绝；禁止删掉失败三角后继续发布。

### 11.3 时域与真实失败语料

- 同步和异步构建得到确定性 geometry hash。
- 连续快速 Brush、worker 延迟、候选取消和 revision supersede 下，不出现 partial dirty-set commit。
- 任一帧 Visual/Collider pair 相同，最终 authority lag 回到 0。
- 固定短轨迹之外必须有 seeded randomized/fuzz Density 场。
- 用户真实失败必须保存为可重放 Density snapshot/Brush sequence，而不是只保存输出四边形或错误日志。

## 12. 性能证据合同

Editor 达标不等于 Quest 达标。正式性能报告至少包括：

- Unity/Player 版本、Android IL2CPP、Development/Release 形态、Burst/Safety Checks。
- 目标设备、刷新率、render scale、foveation、温度和是否降频。
- Density edit/cleanup、FineTopology、Hierarchy、emit、upload、Collider bake、swap 的 Main/Worker/Wall 分类。
- p50/p95/p99、最大帧尖刺、每秒 Brush 次数、dirty brick 数和队列积压。
- Visual/Collider 三角、authority lag、stale discard、failed revision、原子 commit 次数。
- GC Alloc、内存峰值、热稳定 60 秒以上连续挖掘。
- Unity Profiler 与 Meta 系统级指标（FPS、CPU/GPU frame time、stale frame、throttling）。

Quest 2/Pro 先验收 72 Hz，Quest 3/3S 再评估 90 Hz。具体毫秒和三角预算应由目标内容基线反推，不把通用建议伪装成平台官方硬阈值。

## 13. 路线选择门

### 路线 A：Nintendo-style SVO 自适应主链

适用：必须同时获得平面低面、洞口/曲率按需细化和隐藏体素感。

进入条件：完整 FineComponents、受约束 collapse、LeafConnector、几何审计和随机回归均已实现。不能用部分 DC/QEF 先接 Runtime 再持续补洞。

### 路线 B：Corrected MC33 + micro-brick + 2:1 LOD

适用：无洞与可预测性优先于任意平面减面。

特点：公开实现和拓扑证据更强；平坦区只能按 block/LOD 粒度降密，跨 LOD 使用 Transvoxel。若路线 A 无法在门槛内成立，应整体切换为这条唯一主链。

### 路线 C：离散 Block/AABB

适用：Quest 性能和稳定性绝对优先，玩法可以接受块状/量化美术。

### 路线 D：直接 SDF/voxel collision

适用：愿意替换渲染/物理架构，并对 GPU/CPU 体积查询、角色移动、刚体接触和网络重新立项。不能当作现有 Unity MeshCollider 的局部优化。

## 14. 已否决或收窄的旧路线

<details>
<summary>历史路线与否决原因</summary>

- **Indexed Marching Tetrahedra + 后置 QEM/Adaptive Final 作为当前生产主线**：先付出均匀高密网格生成/内存成本，再简化；真实动态路径曾出现破洞和候选失败。只保留为历史实验，不继续作为当前推荐。
- **半套 Direct Adaptive single-owner DC/QEF**：固定回归可以通过，但复杂 multi-component/owner face 仍可能发生 Density 方向拒绝或几何翻折；缺少完整 MDC 与无自交保证。停止追加局部阈值、法线代理、坐标特判和单三角修补。
- **Visual 高精度 + Collider 固定步长独立降采样**：会生成两套拓扑和两条完成进度，造成隐形碰撞、视觉孤岛或悬浮碎片。
- **失败时回退旧高密 Mesher**：让正确性和性能合同随输入变化，掩盖主内核失败；不保留运行时兼容分支。
- **在 Mesh 后删除小连通片**：不能可靠判断体积范围外连接，也会使视觉/碰撞各自判断；改为 Density 层连通清理。
- **Compute Shader 直接解决 Collider 大头**：GPU readback 后仍需 CPU Mesh 和 PhysX cooking，增加同步而不消除瓶颈。
- **编辑器刚好达到刷新率即算完成**：真机 Android IL2CPP、热降频和移动 PhysX 数据未知，不能通过 Editor FPS 宣称可用。

</details>

## 15. 主要参考来源

- [Nintendo Ask the Developer：voxel、material、Switch 2](https://www.nintendo.com/jp/interview/aaaca/02.html)
- [Nintendo US 12,597,199：Density、候选顶点、SVO 合并与判定 Mesh](https://patents.justia.com/patent/12597199)
- [Nintendo US 2025/0242264：小实体 Density 清除](https://patents.justia.com/patent/20250242264)
- [Nintendo US 2025/0245929：独立 sub-voxel 碎块](https://patents.justia.com/patent/20250245929)
- [Astroneer：Density、Marching Cubes 与 dirty Chunk](https://www.gamedeveloper.com/design/what-i-astroneer-i-s-devs-learned-while-leaving-early-access)
- [No Man's Sky：Continuous World Generation](https://www.gdcvault.com/play/1024265/Continuous_World_Generation_in__No_Man_s_Sky_)
- [Claybook：GPU-based clay simulation and ray tracing](https://media.gdcvault.com/gdc2018/presentations/Aaltonen_Sebastian_GPU_Based_Clay.pdf)
- [Godot Voxel Tools：SDF 与 Transvoxel](https://voxel-tools.readthedocs.io/en/latest/smooth_terrain/)
- [Corrected MC33 2019](https://jcgt.org/published/0008/03/01/paper.pdf)
- [Dual Contouring of Hermite Data](https://www.cs.rice.edu/~jwarren/papers/dualcontour.pdf)
- [Manifold Dual Contouring](https://people.engr.tamu.edu/schaefer/research/dualsimp_tvcg.pdf)
- [Transvoxel](https://transvoxel.org/)
- [Unity MeshCollider sharedMesh](https://docs.unity3d.com/2023.2/Documentation/ScriptReference/MeshCollider-sharedMesh.html)
- [Unity MeshCollider cooking optimization](https://docs.unity3d.com/Manual/physics-optimization-cpu-mesh-cooking-options.html)

### 相关记录

- [SDF（有向距离场）知识](./sdf-signed-distance-field.md) - Density/SDF 表达、插值和 CSG 基础。
- [ComputeShader GPGPU 基础概念](./compute-shader-gpgpu-basics.md) - Compute Shader 线程模型、Buffer 与调度基础。
- [GPU 视锥剔除 ComputeShader 实现](./gpu-frustum-culling-compute-shader.md) - classify/append/indirect 工作流经验。
- [Unity 3D Collider 类型性能消耗对比](./unity-collider-types-performance.md) - MeshCollider 与 primitive/compound collider 性能边界。
- [移动端 TBDR 与 Overdraw](./mobile-tbdr-overdraw.md) - Quest/移动 GPU 带宽和过绘约束。

### 验证记录

- [2026-06-25] 初次记录：形成局部 DigVolume、CPU 权威 Density、Brush、异步构网与碰撞代理的早期方案；当时的独立低分辨率 Collider 建议后来被实际一致性问题否决。
- [2026-07-13] 第一次重大修正：引入 Density 层小实体连通清理、Visual/Collider exact pair、revision 成对发布和 Nintendo 专利证据边界；状态改为实验性，Quest 真机仍未验收。
- [2026-07-14] 第二次重大修正（正确性/时效性/来源性/完整性/结构一致性）：用户真实连续挖掘证明旧的后置 Adaptive 与半套 Direct Adaptive 路线即使固定 Editor 回归通过，仍可能发生 owner 连接/Density 方向失败。结合 Nintendo SVO 专利、Astroneer/No Man's Sky/Claybook/Teardown、Godot Voxel Tools，以及 MC33/DC/MDC/Transvoxel 原始资料，将推荐主线改为 `FineTopology → FineComponents → 受约束 SVO Hierarchy → LeafConnector → CandidateValidator → immutable SurfaceRevision → 原子 Visual/Collider publish`。旧 MT/QEM、半套 DC、独立 Collider 降采样和 GPU readback 主链降为已否决历史。此次修正完成语义脱敏：未记录真实项目名、本机路径、内部场景/对象标识、提交哈希、用户日志原文或凭据；仅保留可复用的通用故障模式和公开来源。Quest Android IL2CPP 仍未验证，因此状态保持 `🔬 实验性`。

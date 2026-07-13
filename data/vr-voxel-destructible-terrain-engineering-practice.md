# VR 体素可破坏地形工程实践与验证

**标签**：#unity #graphics #experience #vr #physics #collider #compute-shader #performance
**来源**：方案调研 + Unity 本地实验 + Nintendo 官方访谈 + GDC 官方议程 + Nintendo 公开专利 + Unity/Meta/Unreal 官方文档 + RelicVR 论文
**收录日期**：2026-06-25
**来源日期**：2025-2026（公开资料）+ 2026-07-13（本地实验复核）
**更新日期**：2026-07-13
**状态**：🔬 实验性
**可信度**：⭐⭐⭐⭐（公开专利/官方资料支持公开设计方向，Unity 2022.3 Editor 实验支持本地工程结果；Quest Android IL2CPP 真机性能仍未验收）
**适用版本**：Unity 2022.3.62f3 Editor 已做相对回归；Unity 2022.3+/Unity 6、URP/Meta Quest 与 Unreal Engine 5.x 的生产适用性仍需按目标平台验证

### 概要

VR 中实现局部地面自由挖掘的当前推荐架构是“固定物理范围的局部 DigVolume + CPU 权威 density/SDF + Brush 后第二范围 solid 连通清理写回 + Dirty Chunk 异步重建 + 拓扑/几何约束的自适应 Final Surface + Visual/MeshCollider 同源同 revision 成对发布”。Brush/预览可以读取最新 SDF；玩家、普通刚体和可见接触默认遵循 ActivePair，不能用 SDF 掩盖视觉与碰撞不一致。该路线已完成 Unity Editor 正确性与相对性能闭环，Quest 真机仍待验收。

### 内容

## 1. 结论摘要

游戏内实现“地面可以随意挖，挖掉的地方不能有碰撞”是可行的。高性能路线不是全地图体素化，而是：

```text
静态大地形 / 静态关卡 Mesh
    +
局部 DigVolume 可挖区域
    -> 分块 CPU 权威 density/SDF
    -> Brush CSG 修改体素密度
    -> 在包含 Brush 的第二范围内清除已确认独立的小型 solid 连通分量，并写回同一 density
    -> 合并 dirty bounds，按 Chunk/微砖分帧调度
    -> Indexed Raw Surface
    -> 拓扑、几何、空腔与材质约束下的 Adaptive Final Surface
    -> Collider worker bake/cook
    -> Renderer 与 MeshCollider 使用同一 Final Surface、同一 revision 成对发布
    -> Brush/预览读取权威 SDF；普通物理与可见接触遵循 ActivePair
```

核心设计原则：

- **CPU 侧 density/SDF 是唯一权威数据**。Brush 与小实体清理都先提交到它；存档、网络同步、查询和后续网格都从同一 revision 派生。
- **默认禁止独立固定步长的碰撞降采样**。它会让洞口、薄壁、孤岛和重建进度产生不同拓扑；采样步长为 1 时问题消失，正是这种分叉的直接证据。
- **Visual 与 MeshCollider 共享 Final Surface**。可以是两个 Mesh 对象，但其顶点/索引流和 revision 必须一致，并在 collider bake 完成后成对切换。
- **三角形按几何需要分配**。均匀 voxel 采样不等于均匀最终三角密度；平坦区应通过受约束简化或层级候选大幅合并，曲率、薄壁、洞口和材质边界保留细节。
- **SDF 即时查询是编辑/预览层补充，不是双权威**。发布等待期继续显示并碰撞旧的一致表面对；若某个 SDF 查询会否决仍可见的 ActivePair，必须同时有匹配的过渡视觉，否则应等待 Pair 提交。
- **MVP 不强依赖 Compute Shader**。先用 CPU Jobs/Burst/TaskGraph 跑通正确性；Compute Shader 放在第二阶段做视觉加速。
- **Nintendo 资料需要分层引用**。官方访谈/GDC 只证明《咚奇刚 蕉力全开》的体素破坏方向；公开专利提供“小 solid 写空”和“SVO 约束简化”的可参考实施例，但不能等同于成品全部内部代码。
- **Animal Company/AC 只能作为“Quest VR 沙盒可承载复杂交互”的产品信号**，没有公开证据证明其挖掘实现具体使用体素/SDF/Marching Cubes。更直接的公开案例是 RelicVR，它明确使用 dynamic voxel deformation 做 VR 挖掘交互。

## 2. 调研与验证边界

本次使用了多个子 Agent 并行分析：

- 算法与数据结构 Agent：比较 heightfield、2.5D、density/SDF、Marching Cubes、Surface Nets、Dual Contouring、Transvoxel、Sparse Voxel。
- 动态碰撞 Agent：专门分析“挖掉后不能有碰撞”的实现、Unity/Unreal 动态碰撞 API 与风险。
- Compute Shader/GPU Agent：判断哪些阶段适合 GPU，哪些不能依赖 GPU readback。
- Unity 工程 Agent：给出 Unity 模块、Jobs/Burst、MeshData、MeshCollider、URP/Quest 工程规划。
- Unreal 与案例 Agent：给出 Unreal 组件路线、Nanite 判断，以及 AC/RelicVR/Teardown/Deep Rock 等案例边界。

阿卡西本地检索结果：

- 未命中“VR 体素地面挖掘完整方案”的直接记录。
- 命中可迁移记录：`SDF`（有效）、`ComputeShader GPGPU`（有效）、`GPU 视锥剔除`（有效）、`Unity Collider 性能`（有效，Unity 2022.3）、`移动 TBDR/Overdraw`（有效）、`VR 变体收集`（有效）。
- 命中一条需要维护的记录：`Unity 动态分辨率与注视点渲染冲突` 当前状态为待验证，适用版本是 Unity 2022.3.39f1。外部 Meta 文档显示当前 Dynamic Resolution 可与 Dynamic Foveated Rendering 配合使用，因此该记录应收窄为“Unity 2022.3.39f1 版本特例/待复核”，不能泛化为当前结论。

### 2.1 2026-07-13 外部资料复核

- Nintendo 官方开发者访谈明确说明《咚奇刚 蕉力全开》内部以 voxel 表达地形/敌人，每个 voxel 带材质，地形可逐 voxel 破坏；这证明产品方向，不公开碰撞、线程或阈值。
- Nintendo 的公开专利申请 `US2025/0242264` 描述：事件先更新第一范围，再在至少包含第一范围的第二范围内识别小型连续 present-voxel 区域，把它写成 absent，随后只对受影响范围/Chunk 重建 mesh。可迁移原则是“在权威体数据层删除独立小实体”，不是在生成后的 Mesh 上筛碎屑。
- Nintendo 授权专利 `US 12,597,199` 描述：从同一 SVO/层级顶点候选生成显示与判定用网格，简化候选受几何误差、空腔保持和材质条件约束；判定网格可以更简，也允许与显示网格同形。它支持“同源层级候选”的方向，但不要求两者必须完全相同。
- GDC 官方议程只公开“把 voxel tech 与 destruction gameplay 融合”的主题，未公开 SVO、连通清理、Collider cooking、Compute Shader 或线程细节。
- 专利是公开实施例，不是成品完整源代码。下文的 Marching Tetrahedra、受约束 QEM、成对发布、物理阈值与分帧调度属于本地工程落地，不归因于 Nintendo。

### 2.2 2026-07-13 Unity Editor 实验复核

实验路径：

```text
CPU 权威 density
  -> Brush + 第二范围 solid 连通清理写回
  -> Indexed Marching Tetrahedra Raw Surface
  -> 拓扑/几何受约束 Adaptive Final Surface
  -> 相同 vertex/index stream 上传 Visual 与 Collider
  -> Worker Physics.BakeMesh
  -> revision 仍为最新时成对发布
```

已验证的正确性范围：

- Unity `2022.3.62f3` Windows Editor，Active Build Target 为 Android；Burst 与 Safety Checks 均开启。
- 进度记录报告全部 `21/21` NUnit cases 通过；源码确认存在 21 个 cases，覆盖 density 小实体清理、空气洞保持、触界延后、预算截断、确定性、Raw Burst 与 Adaptive 拓扑门控。此次知识复核没有重新执行测试，因此不把它写成独立复跑证据。
- Core SelfCheck 报告通过，逐顶点/逐索引校验 Visual/Collider exact pair，并覆盖 cleanup 写回、dirty bounds 扩张与空气洞保持。
- Play Mode 可见沟槽观测为 Visual/Collider `10,212/10,212`，revision gap/mismatch 为 `0`；着色线框未观察到主表面意外开放孔。

v8 Editor 相对基准（Debug + Safety Checks，不代表 Quest 帧率）：

| 项目 | 结果 | 边界 |
|---|---:|---|
| Density cleanup 直接 fixture | `0.0345 ms`，扫描 `1,859` samples | 删除 1 个组件/2 个 samples，bounds 扩张、空气洞保持、截断 0 |
| Raw Burst | `2,048` tris，median/p95 `0.8427/1.1931 ms` | 24 次直接 Job 测量 |
| Adaptive Final | `2,048 -> 922` tris，减少 `54.98%` | pipeline median/p95 `4.4486/5.7883 ms`，fallback 0 |
| Runtime 最近一次 cleanup | `1.0659 ms / 7,200 samples` | 单次最近值，不是 p95；截断 0 |
| Runtime 最近 Chunk Raw/Final | `6,640 -> 2,656` tris，减少 `60%` | 接受 1,992 次 collapse |
| Runtime Visual/Collider 总三角 | `10,414/10,414` | revision gap/mismatch/fallback 均为 0 |
| Worker collider bake 最近值 | `0.7283-0.8989 ms` | Windows Editor PhysX 数据，不能外推 Quest |
| 同步压力生命周期墙钟 | median/p95 `87.4084/90.2342 ms` | 不是单帧 CPU 时间，表明仍必须分帧/异步 |

未验证范围：

- Quest Android IL2CPP 真机连续挖掘、72/90 Hz、发布延迟、PhysX bake p95/p99、温升/降频与 release-shaped OVR Metrics。
- Editor 当前线程 `0 managed bytes/iteration` 不能证明 IL2CPP Player 稳态零 GC。
- 严格双向 Hausdorff 包络、全局自交检测、薄壁 clearance 与全部复杂近接面仍未完成验证。

## 3. 需求与非功能指标

### 3.1 功能需求

- 支持玩家用手柄、铲子、钻头、爆破等 Brush 在局部区域挖地。
- 挖掉的地方必须能穿过、不能继续产生旧碰撞。
- 支持洞口、侧壁、下切、坑、短隧道等 3D 形态。
- 支持不可挖边界、岩层、底部限制，避免玩家挖穿玩法区域。
- 支持存档与多人同步；网络同步 Brush 操作或 chunk delta，不同步最终 mesh。
- 支持调试可视化：density/cleanup、dirty chunk、active/pending Pair revision、队列耗时、Raw/Final 三角数与 pair mismatch。

### 3.2 性能目标

| 项目 | Quest 2/Pro | Quest 3/3S | PCVR |
|---|---:|---:|---:|
| 推荐帧率 | 72Hz 起步 | 90Hz 目标 | 90Hz 默认 |
| 总帧时间 | 13.9ms 内 | 11.1ms 内 | 11.1ms 内 |
| 挖掘系统平均 CPU | 0.5-1.0ms | 0.8-1.5ms | 1.5-3.0ms |
| 单帧尖刺 | 尽量小于 2ms | 尽量小于 2ms | 避免 VR hitch |
| 视觉 chunk apply | 每帧 1 个 | 每帧 1-2 个 | 4-8 个可测 |
| Surface Pair 发布 | 停笔后 p95 ≤200ms（实验目标） | 停笔后 p95 ≤200ms（实验目标） | 以目标项目实测为准 |

Meta 文档给出的 Quest 交互应用最低目标是 72 FPS；Quest 2/Pro 中等场景 draw call 参考范围约 200-300，Quest 3/3S 中等场景约 400-600；三角量 Quest 2/Pro 约 750k-1m，Quest 3/3S 约 1.3m-1.8m。可挖地形不应吃掉全部预算，建议只占总三角预算的 20%-40%。上表中的挖掘系统和 Pair 发布预算是工程目标，不是 Meta 官方阈值；必须由目标 Quest 的 Android IL2CPP Player 验收。

## 4. 算法选型

| 方案 | 适用性 | 判断 |
|---|---|---|
| Unity Terrain / Unreal Landscape heightfield | 低 | 只适合高度变化，不能表达洞穴、悬挑、横向掏空。Unity `SetHeights/SetHoles` 还会触发 Terrain LOD/植被相关重算，不适合高频 VR 挖掘。 |
| 2.5D depth/holes | 中 | 可以低成本做浅坑假象，但碰撞和侧壁都需要额外代理；适合小玩法，不适合“真自由挖”。 |
| Occupancy voxel | 中 | 数据简单，但边缘粗糙，法线和材质过渡差。方块风格可用，不推荐作为自然泥土首选。 |
| 3D density/SDF | 高 | 推荐主路线。能表达任意 Brush CSG、洞口、侧壁和下切；能从梯度计算平滑法线。 |
| Marching Cubes | 参考/MVP 备选 | 实现资料多、快速闭环；缺点是三角数偏多，锐边和拓扑质量需要约束。不是当前实验的生产主线。 |
| Indexed Marching Tetrahedra | 当前 Raw Surface | 容易建立稳定索引与明确的四面体拓扑；连通清理必须采用与它一致的邻接约定，避免“数据层认为相连、网格层认为断开”。 |
| 拓扑/几何受约束的 QEM/Edge Collapse | 当前 Final Surface | 在平坦/低曲率区合并三角，在洞口、薄壁、边界和高曲率区拒绝 collapse；当前 Editor 实验约减少 55%-60%，但严格包络仍待补强。 |
| Surface Nets | 后续 A/B | 一格通常一个表面点，面数更少，适合 VR 自然地形；不能只因理论面数较少就替换已验证主线，必须比较拓扑、洞口与 collider bake。 |
| Dual Contouring | 特定需求 | 适合硬边矿洞/建筑式切面；需要 Hermite 数据/QEF，MVP 不建议首发。 |
| Transvoxel | 大范围 LOD | 用于不同体素 LOD 接缝。局部 6-10m DigVolume 可先不用。 |
| Sparse Voxel Octree / Sparse Brick | 层级简化与大范围扩展 | Nintendo 公开专利支持从同一 SVO 候选按误差、空腔、材质门控生成显示/判定网格；适合后续同源多精度 A/B，不适合无约束直接替换。 |
| GPU Raymarch SDF | 视觉特效 | 适合预览/特效，不适合作为主碰撞和主地形，因为碰撞仍需 CPU 数据。 |

推荐路线：

```text
当前 Editor 已验证实验:
    CPU density/SDF + solid 连通清理写回
    + Indexed Marching Tetrahedra
    + 受约束 Adaptive Final Surface
    + Visual/Collider exact pair

Quest 生产候选:
    上述路径 + micro-brick/chunk 池化 + 分帧调度 + Worker bake
    + 存档/网络 + 真机性能门控

同源多精度研究:
    SVO/层级候选 + 误差/空腔/材质/clearance 门控
    + Visual/Collider 分别选级，但必须验证双向包络与交互一致性

高端视觉研究:
    GPU density mirror + GPU meshing/indirect draw
    + CPU 权威 density；Collider 不经未验证的 GPU readback 主链
```

## 5. 数据结构设计

### 5.1 坐标与符号约定

为方便碰撞判断，工程内统一：

```text
density > 0  表示实心 solid
density <= 0 表示空气/已挖空 empty
iso = 0      是可见表面
```

数学资料中常见 SDF 是“负数在物体内部、正数在外部”。如果引用标准 SDF 公式，需要做一次符号转换。本方案选择 `density > 0 = solid`，是为了让 gameplay/collision query 更直观。

### 5.2 Chunk 数据

下列是生产候选布局，不是对当前实验类名/容器的逐字段复刻。当前 Editor 实验使用单一 CPU `float[]` density 作为全场权威；若迁移为量化 `NativeArray<short>` 或真正分 Chunk 存储，必须重新验证数值误差、halo 同步、cleanup 与 Surface Pair 一致性。

```csharp
public struct DigVolumeConfig {
    public float3 origin;
    public float3 sizeMeters;    // 功能有效范围，Inspector 先配置它
    public int3 sampleCells;     // 只控制范围内采样精度，不改变 sizeMeters
    public float3 cellSize;      // 由 sizeMeters / sampleCells 派生
    public int chunkCells;       // 每 Chunk 的 Cell 数，仅影响分块粒度
    public int halo;             // 推荐 1
}

public sealed class DigChunk {
    public int3 coord;
    public Bounds worldBounds;

    // sampleDim = chunkCells + 1 + 2 * halo
    // 唯一权威 density 的 Chunk slice；halo 是只读邻域/同步边界，不是第二份权威。
    public NativeArray<short> densityQ15;
    public NativeArray<byte> materialIds;
    public NativeArray<byte> lockedMask;

    public BoundsInt dirtySamples;
    public DirtyFlags dirtyFlags;
    public int densityEpoch;
    public int activePairEpoch;
    public int pendingPairEpoch;

    public Mesh activeVisualMesh;
    public Mesh pendingVisualMesh;
    public Mesh activeColliderMesh;
    public Mesh pendingColliderMesh;
    public MeshCollider meshCollider;
    public bool pairBuildInFlight;
}
```

Authoring/Inspector 参数必须按以下语义分组：

- **固定物理范围**：`origin + sizeMeters` 是功能边界。修改网格精度、Chunk 大小或 Collider 选级时不得自动缩放这个范围。
- **采样精度**：`sampleCells` 或“每米采样数”只改变 `cellSize` 与样本数量；面板同时显示推导后的 Cell Size、总样本数和预计内存。
- **Brush 物理参数**：半径、强度、轨迹间距使用米/秒等物理单位，不随 voxel 精度隐式变化。
- **独立实体清理参数**：搜索 padding/extent 用米，体积阈值用立方米，Sample budget 只是安全上限；不能用“降网格精度”顺带改变清理功能范围。
- **表面简化参数**：几何误差、法线/边界/薄壁约束和目标三角比例只作用于 Final Surface，不改 density 的物理意义。

低层 runtime 可以继续缓存标量 `voxelSize`，但它必须是固定 Bounds 与采样数的派生值，而不是反向决定功能范围的唯一参数。

当前实验的 cleanup 阈值精确定义如下；复用时不要把 `extent` 猜成单轴长度，也不要把体积简化成纯 sample 计数：

```text
sampleSpan = componentMaxSample - componentMinSample + 1
physicalSpan = sampleSpan * cellSize
componentExtentMeters = length(physicalSpan)   // 样本 AABB 的物理对角线

densityNormalization = max(0.5 * length(cellSize), epsilon)
componentSolidVolume = sum(
    saturate(positiveDensity / densityNormalization) * cellVolume)

remove =
    componentExtentMeters <= maximumRemovableExtentMeters
    AND componentSolidVolume <= maximumRemovableSolidVolumeCubicMeters
    AND not touchesSearchBoundary
    AND searchWasNotTruncated
```

这是本地工程选择，不是 Nintendo 专利规定的唯一阈值公式；专利公开文本只支持按 density 总和或 voxel 数等参考值识别小区域的更宽泛做法。

内存估算：

- `chunkCells = 32`，`halo = 1`，sampleDim = 35，density `35^3 * 2 bytes ≈ 84KB`。
- material 使用 cell 级 `32^3 * 1 byte ≈ 32KB`。
- 单 chunk 主数据约 120KB，加 mesh/cache 后仍可控；Quest 建议先从 `24^3` 或较少活跃 chunk 开始。

### 5.3 Ghost Border / Halo

每个 chunk 必须带 1 voxel halo。原因：

- Marching Cubes/Surface Nets/Marching Tetrahedra 需要读取 cell 角点；Chunk 边界处需要邻居样本。
- 法线梯度需要 `p+dx/p-dx` 的邻域值。
- Brush 跨 chunk 时，如果邻居不 dirty，会出现视觉裂缝或碰撞接缝。

规则：

```text
Brush AABB 与 chunk 相交 -> 修改该 chunk
修改区域触碰 chunk 边界 halo -> 邻居 chunk 标 SurfacePairDirty
每次 mesh build 前同步邻居边界样本或读取共享边界
```

## 6. 挖掘 Brush 与 CSG

VR 工具不能只用离散点采样。手柄两帧之间移动很快时，单点会漏挖，因此要用 capsule stroke：

```csharp
public struct BrushOp {
    public float3 p0;
    public float3 p1;
    public float radius;
    public float strength;
    public byte op;          // Carve / Fill / Paint
    public byte materialId;
    public int sequence;
}
```

球刷与胶囊刷 SDF：

```c
float sdSphere(float3 p, float3 c, float r) {
    return length(p - c) - r; // <0 表示在刷子内部
}

float sdCapsule(float3 p, float3 a, float3 b, float r) {
    float3 pa = p - a;
    float3 ba = b - a;
    float h = saturate(dot(pa, ba) / dot(ba, ba));
    return length(pa - ba * h) - r;
}
```

本工程 `density > 0 = solid`，所以挖掘逻辑可以写成：

```c
// phi: 当前 density，>0 solid，<=0 empty
// brush: 标准 brush SDF，<0 inside brush
float Carve(float phi, float brush, float strength) {
    float target = min(phi, brush);       // brush 内部变成 <=0
    return lerp(phi, target, strength);
}

float Fill(float phi, float brush, float strength) {
    float solidBrush = -brush;            // brush 内部为正 solid
    float target = max(phi, solidBrush);
    return lerp(phi, target, strength);
}
```

Dirty 标记伪代码：

```c
ApplyBrush(BrushOp op):
    aabb = CapsuleAABB(op.p0, op.p1, op.radius + narrowBand)
    brushDirty = EmptyBounds
    for chunk in OverlapChunks(aabb):
        sampleRange = WorldAABBToChunkSamples(chunk, aabb)
        for sample in sampleRange:
            if lockedMask[sample]: continue

            p = SampleToWorld(sample)
            phi = DecodeDensity(chunk.densityQ15[sample])
            brush = sdCapsule(p, op.p0, op.p1, op.radius)
            next = Carve(phi, brush, op.strength)

            if abs(next - phi) > epsilon:
                chunk.densityQ15[sample] = EncodeDensity(next)
                brushDirty.Encapsulate(ToVolumeSample(chunk, sample))

    cleanup = CleanupSmallSolidComponents(secondRangeAround(aabb))
    combinedDirty = Union(brushDirty, cleanup.dirtySamples)
    if combinedDirty is empty: return

    for chunk in OverlapChunks(combinedDirty):
        chunk.densityEpoch++
        MarkSurfacePairDirty(chunk)
        MarkSaveDirty(chunk)
        if NearPlayerOrTool(chunk): RaisePairPriority(chunk)
        if DirtyTouchesBorder(chunk): MarkNeighborPairDirty(chunk)
```

限制规则：

- Brush 半径不小于 `1.5-2 * voxelSize`，否则会制造高频锯齿和碎三角。
- 每帧限制最大修改 sample 数；超出时合并/分帧。
- `lockedMask` 用于不可挖边界、底板、任务保护物、岩层。
- 每个 Chunk 设置容量/时间安全上限；超出时上报并延迟/拆分工作，或在硬约束内继续自适应简化。不得静默降低采样精度或跨过拓扑/几何门控来硬凑三角数。

## 7. 网格生成

### 7.1 Marching Cubes 参考路线

Marching Cubes 因为资料多、容易在 Unity Jobs/Burst 或 Unreal TaskGraph 跑通，仍适合快速参考；当前 Unity 实验主线已改为 Indexed Marching Tetrahedra + Adaptive Final Surface，不能再把下列 MC 草图视为已验证生产路径。

```c
BuildMeshMC(chunk):
    for each cell in chunk:
        s[8] = LoadCornerDensity(cell)
        mask = SignMask(s > 0)
        if mask == 0 or mask == 255:
            continue

        for tri in TriTable[mask]:
            for edge in tri.edges:
                a, b = EdgeCorners(edge)
                t = s[a] / (s[a] - s[b])
                pos = lerp(P[a], P[b], t)
                nrm = normalize(DensityGradient(pos))
                mat = ResolveMaterial(cell, edge)
                EmitVertex(pos, nrm, mat)
```

实现要点：

- 不使用 Unity `RecalculateNormals` 热路径；法线从 density 梯度计算。
- material 不拆太多 submesh；优先 vertex color / texture array index / UV channel。
- bounds 自己计算，避免每次全量重算。
- 只对 dirty chunk 重建；全空/全实心 chunk 直接跳过 renderer/collider。

### 7.2 Surface Nets 后续 A/B

Surface Nets 通常更适合 VR 地形：

- 一格一个候选表面点，顶点数通常比 MC 少。
- 表面更稳定，不容易出现大量细碎三角。
- 对自然泥土/洞穴很合适。

伪代码：

```c
BuildSurfaceNets(chunk):
    for each cell with sign crossing:
        crossings = EdgeIntersections(cell)
        vertex[cell] = Average(crossings)
        vertex[cell] = ClampToCell(vertex[cell])

    for each grid edge with sign crossing:
        cells = IncidentCells(edge)
        EmitQuadOrTwoTriangles(vertex[cells])
```

Dual Contouring 可看作 Surface Nets 的硬边增强路线，需要 Hermite normal 与 QEF。它适合矿石切面、建筑式边界，但不是 MVP 首选。

### 7.3 当前验证主线：Indexed Raw -> Adaptive Final

当前实验把“采样精度”和“最终三角密度”分开：density 仍是规则网格，Raw Surface 保留其拓扑；随后只在满足硬约束时合并边/顶点。因此平面和缓坡可以稀疏，洞口、薄壁、曲率和材质边界保持细致，不会因为 voxel 均匀就让所有位置维持同一三角密度。

```text
BuildSurfacePair(revision):
    snapshot = AuthoritativeDensity(revision)
    raw = BuildIndexedMarchingTetrahedra(snapshot)
    final = ConstrainedAdaptiveSimplify(raw,
        topologyManifold = true,
        maxGeometricError = configured,
        preserveBoundary = true,
        preserveCavityAndThinWall = true,
        preserveMaterialFeatures = true)

    visualMesh = Upload(final.vertices, final.indices)
    colliderMesh = Upload(final.vertices, final.indices)
    BakeColliderOnWorker(colliderMesh, revision)
    CommitPairOnlyIfCurrent(visualMesh, colliderMesh, revision)
```

硬约束优先于目标三角数。到达目标比例不是成功条件；如果一个 collapse 会造成翻面、非流形、洞口封死、薄壁穿透或几何误差超限，就必须拒绝。性能优化顺序是：

1. 只重建 dirty Chunk/微砖；
2. Raw Surface 使用索引复用、Jobs/Burst 和持久缓冲；
3. Final Surface 在平坦区域做受约束 collapse；
4. 减少 Mesh 上传次数并复用 Mesh；
5. 在真机数据支持后，再评估 SVO 层级选级或视觉 GPU 路线。

当前实验已验证拓扑/局部几何拒绝、exact pair 和约 55%-60% 三角减少；严格双向 Hausdorff、全局自交与薄壁 clearance 仍是未完成门控，不能声称“所有形状都安全”。

## 8. 动态碰撞设计

### 8.1 一致性契约

碰撞 cooking 可以异步，**视觉与碰撞的语义不能异步分叉**。当前默认契约是：

```text
ActivePair(revision N) = VisualFinal(N) + ColliderFinal(N)

PendingPair(revision N+1):
    先生成唯一 Final Surface
    -> 分别上传相同 vertex/index stream
    -> Worker bake Collider
    -> bake 完成且 revision 仍最新时，一次提交两者
```

- 等待 N+1 时继续使用完整的 N 对；不得先显示 N+1，再保留 N 的碰撞。
- 新 Brush 产生 N+2 时，N+1 若已过时就丢弃；不得让 stale collider 覆盖新 revision。
- Visual/Collider 可以使用不同 Mesh 实例，便于双缓冲和 cooking，但提交前必须逐顶点、逐索引一致。
- 全空 Chunk 也按 Pair 语义同时关闭 Renderer 与 Collider，避免“没有碰撞但仍漂着一块可见碎网格”。

### 8.2 为什么独立固定步长降采样不可作为默认方案

把视觉 `32^3` 单独降成碰撞 `16^3`，或只提高 `colliderSampleStep`，会同时改变：

- 洞口是否存在、薄壁是否连通；
- 小型 solid 是否被保留；
- 边界插值位置与法线；
- Visual 与 Collider 完成重建的时序。

这不是“Collider 精度稍低”，而是两套拓扑。实验中步长为 1 时不匹配几乎消失，说明根因是独立构网/发布，不应再用 `clearanceBias` 或更高碰撞精度掩盖。

当前优化顺序：

1. **同一 Final Surface 先做一次受约束简化**，Visual 与 Collider 一起受益；
2. **缩小 dirty 重建单元**，把 Chunk 进一步拆成受控 micro-brick，而不是全块重复 cooking；
3. **复用 Mesh/Native 缓冲并 Worker bake**，主线程只做必要上传与 Pair 提交；
4. 真机证明 exact pair 仍超预算后，才 A/B 同源 SVO/层级候选的不同选级。

若未来 Collider 比 Visual 更简，必须同时满足：

- 两者从同一 density revision、同一层级候选源派生；
- 有双向几何包络/最大误差门控，而非仅三角目标；
- 空腔、洞口、薄壁、材质/玩法边界不可丢失；
- 可视区域与可通行区域的误差有明确上限；
- 在目标 Quest 上同时比较 triangle、bake、broadphase、发布延迟和穿透/悬浮回归。

### 8.3 独立小碎屑必须在权威 density 层清理

Mesh 后处理很难稳定删除“看起来小”的浮空三角，因为它不能可靠判断实体是否在网格外仍与主体相连，也无法同步修正碰撞。更稳的路径是公开专利所描述的两范围思路：

```text
第一范围：Brush 实际修改区域
第二范围：包含第一范围并带物理 padding/halo 的连通搜索区域

在第二范围搜索 solid connected components
    -> 触碰搜索边界：保守保留/延后，避免误删范围外仍相连的主体
    -> 同时小于物理 extent 与体积阈值：写成稳定 empty density
    -> 合并 Brush/Cleanup dirty bounds
    -> 从更新后的同一 density 重建 Surface Pair
```

维护要点：

- 只清 **solid component**，不要把封闭空气洞当碎屑删除。
- 邻接约定要与 Raw mesher 的拓扑一致；当前实验采用与 Marching Tetrahedra 相容的邻接，而不是宣称 Nintendo 固定使用某种邻接。
- 阈值使用米/立方米，和网格精度解耦；Sample budget 只防止单次扫描失控。
- 当前实验把 extent 定义为样本 AABB 的物理对角线，把 solid volume 定义为正 density 归一化积分；两个上限使用 `<=` 且为 AND 条件。
- 搜索预算不足时必须保守跳过并上报 truncation，不能只处理一半后提交错误结论。
- Cleanup 必须先写回权威 density，再取得 meshing snapshot；不能让 Visual 和 Collider 各自做一遍碎屑判断。

### 8.4 SDF 查询的正确定位

SDF/density 查询仍适合：

| 对象 | 用法 | 边界 |
|---|---|---|
| 手/铲子/钻头 | sphere/capsule vs SDF | 立即计算 Brush、预览和下一 revision；当前接触仍遵循 ActivePair |
| 玩家角色 | ActivePair ground probe | 默认保持所见即所碰；只有配套过渡视觉时才用新 density 否决旧接触 |
| 射线/抓取 | 明确选择 ActivePair 或 density revision | 物理抓取用 ActivePair；编辑预览可用最新 density，不能混用后假装一致 |
| 普通刚体 | Active Collider Pair | 仍依赖已发布的稳定物理表面 |

SDF 不能修复屏幕上已经显示 N+1、物理上仍是 N 的矛盾。若玩法要求“视觉立刻消失”，应使用不改变最终几何语义的短时特效/遮罩，并让正式 Final Surface 等 collider bake 后成对发布。

Unity `Physics.BakeMesh` 可配合 Job System 预烘，但不要对同一个 Mesh 并发 Bake；`MeshCollider.sharedMesh` 与 Renderer 的 active Mesh 切换仍应在主线程的安全阶段完成。ContactModifyEvent 可做特定接触兜底，但回调可能在任意线程，只能读取线程安全快照，不能作为长期双网格架构。

## 9. Compute Shader / GPU 路线

### 9.1 是否必须使用 Compute Shader

MVP 不需要，也不建议强依赖 Compute Shader。理由：

- 碰撞、角色查询、存档、网络权威都需要 CPU 数据。
- GPU 视觉 mesh 若要变成 MeshCollider，需要 GPU->CPU readback，再做 physics cooking。
- Unity `AsyncGPUReadback` 虽然避免即时 stall，但会增加数帧延迟，不适合“挖掉立刻无碰撞”的正确性链路。
- Quest 移动 GPU 带宽、热功耗和 compute 预算紧张；Foveated Rendering 主要减轻 pixel shading，不会自动降低 meshing compute 成本。

推荐分阶段：

```text
当前实验主线:    CPU density 权威 + Burst Raw/Adaptive Final + Worker bake + exact pair
Quest 生产候选:  上述主线 + dirty micro-brick + 池化 + 分帧 + 真机门控
安全 GPU 增益:   GPU density 镜像用于预览、粒子、调试、culling，不接管 Collider 权威链
PCVR/高端研究:   GPU visual meshing + indirect draw；正式可见表面与 CPU Collider 的包络/发布一致性需另行证明
极限研究:        GPU resident sparse brick/SVO + 自定义 renderer + 同源 CPU 判定候选
```

Compute Shader 可以加速分类、前缀和、视觉三角生成或剔除，但**不能直接消除 PhysX/Chaos collider cook**。若把 GPU 三角回读给 MeshCollider，仍需 `AsyncGPUReadback -> CPU Mesh -> Physics.BakeMesh`，会增加数帧延迟并占用移动 GPU 带宽。因此当前 collider 大头的优先解法是减少/局部化 Final Surface、复用资源、Worker bake 与成对发布，而不是把同一套三角先搬到 GPU 再读回。

### 9.2 可选 Compute Shader 用法

适合 GPU 的阶段：

- 大量 brush 批量写入 GPU 镜像 density。
- GPU classify cells / prefix sum / emit visual triangles。
- GPU normal/material baking。
- GPU chunk culling / indirect draw。

这些阶段若只生成预览/特效可以独立更新；若输出正式地形视觉，则必须同时设计与 CPU 碰撞表面的误差包络、revision 和发布门控。

不适合 GPU 单独承担的阶段：

- 玩家是否站在已挖空区域。
- 工具是否撞到旧土。
- MeshCollider/Chaos 碰撞 cook。
- 网络权威状态。

HLSL 草图：

```hlsl
struct BrushOp {
    float3 p0;
    float radius;
    float3 p1;
    float strength;
    uint op;
    uint material;
};

RWStructuredBuffer<int> DensityQ;
StructuredBuffer<BrushOp> Brushes;
RWStructuredBuffer<uint> CellCase;
AppendStructuredBuffer<uint2> ActiveCells;

[numthreads(8, 8, 8)]
void ApplyBrush(uint3 id : SV_DispatchThreadID) {
    if (any(id >= SampleDim)) return;

    uint index = SampleIndex(id);
    float3 p = ChunkOrigin + id * VoxelSize;
    int d = DensityQ[index];

    for (uint i = 0; i < BrushCount; i++) {
        float brush = SdCapsule(p, Brushes[i].p0, Brushes[i].p1, Brushes[i].radius);
        int q = QuantizeDensity(brush);
        if (Brushes[i].op == 0) d = min(d, q);       // carve
        else d = max(d, -q);                         // fill
    }

    DensityQ[index] = d;
}

[numthreads(8, 8, 8)]
void ClassifyCells(uint3 c : SV_DispatchThreadID) {
    if (any(c >= CellDim)) return;

    uint mask = 0;
    [unroll] for (uint i = 0; i < 8; i++) {
        int s = DensityQ[SampleIndex(c + CornerOffset[i])];
        if (s > 0) mask |= (1u << i);
    }

    uint cell = CellIndex(c);
    CellCase[cell] = mask;
    if (mask != 0 && mask != 255) ActiveCells.Append(uint2(cell, mask));
}
```

生产级 GPU meshing 不建议长期依赖无限 Append。更稳的是两遍法：

```text
classify/count -> prefix sum -> emit into exact ranges -> indirect draw
```

## 10. Unity 工程方案

### 10.1 模块结构

```text
Assets/Game/Digging/
  Runtime/
    DiggableVolume.cs
    DigChunk.cs
    DigRuntimeSystem.cs
    DigBrushSystem.cs
    DensityConnectivityCleanup.cs
    DigDirtyScheduler.cs
    DigSdfQuery.cs
    DigCharacterGroundProbe.cs
    DigContactModifier.cs
    DigSaveDelta.cs
  Jobs/
    ApplyBrushJob.cs
    BuildIndexedRawSurfaceJob.cs
    AdaptiveFinalSurfaceJob.cs
    BakeColliderJob.cs
  Data/
    DigVolumeBakeAsset.cs
    DigVolumeSettings.cs
    DigMaterialPalette.cs
  Rendering/
    DigTerrainLit.shader
    DigBrushPreview.compute
    DigDebugOverlay.cs
  Editor/
    DigVolumeAuthoring.cs
    DigVolumeBaker.cs
    DigChunkDebugWindow.cs
```

### 10.2 烘焙资产

```csharp
[CreateAssetMenu]
public sealed class DigVolumeBakeAsset : ScriptableObject {
    public Bounds localBounds;
    public Vector3Int sampleCells;
    public Vector3 cellSize;
    public int chunkCellSize;
    public byte[] initialDensityCompressed;
    public byte[] materialIdsCompressed;
    public byte[] lockedMaskCompressed;
    public DigChunkBakeInfo[] chunks;
}
```

编辑器烘焙职责：

- 从基础地形/mesh/手工体积生成初始 density。
- 生成不可挖 mask 与边界。
- 切 chunk，压缩初始数据。
- 可选预生成初始 Final Surface Pair；Visual/Collider 从同一 vertex/index stream 派生。
- 生成 debug 预览。

### 10.3 运行时调度

```text
ApplyBrushQueue
  -> Brush + DensityConnectivityCleanup
  -> CombinedDensityDirty
  -> SurfacePairDirtyQueue
  -> Raw/Adaptive/Bake pipeline
  -> PairCommitQueue
  -> SaveDirtyQueue
```

调度规则：

- 同一个 chunk 多个 brush op 合并。
- 近玩家、近手、视锥内 chunk 优先。
- Density cleanup 必须在该 revision 的 mesh snapshot 前完成；Brush 与 cleanup 合并 dirty bounds。
- Raw/Adaptive/Bake 可以跨帧，但新 Visual 与 Collider 必须作为同一 Pair 发布。
- 队列过长时合并 revision、丢弃 stale pending pair、缩小重建单元或冻结远处 Chunk；不得临时切回独立低精度 Collider。
- Pair latency 用停笔后的端到端分位数验收，不能用“每秒更新几次碰撞”掩盖视觉/碰撞进度差。

### 10.4 多线程与时域分帧

可以分帧，但分的是**工作阶段和候选批次**，不是把同一 revision 拆成视觉/碰撞两套真相：

```text
Frame A: 合并 Brush，推进/完成 density cleanup
Frame B: Build Indexed Raw（Burst Job）
Frame C..N: 分批处理 Adaptive collapse 候选
Worker: 上传 Collider 数据后 Physics.BakeMesh
Main safe point: 若 revision 仍最新，提交整个 Surface Pair
```

建议的加速算法/数据结构：

- `Bounds -> Chunk/micro-brick` 直接映射，只访问 dirty 空间；不要每次扫描整个 DigVolume。
- Raw mesher 先 classify active cells，再精确计数/前缀和/写入，避免无限 Append 与反复扩容。
- Density 连通清理的搜索窗口必须有物理边界和预算。规模扩大后可用持久 `NativeArray` + Burst flood fill/union-find；若每笔先把 managed density 全量复制到临时 NativeArray，再同步等待 Job，复制成本会抵消并行收益。
- Adaptive simplifier 使用确定性的边候选队列和局部邻域更新；每批限制候选数，达到时域预算后保留状态到下一帧。
- SVO/层级候选可以把平坦区域快速聚合，但每次合并仍需几何误差、空腔、材质/特征门控。
- 所有后台任务携带 density revision；完成时先校验 revision，过时结果直接丢弃，不回写 active pair。
- 复用 Native/Mesh/scratch 缓冲，避免每次 Brush 分配；Profiler 必须区分调度、Worker wall、主线程 upload、bake 与端到端 Pair latency。

Density cleanup 是最终表面的前置权威事务。它可以做成可恢复的多帧状态机，但未完成或发生预算截断时不得先取 mesh snapshot；否则碎屑会在 Visual/Collider 之间重新出现。

### 10.5 Mesh 提交

使用 Unity MeshData：

```csharp
var meshDataArray = Mesh.AllocateWritableMeshData(1);
var meshData = meshDataArray[0];

// Job 内填充 vertex/index/submesh。

Mesh.ApplyAndDisposeWritableMeshData(meshDataArray, chunk.pendingVisualMesh);
chunk.pendingVisualMesh.MarkDynamic();

// Collider Mesh 使用同一 Final vertex/index stream；Worker bake 后再提交整个 Pair。
```

不要在热路径使用：

- `new List<>` 反复分配。
- LINQ。
- 每帧字符串拼接。
- `RecalculateNormals` / `RecalculateBounds` 全量滥用。
- 同步高频 `MeshCollider.sharedMesh = mesh`。

### 10.6 XR/URP 设置

推荐 Quest 起点：

- URP Forward。
- Opaque 地面 shader。
- SRP Batcher 开。
- 少材质、少 keyword、texture array/atlas。
- MSAA 2x 起步。
- 关闭 HDR、Post Processing、Depth Priming、Depth Texture、Opaque Texture，除非实测需要。
- Quest 用 Multiview；自定义 shader 支持 Single Pass Instanced/Multiview。
- Profiling 时固定 render scale，先关闭动态分辨率以看真实瓶颈；最终构建再开启 Dynamic Resolution / Foveated Rendering 兜底。

Shader 必备宏：

```hlsl
struct Attributes {
    float3 positionOS : POSITION;
    float3 normalOS   : NORMAL;
    UNITY_VERTEX_INPUT_INSTANCE_ID
};

struct Varyings {
    float4 positionCS : SV_POSITION;
    float3 normalWS   : TEXCOORD0;
    UNITY_VERTEX_OUTPUT_STEREO
};
```

### 10.7 Inspector/HUD 信息架构

参数面板不能只显示变量名。建议用卡片和派生摘要把“功能范围、精度、清理、简化、发布、证据等级”分开：

- **顶部证据徽标**：Editor Relative Regression / Quest Device Acceptance，不允许 Editor 达标显示成真机通过。
- **固定物理范围**：中心、尺寸、世界 Bounds；旁边单独显示 sample resolution、Cell Size、总 sample/Chunk 数和预计内存。
- **Density 连通清理**：搜索 padding（m）、最大实体 extent（m）、体积阈值（m³）、Sample 安全预算；Tooltip 解释它们不会改变 DigVolume/Brush 有效范围。
- **Adaptive Final**：最大几何误差、边界/拓扑/薄壁/材质硬约束、目标减面率；明确“目标是软目标，硬约束可阻止继续减面”。
- **调度与 Pair**：每帧任务预算、pending/active revision、stale discard、Pair latency、Worker bake。
- **运行告警**：cleanup truncation、pair mismatch/gap、adaptive fallback 用红色；触界延后用黄色；正常 exact pair 用绿色。
- **性能标签**：每个数值标明 Main/Worker/Wall/Upload/Bake、last/median/p95 与 Editor/Device，防止把跨帧墙钟误当单帧 CPU。

面板可以提供“实验推荐起点”按钮，但必须明确它只是可复现基线，不是 Quest 认证预设。

## 11. Unreal 工程方案

### 11.1 组件路线

| 路线 | 阶段 | 判断 |
|---|---|---|
| `UProceduralMeshComponent` | MVP | 支持自定义三角网格、`CreateMeshSection/UpdateMeshSection`、`bUseAsyncCooking`；Epic 标注 experimental，适合验证。 |
| `UDynamicMeshComponent` | 生产第一版 | 支持动态 mesh、部分 render buffer 更新、内部 chunk、defer collision update、async cooking，更贴近需求。 |
| 自定义 `UPrimitiveComponent + FPrimitiveSceneProxy` | 高性能最终版 | 工程量最大，但可自管 buffer、dirty range、culling、indirect draw。 |

### 11.2 Unreal 数据结构

```cpp
struct FDigChunk {
    FIntVector Coord;
    TArray<int16> Density;
    TArray<uint8> Material;
    FBox Bounds;
    uint32 DensityEpoch;
    uint32 ActivePairEpoch;
    uint32 PendingPairEpoch;
    EDirtFlags Dirty;
};

class ADiggableVolume : public AActor {
    FDigVolumeConfig Config;
    TMap<FIntVector, FDigChunk> Chunks;
    UDynamicMeshComponent* VisualComponent;
};
```

碰撞建议：

- MVP 用 `UProceduralMeshComponent::bUseAsyncCooking = true`，`CreateMeshSection(..., bCreateCollision = true)`。
- 生产用 `UDynamicMeshComponent`，开启 defer collision updates，批量修改后 `UpdateCollision`。
- 无论组件路线如何，都从同一 Final Surface 更新显示/碰撞，并用 PairEpoch 防止 async cook 的过时结果回写。
- 对角色 Movement/Floor Check 增加 SDF 查询可以补充交互语义，但不能先提交新显示网格、再长期保留旧碰撞。

本轮实验只验证 Unity 路径；上述 Unreal 组件/API 建议仍属于待实测规划，不能套用 Unity Editor 指标。

Nanite 判断：

- 不适合作为动态挖洞主链路。Nanite 面向静态/构建后的 cluster；VR 常用 Forward/Stereo/MSAA 与运行时高频拓扑变化都不是它的强项。
- 可用于不可挖的远景岩壁和静态大场景。

## 12. 存档与网络同步

不要同步 mesh，优先同步 BrushOp：

```text
volumeId
opSequence
toolType
p0, p1
radius
strength
materialOp
timestamp
authorId
```

客户端：

- 收到 BrushOp 后本地重放。
- 立即更新 CPU density。
- 从同一 density revision 异步生成 Surface Pair，并只在两者就绪时成对发布。

服务器：

- 对 BrushOp 做频率限制、范围校验、不可挖 mask 校验。
- 维护 chunk epoch/hash。
- 定期发 chunk delta snapshot 修正长时间漂移。

存档：

```text
初始 BakeAsset
  + BrushOp log
  + 周期性 chunk delta snapshot
  + chunk hash/epoch
```

加载时先应用最新 snapshot，再重放 snapshot 之后的 BrushOp。

## 13. 调试与验收

必须有 Digging Debug HUD：

- 本帧 brush voxel 数。
- density cleanup 耗时、扫描/清空 sample 数、删除 component 数。
- cleanup 边界延后数与搜索截断数；截断必须作为危险状态显示。
- dirty chunk 数。
- SurfacePairDirtyQueue / PairCommitQueue 长度。
- mesh build ms。
- Raw/Final triangle 与 accepted/rejected collapse 数。
- mesh apply ms。
- collider bake/cook ms。
- Visual/Collider 顶点/索引是否完全匹配。
- active pair revision gap、mismatch chunk、stale discard 与 fallback 数。
- chunk draw calls。
- GC Alloc。
- SDF query 次数。
- ContactModify 忽略接触数。
- chunk 三角超限次数。

Quest 真机验收：

- Quest 2：单 DigVolume 连续挖 60 秒，72 FPS 稳定。
- Quest 3：90 FPS 目标。
- 无每帧 GC。
- 不出现“已经显示为空但仍有碰撞”或“仍显示实体却已无碰撞”的可感知错配。
- collision cook 不产生明显 hitch。
- OVR Metrics 检查 FPS、App GPU/CPU time、throttling、stale frames、foveation level、eye buffer size。

## 14. 实施路线

### Phase 0: Editor 技术 Spike（已完成相对回归）

- 单个 `6m x 6m x 3m` DigVolume。
- 固定 Bounds + 可调 sample resolution，精度不改变功能范围。
- CPU 权威 density + Brush 后第二范围 solid 连通清理。
- Indexed Marching Tetrahedra Raw + 受约束 Adaptive Final。
- Visual/Collider exact pair、Worker `Physics.BakeMesh`、revision 成对发布。
- Inspector/HUD 显示参数物理语义、cleanup、Raw/Final、pair 与 bake 性能标签。
- 21-case 测试记录、Core SelfCheck、v8 Editor 相对基准与 Play Mode 可见沟槽闭环。

### Phase 1: Quest 真机门控（下一步）

- Quest Android IL2CPP 连续挖掘至少 60 秒。
- Unity Profiler + OVR Metrics 采集 CPU/GPU frame time、Pair latency、Collider bake、GC、热状态与降频。
- 先验收 72Hz 稳态，再评估 90Hz；Editor 数据不得代替。
- 若 collider 大头超预算，先 A/B micro-brick、Final Surface 约束与 Mesh/buffer 复用，不恢复独立固定步长 Collider。

### Phase 2: 生产化

- 持久 Native density/scratch 与 Burst/分阶段连通算法评估；避免每次复制整场 density 后再等待 Job。
- dirty micro-brick、Chunk/mesh/native buffer 池化。
- 严格双向几何包络、全局自交与薄壁 clearance 门控。
- 同源 SVO 层级候选 A/B；只有通过视觉/碰撞一致性与真机 bake 回归才允许不同选级。
- 多 DigVolume streaming。
- 存档 BrushOp + chunk snapshot。
- 网络同步 BrushOp。
- 不可挖 mask、岩层、材质层。
- OVR Metrics/Profiler 自动化采样。

### Phase 3: 高端/PCVR

- GPU density mirror。
- Compute Shader brush preview/批量视觉写入。
- GPU visual meshing/indirect draw 实验。
- CPU density 权威与同源判定候选保留；GPU readback 不进入未验证的 Collider 主链。
- Sparse brick / SVO / Transvoxel 评估。

## 15. 风险清单

| 风险 | 等级 | 缓解 |
|---|---|---|
| Collider cooking 单帧尖刺 | 高 | 同一 Final Surface 受约束简化、dirty micro-brick、Worker bake、资源复用、每帧限量与 Pair latency 预算。 |
| Visual/Collider 进度或形状不一致 | 高 | exact vertex/index pair、同 revision 原子提交、stale discard；禁止独立固定步长降采样。 |
| Pair 等待期间旧表面仍生效 | 高 | Brush/预览可查权威 SDF；玩家与刚体默认遵循 ActivePair，正式新视觉等待 bake 成对发布，必要时只用不改语义的短时特效。 |
| 跨 chunk 破洞/裂缝 | 高 | halo、邻居 dirty、边界样本同步、cleanup 邻接与 mesher 拓扑一致、拓扑 collapse 门控。 |
| 空中小碎屑 | 高 | 在权威 density 的第二范围做 solid 连通清理；触界保留、预算不足保守跳过、写回后统一重建。 |
| 自适应简化封洞/穿薄壁 | 高 | 几何误差、翻面/流形、空腔、边界、材质与 clearance 硬约束；目标三角数只是软目标。 |
| Density cleanup 扫描超预算 | 高 | 有界搜索、持久 scratch、指标/截断门控；真机超限后评估 Persistent NativeArray + Burst/union-find 分阶段。 |
| GPU readback 延迟 | 高 | 碰撞不依赖 GPU；GPU 只做视觉/镜像。 |
| Quest 热降频 | 高 | 按 72Hz/90Hz 预算设计，Foveated/Dynamic Resolution 只兜底。 |
| 网络不同步 | 中高 | 同步 BrushOp、固定顺序重放、chunk epoch/hash、周期 snapshot。 |
| 商业案例/专利误判 | 中 | 官方访谈/GDC 只作产品方向证据；专利只作公开实施例，项目阈值、线程、Collider 与成品内部实现不得混写。 |

## 16. 参考来源

- Nintendo: [Ask the Developer Vol. 19, Part 2](https://www.nintendo.com/us/whatsnew/ask-the-developer-vol-19-donkey-kong-bananza-part-2/) - 官方确认 voxel 是内部地形/敌人结构、每 voxel 带材质并支持逐 voxel 破坏；不披露 Collider/线程/阈值。
- GDC 2026: [Constructive Destruction: Fusing Voxel Tech and 3D Action Platforming in Donkey Kong Bananza](https://schedule.gdconf.com/session/constructive-destruction-fusing-voxel-tech-and-3d-action-platforming-in-donkey-kong-bananza/916931) - 官方议程只佐证体素破坏主题；未核验演讲视频前不扩写具体算法。
- Nintendo patent application: [US2025/0242264](https://patents.justia.com/patent/20250242264) - 第二范围内识别连续 present-voxel 小区域、写为 absent，并对受影响范围/Chunk 重建 mesh 的公开实施例。
- Nintendo patent: [US 12,597,199](https://patents.justia.com/patent/12597199) - SVO/层级候选简化以及几何误差、空腔和材质门控；显示/判定网格可同源但不必完全同形。
- Meta Horizon OS Developers: [Testing and performance analysis](https://developers.meta.com/horizon/documentation/unity/unity-perf/) - Quest FPS、draw call、三角预算、OVR Metrics。
- Meta Horizon OS Developers: [Dynamic Resolution](https://developers.meta.com/horizon/documentation/unity/dynamic-resolution-unity/) - 动态分辨率与动态注视点渲染相关说明。
- Meta Horizon OS Developers: [Fixed Foveated Rendering](https://developers.meta.com/horizon/documentation/unity/unity-fixed-foveated-rendering/) - FFR 对像素着色/GPU 负载的影响。
- Unity: [Mesh.AllocateWritableMeshData](https://docs.unity3d.com/ScriptReference/Mesh.AllocateWritableMeshData.html) - C# Jobs 可写 MeshData。
- Unity: [Mesh.ApplyAndDisposeWritableMeshData](https://docs.unity3d.com/ScriptReference/Mesh.ApplyAndDisposeWritableMeshData.html) - 提交并释放 MeshData。
- Unity: [Physics.BakeMesh](https://docs.unity3d.com/ScriptReference/Physics.BakeMesh.html) - MeshCollider 预烘、Job 使用与 Read/Write 要求。
- Unity: [Collider types and performance](https://docs.unity3d.com/2022.3/Documentation/Manual/physics-optimization-cpu-collider-types.html) - collider 性能排序与 MeshCollider 成本。
- Unity: [AsyncGPUReadback](https://docs.unity3d.com/ScriptReference/Rendering.AsyncGPUReadback.html) - GPU readback 无 stall 但有数帧延迟。
- Unity: [ContactModifyEvent](https://docs.unity3d.com/ScriptReference/Physics.ContactModifyEvent.html) - 接触修改兜底。
- Unity: [Single-pass instanced rendering](https://docs.unity3d.com/Manual/SinglePassInstancing.html) - XR 自定义 shader 支持。
- Unreal Engine: [UProceduralMeshComponent](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Plugins/ProceduralMeshComponent/UProceduralMeshComponent) - procedural mesh 与 async cooking。
- Unreal Engine: [UDynamicMeshComponent](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/GeometryFramework/UDynamicMeshComponent) - 动态 mesh 路线。
- RelicVR: [A Virtual Reality Game for Active Exploration of Archaeological Relics](https://arxiv.org/abs/2109.14185) - VR dynamic voxel deformation 公开案例。
- Animal Company: [官网](https://www.animalcompanyvr.com/) 与 [Steam](https://store.steampowered.com/app/4551040/Animal_Company/) - 证明其为 Quest/SteamVR 多人 VR 沙盒，但未披露挖掘算法。
- NVIDIA GPU Gems 3: [Generating Complex Procedural Terrains Using the GPU](https://developer.nvidia.com/gpugems/gpugems3/part-i-geometry/chapter-1-generating-complex-procedural-terrains-using-gpu) - GPU 体素地形/Marching Cubes 参考。
- CGAL: [3D Isosurfacing](https://doc.cgal.org/latest/Isosurfacing_3/index.html) - Marching Cubes、Dual Contouring 等 isosurface 方法参考。
- Transvoxel: [The Transvoxel Algorithm](https://transvoxel.org/) - voxel LOD 接缝方案。
- NVIDIA Research: [Efficient Sparse Voxel Octrees](https://research.nvidia.com/publication/2010-02_efficient-sparse-voxel-octrees) - 稀疏体素结构参考。

## 17. 最终建议

第一版请不要追求“全地图自由挖掘”。当前证据支持的最小工程闭环是：

```text
一个固定物理范围、精度独立可调的局部 DigVolume
+ CPU 权威 narrow-band density/SDF
+ capsule brush
+ 第二范围 solid 连通清理写回
+ Indexed Raw Surface
+ 拓扑/几何/空腔/材质约束的 Adaptive Final Surface
+ Worker collider bake
+ Visual/Collider exact pair + revision 成对发布
+ SDF 编辑/预览查询（补充，不作为双网格借口）
+ Editor 相对回归 + Quest 真机 profiling
```

在 Quest 2/3 真机稳定后，再逐步扩展 micro-brick、多区域 streaming、存档/网络、同源 SVO 多精度候选与 GPU 视觉镜像。任何更简 Collider 都必须先证明与视觉的误差包络、空腔/薄壁保持和发布一致性，不能回到独立固定步长降采样。



### 相关记录

- [SDF（有向距离场）知识](./sdf-signed-distance-field.md) - density/SDF 表达和插值的基础概念。
- [ComputeShader GPGPU 基础概念](./compute-shader-gpgpu-basics.md) - Compute Shader 线程模型与 Buffer 使用基础。
- [GPU 视锥剔除 ComputeShader 实现](./gpu-frustum-culling-compute-shader.md) - GPU 并行剔除与 AppendBuffer 的可迁移经验。
- [Unity 3D Collider 类型性能消耗对比](./unity-collider-types-performance.md) - MeshCollider 与 primitive collider 性能边界。
- [移动端 TBDR 与 Overdraw](./mobile-tbdr-overdraw.md) - Quest/移动 GPU 带宽与过绘约束。
- [Unity 动态分辨率与注视点渲染冲突](./unity-dynamicres-foveated-conflict.md) - 该记录需收窄为 Unity 2022.3.39f1 特例/待复核，不能泛化为当前 Meta 文档结论。

### 验证记录

- [2026-06-25] 初次记录。来源为多 Agent 调研、相邻记录、官方文档/论文与本地算法模拟。当时确认 Brush 后 density 与延迟碰撞代理会产生进度差，并提出独立低分辨率 Collider + SDF 兜底；该碰撞建议已被 2026-07-13 的实际一致性问题与实验结果收窄，不再作为默认生产路线。
- [2026-07-13] 重大修正（正确性/来源性/完整性/结构一致性）：对 Nintendo 官方访谈、GDC 官方议程与两项公开专利进行分层复核后，划定可迁移边界为“权威 volume 第二范围小实体写空”和“同源 SVO 层级候选受几何误差、空腔、材质约束”；专利实施例不能表述成成品完整实现，也没有公开证据支持具体邻接、线程、Compute、Chunk、Collider cook 或阈值。
- [2026-07-13] Unity Editor 实验复核：进度记录报告 21/21 cases、Core SelfCheck 与可见沟槽通过；v8 基准在 Unity 2022.3.62f3 Windows Editor、Android active target、Burst/Safety Checks 开启下验证 density cleanup、约 55%-60% 自适应减面、Visual/Collider exact pair 以及 gap/mismatch/fallback/truncation 为 0。此次知识维护只读核对源码、进度记录与 102 字段基准 JSON，没有重新执行 Unity 测试。
- [2026-07-13] 状态由“⚠️ 待验证”改为“🔬 实验性”：Windows Editor 的正确性和相对回归已有证据；Quest Android IL2CPP 的 72/90 Hz、PhysX bake p95/p99、Pair latency、稳态 GC 与热状态仍未验证。正式记录已泛化真实项目名、本机路径与内部场景标识，只保留可复用架构、公开来源和通用指标。

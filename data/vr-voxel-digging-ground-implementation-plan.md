# VR 体素可挖掘地面实现规划与工程方案

**标签**：#unity #graphics #idea #vr #physics #collider #compute-shader #performance
**来源**：本轮多 Agent 调研整理 + 阿卡西本地相邻记录 + Unity/Meta/Unreal 官方文档 + RelicVR 论文 + 本地算法模拟
**收录日期**：2026-06-25
**来源日期**：2026-06-25
**状态**：⚠️ 待验证
**可信度**：⭐⭐⭐⭐（官方资料与论文交叉支持，已做本地算法模拟；未在目标 VR 真机项目中实践）
**适用版本**：Unity 2022.3+/Unity 6、URP/Meta Quest、Unreal Engine 5.x；具体版本需以项目真机验证为准

### 概要

VR 中实现局部地面自由挖掘的推荐架构是“局部 DigVolume + CPU 权威 density/SDF + Dirty Chunk 异步网格重建 + 低分辨率动态碰撞代理 + SDF 即时碰撞查询”。本记录为方案级工程规划，重点说明数据结构、算法、动态碰撞、Compute Shader 使用边界、Unity/Unreal 落地路线与风险。

### 内容

## 1. 结论摘要

游戏内实现“地面可以随意挖，挖掉的地方不能有碰撞”是可行的。高性能路线不是全地图体素化，而是：

```text
静态大地形 / 静态关卡 Mesh
    +
局部 DigVolume 可挖区域
    -> 分块 CPU 权威 density/SDF
    -> Brush CSG 修改体素密度
    -> Dirty Chunk 分帧调度
    -> 视觉 Mesh 高频/异步重建
    -> 碰撞代理低频/低分辨率重建
    -> 角色/手/工具直接查 SDF 兜底
```

核心设计原则：

- **CPU 侧 density/SDF 是权威数据**。碰撞、角色站立、工具命中、存档、网络同步都以它为准。
- **视觉 Mesh 与碰撞 Mesh 分离**。视觉可以较细、更新较快；碰撞必须低模、低频、可滞后。
- **挖空即时性不依赖 MeshCollider/Chaos 完成 cook**。强交互对象直接查 SDF；旧 collider 只是普通物理对象的延迟缓存。
- **MVP 不强依赖 Compute Shader**。先用 CPU Jobs/Burst/TaskGraph 跑通正确性；Compute Shader 放在第二阶段做视觉加速。
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

浏览器验证边界：

- Codex 自带浏览器对外部资料域名与本地 `file://` 页面访问触发安全策略拦截，本次没有绕过。
- 改用本地纯算法模拟验证核心假设：brush 修改 density 后，SDF 查询立即显示空洞；碰撞代理在重建前仍保留旧 solid 状态；重建后 collision 才同步为空。结论是：强交互必须查 SDF，MeshCollider/Chaos 只能作为延迟缓存。

本地模拟结果：

```json
{
  "before": { "densitySolid": true, "collisionSolid": true, "dirtyChunks": 0 },
  "afterBrush": { "densitySolid": false, "collisionSolid": true, "dirtyChunks": 4, "touched": 377 },
  "afterCook": { "densitySolid": false, "collisionSolid": false, "dirtyChunks": 0 }
}
```

## 3. 需求与非功能指标

### 3.1 功能需求

- 支持玩家用手柄、铲子、钻头、爆破等 Brush 在局部区域挖地。
- 挖掉的地方必须能穿过、不能继续产生旧碰撞。
- 支持洞口、侧壁、下切、坑、短隧道等 3D 形态。
- 支持不可挖边界、岩层、底部限制，避免玩家挖穿玩法区域。
- 支持存档与多人同步；网络同步 Brush 操作或 chunk delta，不同步最终 mesh。
- 支持调试可视化：density、dirty chunk、collision epoch、队列耗时、三角数。

### 3.2 性能目标

| 项目 | Quest 2/Pro | Quest 3/3S | PCVR |
|---|---:|---:|---:|
| 推荐帧率 | 72Hz 起步 | 90Hz 目标 | 90Hz 默认 |
| 总帧时间 | 13.9ms 内 | 11.1ms 内 | 11.1ms 内 |
| 挖掘系统平均 CPU | 0.5-1.0ms | 0.8-1.5ms | 1.5-3.0ms |
| 单帧尖刺 | 尽量小于 2ms | 尽量小于 2ms | 避免 VR hitch |
| 视觉 chunk apply | 每帧 1 个 | 每帧 1-2 个 | 4-8 个可测 |
| 碰撞更新 | 5-15Hz | 10-20Hz | 20Hz+ 可测 |

Meta 文档给出的 Quest 交互应用最低目标是 72 FPS；Quest 2/Pro 中等场景 draw call 参考范围约 200-300，Quest 3/3S 中等场景约 400-600；三角量 Quest 2/Pro 约 750k-1m，Quest 3/3S 约 1.3m-1.8m。可挖地形不应吃掉全部预算，建议只占总三角预算的 20%-40%。

## 4. 算法选型

| 方案 | 适用性 | 判断 |
|---|---|---|
| Unity Terrain / Unreal Landscape heightfield | 低 | 只适合高度变化，不能表达洞穴、悬挑、横向掏空。Unity `SetHeights/SetHoles` 还会触发 Terrain LOD/植被相关重算，不适合高频 VR 挖掘。 |
| 2.5D depth/holes | 中 | 可以低成本做浅坑假象，但碰撞和侧壁都需要额外代理；适合小玩法，不适合“真自由挖”。 |
| Occupancy voxel | 中 | 数据简单，但边缘粗糙，法线和材质过渡差。方块风格可用，不推荐作为自然泥土首选。 |
| 3D density/SDF | 高 | 推荐主路线。能表达任意 Brush CSG、洞口、侧壁和下切；能从梯度计算平滑法线。 |
| Marching Cubes | MVP 首选 | 实现资料多、快速闭环；缺点是三角数偏多，锐边和拓扑质量需要约束。 |
| Surface Nets | 生产版优先评估 | 一格通常一个表面点，面数更少，适合 VR 自然地形；实现比 MC 略复杂。 |
| Dual Contouring | 特定需求 | 适合硬边矿洞/建筑式切面；需要 Hermite 数据/QEF，MVP 不建议首发。 |
| Transvoxel | 大范围 LOD | 用于不同体素 LOD 接缝。局部 6-10m DigVolume 可先不用。 |
| Sparse Voxel / Sparse Brick | 后续扩展 | 大世界/流送有价值，但动态编辑、邻居查询、LOD 接缝复杂，不适合第一版。 |
| GPU Raymarch SDF | 视觉特效 | 适合预览/特效，不适合作为主碰撞和主地形，因为碰撞仍需 CPU 数据。 |

推荐路线：

```text
MVP:        int16 narrow-band density/SDF + Marching Cubes + 低模碰撞代理
生产版:     Surface Nets 评估 + chunk 池化 + 低频异步碰撞 + 存档/网络
高端版:     GPU 视觉镜像 + GPU meshing/indirect draw + CPU 低模碰撞权威
大世界版:   Sparse Brick + LOD/Transvoxel + Streaming
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

```csharp
public struct DigVolumeConfig {
    public float3 origin;
    public float voxelSize;      // Quest: 0.12-0.18m; PCVR: 0.06-0.10m
    public int chunkCells;       // Quest: 16/24; Quest3/PCVR: 24/32
    public int halo;             // 推荐 1
}

public sealed class DigChunk {
    public int3 coord;
    public Bounds worldBounds;

    // sampleDim = chunkCells + 1 + 2 * halo
    public NativeArray<short> densityQ15;
    public NativeArray<byte> materialIds;
    public NativeArray<byte> lockedMask;

    public BoundsInt dirtySamples;
    public DirtyFlags dirtyFlags;
    public int densityEpoch;
    public int visualMeshEpoch;
    public int activeColliderEpoch;
    public int pendingColliderEpoch;

    public Mesh visualMesh;
    public Mesh colliderMeshA;
    public Mesh colliderMeshB;
    public MeshCollider meshCollider;
    public bool collisionCookInFlight;
}
```

内存估算：

- `chunkCells = 32`，`halo = 1`，sampleDim = 35，density `35^3 * 2 bytes ≈ 84KB`。
- material 使用 cell 级 `32^3 * 1 byte ≈ 32KB`。
- 单 chunk 主数据约 120KB，加 mesh/cache 后仍可控；Quest 建议先从 `24^3` 或较少活跃 chunk 开始。

### 5.3 Ghost Border / Halo

每个 chunk 必须带 1 voxel halo。原因：

- Marching Cubes/Surface Nets 需要读取 cell 8 个角点；chunk 边界处需要邻居样本。
- 法线梯度需要 `p+dx/p-dx` 的邻域值。
- Brush 跨 chunk 时，如果邻居不 dirty，会出现视觉裂缝或碰撞接缝。

规则：

```text
Brush AABB 与 chunk 相交 -> 修改该 chunk
修改区域触碰 chunk 边界 halo -> 邻居 chunk 标 MeshDirty/CollisionDirty
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
                chunk.dirtySamples.Encapsulate(sample)

        if chunk.dirtySamples not empty:
            chunk.densityEpoch++
            MarkVisualDirty(chunk)
            MarkSaveDirty(chunk)
            if NearPlayerOrTool(chunk): MarkCollisionDirty(chunk)
            if DirtyTouchesBorder(chunk): MarkNeighborDirty(chunk)
```

限制规则：

- Brush 半径不小于 `1.5-2 * voxelSize`，否则会制造高频锯齿和碎三角。
- 每帧限制最大修改 sample 数；超出时合并/分帧。
- `lockedMask` 用于不可挖边界、底板、任务保护物、岩层。
- 每个 chunk 设置三角硬上限，超出时降分辨率、平滑或延迟更新。

## 7. 网格生成

### 7.1 Marching Cubes MVP

MVP 采用 Marching Cubes，因为实现快、资料多、容易在 Unity Jobs/Burst 或 Unreal TaskGraph 里跑通。

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

### 7.2 Surface Nets 生产评估

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

## 8. 动态碰撞设计

### 8.1 基本原则

挖掉的地方不能有碰撞，但 MeshCollider/Chaos collision cooking 不可能每次 brush 后立即完成。因此系统必须分两层：

```text
即时逻辑碰撞: SDF/density 查询，立刻生效
物理引擎碰撞: 低分辨率 mesh collider，异步/低频重建
```

对象策略：

| 对象 | 推荐方式 | 说明 |
|---|---|---|
| 手/铲子/钻头 | sphere/capsule vs SDF query | 必须即时反馈，不能等 collider |
| 玩家角色 | CharacterController/Capsule sweep + SDF ground probe | SDF 可否决旧 collider 的地面结果 |
| 普通掉落物 | 低模 MeshCollider/Chaos mesh | 可接受 50-150ms 延迟 |
| 射线/抓取 | 体素 DDA/SDF raymarch 后再 Physics.Raycast | 避免射中旧土 |
| 大型动态物体 | compound primitive 或限制进入可挖区 | 不要让高精地形碰撞参与复杂刚体 |

### 8.2 碰撞代理生成

视觉 `32^3` chunk，碰撞可以用 `16^3` 或更粗。

```text
视觉 density -> downsample -> clearanceBias -> collision mesh -> async bake/cook -> FixedUpdate swap
```

`clearanceBias` 的目的：让碰撞实体略微缩进实心区。宁可洞口碰撞比视觉洞口略大，也不要出现视觉已经挖掉但仍有隐形墙。

```csharp
float collisionIso = +clearanceBias;
bool IsCollisionSolid(float density) => density > collisionIso;
```

Unity 交换流程：

```csharp
void FixedUpdate() {
    scheduler.PumpVisualJobs(maxApplyPerFrame: 1);
    scheduler.PumpCollisionJobs(maxBakePerFrame: 1);

    while (finishedColliderQueue.TryDequeue(out DigChunk c)) {
        c.meshCollider.sharedMesh = null;
        c.meshCollider.cookingOptions =
            MeshColliderCookingOptions.CookForFasterSimulation |
            MeshColliderCookingOptions.UseFastMidphase;
        c.meshCollider.sharedMesh = c.GetInactiveCookedMesh();
        c.activeColliderEpoch = c.pendingColliderEpoch;
    }
}
```

Unity `Physics.BakeMesh` 可预烘 MeshCollider 数据，并可配合 Job System，但 Player 里需要 Read/Write mesh 数据可用；不要对同一个 mesh 并发 Bake。`MeshCollider.sharedMesh` 更换时仍在主线程执行。

高级兜底：ContactModifyEvent。

```csharp
void OnContactModify(PhysicsScene scene, NativeArray<ModifiableContactPair> pairs) {
    foreach (var pair in pairs) {
        for (int i = 0; i < pair.contactCount; i++) {
            float3 p = pair.GetPoint(i);
            if (!sdfSnapshot.IsSolid(p, clearance: 0.02f)) {
                pair.IgnoreContact(i);
            }
        }
    }
}
```

注意：ContactModify 回调可能在任意线程执行，只能访问线程安全、只读的 SDF snapshot，不能访问 Unity 对象。

### 8.3 为什么不能只靠 MeshCollider

本地算法模拟显示：

- Brush 后 density 已经 empty。
- 碰撞代理在重建前仍 solid。
- 只有 cook/swap 后 collision 才 empty。

因此“挖掉就无碰撞”的严格体验必须由 SDF 查询兜底。MeshCollider/Chaos 只是低频代理，服务普通刚体和稳定接触。

## 9. Compute Shader / GPU 路线

### 9.1 是否必须使用 Compute Shader

MVP 不需要，也不建议强依赖 Compute Shader。理由：

- 碰撞、角色查询、存档、网络权威都需要 CPU 数据。
- GPU 视觉 mesh 若要变成 MeshCollider，需要 GPU->CPU readback，再做 physics cooking。
- Unity `AsyncGPUReadback` 虽然避免即时 stall，但会增加数帧延迟，不适合“挖掉立刻无碰撞”的正确性链路。
- Quest 移动 GPU 带宽、热功耗和 compute 预算紧张；Foveated Rendering 主要减轻 pixel shading，不会自动降低 meshing compute 成本。

推荐分阶段：

```text
MVP/Quest:       CPU SDF 权威 + Burst Jobs 生成视觉/碰撞 mesh
生产/Quest:      CPU 权威 + GPU density 镜像用于预览、粒子、调试、culling
PCVR/高端:       GPU 视觉 meshing + indirect draw，CPU 低模碰撞代理
极限版:          GPU resident sparse brick + 自定义 renderer + CPU 碰撞低模权威
```

### 9.2 可选 Compute Shader 用法

适合 GPU 的阶段：

- 大量 brush 批量写入 GPU 镜像 density。
- GPU classify cells / prefix sum / emit visual triangles。
- GPU normal/material baking。
- GPU chunk culling / indirect draw。

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
    DigDirtyScheduler.cs
    DigSdfQuery.cs
    DigCharacterGroundProbe.cs
    DigContactModifier.cs
    DigSaveDelta.cs
  Jobs/
    ApplyBrushJob.cs
    BuildMarchingCubesJob.cs
    BuildSurfaceNetsJob.cs
    BuildCollisionMeshJob.cs
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
    public float voxelSize;
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
- 可选预生成初始 visual mesh 与 collision mesh。
- 生成 debug 预览。

### 10.3 运行时调度

```text
ApplyBrushQueue
  -> DensityDirty
  -> VisualDirtyQueue
  -> CollisionDirtyQueue
  -> SaveDirtyQueue
```

调度规则：

- 同一个 chunk 多个 brush op 合并。
- 近玩家、近手、视锥内 chunk 优先。
- visual mesh 可延迟 1-3 帧。
- collision mesh 可低频，stroke end 或 5-15Hz 更新。
- 队列过长时降低碰撞分辨率或冻结远处 chunk。

### 10.4 Mesh 提交

使用 Unity MeshData：

```csharp
var meshDataArray = Mesh.AllocateWritableMeshData(1);
var meshData = meshDataArray[0];

// Job 内填充 vertex/index/submesh。

Mesh.ApplyAndDisposeWritableMeshData(meshDataArray, chunk.visualMesh);
chunk.visualMesh.MarkDynamic();
```

不要在热路径使用：

- `new List<>` 反复分配。
- LINQ。
- 每帧字符串拼接。
- `RecalculateNormals` / `RecalculateBounds` 全量滥用。
- 同步高频 `MeshCollider.sharedMesh = mesh`。

### 10.5 XR/URP 设置

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
    uint32 VisualEpoch;
    uint32 CollisionEpoch;
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
- 对角色 Movement/Floor Check 增加 SDF 否决逻辑；dirty chunk cook 未完成时旧碰撞不能作为唯一地面依据。

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
- 视觉/collision 按本地队列异步生成。

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
- dirty chunk 数。
- VisualDirtyQueue 长度。
- CollisionDirtyQueue 长度。
- mesh build ms。
- mesh apply ms。
- collider bake/cook ms。
- 顶点/三角数。
- chunk draw calls。
- GC Alloc。
- SDF query 次数。
- ContactModify 忽略接触数。
- collider epoch 落后帧数。
- chunk 三角超限次数。

Quest 真机验收：

- Quest 2：单 DigVolume 连续挖 60 秒，72 FPS 稳定。
- Quest 3：90 FPS 目标。
- 无每帧 GC。
- 不出现玩家/手/工具撞到已挖空区域的可感知旧碰撞。
- collision cook 不产生明显 hitch。
- OVR Metrics 检查 FPS、App GPU/CPU time、throttling、stale frames、foveation level、eye buffer size。

## 14. 实施路线

### Phase 0: 技术 Spike

- 单个 `6m x 6m x 3m` DigVolume。
- `24^3` chunk，`voxelSize = 0.15m`。
- CPU density + Marching Cubes。
- 本地键鼠/VR 手柄 brush。
- SDF query 验证“挖掉即无碰撞”。

### Phase 1: Unity MVP

- Unity Jobs/Burst ApplyBrushJob。
- MeshData 生成 visual mesh。
- 低分辨率 collision mesh。
- MeshCollider 双缓冲与 `Physics.BakeMesh`。
- 玩家/手/工具 SDF 查询。
- 调试 HUD。
- Quest 2 72Hz 验收。

### Phase 2: 生产化

- Surface Nets A/B。
- 多 DigVolume streaming。
- chunk 池化、NativeArray 池化。
- 存档 BrushOp + chunk snapshot。
- 网络同步 BrushOp。
- 不可挖 mask、岩层、材质层。
- OVR Metrics/Profiler 自动化采样。

### Phase 3: 高端/PCVR

- GPU density mirror。
- Compute Shader brush preview/批量视觉写入。
- GPU visual meshing/indirect draw 实验。
- CPU 低模碰撞权威保留。
- Sparse brick / Transvoxel 评估。

## 15. 风险清单

| 风险 | 等级 | 缓解 |
|---|---|---|
| Collider cooking 单帧尖刺 | 高 | 低分辨率碰撞、异步 bake/cook、FixedUpdate 边界交换、每帧限量。 |
| 已挖空但旧 collider 仍挡玩家 | 高 | SDF query 兜底、ContactModifyEvent、玩家 ground probe 否决旧地面。 |
| 跨 chunk 裂缝/隐形墙 | 高 | halo、邻居 dirty、边界样本同步、collision clearanceBias。 |
| 三角数爆炸 | 高 | 最小 brush 半径、Surface Nets、三角上限、chunk 限预算。 |
| GPU readback 延迟 | 高 | 碰撞不依赖 GPU；GPU 只做视觉/镜像。 |
| Quest 热降频 | 高 | 按 72Hz/90Hz 预算设计，Foveated/Dynamic Resolution 只兜底。 |
| 网络不同步 | 中高 | 同步 BrushOp、固定顺序重放、chunk epoch/hash、周期 snapshot。 |
| AC 案例误判 | 中 | 只把 AC 当产品可行信号，不把它当算法证据。 |

## 16. 参考来源

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

第一版请不要追求“全地图自由挖掘”。正确的工程闭环是：

```text
一个局部 DigVolume
+ CPU 权威 narrow-band density/SDF
+ capsule brush
+ Marching Cubes
+ SDF 即时碰撞查询
+ 低模 MeshCollider/Chaos 延迟代理
+ 真机 profiling
```

当这个闭环在 Quest 2/3 上稳定后，再逐步扩展 Surface Nets、多区域 streaming、存档/网络、GPU 视觉镜像和 PCVR 高端路径。



### 相关记录

- [SDF（有向距离场）知识](./sdf-signed-distance-field.md) - density/SDF 表达和插值的基础概念。
- [ComputeShader GPGPU 基础概念](./compute-shader-gpgpu-basics.md) - Compute Shader 线程模型与 Buffer 使用基础。
- [GPU 视锥剔除 ComputeShader 实现](./gpu-frustum-culling-compute-shader.md) - GPU 并行剔除与 AppendBuffer 的可迁移经验。
- [Unity 3D Collider 类型性能消耗对比](./unity-collider-types-performance.md) - MeshCollider 与 primitive collider 性能边界。
- [移动端 TBDR 与 Overdraw](./mobile-tbdr-overdraw.md) - Quest/移动 GPU 带宽与过绘约束。
- [Unity 动态分辨率与注视点渲染冲突](./unity-dynamicres-foveated-conflict.md) - 该记录需收窄为 Unity 2022.3.39f1 特例/待复核，不能泛化为当前 Meta 文档结论。

### 验证记录

- [2026-06-25] 初次记录。来源为本轮多 Agent 并行调研、阿卡西本地相邻记录、官方文档/论文资料与本地算法模拟。模拟验证了 brush 后权威 density 立即为空、碰撞代理在重建前仍可能保持旧 solid 状态，因此强交互必须直接查询 SDF/density，MeshCollider/Chaos 只能作为延迟缓存。当前尚未在目标 Quest/PCVR 真机项目中实践，状态标为待验证。

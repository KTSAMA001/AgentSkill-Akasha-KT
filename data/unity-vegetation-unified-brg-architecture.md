# Unity 大规模植被系统的统一 BRG 架构：数据权威、空间分区与编辑事务

**标签**：#unity #architecture #rendering #editor #performance #culling #scriptable-object
**来源**：工程实践抽象 - Unity 大规模植被的数据、渲染与编辑架构
**收录日期**：2026-08-06
**更新日期**：2026-08-26
**状态**：📘 有效
**可信度**：⭐⭐⭐（核心模式有工程实现与自动化测试支撑；高级演进契约未全部落地，多视图、容量与平台边界仍需验证）
**适用版本**：Unity 2022.3 LTS 的 BatchRendererGroup API 模型；其它版本需复核 API 与图形后端行为

---

### 概要

本文讨论一种面向大规模植被的 Unity 架构：编辑模式与播放模式共享同一套 `BatchRendererGroup` 渲染实现，场景组件只负责数据授权和运行策略，编辑工具只负责数据编辑，空间分区与渲染 Batch 保持解耦。空间分区还可以承担增量编译、流式加载和内容所有权边界，但不自动决定绘制分桶。本文同时区分已经由参考实现和测试支撑的核心模式，以及尚未落地的高级演进契约，避免把架构目标误写成现成功能。

这套架构的核心不是“把所有代码塞进一个管理器”，而是建立清晰的不变量：作者数据只有一个权威来源；同一实例所有权域不能被多个提交者重复绘制；连续预览不等于正式提交；空间分区、GPU 数据布局和绘制分桶是三个相互独立的维度。对普通单场景工作流，可以进一步采用“一个 Unity Scene 只有一个渲染会话”的简化政策；2026-08-25 参考实现没有采用该简化政策，而是把每个运行时 Cell 定义为独立所有权域。

长文可按问题阅读：第一至五节建立术语、职责和所有权；第六至九节解释数据、加载、GPU 与剔除；第十至十二节解释编辑事务、缓存和刷新；第十三至十六节用于方案选择、验证与反模式检查。只想理解当前工程快照的读者，可先读“本文与参考实现的关系”、第二节术语、第七节和相关记录。

## 一、问题定义与适用范围

本文面向熟悉 Unity Scene、ScriptableObject、Job System 和渲染基础概念的工程师。文中的“大规模”不是固定实例数量，而是指逐株 GameObject、逐对象 Renderer 或逐对象生命周期管理已经不再适合，需要集中式实例数据、批量提交和空间工作集管理的规模。

本文讨论架构职责和数据流，不直接解决以下问题：

- GPU 遮挡剔除算法。
- 特定 Shader、渲染管线或 XR 变体兼容。
- 资源包和流式 IO 的具体实现。
- 植被交互、弯曲和物理模拟。
- 任意目标设备上的固定实例上限或性能保证。

大规模植被系统通常同时服务以下场景：

- 编辑器中刷写、擦除、选择、移动和替换植被。
- SceneView 与非播放状态的 GameView 预览。
- 播放模式中的相机渲染、LOD、阴影和视锥剔除。
- 根据玩家、相机或其它参考物体激活附近区域。
- 在不创建逐株 GameObject 的前提下保存大量实例。

如果这些能力分别实现，很容易形成多个相互竞争的系统：

- 编辑器预览和运行时各有一套渲染算法。
- 植被笔刷工具、Inspector、Overlay 或其它编辑器界面分别持有渲染资源。
- 空间分区被直接映射为多个渲染器、Buffer 或 Batch。
- 鼠标移动、窗口 Repaint 和资源扫描触发整场重建。
- 编辑数据、编译缓存、运行快照和临时预览互相覆盖。

本文给出的架构适合作为以下条件下的默认方案：

1. 植被实例以静态或低频修改为主。
2. 单个场景上下文中的实例数据能够全部驻留 GPU，或按固定容量的 Buffer Page 分页驻留。
3. 编辑模式和播放模式不需要同时对同一场景提交植被绘制。
4. 植被资产能够通过稳定实例标识建立持久引用。
5. 运行时空间激活主要改变可见工作集，而不是频繁搬迁完整实例属性。

对于超大开放世界、多场景并行编辑、服务器动态生成或必须异步卸载实例属性的系统，应保留本文的职责边界，但采用后文所述的分片变体。

### 本文与参考实现的关系

本文是一篇独立的架构论文，不是某个项目版本的交付报告。下文中的“应”“必须”和“推荐”描述设计约束或演进目标，并不自动表示参考实现已经完整覆盖。当前参考实现仅用来回答两个问题：这些职责边界是否能在真实 Unity 工程中成立，以及哪些简化政策已经得到代码和测试证据支撑。

先说明一个容易造成误读的术语差异：本文历史上把最小空间分区统称为 **Cell**；2026-08-25 的参考实现把这个层级命名为 **Heap**，并把“一个管理器组件 + 一份场景植被资产 + 一套独立运行资源”命名为 **运行时 Cell**。因此，除非段落明确写“运行时 Cell”，本文后续的通用 `Cell` 均应映射为该实现中的 `Heap`，而不是管理器所代表的较大加载单元。

阅读覆盖表前可先记住六个实现词：运行时 Cell 是加载与资源所有权边界；Heap 是其内部空间块；SceneGuid 标识一份场景植被资产；HeapGuid 由 SceneGuid 与 Heap 坐标确定性生成；StableGuid 是实例在该资产内的持久身份；RuntimeIndex 和 HeapBase 只在加载后组合成临时 GPU 地址。QueryWorld 是每运行时 Cell 的解析查询数据，ColliderStreamer 是每运行时 Cell 的 PhysX 代理状态机。

当前作者链中的 Prefab、Prototype 与 SceneAsset 是三层关系，而不是三个并列权威源：普通 Prefab 是原型烘焙的作者输入，烘焙器在隔离的 Prefab Contents 中读取 Authoring、LOD、Renderer 和显式标记的碰撞信息；`PrototypeAsset` 是由该输入生成的静态绘制与碰撞描述，并以 PrototypeGuid 标识；`SceneAsset` 的 PrototypeTable 引用这些 Prototype，实例只保存 PrototypeId、StableGuid 和 Heap 局部 TRS。运行时按 PrototypeTable 和实例记录集中提交 BRG，不会为每株植被实例化原始 Prefab。因而 Prefab 不是运行时实例权威，Prototype 也不拥有场景中的逐株位置。

当前 `HeapMask` 也有单独且有限的语义：每个已加载运行时 Cell 各自持有一份按 SceneAsset 当前 Heap 顺序索引的一字节掩码；管理器把 Heap Bounds 变换到世界空间，再依据兴趣源距离与加载/卸载迟滞更新对应位。`VegetationBrgWorld` 在写入新掩码前等待既有剔除 Job，并把结果交给 Heap 粗筛及后续 Count/Scatter 的 Heap 可见门禁。它只回答“本次剔除是否继续处理这个 Heap”，不表示 Heap 资源已经单独 Loaded 或 Unloaded，也不会触发 Heap 级 Buffer 上传、缩容或释放。

“当前参考实现”主体固定指 2026-08-25 的匿名工程快照：Unity `2022.3.62f3`、URP 14、Android 构建目标配置，证据来自当日源码静态复核与同轮 Unity Test Runner（EditMode `239/239`、PlayMode `11/11`）。2026-08-26 又叠加两个相互独立的候选增量：物理 QueryWorld 的 Heap/Shape 两级懒建 BVH，以及 BRG 固定逐株区由 `128 B` 收敛到 `32 B` 的量化 ABI；最终严格回归为 EditMode `244/244`、PlayMode `11/11`。作者、编译和完整 Cell 卸载主链仍按 2026-08-25 主体陈述，本文的 Buffer 公式、上传、预览与 CPU/GPU 量化口径则按 2026-08-26 候选陈述。该候选有实际 Buffer 回读和 Editor 渲染证据，但当时没有绑定不可变 VCS 源码摘要。阿卡西记录按规则不保存私有仓库路径、提交号和 RunId，因此这些实现行属于有边界的工程快照证据，不是读者仅凭本文即可复跑的公开基准；设备数字与实验条件只在专门性能记录中陈述。

匿名证据索引保留到类与入口粒度：作者分区与身份由 `VegetationSceneAsset`、`VegetationRegionHeap`、`VegetationSceneEditSession.Commit` 和 `VegetationSceneCompiler.RefreshAffected` 复核；加载与槽位由 `VegetationCellManager.LoadCell/UnloadCell`、`VegetationSceneBatch` 和 `VegetationBrgWorld` 复核；32 B ABI 与 CPU/GPU 解码口径由 `VegetationRenderDataLayout`、`PackedVegetationInstanceData` 和 BRG Shader 复核；剔除由 `CullVegetationHeapsJob`、`CountVegetationInstancesWithLodReferenceJob` 与 `ScatterVegetationVisibleInstancesJob` 复核；物理由 `VegetationCellPhysicsRuntime` 与 `VegetationColliderStreamer` 复核。它能说明结论来自哪些机制，但因不包含可检出的私有快照标识，仍不能让外部读者独立还原该工程版本。

| 覆盖级别 | 当前参考实现的事实边界 | 阅读时应如何理解 |
|----------|------------------------|------------------|
| 已覆盖 | 编辑模式和播放模式创建同一种 BRG 后端与数据布局；编辑器宿主为每个已加载且有效的运行时 Cell 建立独立会话，工具窗口不拥有会话；Prefab Stage、PlayMode 切换和 Scene 卸载都有释放路径 | 统一的是后端协议，不是跨运行时 Cell 共享同一个 BRG 对象 |
| 已覆盖 | 一个运行时 Cell 绑定一份场景植被资产；资产内含多个 Heap。每个已加载运行时 Cell 独立创建 BRG、GPU Buffer、剔除快照、查询世界和碰撞流送器；多个 Additive Scene 可并存并共享兴趣源 | 当前实现选择“运行时 Cell 作为资源与生命周期隔离边界，Heap 作为其内部空间分区”，不能再把两者写成同一层级 |
| 已覆盖 | 单个运行时 Cell 的全部 Heap 与实例一次上传到一块 GPU Buffer；2026-08-26 候选的固定逐株记录为 32 B，另加 8 B 或 20 B 的稀疏光照记录和每 Heap 128 B 量化参数 | 32 B 只接受有限、无剪切、非镜像、正数统一缩放；Heap 激活只更新剔除掩码，不会按 Heap 上传、释放或缩小 Buffer。真正释放发生在整个运行时 Cell 卸载时 |
| 已覆盖 | 每次 BRG 视图回调先做 Heap 粗筛，再对本运行时 Cell 全部实例执行 Count 和 Scatter 两遍 Job；失活 Heap 的实例只在 Job 内提前退出 | 复杂度仍近似 `O(本运行时 Cell 总实例数 × Camera/Light 视图数)`，不能把 Heap 掩码描述成紧凑实例工作集 |
| 部分覆盖 | Paint/Erase 与 Replace/Reproject/Transform 都先暂存作者数据；变换拖动只修改预览矩阵；正式提交形成一个 Undo 边界并保留跨 Heap 移动实例的 StableGuid | 范围操作会尝试用外层 Undo 回滚作者资产；普通增量编译仍逐 Heap 写回，派生缓存与 BRG 恢复未被证明为完整两阶段事务 |
| 已覆盖 | Heap 坐标由运行时 Cell 局部位置、分区原点和尺寸计算；HeapGuid 由 SceneGuid 与坐标确定性生成；实例以 Heap 局部 TRS、PrototypeId 和 StableGuid 保存，RuntimeIndex 只在 Heap 内连续 | GPU 全局槽位在加载时由 HeapBase 与 RuntimeIndex 派生，不得把 RuntimeIndex 当作持久身份或跨 Heap 地址 |
| 部分覆盖 | 统一兴趣源向每个运行时 Cell 广播位置、运动预测和优先级；物理加载/卸载半径、固定步激活预算、QueryWorld 与 ColliderStreamer 归各运行时 Cell 所有；大集合 QueryWorld 使用 Heap/Shape 两级懒建 BVH | 多运行时 Cell 所有权隔离已覆盖，但预算和 `Physics.SyncTransforms` 仍按运行时 Cell 计，尚无全局调度器；少于 64 项仍线性，冷建树/增删重建与最坏全扫未做 Quest 验证，且外层视觉 Heap Bounds 仍可能漏包 Query Shape |
| 部分覆盖 | 每个视图都有独立 culling callback 和投影参数，阴影视图不写普通相机的 LOD 历史；但多个普通相机仍共享同一份 `PreviousLod` 数组，运行时激活集合也只来自主相机与显式参考物体 | 后文的每视图 LOD 历史、视图淘汰和所有受支持视图保守并集属于待演进契约 |
| 部分覆盖 | 每次 culling 回调的新 Job 链都以旧最终 Handle 为前置依赖，因此修改和释放前等待覆盖旧任务的传递聚合链；预览会原地更新公开 GPU Buffer 的矩阵和 CPU 包围体 | 当前同步重建路径不等于 Closing/Retiring 热切换协议；CPU Job 完成和原地 Buffer 更新也不等于 GPU 在途使用已经退役 |
| 未覆盖 | Buffer Page、单运行时 Cell 内多 Batch、异步实例属性流式加载、紧凑实例工作集、跨资产世界命名空间、会话世代、视图历史淘汰和跨运行时 Cell 全局加载预算 | 这些内容是为规模扩大准备的架构契约和验证清单，不能据此声称参考实现已经支持 |

2026-08-25 主体快照的严格自动化门禁为 EditMode `239/239`、PlayMode `11/11`，覆盖 BRG 创建释放、Heap 激活、查询与代理生命周期、场景授权、同场景多运行时 Cell、Additive Scene、变换预览、StableGuid 和 Undo 主流程。2026-08-26 最终候选为 EditMode `244/244`、PlayMode `11/11`：查询增量新增大集合解析查询与索引同步门禁；Buffer 增量补强 32 B 金样、Half/矩阵范围失败、整段 GPU 回读、预览和 Cell/Origin 失败事务，以及真实 SRP 前景 Mask。它证明逻辑 Buffer 请求与回读长度下降及当前 Editor 闭环，没有证明冷建树、Quest 帧耗、GPU 带宽、物理显存或四个 Shader Pass 的真机视觉等价。这些结果来自 Unity 2022.3 LTS 的 Windows Editor、Android 构建目标配置，也没有证明保存失败、部分编译失败、GPU 在途预览退役、多普通相机 LOD 隔离或长时间编辑交互。本文的“有效”状态表示架构论证与已覆盖核心模式相符，不表示所有高级扩展均已实现。

### 当前快照的连续寻址与加载链

下面只描述当前单 Buffer、单 Batch 的事实路径，不包含后文的分页与多 Batch 目标契约：

```text
Painter 提交运行时 Cell 局部位置
  → floor((position - partitionOrigin) / heapSize) 得到 HeapCoordinate
  → 首次触及坐标时，在 Commit 阶段创建内嵌 Heap
  → SceneGuid + HeapCoordinate 确定性生成 HeapGuid
  → Compiler 在该 Heap 内按 PrototypeId、Morton、StableGuid 排序
  → Compiler 分配 Heap 内连续 RuntimeIndex
  → 运行时 Cell 加载时按 SceneAsset 的 Heap 顺序扫描
  → 前序 Heap 实例总数形成当前 HeapBase（不序列化）
  → GPU Slot = HeapBase + RuntimeIndex
  → 同一个数值写入剔除快照的 GlobalInstanceIndex
  → 当前仅一个 BRG Batch，因此 BatchLocalIndex = GPU Slot
  → Count/Scatter 按 RenderBucket 生成 visibleInstances 与 DrawCommand
```

Heap 在作者 Commit 时成为 SceneAsset 的权威内嵌记录；排序、RuntimeIndex 和光照表在 Compile 时生成；HeapBase、GPU Slot、BatchLocalIndex 只在运行时 Cell 加载并构建当前批次时派生。后文出现的 PageID、多 Batch 或 `BatchRegistrationPolicy` 都是目标契约，不能倒推为当前路径已经存在的额外寻址层。

当前非空运行时 Cell 的 GPU Raw Buffer 可按下式复算：

```text
N = 实例数，H = Heap 数，C = StaticLightColor 记录数，S = StaticBakerySh 记录数
bytes = Align16(
          Align16(96 + 32×max(1,N) + 128×max(1,H) + 8×max(1,C))
          + 20×max(1,S))
```

其中 96 B 是 64 B 合法零地址哨兵与两组 16 B 运行时 Cell 风场参数；逐株 32 B 保存三个 float32 世界位置、smallest-three `10:10:10:2` 旋转、Half/UNorm16 连续参数、UInt16 HeapIndex，以及 1 位光照模式与 31 位稀疏记录索引。它成立的前提是最终矩阵必须有限、无剪切、非镜像且为正数统一缩放；CPU 剔除使用同一量化后 TRS，并对风摆 Half 取原值与恢复值中的较大者扩展 Bounds。8 B 对应 `StaticLightColor`，20 B 对应 `StaticBakerySh`，每 Heap 128 B 是两种光照的量化参数。`max(1, …)` 和 `Align16` 来自空表合法寻址与 Raw Buffer 对齐。该公式只统计这一块静态 GPU Raw Buffer，不包含 CPU 托管快照、Persistent NativeArray、BRG Metadata、Mesh/Material、每视图 visibleInstances、TempJob 输出或驱动内部副本；完整字段和证据边界见专门的 32 B ABI 记录。

### 当前快照的端到端运行流程

下面把当前已覆盖路径串成一条链；其中“预览”是编辑期旁路，“多运行时 Cell”表示多套相互隔离的同构会话，并不改变单 Cell 内的步骤：

```text
Prefab 作者输入
  → 烘焙为 PrototypeAsset
  → SceneAsset.PrototypeTable 建立 PrototypeId 映射
  → Painter 取得一个运行时 Cell 的作者 Authority
  → Stage/Preview 只改内存候选或预览矩阵
  → Commit 按坐标创建或更新内嵌 Heap，并保存 StableGuid + PrototypeId + Heap 局部 TRS
  → Compile 对受影响 Heap 排序，生成 RuntimeIndex、Bounds、光照表和 Hash
  → 运行时 Cell 加载：创建独立 BRG、Raw Buffer、剔除快照、QueryWorld 与 ColliderStreamer
  → 按 Heap 顺序派生 HeapBase 与 GPU Slot，把量化后的 32 B 逐株记录及共享光照表一次上传
  → 兴趣源与迟滞更新该 Cell 独立的 HeapMask
  → 每视图回调执行 Heap 粗筛 → 全实例 Count → LOD/RenderBucket → Prefix → 全实例 Scatter
  → 多运行时 Cell 分别执行同一链路，共享兴趣源但不共享 SceneAsset、BRG、Buffer、HeapMask、查询或代理
  → 外部 Floating Origin 协调器可在运行中触发 Rebase；渲染侧重建完整 32 B 记录与剔除快照，物理侧按同一增量平移查询世界和代理
  → 编辑预览可原地修补当前会话；正式提交后再由刷新链重建或更新派生状态
  → 整个运行时 Cell 越过卸载半径：排空 CPU Job → 移除 BRG 可回调状态 → 释放 NativeArray/Prototype 引用/Batch/Buffer
  → 物理侧反注册 Heap、归还代理并释放 QueryWorld；外层场景或资源句柄负责资产及 Mesh/Material 的最终卸载
```

这里的 HeapMask 失活只减少后续细处理和绘制，不减少当前 Count/Scatter 的调度长度；只有最后的整运行时 Cell 卸载才释放其 BRG、Buffer、查询世界和物理代理资源。

### 当前 Rebase、Floating Origin 与 Cell Transform 更新

本文的 **Rebase** 只表示修改累计 Floating Origin 偏移，不表示重新计算 `HeapCoordinate`、重建 Heap 或改写 SceneAsset。渲染坐标的核心关系是：

```text
renderMatrix = Translate(-absoluteOriginOffset)
               × CellTransform.LocalToWorld
               × authoredCellLocalTRS
```

因此，Rebase 前后保持不变的是 SceneAsset 中的 Heap 局部 TRS、HeapCoordinate、HeapGuid、StableGuid、Compile 得到的 RuntimeIndex，以及由当前 Heap 顺序派生的 HeapBase/GPU Slot；变化的是实例、Heap Bounds、风场空间原点、查询形状和物理代理在当前渲染/物理世界中的坐标。每次编码都从 SceneAsset 的高精度局部 TRS 重新开始，不会把上一次 32 B 量化结果当作下一次输入。

当前渲染入口接收**新的累计绝对偏移**。它先拒绝 NaN/Infinity，再在互斥区完成上一条剔除 Job，并保存现有 HeapMask。若 Cell 尚未加载，只缓存偏移供之后建批使用；若已经加载，则按以下顺序更新：

```text
旧 CellTransform + 新 absoluteOriginOffset
  → 构建候选 CPU 剔除 Snapshot
  → 从权威局部 TRS 编码并全量上传候选 32 B Buffer，同时更新风场空间参数
  → 两步成功后清理旧预览，发布 SceneBatch 的 Origin、StableGuid→Slot 反查与公开 Snapshot
  → World 发布同一 Origin，重建 Persistent NativeArray，并按原索引恢复 HeapMask
```

Half 上溢、最终统一缩放下溢或非有限 Origin 会在相关字段发布前失败；现有回归覆盖这些输入失败时旧 Origin、CellTransform、公开 Snapshot、完整 Buffer 和预览保持不变。该事务证据只覆盖验证、编码与上传失败，不证明后续 Persistent NativeArray 分配失败可以原子回滚，也不提供 GPU 在途读取的 Fence/世代退役。

管理器 Transform 变化不是 Rebase。运行时管理器每帧提取有限、无剪切、非镜像的正数统一缩放 CellTransform；值变化时，以“新 CellTransform + 现有 absoluteOriginOffset”走同一候选 Snapshot、完整 Buffer 上传和成功后发布链。它会改变最终世界 TRS、Bounds、风摆距离和 32 B 量化值，但同样不改 SceneAsset 分桶、StableGuid 或编译顺序。

物理侧使用的是**本次偏移增量**：QueryWorld 把 Heap/Shape 广相位整体平移 `-delta`；ColliderStreamer 同步平移缓存描述和当前代理，并把多次调用合并到下一次物理同步。当前插件提供了渲染绝对偏移、查询增量和平移代理三组入口，但没有内建一个把所有已加载运行时 Cell 与三个子系统原子广播的全局 Floating Origin 协调器；生产接入方必须按同一世代分发 `absoluteOriginOffset` 与 `delta`。现有测试证明各入口的局部坐标和身份保持规则，不证明跨渲染、查询、PhysX 的失败恢复原子性。

## 二、术语

### BatchRendererGroup

`BatchRendererGroup`，下文简称 **BRG**，是 Unity 提供的底层批量渲染接口。应用负责：

- 注册 Mesh 和 Material。
- 提供每实例 GPU 数据及其元数据布局。
- 在 Unity 请求剔除结果时生成可见实例索引和绘制命令。
- 管理相关 Buffer、Native 容器和 Job 生命周期。

BRG 不会自动决定场景数据从哪里来，也不会替编辑工具管理 Undo、资产保存或空间激活。

### 场景上下文与渲染会话

**场景上下文**是拥有独立数据授权和绘制所有权的逻辑域。它可以是一个 Unity Scene、一个聚合 World、一个 Prefab Stage，或一个专用 Preview Scene。

**渲染会话**是在某个场景上下文中持有 BRG、GPU Buffer、运行快照和绘制提交权的生命周期对象。共享后端实现不代表所有上下文共用同一个会话对象。

### 场景植被资产

本文所称“场景植被资产”是一个自定义 `ScriptableObject` 数据资产，不是 Unity Scene 文件。它保存一个场景上下文中的植被作者数据，例如：

- 原型引用。
- 空间块。
- 植被实例。
- 稳定实例 ID。
- 数据修订号。

场景植被资产是实例内容的权威来源，但不要求把相机、激活半径、更新时间间隔等运行策略也存入该资产。

### 空间块

**空间块**是植被实例的空间组织单元，常见命名包括 `Cell`、`Chunk`、`Region` 或 `Heap`。为保持本文历史术语稳定，下文仍统一使用 **Cell**；映射到 2026-08-25 的参考实现时，它就是资产内嵌的 **Heap**。

一个 Cell 通常包含：

- 世界空间包围盒或包围球。
- 区域原点或坐标。
- 属于该区域的实例集合。
- 局部修订号和可再生编译信息。

在本文默认模型中，一个实例在同一编译快照内只属于一个空间 Cell。它是否来自规则网格、人工划分、四叉树叶节点或其它分区算法，不影响后续职责模型。参考实现另有一个更大的“运行时 Cell”概念：一个场景管理器绑定一份场景植被资产，资产包含多个 Heap；两种 Cell 不能混称。

### 原型

**原型**描述一类植被的渲染资源和规则，例如：

- Mesh、Material 和 SubMesh。
- LOD 层级。
- 阴影绘制部件。
- 局部包围盒。
- 风摆位移上限。

实例只保存原型引用和每实例参数，不重复保存整套渲染资源。

### 稳定 ID、逻辑索引、Buffer 地址与可见索引

以下四种标识不能混为一谈：

- **稳定 ID**：实例的持久身份，用于保存、选择、Undo 和跨编译定位。
- **逻辑实例索引**：某一运行快照中，实例在 CPU 连续数组里的位置。
- **Buffer 地址**：实例属性在 GPU 中的位置。单 Buffer 时可以表示为 Slot；分页时应表示为 `PageID + LocalSlot`。
- **可见索引**：某个相机或阴影视图当前提交给 BRG 的批次内实例索引。

稳定 ID 应跨编辑提交保持不变。逻辑实例索引和 Buffer 地址可以在完整重编译后变化，因此系统需要维护：

```text
稳定 ID
  → 当前逻辑实例索引
  → PageID + LocalSlot
```

单 Batch 实现中，可见索引可以直接等于 Buffer Slot；多 Page 或多 Batch 实现中，可见索引必须相对于对应 DrawCommand 的 Batch 解释，不能把它当作全局 GPU 地址。

存储寻址与绘制分类是两条不同映射：

```text
StableID
  → LogicalIndex
  → PageID + LocalSlot

LogicalInstance + LOD + Pass + RenderPart
  → RenderBucketKey

PageID + LocalSlot + RenderBucketKey
  → BatchRegistrationPolicy
  → 一个或多个兼容的 (BatchID, BatchLocalIndex, RenderBucketKey)

(BatchID, RenderBucketKey)
  → 一个或多个 DrawCommand
```

默认分页政策可以规定“一个 Page 注册为一个 Batch，`LocalSlot` 等于 `BatchLocalIndex`”。但这只是简化政策，不是 BRG 不变量：同一个 GraphicsBuffer 可以参与多个 Batch 注册，一个存储位置也可能按不同 Metadata 或注册策略映射到不同 Batch。

`BatchRegistrationPolicy` 必须同时检查存储 Page、Metadata 布局和 `RenderBucketKey` 的兼容性，只枚举能够解释该实例数据并服务对应 RenderPart/Pass 的注册。不能先取得所有 Batch 再与所有绘制桶做笛卡尔积，否则会重复绘制或使用不兼容的 Metadata。

一个实例还可能因为多个 SubMesh、阴影部件或 Pass 同时进入多个绘制桶，因此 `BatchID` 不能成为稳定身份到物理存储地址的固定单值中间节点。

稳定 ID 还必须有明确作用域。推荐把世界级身份表示为：

```text
AssetPersistentId + InstanceStableId
```

其中：

- `AssetPersistentId` 只在同一资产文件身份保持不变期间稳定。资产复制或拆分时，是否重映射身份取决于后文选择的命名空间政策。
- `InstanceStableId` 在所属资产内唯一，删除后不复用。
- 复制实例必须生成新的 `InstanceStableId`。
- 在同一资产内移动或重新分配 Cell 时保留身份。
- 跨资产迁移时，由事务生成目标身份并记录旧身份到新身份的重映射。
- 合并资产或加载多个 Scene 时，必须检测复合身份冲突，不能依赖数组位置消除冲突。

ID 生成不能依赖会随 Undo 回退的简单序列化计数器。推荐使用高熵随机 ID，并在资产导入、复制、合并和运行时烘焙时执行冲突检查。另一种方案是不参与 Undo 的单调高水位加墓碑集合，但其持久化和迁移复杂度更高。Undo 恢复被删除实例时恢复原身份，新建实例仍生成新的 ID。

检测到复合身份冲突时，默认行为应是阻止聚合、编译或发布，不能静默保留其中一方。修复必须通过可 Undo 的显式事务完成，并生成旧身份到新身份的重映射表；所有能够解析的外部持久引用必须在同一事务中迁移，存在无法迁移的引用时应终止修复并报告。

资产复制和拆分必须预先选择一种身份政策：

### 物理资产命名空间

世界身份使用 `AssetPersistentId + InstanceStableId`。

- 普通整资产复制必须生成新的 `AssetPersistentId`。实例 ID 可以保留，因为命名空间已经改变；克隆资产内能够解析的复合引用必须改写到新资产命名空间。
- 资产拆分产生的新资产拥有新的 `AssetPersistentId`。迁移实例的复合身份发生变化，必须通过重映射表更新外部引用。

### 世界命名空间

世界身份使用 `WorldNamespaceId + InstanceStableId`，物理 `AssetPersistentId` 只描述存储位置。

- 普通整资产复制代表新的世界内容时，必须生成新的 `WorldNamespaceId`，或者重新生成全部实例 ID 并迁移克隆资产内的引用。
- 只有显式执行“同世界分片”操作时，多个物理资产才允许保留同一个 `WorldNamespaceId`；这些分片的实例 ID 集合必须互不重叠。
- 导入、聚合和构建阶段必须检查所有分片中的 `(WorldNamespaceId, InstanceStableId)` 冲突。

通用 Duplicate 命令不能被当成“同世界分片”命令；保留世界命名空间必须是显式、可审计的操作。

### Buffer Page

**Buffer Page** 是实例数据超过单 Buffer 容量、常量 Buffer 窗口或项目设定上限时使用的固定容量分段。分页只改变物理存储和 Batch 映射，不应改变稳定 ID 或作者数据结构。

### Batch、绘制桶与 Draw Call

- **BRG Batch**：在本文限定的 Unity 2022.3 API 模型中，一次 `AddBatch` 注册的一个 `GraphicsBuffer`、一组 Metadata 和对应 `BatchID`。多个 Buffer Page 通常需要多个 Batch，或由额外适配层组织。
- **绘制桶**：共享一组可合并绘制状态的实例集合。Mesh、Material、SubMesh、LOD 和阴影状态只是常见维度；实际分桶键必须覆盖所有影响 DrawCommand、过滤条件和渲染状态的字段。
- **Draw Call**：最终提交给图形 API 的一次绘制命令。

一个共享 Buffer 不代表只有一个 Batch；一个 Batch 也不代表只有一个 Draw Call。

### 权威数据、派生缓存、运行快照与预览状态

- **权威作者数据**：用户真正编辑和保存的实例、原型引用与空间归属。
- **派生缓存**：由权威数据生成的排序、Hash、连续数组或照明数据；可以删除并重新生成。
- **运行快照**：供 BRG 与 Job 读取的不可变或版本化数据。
- **预览状态**：鼠标拖动期间的临时覆盖，不属于正式资产。

派生缓存和运行快照都不能成为第二份权威数据。

### 架构总览

```text
权威作者数据
  ├── 原型、Cell、实例与稳定身份
  └── 运行策略由场景授权组件提供
          │
          ├── 正式编辑事务
          │     → 校验与修订传播
          │     → 派生缓存
          │     → 不可变运行快照
          │
          └── 临时预览状态
                → Preview Overlay / 备用快照

不可变运行快照
  → BRG 渲染会话
  → 世界级 ActiveCellSet
  → 每视图 Cell/实例剔除
  → 每视图 LOD 状态
  → visibleInstances 与 DrawCommand
```

编辑工具只能进入“正式编辑事务”或“临时预览状态”两条通道，不能绕过宿主直接控制 BRG 会话。

## 三、设计不变量与可替换政策

为了避免把某一种项目配置误写成普遍定律，需要区分“不变量”和“默认政策”。

### 架构不变量

1. **编辑器与运行时共享同一后端实现和数据布局。**
2. **同一实例所有权域不能存在范围重叠的绘制提交者。**
3. **正式实例内容只有一个权威作者数据来源。**
4. **编辑工具不直接创建实例渲染器或提交 DrawCommand。**
5. **预览状态与正式提交分离。**
6. **空间 Cell 与渲染绘制桶正交。**
7. **BRG 剔除回调只读取一致的运行快照。**

“共享同一后端”指共享算法、数据协议和资源模型，并不要求整个进程永远只有一个后端对象。多个 Scene、多个独立世界或专用 Preview Scene 可以各自持有会话，只要它们的实例集合和提交所有权不重叠。

### 默认政策

对普通单场景工作流，可以采用以下默认政策：

- 当前场景只允许一个有效的植被授权组件。
- 一个场景上下文同时只保留一个植被渲染会话。
- 编辑模式由编辑器宿主持有渲染会话。
- 播放模式由运行时宿主持有渲染会话。
- Prefab Stage 和资产预览不显示主场景植被。
- 一个场景资产内部包含多个 Cell。

这些是降低复杂度的工程选择，不是 BRG API 的硬性限制。

2026-08-25 参考实现采用另一条已明确的政策：**每个运行时 Cell 是一个实例与资源所有权域**。同一 Unity Scene 可以有多个运行时 Cell，每个管理器绑定独立 SceneAsset，并由编辑器宿主建立独立 BRG/Buffer 会话；Painter 同一时刻仍只授予其中一个运行时 Cell 作者写权限。因而“多个运行时 Cell 会话并存”与“只有一个当前作者 Authority”不冲突，也不代表多个管理器共享同一个会话。上面的单场景表只适用于选择了简化政策的其它实现，不是当前快照描述。

### 必须显式定义的可替换政策

- 禁用的管理组件是否参与授权冲突检测。
- Additive Scene 是每个 Scene 独立授权，还是由世界级聚合器统一授权。
- Cell 是规则网格、人工区域还是层级空间结构。
- 实例 Buffer 是单块、分页还是按流式分片。
- 原型变化是局部更新、整 Cell 重编译还是整场重建。

实现必须把这些政策写成明确规则，不能依赖组件查找顺序或隐式约定。

## 四、职责模型

| 角色 | 核心职责 | 禁止承担的职责 |
|------|----------|----------------|
| 场景植被资产 | 保存权威作者数据和可再生缓存 | 控制编辑器窗口；主动提交渲染 |
| 场景授权组件 | 指定当前场景使用的资产；保存运行策略 | 实现第二套渲染算法；包含编辑器绘制代码 |
| BRG 后端 | 注册资源、上传 Buffer、维护运行快照、执行剔除和生成 DrawCommand | 搜索场景组件；读取植被笔刷工具的内部状态 |
| 编辑器宿主 | 解析编辑场景授权；创建、刷新和释放 BRG 会话 | 允许工具任意绕过场景授权指定资产 |
| 运行时宿主 | 管理播放模式会话；更新参考物体和 Cell 激活状态 | 负责编辑器 Undo 或 AssetDatabase 操作 |
| 编辑工具 | 修改作者数据；管理选择、笔刷、事务和 Undo | 持有 BRG 生命周期；直接提交实例绘制 |
| 预览通道 | 保存临时覆盖；通知宿主把覆盖转交给渲染会话 | 写入正式资产 |
| 变更通道 | 发布资产、Cell、原型和修订号的正式变化 | 直接执行渲染或篡改作者数据 |

场景授权组件是“授权者和运行策略宿主”，不是渲染算法本身。BRG 后端应当是可创建、可释放、与 `UnityEditor` 解耦的普通运行时对象。

## 五、生命周期与提交所有权

### 单场景默认状态

| 上下文 | 授权条件 | 渲染会话所有者 | 是否允许正式编辑 |
|--------|----------|----------------|------------------|
| 普通编辑模式 | 存在唯一有效授权 | 编辑器宿主 | 是 |
| 播放模式 | 存在有效运行时授权 | 运行时宿主 | 通常否 |
| Prefab Stage | 不使用主场景授权 | 无，或专用预览宿主 | 否 |
| 资产 Preview Scene | 不使用主场景授权 | 专用预览宿主 | 否 |
| 无有效授权 | 无 | 无 | 否 |
| 授权冲突 | 多个候选 | 无，并报告配置错误 | 否 |

“有效授权”的候选规则必须明确。例如可以规定：只有位于当前场景、已加载、启用且绑定有效资产的组件才参与候选；候选为零表示未授权，候选大于一表示冲突。

编辑器中的授权解析不能替代播放模式的所有权门禁。所有能够创建运行会话的入口都必须按场景上下文或实例所有权域登记并拒绝重叠提交者；仅限制单个 GameObject 上不能重复挂载组件，无法阻止场景中多个对象分别创建会话。

### 模式切换

```text
普通编辑模式
  → 编辑器宿主解析授权
  → 创建编辑会话

进入播放模式
  → 先释放编辑会话
  → 运行时宿主创建运行会话

退出播放模式
  → 释放运行会话
  → 重新解析当前编辑场景授权
  → 恢复编辑会话
```

会话切换的关键不是“谁先 Repaint”，而是资源所有权明确转移。任意时刻都不能让两个会话对同一场景上下文重复提交实例。

### 多场景变体

多场景同时加载时，必须选择一种明确模型：

1. **每 Scene 独立会话**：每个 Scene 有自己的资产、授权者和 BRG 会话。
2. **世界级聚合会话**：世界管理器收集多个 Scene 的资产，由一个聚合后端提交。

不能继续使用“活动场景里找第一个组件”作为隐含规则，否则 SceneView、Additive Scene 和运行时切场景会产生不确定性。

## 六、数据模型：一个资产与多个 Cell

一种常见的场景资产结构是：

```text
SceneVegetationAsset
├── PrototypeTable
├── Cell[0]
│   ├── Bounds
│   ├── Revision
│   └── Instances
├── Cell[1]
└── GlobalRevision
```

每个实例至少需要：

- 稳定 ID。
- 原型 ID。
- 所属 Cell。
- 位置、旋转和缩放。
- 状态标志。
- 可选的每实例光照或交互参数。

### 为什么 Cell 不应自动决定 Batch

Cell 表达的是“实例在哪里”，绘制桶表达的是“实例如何被绘制”。两者的变化原因不同：

- 玩家移动会改变激活 Cell，但不会改变 Mesh 或 Material。
- 原型 LOD 或材质变化会改变绘制桶，但不一定改变空间归属。
- Cell 重新划分会改变空间组织，但不应迫使每株植被重新注册渲染资源。

如果为每个 Cell 创建独立 BRG、Buffer 或材质批次，区域数量就会侵入渲染资源数量，增加：

- Batch 和 DrawCommand 管理成本。
- Buffer 碎片与重复上传。
- Cell 激活时的资源创建尖峰。
- 编辑器与运行时的生命周期组合数量。

因此 Cell 可以成为数据组织、增量编译、流式加载和内容所有权的边界，但不应仅因 Cell 数量增加，就自动增加 BRG、Buffer、Batch 或材质资源。

Cell 与 Batch 对齐并非永远错误。当分片拥有独立流式生命周期、独立 Buffer Page、不同资源集合或明确的故障隔离需求时，可以有意识地建立映射。关键是把这种映射作为经过成本分析的策略，而不是空间分区的隐式副作用。

### 一个资产并非无限扩张

一个场景一个资产适合以下条件：

- 全场作者数据的序列化体积可接受。
- 运行时能够加载该资产的索引和必要实例数据。
- 团队不会频繁同时修改同一个大文件。
- 构建、补丁和版本控制粒度满足需求。

需要拆分资产的理由不只有内存，还包括：

- 必须异步流式加载和卸载实例属性。
- Additive Scene 拥有独立生命周期。
- 多人并行编辑导致单文件冲突严重。
- 增量构建或补丁要求更小粒度。
- 某个分片损坏时需要故障隔离。
- 内容所有权和发布节奏不同。

拆分资产时仍应保留统一后端、稳定 ID、显式授权和提交边界，不需要退回到每个分片一套渲染算法。

## 七、GPU 数据、激活与可见集合

### 静态实例属性

在数据能够驻留的前提下，可以把实例属性写入一个共享 Buffer 或少量 Buffer Page：

- `ObjectToWorld` 与 `WorldToObject`。
- 原型和实例参数。
- 光照参数。
- 球谐光照（Spherical Harmonics，SH）等每实例数据。

Cell 激活变化通常不需要重传这些属性。它只改变哪些逻辑实例可以进入当前视图的可见集合。

### 保守包围体

Cell 和实例包围体必须保守覆盖所有可能的可见位置，否则粗剔除会把仍然可见的几何体错误移除。包围体至少需要考虑：

- 所有 LOD Mesh 的范围。
- 实例缩放。
- 风摆和顶点动画的最大位移。
- 运行时允许的形变。
- 编辑预览中的临时变换。

Cell 包围体通常由其内部实例的保守包围体合并得到。实例预览移动到原 Cell 之外时，可以临时扩张原 Cell 包围体、把预览实例加入独立预览集合，或让旧 Cell 和目标 Cell 同时参与剔除；不能在正式提交重新分配 Cell 之前仍只使用原始 Cell 边界。

### 世界级候选集合与低频 Cell 激活

Cell 激活回答的是“哪些空间区域值得进入当前精细剔除工作集”。本文把默认非流式模型中的结果称为 `ActiveCellSet`。它不表示资源一定刚刚加载，也不是某个相机的最终可见集合；全场实例属性可以一直驻留 GPU，而 `ActiveCellSet` 只控制哪些 Cell 继续参与精细计算。

`ActiveCellSet` 可以由以下信息决定：

- 所有需要保证正确显示的相机或编辑器视图。
- 玩家、交互角色或其它世界参考物体。
- 加载半径和卸载半径。
- 激活滞回。
- 更新时间间隔。
- 参考物体移动阈值。

加载半径小于卸载半径可以避免参考物体在边界附近移动时频繁开关 Cell。

如果系统支持 SceneView、GameView、辅助相机和反射/阴影视图，就不能只用主相机生成一个排他的激活集合。可选策略包括：

1. **保守并集**：把所有受支持视图和参考物体的需求合并为世界级 `ActiveCellSet`。
2. **每视图驻留集合**：为每个视图维护独立集合，再由资源层统计引用计数。
3. **编辑模式全驻留**：编辑器中保持全部 Cell 可用，播放模式再采用空间激活。

保守并集通常最容易保证正确性；每视图集合节省更多工作集，但资源引用、回收和调试复杂度更高。

流式系统还必须把资源状态拆开：

```text
DesiredCellSet：参考物体希望使用
LoadedCellSet：实例属性和依赖资源已经就绪
ActiveCellSet：Desired ∩ Loaded，并通过当前运行政策
```

这样才能表达“已经请求但尚未加载完成”和“资源仍在内存中但暂时不参与精细剔除”。不要让单一 Cell 集合同时承担请求、加载完成和运行激活三种语义。

全量数据始终驻留、仅维护一个 `ActiveCellMask` 的实现不属于上述三态流式系统。它可以是有效的基础政策，但不能把“场景 Batch 已创建”或“Cell 暂时不参与剔除”分别重命名为 `Loaded` 和 `Desired`，否则会掩盖真实的 IO、上传和发布边界。

`Loaded` 不能只表示磁盘 IO 已结束。一个 Cell 进入 `LoadedCellSet` 前，至少要满足：

- CPU 侧实例和原型数据可读取。
- Mesh、Material 等依赖资源已经就绪。
- 对应 GPU 数据已经上传完成。
- 所需 BRG Batch 和资源注册已经发布。
- 后续 culling callback 能在同一个可见性屏障之后取得这些数据。

异步加载完成到 `Loaded` 状态发布之间应存在明确的提交屏障，防止剔除线程看到“状态已加载，但 Buffer 或 Batch 尚未可用”的半成品。

### Cell 卸载与 Retiring 屏障

分片卸载不能把 `Loaded` 直接改成 false 后立即释放。安全顺序应为：

```text
停止接受新的 Desired/Active 引用
  → 从 ActiveCellSet 移除，禁止产生新的精细剔除读取者
  → 标记 Retiring，但暂时保留在 LoadedCellSet
  → 排空该 Cell 已发布的 CPU Job 和 callback
  → 等待或隔离仍可能读取旧 Batch/Buffer 的 GPU 工作
  → 注销 BRG Batch，释放 Buffer、Native 容器和原型注册引用
  → 释放 Mesh/Material/资产句柄的本 Cell 引用
  → 最后从 LoadedCellSet 移除并忘记该世代
```

这里的关键是先门控新读取者，再排空旧读取者，最后释放资源。整会话 Closing 处理整个渲染域；Cell Retiring 只处理一个流式分片，两者需要同样的“门控—排空—退役”原则，但不能互相替代。

2026-08-25 参考快照没有 Heap 级 GPU 资源卸载；它同步卸载整个运行时 Cell。管理器调用 `SceneBatch.Dispose` 时并非先销毁资源：该入口进入所属 `VegetationBrgWorld` 的互斥销毁路径，先完成覆盖此前剔除链的最终 JobHandle，再把会话从可回调状态移除，释放剔除 NativeArray 与 Prototype 引用，最后 RemoveBatch 并 Dispose GraphicsBuffer。随后 `VegetationBrgWorld.Dispose` 再防御性完成 JobHandle，并释放 PrototypeRegistry 与 BatchRendererGroup；管理器最后清空 HeapMask 和运行引用。物理组件另行按实际注册顺序反注册本运行时 Cell 的 Heap、归还代理并 Dispose QueryWorld。该路径有可确认的 CPU Job 屏障，但没有显式 GPU Fence 或异步 Retiring 世代证据；外层 Additive Scene 或资源句柄仍负责让 SceneAsset、Mesh 和 Material 真正离开内存。

### 每视图 BRG 剔除

BRG 剔除回答的是“这个相机或阴影视图最终绘制哪些实例”。典型流水线为：

```text
ActiveCellMask
  → Cell 包围体粗剔除
  → 实例包围体精细剔除
  → LOD 选择与滞回
  → 解析 RenderBucketKey
  → 根据 PageID / LocalSlot + RenderBucketKey 查询 BatchRegistrationPolicy
  → 枚举兼容的 BatchID / BatchLocalIndex
  → 按 (BatchID, RenderBucketKey) 最终命令组计数
  → Prefix Sum 计算命令组区间
  → Scatter 写入 visibleInstances
  → 生成 DrawCommand
```

其中：

- `RenderBucketKey` 描述 Mesh、Material、SubMesh、LOD、Pass、阴影和过滤状态等绘制分类。
- 同一个 `RenderBucketKey` 的实例可能分布在多个 Buffer Page，因此最终命令组必须使用 `(BatchID, RenderBucketKey)`。
- `Prefix Sum` 根据每个最终命令组的数量计算其在可见索引数组中的起始偏移。
- `Scatter` 把 `BatchLocalIndex` 写入对应命令组的可见区间。
- `visibleInstances` 保存对应 DrawCommand 所属 Batch 能解释的局部索引，不需要复制完整实例属性。

一个逻辑绘制桶可能因为跨 Page、不同 Batch 或其它命令限制被拆成多个 DrawCommand；Bucket 不应被建模成单值 `BatchID`。

### 每视图 LOD 状态

视锥剔除和 LOD 都属于视图相关状态。不同相机的投影参数、位置和视口不同，不能默认共享同一份实例 LOD 滞回历史。

常见策略包括：

- 按会话内稳定的视图键维护 `View → Instance → PreviousLod`。在 Unity 2022.3 BRG 模型中，可以使用 culling context 提供的 `viewID` 作为主要身份，并组合会话世代和 `ViewType`；若项目需要把双眼子视图、反射面或阴影 split 进一步隔离，应把对应 Subview 身份加入键中。
- 使用无状态 LOD 计算，并通过更保守的阈值减轻抖动。
- 明确选择一个主观察视图决定渲染 LOD，其它视图只复用结果；这种策略必须接受视觉误差。

阴影视图还需要独立政策：可以使用自身的 split 和距离选择阴影 LOD，也可以明确复用主观察视图的 LOD。阴影视图不应无条件写入普通相机的 LOD 历史。

视图销毁、SceneView 关闭或相机失效时，必须清理对应历史，避免状态泄漏和长期内存增长。对于无法收到明确销毁通知的临时视图，可以记录 `LastSeenGeneration` 或最后访问帧，并在超过设定窗口后淘汰；会话世代变化时应整体废弃旧视图历史。

能够为多个相机分别执行 culling callback，只证明视锥和投影输入按回调变化，不证明 LOD 滞回历史已经按视图隔离。如果多个普通相机写入同一份 `PreviousLod` 数组，仍然属于共享历史政策，必须明确接受其跨相机误差，或限制为唯一主观察视图。

### 与 ComputeShader Append Buffer 的区别

两种方案都维护动态可见集合：

- ComputeShader 方案常把通过剔除的数据或索引追加到 Append Buffer，再生成间接绘制参数。
- BRG 方案由 culling callback 生成 `visibleInstances` 和 DrawCommand，完整实例属性可以继续驻留原 Buffer。

差异主要在动态结果的表示和提交接口。二者都不会自动消除剔除计算，也不能仅凭“GPU 实例化”判断性能一定足够。

## 八、运行快照与线程一致性

BRG culling callback 可能调度 Job 读取 Cell、实例、LOD 和绘制桶数组。编辑器主线程或运行时逻辑不能在 Job 读取期间直接修改这些数组。

可靠实现应采用以下方式之一：

1. **不可变快照**：正式提交后创建新快照，旧 Job 完成后释放旧快照。
2. **版本化双缓冲**：写入备用数组，在安全点交换读写版本。
3. **显式同步点**：修改前完成依赖当前数据的 Job，再原地更新。

对于低频作者数据变更，不可变快照通常最容易保证正确性；对于高频运行状态，可以把激活掩码等小型数组单独同步，避免重建完整实例快照。

需要为以下数据定义一致性边界：

- 世界级 `ActiveCellSet`，以及流式变体中的 Desired/Loaded 状态。
- Cell 和实例包围体。
- 按 View 隔离的 LOD 历史和临时剔除结果。
- 稳定 ID、逻辑实例索引与 PageID/LocalSlot 的存储映射，以及实例到 Bucket/Batch/DrawCommand 的绘制映射。
- 原型注册和绘制桶。
- 预览覆盖状态。

完整释放渲染会话或卸载其全部 Buffer 前，必须使用明确的关闭协议：

```text
Running
  → Closing：阻止新的 callback 获取旧快照租约
  → Freeze：等待正在进入调度区的 callback 退出，并冻结 Handle 集合
  → Drain：CombineDependencies 并等待全部旧快照 JobHandle
  → Disposed：释放 Native 容器、Batch、GraphicsBuffer 和 BRG
```

culling callback 在取得快照和登记 JobHandle 时必须经过同一把锁、原子状态或引用计数协议。进入 `Closing` 后，新 callback 应返回合法空结果，不能继续登记任何旧快照读取者。如果每次新任务都在同一登记协议下依赖上一条最终 Handle，那么最后一条 Handle 可以作为覆盖全部旧任务的传递聚合点；否则，“最后一次观察到的 Job”不能代表所有读取者，必须冻结并 `CombineDependencies` 全部已登记 Handle。无论采用哪一种聚合形式，都必须先阻止新读取者加入，再等待聚合依赖完成。

快照热切换使用不同路径：先原子发布新快照，让后续 callback 只取得新版本；旧快照进入 `Retiring`，冻结并排空它已经登记的全部 JobHandle，最后只释放旧快照资源。此时会话本身仍处于 Running，不应复用完整销毁用的 `Closing` 语义。

## 九、全量扫描与紧凑工作集

共享 Buffer 和 Cell 激活掩码并不意味着剔除 Job 只访问激活实例。

### 方案 A：全量实例扫描并提前退出

每个视图对全量实例数组调度并行 Job，实例首先检查所属 Cell 是否可见。

优点：

- 实现简单。
- 逻辑实例索引和数组布局稳定。
- 无需维护动态实例区间。
- 适合中等规模或剔除 Job 成本较低的场景。

缺点：

- 每视图访问复杂度仍接近 `O(全场实例数)`。
- 不可见 Cell 只减少后续计算，没有消除实例读取和 Job 调度。

### 方案 B：按可见 Cell 构造紧凑范围

先收集激活且通过粗剔除的 Cell，再仅对这些 Cell 的实例区间调度精细剔除。

优点：

- 能减少实际访问的实例数量。
- 更适合实例极多但局部可见的世界。

缺点：

- 需要实例在 Cell 内形成连续区间，或额外维护紧凑索引。
- Cell 激活变化会增加工作集构造成本。
- Job 依赖、索引稳定性和调试复杂度更高。

选择依据应是目标设备分析结果。不要为了追求理论上的更低复杂度，提前引入比当前瓶颈更昂贵的数据维护。

无论采用哪种方案，都可以保持原始实例属性 Buffer 不变，只改变 CPU/Burst 剔除所访问的索引集合。

## 十、编辑事务与预览覆盖

### 为什么预览不能直接写资产

SceneView Handle、笔刷移动和参数拖动可能在一秒内产生大量更新。如果每次更新都执行：

- ScriptableObject 序列化。
- Undo 登记。
- Cell 重编译。
- Buffer 重建。
- AssetDatabase 刷新。

编辑器会出现明显卡顿，Undo 栈也会被无意义地拆碎。

### 预览通道

编辑工具不直接调用 BRG，而是把临时状态写入独立预览通道：

```text
编辑工具
  → PreviewState（资产、稳定 ID、临时值）
  → 编辑器宿主
  → 当前渲染会话
  → 覆盖对应逻辑实例的渲染数据
```

对不改变原型和绘制桶归属的变换预览，可以在独立预览覆盖层中保存：

- 临时实例矩阵。
- 临时保守包围体。

编辑器宿主可以在安全同步点把覆盖写入备用快照并交换版本，也可以让剔除阶段优先读取独立预览覆盖层。不能原地修改正在被 BRG culling Job 读取的不可变快照。

CPU 侧预览只修正剔除和包围体，不能自动移动 Shader 读取的几何数据。GPU 侧必须选择一种明确路径：

1. **局部 Buffer Patch**：通过 `PageID + LocalSlot` 更新预览实例的矩阵与相关属性，取消时恢复正式值。
2. **双 Buffer / 双 Page**：把覆盖写入备用 Buffer，在上传完成和旧 Job 排空后交换 Batch 使用的版本。
3. **独立预览 Batch**：正式实例在当前视图的可见集合中暂时隐藏，由小型预览 Buffer 和独立 Batch 绘制临时状态。

局部原地 Patch 只有在后端能够证明旧 DrawCommand 和在途 GPU 工作不会继续读取被改写区域时才安全。如果无法建立这种屏障，应禁用原地 Patch，改用双 Buffer 或独立预览 Batch。

一次可见的预览发布应是原子组合：

```text
PreviewPublication
  = PreviewGeneration
  + CpuPreviewSnapshotVersion
  + GpuBufferVersion
  + UploadReadyState
  + CommandBuildVersion
```

推荐顺序为：

1. 构建新 CPU 预览快照。
2. 把矩阵和属性上传到尚未公开的 GPU Buffer 版本。
3. 等待上传达到可被后续绘制读取的就绪点。
4. 原子发布新的 `PreviewPublication`。
5. 后续 culling 和命令构建只取得已经完整发布的组合。
6. 旧组合等待全部 CPU Job 和相关 GPU 使用退役后，才允许复用 Buffer 区域或恢复正式值。

取消预览和连续拖动产生下一世代时也必须遵守相同流程，不能直接覆盖仍被上一世代使用的 Buffer。

`visibleInstances` 的元素本身仍然只是批次内索引，不需要额外携带世代字段；它所属的命令构建结果和快照租约必须关联同一个 `PreviewGeneration`。渲染会话不能把新包围体与旧 GPU 矩阵混合，否则会出现“剔除位置正确但几何体仍在旧位置”的错误。

完成 CPU culling Job 后对公开 Buffer 原地调用上传 API，只能证明 CPU 读写没有重叠，不能自动证明先前提交的 GPU 工作已经停止读取该区域。没有 Fence、版本化 Buffer、独立预览 Batch 或其它等价退役证据时，应把这种实现标为同步简化路径，而不能声称已经满足 `PreviewPublication` 的世代一致性协议。

这种快速路径不适用于：

- 替换原型。
- 改变 Mesh、Material 或 SubMesh。
- 新增或删除实例。
- 改变会导致 Buffer 布局变化的实例数据。

这些结构性变化需要专门的结构预览，或在正式提交后重建受影响范围。

### 逻辑提交协议

正式提交首先是一次内存中的一致性事务，不等同于“立即保存到磁盘”。推荐协议为：

1. 创建一个 Unity Undo Group，并在修改前登记所有受影响的 ScriptableObject。结构性列表变化通常需要完整对象 Undo，而不仅是记录单个字段。
2. 在临时事务对象或副本中生成候选作者数据，以及维持作者状态合法所必需的结构索引。
3. 校验稳定 ID 唯一性、原型引用、Cell 归属、有限数值、缩放范围和作者数据 Schema 约束。
4. 作者校验或必需结构索引生成失败时丢弃候选结果；如果已经修改正式对象，则回退整个 Undo Group，并且不发布变更事件。
5. 校验成功后，把候选结果一次性发布为新的权威作者状态，并更新修订信息。
6. 将可延后重建的编译缓存标记为 Stale，并按同步、延迟或后台政策重新生成。此类缓存失败不应回滚已经合法提交的作者数据。
7. 标记受影响资产为 Dirty，合并本次 Undo Group。
8. 在内存状态已经自洽后发布正式变更事件。
9. 清除对应预览状态。

变更事件表示“新的内存作者状态已经可读取”，不应在候选数据尚未完整发布时提前触发。

这里需要区分两类派生数据：

- **提交必需结构**：稳定 ID 索引、Cell 归属表、保证作者状态可解释的边界信息。生成失败意味着逻辑事务失败。
- **可再生编译缓存**：Page/LocalSlot 排列、GPU Buffer 布局、照明展开和构建优化数据等。它们可以暂时处于 Stale 或 Error 状态，并在提交后重建。

目标平台容量不足、Buffer Page 排布失败或某个可选编译器暂不可用，不应默认回滚合法作者数据。构建门禁可以阻止发布尚未成功编译的资产，但这是编译/发布政策，不是作者事务的原子性条件。

变更事件至少应描述：

- 哪一份资产发生变化。
- 哪些 Cell 受影响。
- 原型表是否变化。
- 渲染数据 Schema、原型依赖或编译缓存是否需要失效。
- 是否允许局部更新。

当前选择完整重建还是局部更新，应由渲染宿主决定，编辑工具不需要知道后端实现细节。

### 持久化政策

把 Dirty 资产写入磁盘是独立政策，可以选择：

- 每次逻辑提交后立即保存。
- 延迟到一组操作结束后保存。
- 由用户显式执行保存。
- 在场景切换、构建或关闭编辑器前统一保存。

保存失败时，内存作者状态和 Dirty 标记仍然存在，系统应允许重试；只有确实需要“持久化成功”语义的模块，才应监听单独的保存完成事件。不要把 `AssetDatabase.SaveAssets` 强制写进所有编辑事务的不变量。

### Undo、取消与重载

- 取消预览只清除预览覆盖，不修改作者数据，也不产生 Undo。
- Undo/Redo 后必须清除与旧作者状态不再匹配的预览，并发布新的失效世代，让宿主重建或交换快照。
- Domain Reload 前应完成相关 culling Job、释放渲染会话和非托管资源。
- 预览状态默认不持久化；重载后从正式作者数据恢复。
- 如果需要跨重载恢复未提交操作，应使用独立草稿机制，不能把预览覆盖伪装成正式资产。

## 十一、修订号、Hash 与缓存失效

高频编辑器路径不应通过遍历所有实例计算完整 Hash 来判断是否变化，但一个可被 Undo 的序列化 Revision 也不能单独作为永久唯一的缓存键。

例如：

```text
Revision 6 / 内容 B
  → Undo 到 Revision 5
  → 新编辑得到 Revision 6 / 内容 C
```

如果持久缓存只使用 Revision，就可能把内容 B 的缓存错误用于内容 C。可靠实现应区分三类标识：

### 作者修订号

- 序列化在场景资产和 Cell 中。
- 表示作者状态的相对版本。
- 可以随 Undo/Redo 回退。
- 适合 Inspector 展示、局部变化比较和序列化追踪。

### 会话变更世代

- 当前编辑器或运行进程内单调递增。
- 任意提交、Undo、Redo、外部资源失效或快照交换都会递增。
- 不参与持久化，不随 Undo 回退。
- 适合 O(1) 判断当前运行快照是否失效。

### 持久缓存键

持久编译缓存应使用以下信息生成内容键：

```text
AssetPersistentId
  + 规范化作者数据 ContentHash
  + 外部依赖指纹
  + 编译器 / 数据布局 SchemaVersion
```

ContentHash 可以用于检查缓存一致性、依赖变化和构建产物去重，但应在正式提交、导入或显式编译边界计算，不能进入 Repaint 高频路径。

运行快照应记录自己对应的会话世代和持久缓存键。Revision 用于描述作者编辑历史，SessionGeneration 用于即时失效，ContentHash 用于跨会话验证；三者不能互相替代。

## 十二、事件驱动的编辑器刷新

编辑器渲染宿主应在状态真正失效时刷新，例如：

- 场景打开或活动上下文变化。
- 授权组件启用、禁用或关键字段变化。
- 正式编辑事务提交。
- Undo 或 Redo。
- 原型资源显式刷新。
- 进入或退出播放模式。
- 进入或退出 Prefab Stage。

多个连续事件应合并到一次延迟刷新，避免同一帧重复释放和创建资源。

以下操作不能进入 Inspector、SceneView 或 Overlay 的 Repaint 高频路径：

- 全项目 AssetDatabase 扫描。
- 原型反向引用搜索。
- 全量实例序列化。
- 完整 Buffer 重建。
- 持续调用 `SceneView.RepaintAll()`。

资源搜索结果可以缓存，并只在项目资源变化或用户显式刷新时失效。

### 视图隔离

编辑器中可能同时存在主 SceneView、GameView、Prefab Stage 和 Preview Scene。渲染会话必须明确自己允许参与哪些视图。

常见方法包括：

- 使用 Unity 编辑器用于隔离场景内容的 Scene Culling Mask 限定主场景会话。
- 在进入 Prefab Stage 时释放主场景编辑会话。
- 为专用 Preview Scene 创建独立、只读取预览资产的会话。

如果 SceneView 周期性闪烁，应优先检查：

- 是否有多个会话重复提交。
- Buffer 或 BRG 是否在 Repaint 链路中反复创建和释放。
- 当前会话是否进入了错误视图。
- 正式提交和预览覆盖是否互相重建。

同时仍需排查 Shader、透明排序、深度、阴影和渲染管线配置，不能把所有闪烁都归因于生命周期。

## 十三、架构变体的选择

| 条件 | 推荐结构 |
|------|----------|
| 单场景、中等规模、数据可驻留 | 一个场景资产、多个 Cell、一个场景会话 |
| Additive Scene 独立加载卸载 | 每 Scene 独立资产与会话，或世界聚合器统一注册 |
| GPU 数据超过单 Buffer 或 API 限制 | 使用 Buffer Page，保持统一的逻辑索引到 PageID/LocalSlot 存储映射；绘制分类另行映射到 Bucket/Batch |
| 世界极大且局部可见 | Cell 分片资产 + 紧凑可见工作集 |
| 多人同时编辑 | 按 Scene、区域或内容所有权拆分作者资产 |
| 原型高频变化 | 原型注册与实例数据分离，按依赖修订号局部失效 |
| 运行时新增删除频繁 | 引入空闲 LocalSlot、间接映射或动态 Page，不依赖静态连续数组 |

架构演进时应优先保持以下接口稳定：

- 稳定 ID 到当前逻辑实例索引和物理 Buffer 地址的解析。
- 场景授权协议。
- 正式变更事件。
- 预览通道。
- BRG 后端的数据布局契约。

在权威作者语义、身份协议和资源生命周期契约保持稳定的前提下，多数资产分片和剔除变化可以被约束在既定接口之后。流式化仍可能扩展快照编译器、Batch 注册、同步、资源回收、构建管线和编辑协作；跨资产事务、引用迁移和授权聚合也可能扩展编辑工具，但不应迫使笔刷与选择逻辑直接依赖新的 Buffer 或 Batch 布局。

## 十四、可检验主张与验证方法

下表定义的是架构主张的验收方法，不是参考实现的功能完成清单。判断某项是否已经落地，应同时查看前文“本文与参考实现的关系”中的覆盖级别；仅列出验证方法不等于相关测试已经执行。

| 可检验主张 | 验证方法 | 失败信号 |
|----------|----------|----------|
| 编辑器与运行时共享后端实现 | 检查创建类型、Buffer 布局和剔除代码路径 | 两套渲染算法或不同材质注册逻辑 |
| 同一实例所有权域没有重叠提交者 | 检查不同会话负责的实例集合，并记录模式切换时的会话数量 | 同一实例被重复提交、闪烁或资源重复 |
| 工具窗口不拥有渲染生命周期 | 关闭植被笔刷工具、Inspector 和 Overlay | 植被随窗口关闭而消失 |
| 无授权时不渲染 | 打开没有授权组件的场景 | 旧场景植被继续显示 |
| Prefab 与主场景隔离 | 进入 Prefab Stage 和 Preview Scene | 主场景植被泄漏到预览视图 |
| 预览不修改正式数据 | 连续拖动后取消并检查资产与 Undo | 资产变脏、Undo 产生大量碎片 |
| 逻辑事务失败时不发布半成品 | 注入作者校验或提交必需结构索引生成失败 | 资产只修改一半、错误事件已发布或无法 Undo |
| 可再生缓存失败不破坏作者提交 | 注入 GPU 排列或其它可延后缓存生成失败 | 合法作者数据被回滚，或缓存 Stale 状态没有记录 |
| 磁盘保存失败保留内存提交 | 在逻辑提交完成后注入保存失败 | Dirty 状态丢失、作者修改被错误回滚，或错误发布“保存完成” |
| Undo 分支不会命中旧缓存 | Undo 后从旧 Revision 创建不同内容 | SessionGeneration 未变化或 ContentHash 错误复用 |
| 稳定身份作用域完整 | 复制、跨 Cell 移动、跨资产迁移和多 Scene 合并 | 身份冲突、选择错位或引用失效 |
| 世界命名空间复制政策明确 | 普通复制整资产，以及显式执行同世界分片 | 克隆保留相同 WorldNamespace 与重叠实例 ID，或分片身份被无故重映射 |
| 身份冲突修复是显式事务 | 制造复合 ID 冲突并尝试聚合、编译和修复 | 静默覆盖、外部引用未迁移或无法 Undo |
| ActiveCellSet 覆盖所有受支持视图 | 让辅助相机或 SceneView 观察主相机范围外的 Cell | 视锥内实例因世界级候选集合缺失而消失 |
| Loaded 状态具有完整就绪屏障 | 在 IO、GPU 上传和 Batch 注册之间分别注入延迟 | Cell 标记 Loaded 后 culling 仍访问缺失资源 |
| LOD 历史按视图隔离或有明确共享政策 | 让两个相机从不同距离同时观察同一实例 | 相机之间互相改变 LOD 或持续抖动 |
| 临时视图历史可以淘汰 | 连续创建和销毁 SceneView、反射或阴影视图 | View 历史持续增长或旧状态污染新视图 |
| Cell 不会无理由增加 Batch | 增加 Cell 数并比较 Batch/DrawCommand，记录任何有意映射 | Batch 数随 Cell 数增长但没有流式或资源隔离依据 |
| 跨 Page 绘制按最终命令组分桶 | 让同一 RenderBucketKey 的实例分布在多个 Page，并为同一 Page 注册多个候选 Batch | 错误笛卡尔积、重复绘制、一个 DrawCommand 引用不兼容 Batch，或 visibleInstances 使用全局地址 |
| 激活不重传静态实例属性 | 移动参考物体并记录 Buffer 上传 | 每次 Cell 开关都上传整场数据 |
| 预览 CPU/GPU 数据属于同一世代 | 在旧 GPU 工作仍在途时连续产生新预览并取消，比较几何位置、包围体和命令版本 | 剔除位置与几何位置跨世代混合，或取消时覆盖仍被使用的 Buffer |
| 剔除快照线程安全 | 在提交、Undo 和相机剔除并发时压力测试 | Native 容器错误、错帧或崩溃 |
| 会话关闭先门控再排空 | 在 callback 持续进入时切换模式或卸载 | Closing 后仍产生旧快照读取者，或已释放内存仍被 Job 访问 |
| 复杂度符合规模 | 分别分析全量扫描与紧凑工作集 | Job 时间随全场实例数不可接受增长 |
| 目标设备预算满足要求 | 测量 CPU、GPU、内存和尖峰 | 编辑器测试通过但设备帧率不达标 |

测试应把“架构正确性”和“容量性能”分开。生命周期、数据一致性通过，并不代表任意实例规模都满足目标设备预算。

## 十五、反模式速查

| 反模式 | 直接后果 | 替代原则 |
|--------|----------|----------|
| 编辑器和运行时维护两套渲染实现 | 材质、LOD、阴影和剔除行为逐渐分叉 | 共享后端实现，只分离生命周期宿主 |
| 工具窗口持有渲染会话 | 窗口关闭或重载时显示意外消失 | 工具只管理交互，宿主管理会话 |
| Cell 数量无条件决定 Batch 数量 | 空间分区数量侵入渲染资源数量 | 概念职责独立；只有在流式或资源隔离需要时显式建立物理映射 |
| Repaint 时扫描资源并完整同步 | SceneView、Prefab 和 Inspector 持续卡顿 | 事件驱动失效与显式刷新 |
| 用物理 Buffer 地址代替稳定 ID | 重编译或分页后选择、Undo 和存档错位 | 维护稳定 ID 到当前运行时地址的映射 |
| 把共享 Buffer 当作没有全量遍历 | 误判剔除复杂度和真实瓶颈 | 分别测量上传、访问实例数和 Job 成本 |
| 派生缓存成为第二权威 | 编辑结果、预览和运行时状态互相不一致 | 缓存必须可由作者数据和修订号重建 |

## 十六、结论

Unity 大规模植被系统的稳定性首先来自职责、所有权和数据边界，而不是某一个剔除算法。

最重要的四项原则是：

1. 权威作者数据、派生缓存、运行快照和预览覆盖必须分层。
2. 编辑器与运行时共享 BRG 后端实现，同一实例所有权域不能被重复提交。
3. Cell、物理 Buffer、BRG Batch 和绘制桶的概念职责必须独立建模；物理映射只能是经过成本分析的显式策略。
4. 静态实例数据、低频空间激活和逐视图可见集合必须分别维护。

在权威作者语义、身份协议和资源生命周期契约不变时，Buffer 分页、Cell 工作集和剔除策略可以沿既定接口演进，但仍可能修改快照编译、Batch 注册、同步和资源回收模块。Additive Scene、资产分片、跨资产事务和引用迁移还可能要求扩展构建管线、加载状态机与编辑工具。

---

### 参考链接

- [Unity Manual - BatchRendererGroup](https://docs.unity3d.com/2022.3/Documentation/Manual/batch-renderer-group.html) - BRG 的定位、适用范围与相关主题入口。
- [Unity Manual - How BatchRendererGroup works](https://docs.unity3d.com/2022.3/Documentation/Manual/batch-renderer-group-how.html) - BRG 渲染流程和核心概念。
- [Unity Scripting API - BatchRendererGroup](https://docs.unity3d.com/2022.3/Documentation/ScriptReference/Rendering.BatchRendererGroup.html) - BRG 类型与 API 参考。
- [Unity Scripting API - OnPerformCulling](https://docs.unity3d.com/2022.3/Documentation/ScriptReference/Rendering.BatchRendererGroup.OnPerformCulling.html) - 剔除回调接口。
- [Unity Scripting API - BatchCullingContext.viewID](https://docs.unity3d.com/2022.3/Documentation/ScriptReference/Rendering.BatchCullingContext-viewID.html) - BRG culling view 身份字段。
- [Unity Manual - DOTS Instancing shaders](https://docs.unity3d.com/2022.3/Documentation/Manual/dots-instancing-shaders.html) - Shader 读取每实例数据的官方说明。

### 相关记录

- [植被 Painter 作者工作流与事务设计](./unity-vegetation-painter-authoring-transaction-workflow.md) - 把 UI 操作、暂存、预览、编译和 Undo 串成可观察的作者闭环。
- [BRG 逐株 Buffer 的 32 字节压缩与量化 ABI](./unity-brg-packed-instance-buffer-quantization.md) - 32 B 位布局、CPU/GPU 同量化剔除、多 Heap 寻址、失败事务与验证分层。
- [多运行时 Cell 物理查询与 Collider 流送](./unity-vegetation-multi-cell-physics-streaming.md) - 以运行时 Cell 为所有权层级，解释兴趣源广播、两级懒建 QueryWorld BVH、代理状态机和卸载边界；包含历史与当前 Editor 物理数据，不是 Quest 验收。
- [Bakery L2 静态光照与投影代理](./unity-vegetation-bakery-static-lighting-pipeline.md) - 解释代理、Probe、稀疏光照记录和运行时解码。
- [Quest 3S BRG 与普通 GO 性能基线](./quest-vegetation-brg-performance-lighting-validation.md) - 当前实现之外的历史设备 A/B/A 证据与严格适用边界。
- [大规模渲染相关经验](./gpu-grass-large-scale-rendering.md) - ComputeShader 草渲染、Append Buffer 与 GPU 视锥剔除的相邻方案。
- [GPU 视锥剔除](./gpu-frustum-culling-compute-shader.md) - ComputeShader 可见集合生成的基础实现。
- [Unity 性能优化：ECS 与剔除](./unity-performance-ecs-culling.md) - 大规模实体组织和剔除的相邻经验。

### 验证记录

- [2026-08-06] 从 Unity 2022.3 LTS 的工程实践中归纳统一后端、场景授权、空间 Cell、共享实例数据和编辑提交边界。
- [2026-08-06] 定义多视图 ActiveCellSet、每视图 LOD、逻辑事务、Undo 分支缓存键和稳定身份作用域的设计要求；将状态调整为“有效”，避免把验证方法表述成已完成实验结果。
- [2026-08-06] 定义存储寻址与绘制分类、Desired/Loaded/Active Cell 状态、提交必需结构与可再生缓存，以及高熵 ID 和 culling JobHandle 生命周期的演进契约。
- [2026-08-06] 定义 `(BatchID, RenderBucketKey)` 最终命令分组、Closing 门控、GPU 预览路径、Loaded 就绪屏障和身份冲突修复协议；这些高级协议仍需对应实现与压力测试。
- [2026-08-06] 定义世界命名空间下的复制/分片政策、多 Batch 兼容选择，以及 PreviewPublication 的 CPU/GPU 发布与退役屏障；不把这些设计要求记为当前参考实现已完成的功能。
- [2026-08-06] 逐项对照参考实现与现有测试，新增实现覆盖边界：统一后端、单 Buffer/单 Batch、Cell 激活、全量扫描、编辑预览与单次 Undo 已有证据；多视图 LOD 隔离、流式状态、分页、关闭/预览退役协议和跨资产身份迁移明确标为尚未完整落地的演进契约。
- [2026-08-25] 复核当前源码与自动化证据，明确“运行时 Cell → 多 Heap”的术语映射、每运行时 Cell 独立 BRG/Buffer/物理所有权、Heap 掩码不释放 Buffer、全实例两遍 Job、多运行时 Cell 已落地及其全局预算边界。
- [2026-08-26] 叠加 QueryWorld 的 Heap/Shape 两级懒建 BVH 状态，更新最终回归为 EditMode `244/244`、PlayMode `11/11`；冷建树和 Quest 物理性能仍未验证。
- [2026-08-26] 审查 BRG 固定逐株区由 128 B 收敛到 32 B 的候选实现，更新 Buffer 公式、上传/预览和 CPU/GPU 同量化口径；实际回读支持逻辑分配下降，但没有把它写成 Quest 帧耗或物理显存收益。

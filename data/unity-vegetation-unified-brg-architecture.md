# Unity 大规模植被的统一 BatchRendererGroup（BRG）架构

**标签**：#unity #architecture #rendering #editor #performance #culling #scriptable-object
**来源**：工程实践抽象 - Unity 大规模植被的数据权威、渲染会话与空间工作集设计
**收录日期**：2026-08-06
**更新日期**：2026-09-03
**状态**：📘 有效
**可信度**：⭐⭐⭐⭐（Unity 官方 API 文档与参考实现源码交叉核对；运行时故障注入和目标设备性能仍未验证）
**适用版本**：Unity 2022.3 LTS 的 BatchRendererGroup API 模型；其它版本需重新确认 API 与图形后端行为

---

### 概要

当同一场景中有大量草、灌木或重复装饰物时，逐株 GameObject、编辑器窗口和空间分区若各自维护一套渲染状态，很容易产生重复数据、重复绘制和不一致的生命周期。为了让后续论证不依赖项目内部叫法，本文先固定四个核心对象：

- **植被原型（Prototype）**：一类植被共享的 Mesh、Material、LOD（随观察尺寸切换的细节等级）、阴影部件和局部包围盒规则。
- **场景植被资产（SceneAsset）**：一个可序列化的 Unity 资产对象（`ScriptableObject`），保存 Prototype 引用表、实例变换、持久身份和空间分组数据；它不是 Unity Scene 文件。
- **运行时 Cell**：一份 SceneAsset 及其独立渲染、查询和资源生命周期构成的所有权域。一个 Unity Scene 可以包含多个 Cell，附加加载的多个 Scene 也可以各自带 Cell。
- **Heap**：运行时 Cell 内按空间网格归类的一组实例，是编辑、激活和粗剔除单位；它不是独立 Unity 资产，也不天然对应一次 GPU 绘制。

挂在场景 GameObject 上、为一个 Cell 绑定 SceneAsset 和运行策略的组件，本文称为 **Manager**。供美术人员刷取、选择和变换植被的编辑器工具称为 **Painter**。本文的**植被编译器**不是 C# 编译器，而是把可编辑作者数据检查、排序并转换成运行时数组、Bounds 和缓存的构建器。**RuntimeIndex** 是该构建器在一个 Heap 内为实例重新生成的连续下标，只连接本次编译的数组和缓存，不能充当持久身份。**ABI** 是“应用二进制接口”（Application Binary Interface）：在本文中专指 CPU 写入 GPU Buffer（GPU 可读取的连续数据存储）与 Shader 解码时必须共同遵守的字节布局、步长和位序契约。

BRG 是 Unity 允许应用自行提供批次数据和每视图可见结果的底层批量渲染接口；一个 **BRG Batch** 是共享同一 GPU 存储及其解释规则的注册单元，**绘制桶**则是一组 Mesh、Material、Pass 等绘制状态相同的可见实例。在这些定义下，更稳定的做法是：SceneAsset 保存唯一的作者数据，编辑器与运行时共享同一套 BRG 后端协议，Heap 只组织数据和空间工作集，而 GPU 存储、BRG Batch 与绘制桶分别建模。核心结论是：Heap、GPU 存储、BRG Batch 和绘制命令不是同一层分区；把它们解耦，才能同时保持稳定身份、较少的提交状态以及可独立演进的空间流送策略。Painter 事务、实例压缩 ABI、物理查询、静态光照和 Floating Origin（通过移动世界原点控制大坐标误差）的内部实现属于独立专题；本文只定义它们接入渲染架构时必须满足的接口。

### 论证范围、证据等级与 BRG 最小模型

本文不是某次项目验收报告。为了使实现观察与架构建议不会互相冒充，正文按以下四类证据陈述：

- **Unity API 事实**：由文末 Unity 2022.3 官方文档支持，例如 BRG 的 Batch 注册、剔除回调和 `visibleInstances` 约定。
- **参考实现观察**：来自对文中具名类型及其调用链的静态源码核对，只说明被检查实现如何组织数据，不等同于当前版本完整回归、异常注入或设备实测。
- **接口要求**：为了保持数据、生命周期或并发一致性而推导出的必要约束；除非另有实现证据，不表示参考实现已经满足。
- **未来可选方案**：分页、紧凑工作集、版本化快照等尚未落地或尚未验证的演进方向。

因此，本文可以支持架构理解和方案评审，但不能单独证明某个具体版本已经通过完整功能门禁，也不能给出目标设备的容量或帧耗结论。第十节提供可复现实验方法，读者可以据此核验自己的实现。

Unity Job System 是把 CPU 工作拆成可并行任务并交给工作线程执行的框架。一个 Job 调度后会返回 `JobHandle`；后续 Job 可以声明依赖某个句柄，只有依赖完成后才开始，这就是本文所说的“依赖调度”。在 CPU 线程上调用 `JobHandle.Complete()` 会等待该 Job 及其依赖结束，因此可以在修改或释放 Job 正在访问的内存前建立 CPU 同步点；它不能证明 GPU 已经停止读取某个 Buffer。

`BatchRendererGroup`（BRG）是本文的批量渲染提交后端。渲染宿主注册 Batch 及其 Metadata（Shader 属性到 Buffer 字节基址的小型寻址表）；每个相机或阴影视图触发一次剔除回调后，CPU Job 计算可见实例，把该 Batch 可解释的实例索引写入 `visibleInstances`（可见实例索引数组），再生成引用相应数组区间的 DrawCommand（绘制命令）。Shader 按 Batch Metadata 解释实例索引，并从 GPU Buffer 读取逐实例属性。

本文还使用以下约定：

- **Buffer**：保存逐实例 GPU 属性的存储；当前参考实现为每个运行时 Cell 一份共享 Buffer。
- **Batch**：共享一套 Metadata 和存储解释规则的 BRG 注册单元；注册返回的 `BatchID` 是 DrawCommand 选择该单元的句柄。Batch 不等同于 Heap。
- **Metadata**：BRG Batch 注册时提交的小型寻址表。每项用 Shader 属性的 `NameID` 指向 Buffer 中某类数据的字节基址，并用标志说明它是逐实例还是整批共享。Metadata 不保存 Mesh、Material 或一株实例的完整属性；它告诉 Shader 应从同一 Buffer 的哪个区域开始解释数据。
- **DrawCommand / DrawRange**：DrawCommand 指定 Batch、Mesh、Material、SubMesh 和 `visibleInstances` 区间；DrawRange 再为一组命令附加过滤状态。当前实现为每个非空桶生成一条命令和一个 Range。
- **RenderBucketKey**：一次绘制中必须相同的 Mesh、Material、SubMesh、Shader Pass、LOD 渲染部件（RenderPart，即一个 LOD 中独立提交的网格/材质部分）和固定 Filter 状态（例如阴影模式、渲染 Layer 等整条命令共享的过滤属性）组合。早期实现或资料中的 DrawBucket 指同一层概念，本文下文统一使用 `RenderBucketKey`。
- **Bounds**：包住一组实例或一个模型的保守空间边界；剔除只能在该边界确定完全位于视锥外时丢弃对象。
- **ActiveHeapMask / HeapVisibility**：前者是运行策略允许参与计算的 Heap 掩码，后者是当前视图对这些 Heap 做空间测试后的可见标记；改变前者不会自动缩短实例数组。
- **Buffer Page**：未来可能采用的物理存储分片，当前单 Buffer 实现没有 `PageID`。
- **GraphicsFence**：用于确认 GPU 工作已经越过某一资源使用点的同步信号；当前实现没有该退役闭环。
- **StableID**：一株实例跨排序、重编译和空间块迁移仍保持不变的持久身份。参考实现的具体字段名是 `StableGuid`；它不是数组下标。
- **Desired / Loaded / Active**：分别表示“策略希望使用”“资源已经完整就绪”和“本轮允许参与计算”。三个状态的完整关系在第七节展开。
- **JobHandle**：上文所述的 Job 依赖与 CPU 完成句柄；下文凡写 `Complete()`，都只表示等待 CPU Job 链结束。
- **Native 容器**：供 Unity Job 和 Burst 编译器访问的非托管内存容器，例如 `NativeArray<T>`。它们必须显式释放，并且在相关 Job 完成前不能被修改或释放。
- **LOD 滞回**：在相邻细节等级切换阈值周围保留一段回差区间，避免相机轻微移动时两个 LOD 来回跳变。滞回需要记住上一次选择，因此共享历史会造成多相机互相影响。
- **Prefix Sum（前缀和）**：把各绘制桶的实例数量转换成连续数组中的起始偏移。例如三个桶分别有 2、3、1 株，起点就是 0、2、5；各 Job 随后可以写入互不重叠的区间。
- `VegetationBrgWorld` 与 `VegetationSceneBatch` 是当前参考实现中的类型名，不是 Unity 通用概念。前者拥有一个运行时 Cell 的 BRG 会话，后者持有该 Cell 的 Batch、Buffer 和运行读数据。
- 复杂度符号：`H` 是当前 Cell 的 Heap 数，`N` 是完整实例数组长度，`B` 是已编译绘制桶总数，`P` 是本视图最终要写入的可见“实例—渲染部件”引用数，`D` 是其中非空绘制桶数，`K` 是一帧内触发的相机与阴影视图回调数。第七节会给出完整成本；`O(H + N)` 只是主扫描的简写。

## 被分析参考实现的基线

后续讨论以一份已经完成静态源码核对的实现为基线。这里列出的只是实现观察，不是完整运行时验收结果：

- 每个 Manager 只绑定并管理自己的 SceneAsset；同一 Unity Scene 或 Additive Scene（在保留当前 Scene 的同时附加加载、并可独立卸载的 Scene）集合可以存在多个相互隔离的运行时 Cell。
- 每个已加载 Cell 独立创建一个 `VegetationBrgWorld` 和一个 `VegetationSceneBatch`；该 SceneBatch 注册一个 BRG Batch，并持有一份包含该 Cell 全部实例、Heap 量化表和稀疏光照数据的共享 Buffer。
- Heap 是空间与激活单位，不直接产生 BRG Batch 或 DrawCommand。`RenderBucketKey` 由 Mesh、Material、SubMesh、Pass 和固定 Filter 状态决定；相同绘制状态可以跨多个 Heap 合并进同一命令。
- Cell 加载完成后，整份 Buffer 常驻。兴趣范围只更新 `ActiveHeapMask`。每个视图先以 Heap Bounds 生成 `HeapVisibility`，随后 Count（剔除、选 LOD 并统计桶）与 Scatter（把已选实例索引散射到各桶连续区间）两个实例 Job 都仍按完整实例数组调度。单视图的渐进成本是 `O(H + B + N + P)`，但这个简式隐藏了两次 `B` 桶遍历、两次 `N` 实例遍历和两次可见引用处理；关闭或视锥剔除多数 Heap 不等于 CPU 只遍历活动实例。
- 在空间流送与 Heap 激活路径中，只有整个 Cell 被宿主卸载或对应 Scene 卸载时，才 Dispose SceneBatch、BRG World 和整份 Buffer；编辑器强制刷新或资产重建也可以重建这些资源。当前没有 Heap 级 GPU Buffer 装卸、分页或紧凑活动工作集。
- 多 Camera 共用一份 LOD 历史。Shadow 视图不更新该历史，但普通 Camera 与 SceneView 没有按稳定视图身份隔离，因此不能宣称多视图 LOD 状态独立。
- 释放前会等待最后登记的 Culling Job 完成；当前没有 GraphicsFence、版本化 Buffer 或 GPU 资源世代，因而只能确认 CPU Job 排空，不能把它扩大为严格 GPU 退役协议。

下文提到的 Buffer Page、紧凑工作集、按视图 LOD 历史、快照租约和 GPU Fence 都是演进约束或候选方案，不是当前已实现能力。

### 可冻结的工程案例证据

为使“参考实现观察”能够与一个不再漂移的源码状态绑定，本文使用以下匿名证据锚点：

- Git 提交：`f0fef16849cfb8945e9928e5219a140ee250fcf4`
- 该提交中模块根 Git tree：`4700f76e0b087fe3935c06e660ee732bbf55c87a`

Git tree 是目录内容的递归摘要；提交与 tree 同时匹配，才能说明下表相对路径指向本文分析的那份模块内容。持有该私有快照的读者可以检出提交、核对模块 tree，再按下表复核主张。没有源码访问权的外部读者只能把它视为可定位的工程案例证据，不能独立复跑或把它当成公开源码证明。

| 核心主张 | 模块内相对源码入口 | 可核对的行为 |
|---|---|---|
| SceneAsset 是实例权威，Prototype 是跨场景复用规则，Heap 是资产内空间分组 | `Runtime/Core/VegetationSceneAsset.cs`；`Runtime/Core/VegetationRegionHeap.cs`；`Runtime/Core/VegetationPrototypeAsset.cs`；`Runtime/Core/VegetationRecords.cs` | SceneAsset 序列化 Prototype 槽位和 Heap；实例保存在 Heap 内并以 StableGuid 持久标识；Prototype 不保存场景实例或场景 SH 数据 |
| Manager 为自己的 SceneAsset 建立独立 Cell 生命周期 | `Runtime/Rendering/VegetationCellManager.cs` → `LoadCell`、`UnloadCell`、`UpdateCellStreaming` | Manager 绑定一份 SceneAsset，并以自身 Transform 与运行策略创建、刷新或释放对应渲染会话 |
| 每个运行时 Cell 使用一份 Buffer 和一个 BRG Batch | `Runtime/Rendering/VegetationBrgWorld.cs` → `CreateSceneBatch`；`Runtime/Rendering/VegetationSceneBatch.cs` → 构造函数、`CreateBufferAndBatch` | World 拒绝创建第二个 SceneBatch；SceneBatch 创建一个 GraphicsBuffer，并调用一次 `AddBatch` |
| Heap Bounds 粗筛后仍全量调度实例 | `Runtime/Rendering/VegetationBrgWorld.cs` → `OnPerformCulling`；`Runtime/Rendering/VegetationCulling.cs` → `CullVegetationHeapsJob`、`CountVegetationInstancesWithLodReferenceJob`、`ScatterVegetationVisibleInstancesJob` | Heap Job 处理 `H` 个 Heap 并生成可见标记；后续 Count 与 Scatter 仍各自按 `N` 个实例调度 |
| 绘制桶与每视图输出成本 | `Runtime/Rendering/VegetationBrgWorld.cs` → `OnPerformCulling`；`Runtime/Rendering/VegetationCulling.cs` → `ClearVegetationBucketsJob`、`PrefixVegetationBucketsJob` | 每个回调按全部 Bucket 和最大可见引用数分配输出容量；Clear/Prefix 扫描全部 `B` 个桶，Prefix 只为 `D` 个非空桶发出命令 |
| 可见索引与 GPU 槽位按同一展开序保持相等 | `Runtime/Rendering/VegetationSceneBatch.cs` → `UploadInstanceData`、`BuildCullingSnapshot`；`Runtime/Rendering/VegetationCulling.cs` → `ScatterVegetationVisibleInstancesJob.Execute`；`Shaders/MiniatureWorldVegetationInput.hlsl` → `VegetationLoadInstanceData` | 上传与 CPU 剔除数组都按 Heap/实例同序展开；Scatter 直接写数组下标，Shader 用该值乘 32 字节步长，没有额外索引表 |
| 常驻容量、全量上传与局部更新边界 | `Runtime/Rendering/VegetationRenderDataLayout.cs` → 构造函数；`Runtime/Rendering/VegetationSceneBatch.cs` → `CreateBufferAndBatch`、`Rebase`、`SetCellTransform`、`UploadInstanceData`、`UploadPackedInstanceData`；`Runtime/Rendering/VegetationBrgWorld.cs` → `SetActiveHeapMask` | 创建、Rebase 或 Cell Transform 变化会重建整份上传数据；单株预览只覆写目标 32 字节记录；Heap 激活只更新 CPU 掩码 |
| 普通视图共享 LOD 历史，阴影视图不更新历史 | `Runtime/Rendering/VegetationBrgWorld.cs` → `RebuildCullingSnapshot`、`OnPerformCulling`；`Runtime/Rendering/VegetationCulling.cs` → `CountVegetationInstancesWithLodReferenceJob.Execute` | World 只分配一份 `_previousLods`；普通视图写回，Light 视图把 `UpdateLodHistory` 设为 0 |
| 释放 Native 数据和 BRG 前等待最后的 CPU Culling Job | `Runtime/Rendering/VegetationBrgWorld.cs` → `Dispose`、`RebuildCullingSnapshot` | 先调用 `_lastCullingHandle.Complete()`，再释放 Culling NativeArray、原型注册与 BRG |
| 变换预览走现有会话内的原地更新 | `Runtime/Rendering/VegetationSceneBatch.cs` → `SetTransformPreviews`、`TryApplyTransformPreviewData`；`Runtime/Rendering/VegetationBrgWorld.cs` → `TrySetInstanceTransformPreviews` | 先验证整批 StableGuid，再更新当前 Buffer 与 CPU 剔除数据；没有独立预览 Buffer 或版本化资源世代 |

这些入口只能支持表内的窄主张。例如 `Complete()` 的存在不能证明 GPU Fence 退役已经实现；构造成功也不能替代失败注入。

源码中虽然存在名为 `VegetationSceneCullingSnapshot` 的运行读对象，但它没有资源世代、租约和独立 GPU Buffer；本文因此仍把“版本化快照退役”归入未来方案，不能只凭类型名推断该机制已经实现。

## 一、问题与适用范围

本文面向了解 Unity Scene、GameObject、Mesh、Material 与 Shader 基本关系的工程师，不要求读者预先掌握 Job System、BRG 或本项目命名；这些概念会在首次参与论证时定义。这里的“大规模”没有固定实例数，而是指逐对象 Renderer 和逐对象生命周期管理已经不再合适，需要集中实例数据、批量提交与空间工作集管理。

系统通常要同时满足：

- 编辑模式和播放模式看到同一份正式植被内容；
- SceneView、GameView、相机和阴影视图可以独立剔除；
- 编辑工具可以预览、提交和撤销，但不拥有长期渲染资源；
- 空间区域可以低频激活或流式装卸，而不为每次开关重传全部静态属性；
- 实例重排、分页或跨空间块移动后，选择和持久引用仍然有效。

本文不直接解决 GPU 遮挡剔除、特定 Shader/URP/XR 变体、资源包 IO、植被弯曲与物理模拟，也不承诺任意目标设备上的实例上限或帧耗。对于服务器动态生成、超大开放世界或多人并行编辑，可以保留本文的不变量，但必须替换资产分片、加载和协作政策。

## 二、核心术语与数据层

### 运行时 Cell 与 Heap

为避免同一个 “Cell” 同时表示两层边界，本文采用以下约定：

- **运行时 Cell**：一份场景植被资产及其独立渲染、查询和资源生命周期的所有权域。
- **Heap**：运行时 Cell 内部的最小空间分区，保存局部实例集合、空间坐标、Bounds 和可再生编译信息。

一个实现也可以把它们命名为 World/Cell、Region/Chunk 等。关键不是名字，而是加载域与内部空间块不能混称；同一实例在一个编译快照内只属于一个 Heap。

### 场景植被资产与原型

**场景植被资产**是保存植被作者数据的 ScriptableObject，不是 Unity Scene 文件。它至少保存原型表、Heap、实例变换、稳定身份和修订信息。相机、激活半径和更新频率属于运行策略，不必成为作者资产的一部分。

**原型**描述一类植被共享的 Mesh、Material、SubMesh、LOD、阴影部件、局部 Bounds 和其它静态规则。实例只保存原型引用和逐实例参数；Prototype 文件如何创建、刷新或发布不属于本文，只要求渲染快照取得的是身份稳定且通过输入校验的原型。

### 四层状态

系统必须区分：

1. **权威作者数据**：用户真正编辑和保存的实例、原型引用与 Heap 归属。
2. **派生缓存**：排序、Hash、连续数组、光照展开等可由作者数据重建的结果。
3. **运行读视图**：供 BRG 回调和 Job 一致读取的数据；版本化快照属于未来可选实现，不是当前 Buffer 组织方式。
4. **预览覆盖**：尚未提交的临时显示状态，不属于正式资产。

派生缓存和运行读视图都不能成为第二份权威数据。删除缓存后，系统必须能够从作者数据和外部依赖重新生成它。

### 渲染会话、活动集合与可选快照租约

**渲染会话**是一个实例所有权域内持有 BRG、GPU 存储、运行读视图和绘制提交权的生命周期对象；共享后端协议不表示多个所有权域共用同一个会话。

**ActiveHeapSet** 是当前会话中已经就绪、且被运行策略允许进入本次剔除的 Heap 集合。它是派生工作集，不是作者数据，也不表示每个 Heap 都拥有独立 Buffer 或 Batch；Desired、Loaded 与 Active 的精确关系见第七节。

**快照世代与快照租约**是未来可选的一致性模型：回调取得某一世代只读引用并登记其 JobHandle，换代时等待该世代的读取者排空。当前实现没有版本化 Buffer 或资源世代；当前明确执行的同步只是卸载或销毁前等待最后登记的 Culling Job，不能把后文的租约和世代协议描述为已经落地。

## 三、架构不变量

| 不变量 | 目的 |
|---|---|
| 编辑器与运行时共享同一后端实现和数据布局 | 防止材质、LOD、阴影和剔除规则分叉 |
| 同一实例所有权域不能存在范围重叠的绘制提交者 | 防止重复绘制、闪烁和重复资源 |
| 正式实例内容只有一个作者权威源 | 防止资产、缓存和预览互相覆盖 |
| 编辑工具不直接持有 BRG 生命周期或提交 DrawCommand | 让窗口关闭、重载和模式切换不破坏显示 |
| 预览状态与正式提交分离 | 保证取消、Undo 和失败恢复语义清楚 |
| Heap、GPU 存储、BRG Batch 与绘制桶相互正交 | 避免空间分区数量侵入渲染资源数量 |
| BRG 回调只读取一致的运行读视图 | 防止主线程修改与剔除 Job 并发冲突 |

“共享后端”指共享算法、协议和资源模型，不要求整个进程只有一个 BRG 对象。多个 Scene、多个运行时 Cell 或专用 Preview Scene 可以持有相互隔离的会话，只要实例集合与提交所有权不重叠。

## 四、端到端数据路径

下面分别列出当前参考实现与未来演进路径，二者不能合并成一条“已经实现”的执行轨迹。

**【实现观察】当前参考实现：**

```text
Prefab 或其它作者输入
  → 生成身份稳定且通过输入校验的 Prototype
  → SceneAsset 保存 Prototype 引用、StableID 与 Heap 局部 TRS（位置、旋转、缩放）
  → 正式作者事务发布新的内存作者状态
  → 编译器生成排序、Bounds、存储映射和绘制分类
  → 每个已加载运行时 Cell 创建独立 VegetationBrgWorld
  → SceneBatch 上传该 Cell 的共享 Buffer，并注册一个 BRG Batch
  → 世界策略更新 ActiveHeapMask
  → 每个视图仍扫描该 Cell 的全部实例
  → 先检查实例所属 Heap 的掩码，再执行实例剔除、LOD 和 RenderBucketKey 分类
  → visibleInstances 与 DrawCommand 引用同一份当前运行数据
  → 整个 Cell 或对应 Scene 卸载时，等待最后登记的 Culling Job 后释放整份资源
```

当前路径没有 Heap 级 Buffer 装卸、紧凑活动数组、独立多视图 LOD 历史或严格 GPU Fence 退役。

**【未来方案】可选演进：**

```text
作者状态
  → 版本化运行快照
  → 按需加载的 Buffer Page 或紧凑活动工作集
  → Desired、Loaded、Active 分阶段发布
  → 按稳定视图身份隔离的 LOD 历史
  → 新快照原子发布
  → 旧快照停止接受新租约
  → 等待 CPU Job 与 GPU Fence，或由独立资源世代完成隔离
  → 释放旧 Page、Batch 和 Buffer
```

这条演进路径是接口约束和候选方案，不是当前实现的验证结果。

作者事务只负责发布合法的作者状态和变更描述；完整重建还是局部更新由渲染宿主决定。Painter 的暂存（Stage）、撤销（Undo）、保存（Save）和通知协议见[植被 Painter 作者工作流](./unity-vegetation-painter-authoring-transaction-workflow.md)。

## 五、稳定身份、存储地址与绘制地址

本文用 **StableID** 泛指持久实例身份；配套专项在描述参考实现时使用具体名称 **StableGuid**，两者处于同一语义层。

以下标识不能互换：

- **StableID**：实例的持久身份，用于保存、选择、Undo 和跨编译定位。
- **LogicalIndex**：当前运行读视图中，实例在 CPU 连续数组里的位置。
- **SharedBufferSlot**：当前共享 Buffer 实例区中的记录序号；第 `s` 个槽的字节地址是 `PackedInstanceDataOffset + s × 32`。
- **BatchLocalIndex**：本文给 `visibleInstances` 元素中整数值起的语义名称。BRG 把它作为当前 Batch 的实例索引交给 Shader；它不会自动查询另一张“槽位映射表”。
- **可见表位置**：实例在 `visibleInstances` 数组中的写入位置。DrawCommand 保存这段数组的起点与数量，而数组元素本身保存 `BatchLocalIndex`。

**RenderBucketKey** 表示一次绘制中必须相同的渲染状态组合，例如已选 LOD、Pass、Prototype 绘制部件、Mesh/SubMesh、Material 和需要独立命令的固定变体。具体字段可以替换，但它不能包含每株都会变化的存储地址。

当前单 Buffer、单 Batch 实现不使用 `PageID`，也没有 `BatchLocalIndex → SharedBufferSlot` 间接表。上传器与 CPU 剔除快照都按 `SceneAsset.Heaps` 顺序、再按 Heap 内实例顺序展开；进入一个 Heap 时，之前 Heap 的实例总数就是 `HeapBase`，因此：

```text
StableID
  → Heap 内 RuntimeIndex
  → GlobalInstanceIndex = HeapBase + RuntimeIndex

LogicalIndex = GlobalInstanceIndex
SharedBufferSlot = GlobalInstanceIndex
BatchLocalIndex = GlobalInstanceIndex
```

这里的三个运行时编号在当前实现中被**有意保持数值相等**，但职责仍然不同：CPU 数组用 `LogicalIndex`，上传器用 `SharedBufferSlot`，BRG/Shader 用 `BatchLocalIndex`。Scatter 直接把正在遍历的 `LogicalIndex` 写进 `visibleInstances`；Shader 调用 `ComputeDOTSInstanceDataAddress(metadata, 32)`，以 Metadata 的实例区基址加上 `BatchLocalIndex × 32` 得到记录地址。不存在未写在源码中的额外重定向步骤。

绘制分类则决定这个编号被哪条命令引用：

```text
LogicalIndex + LOD + Pass + RenderPart
  → RenderBucketKey

LogicalIndex
  → 当前唯一 BatchID 下数值相同的 BatchLocalIndex
  → MetadataBase + BatchLocalIndex × 32
  → 数值相同的 SharedBufferSlot

按 BatchID + RenderBucketKey 计数并分配 visibleInstances 区间
  → visibleInstances[range] = BatchLocalIndex
  → DrawCommand{BatchID, RenderBucketKey, visibleOffset, visibleCount}
```

这种相等关系不是 BRG 的普遍定律，却是该参考实现当前 ABI 的硬约束；只改其中任意一条展开顺序都会让 Shader 读错实例。若未来让 `BatchLocalIndex` 与 `SharedBufferSlot` 不同，就必须实现一种真实可检查的地址变换：例如一个 Batch 对应 Buffer 中连续子区间时，把 Metadata 基址指向该子区间，并令 `SharedBufferSlot = BatchBaseSlot + BatchLocalIndex`；任意重排则必须增加并实际上传索引表，或把实例重排后复制到连续存储。当前实现三者都没有，因此不能宣称它已支持任意不同的两种编号。

### 一株实例如何走完整条链

下面用一株虚构的草 `G` 说明这些地址为何职责不同，即使当前值相等也不能在持久层混用。数字只用于演示；其中“32 字节记录”和三个运行时编号相等是本节绑定的工程案例布局，不是 BRG 的通用规定。

1. 作者资产把 `G` 的 `StableID` 保存为 `8f…21`。以后即使重新排序或移动到别的 Heap，这个身份仍不变。
2. 本次编译中，`G` 位于第 3 个 Heap。前面 Heap 共占 120 个槽，`G` 在本 Heap 的 `RuntimeIndex` 是 7，因此当前 `LogicalIndex` 和 GPU 槽都是 `127`。这只是本次编译结果，下次可能变成 204。
3. 上传器把它的紧凑实例记录写到 `PackedInstanceDataOffset + 127 × 32`。Batch 的 Metadata 为 Shader 属性 `_PackedInstanceData` 保存 `PackedInstanceDataOffset`，并标记该属性按实例寻址。当前 ABI 要求后续写入 `visibleInstances` 的值仍是 127，Shader 才会用相同公式找到第 127 条记录。
4. 相机剔除后，假设 `G` 选择了 LOD 1，并进入“草叶 Mesh + 绿色 Material + Forward Pass”对应的 `RenderBucketKey`。该分类决定怎样画，不改变 `G` 存在哪里。
5. Prefix Sum 为这个绘制桶分到 `visibleInstances[40..55]`。Scatter 恰好把 `G` 写到其中第 42 位，即 `visibleInstances[42] = 127`。这里的 42 是可见表位置，127 是当前 Batch 内可解释的实例索引。
6. DrawCommand 只需携带当前 `BatchID`、Mesh/Material 等绘制状态，以及 `visibleOffset = 40`、`visibleCount = 16`。执行到第 42 位时，BRG 读出 127；Batch Metadata 再让 Shader 从共享 Buffer 的实例区域解码 `G`。

因此，`StableID` 回答“它是谁”，127 回答“本次编译到哪里取数据”，42 回答“本视图的哪一段命令会引用它”。DrawCommand 不需要复制 `G` 的变换；Metadata 也不负责选择 Mesh 或 Material。将三类编号分开后，实例重排只需重建派生映射，不会破坏保存和选择所依赖的持久身份。

如果未来采用分页或多个存储 Batch，一种不需要间接表的具体做法是让每个 Batch 覆盖一个连续 Page：

```text
StableID
  → LogicalIndex
  → PageID + LocalSlot

PageID + LocalSlot + RenderBucketKey
  → 选择该 Page 的 BatchID
  → 该 Batch 的 MetadataBase 指向 Page 起点
  → BatchLocalIndex = LocalSlot
  → SharedBufferSlot = PageBaseSlot + LocalSlot
```

BRG 按 DrawCommand 的 `BatchID` 选择 Metadata，再用该命令引用的 `BatchLocalIndex` 做固定步长寻址。这是未来分页方案的一个可实现例子，不是当前代码路径。若 Page 内也要任意重排，就必须另行定义并实现索引表或重排上传。无论使用哪种方案，都应只为真实存在的 `BatchID + RenderBucketKey` 组合生成命令，不能先枚举全部 Batch，再与全部 `RenderBucketKey` 做笛卡尔积。

StableID 必须有明确作用域。资产内身份可以表示为复合键 `(SceneAssetID, StableID)`；跨资产拆分或合并时，要么为新资产建立新命名空间并迁移引用，要么显式声明多个分片属于同一世界命名空间并检查身份集合不重叠。普通复制不能静默继承会与原资产冲突的世界身份。

逐株数据的压缩位序、量化限制和 CPU/GPU 同量化要求见[BRG 逐株 Buffer 的压缩与量化 ABI](./unity-brg-packed-instance-buffer-quantization.md)。架构层只依赖一个不变量：CPU 剔除、GPU 解码和预览必须解释同一版数据协议。

## 六、职责与渲染会话生命周期

| 角色 | 核心职责 | 不应承担的职责 |
|---|---|---|
| 场景植被资产 | 保存作者数据和可再生缓存 | 主动提交渲染 |
| 场景授权组件 | 选择资产并保存运行策略 | 实现第二套渲染算法 |
| BRG 后端 | 注册资源、上传数据、持有当前运行读视图、剔除并生成命令 | 搜索编辑工具内部状态；在没有版本化实现时宣称持有“快照世代” |
| 编辑器宿主 | 解析编辑上下文授权，创建、刷新和释放会话 | 允许窗口绕过授权指定任意资产 |
| 运行时宿主 | 管理播放模式会话和运行工作集 | 执行编辑器 Undo 或 AssetDatabase 操作 |
| 编辑工具 | 修改作者数据并产生预览/正式变更 | 持有长期 BRG、Buffer 或 DrawCommand 所有权 |

### 授权与模式切换

**【接口要求】** 每个场景上下文或实例所有权域都要显式登记提交者。候选为零表示不渲染，候选冲突表示配置错误；“只允许一个对象挂组件”不能替代实例集合级的所有权门禁。

**【接口要求】** 编辑模式与播放模式的推荐切换协议如下。它描述应满足的所有权顺序，不表示本文已经验证参考实现对域重载、异常中断和所有模式切换分支都完成了该协议。

```text
普通编辑模式
  → 编辑器宿主持有会话

进入播放模式
  → 编辑会话停止接收新回调并完成退役
  → 运行时宿主从同一作者协议创建新会话

退出播放模式
  → 运行会话退役
  → 编辑器重新解析当前授权并恢复会话
```

**【接口要求】** 多 Scene 可以选择每 Scene 独立会话，也可以由世界级聚合器统一提交。两种政策都成立，但不能依赖“活动场景中找到的第一个组件”；授权作用域、实例集合和卸载责任必须可判定。

## 七、空间工作集与每视图可见集合

### Heap 不自动决定 Batch

Heap 回答“实例在哪里”，绘制桶回答“实例怎样绘制”。玩家移动会改变活动 Heap，但不会改变 Mesh 或 Material；材质和 LOD 变化会改变绘制桶，却不一定改变空间归属。

因此，增加 Heap 不应自动增加 BRG、Buffer 或 Batch。只有分片确实拥有独立流式生命周期、Buffer Page、资源集合或故障隔离要求时，才应通过显式政策把 Heap 映射到物理资源。

### 静态属性与保守 Bounds

**【实现观察】** 参考实现让实例静态属性整 Cell 驻留；Heap 激活只改变掩码，不重传变换、原型和光照数据。`BuildCullingSnapshot` 从编译 Bounds 出发，再并入量化后实例的视觉包围球与风摆余量，形成 Heap 的保守剔除球。

**【接口要求】** 无论采用何种数据结构，Heap 与实例 Bounds 都必须覆盖全部 LOD、缩放、风摆、顶点动画和允许的运行形变；否则视锥会在仍有顶点可见时提前剔除对象。预览把实例移出原 Heap 时，也必须临时扩张 Bounds 或使用独立预览集合。

### Desired、Loaded 与 Active

流式系统不能用一个布尔值同时表示请求、就绪和参与计算。这三个词描述的是一条资源状态链，而不是三种剔除算法：

```text
DesiredHeapSet：兴趣源和半径策略“想要”的 Heap；此时资源可能尚未准备好
LoadedHeapSet：CPU 数据、Mesh/Material 等依赖、GPU 数据和 Batch 注册都已就绪的 Heap
ActiveHeapSet：既 Desired 又 Loaded，并通过暂停、质量级别等运行政策，允许进入本轮计算的 Heap
```

**【接口要求】** `Loaded` 的发布必须有完整就绪屏障，保证后续回调能同时取得 CPU 数据、GPU 存储和 Batch 注册。只下载完 CPU 文件、但尚未上传 Buffer 的 Heap 不能称为 Loaded。

**【实现观察】** 当前参考实现没有 Heap 级异步装卸：整个 Cell 创建时全量数据一起驻留，因此 Heap 级 Loaded 实际上退化为“Cell 是否整体就绪”；兴趣策略只更新 `ActiveHeapMask`。

### 构建、加载与刷新失败

**【实现观察】** 静态源码核对只确认参考实现会在整 Cell 卸载前等待最后登记的 CPU Culling Job。本文没有证据证明它已经完成候选资源隔离、刷新失败回滚、旧回调门控或 GPU 安全退役。

**【接口要求】** 一次不会污染旧会话的刷新应具有以下事务边界；这段流程不能作为参考实现的能力声明。

```text
旧运行读视图继续服务现有回调
  → 在旧会话之外构建候选 CPU 数据、Buffer 与 Batch
  → 校验候选数据、Metadata、Batch 和依赖全部就绪
  → 构建失败：只销毁候选阶段已创建的资源，旧会话保持不变
  → 构建成功：一次性切换新回调可见的运行读视图
  → 阻止后续回调取得旧视图，同时允许已取得旧视图的回调结束
  → 等待旧 CPU Job；再通过 Fence 或独立资源世代确认旧 GPU 使用结束
  → 注销旧 Batch 并释放旧 Buffer、Native 容器和其它资源
```

**【接口要求】** “一次性切换”不限定具体实现；必要条件是回调不能观察到“新 Bounds 配旧 Buffer”或“新 Batch 配旧 Metadata”这样的混合状态。如果当前实现没有版本和 GPU 退役协议，安全做法是停止该 Cell 的新提交、排空现有工作并完整重建，而不是假装支持无缝热刷新。

**【未来方案】** 锁保护的引用替换、版本化双缓冲或完整会话换代都可以实现上述事务边界，但需要根据更新频率和资源成本单独选择。

各失败点至少应遵守以下政策：

| 失败点 | 接口要求 | 参考实现证据 |
|---|---|---|
| 作者状态编译或运行读视图构建失败 | 不发布候选视图；旧视图可用时继续使用，否则停止该 Cell 提交并报告错误 | 未验证失败路径 |
| GPU Buffer 创建或上传失败 | 候选资源不得进入 `Loaded`；释放候选阶段已创建资源，不改变旧 Batch 的存储解释 | 未执行失败注入 |
| BRG Batch 注册失败 | 清理候选的部分注册结果；不能留下“Buffer 已发布但 Batch 不可读”的状态 | 未执行失败注入 |
| 正式变更通知或宿主刷新失败 | 作者资产仍是恢复依据；重试只重建派生状态，不重复执行用户编辑事务 | 重试与错误呈现政策未确认 |
| 剔除回调或 Job 调度失败 | 不发布部分填充的可见表或 DrawCommand；进入可诊断的停绘或重建状态 | 异常处理路径未确认 |
| Cell 卸载 | 先拒绝新读取者，再排空已有 CPU/GPU 使用，最后释放资源 | 只确认 CPU Job 等待；GPU 退役未验证 |

任何失败都不能把半份运行数据标成 `Loaded`。实现还必须写清保留旧画面、暂时停绘或重试时的用户可见行为；沉默地保留一半新状态不是一种恢复策略。

### 每视图剔除与 LOD

**【实现观察】** Heap Bounds 同时参与两层判断，但两层不能混为一谈：兴趣源策略先决定 `ActiveHeapMask`；BRG 每视图回调再用当前视锥测试活动 Heap 的 Bounds，生成 `HeapVisibility`。随后 Count 和 Scatter 仍各自遍历该 Cell 的完整实例数组，因此 Heap 粗筛减少的是每株后续精细计算和可见输出，不会缩短这两个 Job 的迭代长度。

```text
上一个视图的 JobHandle
  ├─ Clear：清零全部 B 个桶的计数、掩码与游标
  └─ Heap Cull：用 ActiveHeapMask、Heap Bounds 和当前视图平面处理全部 H 个 Heap
       → 生成 HeapVisibility
  → Count：处理全部 N 个 LogicalIndex
       → 不可见 Heap 的实例立即退出
       → 对剩余实例做实例 Bounds 视锥测试、LOD 与滞回
       → 为每个可见渲染部件累计桶计数，共处理 P 个实例—部件引用
  → Prefix Sum：扫描全部 B 个桶并分配 visibleInstances 区间
       → 只为其中 D 个非空桶生成 DrawCommand/DrawRange
  → Scatter：再次处理全部 N 个 LogicalIndex
       → 把 P 个 BatchLocalIndex 写入已分配区间
```

这条依赖链说明 `O(H + N)` 只适合表达“一个视图的两个主数组规模”，不是完整成本：

- 单个视图回调实际包含一次 `H` 遍历、两次 `B` 遍历、两次 `N` 遍历，以及 Count/Scatter 各一次对 `P` 个可见实例—部件引用的处理，写成渐进式为 `O(H + B + N + P)`。
- 同一 Cell 一帧若收到 `K` 次相机或阴影视图回调，总成本为 `O(K(H + B + N) + ΣPᵥ)`；`Pᵥ` 是第 `v` 个视图的可见引用数。当前实现还把每次回调依赖到 `_lastCullingHandle`，所以不同视图的这几段工作进入同一串行依赖链，并不会自动彼此并行。
- `D ≤ B` 决定该视图实际生成的 DrawCommand/DrawRange 数量；即使只有少数非空桶，Clear 和 Prefix 仍会访问全部 `B` 个桶。Heap 数 `H` 不直接等于 DrawCall 数。
- 每个回调按 `B` 为 DrawCommand 与 DrawRange 预留容量，并按 `M` 为 `visibleInstances` 预留容量；`M` 是构建快照时按每株所有 LOD 中最大渲染部件数求和的保守上限，可能大于本视图实际写入的 `P`。

这些都是**每视图 CPU 剔除与输出成本**，不包含 Cell 首次创建、重建和常驻内存。当前 32 字节 ABI 下，共享 GPU Buffer 的主体容量为：

```text
固定头与对齐
+ 32 × max(1, N)                  // 逐株记录
+ 128 × max(1, H)                // 每 Heap 光照量化表
+ 8 × max(1, Lcolor)             // 静态颜色记录
+ 20 × max(1, Lsh)               // Bakery SH 记录
```

`Lcolor` 与 `Lsh` 分别是选择两种静态光照模式的实例数。Cell 创建时，上传器先在 CPU 端构造这整块数据，再一次性上传；Floating Origin 重定位（Rebase）或 Manager 根 Transform 变化也会重建快照并重传整块 Buffer。相反，兴趣范围变化只在等待旧 CPU Job 后复制 `H` 项 `ActiveHeapMask`，不会重传逐株 GPU 数据；单株变换预览只覆写目标的 32 字节记录。因而“剔除不重传”不等于“数据不常驻”，也不等于“完整重建没有上传成本”。

**【未来方案】** 如果要让 Heap 粗筛同时减少实例迭代数，执行链还要改为“按视图收集可见 Heap，再枚举这些 Heap 的实例区间”。这要求 Heap 能提供连续实例范围或额外索引；仅仅已有 `HeapVisibility`，不会让当前全实例 Job 自动变成紧凑遍历。

SceneView、普通相机、反射和阴影视图的投影与观察位置不同。LOD 历史要么按稳定视图身份隔离并在视图消失后淘汰，要么明确采用无状态或单主视图政策并接受误差。当前参考实现的普通视图共享 LOD 历史，Shadow 视图只是不更新历史；能够分别收到多个 culling callback，并不证明它们的 LOD 历史已经隔离。

全量扫描和紧凑工作集是两种可替换政策：

| 政策 | 优点 | 代价 |
|---|---|---|
| 全实例扫描，先检查 Heap 掩码 | 实现简单，索引稳定 | 每视图访问仍接近全量实例数 |
| 先收集可见 Heap，再构造紧凑实例范围 | 局部可见世界中访问更少 | 需要连续区间或额外索引，依赖和调试更复杂 |

选择应由目标设备分析决定。共享 Buffer 和激活掩码不能被当作“已经没有全量遍历”的证据。

## 八、运行一致性与未来退役协议

**【API事实】** BRG 剔除回调可以返回一个 `JobHandle`，Unity 会等待该依赖后消费回调输出。这个契约保护回调产生的 CPU 输出依赖，但不会自动替应用管理长期存在的 Native 容器和 GraphicsBuffer 生命周期。

**【实现观察】** 参考实现的回调 Job 会读取 Heap、实例、LOD 和绘制映射；主线程在替换这些 NativeArray 或整体释放前调用最后登记的 Culling `JobHandle.Complete()`。当前证据只支持 CPU Job 排空。

**【未来方案】** 下面的不可变快照、版本化双缓冲、租约和 GPU Fence 是更严格热切换或退役所需的候选协议，不是当前已经实现的生命周期。

**【接口要求】** 完整关闭会话时，安全顺序为：

```text
Running
  → Closing：阻止新回调取得旧快照
  → Draining：冻结已登记的租约集合并等待 CPU Job
  → Retiring：等待 GPU Fence，或用独立资源世代隔离仍使用旧 Batch/Buffer 的工作
  → Disposed：注销 Batch 并释放 Native 容器、Buffer 和 BRG
```

**【未来方案】** 热切换快照时，会话仍保持 Running：先原子发布新快照，使新回调只取得新世代；旧快照停止发出租约，经过 Draining 后进入 Retiring，排空自己的 GPU 使用再释放。完成 CPU Job 只能证明 CPU 不再读取，不能证明此前提交的 GPU 工作已经停止使用公开 Buffer；如果没有 Fence、版本化 Buffer 或独立资源世代，就不能声称已完成 GPU 退役。

**【未来方案】** 若加入 Heap 或 Buffer Page 级装卸，单个分片也必须遵循同样的“门控—排空—退役”原则，且不能复用整会话 Closing 误伤其它仍在工作的分片。当前实现没有这条 Heap 级资源装卸路径。

## 九、作者预览与外部坐标系统的接口

**【接口要求】** 编辑工具只应通过两条受控通道接入：

- **预览通道**发布 StableID、临时矩阵、保守 Bounds 和预览世代；它不能写正式资产，也不能直接控制 BRG 生命周期。
- **正式变更通道**在新的作者状态自洽后发布资产身份、受影响 Heap、原型变化和缓存失效范围；后端自行选择局部更新或重建。

**【实现观察】** 参考实现的变换预览在验证整批 StableGuid 后，原地更新现有 Buffer 与 CPU 剔除数据；它没有独立预览 Buffer 或版本化资源世代。该事实说明当前路径如何工作，不证明在途 GPU 读取下的原地覆盖已经具备严格退役保证。

**【接口要求】** 一次可见预览必须让 CPU Bounds、GPU 实例数据和命令构建相互一致。局部原地 Patch 只有在能够证明旧 GPU 工作不再读取目标区域时才安全。

**【未来方案】** 备用 Buffer、版本化 Page 或独立预览 Batch 都能隔离预览写入，但代价不同，本文不指定唯一实现。完整交互与 Undo 语义见[植被 Painter 作者工作流](./unity-vegetation-painter-authoring-transaction-workflow.md)。

**【接口要求】** Floating Origin 或运行时 Cell Transform 变化不应改写作者 Heap 坐标和 StableID。外部协调器必须让渲染、解析查询和物理代理观察到同一次坐标变更；压缩重编码边界见[逐株 Buffer ABI](./unity-brg-packed-instance-buffer-quantization.md)，查询索引平移见[两级懒建 BVH](./unity-vegetation-two-level-lazy-bvh-query.md)，物理代理边界见[多运行时 Cell 物理流送](./unity-vegetation-multi-cell-physics-streaming.md)。

## 十、策略变体与验证方法

| 条件 | 推荐变体 | 主要代价 |
|---|---|---|
| 单场景、中等规模、数据可驻留 | 一份场景资产、多个 Heap、一个会话 | 全量扫描和单文件体积可能先成为瓶颈 |
| Additive Scene 独立装卸 | 每 Scene 独立资产与会话，或世界聚合会话 | 必须定义授权和卸载所有权 |
| GPU 数据超过单 Buffer 或项目上限 | 固定容量 Buffer Page | 增加地址映射、Batch 注册和资源退役复杂度 |
| 世界极大且局部可见 | 资产分片、异步加载和紧凑工作集 | 需要 Loaded 屏障、引用计数和分片事务 |
| 多人并行编辑 | 按 Scene、区域或内容所有权拆分作者资产 | 需要跨资产身份和引用迁移政策 |
| 运行时实例高频增删 | 空闲槽、间接映射或动态 Page | 索引稳定性和碎片管理更复杂 |

本文已经给出冻结 Git 提交与模块 tree 作为可定位的源码锚点，但知识记录没有复制该私有仓库的完整源码，也没有附带自动化原始报告或目标设备捕获。因此，文中的参考实现观察可由有权限的读者复核，却不能用精确用例计数或一个哈希值替代运行验证。读者可以用下面的最小实验核验自己的版本；每项实验应记录 Unity 版本、图形后端、提交标识、场景输入、相机参数和原始捕获，而不是只保存“通过”结论。

| 要验证的主张 | 可复现实验 | 应观察的结果 | 结论边界 |
|---|---|---|---|
| 编辑器与运行时共享后端协议 | 对比两种模式下创建的后端类型、Metadata、Buffer 布局与剔除入口 | 两种模式走同一数据解释和命令构建路径 | 只能证明协议一致，不能证明视觉和性能已达标 |
| 同一实例只有一个提交者 | 在多 Scene、Additive Scene 和播放模式切换时记录会话 ID 与 StableID 集合 | 任一时刻各提交集合不重叠，卸载后对应集合消失 | 需覆盖异常中断和重载，单场景测试不够 |
| Heap 与 Batch 正交 | 固定 Mesh、Material、Pass 和 LOD，只增加 Heap 数；用 Frame Debugger 或 BRG 统计记录 Batch/DrawCommand | 命令按渲染状态形成，不随 Heap 数线性增长 | 相机可见性、Pass 或 LOD 变化会合法地改变命令数 |
| Heap 激活和视锥粗筛不重传静态数据 | 在不修改实例的情况下改变兴趣范围和相机视锥，记录 Buffer 上传字节以及 `H/N/B/P/D/K` 与各 Job 耗时 | 静态实例 Buffer 不重传；每视图 Heap Cull 处理 `H`，Clear/Prefix 处理 `B`，Count/Scatter 各处理 `N`，实际输出为 `P` 个引用和 `D` 条命令 | 证明“不可见实例很快退出”不等于证明“CPU 不全扫”；单相机结果不能代表多视图成本 |
| 多视图 LOD 是否隔离 | 两台距离显著不同的相机同时观察同一实例并交替渲染 | 独立方案应各自稳定；基线共享历史可能互相影响 | 必须记录每个视图的 LOD 选择，单张截图不足 |
| 刷新失败能否保旧 | 分别在编译、Buffer 上传和 Batch 注册阶段注入失败 | 旧完整会话继续显示，或按声明政策停绘；不能出现半新半旧状态 | 本文把它列为接口要求，未声明参考实现已通过 |
| 关闭是否安全退役 | 在持续产生剔除回调时反复卸载 Cell，并结合 Job 安全检查与 GPU 捕获 | 不再有旧回调访问；CPU Job 和 GPU 资源都在释放前排空 | 只等待 Job 不能证明 GPU 已结束使用 |
| 全量扫描是否符合预算 | 固定可见实例数，逐步增加非活动实例，再比较全量扫描与紧凑工作集 | 基线 CPU 时间会随总实例数增长；紧凑方案应主要随候选数增长 | 必须在目标设备测量，Editor 数据不可替代设备预算 |

如果实验记录没有绑定具体输入和原始捕获，就只能作为排查线索，不能升级为可复核的性能或正确性证据。

### 参考链接

- [Unity Manual - BatchRendererGroup](https://docs.unity3d.com/2022.3/Documentation/Manual/batch-renderer-group.html) - BRG 的定位与使用入口。
- [Unity Manual - How BatchRendererGroup works](https://docs.unity3d.com/2022.3/Documentation/Manual/batch-renderer-group-how.html) - Batch、剔除回调和绘制流程。
- [Unity Scripting API - BatchRendererGroup](https://docs.unity3d.com/2022.3/Documentation/ScriptReference/Rendering.BatchRendererGroup.html) - API 类型与生命周期参考。
- [Unity Manual - DOTS Instancing shaders](https://docs.unity3d.com/2022.3/Documentation/Manual/dots-instancing-shaders.html) - Shader 读取每实例数据的协议。

### 相关记录

- [植被 Painter 作者工作流与事务设计](./unity-vegetation-painter-authoring-transaction-workflow.md) - Authority、Stage、Undo 与正式变更协议。
- [BRG 逐株 Buffer 的压缩与量化 ABI](./unity-brg-packed-instance-buffer-quantization.md) - 存储位序、量化限制及 CPU/GPU 一致性。
- [Heap–Shape 两级懒建 BVH 查询](./unity-vegetation-two-level-lazy-bvh-query.md) - 空间查询、索引失效和 Floating Origin 平移。
- [多运行时 Cell 物理查询与 Collider 流送](./unity-vegetation-multi-cell-physics-streaming.md) - 查询与物理代理的所有权、加载和卸载接口。
- [Bakery L2 静态光照与投影代理](./unity-vegetation-bakery-static-lighting-pipeline.md) - Prototype/实例变化引起的光照缓存失效边界。

### 验证记录

- [2026-09-03] 证据快照：Unity 2022.3 官方 BRG 文档与提交 `f0fef16849cfb8945e9928e5219a140ee250fcf4`、模块 tree `4700f76e0b087fe3935c06e660ee732bbf55c87a` 的静态源码共同支持本文所述单 Cell Buffer/Batch、Heap 激活、可见索引寻址、两级剔除调度、LOD 历史和 CPU Job 释放顺序。该快照没有包含故障注入、完整模式切换回归、GPU 退役捕获或目标设备性能测量；分页、紧凑工作集、按视图 LOD 历史、候选刷新事务和 GPU 世代退役仍属于接口要求或未来方案。

## 结论

对于数据能够整 Cell 驻留、可以接受每个相机与阴影视图都扫描该 Cell 完整实例数组的场景，当前参考实现给出了一条明确基线：SceneAsset 保存唯一作者数据，每个运行时 Cell 独立拥有一份共享 Buffer 和一个 BRG Batch，Heap 只承担空间归属与激活筛选，StableID、存储地址和绘制地址分别建模。当前 Shader 寻址之所以成立，是因为 CPU 剔除数组、GPU 上传槽和 `visibleInstances` 值按同一顺序展开；它不是 BRG 自动提供的任意索引映射。

这条基线不等于超大开放世界或目标设备生产预算已经解决。当全量扫描、单 Buffer 容量、多视图 LOD 干扰或资源退役成为实际瓶颈时，应分别验证紧凑工作集、分页、独立视图历史和 GPU 世代退役；未完成对应验证前，不应把候选方案写成当前能力。本文对“当前实现”的判断只绑定前述冻结提交与模块 tree 的静态源码观察；故障注入、完整模式切换回归、GPU 退役捕获和目标设备容量/帧耗仍未执行。

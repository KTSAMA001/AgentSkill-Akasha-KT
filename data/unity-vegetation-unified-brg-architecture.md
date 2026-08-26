# Unity 大规模植被的统一 BRG 架构

**标签**：#unity #architecture #rendering #editor #performance #culling #scriptable-object
**来源**：工程实践抽象 - Unity 大规模植被的数据权威、渲染会话与空间工作集设计
**收录日期**：2026-08-06
**更新日期**：2026-08-26
**状态**：⚠️ 待验证
**可信度**：⭐⭐⭐（核心职责边界可由 BRG API 责任模型与状态转换推导；分页、紧凑工作集、多视图历史与 GPU 退役仍需按项目验证）
**适用版本**：Unity 2022.3 LTS 的 BatchRendererGroup API 模型；其它版本需重新确认 API 与图形后端行为

---

### 概要

大规模植被不应由逐株 GameObject、编辑器窗口或空间块各自维护一套渲染状态。更稳定的做法是：场景资产保存唯一的作者数据，编辑器与运行时共享同一套 `BatchRendererGroup`（BRG）后端协议，空间分区只组织数据和工作集，GPU 存储、BRG Batch 与绘制桶分别建模。

本文只讨论这套架构的职责、地址、生命周期和演进边界。Painter 事务、实例压缩 ABI、物理查询、静态光照和 Floating Origin 的内部实现属于独立专题；本文仅定义它们接入渲染架构时必须满足的接口。

## 一、问题与适用范围

本文面向熟悉 Unity Scene、ScriptableObject、Job System 和基本渲染概念的工程师。这里的“大规模”没有固定实例数，而是指逐对象 Renderer 和逐对象生命周期管理已经不再合适，需要集中实例数据、批量提交与空间工作集管理。

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
3. **运行快照**：供 BRG 回调和 Job 读取的不可变或版本化数据。
4. **预览覆盖**：尚未提交的临时显示状态，不属于正式资产。

派生缓存和运行快照都不能成为第二份权威数据。删除缓存后，系统必须能够从作者数据和外部依赖重新生成它。

### 渲染会话、活动集合与快照租约

**渲染会话**是一个实例所有权域内持有 BRG、GPU 存储、运行快照和绘制提交权的生命周期对象；共享后端协议不表示多个所有权域共用同一个会话。

**ActiveHeapSet** 是当前会话中已经就绪、且被运行策略允许进入本次剔除的 Heap 集合。它是派生工作集，不是作者数据，也不表示每个 Heap 都拥有独立 Buffer 或 Batch；Desired、Loaded 与 Active 的精确关系见第七节。

**快照世代**是一次完整运行快照的单调递增标识。**快照租约**是回调取得某一世代只读引用并登记其 JobHandle 的协议：取得租约与确认会话仍可读必须原子完成，释放或换代则必须等该世代的全部租约排空。

## 三、架构不变量

| 不变量 | 目的 |
|---|---|
| 编辑器与运行时共享同一后端实现和数据布局 | 防止材质、LOD、阴影和剔除规则分叉 |
| 同一实例所有权域不能存在范围重叠的绘制提交者 | 防止重复绘制、闪烁和重复资源 |
| 正式实例内容只有一个作者权威源 | 防止资产、缓存和预览互相覆盖 |
| 编辑工具不直接持有 BRG 生命周期或提交 DrawCommand | 让窗口关闭、重载和模式切换不破坏显示 |
| 预览状态与正式提交分离 | 保证取消、Undo 和失败恢复语义清楚 |
| Heap、GPU 存储、BRG Batch 与绘制桶相互正交 | 避免空间分区数量侵入渲染资源数量 |
| BRG 回调只读取一致的运行快照 | 防止主线程修改与剔除 Job 并发冲突 |

“共享后端”指共享算法、协议和资源模型，不要求整个进程只有一个 BRG 对象。多个 Scene、多个运行时 Cell 或专用 Preview Scene 可以持有相互隔离的会话，只要实例集合与提交所有权不重叠。

## 四、端到端数据路径

一个完整但不绑定具体工具类的路径如下：

```text
Prefab 或其它作者输入
  → 生成身份稳定的 Prototype
  → 场景资产保存 Prototype 引用、StableID 与 Heap 局部 TRS
  → 正式作者事务发布新的内存状态
  → 编译器生成排序、Bounds、存储映射和绘制分类
  → 渲染宿主构建不可变运行快照
  → 上传实例数据并注册兼容的 BRG Batch
  → 世界策略得到已就绪且允许参与剔除的 ActiveHeapSet
  → 每个视图执行 Heap 粗筛、实例精筛、LOD 与绘制分组
  → visibleInstances 和 DrawCommand 引用同一快照世代
  → 快照替换或运行时 Cell 卸载时，先门控新读取者，再排空并退役旧资源
```

作者事务只负责发布合法的作者状态和变更描述；完整重建还是局部更新由渲染宿主决定。Painter 的 Stage、Undo、Save 和通知协议见[植被 Painter 作者工作流](./unity-vegetation-painter-authoring-transaction-workflow.md)。

## 五、稳定身份、存储地址与绘制地址

本文用 **StableID** 泛指持久实例身份；配套专项在描述参考实现时使用具体名称 **StableGuid**，两者处于同一语义层。

以下标识不能互换：

- **StableID**：实例的持久身份，用于保存、选择、Undo 和跨编译定位。
- **LogicalIndex**：某个运行快照中，实例在 CPU 连续数组里的位置。
- **存储地址**：实例属性在 GPU 中的位置；分页时通常表示为 `PageID + LocalSlot`。
- **BatchLocalIndex**：实例在某个 `BatchID` 协议内的索引；该 Batch 的 Metadata 必须能把它解释为正确的 GPU 存储位置。
- **可见表位置**：实例在 `visibleInstances` 数组中的写入位置。DrawCommand 保存这段数组的起点与数量，而数组元素本身保存 `BatchLocalIndex`。

**RenderBucketKey** 表示一次绘制中必须相同的渲染状态组合，例如已选 LOD、Pass、Prototype 绘制部件、Mesh/SubMesh、Material 和需要独立命令的固定变体。具体字段可以替换，但它不能包含每株都会变化的存储地址。

存储寻址是：

```text
StableID
  → LogicalIndex
  → PageID + LocalSlot
```

绘制分类是另一条映射：

```text
LogicalIndex + LOD + Pass + RenderPart
  → RenderBucketKey

PageID + LocalSlot + RenderBucketKey
  → 兼容的 Batch 注册
  → BatchID + BatchLocalIndex

LogicalIndex
  → BatchID + BatchLocalIndex + RenderBucketKey

按 BatchID + RenderBucketKey 计数并分配 visibleInstances 区间
  → visibleInstances[range] = BatchLocalIndex
  → DrawCommand{BatchID, RenderBucketKey, visibleOffset, visibleCount}
```

BRG 按 DrawCommand 的 `BatchID` 选择 Metadata，再把该命令所引用 `visibleInstances` 区间中的每个 `BatchLocalIndex` 解释为批次内实例。单 Buffer、单 Batch时，LogicalIndex、LocalSlot 与 BatchLocalIndex 可能偶然相等；它们仍然不是同一种身份。分页、多 Batch、多个 SubMesh 或阴影部件都会打破这种相等关系。一个存储位置也可能通过不同 Metadata 参与多个兼容 Batch，因此不能先枚举全部 Batch，再与全部绘制桶做笛卡尔积。

StableID 必须有明确作用域。资产内身份可以表示为复合键 `(SceneAssetID, StableID)`；跨资产拆分或合并时，要么为新资产建立新命名空间并迁移引用，要么显式声明多个分片属于同一世界命名空间并检查身份集合不重叠。普通复制不能静默继承会与原资产冲突的世界身份。

逐株数据的压缩位序、量化限制和 CPU/GPU 同量化要求见[BRG 逐株 Buffer 的压缩与量化 ABI](./unity-brg-packed-instance-buffer-quantization.md)。架构层只依赖一个不变量：CPU 剔除、GPU 解码和预览必须解释同一版数据协议。

## 六、职责与渲染会话生命周期

| 角色 | 核心职责 | 不应承担的职责 |
|---|---|---|
| 场景植被资产 | 保存作者数据和可再生缓存 | 主动提交渲染 |
| 场景授权组件 | 选择资产并保存运行策略 | 实现第二套渲染算法 |
| BRG 后端 | 注册资源、上传数据、持有快照、剔除并生成命令 | 搜索编辑工具内部状态 |
| 编辑器宿主 | 解析编辑上下文授权，创建、刷新和释放会话 | 允许窗口绕过授权指定任意资产 |
| 运行时宿主 | 管理播放模式会话和运行工作集 | 执行编辑器 Undo 或 AssetDatabase 操作 |
| 编辑工具 | 修改作者数据并产生预览/正式变更 | 持有长期 BRG、Buffer 或 DrawCommand 所有权 |

### 授权与模式切换

每个场景上下文或实例所有权域都要显式登记提交者。候选为零表示不渲染，候选冲突表示配置错误；“只允许一个对象挂组件”不能替代实例集合级的所有权门禁。

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

多 Scene 可以选择每 Scene 独立会话，也可以由世界级聚合器统一提交。两种政策都成立，但不能依赖“活动场景中找到的第一个组件”；授权作用域、实例集合和卸载责任必须可判定。

## 七、空间工作集与每视图可见集合

### Heap 不自动决定 Batch

Heap 回答“实例在哪里”，绘制桶回答“实例怎样绘制”。玩家移动会改变活动 Heap，但不会改变 Mesh 或 Material；材质和 LOD 变化会改变绘制桶，却不一定改变空间归属。

因此，增加 Heap 不应自动增加 BRG、Buffer 或 Batch。只有分片确实拥有独立流式生命周期、Buffer Page、资源集合或故障隔离要求时，才应通过显式政策把 Heap 映射到物理资源。

### 静态属性与保守 Bounds

实例属性能够驻留时，Heap 激活只改变精细剔除的候选集合，不需要重传静态变换、原型和光照数据。Heap 与实例 Bounds 必须保守覆盖全部 LOD、缩放、风摆、顶点动画和允许的运行形变；预览把实例移出原 Heap 时，也必须临时扩张 Bounds 或使用独立预览集合。

### Desired、Loaded 与 Active

流式系统不能用一个布尔值同时表示请求、就绪和参与计算：

```text
DesiredHeapSet：参考物体希望使用的区域
LoadedHeapSet：CPU 数据、依赖资源、GPU 数据和 Batch 注册均已就绪
ActiveHeapSet：Desired ∩ Loaded，并通过当前运行政策
```

`Loaded` 的发布必须有完整就绪屏障，保证后续回调能同时取得 CPU 数据、GPU 存储和 Batch 注册。全量数据始终驻留、只更新一个激活掩码也是合法基础政策，但不能把它描述成已经具备异步流式装卸。

### 每视图剔除与 LOD

典型流水线为：

```text
ActiveHeapSet
  → Heap Bounds 粗筛
  → 实例 Bounds 精筛
  → 每视图 LOD 选择与滞回
  → RenderBucketKey
  → 兼容的 BatchID / BatchLocalIndex
  → Count：统计每个 BatchID + RenderBucketKey 的可见数量
  → Prefix Sum：把各组数量转换为互不重叠的 visibleInstances 写入区间
  → Scatter：把每株的 BatchLocalIndex 写入所属区间
  → DrawCommand 引用 BatchID、渲染状态和对应区间
```

SceneView、普通相机、反射和阴影视图的投影与观察位置不同。LOD 历史要么按稳定视图身份隔离并在视图消失后淘汰，要么明确采用无状态或单主视图政策并接受误差。能够分别收到多个 culling callback，并不自动证明它们的 LOD 历史已经隔离。

全量扫描和紧凑工作集是两种可替换政策：

| 政策 | 优点 | 代价 |
|---|---|---|
| 全实例扫描，先检查 Heap 掩码 | 实现简单，索引稳定 | 每视图访问仍接近全量实例数 |
| 先收集可见 Heap，再构造紧凑实例范围 | 局部可见世界中访问更少 | 需要连续区间或额外索引，依赖和调试更复杂 |

选择应由目标设备分析决定。共享 Buffer 和激活掩码不能被当作“已经没有全量遍历”的证据。

## 八、运行快照、关闭与 Retiring

BRG 回调可能调度 Job 读取 Heap、实例、LOD 和绘制映射。主线程不能在这些读取期间原地修改数据。常见一致性方案有不可变快照、版本化双缓冲和显式同步点；无论采用哪一种，回调取得快照和登记 JobHandle 必须经过同一套租约协议。

完整关闭会话时，安全顺序为：

```text
Running
  → Closing：阻止新回调取得旧快照
  → Draining：冻结已登记的租约集合并等待 CPU Job
  → Retiring：等待 GPU Fence，或用独立资源世代隔离仍使用旧 Batch/Buffer 的工作
  → Disposed：注销 Batch 并释放 Native 容器、Buffer 和 BRG
```

热切换快照时，会话仍保持 Running：先原子发布新快照，使新回调只取得新世代；旧快照停止发出租约，经过 Draining 后进入 Retiring，排空自己的 GPU 使用再释放。完成 CPU Job 只能证明 CPU 不再读取，不能证明此前提交的 GPU 工作已经停止使用公开 Buffer；如果没有 Fence、版本化 Buffer 或独立资源世代，就不能声称已完成 GPU 退役。

单个流式 Heap 卸载遵循同样的“门控—排空—退役”原则，但只处理该分片。它不能复用整会话 Closing 来误伤其它仍在工作的 Heap。

## 九、作者预览与外部坐标系统的接口

架构篇只要求编辑工具通过两条受控通道接入：

- **预览通道**发布 StableID、临时矩阵、保守 Bounds 和预览世代；它不能写正式资产，也不能直接控制 BRG 生命周期。
- **正式变更通道**在新的作者状态自洽后发布资产身份、受影响 Heap、原型变化和缓存失效范围；后端自行选择局部更新或重建。

一次可见预览必须让 CPU Bounds、GPU 实例数据和命令构建属于同一世代。局部原地 Patch 只有在能够证明旧 GPU 工作不再读取目标区域时才安全；否则应使用备用 Buffer、版本化 Page 或独立预览 Batch。完整交互与 Undo 语义见[植被 Painter 作者工作流](./unity-vegetation-painter-authoring-transaction-workflow.md)。

Floating Origin 或运行时 Cell Transform 变化不应改写作者 Heap 坐标和 StableID。外部协调器必须以同一世代更新渲染、解析查询和物理代理；压缩重编码边界见[逐株 Buffer ABI](./unity-brg-packed-instance-buffer-quantization.md)，查询索引平移见[两级懒建 BVH](./unity-vegetation-two-level-lazy-bvh-query.md)，物理代理边界见[多运行时 Cell 物理流送](./unity-vegetation-multi-cell-physics-streaming.md)。

## 十、策略变体与验证

| 条件 | 推荐变体 | 主要代价 |
|---|---|---|
| 单场景、中等规模、数据可驻留 | 一份场景资产、多个 Heap、一个会话 | 全量扫描和单文件体积可能先成为瓶颈 |
| Additive Scene 独立装卸 | 每 Scene 独立资产与会话，或世界聚合会话 | 必须定义授权和卸载所有权 |
| GPU 数据超过单 Buffer 或项目上限 | 固定容量 Buffer Page | 增加地址映射、Batch 注册和资源退役复杂度 |
| 世界极大且局部可见 | 资产分片、异步加载和紧凑工作集 | 需要 Loaded 屏障、引用计数和分片事务 |
| 多人并行编辑 | 按 Scene、区域或内容所有权拆分作者资产 | 需要跨资产身份和引用迁移政策 |
| 运行时实例高频增删 | 空闲槽、间接映射或动态 Page | 索引稳定性和碎片管理更复杂 |

下表是可证伪的验收方法，不表示任何具体实现已经执行这些测试：

| 主张 | 验证方法 | 失败信号 |
|---|---|---|
| 编辑器与运行时共享后端协议 | 比较创建类型、数据布局和剔除路径 | 两套材质或剔除逻辑逐渐分叉 |
| 同一实例只有一个提交者 | 统计各会话负责的实例集合和模式切换过程 | 重复绘制、闪烁或重复资源 |
| Heap 不自动决定 Batch | 增加 Heap 数并观察 Batch/DrawCommand | Batch 随 Heap 无理由增长 |
| 激活不重传静态属性 | 移动参考物体并记录上传范围 | 每次开关都重传整场实例数据 |
| Loaded 有完整屏障 | 在 IO、上传和 Batch 注册间分别注入延迟 | 已标 Loaded 的 Heap 缺少可读资源 |
| 多视图状态隔离 | 让两个距离不同的相机同时观察同一实例 | 相机互相改变 LOD 或持续抖动 |
| 快照关闭先门控再排空 | 在回调持续进入时切换模式或卸载 | 释放后仍有 Job 或回调读取旧资源 |
| GPU 资源按世代退役 | 连续切换预览或快照并检查旧工作 | 新 Bounds 与旧矩阵混用或覆盖在途 Buffer |
| 复杂度符合目标规模 | 分别测全量扫描和紧凑工作集 | Job 时间随无关实例数不可接受增长 |
| 设备预算满足要求 | 在目标设备测 CPU、GPU、内存和尖峰 | 编辑器正确但设备帧率或内存不达标 |

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

- **设计依据**：职责分离、StableID 与运行地址分层、Heap/Batch 正交、会话门控和快照退役，都能由 BRG API 的责任模型及明确的编辑器/运行时状态转换推导，并可按第十节逐项证伪。
- **未验证边界**：Buffer Page、多 Batch、紧凑工作集、每视图 LOD 历史、GPU Fence 或版本化退役，以及目标设备容量和性能，必须在采用这些策略的具体实现中分别验证。

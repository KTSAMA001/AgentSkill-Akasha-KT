# Unity 输出型 AssetPostprocessor 的语义差分与可恢复重导设计

**标签**：#unity #fbx #custom-editor #architecture
**来源**：实践总结 - Unity 2022.3 LTS 隔离验证，并结合 Unity 官方文档复核
**收录日期**：2026-07-21
**来源日期**：2026-07-21
**更新日期**：2026-07-22
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐（Unity 2022.3 LTS 实践验证 + Unity 官方 API 文档复核）
**适用版本**：Unity 2021.2+；实践验证版本为 Unity 2022.3 LTS

### 概要

当 `AssetPostprocessor` 不只是调整 Importer 参数，而是直接改变 Mesh、UV、法线等导入输出时，正确性不能只靠“配置文件变了就全量重导”或“缓存里有记录就跳过”。稳定设计需要同时建立三条关系：配置输出语义与受影响范围的差分、输出配置与 Unity 导入缓存的自定义依赖、资源实际处理结果与可恢复任务的持久化记录。

### 内容

#### 一、先区分三种变化来源

| 变化来源 | 应负责的机制 | 不应采用的替代方案 |
|---|---|---|
| 处理器代码变化 | 显式版本策略，或由开发者判断后手动全量重导 | 每次自动扫描源码并把哈希当作版本 |
| 配置输出语义变化 | 处理器级语义指纹、旧/新作用范围差分、Unity 自定义依赖 | 原始配置文件整体哈希变化后全项目重导 |
| 资源或处理记录不一致 | 正常 Unity 导入回执、完整性检查和未完成任务恢复 | 导入结束后立即再次导入同一资源 |

代码、配置、资源状态的生命周期不同。把三者合成一个全局哈希虽然实现简单，但会同时制造误重导和漏处理：非输出字段变化会扩大导入范围，范围缩小时旧结果无法清理，代码编译失败期间进入项目的资源也缺少可靠的后续补偿依据。

#### 二、`GetVersion()` 应是显式版本，不应是动态源码哈希

Unity 官方定义中，`AssetPostprocessor.GetVersion()` 的版本发生变化后，相关资源会在脚本重新编译时重导。它适合“开发者明确提升导入算法版本”的场景。

如果产品策略决定代码变化由开发者人工判断，则可以删除该覆写，并把“强制全量重导”作为显式操作。尤其不建议动态读取源码并计算版本，原因包括：

- 注释、空白、辅助代码和文件顺序都可能产生非输出变化。
- 一个全局源码哈希无法表达“哪个处理器变化、影响哪个范围”。
- Unity 会把版本变化理解为导入器版本变化，可能触发远大于真实影响范围的重导。
- 代码编译失败时，新源码和当前实际运行的最后一次有效程序集可能并不一致。

这不是说 `GetVersion()` 本身有问题，而是版本的所有权必须明确：要么由开发者显式维护，要么完全交给人工全量重导，不能用不稳定的源码文本自动替代业务版本决策。

#### 三、具体 `AssetPostprocessor` 回调类型名应保持稳定

Unity 扫描到的具体 `AssetPostprocessor` 完整类型名可能参与导入器缓存身份。即使回调行为没有变化，代码整理时改变该类型的命名空间、程序集或类名，也可能使已有模型发生迁移性重导。

Unity 2022.3 隔离对照测试表明：

- 直接改变具体后处理器的完整类型名，已有模型可能发生迁移性重导。
- 保留原命名空间、程序集和类名的具体回调入口，只把内部实现移动到新位置时，单纯代码整理不会触发已有模型重导。
- 随后真实修改模型资源，稳定入口仍会调用新实现，说明薄入口没有阻断正常导入。

因此应把具体回调类型当作导入器的稳定外壳：

1. 长期保留被 Unity 扫描的具体 `AssetPostprocessor` 完整类型名。
2. 回调入口只转发到唯一业务实现，不保存配置、不复制算法、不持有独立状态。
3. 命名空间和程序集整理优先发生在内部实现层，而不是具体回调入口。
4. 如果确实需要改变入口身份，应把它视为一次导入器身份迁移，明确评估和验证已有资源的重导范围。

这条规则来自导入缓存行为验证，不能由“代码已经编译”代替实际资源导入对照测试。

#### 四、处理器必须有稳定身份和语义指纹

每个可配置处理器应保存稳定 `ProcessorId`，并为当前配置生成确定性的语义指纹：

```text
ProcessorSnapshot
- processorId
- processorType
- semanticConfigHash
- enabled
- orderIndex
- matchedAssetGuids
```

语义指纹只包含会影响输出或作用范围的数据：

- 处理器类型、启用状态、Include/Exclude 规则和输出参数。
- 对象引用转换为稳定 GUID；无序集合排序后再序列化。
- 字符串路径统一分隔符和大小写策略；运行时会忽略的空字符串，指纹也必须忽略。
- 全局启用状态和处理器顺序需要进入配置快照。

以下内容不应进入语义指纹：日志开关、Inspector 展开状态、缓存/记录路径、显示文本、`ProcessorId` 本身以及其他不影响输出的界面数据。

不要使用 `string.GetHashCode()` 做持久化指纹。应构造稳定规范文本，再计算 SHA-256 或 `Hash128`。

#### 五、配置差分必须同时考虑旧范围和新范围

范围变化的核心不是“新配置现在匹配谁”，而是“哪些资源的最终输出可能与当前配置不一致”。

| 变化 | 重导目标 |
|---|---|
| 输出参数变化 | 该处理器旧范围 ∪ 新范围 |
| 新增处理器 | 新范围 |
| 删除处理器 | 旧范围 |
| 启用或禁用 | 旧范围 ∪ 新范围 |
| 全局启用状态变化 | 所有处理器旧范围 ∪ 新范围 |
| 处理器顺序变化 | 从最早变化位置起，该处理器及后续处理器的旧/新范围 |

缩小范围、禁用和删除必须重导旧范围，否则 FBX 中已经写入的 UV、法线或其他派生数据会永久残留。

范围实现还应满足：

- 最终判断统一调用处理器自己的 `ShouldProcess(assetPath)`，避免候选扫描和真实执行使用两套语义。
- `IncludePaths` 为空时，需要明确定义为“全部资源”还是“不处理”，并在候选扫描、指纹和运行时保持一致。
- 非空列表中的失效对象引用应失败关闭，不能意外退化成全项目匹配。
- 目录前缀比较必须包含目录边界，避免 `Assets/Role` 错误匹配 `Assets/RoleBackup`。
- 资源集合使用 GUID 去重，路径只作为可变的当前位置。

#### 六、输出配置必须真正进入 Unity 导入依赖

如果配置会改变导入结果，却没有进入 Unity 的导入依赖关系，就可能出现以下矛盾：

```text
Unity 看到的依赖哈希相同
实际生成的 Mesh/UV 内容不同
→ Importer Consistency 检查报告不一致
```

正确做法分两步：

1. 在资源导入开始前，以稳定的全局名称注册自定义依赖，值为处理器当前输出语义哈希。
2. 在导入上下文中，只为实际匹配该资源的处理器声明对应依赖。

自定义依赖名称是全局的，应包含工具命名空间和稳定处理器 ID，避免与其他工具冲突。`RegisterCustomDependency` 不能在 Asset Import 过程中调用，因此应在主 Editor 的配置恢复、Domain Reload 后安全入口或导入任务开始前完成注册；导入过程中只调用 `DependsOnCustomDependency`。

`AssetDatabase.GetAssetDependencyHash` 可作为资源、meta、目标平台和 Importer 版本变化的快速信号，但不能单独证明处理器已成功执行，也不能把它的每次变化都直接解释为源资源变化。实践中该聚合值还可能随脚本或导入管线状态改变；如果产品策略明确不检测代码变化，完整性检查应在依赖哈希变化时继续核对源文件 SHA-256 和独立导入设置指纹。源文件、`.meta`、目标平台、Unity 版本和处理器语义均未变时，只更新观察到的聚合值，不创建重导任务。最终正确性仍需要处理器级回执。

#### 七、处理记录是正确性证据，不只是性能缓存

推荐按资源和处理器记录实际结果：

```text
ProcessingRecordData
- version
- serializedRecordCount
- appliedConfigSnapshot
- assetRecords
- pendingImportJob

AssetRecord
- guid
- assetPath
- sourceHash
- dependencyHash
- importSettingsHash
- processorResults
- lastSuccessfulImportTime

ProcessorResult
- processorId
- semanticConfigHash
- resultStatus
- lastSuccessTime
```

资源只有同时满足以下条件才算一致：

- GUID 和当前路径有效，不在未完成任务中。
- 当前期望处理器集合与记录完全一致。
- 每个处理器的语义指纹一致，结果为成功或终止性跳过。
- 源文件、聚合依赖和导入设置指纹非空，且没有失败或缺失回执。

源文件 SHA-256 适合诊断和确认真实源变化，但读取大型 FBX 成本较高。可在新记录、依赖哈希变化或诊断时计算，而不是每次完整性检查都顺序读取全部源文件。

成功时间应表达“最近一次成功”，不能只在首次成功时写入：

- 资源级 `lastSuccessfulImportTime` 在每次完整导入成功、处理器回执和最终依赖均已确认后更新。
- 处理器级 `lastSuccessTime` 在每次 `Success` 或 `TerminalSkipped` 后更新。
- 本次失败不能伪造新的成功时间；可以保留同一处理器 ID、同一语义指纹下的上一次成功时间，但当前结果仍必须是 `Failed`。
- 处理器语义指纹已经改变时，不能把旧配置下的成功时间带入新配置的失败结果，否则时间会误导维护者认为新配置曾成功执行。

因此成功时间是诊断与恢复证据，不是“创建记录的时间”，也不是判断当前是否正常的唯一依据；当前结果状态、语义指纹、未完成任务和资源哈希仍需共同校验。

#### 八、使用两阶段提交恢复失败和中断

批量重导不能把“调用了 `ImportAsset`”当作完成。应使用可持久化的未完成任务：

```text
1. 计算目标 GUID 集合
2. 创建或合并 PendingImportJob
3. 先原子保存任务
4. 再调用 Unity 导入
5. OnPostprocessModel 汇总处理器结果
6. OnPostprocessAllAssets 获取最终依赖哈希并批量提交
7. 全部目标成功后，才提交新的配置快照并清空任务
```

处理器结果建议区分：

- `Success`：实际执行并成功。
- `TerminalSkipped`：资源没有 Mesh 或存在明确、不会靠重试改变的跳过条件。
- `Failed`：处理器异常、输出验证失败或回执不完整，必须保留待重试状态。

若启用了 Parallel Import，Import Worker 与主 Editor 不是同一进程，不能依赖静态内存共享回执。此时应把“本次导入的临时回执”和“可跨重启恢复的长期处理记录”分成两层：

| 阶段 | 临时回执职责 | 失败时的含义 |
|---|---|---|
| 开始 | 清除同路径的旧内存结果，原子写入 `pending` 临时回执文件 | 证明本次导入已经开始，但没有可靠完成结果 |
| 发布 | 后处理结束后生成处理器级结果；同进程写入内存暂存，同时把临时文件原子覆盖为 `complete` | 写入失败时不能伪造成功，主 Editor 会看到缺少有效回执 |
| 消费 | `OnPostprocessAllAssets` 优先读取同进程内存结果，跨 Worker 时读取临时文件；只接受 `complete`、资源路径匹配且处理器集合与语义指纹一致的结果 | `pending`、路径不匹配、文件损坏或处理器期望不一致都保持未完成，等待后续完整性检查补处理 |
| 清理 | 回执被消费、资源删除/移动或临时文件无效后，删除该一次性文件 | 删除失败只记录诊断，不能因此把资源标记为成功 |

临时回执文件必须消费即删除，原因不是“处理完成后不再需要缓存”，而是它本来就是一次性消息：

- 残留的 `complete` 可能在下一次同路径导入时被误认为本次成功，产生假回执。
- 残留的 `pending` 或损坏文件会把已经失效的故障现场带到后续导入判断中。
- 临时文件只负责跨进程传递，长期正确性应由资源处理记录和未完成任务承担；二者不能互相替代。
- 下一次导入开始时仍应先覆盖或清除同路径旧结果，不能假设上一次清理一定成功。

命名也应直接表达生命周期。例如内存容器使用 `InMemoryImportReceipts`，文件数据类型使用 `ImportReceiptFileData`，函数使用 `Begin`、`Publish`、`Consume`、`DeleteImportReceiptFile` 等动词。避免使用需要额外猜测的 `PendingReceipts`、`Envelope`、`Stage`，也不要把临时回执描述成长期处理记录。

Parallel Import 表示 Unity 可以同时处理多个受支持资源，但不能据此直接推断“同一资源的同一个 Artifact 会被多个 Worker 同时处理”。官方文档能够确认的是：`OutOfProcessPerQueue` 会尽可能并行处理资源，同时遵守导入器队列和依赖；资源在导入期间发生时间戳变化时，会被重新加入导入队列。官方文档没有承诺所有 Unity 版本和所有导入入口都绝不会让同一 Artifact 重叠执行，因此设计判断还需要受控实测。

在 Unity 2022.3.62f3 中，将刷新模式切换为真实 `OutOfProcessPerQueue`，对同一个已有成功记录的模型资源连续发起多次导入，并在导入期间多次改变源文件时间戳。日志显示：重复请求被合并或重新排队；当前 Artifact 因源变化失效后，后一个请求只在前一个 Artifact 完成后才开始，且由同一个 Worker 串行处理，其他 Worker 没有同时接收该资源路径。这个结果只证明当前 Unity 版本和当前导入入口的行为，不应扩张为未来版本的永久保证。

因此，当前实现可以继续让一个资源路径对应一个临时回执文件，不因未经证实的竞争假设增加导入尝试编号、同资源跨进程锁或按尝试拆分的目录。原子替换仍然必须保留，但它解决的是主 Editor 不能读取半写 JSON、跨进程只能看到完整发布结果的问题，而不是用来掩盖同一资源并发写入。如果升级 Unity、改变导入 API，或日志出现“前一个 Artifact 尚未完成，另一个 Worker 已开始处理同一路径”的证据，再扩展协议和锁设计。

主 Editor 内存中的最新回执与磁盘长期记录还存在一个提交顺序边界。典型竞态如下：

1. Import Worker 完成导入并发布完整回执。
2. 主 Editor 在资源批次回调中消费回执，更新内存记录，并把批量保存安排到稍后的编辑器更新阶段。
3. 更早排队的 Domain Reload 或配置恢复检查要求“重新从磁盘加载”。
4. 如果此时直接读取磁盘，尚未保存的新回执会被旧文件覆盖。
5. 后续完整性检查可能只刷新依赖哈希，使记录表面接近正常，但最近成功时间和处理器回执仍停留在旧值。

这不是两个线程同时修改同一静态容器造成的数据竞争，而是 Worker 进程、主 Editor、Domain Reload 和延迟持久化之间的生命周期顺序问题。安全规则是：只要内存记录处于待保存状态，任何显式磁盘重载都必须先尝试原子保存，并让当前检查继续使用最新内存状态；即使本次保存暂时失败，也不能用已知较旧的磁盘文件覆盖内存。后续任务合并、完整性检查收敛或编辑器更新应再次尝试保存。

```csharp
// 伪代码：内存中存在尚未落盘的回执时，磁盘不是更新的数据源。
if (reloadRequested && saveScheduled)
{
    TrySaveCurrentRecordsAtomically();
    reloadRequested = false;
}

EnsureRecordsReady(reloadRequested);
```

#### 九、统一使用资源批次回调作为恢复入口

五参数 `OnPostprocessAllAssets` 在资源批次完成后调用，并通过 `didDomainReload` 表明是否发生 Domain Reload。推荐把它作为统一协调入口：

- imported：完成回执并提交最终依赖哈希。
- moved：按 GUID 更新路径，并检查移动前后的作用范围。
- deleted：清理处理记录和未完成任务目标。
- 配置资产变化：执行处理器级语义差分。
- `didDomainReload == true`：恢复未完成任务并执行完整性检查。

回调只负责入队，实际重导放到 `EditorApplication.delayCall`：

- 同一 GUID 多次入队只保留一次。
- 新请求与当前未完成任务合并。
- 执行导入时设置重入保护。
- 不无条件调用 `AssetDatabase.Refresh()`。

官方文档提醒：在 `OnPostprocessAllAssets` 中触发新导入会再次调用该回调。没有去重、任务状态和延迟执行时，很容易形成递归重导循环。

#### 十、不要把代码错误等同于“Unity 正在编译”

资源进入项目时可能存在 C# 错误，但 Unity 可能仍在运行上一次成功编译的 Editor 程序集。也可能因为 Domain Reload、配置类型暂不可用或导入回调未加载而没有执行最新处理逻辑。

因此补偿机制不能只检查 `isCompiling`：

- 只有可靠处理器回执才能提交成功记录。
- 配置无法加载时不提交成功。
- 代码恢复并发生 Domain Reload 后，统一执行完整性检查。
- 当前范围、历史范围或未完成任务中缺少成功证据的资源应补导。

这能覆盖“错误期间资源已进入项目，之后修复代码”的场景，而不需要推测当时 Unity 是否处于编译状态。

#### 十一、持久化文件必须验证结构，而不只是 JSON 可解析

`JsonUtility.FromJson` 成功不代表数据完整。类似 `{"version":3}` 的截断文件仍可能生成一个看似合法的空对象。

加载时至少检查：

- 记录数组存在，保存的数量摘要与实际数量一致。
- 资源 GUID 非空且唯一，处理器结果不重复。
- 配置快照结构完整，处理器 ID 和顺序有效。
- 未完成任务的完成、失败集合都是目标集合的子集，且不能互相冲突。
- 空哈希不能作为有效一致状态。

保存建议使用：临时文件写入 → 原子替换主文件 → 保留 `.bak`。不要先删除主文件再移动临时文件。

恢复顺序：

1. 主文件有效则加载。
2. 主文件无效则尝试备份。
3. 主备都无效时，因历史范围不可恢复，只能进入项目级保守重建。
4. 旧版本迁移时先保留全部历史 GUID，再与当前范围合并，禁止迁移前清空旧记录。

#### 十二、菜单语义必须与恢复模型一致

- “检测并处理”：只补导当前不一致的资源。
- “强制全量重导”：目标为历史 GUID 与当前作用范围并集；先保存未完成任务，不能先清空记录。
- “重建处理记录”：必须明确执行项目内全部目标资源的真实重导，不能只是删除 JSON。

如果代码变化不自动检测，应在“强制全量重导”的说明中明确：是否需要重导由开发者判断。

#### 十三、可复用验证方法

输出型导入工具不能只验证日志。推荐使用隔离资源和可数值确认的输出：

1. 使用 DCC 或程序生成两个拓扑/尺寸明确不同的 FBX 版本。
2. 临时处理器只匹配唯一隔离目录，把固定值写入高编号 UV 通道。
3. 同时记录目标 GUID、导入次数、顶点数、UV 数量、源哈希、依赖哈希和处理器结果。
4. 覆盖以下场景：代码变化、非输出配置、范围扩大/缩小、禁用/删除、源文件覆盖、单条记录缺失、真实失败、Domain Reload、配置不可用、代码错误、主备损坏和 Inspector 打开。
5. 所有临时配置、失败注入和记录损坏都使用 `try/finally` 恢复。
6. 项目级全量重导、主备都损坏后的真实重建和关闭整个 Unity 进程，应在副本项目执行或单独取得授权。

Parallel Import 的验证还应覆盖“Worker 导入与 Domain Reload 检查处于同一事件链”的场景：选择已有成功记录的少量资源，连续执行普通 Worker 导入和带 Domain Reload 的 Worker 导入，确认资源级与每个处理器级最近成功时间均逐次前进、结果状态保持一致、未完成任务清空、一次性回执目录为空。只看到 Worker 日志或 `ImportAsset` 返回不足以证明主 Editor 已正确提交结果。

验证同一资源是否存在 Worker 竞争时，应对同一路径连续发起多次导入，并在导入期间改变源文件时间戳以强制产生重新排队条件，然后联合检查所有 Worker 日志。只有在前一个 Artifact 尚未完成时，另一个 Worker 已开始处理同一路径，才算发现真实重叠；请求数量大于实际 Artifact 数量、同一 Worker 的顺序执行或导入失效后的后续重排都不属于并发写入证据。

测试结束必须确认：配置恢复、临时类型和资产清理、无未完成任务、主备结构有效、处理器集合和指纹一致、没有新增编译或 Inspector 错误。

#### 十四、常见反模式

| 反模式 | 后果 | 替代设计 |
|---|---|---|
| 动态源码哈希覆写 `GetVersion()` | 无关代码变化造成大范围重导 | 显式版本或人工全量重导 |
| 原始配置文件整体哈希 | 日志/排版变化也触发重导 | 处理器级语义指纹 |
| 只扫描新范围 | 缩小、禁用、删除后旧输出残留 | 旧范围 ∪ 新范围 |
| 配置影响输出但未声明依赖 | 相同依赖生成不同 Artifact | 注册并声明自定义依赖 |
| ImportAsset 返回就算成功 | Worker 失败或回执缺失被误报完成 | 两阶段提交 + 最终回执 |
| JSON 可解析就接受 | 截断记录被当作空的正常状态 | 结构、数量和集合关系校验 |
| 清空记录后再全量导入 | 部分失败时丢失历史范围 | 先保存未完成任务，成功后覆盖 |
| 回调内立即递归重导 | 重复导入或刷新循环 | 入队、去重、delayCall、重入保护 |
| 只看 `isCompiling` 判断遗漏 | 代码错误与实际程序集状态被混淆 | 以成功回执和 Domain Reload 审计为准 |
| 依赖哈希一变就补导 | 普通脚本重载可能间接恢复代码变化检测 | 再核对源文件与独立导入设置指纹 |
| 代码整理时直接改变具体 `AssetPostprocessor` 完整类型名 | 可能触发已有资源迁移性重导 | 保留稳定具体回调入口，只移动内部实现；入口变化时单独验证重导范围 |
| Parallel Import 只用静态字典传结果 | Import Worker 与主 Editor 不共享内存，主进程收不到可靠回执 | 同进程内存快速通道 + 跨进程原子临时回执文件 |
| 未调查调度语义就为同一资源增加导入尝试编号和跨进程锁 | 协议复杂度、锁恢复和故障面在没有竞争证据时被扩大 | 先核对官方队列语义并做同路径重复请求与导入中变化测试；只在出现真实重叠证据后扩展协议 |
| 已消费的临时回执文件继续保留 | 后续同路径导入可能误用旧成功结果 | 校验后消费即删除；长期状态只写入处理记录 |
| 内存回执待保存时仍强制重载磁盘 | 旧磁盘记录覆盖本次成功结果，出现两次导入记录不一致 | 先原子保存并保留最新内存状态，后续安全入口重试持久化 |
| 成功时间只写一次或失败时清零 | 无法判断最近一次真实成功；历史成功证据被破坏 | 每次成功更新；失败只保留同语义下的历史时间且状态仍为失败 |

### 关键代码

以下代码只表达职责边界，具体命名和序列化结构应按项目实现：

```csharp
// 必须在导入开始前注册；名称全局唯一，值只包含输出语义。
static void RegisterProcessorDependency(string processorId, string semanticHash)
{
    string key = $"com.example.asset-processing/{processorId}";
    AssetDatabase.RegisterCustomDependency(key, Hash128.Compute(semanticHash));
}

// 导入期间只为实际匹配的处理器声明依赖。
void OnPreprocessModel()
{
    foreach (var processor in GetMatchingProcessors(assetPath))
    {
        context.DependsOnCustomDependency(
            $"com.example.asset-processing/{processor.ProcessorId}");
    }
}
```

```csharp
// 批次回调只协调状态；真实重导延迟执行，避免递归。
static void OnPostprocessAllAssets(
    string[] imported,
    string[] deleted,
    string[] moved,
    string[] movedFrom,
    bool didDomainReload)
{
    CompleteImportReceipts(imported);
    UpdateMovedAssets(moved, movedFrom);
    RemoveDeletedAssets(deleted);

    if (didDomainReload)
        QueueIntegrityAudit();

    ScheduleDelayedImportIfNeeded();
}
```

### 参考链接

- [Unity AssetPostprocessor.GetVersion](https://docs.unity3d.com/2022.3/Documentation/ScriptReference/AssetPostprocessor.GetVersion.html) - 版本变化与相关资源重导语义。
- [Unity AssetDatabase.RegisterCustomDependency](https://docs.unity3d.com/cn/2022.1/ScriptReference/AssetDatabase.RegisterCustomDependency.html) - 注册全局自定义依赖及禁止在导入过程中调用的限制。
- [Unity AssetImportContext.DependsOnCustomDependency](https://docs.unity3d.com/cn/2021.3/ScriptReference/AssetImporters.AssetImportContext.DependsOnCustomDependency.html) - 在导入上下文中声明自定义依赖。
- [Unity AssetPostprocessor.OnPostprocessAllAssets](https://docs.unity.cn/ScriptReference/AssetPostprocessor.OnPostprocessAllAssets.html) - 五参数资源批次回调、Domain Reload 和再次导入行为。
- [Unity AssetDatabase.GetAssetDependencyHash](https://docs.unity3d.com/2022.3/Documentation/ScriptReference/AssetDatabase.GetAssetDependencyHash.html) - 聚合依赖哈希的组成和用途。
- [Unity Parallel importing](https://docs.unity3d.com/2022.3/Documentation/Manual/ParallelImport.html) - 支持并行导入的资源类型、Worker 设置和并行导入器的确定性要求。
- [Unity Refreshing the Asset Database](https://docs.unity.cn/Manual/AssetDatabaseRefreshing.html) - Asset Database 刷新循环和可能重新启动导入的条件。

### 相关记录

- [Unity 编辑器资源导入工具架构（配置驱动 + AssetPostprocessor 自动化）](./unity-asset-import-tool-architecture.md) - 侧重 Importer 参数配置、文件夹规则和编辑器界面；本记录补充输出型后处理器的正确性、依赖和恢复设计。

### 验证记录

- [2026-07-21] 初次记录。通过 Unity 2022.3 LTS、真实 FBX 源文件变化和隔离处理器验证代码变化策略、语义配置差分、范围扩大/缩小/删除、Unity 自定义依赖、单条记录补偿、失败与 Domain Reload 恢复、配置暂不可用、代码错误、主备结构损坏和 Inspector 打开等场景；同时使用 Unity 官方 API 文档复核关键生命周期与调用限制。
- [2026-07-21] 补充验证。确认 Unity 聚合依赖哈希变化不能单独作为自动补导依据；增加源文件与导入设置指纹的二次判定。
- [2026-07-21] 补充具体后处理器身份验证。使用隔离 Unity 项目对比“直接改变具体 `AssetPostprocessor` 完整类型名”“保留稳定入口并转发到新实现”和“真实修改模型资源”三种情况，确认稳定薄入口可以避免代码整理本身造成迁移性重导，同时保持正常回调执行。
- [2026-07-22] 补充 Parallel Import 回执生命周期。通过 Unity 2022.3 LTS 主 Editor 与两个 Asset Import Worker 验证：脚本刷新和 Domain Reload 后无编译失败、无意外 FBX 重导、无回执读写错误；长期处理记录无失败/未完成任务，临时回执目录为空。同步明确 pending/complete、原子发布、严格消费和消费即删除的职责边界，并完成敏感信息泛化。
- [2026-07-22] 补充最近成功时间和延迟持久化顺序。通过 Unity 2022.3 LTS 的实际 Import Worker 子进程，使用两个已有成功记录的测试 FBX 连续验证普通导入、Domain Reload 后导入与修复后回归：三个匹配处理器及资源级最近成功时间均在每次成功后前进，失败不会伪造成功；临时回执全部消费，无新增编译、回执或保存错误。复现并修复了主 Editor 已消费回执但尚未落盘时，延迟检查从旧磁盘文件重载并覆盖内存结果的问题。
- [2026-07-22] 补充同一资源的 Import Worker 调度调查。Unity 2022.3.62f3 的真实 `OutOfProcessPerQueue` 测试中，对同一路径重复请求并在导入期间改变源文件时间戳，观察到当前 Artifact 失效后串行重排，未观察到多个 Worker 同时处理同一路径。结合官方“遵守导入队列与依赖”和“导入中源时间戳变化会重新入队”的说明，当前不增加导入尝试编号或同资源跨进程锁；该结论限定于已验证版本和入口，升级或出现重叠日志证据时重新评估。

---

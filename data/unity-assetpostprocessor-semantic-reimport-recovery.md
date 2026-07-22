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

#### 三、处理器必须有稳定身份和语义指纹

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

#### 四、配置差分必须同时考虑旧范围和新范围

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

#### 五、输出配置必须真正进入 Unity 导入依赖

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

#### 六、处理记录是正确性证据，不只是性能缓存

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

#### 七、命名空间迁移要区分序列化类型和 Unity 回调类型

`[SerializeReference]` 会把 managed-reference 的 ID、完整类型名和字段值写入宿主资产。配置、处理器或枚举改命名空间时，应使用 `MovedFrom` 描述旧命名空间、程序集和类型名，并用 `SerializationUtility.HasManagedReferencesWithMissingTypes` 验证旧配置副本。迁移成功至少应确认：

- 旧配置和当前配置都能加载，缺失 managed-reference 为 0。
- 处理器数量、稳定 ID 和输出参数保持不变。
- 旧配置与当前配置的语义指纹相同。
- 持久化快照中的旧类型名只迁移元数据，不因此创建重导任务。

具体 `AssetPostprocessor` 类型需要单独处理。Unity 官方的 `MovedFrom` 说明面向 API/序列化类型迁移，并不保证维持 Asset Import Pipeline 对具体后处理器类型的缓存身份。Unity 2022.3 隔离对照测试表明：直接改变具体后处理器完整类型名，即使添加 `MovedFrom`，仍会使测试 FBX 重导；保持原具体类型名，把业务实现继承或转发到新命名空间时，代码变化不导入 FBX，真实修改 FBX 后回调仍会执行。

因此安全迁移方式是：

1. 配置、处理器、扩展接口和实际实现迁移到新命名空间。
2. 仅保留 Unity 扫描所需的旧完整名具体回调作为薄兼容入口。
3. 兼容入口不承载配置或业务逻辑，只继承新实现或转发静态处理函数。
4. 用隔离项目分别验证“直接移动”“稳定入口 + 新实现”和真实资源变化，不能仅凭编译成功判断没有触发模型缓存重建。

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
| 直接移动具体后处理器并只加 `MovedFrom` | Unity 原生模型缓存可能整体失效 | 保留稳定具体回调类型名，转发或继承新实现 |
| Parallel Import 只用静态字典传结果 | Import Worker 与主 Editor 不共享内存，主进程收不到可靠回执 | 同进程内存快速通道 + 跨进程原子临时回执文件 |
| 已消费的临时回执文件继续保留 | 后续同路径导入可能误用旧成功结果 | 校验后消费即删除；长期状态只写入处理记录 |

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
- [Unity SerializeReference](https://docs.unity3d.com/2022.3/Documentation/ScriptReference/SerializeReference.html) - managed-reference 的完整类型名与缺失类型语义。
- [Unity SerializationUtility.HasManagedReferencesWithMissingTypes](https://docs.unity3d.com/2022.3/Documentation/ScriptReference/SerializationUtility.HasManagedReferencesWithMissingTypes.html) - 检查宿主资产是否含无法解析的 managed-reference。
- [Unity MovedFromAttribute](https://docs.unity3d.com/2022.3/Documentation/ScriptReference/Scripting.APIUpdating.MovedFromAttribute.html) - 描述类型原有命名空间、程序集和类型名。
- [Unity Refreshing the Asset Database](https://docs.unity.cn/Manual/AssetDatabaseRefreshing.html) - Asset Database 刷新循环和可能重新启动导入的条件。

### 相关记录

- [Unity 编辑器资源导入工具架构（配置驱动 + AssetPostprocessor 自动化）](./unity-asset-import-tool-architecture.md) - 侧重 Importer 参数配置、文件夹规则和编辑器界面；本记录补充输出型后处理器的正确性、依赖和恢复设计。

### 验证记录

- [2026-07-21] 初次记录。通过 Unity 2022.3 LTS、真实 FBX 源文件变化和隔离处理器验证代码变化策略、语义配置差分、范围扩大/缩小/删除、Unity 自定义依赖、单条记录补偿、失败与 Domain Reload 恢复、配置暂不可用、代码错误、主备结构损坏和 Inspector 打开等场景；同时使用 Unity 官方 API 文档复核关键生命周期与调用限制。
- [2026-07-21] 补充验证。确认 Unity 聚合依赖哈希变化不能单独作为自动补导依据；增加源文件与导入设置指纹的二次判定。使用隔离 Unity 项目对比具体 `AssetPostprocessor` 直接迁移、稳定旧入口转发/继承新实现和真实资源变化，确认 `MovedFrom` 能恢复旧 managed-reference，但不能替代后处理器缓存身份的稳定入口。
- [2026-07-22] 补充 Parallel Import 回执生命周期。通过 Unity 2022.3 LTS 主 Editor 与两个 Asset Import Worker 验证：脚本刷新和 Domain Reload 后无编译失败、无意外 FBX 重导、无回执读写错误；长期处理记录无失败/未完成任务，临时回执目录为空。同步明确 pending/complete、原子发布、严格消费和消费即删除的职责边界，并完成敏感信息泛化。

---

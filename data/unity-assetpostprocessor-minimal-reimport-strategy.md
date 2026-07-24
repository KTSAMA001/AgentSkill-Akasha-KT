# Unity 输出型 AssetPostprocessor 的最小重导策略

**标签**：#unity #fbx #custom-editor #architecture
**来源**：实践复盘 - Unity 2022.3 LTS 项目改造、隔离资源验证与 Unity 官方文档复核
**收录日期**：2026-07-24
**来源日期**：2026-07-24
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐（Unity 2022.3 LTS 实践验证 + Unity 官方 API 文档复核）
**适用版本**：Unity 2021.2+；实践验证版本为 Unity 2022.3 LTS

### 概要

输出型 `AssetPostprocessor` 不应默认建立一套平行于 Unity Asset Pipeline 的资源状态监控系统。普通资源新增、内容修改、`.meta` 或 Importer 变化由 Unity 自己触发导入；工具只需要补足 Unity 无法自动推导的两类关系：外部配置如何影响导入 Artifact，以及配置作用范围改变后哪些旧资源需要清理历史输出。默认方案是“语义配置依赖 + 旧/新范围差分 + 出入范围移动重导 + 人工强制全量重导”，逐资源成功记录、跨进程回执和 Domain Reload 完整性审计只在业务确实要求自动证明与恢复漏处理时采用。

### 内容

#### 一、先划清 Unity 与工具各自负责的变化

| 变化来源 | 默认负责者 | 工具需要补充的行为 |
|---|---|---|
| FBX 新增或内容变化 | Unity Asset Pipeline | 正常执行后处理器，不重复监控源文件哈希 |
| `.meta`、Importer、平台或导入器依赖变化 | Unity Asset Pipeline | 正常执行后处理器，不另建依赖哈希巡检 |
| 会影响输出的外部配置变化 | 工具 | 注册语义自定义依赖，并按旧/新作用范围重导 |
| 资源移动后进入或离开处理范围 | Unity + 工具 | 比较移动前后的匹配处理器集合，只补充范围转换重导 |
| 处理器代码变化 | 开发者策略 | 默认人工判断后使用强制全量重导；不要扫描源码自动计算版本 |
| 偶发代码/配置不可用期间可能漏处理 | 产品策略 | 默认由人工全量重导兜底；只有明确要求自动恢复时才升级机制 |

这个边界避免重复实现 Unity 已有的资源变化检测。工具的持久化数据也不再承担“证明每个资源最后一次成功”的职责，只保存配置差分必须知道、而 Unity 不会替工具保存的历史范围。

#### 二、默认最小闭环

推荐默认实现以下四项：

1. 为每个处理器保存稳定 ID，并计算只包含输出语义的确定性指纹。
2. 保存最后一次已应用的配置快照及各处理器匹配过的资源 GUID，用于配置变化时找回旧范围。
3. 资源移动时比较旧路径和新路径匹配的处理器集合，仅在进入或离开范围时补充重导。
4. 提供人工“强制全量重导”，处理代码变化和罕见异常恢复。

最小状态示例：

```text
AppliedConfigState
- globalEnabled
- processors

ProcessorSnapshot
- processorId
- processorType
- semanticConfigHash
- orderIndex
- matchedAssetGuids
```

这里没有逐资源成功状态、源文件哈希、依赖哈希、最近成功时间、未完成任务或跨进程回执。它的目标是完成配置范围差分，不是替代 Unity 的资源数据库。

#### 三、配置变化必须重导旧范围与新范围

配置差分仍然是必要机制，因为 Unity 不知道“一个外部配置处理器以前作用于哪些资源”。

| 配置变化 | 重导目标 |
|---|---|
| 参数变化 | 该处理器旧范围 ∪ 新范围 |
| 新增处理器 | 新范围 |
| 删除处理器 | 旧范围 |
| 启用或禁用 | 旧范围 ∪ 新范围 |
| 全局启用状态变化 | 所有处理器旧范围 ∪ 新范围 |
| 处理器顺序变化 | 从最早变化位置起，相关处理器的旧/新范围 |

缩小范围、禁用或删除处理器时，旧范围必须重导，才能清除已经写入 Mesh、UV、法线等 Artifact 的历史处理结果。范围集合使用 GUID 保存，路径仅作为当前可变位置。

范围实现应满足：

- 候选扫描和真实执行最终统一调用处理器的 `ShouldProcess(assetPath)`。
- `IncludePaths` 为空的含义必须固定，并在扫描、指纹和执行阶段一致。
- 目录前缀比较包含边界，避免相似目录名误匹配。
- 对象引用先转为 GUID，无序集合排序后再参与指纹。
- 日志开关、界面折叠状态、记录位置等非输出字段不得进入语义指纹。

#### 四、资源移动只处理“范围集合发生变化”

移动事件不需要发展成全资源监控。对同一 GUID，分别计算旧路径和新路径匹配的处理器 ID 集合：

```text
oldProcessors == newProcessors  → 不补充重导
oldProcessors != newProcessors  → 重导移动后的资源
```

从范围内移出时也必须重导，因为新路径下需要以当前匹配集合重新生成 Artifact，清除旧处理结果。仅路径改变但匹配集合相同时，交给 Unity 正常处理即可。

#### 五、外部输出配置必须声明为 Unity 导入依赖

如果同一个源资源和同一组 Unity 已知依赖，在不同外部配置下生成不同输出，Importer Consistency 检查可能得到不一致 Artifact。正确做法是：

1. 在资源导入开始前，用稳定且全局唯一的名称注册处理器语义哈希。
2. 导入过程中，只为实际匹配资源的处理器声明对应自定义依赖。

```csharp
// 注册发生在导入过程之外；值只代表会影响输出的配置语义。
AssetDatabase.RegisterCustomDependency(
    $"com.example.asset-processing/{processorId}",
    Hash128.Compute(semanticConfigHash));

// 导入时只声明当前资源实际依赖的处理器配置。
context.DependsOnCustomDependency(
    $"com.example.asset-processing/{processorId}");
```

自定义依赖解决的是“配置属于 Artifact 输入”的问题，不是资源状态监控，也不能替代旧范围差分。

#### 六、`GetVersion()` 只用于显式导入算法版本

`AssetPostprocessor.GetVersion()` 变化会使 Unity 把相关资源视为需要重新导入。它适合开发者明确维护导入算法版本的场景，不适合动态扫描源码生成版本：

- 注释、空白、辅助代码和文件顺序可能造成无意义重导。
- 全局代码哈希不能表达具体处理器和作用范围。
- 编译失败时，磁盘源码与 Unity 当前运行的最后一次有效程序集可能不同。

如果团队接受“代码变化由开发者判断”，可以直接不覆写 `GetVersion()`，并在必要时人工强制全量重导。

#### 七、Parallel Import 不等于必须自建磁盘回执

Import Worker 与主 Editor 是不同进程，静态内存不能跨进程共享，这是已验证的机制事实。但它只说明“跨进程共享自定义结果时不能依赖静态字段”，并不推出每个 AssetPostprocessor 工具都必须创建 JSON 回执。

只有同时满足以下条件时，才考虑临时磁盘回执：

- 主 Editor 必须得到处理器级结果，而 Unity 提供的导入完成边界和导入日志无法满足需求。
- 产品要求中断、重启或代码/配置不可用后自动恢复，并能证明没有漏处理。
- 已经复现了缺少跨进程数据会导致实际错误，而不是只基于并行导入的可能性推演风险。

如果当前目标只是同步发起重导、等待该调用完成并检查 Unity 导入日志，就不需要再维护 `pending/complete` 文件、消费删除协议、最近成功时间和长期逐资源记录。不要因为 Import Worker 存在，就预先实现一套消息协议。

#### 八、强恢复方案是可选层，不是默认层

以下机制本身可以成立，但只服务于“自动证明并恢复漏处理”的强保证：

- 逐资源、逐处理器成功结果和最近成功时间。
- 可持久化未完成任务与两阶段提交。
- Import Worker 到主 Editor 的临时回执。
- Domain Reload 后完整性审计。
- 主备记录文件、损坏恢复和项目级保守重建。
- 源文件、聚合依赖和独立导入设置指纹的交叉核对。

采用前应满足一组明确门槛：

1. 业务确实要求全自动恢复，而人工全量重导不可接受。
2. 已有可复现的漏处理故障，且 Unity 原生导入与自定义依赖不能覆盖。
3. 能承担持久化协议、迁移、损坏恢复、跨进程生命周期和长期回归测试成本。
4. 收益可以量化，例如避免高频生产事故，而不是仅追求理论上的“绝不遗漏”。

达不到这些门槛时，应停在最小闭环。强恢复设计不是更严谨的天然终点，它只是更高成本、适用范围更窄的产品选择。

#### 九、语义指纹格式本身是持久化协议

只要语义指纹会保存到配置快照或注册为自定义依赖，生成它的规范文本格式就属于兼容协议。即使字段语义没变，改变分隔符、空白、排序或空值写法也会得到新哈希，可能触发大范围迁移性重导。

实践中曾因整理规范文本时遗漏原格式中的尾随空格，使数百个模型被误判为配置变化并重导。修复原则是：

- 不随意整理已持久化的规范文本格式。
- 必须改变时增加格式版本或兼容旧哈希的迁移路径。
- 先用少量隔离资源验证当前哈希与已应用哈希，再在主项目启用变化检测。

这类兼容性问题与哈希算法强度无关；SHA-256 也无法弥补输入规范不稳定。

#### 十、验证范围应围绕实际职责

最小方案至少验证：

1. 新增或修改 FBX 时，只由 Unity 正常导入一次并执行匹配处理器。
2. 修改非输出配置时，语义指纹不变且不重导。
3. 参数变化、范围扩大/缩小、禁用和删除处理器时，目标等于旧范围与新范围的正确并集。
4. 资源在范围内外移动时，只在匹配处理器集合变化时补充重导。
5. 配置变化后 Unity 自定义依赖更新，Importer Consistency 不再出现相同依赖生成不同输出。
6. 修改处理器代码但不修改配置时，工具不主动重导；人工强制全量重导可用。
7. Parallel Import 开启时，不产生工具自建回执文件，也不依赖跨进程静态状态。
8. 配置快照格式兼容，普通脚本刷新或 Domain Reload 不产生意外全量重导。

测试应使用隔离目录和可数值确认的 Mesh/UV 输出，并区分其他导入工具触发的连带导入，不能把项目中所有导入日志都归因于当前工具。

#### 十一、常见目标偏移

| 目标偏移 | 实际代价 | 更合适的处理 |
|---|---|---|
| 重新监控 FBX、meta 和 Importer 变化 | 重复 Unity Asset Pipeline，增加误判和维护成本 | 依赖 Unity 正常导入 |
| 默认保存每个资源最近成功时间 | 需要定义成功、失败、迁移和并发提交语义 | 没有诊断或恢复需求时不保存 |
| 因存在 Import Worker 就设计磁盘消息协议 | 增加临时文件、原子替换、消费和损坏处理 | 先确认是否真的需要跨进程自定义结果 |
| Domain Reload 后默认全项目完整性审计 | 编辑器启动成本和误重导风险上升 | 罕见异常由人工全量重导兜底 |
| 为所有理论中断设计未完成任务 | 状态机和恢复路径成为主要复杂度 | 只有严格自动恢复要求时采用 |
| 把 GetAssetDependencyHash 当成功证明 | 聚合变化不代表后处理器成功 | 默认无需二次证明；强恢复方案另行设计 |
| 修改持久化指纹的空白或排序 | 无语义变化却触发迁移性重导 | 版本化规范格式或兼容旧哈希 |

### 关键代码

```csharp
// 移动后只有处理器集合发生变化，才补充一次重导。
HashSet<string> oldSet = GetMatchingProcessorIds(movedFromPath);
HashSet<string> newSet = GetMatchingProcessorIds(movedPath);

if (!oldSet.SetEquals(newSet))
{
    QueueReimport(assetGuid);
}
```

```csharp
// 配置状态只保存差分所需的稳定身份、语义和历史范围。
[Serializable]
sealed class ProcessorSnapshot
{
    public string processorId;
    public string processorType;
    public string semanticConfigHash;
    public int orderIndex;
    public List<string> matchedAssetGuids;
}
```

### 参考链接

- [Unity AssetPostprocessor](https://docs.unity3d.com/ScriptReference/AssetPostprocessor.html) - 资源导入前后处理入口。
- [Unity AssetPostprocessor.GetVersion](https://docs.unity3d.com/2022.3/Documentation/ScriptReference/AssetPostprocessor.GetVersion.html) - 显式版本变化与资源重导语义。
- [Unity AssetDatabase.RegisterCustomDependency](https://docs.unity3d.com/2022.3/Documentation/ScriptReference/AssetDatabase.RegisterCustomDependency.html) - 注册外部自定义依赖。
- [Unity AssetImportContext.DependsOnCustomDependency](https://docs.unity3d.com/2022.3/Documentation/ScriptReference/AssetImporters.AssetImportContext.DependsOnCustomDependency.html) - 在导入上下文中声明自定义依赖。
- [Unity AssetPostprocessor.OnPostprocessAllAssets](https://docs.unity3d.com/2022.3/Documentation/ScriptReference/AssetPostprocessor.OnPostprocessAllAssets.html) - 资源批次与移动回调。
- [Unity Parallel importing](https://docs.unity3d.com/2022.3/Documentation/Manual/ParallelImport.html) - Import Worker 与并行导入边界。

### 相关记录

- [Unity 编辑器资源导入工具架构（配置驱动 + AssetPostprocessor 自动化）](./unity-asset-import-tool-architecture.md) - 配置驱动工具的基本分层、范围规则和编辑器入口。
- [历史方案：Unity 输出型 AssetPostprocessor 的强恢复重导设计](./unity-assetpostprocessor-semantic-reimport-recovery.md) - 保留已验证机制与曾采用的强恢复方案；该方案不再作为默认架构。

### 验证记录

- [2026-07-24] 初次记录。基于 Unity 2022.3 LTS 中一个配置驱动的输出型 FBX 后处理工具完成从强恢复机制到最小闭环的重构：移除逐资源状态监控、源/依赖哈希审计、未完成任务、Worker 临时回执和 Domain Reload 完整性检查；保留语义配置快照、旧/新范围差分、范围进出移动处理、自定义依赖与人工强制全量重导。验证普通资源导入、配置哈希一致性、隔离模型重导、无旧记录继续写入、无临时回执生成及无 Importer Consistency 新错误。
- [2026-07-24] 兼容性补充。复现语义指纹规范文本的尾随空格变化导致数百个模型发生迁移性重导，恢复旧格式并增加兼容处理后，当前与已应用指纹一致，脚本刷新不再触发配置批量重导。由此确认指纹规范格式必须按持久化协议维护。

---

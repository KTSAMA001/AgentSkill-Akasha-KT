# Unity 编辑器资源导入工具架构（配置驱动 + AssetPostprocessor 自动化）

**标签**：#unity #custom-editor #tools #architecture #scriptable-object #fbx #texture
**来源**：实地代码分析
**收录日期**：2026-03-31
**更新日期**：2026-07-24
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐（实地分析）
**适用版本**：Unity 2021+

### 概要
基于 ScriptableObject 配置驱动 + AssetPostprocessor 自动执行的资源导入管理框架。模型使用可叠加规则队列与唯一最终目标，纹理保留文件夹最长匹配；两者共享顶层处理范围、批次配置快照、单资源豁免、移动检查和编辑器可视化。模型导入还可在基础设置之后运行可扩展的跨资源关系阶段，用于 Avatar 提供者与消费者等依赖。

### 内容

#### 1. 整体架构

采用**配置 SO + Processor 处理器 + PostProcessor 自动触发**三层架构。模型与纹理共享安全边界和配置生命周期，但匹配与合并语义不同；模型另外包含跨资源关系扩展：

```
┌─────────────────────────────────────────────────────┐
│                   Odin 窗口入口                       │
│  OdinMenuEditorWindow 加载两个配置 SO 到菜单树         │
└─────────────┬───────────────────────┬───────────────┘
              │                       │
     ModelImportOdinGUI        TextureImportOdinGUI
     (SerializedScriptableObject)                     
              │                       │
     ModelImportProcessor      TextureImportProcessor
     (规则合并与最终目标)       (文件夹最长匹配)
              │                       │
     ModelPostProcessor        TexturePostProcessor
     (AssetPostprocessor)      (AssetPostprocessor)
              │                       │
     ModelMoveProcessor        TextureMoveProcessor
     (最终语义比较)             (配置匹配比较)
              │
     IAssetRelationProcessor → AssetRelationProcessingQueue
     (模块外关系扩展)           (分阶段导入与完成验证)
```

#### 2. 配置层设计

配置 SO 继承 `SerializedScriptableObject`（Odin），公共核心字段包括：

- `AutoSetXxxImportSettings`：全局自动处理开关
- `processFolders`：限定处理范围的文件夹列表
- 模型：`List<ModelImportRule>` 规则队列。每条规则包含名称、启用状态、整数队列值、文件夹/子目录与文件名后缀条件，以及逐字段模型设置覆盖项。
- 纹理：继续使用文件夹特定设置列表和最长目录匹配。
- 模型资源关系：与模型规则保存在同一配置中，使用 `SerializeReference` 保存模块外处理器实例。

**每项设置独立启用开关**：每个导入参数都有 `enableXxxConfig` 布尔开关，未启用的项不会被强制覆盖。这样可以实现"只管我关心的设置，其余不干预"。

```csharp
// 示例：模型设置中的独立开关模式
[ToggleLeft][LabelText("启用网格压缩配置")] public bool enableMeshCompressionConfig = false;
[ShowIf("enableMeshCompressionConfig")] public ModelImporterMeshCompression meshCompression;

[ToggleLeft][LabelText("启用法线导入模式配置")] public bool enableImportNormalsConfig = false;
[ShowIf("enableImportNormalsConfig")] public ModelImporterNormals importNormals;
```

#### 3. 模型规则合并与纹理最长路径匹配

模型会收集资源命中的全部规则，按队列值升序、配置列表顺序升序合并；每个设置开关只决定当前规则是否覆盖对应字段，未启用字段继承此前结果。同队列同字段由列表后项生效，并形成可诊断冲突。合并后生成唯一只读最终目标，自动导入、批量应用、Inspector、Project 标记和移动比较共用该结果。

纹理仍使用**最长路径前缀匹配**选择最具体的单条文件夹配置：

```csharp
public static PathFolderSpecificSettings FindMatchingFolderConfig(
    string assetPath, List<PathFolderSpecificSettings> folderSettings)
{
    string normalizedPath = assetPath.Replace('\\', '/');
    return folderSettings
        .Where(s => !string.IsNullOrEmpty(s.folderPath))
        .Select(s => new {
            Setting = s,
            FolderPath = s.folderPath.Replace('\\', '/').TrimEnd('/') + "/"
        })
        .Where(item => normalizedPath.StartsWith(item.FolderPath))
        .OrderByDescending(item => item.FolderPath.Length)
        .FirstOrDefault()?.Setting;
}
```

#### 4. 豁免机制（Exemption）

通过 Unity Asset Labels（meta 文件的 `labels` 字段）存储豁免标记，格式为 `XxxImportExempt:Key`：

- **存储**：写在 `.meta` 文件的 labels 中，不污染资源本身
- **读取**：处理时解析 meta 文件提取豁免项集合
- **检查**：每个设置项应用前先检查 `exemptOptions.Contains("Key")`
- **管理**：在 Inspector 中通过自定义 GUI 添加/移除，支持单选和多选

```csharp
// 豁免检查示例
if (!exemptOptions.Contains("MeshCompression") 
    && settings.enableMeshCompressionConfig 
    && importer.meshCompression != settings.meshCompression)
{
    importer.meshCompression = settings.meshCompression;
    hasChanges = true;
}
```

Inspector 豁免 GUI 通过 `Editor.finishedDefaultHeaderGUI` 钩入，在原生 Importer Inspector 下方绘制，无需自定义 Editor 替换原有界面。

#### 5. 自动触发链

```
资源导入 ──→ PostProcessor.OnPreprocessModel/Texture
              │  批次开始读取一次最新配置
              │  检查 AutoSet 开关 + processFolders 范围
              │  模型解析唯一最终目标，纹理选择最长目录配置
              │  模型基础设置完成后应用资源关系字段
              │
资源移动 ──→ MoveProcessor.OnPostprocessAllAssets
              │  模型比较新旧最终语义，纹理比较匹配配置
              │  仅在输出目标变化时补充 reimport
              │
手动按钮 ──→ OdinGUI."应用导入设置"
              │  每次逻辑批处理复用一份配置快照
              │
模型批次完成 ──→ ModelPostProcessor.OnPostprocessAllAssets
                 │  收集关系计划并按阶段导入
                 │  真实完成回执到齐且验证通过后进入下一阶段
```

#### 6. 单资源规则与跨资源关系分离

模型规则只负责一个 FBX 自身的 Importer 目标。文件夹基础设置与文件名后缀变体通过多条规则逐字段覆盖，不再使用 `ModelFolderType` 枚举或在核心处理器中硬编码项目分类。

Avatar 等“一个资源依赖另一个资源”的逻辑由资源关系处理器负责。处理器读取模型规则合并后的最终目标；最终目标明确为 `NoAvatar` 的资源直接退出 Avatar 关系，避免在规则与关系配置中重复维护排除后缀。

#### 7. 模型资源关系扩展（IAssetRelationProcessor）

统一的 `ModelPostProcessor` 保持为稳定 AssetPostprocessor 入口，项目或其它模块可在独立 Editor 程序集中实现关系处理器：

```csharp
public interface IAssetRelationProcessor
{
    int Priority { get; }
    bool ShouldProcess(string assetPath);
    void CollectPlans(AssetRelationCollectContext context,
                      AssetRelationPlanCollector collector);
    void ApplyImporter(AssetImporter importer,
                       IAssetImportTargetQuery targetQuery);
    bool ValidateImportedAsset(string assetPath,
                               IAssetImportTargetQuery targetQuery,
                               out string error);
}
```

关系处理器声明提供者、消费者和阶段顺序，宿主在基础模型设置之后调用 `ApplyImporter`，并由持久队列以真实 `OnPostprocessAllAssets` 完成回执推进阶段。队列不使用 `delayCall` 猜测导入完成；脚本重载或编辑器中断后的未完成阶段保存在 `Library`，完成后清空。

处理器类型、命名空间和稳定 TypeId 应只表达功能，不绑定具体项目名称。重命名已序列化的实现时必须同步迁移 managed-reference 配置；是否保留 `MovedFrom` 兼容层由发布和迁移范围决定，能够一次性更新全部配置时可以直接迁移而不保留旧身份。

#### 8. Project 窗口可视化

通过 `EditorApplication.projectWindowItemOnGUI` 注册绘制回调：

- 在文件/文件夹右侧显示模型最高生效规则及额外规则数量，纹理显示匹配配置
- 按启用/禁用状态使用不同颜色
- 支持通过 Odin 面板和 MenuItem 菜单开关，默认关闭
- 配置变化后同步刷新绘制回调；绘制时使用当前配置和统一目标解析

#### 9. 辅助功能

- 旧“逐个导入文件夹内资源”右键菜单已移除；Avatar 提供者与消费者顺序由关系阶段自动处理，不要求用户先导入特定后缀资源
- 处理器代码变化或罕见漏处理使用明确的人工全量重导入口或 Unity 原生 Reimport 兜底，不把跨资源正确性绑定到通用逐文件菜单
- **查找并移除 Missing Scripts**：遍历 Prefab/SO/Scene 递归清理
- **平台特定纹理设置**：Android / Windows 分 Tab 页独立配置格式、压缩等

#### 10. 自动化边界与最小状态

该三层架构解决“配置如何驱动导入”，不意味着工具还要并行维护一套资源状态监控系统。普通资源新增、内容修改、`.meta` 和 Importer 变化由 Unity Asset Pipeline 触发；配置型工具默认只补充 Unity 无法自行推导的部分：

- 会影响输出的外部配置应声明为自定义导入依赖。
- 配置范围扩大、缩小、禁用或删除时，重导旧范围与新范围的并集。
- 资源移动时，仅在移动前后的匹配规则集合发生变化时补充重导。
- 处理器代码变化和罕见漏处理由开发者人工强制全量重导兜底。

只有产品明确要求跨代码错误、配置不可用、中断或重启后自动证明“没有漏处理”，并且已有可复现故障表明 Unity 原生导入不足时，才增加逐资源结果、未完成任务、Import Worker 回执和完整性审计。框架的可扩展性不应成为默认启用高成本恢复协议的理由。

### 设计要点总结

| 设计点 | 实现方式 | 收益 |
|--------|---------|------|
| 配置与逻辑分离 | SO 配置 + Processor + 批次快照 | 配置可序列化、每批使用一致的最新目标 |
| 多规则最终目标 | 队列合并 + 逐字段覆盖 + 语义哈希 | 同目录多类资源可得到不同目标，所有入口共用结果 |
| 细粒度控制 | 每项设置独立覆盖开关 | 高队列只修改需要覆盖的字段 |
| 单资源豁免 | meta labels | 不影响其他资源，无需改配置 |
| 自动化触发 | AssetPostprocessor | 导入/移动自动执行，无需手动 |
| 可扩展资源关系 | IAssetRelationProcessor + 阶段队列 | 模块外声明跨资源依赖，不污染基础规则 |
| 真实完成边界 | OnPostprocessAllAssets 回执 + 结果验证 | 不依赖文件枚举顺序或延迟帧推测 |
| Inspector 增强 | finishedDefaultHeaderGUI | 不替换原生 Inspector，低侵入 |
| Project 窗口标记 | projectWindowItemOnGUI | 可视化配置覆盖范围 |

### 参考链接

- [Unity AssetPostprocessor 官方文档](https://docs.unity3d.com/ScriptReference/AssetPostprocessor.html)
- [Odin Inspector - SerializedScriptableObject](https://odininspector.com/documentation/sirenix.odinInspector.editor/serializedscriptableobject)

### 相关记录

- [Unity 输出型 AssetPostprocessor 的最小重导策略](./unity-assetpostprocessor-minimal-reimport-strategy.md) - 外部配置依赖、旧/新范围差分、移动范围转换和自动恢复强度的决策边界。
- [历史方案：Unity 输出型 AssetPostprocessor 的强恢复重导设计](./unity-assetpostprocessor-semantic-reimport-recovery.md) - 已废弃的强恢复默认方案；仅保留特定强保证需求下的机制参考。

### 验证记录
- [2026-03-31] 初次记录，来源：完整阅读项目 AssetsTool 全部 13 个源文件的实地代码分析
- [2026-07-24] 架构边界修正。结合输出型 FBX 后处理工具的简化实践，明确配置驱动和模块化扩展不等于需要逐资源状态监控；普通资源变化交给 Unity，只保留外部配置依赖、范围差分、范围转换和人工全量重导作为默认闭环。
- [2026-07-24] 按当前模型规则队列与资源关系实现完成重大时效性修正：模型改为多规则最终目标，跨资源 Avatar 依赖改由真实导入回执驱动的阶段队列处理；删除旧 FolderType、AvatarSync 延迟模块和 `_Skin` 优先逐个导入菜单描述，并补充可移植类型身份与配置同步迁移约束。

---

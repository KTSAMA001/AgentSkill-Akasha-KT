# Unity 编辑器资源导入工具架构（配置驱动 + AssetPostprocessor 自动化）

**标签**：#unity #custom-editor #tools #architecture #scriptable-object #fbx #texture
**来源**：实地代码分析
**收录日期**：2026-03-31
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐（实地分析）
**适用版本**：Unity 2021+

### 概要

基于 ScriptableObject 配置驱动 + AssetPostprocessor 自动执行的资源批量导入管理框架，分为模型处理和纹理处理两大平行子系统。支持文件夹级别的规则配置、单资源豁免机制、资源移动自动重新导入、模块化后处理扩展，以及 Project 窗口/Inspector 的可视化增强。

### 内容

#### 1. 整体架构

采用**配置 SO + Processor 处理器 + PostProcessor 自动触发**三层架构，模型和纹理各有一套完全对称的子系统：

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
     (核心处理逻辑，static)     (核心处理逻辑，static)
              │                       │
     ModelPostProcessor        TexturePostProcessor
     (AssetPostprocessor)      (AssetPostprocessor)
              │                       │
     ModelMoveProcessor        TextureMoveProcessor
     (资源移动监听)             (资源移动监听)
```

#### 2. 配置层设计

配置 SO 继承 `SerializedScriptableObject`（Odin），核心字段：

- `AutoSetXxxImportSettings`：全局自动处理开关
- `processFolders`：限定处理范围的文件夹列表
- `List<PathFolderSpecificXxxSettings>`：文件夹特定设置列表，每项包含：
  - `configName`：配置名称（用于 Project 窗口标记显示）
  - `folderPath`：目标文件夹路径（Odin FolderPath 属性）
  - `settings`：具体导入设置对象

**每项设置独立启用开关**：每个导入参数都有 `enableXxxConfig` 布尔开关，未启用的项不会被强制覆盖。这样可以实现"只管我关心的设置，其余不干预"。

```csharp
// 示例：模型设置中的独立开关模式
[ToggleLeft][LabelText("启用网格压缩配置")] public bool enableMeshCompressionConfig = false;
[ShowIf("enableMeshCompressionConfig")] public ModelImporterMeshCompression meshCompression;

[ToggleLeft][LabelText("启用法线导入模式配置")] public bool enableImportNormalsConfig = false;
[ShowIf("enableImportNormalsConfig")] public ModelImporterNormals importNormals;
```

#### 3. 最长路径匹配算法

当资源可能匹配多个文件夹配置时，使用**最长路径前缀匹配**确保优先应用最具体的配置：

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
              │  检查 AutoSet 开关 + processFolders 范围
              │  委托给 Processor.ProcessSingleXxx()
              │
资源移动 ──→ MoveProcessor.OnPostprocessAllAssets
              │  检测新旧路径配置匹配变化
              │  自动 reimport
              │
手动按钮 ──→ OdinGUI."应用导入设置"
              │  Processor.ProcessAll() → ReimportProcessed()
```

#### 6. FolderType 策略（模型专有）

通过 `ModelFolderType` 枚举 + 文件名后缀识别，在 partial class 中拆分处理逻辑：

| FolderType | 后缀 | 行为 |
|------------|------|------|
| Monster | `_Skin` | 创建自己的 Avatar (CreateFromThisModel) |
| Monster | `_Broken` | 关闭动画、无 Avatar、开启 isReadable |
| Monster | `_Prop` | 关闭动画、无 Avatar |
| Monster | 其他 | 从同目录 `*_Skin.fbx` 复制 Avatar (CopyFromOther) |
| Prop / Environment | — | 关闭动画导入 |

#### 7. 模块化后处理（IPostprocessModule）

统一的 `ModelPostProcessor` 作为唯一 AssetPostprocessor 入口，通过接口分发：

```csharp
public interface IPostprocessModule
{
    string ModuleName { get; }
    int Priority { get; }           // 数值越小越先执行
    bool IsEnabled { get; set; }
    bool HasPendingWork { get; }
    void OnAssetsImported(string[] imported, string[] deleted, 
                          string[] moved, string[] movedFrom, Config config);
    void ProcessDelayed(Config config);  // DelayCall 中执行
    void Reset();
}
```

当前已实现模块：`AvatarSyncModule`（当 `*_Skin.fbx` 被重新导入时，自动更新同目录下引用该 Skin 的关联模型的 sourceAvatar）。

#### 8. Project 窗口可视化

通过 `EditorApplication.projectWindowItemOnGUI` 注册绘制回调：

- 在文件/文件夹右侧显示其匹配的配置规则名称
- 按启用/禁用状态使用不同颜色
- 支持通过 Odin 面板和 MenuItem 菜单开关
- 使用配置缓存和扩展名 HashSet 优化性能

#### 9. 辅助功能

- **逐个导入**（右键菜单）：优先导入 `_Skin.FBX`，保证 Avatar 源先就位
- **查找并移除 Missing Scripts**：遍历 Prefab/SO/Scene 递归清理
- **平台特定纹理设置**：Android / Windows 分 Tab 页独立配置格式、压缩等

### 设计要点总结

| 设计点 | 实现方式 | 收益 |
|--------|---------|------|
| 配置与逻辑分离 | SO 配置 + static Processor | 配置可序列化、可版本控制 |
| 细粒度控制 | 每项设置独立开关 | 只覆盖关心的设置 |
| 单资源豁免 | meta labels | 不影响其他资源，无需改配置 |
| 自动化触发 | AssetPostprocessor | 导入/移动自动执行，无需手动 |
| 可扩展后处理 | IPostprocessModule 接口 | 新增模块只需实现接口+注册 |
| partial class 拆分 | FolderType 策略独立文件 | 可维护性好，职责清晰 |
| Inspector 增强 | finishedDefaultHeaderGUI | 不替换原生 Inspector，低侵入 |
| Project 窗口标记 | projectWindowItemOnGUI | 可视化配置覆盖范围 |

### 参考链接

- [Unity AssetPostprocessor 官方文档](https://docs.unity3d.com/ScriptReference/AssetPostprocessor.html)
- [Odin Inspector - SerializedScriptableObject](https://odininspector.com/documentation/sirenix.odinInspector.editor/serializedscriptableobject)

### 验证记录

- [2026-03-31] 初次记录，来源：完整阅读项目 AssetsTool 全部 13 个源文件的实地代码分析

---

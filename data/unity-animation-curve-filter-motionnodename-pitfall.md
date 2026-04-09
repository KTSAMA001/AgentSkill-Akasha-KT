# Unity OnPostprocessAnimation 动画曲线过滤：不要用 motionNodeName 读取 Rig Root node

**标签**：#unity #animation #fbx #experience #bug #custom-editor
**来源**：实践验证 + Unity API 调查
**收录日期**：2026-04-08
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐（实地验证）
**适用版本**：Unity 2021+

### 概要

在 `AssetPostprocessor.OnPostprocessAnimation` 中实现动画曲线过滤时，**不能把** `ModelImporter.motionNodeName` **当成** Inspector `Rig` 页签里 Generic 动画的 `Root node`。`motionNodeName` 对应的是 `Animation` 页签 `Motion` 区域的 `Root Motion Node`，不是同一个设置。当前已验证可用的做法，是通过 `SerializedObject` 读取内部属性 `m_HumanDescription.m_RootMotionBoneName`，再按 `EditorCurveBinding.path` 的 Transform 路径字符串做匹配。

### 内容

#### 需求场景

FBX 模型导入时，自动过滤动画曲线：
- **保留** Root 节点（`Rig` 页签中配置的 `Root node`）自身的指定曲线
- **删除** 其他节点的指定曲线
- 目的是减少动画数据量，并保证 Root 节点曲线不被误删

#### 核心结论：Rig Root node 与 Root Motion Node 不是一回事

根据 Unity 官方文档：

- `Rig` 页签 Generic 配置中的 `Root node`：用于指定 Generic 骨架的根节点
- `Animation` 页签 `Motion` 区域中的 `Root Motion Node`：用于指定 Root Motion 的提取来源

`ModelImporter.motionNodeName` 对应的是后者，不是前者。因此，拿 `motionNodeName` 去读取 `Rig` 页签的 `Root node` 在语义上就是错的，不能因为“有时返回空值”就把它当成一个不稳定但可用的 API。

当前已验证的 `Rig Root node` 存储位置是内部序列化属性：
```
m_HumanDescription.m_RootMotionBoneName
```

这个字段不是公开 API。Unity 官方文档说明了 `Rig Root node` 与 `Root Motion Node` 的概念区别，但没有提供读取 `Rig Root node` 的公开脚本接口。该字段可从 [Unity 社区讨论](https://discussions.unity.com/t/using-modelimporter-to-set-root-node-from-script/543933) 和 [UnityCsReference 源码](https://github.com/Unity-Technologies/UnityCsReference/blob/master/Modules/AssetPipelineEditor/ImportSettings/ModelImporterRigEditor.cs) 中得到佐证。

#### 当前已验证可用的读取方式

```csharp
private static string ResolveRootMotionNodePath(ModelImporter importer)
{
    if (importer == null) return "";

    var so = new SerializedObject(importer);
    string rootPath = so.FindProperty("m_HumanDescription.m_RootMotionBoneName")?.stringValue ?? "";
    return rootPath;
}
```

说明：

- 这仍然属于**依赖内部序列化字段**的做法，不是公开 API
- 但就当前已知信息和项目实测而言，这是读取 `Rig Root node` 的正确方向
- `motionNodeName` 应只在你要处理 `Root Motion Node` 时使用

#### Root 匹配本质上是 Transform 路径字符串匹配

`OnPostprocessAnimation` 中拿到的不是 `Transform` 对象引用，而是 `EditorCurveBinding.path`。因此过滤逻辑的本质是：

- 先读取 `Rig Root node` 的字符串
- 再和每条曲线的 `binding.path` 做字符串匹配

当前项目中，为避免导入后的 `binding.path` 与配置值在层级前缀上不完全一致，使用了“完全匹配 + 后缀匹配”的兼容策略：

```csharp
private static bool IsRootNodeBinding(string bindingPath, string rootPath)
{
    if (string.IsNullOrEmpty(rootPath))
        return string.IsNullOrEmpty(bindingPath);

    string normalizedBinding = bindingPath.Replace('\\', '/');
    string normalizedRoot = rootPath.Replace('\\', '/');

    // 完全匹配（不区分大小写）
    if (string.Equals(normalizedBinding, normalizedRoot, StringComparison.OrdinalIgnoreCase))
        return true;

    // 后缀匹配（rootPath 可能只是叶节点名）
    if (normalizedBinding.EndsWith("/" + normalizedRoot, StringComparison.OrdinalIgnoreCase))
        return true;

    return false;
}
```

#### 曲线过滤的实现位置

在 `AssetPostprocessor.OnPostprocessAnimation(GameObject root, AnimationClip clip)` 回调中执行：

- 通过 `AnimationUtility.GetCurveBindings(clip)` 获取所有曲线绑定
- 跳过 Root 节点的曲线
- 对非 Root 节点，用 `AnimationUtility.SetEditorCurve(clip, binding, null)` 删除指定曲线
- 此回调在模型导入管线中，clip 可写，修改会被持久化

#### 配置集成建议

作为 FBX 导入规则的标准处理项（而非特定 FolderType 的附加配置），遵循现有工具的 `enable+值` 开关模式：

| 字段 | 作用 |
|------|------|
| `enableAnimCurveFilterConfig` | 总开关 |
| `animCurveFilterBySuffix` | 是否仅对指定后缀 FBX 生效 |
| `animCurveFilterSuffixes` | 后缀列表（`_` 分割取末段匹配） |
| `animCurveFilterCustomRoot` | 是否自定义 Root 路径（否则自动从 Rig 读取） |
| `animCurveFilterRootPath` | 手动指定的 Root 路径 |
| `animCurveFilterPropertyTypes` | 删除哪些内置曲线类型（当前项目已改为多选枚举） |

### 参考链接

- [Unity ModelImporter.motionNodeName 官方文档](https://docs.unity3d.com/2022.3/Documentation/ScriptReference/ModelImporter-motionNodeName.html) - 对应 Animation 页签 Motion 的 Root Motion Node，而非 Rig Root node
- [Unity Rig tab 官方文档](https://docs.unity3d.com/2020.3/Documentation/Manual/FBXImporter-Rig.html) - Generic 动画需指定 Root node
- [Unity Motion 官方文档](https://docs.unity3d.com/2023.1/Documentation/Manual/AnimationRootMotionNodeOnImportedClips.html) - Root Motion Node 说明
- [Unity 社区：Setting Root Node from script](https://discussions.unity.com/t/using-modelimporter-to-set-root-node-from-script/543933) - 揭示 `m_RootMotionBoneName` 的帖子
- [Unity OnPostprocessAnimation 官方文档](https://docs.unity3d.com/Documentation/ScriptReference/AssetPostprocessor.OnPostprocessAnimation.html) - 动画后处理回调
- [Unity AnimationUtility.SetEditorCurve 官方文档](https://docs.unity3d.com/2022.3/Documentation/ScriptReference/AnimationUtility.SetEditorCurve.html) - 传 null 移除曲线

### 相关记录

- [Unity 编辑器资源导入工具架构](./unity-asset-import-tool-architecture.md) - 本功能所在的整体工具架构
- [Unity Generic 动画导入配置完整流程](./unity-generic-animation-import-config.md) - Rig/Root node 的手动配置流程

### 验证记录

- [2026-04-08] 初次记录。将 `motionNodeName` 误判为读取 Rig Root node 的公开 API，后续需继续核验其语义边界。
- [2026-04-09] 修正：结合 Unity `Rig` / `Motion` 官方文档与项目代码复核，确认 `motionNodeName` 对应的是 `Root Motion Node`，不是 `Rig Root node`。当前已验证的正确方向是使用 `SerializedObject` 读取 `m_HumanDescription.m_RootMotionBoneName`，并按 `EditorCurveBinding.path` 做字符串匹配过滤。移除了“三级回退链 / transformPaths 映射”为已验证结论的表述。

---

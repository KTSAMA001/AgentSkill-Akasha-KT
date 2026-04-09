# Unity OnPostprocessAnimation 动画曲线过滤：motionNodeName 返回空值的坑

**标签**：#unity #animation #fbx #experience #bug #custom-editor
**来源**：实践验证 + Unity API 调查
**收录日期**：2026-04-08
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐（实地验证）
**适用版本**：Unity 2021+

### 概要

在 `AssetPostprocessor.OnPostprocessAnimation` 中实现动画曲线过滤（删除非 Root 节点的 Position/Scale 曲线）时，`ModelImporter.motionNodeName` 公开 API 在很多情况下返回空字符串，即使 Inspector Rig 页签的 "Root node" 已正确设置。必须通过 `SerializedObject` 读取内部属性 `m_HumanDescription.m_RootMotionBoneName` 来获取真实的 Root 节点配置。

### 内容

#### 需求场景

FBX 模型导入时，自动过滤动画曲线：
- **保留** Root 节点（Rig 页签中配置的 Root node）的 Position + Rotation 曲线
- **删除** 所有其他节点的 Position 和 Scale 曲线（只保留 Rotation）
- 目的是减少动画数据量，只让 Root 节点驱动位移

#### 核心坑点：motionNodeName 返回空值

Unity Inspector Rig 页签中 "Root node" 下拉框（如显示 `root/Bip001`）的值，并不存储在公开 API `ModelImporter.motionNodeName` 中。实际测试中 `motionNodeName` 经常返回空字符串。

真正的存储位置是内部序列化属性：
```
m_HumanDescription.m_RootMotionBoneName
```

这个事实在 Unity 官方文档中没有明确说明，只能从 [Unity 社区讨论](https://discussions.unity.com/t/using-modelimporter-to-set-root-node-from-script/543933) 和 [UnityCsReference 源码](https://github.com/Unity-Technologies/UnityCsReference/blob/master/Modules/AssetPipelineEditor/ImportSettings/ModelImporterRigEditor.cs) 中找到线索。

#### 解决方案：三级回退链

```csharp
private static string ResolveRootMotionNodePath(ModelImporter importer)
{
    if (importer == null) return "";

    // 1. 尝试 motionNodeName（公开 API）
    string rootPath = importer.motionNodeName;
    if (!string.IsNullOrEmpty(rootPath))
        return rootPath;

    // 2. 通过 SerializedObject 读取 Rig 页签的 Root node
    var so = new SerializedObject(importer);
    var prop = so.FindProperty("m_HumanDescription.m_RootMotionBoneName");
    string rootBoneName = prop?.stringValue;
    if (string.IsNullOrEmpty(rootBoneName))
        return "";

    // 3. 在 transformPaths 中查找骨骼名对应的完整路径
    string[] paths = importer.transformPaths;
    if (paths != null)
    {
        // 先精确路径匹配（m_RootMotionBoneName 可能已经是完整路径）
        foreach (string path in paths)
        {
            if (string.IsNullOrEmpty(path)) continue;
            if (string.Equals(path, rootBoneName, StringComparison.OrdinalIgnoreCase))
                return path;
        }
        // 再叶节点名匹配
        foreach (string path in paths)
        {
            if (string.IsNullOrEmpty(path)) continue;
            int lastSlash = path.LastIndexOf('/');
            string leafName = lastSlash >= 0 ? path.Substring(lastSlash + 1) : path;
            if (string.Equals(leafName, rootBoneName, StringComparison.OrdinalIgnoreCase))
                return path;
        }
    }

    return rootBoneName;
}
```

#### binding.path 匹配也需要容错

`EditorCurveBinding.path` 与获取到的 Root 路径之间可能存在大小写差异、路径分隔符差异、或完整路径 vs 叶节点名差异。需要模糊匹配：

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
- 对非 Root 节点，用 `AnimationUtility.SetEditorCurve(clip, binding, null)` 删除 `m_LocalPosition.*` 和 `m_LocalScale.*` 曲线
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
| `animCurveFilterRemovePosition` | 删除非 Root 的 Position 曲线 |
| `animCurveFilterRemoveScale` | 删除非 Root 的 Scale 曲线 |

### 参考链接

- [Unity ModelImporter.motionNodeName 官方文档](https://docs.unity3d.com/2022.3/Documentation/ScriptReference/ModelImporter-motionNodeName.html) - 公开 API（实际常返回空值）
- [Unity 社区：Setting Root Node from script](https://discussions.unity.com/t/using-modelimporter-to-set-root-node-from-script/543933) - 揭示 `m_RootMotionBoneName` 的帖子
- [Unity OnPostprocessAnimation 官方文档](https://docs.unity3d.com/Documentation/ScriptReference/AssetPostprocessor.OnPostprocessAnimation.html) - 动画后处理回调
- [Unity AnimationUtility.SetEditorCurve 官方文档](https://docs.unity3d.com/2022.3/Documentation/ScriptReference/AnimationUtility.SetEditorCurve.html) - 传 null 移除曲线

### 相关记录

- [Unity 编辑器资源导入工具架构](./unity-asset-import-tool-architecture.md) - 本功能所在的整体工具架构
- [Unity Generic 动画导入配置完整流程](./unity-generic-animation-import-config.md) - Rig/Root node 的手动配置流程

### 验证记录

- [2026-04-08] 初次记录。实际项目中验证：`motionNodeName` 对 Generic 动画类型返回空字符串，通过 `SerializedObject` 读取 `m_HumanDescription.m_RootMotionBoneName` 后成功获取 Root 节点路径。动画曲线过滤功能在 FBX 导入后正确保留 Root 节点的 Position/Rotation 曲线，删除其他节点的 Position/Scale 曲线。

---

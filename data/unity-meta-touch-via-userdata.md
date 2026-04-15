# Unity 中通过 userData 稳定触发 Meta 变更

**标签**：#unity #editor #tools #experience #serialization
**来源**：实践总结
**收录日期**：2026-04-07
**更新日期**：2026-04-07
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐
**适用版本**：Unity 2022.3+

### 概要
如果目标只是让 Unity 资源对应的 `.meta` 文件稳定产生变化，优先使用 `AssetImporter.userData` 写入自定义标记，而不是依赖 `timeCreated` 这类未明确公开承诺的内部字段。

### 内容

#### 推荐做法

使用 `AssetImporter.GetAtPath()` 获取资源导入器，通过 `importer.userData` 写入一个自定义键值，例如：

```text
meta_touch_key=<unix_timestamp>
```

推荐原因：

- `userData` 是 Unity 官方公开支持的导入器字段。
- 变化会持久化到对应 `.meta` 文件。
- 一般不会影响资源功能，除非项目自己的导入流程主动读取该字段。
- 比直接操作 `.meta` 中的 `timeCreated` 更稳妥。

#### 批量处理建议

当需要批量修改大量资源时，不要对每个资源都调用 `SaveAndReimport()`，否则会出现“改一个、导一个”，速度很慢。

推荐流程：

1. `AssetDatabase.StartAssetEditing()`
2. 遍历资源并更新 `importer.userData`
3. 使用 `AssetDatabase.WriteImportSettingsIfDirty(assetPath)` 写回导入设置
4. 全部处理完成后执行 `AssetDatabase.StopAssetEditing()`
5. 最后统一 `AssetDatabase.Refresh()`

这样可以明显减少批处理过程中的频繁导入开销。

#### 字段更新策略

对写入到 `userData` 的标记，推荐采用 upsert 逻辑：

- 已存在同名键：更新值
- 不存在同名键：追加新行

这样可以避免同一个标记重复堆积。

#### 关于 timeCreated

若历史流程已经人为写入过 `.meta` 的 `timeCreated:` 行，而当前决定切换到 `userData` 方案，则可以在处理时顺手移除旧的 `timeCreated:` 行，统一让 `.meta` 变化来源收敛到 `userData` 标记。

### 关键代码

```csharp
AssetImporter importer = AssetImporter.GetAtPath(assetPath);
string newUserData = UpsertTouchMarker(importer.userData, timestamp);
importer.userData = newUserData;
AssetDatabase.WriteImportSettingsIfDirty(assetPath);
```

### 参考链接

- [Unity - Scripting API: AssetImporter.userData](https://docs.unity3d.com/Documentation/ScriptReference/AssetImporter-userData.html) - 官方支持的自定义导入器数据字段
- [Unity - Scripting API: AssetDatabase.WriteImportSettingsIfDirty](https://docs.unity3d.com/ScriptReference/AssetDatabase.WriteImportSettingsIfDirty.html) - 批量写入 importer 设置
- [Unity - Manual: Asset Metadata](https://docs.unity3d.com/2022.3/Documentation/Manual/AssetMetadata.html) - `.meta` 文件的官方概述

### 相关记录

- [Unity 编辑器资源导入工具架构](./unity-asset-import-tool-architecture.md) - 配置驱动 + AssetPostprocessor 自动化导入框架，与本记录互补：导入工具控制资源导入规则，本记录解决批量触碰 `.meta` 的具体手段

### 验证记录
- [2026-04-07] 初次记录，来源：Unity 项目内批量 meta 触碰工具实践
- [2026-04-07] 确认 `userData` 适合作为稳定触发 `.meta` 变化的官方路径；批量处理应采用 `StartAssetEditing + WriteImportSettingsIfDirty + Refresh`

---

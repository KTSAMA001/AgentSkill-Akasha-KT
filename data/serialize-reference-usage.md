# Unity SerializeReference 多态序列化与配置类型迁移

**标签**：#unity #csharp #serialization #experience
**来源**：实践总结 - Unity 2022.3.62f3 配置资产验证，并结合 Unity 官方文档与 UnityCsReference 复核
**收录日期**：2026-03-05
**来源日期**：2026-07-22
**更新日期**：2026-07-22
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐（Unity 2022.3.62f3 实践验证 + Unity 官方资料复核）
**适用版本**：基础用法为 Unity 2020.1+；本文 YAML 结构、缺失类型检查与迁移流程验证于 Unity 2022.3.62f3

### 概要

`[SerializeReference]` 让 Unity 以 managed reference 方式保存普通 C# 对象，支持接口、抽象类、多态、`null`、共享引用和循环引用。它同时会持久化对象的类名、命名空间和程序集名；这些类型身份变化后，必须通过 `MovedFrom` 或受控修改配置资产中的 `references` 类型信息完成迁移，才能保留原有字段值。

### 内容

#### 一、`SerializeReference` 解决什么问题

Unity 默认按值序列化普通可序列化类。字段声明为接口、抽象类，或需要保存真实派生类型、共享对象引用和循环结构时，应在宿主对象的字段上使用 `[SerializeReference]`。

```csharp
using System;
using UnityEngine;

public interface IStrategy
{
    void Execute();
}

[Serializable]
public sealed class ExampleStrategy : IStrategy
{
    public bool enabled = true;
    public float scale = 1f;

    public void Execute()
    {
    }
}

public sealed class StrategyConfig : ScriptableObject
{
    [SerializeReference]
    private IStrategy strategy;
}
```

需要同时满足：

- 具体实现类标记 `[Serializable]`，且不是 `UnityEngine.Object` 派生类。
- `[SerializeReference]` 标记的是宿主对象中的字段，而不是具体实现类。
- 默认 Inspector 是否提供方便的派生类型创建入口取决于 Unity 版本和自定义编辑器；该特性负责序列化能力，不等同于完整的类型选择界面。
- managed reference 只在同一个宿主对象内部共享。多个宿主对象需要共享同一份数据时，应考虑 `ScriptableObject`。
- Unity 官方明确说明按值序列化更节省存储、内存和加载/保存时间；只有确实需要上述引用语义时才使用 `[SerializeReference]`。

#### 二、Unity 2022.3 如何保存 managed reference

Unity 官方文档说明，managed reference 会写在宿主对象序列化数据末尾的 `references` 区域，每个对象保存唯一 ID、完整类型身份和字段值。

在 Unity 2022.3.62f3、Force Text 序列化下，实际配置资产呈现为：

```yaml
Strategies:
- rid: 1001
references:
  version: 2
  RefIds:
  - rid: 1001
    type: {class: ExampleStrategy, ns: Example.Legacy, asm: Example.Editor}
    data:
      enabled: 1
      scale: 1
```

各部分职责是：

| 字段 | 含义 | 类型迁移时是否应改变 |
|---|---|---|
| `rid` | 宿主字段与 `RefIds` 对象数据之间的引用 ID | 不应改变 |
| `type.class` | 具体实现类名 | 只有类名确实改变时修改 |
| `type.ns` | 具体实现类所在命名空间 | 命名空间改变时修改 |
| `type.asm` | 不带扩展名的程序集名 | 类型迁移到其他程序集时修改 |
| `data` | 该 managed reference 的实际字段值 | 只做类型迁移时不应改变 |

`references.version: 2`、`RefIds` 和具体 YAML 排版是 Unity 2022.3.62f3 的实际输出，不是跨版本稳定的公开文件格式承诺。升级 Unity 后应先创建或保存一个小型测试资产，检查当前文本结构，再编写迁移工具。

#### 三、类型身份缺失不等于数据已经丢失

Unity 2022.3 官方文档说明：反序列化时如果记录的命名空间、类名和程序集名无法解析，C# 字段会暂时为 `null`；但 managed reference 的持久化状态仍保留在资产中，并会随资产再次保存。缺失类型之后重新可用时，原状态可以恢复。

可以在编辑器代码中明确检查：

```csharp
using UnityEditor;
using UnityEngine;

internal static class ManagedReferenceGuard
{
    internal static bool CanSafelyRewrite(Object config)
    {
        return config != null &&
               !SerializationUtility.HasManagedReferencesWithMissingTypes(config);
    }
}
```

虽然 Unity 2022.3 会保留缺失对象的数据，实践中仍建议在检查结果为 `true` 时拒绝迁移完成标记和主动保存。原因是项目可能还使用 Odin、定制 Inspector 或其他保存链路，不能把 Unity 原生保留语义扩大解释为所有第三方保存流程都绝对安全。

#### 四、推荐方式：用 `MovedFrom` 让旧配置自动解析

脚本只改变命名空间、程序集或类名时，应先在新类型上声明旧身份，再让 Unity 加载旧资产：

```csharp
using System;
using UnityEngine.Scripting.APIUpdating;

namespace Example.Current
{
    [Serializable]
    [MovedFrom(
        true,
        "Example.Legacy",
        "Example.Editor",
        "ExampleStrategy")]
    public sealed class ExampleStrategy : IStrategy
    {
        public bool enabled = true;
        public float scale = 1f;

        public void Execute()
        {
        }
    }
}
```

Unity 2022.3.62f3 的官方程序集实际提供两个构造函数：`MovedFromAttribute(bool, string, string, string)` 与 `MovedFromAttribute(string)`。UnityCsReference 进一步说明，四个参数依次表示是否参与 API Updater、旧命名空间、旧程序集和旧类名；传入 `null` 表示该部分身份没有变化。

推荐顺序：

1. 在代码移动的同一次变更中，为每个 `[SerializeReference]` 具体类型添加准确的 `MovedFrom`。
2. 等待脚本编译完成，再加载旧配置资产。
3. 使用 `HasManagedReferencesWithMissingTypes` 确认所有对象类型都已解析。
4. 核对对象数量、具体类型、字段值和引用关系。
5. 只有全部检查通过后，才调用 `EditorUtility.SetDirty` 与 `AssetDatabase.SaveAssetIfDirty` 写回当前类型身份。
6. `MovedFrom` 应保留一段兼容周期，以覆盖其他分支、其他项目或尚未打开过的旧配置资产。

#### 五、受控方式：直接同步配置资产的类型信息

若配置资产与代码必须在同一次提交中立即呈现新类型身份，可以在 Unity 未加载该资产时受控修改 Force Text 文件。命名空间改变但类名和程序集未变时，只修改 `type.ns`：

```yaml
# 修改前
type: {class: ExampleStrategy, ns: Example.Legacy, asm: Example.Editor}

# 修改后
type: {class: ExampleStrategy, ns: Example.Current, asm: Example.Editor}
```

必须保持不变：

- 宿主字段中的 `rid` 及 `RefIds` 对应关系。
- `data` 下的全部业务字段和值。
- 未发生变化的 `class` 和 `asm`。
- Unity 对象引用的 `fileID`、GUID 和类型信息。
- 宿主 `MonoBehaviour` 或 `ScriptableObject` 的脚本资源 GUID；仅修改命名空间不会改变 `.cs.meta` 身份。

直接修改的安全流程：

1. 先提交或备份原配置，并确认项目使用 Force Text 序列化。
2. 关闭 Unity，或确保目标资产没有被 Editor 加载和等待保存。
3. 从已编译的新类型读取 `Type.Name`、`Type.Namespace` 和 `Type.Assembly.GetName().Name`，不要凭文件夹名猜测。
4. 只替换匹配旧 `class + ns + asm` 组合的 `type` 条目，不做没有边界的全仓库字符串替换。
5. 用差异检查确认 `rid` 和 `data` 没有变化。
6. 重新打开或导入资产，检查缺失类型、对象数量和全部原配置值。

当前实践采用“双保险”：当前仓库内的配置资产显式同步 `type.ns`，让它立即指向新类型；代码仍保留 `MovedFrom`，用于恢复其他位置尚未更新的旧配置。两者解决的是不同覆盖范围，不是重复写同一份状态。

#### 六、迁移完成条件

一次命名空间迁移只有同时满足以下条件才算完成：

- `HasManagedReferencesWithMissingTypes` 为 `false`。
- `[SerializeReference]` 列表数量、顺序、`rid` 对应关系和具体类型符合迁移前结果。
- 每个对象的业务字段值保持不变。
- 配置 Inspector 能正常打开，没有 missing managed reference 错误。
- 保存并重新加载后结果仍一致，配置文件中的 `type.ns/class/asm` 已是当前身份。
- 版本控制差异只包含预期的类型身份、明确的迁移版本标记或本次业务改动。

若检查失败，应保留原资产内容并恢复类型解析，不能用“保存一次看看”覆盖仍然存在的 managed reference 数据。

#### 七、常见误区

| 误区 | 风险 | 正确做法 |
|---|---|---|
| 代码编译成功就代表旧配置完成迁移 | 旧 YAML 仍可能指向不存在的类型身份 | 检查 missing type 并重新加载旧配置 |
| 命名空间变化时只改 C# `using` | `references` 中的 `type.ns` 不会因此自动变成新值 | 使用 `MovedFrom` 或受控同步 YAML |
| 发现字段为 `null` 就清空或重建配置 | Unity 可能仍保留完整 managed reference 数据 | 先恢复类型，再验证原状态 |
| 批量替换所有旧命名空间字符串 | 可能修改无关数据、程序集名或普通文本字段 | 精确匹配 `type` 的三段身份 |
| 类型缺失时仍写入迁移完成标记 | 不完整配置被误报为成功，后续恢复入口被关闭 | 全部类型可解析后再写回和递增版本 |
| 把字段改名和类型迁移当成同一件事 | 字段值仍可能归零 | 字段改名另用 `FormerlySerializedAs` |

### 参考链接

- [Unity 2022.3 SerializeReference](https://docs.unity3d.com/2022.3/Documentation/ScriptReference/SerializeReference.html) - managed reference、宿主对象、`references` 区域和性能取舍。
- [Unity 2022.3 SerializationUtility.HasManagedReferencesWithMissingTypes](https://docs.unity3d.com/2022.3/Documentation/ScriptReference/SerializationUtility.HasManagedReferencesWithMissingTypes.html) - 缺失类型时的 `null` 表现、持久化数据保留与恢复语义。
- [UnityCsReference UpdatedFromAttribute.cs](https://github.com/Unity-Technologies/UnityCsReference/blob/master/Runtime/Export/Scripting/APIUpdating/UpdatedFromAttribute.cs) - `MovedFromAttribute` 的官方源码、参数和序列化迁移说明。
- [Unity 2022.3 FormerlySerializedAsAttribute](https://docs.unity3d.com/2022.3/Documentation/ScriptReference/Serialization.FormerlySerializedAsAttribute.html) - 字段改名时保留原序列化值。

### 验证记录

- [2025-02-24] 实际项目验证 `[SerializeReference]` 接口与具体实现的多态配置。
- [2026-03-05] 从长期记录提取到阿卡西。
- [2026-07-22] 使用 Unity 2022.3.62f3 的实际 Force Text 配置资产验证 `references.version: 2`、`RefIds`、`rid`、`type.class/ns/asm` 和 `data` 结构；命名空间迁移仅同步 `type.ns`，保留引用 ID 与原字段值。通过 `MovedFrom`、`HasManagedReferencesWithMissingTypes`、配置重新加载和差异检查确认原配置可恢复且不会因迁移丢失参数。官方文档结论与本次实践一致，示例已泛化全部项目标识。

# Behavior Designer ObjectDrawer 系统

**标签**：#unity #ai #knowledge #behavior-designer
**来源**：[Opsive 官方文档](https://opsive.com/support/documentation/behavior-designer/object-drawers/)
**收录日期**：2026-02-03
**来源日期**：2026-02-03
**更新日期**：2026-06-13
**状态**：📘 有效
**可信度**：⭐⭐⭐⭐⭐(官方)
**适用版本**：Behavior Designer（2026-02-03 官方文档时点）

### 概要

ObjectDrawer 是 Behavior Designer 的自定义字段绘制系统，功能定位类似 Unity `PropertyDrawer`，但它独立实现，并且不能访问 Task 实例或其他字段。

### 内容

#### 定义/概念

ObjectDrawer 用于控制 Behavior Designer 字段在编辑器中的绘制方式。它适合基于当前字段值和字段 Attribute 做显示定制，但不适合实现依赖其他字段状态的条件显示。

#### 工作机制

1. 定义一个继承 `ObjectDrawerAttribute` 的 Attribute，放在 Runtime 代码中。
2. 创建一个继承 `ObjectDrawer` 的 Drawer 类，放在 Editor 文件夹中。
3. 使用 `[CustomObjectDrawer(typeof(YourAttribute))]` 将 Drawer 与 Attribute 关联。

#### ObjectDrawer 可访问成员

| 成员 | 类型 | 说明 |
|------|------|------|
| `value` | `object` | 当前字段的值，可读写 |
| `attribute` | `ObjectDrawerAttribute` | 当前字段上的 Attribute 实例 |

#### 关键限制

`ObjectDrawer.OnGUI` 的能力边界：

- ✅ 可以访问当前字段的 `value`。
- ✅ 可以访问当前字段的 `attribute`。
- ❌ 无法访问 Task 实例。
- ❌ 无法访问其他字段的值。
- ❌ 无法直接实现 ShowIf/HideIf 这类依赖其他字段的条件显示。

与 Unity `PropertyDrawer` 对比：

| 功能 | Unity PropertyDrawer | Behavior Designer ObjectDrawer |
|------|---------------------|--------------------------------|
| 访问当前字段 | ✅ | ✅ |
| 访问 SerializedObject | ✅ | ❌ |
| 遍历其他字段 | ✅ | ❌ |
| 条件显示 | ✅ 可实现 | ❌ 不可实现 |

### 关键代码

Attribute 定义应放在 Runtime 侧：

```csharp
using BehaviorDesigner.Runtime.ObjectDrawers;

public class RangeAttribute : ObjectDrawerAttribute
{
    public float min, max;

    public RangeAttribute(float min, float max)
    {
        this.min = min;
        this.max = max;
    }
}
```

Drawer 实现应放在 Editor 侧：

```csharp
using UnityEditor;
using BehaviorDesigner.Editor;

[CustomObjectDrawer(typeof(RangeAttribute))]
public class RangeDrawer : ObjectDrawer
{
    public override void OnGUI(GUIContent label)
    {
        var attr = (RangeAttribute)attribute;
        value = EditorGUILayout.Slider(label, (float)value, attr.min, attr.max);
    }
}
```

### 参考链接

- [官方文档 - Object Drawers](https://opsive.com/support/documentation/behavior-designer/object-drawers/) - Behavior Designer ObjectDrawer 官方说明。

### 相关记录

- [Behavior Designer Task Attributes 系统](./behavior-designer-task-attributes.md) - 同属 Behavior Designer 编辑器扩展能力。
- [BD 节点条件显示的替代方案](./bd-showif-workaround.md) - ObjectDrawer 无法直接实现条件显示时的实践替代方案。

### 验证记录

- [2026-04-15] 结构修复：补齐模板必填章节，未改动原结论。
- [2026-06-13] 结构维护：从旧聚合记录拆分，未重新验证原技术结论。
---

# Behavior Designer 行为树插件的技术规范、API 和原理

### 概要
Behavior Designer 行为树插件的技术规范、API 和原理


> Behavior Designer 行为树插件的技术规范、API 和原理
> 
> 本文档记录"是什么/为什么"的理论知识，实践经验请查阅经验文档

---

## BehaviorDesigner Task Attributes 系统

**标签**：#unity #knowledge #behavior-designer #ai
**来源**：[Opsive 官方文档](https://opsive.com/support/documentation/behavior-designer/task-attributes/)
**来源日期**：2026-02-03
**收录日期**：2026-02-03
**可信度**：⭐⭐⭐⭐⭐(官方)
**状态**：📘 有效

### 定义/概念

BehaviorDesigner 提供一系列 Attribute 用于定义 Task 的元数据和显示行为。

### 原理/详解

#### 内置 Task Attributes

| Attribute | 用途 | 示例 |
|-----------|------|------|
| `[TaskDescription("...")]` | 任务描述，显示在编辑器底部 | `[TaskDescription("移动到目标点")]` |
| `[TaskCategory("...")]` | 分类，支持嵌套（用 `/` 分隔） | `[TaskCategory("Custom/Movement")]` |
| `[TaskName("...")]` | 自定义显示名称 | `[TaskName("移动")]` |
| `[TaskIcon("...")]` | 任务图标路径 | `[TaskIcon("Assets/Icons/move.png")]` |
| `[HelpURL("...")]` | 帮助文档链接 | `[HelpURL("http://docs.example.com")]` |
| `[LinkedTask]` | 关联其他 Task | 用于 TaskGuard 等场景 |
| `[RequiredField]` | 必填字段标记 | 编辑器中会特殊提示 |

#### 字段 Attributes

| Attribute | 命名空间 | 说明 |
|-----------|----------|------|
| `[Tooltip]` | `BehaviorDesigner.Runtime.Tasks` | BD 专用字段提示 |
| `[Tooltip]` | `UnityEngine` | Unity 原生提示 |
| `[Header]` | `UnityEngine` | 分组标题（BD 中可用） |

### 关键点

- TaskCategory 支持多级嵌套：`"RTS/Harvester"` 会创建两层菜单
- TaskDescription 支持换行符 `\n`
- TaskIcon 路径支持 `{SkinColor}` 关键字自动适配 Light/Dark 主题
- BD 有自己的 `TooltipAttribute`，与 `UnityEngine.TooltipAttribute` 同名

### 相关链接

- [官方文档 - Task Attributes](https://opsive.com/support/documentation/behavior-designer/task-attributes/)

---

## BehaviorDesigner ObjectDrawer 系统

**标签**：#unity #knowledge #behavior-designer #ai
**来源**：[Opsive 官方文档](https://opsive.com/support/documentation/behavior-designer/object-drawers/)
**来源日期**：2026-02-03
**收录日期**：2026-02-03
**可信度**：⭐⭐⭐⭐⭐(官方)
**状态**：📘 有效

### 定义/概念

ObjectDrawer 是 BehaviorDesigner 提供的自定义字段绘制系统，类似于 Unity 的 PropertyDrawer，但独立实现。

### 原理/详解

#### 工作机制

1. 定义一个继承 `ObjectDrawerAttribute` 的 Attribute（放在 Runtime 代码中）
2. 创建一个继承 `ObjectDrawer` 的 Drawer 类（放在 Editor 文件夹中）
3. 用 `[CustomObjectDrawer(typeof(YourAttribute))]` 关联

#### 代码结构

**Attribute 定义**（Runtime）：
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

**Drawer 实现**（Editor）：
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

#### ObjectDrawer 可访问的成员

| 成员 | 类型 | 说明 |
|------|------|------|
| `value` | `object` | 当前字段的值，可读写 |
| `attribute` | `ObjectDrawerAttribute` | 当前字段上的 Attribute 实例 |

### 关键点（重要限制）

**ObjectDrawer 的 OnGUI 方法：**
- ✅ 可以访问当前字段的 `value`
- ✅ 可以访问当前字段的 `attribute`
- ❌ **无法访问** Task 实例
- ❌ **无法访问** 其他字段的值
- ❌ **无法实现** ShowIf/HideIf 条件显示

**与 Unity PropertyDrawer 对比：**

| 功能 | Unity PropertyDrawer | BD ObjectDrawer |
|------|---------------------|-----------------|
| 访问当前字段 | ✅ | ✅ |
| 访问 SerializedObject | ✅ | ❌ |
| 遍历其他字段 | ✅ | ❌ |
| 条件显示 | ✅ 可实现 | ❌ 不可实现 |

### 相关链接

- [官方文档 - Object Drawers](https://opsive.com/support/documentation/behavior-designer/object-drawers/)

### 与经验关联

- [BD 节点 Tooltip 命名空间冲突解决](./bd-tooltip-namespace-conflict.md#bd-tooltip-namespace-conflict)
- [BD 节点条件显示的替代方案](./bd-showif-workaround.md#bd-showif-workaround)


### 验证记录
- [2026-04-15] 结构修复：补齐模板必填章节，未改动原结论。

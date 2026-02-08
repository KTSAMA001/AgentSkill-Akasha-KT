# BD 节点 Tooltip 命名空间冲突解决 {#bd-tooltip-namespace-conflict}

**收录日期**：2026-02-03
**标签**：#unity #experience #editor #behavior-designer
**来源**：KTSAMA 实践经验
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐ (实践验证)
**适用版本**：BehaviorDesigner 1.7.x

### 问题/场景

在 BehaviorDesigner 节点中使用 `[Tooltip]` 属性时，编译报错：
```
'Tooltip' is an ambiguous reference between 
'BehaviorDesigner.Runtime.Tasks.TooltipAttribute' and 'UnityEngine.TooltipAttribute'
```

### 解决方案

**方案 1：使用完整命名空间（推荐）**
```csharp
[UnityEngine.Tooltip("说明文字")]
public float myValue;
```

**方案 2：using 别名**
```csharp
using Tooltip = BehaviorDesigner.Runtime.Tasks.TooltipAttribute;

[Tooltip("说明文字")]
public float myValue;
```

**方案 3：枚举值用 XML 注释替代**
```csharp
public enum DirectionType
{
    /// <summary>前方</summary>
    Forward,
    /// <summary>后方</summary>
    Back
}
```

### 验证记录

| 日期 | 验证者 | 结果 |
|------|--------|------|
| 2026-02-03 | KT | ✅ 方案1在项目中验证通过 |

### 理论基础

- [BehaviorDesigner Task Attributes 系统](./behavior-designer-api.md#behaviordesigner-task-attributes-系统)

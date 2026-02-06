# Unity 编辑器扩展经验

> Unity Editor 扩展开发相关经验
> 
> 包含：自定义 Inspector、EditorWindow、菜单扩展、资源导入管线、工具开发等

---

## BD 节点 Tooltip 命名空间冲突解决 {#bd-tooltip-namespace-conflict}

**收录日期**：2026-02-03
**标签**：#BehaviorDesigner #Tooltip #命名空间冲突
**状态**：✅ 已验证
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

- [BehaviorDesigner Task Attributes 系统](../../knowledge/unity/behavior-designer.md#behaviordesigner-task-attributes-系统)

---

## BD 节点条件显示的替代方案 {#bd-showif-workaround}

**收录日期**：2026-02-03
**标签**：#BehaviorDesigner #ShowIf #条件显示 #Inspector
**状态**：✅ 已验证
**适用版本**：BehaviorDesigner 1.7.x

### 问题/场景

希望在 BehaviorDesigner 节点中实现类似 Odin 的 `[ShowIf]` 功能，让某些参数只在特定条件下显示。

经调查发现：
- BD 的 ObjectDrawer 无法访问其他字段，**无法实现真正的条件显示**
- Odin 的 `[ShowIf]` 在 BD 节点中**不生效**（BD 用自己的 Inspector）

### 解决方案

**采用 Header 分组 + 注释标注的方式：**

```csharp
[TaskDescription("节点描述\n用途说明")]
[TaskCategory("Custom")]
public class MyAction : ProfilingAction
{
    #region 基础设置
    [Header("【基础设置】")]
    [UnityEngine.Tooltip("Forward=前方, Back=后方, Custom=自定义")]
    public DirectionType directionType = DirectionType.Forward;
    
    [Header("↳ 仅 directionType=Custom 时生效")]
    [UnityEngine.Tooltip("自定义方向向量")]
    public SharedVector3 customDirection;
    #endregion

    #region 可选功能
    [Header("【可选功能】")]
    [UnityEngine.Tooltip("是否启用高度限制")]
    public bool enableHeightLimit = true;
    
    [Header("↳ 仅 enableHeightLimit=true 时生效")]
    [UnityEngine.Tooltip("最大高度差")]
    public SharedFloat maxHeightDifference;
    #endregion
}
```

**关键技巧：**
- 用 `【】` 标记主分组
- 用 `↳` 标记条件参数，说明生效条件
- 用 `#region` 在代码中分组（不影响 Inspector 显示，便于维护）
- TaskDescription 用 `\n` 换行写多行说明

### 为什么不用其他方案

| 方案 | 问题 |
|------|------|
| Odin [ShowIf] | BD 用自己的 Inspector，Odin 不生效 |
| 自定义 ObjectDrawer | 无法访问其他字段的值 |
| 重写 Task Inspector | 工作量大，需修改 BD 源码或大量反射 |

### 验证记录

| 日期 | 验证者 | 结果 |
|------|--------|------|
| 2026-02-03 | KT | ✅ Header 分组在 BD Inspector 中正常显示 |

### 理论基础

- [BehaviorDesigner ObjectDrawer 系统](../../knowledge/unity/behavior-designer.md#behaviordesigner-objectdrawer-系统)

---

## BD 节点日志频率控制 {#bd-log-throttle}

**收录日期**：2026-02-03
**标签**：#BehaviorDesigner #日志 #性能
**状态**：✅ 已验证

### 问题/场景

行为树节点的 `OnUpdate` 可能每帧执行，如果在其中打印日志会导致：
- Console 刷屏
- 性能下降
- 难以定位关键信息

### 解决方案

添加日志频率控制，限制同一消息最多每秒输出一次：

```csharp
public class MyConditional : ProfilingConditional
{
    // 日志频率控制
    private float _lastLogTime = 0f;
    private const float LOG_INTERVAL = 1f; // 秒

    private bool CanLog()
    {
        float currentTime = Time.time;
        if (currentTime - _lastLogTime >= LOG_INTERVAL)
        {
            _lastLogTime = currentTime;
            return true;
        }
        return false;
    }

    public override TaskStatus OnUpdate_Profiler()
    {
        if (someConditionFailed)
        {
            if (CanLog())
                Debug.LogWarning($"KT---{GetType().Name}---失败原因---{DateTime.Now:HH:mm:ss}");
            return TaskStatus.Failure;
        }
        return TaskStatus.Success;
    }
}
```

### 关键代码

- 使用 `Time.time` 而非 `DateTime.Now` 比较（性能更好）
- 每个节点实例独立计时
- 日志格式遵循项目规范：`KT---类名---信息---时间`

### 验证记录

| 日期 | 验证者 | 结果 |
|------|--------|------|
| 2026-02-03 | KT | ✅ 日志频率正常控制，不再刷屏 |

---

> 另见：[EffectSystem 代码审查](docs/effect-system-review.md) - Unity 编辑器扩展（PropertyDrawer, CustomEditor）相关分析

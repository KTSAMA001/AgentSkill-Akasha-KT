# SerializeReference 多态序列化

**标签**：#unity #csharp #serialization #experience
**来源**：实践总结
**收录日期**：2026-03-05
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐
**适用版本**：Unity 2020.1+

## 概要

使用 `[SerializeReference]` 特性实现接口或抽象类的多态序列化，支持在 Inspector 中配置不同类型的实现。

## 内容

### 使用场景

当需要：
- 序列化接口类型字段
- 序列化抽象类
- 同一字段存储不同类型的实现

### 使用示例

```csharp
public interface IAnimal
{
    void Speak();
}

[Serializable]
public class Dog : IAnimal
{
    public string name;
    public void Speak() => Debug.Log("Woof! " + name);
}

[Serializable]
public class Cat : IAnimal
{
    public string name;
    public void Speak() => Debug.Log("Meow! " + name);
}

public class AnimalManager : MonoBehaviour
{
    [SerializeReference]
    public IAnimal animal; // Inspector 中可选择 Dog 或 Cat
}
```

### 性能分析

| 阶段 | 开销 | 说明 |
|------|------|------|
| 编辑器序列化 | 中等 | 有反射开销，但只在编辑器模式 |
| 运行时反序列化 | 小 | 场景加载时一次性开销 |
| 运行时使用 | 无 | 与普通字段无异 |

### 注意事项

1. **性能不是问题**：运行时开销几乎可忽略
2. **频繁序列化**：如果需要频繁动态创建/反序列化，注意反射消耗
3. **类型约束**：实现类必须标记 `[Serializable]`

### 最佳实践

- 配合接口/抽象类定义统一的契约
- 不同类型通过继承同一接口区分
- 方便管理和扩展

### 验证记录

- [2025-02-24] 实际项目使用验证
- [2026-03-05] 从长期记录提取到阿卡西

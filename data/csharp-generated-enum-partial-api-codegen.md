# Unity/C# 可选生成类型 + partial 同步生成其消费 API

**标签**：#csharp #unity #code-generation #partial-class #experience
**来源**：实践总结（TAModule/EffectSystem 重构验证）
**收录日期**：2026-06-29
**更新日期**：2026-06-29
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐
**适用版本**：C# 7.3+（partial class）；Unity 2022.3 实测

### 概要

当一个类型是「按需生成、可能缺席」的（典型：从配置/数据生成的 `enum`），而某个类又想提供以该类型为参数的便捷 API 时，把**类型本身 + 消费它的便捷 API**一起放进生成文件，用 `partial class` 合并补回。从而做到：生成物缺席时该类仍可独立编译，生成物在场时便捷 API 自动可用且调用方写法不变；同时让"模块/库"与"项目/数据侧"天然解耦。

### 内容

#### 问题本质

存在一个**按需生成、可能不存在**的类型，最常见是「扫描项目数据生成的枚举」，例如把配置表里的效果名/物品 ID 生成成 `enum`。围绕它有两类代码：

- **库/模块**想提供类型安全的便捷重载：`Manager.Do(MyEnum x)`（有智能提示、编译期检查）。
- **业务/项目**直接调用：`Manager.Do(MyEnum.Foo)`。

矛盾点：

1. **enum 不能拆分扩展**——C# 没有 `partial enum`，也不能给已定义的 enum「追加成员」。所以「库放基础 enum + 生成补成员」的思路不成立（同名 enum 重复定义会 CS0101 编译失败）。
2. **若把 enum 定义留在库里**：它本是项目数据生成的，不该由库持有；且库会携带具体项目数据。
3. **若把 enum 完全外置、库里仍写 `Do(MyEnum)`**：库引用了一个可能不存在的类型 → **生成物缺席时库编译失败**。

#### 核心解法：生成文件同时生成「类型」+「消费它的 API」

关键认知：**enum 不能扩展，但 `class` 可以用 `partial` 跨文件合并**。于是把「消费该 enum 的便捷 API」做成目标类的 partial 片段，和 enum 一起生成。

- **库/模块本体**：
  - 只提供**不依赖该可选类型**的底层 API（例如 `string`/`int` 版）。
  - 把承载便捷 API 的类声明为 `partial class`。
  - 本体内**完全不出现**该 enum 类型 → 没有生成文件时也能独立编译。
- **生成文件（随数据/项目侧走）**：
  - `enum MyEnum { ... }` 本体；
  - 可选的扩展方法（如 `ToBase()` 把 enum 转底层值）；
  - `partial class Manager { public void Do(MyEnum x) => Do(x.ToBase()); }` —— 把便捷重载补回库的类。

编译期 partial 合并后，`Manager` 同时拥有底层 API（来自本体）和便捷重载（来自生成文件），调用方 `Manager.Do(MyEnum.Foo)` 照常解析。

#### 达到的两个目的

1. **缺席安全（避免没有枚举时函数调用/编译出错）**：库本体不引用 enum，缺生成文件也能编译；有生成文件时便捷 API 自动出现，调用方零改动。
2. **天然解耦**：可选类型与其专属 API 都在生成文件里，跟随数据/项目仓库；库本体保持纯净，与项目内容物理隔离，便于库的独立分发/同步。

#### 关键前提与坑

- **必须同一程序集**：partial class 可跨文件但**不可跨 assembly**。库的 partial 类、生成文件、调用方三者要在同一程序集。Unity 中没有 `.asmdef` 约束时它们同进 `Assembly-CSharp`；若库有独立 asmdef，则此法不成立（需另想，如接口/字符串方案）。
- **生成器模板必须同步产出 partial API 段**：否则下次「重新生成」只生成 enum、丢掉便捷重载，导致调用方编译失败。生成逻辑要把 enum + 扩展 + `partial class` 重载一次性写出。
- **保持类型形态不变以免破坏序列化**：让 enum 仍是 enum（值按整数序列化），已有 Inspector/资产里配置的值不丢。若把 enum 改成 string/struct，会破坏既有序列化数据，需配合 `ISerializationCallbackReceiver` 迁移，成本高。
- **依赖该类型的示例/消费脚本也要归生成侧**：库自带的、直接引用 enum 的示例脚本必须一并移到项目/生成侧，否则库本体又出现 enum 依赖，破坏「缺席可编译」。

### 关键代码

库本体（随库分发，不引用 MyEnum，可独立编译）：

```csharp
// Manager.cs —— 库本体
public partial class Manager   // partial：便捷重载由生成文件补回
{
    // 只提供不依赖可选类型的底层 API
    public void Do(string key) { /* 真正逻辑 */ }
}
```

生成文件（随数据/项目侧走，由代码生成器产出）：

```csharp
// MyEnum.Generated.cs —— 生成物，落在项目/数据目录
public enum MyEnum { None = 0, Foo, Bar }

public static class MyEnumExtensions
{
    public static string ToBase(this MyEnum e)
        => e == MyEnum.None ? string.Empty : e.ToString();
}

// 把便捷重载补回库的 Manager（同一程序集内 partial 合并）
public partial class Manager
{
    public void Do(MyEnum x) => Do(x.ToBase());
}
```

调用方（项目代码，写法不变）：

```csharp
manager.Do(MyEnum.Foo);   // 解析到生成文件的 partial 重载 → 内部转 base → 调底层 string 版
manager.Do("Foo");        // 直接走库本体底层 API
```

生成器要点：模板必须在生成 enum 的同时，把 `partial class Manager { Do(MyEnum) ... }` 段一并写出，保证重新生成后便捷 API 不丢失。

### 参考链接

- [C# 编译错误 CS0101（同命名空间重复定义）](https://learn.microsoft.com/en-us/dotnet/csharp/misc/cs0101) - enum 不能同名重复定义的依据
- [Unity Script Serialization](https://docs.unity3d.com/2022.2/Documentation/Manual/script-Serialization.html) - enum 改 string 会破坏序列化数据的背景

### 相关记录

- [EffectSystem 效果系统 - 代码审查与架构分析](./effect-system-code-review.md) - 本方案的落地对象；其 enum 调用本质是 string 驱动的便捷糖
- [配置表 ID 一键生成枚举](./config-id-enum-generator.md) - 同类「数据生成 enum 供编辑器选择」模式，运行时仍用稳定 ID/string 查找

### 验证记录

- [2026-06-29] 初次记录，来源：TAModule/EffectSystem 重构实践。EffectManager 改 partial、enum 与其重载外置到生成文件，Unity 2022.3 编译 + 运行时功能验证通过；调用方代码与枚举序列化值保持不变。

---

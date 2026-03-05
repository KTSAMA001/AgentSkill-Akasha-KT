# 角色/怪物材质统一管理

**标签**：#unity #shader #material #experience
**来源**：实践总结
**收录日期**：2026-03-05
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐
**适用版本**：Unity 2020.3+

## 概要

多种 Shader 之间的宏开关和参数切换需要统一管理，否则会导致配置混乱。

## 内容

### 问题场景

项目中存在多种 Shader（角色、怪物、特效等），每个 Shader 有不同的宏开关和参数：
- 手动配置容易出错
- 参数切换难以追踪
- 多人协作时配置不一致

### 解决方案

建立统一的材质管理模块：

1. **集中配置**
   - 所有角色/怪物材质创建走统一入口
   - 特殊参数设置由管理器控制

2. **宏开关管理**
   - 预设常用的宏组合
   - 通过枚举或配置表选择

3. **参数继承/覆盖**
   - 基础参数全局配置
   - 特殊个体可覆盖

### 实现建议

```csharp
// 示例：材质管理器接口
public interface IMaterialManager
{
    Material GetMaterial(string materialName);
    void SetKeyword(Material mat, string keyword, bool enable);
    void ApplyPreset(Material mat, MaterialPreset preset);
}
```

### 注意事项

- 管理器初始化时机要早于材质使用
- 考虑运行时材质实例的生命周期管理

### 验证记录

- [2025-03-31] 项目实践验证
- [2026-03-05] 从长期记录提取到阿卡西

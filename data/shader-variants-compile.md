# HLSL 着色器语言相关经验

> HLSL 着色器语言相关经验
> 
> 包含：数据类型、内置函数、语义、编译指令等


---
## Shader 变体（Shader Variants）详解

**标签**：#shader #experience #hlsl #shader-variants
**来源**：Technical_Artist_Technotes/TA零散知识
**收录日期**：2026-01-31
**来源日期**：2026-01-31
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐ (实践验证)

**问题/场景**：

什么是 Shader 变体？multi_compile 和 shader_feature 有什么区别？如何控制变体数量？

**核心概念**：

### 1. 什么是 Shader 变体

Shader 变体是根据不同的**平台、渲染管线、材质属性和宏定义**等因素生成的一组 Shader 程序。

- **编辑器中**：变体在运行时（Runtime）按需编译，未编译的部分显示为蓝色
- **打包时**：所有变体在打包过程中一次性编译完成
- **出包后**：不再进行编译，只能使用打包时已编译的变体

### 2. 如何产生变体

通过 `#pragma` 指令声明关键字：

```hlsl
// multi_compile：生成所有组合的变体
#pragma multi_compile _ _DEBUG _RELEASE

// shader_feature：只生成材质引用的变体
#pragma shader_feature _ALPHATEST_ON
#pragma shader_feature _SPECULARHIGHLIGHTS_OFF
```

### 3. multi_compile vs shader_feature

| 特性 | multi_compile | shader_feature |
|------|---------------|----------------|
| 变体生成 | 生成**所有**关键字组合 | 只生成**被材质引用**的组合 |
| 变体数量 | N 个声明 = 2^N 个变体 | 取决于实际使用 |
| 运行时切换 | ✅ 可通过 API 动态切换 | ❌ 出包后无法启用未打包的变体 |
| 适用场景 | 阴影开关、雾效等运行时需切换的功能 | 法线贴图、视差等编辑期确定的功能 |

**关键代码示例**：

```hlsl
// 声明关键字
#pragma shader_feature _ALPHATEST_ON
#pragma shader_feature _SPECULARHIGHLIGHTS_OFF

// 在代码中使用
#ifdef _ALPHATEST_ON
    clip(_AlphaClip);
#endif

#ifdef _SPECULARHIGHLIGHTS_OFF
    half3 spec = 0;
#else
    half3 spec = _SpecColor.rgb * _Specular * pow(...);
#endif
```

### 4. _local 后缀

```hlsl
// 普通声明：可被全局 API 修改
#pragma multi_compile _ _FOG_ON

// local 声明：只能通过 Material.EnableKeyword 修改
#pragma multi_compile_local _ _FOG_ON
#pragma shader_feature_local _NORMAL_MAP
```

**local 的作用**：
- 减少全局 Keyword 数量（早期 Unity 版本全局 Keyword 数量有限）
- `Shader.EnableKeyword`、`CommandBuffer.EnableKeyword` 对 local 关键字无效
- 只能通过 `Material.EnableKeyword` 控制

### 5. 变体数量计算

**multi_compile**：
```
N 个 multi_compile 声明 → 2^N 个变体
```

**shader_feature**：
```
打包时检查所有材质 → 只编译被引用的关键字组合
```

**最佳实践**：
- 运行时需要动态切换的功能 → `multi_compile`
- 编辑期确定、出包后不变的功能 → `shader_feature`
- 移除不必要的 multi_compile 可显著减少变体数量

### 6. shader_feature 的陷阱

如果 SVC（Shader Variant Collection）只包含特定变体，打包时可能丢失变体：

- **问题**：只含 VR 变体的 SVC，Unity 认为"当前平台未启用 VR"而剔除
- **解决**：使用双文件策略（一个完整 SVC 用于打包引用，一个精简 SVC 用于预热）

### 7. ASE 中使用变体

在 Amplify Shader Editor 中，使用 **Static Switch** 节点实现变体控制。

**验证记录**：

- [2026-01-31] 从 Technical_Artist_Technotes 整理提取

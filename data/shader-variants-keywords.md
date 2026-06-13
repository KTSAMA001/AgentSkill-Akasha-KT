# Shader 变体与关键字

**标签**：#unity #shader #knowledge #shader-variants
**来源**：Unity 官方文档 - Shader variants and keywords、TA 工程实践经验整理
**收录日期**：2026-02-01
**更新日期**：2026-06-13
**状态**：📘 有效
**可信度**：⭐⭐⭐⭐⭐ (官方文档 + 实践验证)
**适用版本**：Unity Shader / SRP

### 概要

Shader 变体是同一个 shader 因关键字组合不同而生成的多份编译结果；关键字组合越多，构建、包体和运行时加载成本越容易膨胀。

### 内容

Shader 变体的核心风险是组合爆炸。关键字越多，最终可能产生越多编译结果，进而影响：

- 构建时间。
- 包体或缓存大小。
- 运行时加载与切换成本。

#### 关键点

- 通用原则是能少开关键字就少开，能用更少组合表达需求就不要设计全排列。
- `multi_compile` 倾向于永远编译所有组合。
- `shader_feature` 倾向于只编译实际使用到的组合。
- 具体行为与 Unity 和渲染管线版本相关，需要以当前项目版本和打包结果为准。

### 关键代码

```hlsl
#pragma multi_compile _ _FOG_ON
#pragma shader_feature _NORMAL_MAP
```

### 相关记录

- [Unity Shader 关键字与变体基础](./unity-shader-keywords-variants-basics.md) - 从 HLSL 聚合记录拆出的关键字速记。
- [HLSL 着色器语言相关经验](./shader-variants-compile.md) - 更完整的 `multi_compile` / `shader_feature` 实践记录。

### 验证记录

- [2026-04-15] 旧聚合记录结构修复：补齐模板必填章节，未改动原结论。
- [2026-06-13] 结构维护：从旧聚合记录拆分，未重新验证原技术结论。

---

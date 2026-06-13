# Unity Shader 关键字与变体基础

**标签**：#unity #shader #knowledge #hlsl #shader-variants
**来源**：Unity 官方文档 - Shader variants and keywords
**收录日期**：2026-02-08
**更新日期**：2026-06-13
**状态**：📘 有效
**可信度**：⭐⭐⭐⭐⭐ (官方文档 + 实践验证)
**适用版本**：Unity Shader

### 概要

Unity Shader 关键字组合会生成多个编译变体，组合数量容易膨胀；应尽量用更少关键字表达需求。

### 内容

旧聚合记录保留了两条基础原则：

- 关键字组合会生成多个编译变体，组合数量容易爆炸。
- 通用原则是能少开就少开，用更少组合表达需求。

在 Unity 中，变体数量会影响构建时间、包体和运行时加载。对于运行时必须动态切换的功能、材质静态功能、平台差异和管线关键字，需要分别选择合适的声明方式，并用构建报告或变体收集结果验证最终数量。

### 关键代码

```hlsl
#pragma shader_feature _ALPHATEST_ON
#pragma multi_compile _ _MAIN_LIGHT_SHADOWS
```

### 相关记录

- [Shader 变体与关键字](./shader-variants-keywords.md) - 从渲染管线聚合记录拆出的概念版。
- [HLSL 着色器语言相关经验](./shader-variants-compile.md) - `multi_compile`、`shader_feature` 和 local 关键字的详细经验。
- [Unity 严格变体匹配与 Enum Keyword](./unity-strict-variant-matching-enum-keyword.md) - 变体匹配相关实践。

### 验证记录

- [2026-04-15] 旧聚合记录结构修复：补齐模板必填章节，未改动原结论。
- [2026-06-13] 结构维护：从旧聚合记录拆分，未重新验证原技术结论。

---

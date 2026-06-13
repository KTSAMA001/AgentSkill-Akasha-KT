# HLSL half / float 精度取舍

**标签**：#unity #shader #knowledge #hlsl #performance
**来源**：Unity 官方文档 - Shader data types、ARM Mali GPU 文档
**收录日期**：2026-02-08
**更新日期**：2026-06-13
**状态**：📘 有效
**可信度**：⭐⭐⭐⭐ (官方文档 + 实践验证)
**适用版本**：Unity Shader / 移动端 GPU

### 概要

移动端 shader 中常用 `half` 降低带宽或寄存器压力，但深度、世界坐标、矩阵运算等关键计算通常使用 `float` 更稳妥。

### 内容

旧聚合记录保留的核心原则：

- 移动端常用 `half` 以降低带宽或寄存器压力。
- 使用 `half` 时要注意精度问题。
- 深度、世界坐标、矩阵运算等关键计算通常使用 `float` 更安全。

工程判断不应只按类型名做静态规则，而要结合目标平台、shader 编译结果、画面误差和性能数据。对移动 GPU，`half` 的收益和风险都更值得关注；对桌面平台，具体收益可能受编译器和硬件实现影响。

### 关键代码

```hlsl
half3 albedo = SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, uv).rgb;
float3 positionWS = TransformObjectToWorld(positionOS);
```

### 相关记录

- [Shader 优化 HLSL](./shader-optimization-hlsl.md) - HLSL 性能优化经验。
- [移动端 TBDR 与 Overdraw](./mobile-tbdr-overdraw.md) - 移动端性能背景。

### 验证记录

- [2026-04-15] 旧聚合记录结构修复：补齐模板必填章节，未改动原结论。
- [2026-06-13] 结构维护：从旧聚合记录拆分，未重新验证原技术结论。

---

# Unity Shader / HLSL 基础知识

<!-- 
修改记录：
- [2026-01-30] 补充来源和可信度标注，确保知识条目符合规范。
- [2026-01-31] 将 TA 笔记中的 HLSL/Shader 常用概念（语义、varying、CBUFFER、关键字/变体、精度选择）整理为可复用的知识卡片，方便写 Shader 与排查渲染问题。
-->

本文档聚焦 Unity Shader 里最常用的 HLSL 概念与工程习惯。

---

## 顶点/片元阶段与数据流

**分类**：HLSL > 基础
**关键词**：#vertex #fragment #varyings #interpolation
**来源**：Microsoft HLSL 文档、Unity Shader 官方文档
**可信度**：⭐⭐⭐⭐⭐ (官方文档)

- 顶点阶段输出：`SV_POSITION` + 自定义 varyings。
- 片元阶段输入：对 varyings 的插值结果（屏幕覆盖越大执行越多）。

---

## 语义（Semantics）

**分类**：HLSL > 语法
**关键词**：#semantics #SV_POSITION
**来源**：Microsoft HLSL 文档、Unity ShaderLab 文档
**可信度**：⭐⭐⭐⭐⭐ (官方文档)

常见：
- `POSITION`：顶点输入位置（对象空间）
- `NORMAL` / `TANGENT`：顶点法线/切线
- `TEXCOORD0..n`：UV/自定义插值通道
- `SV_POSITION`：裁剪空间位置（顶点输出/片元输入）

---

## CBUFFER（Constant Buffer）与参数组织

**分类**：HLSL > 性能
**关键词**：#CBUFFER #UnityPerMaterial #SRPBatcher
**来源**：Unity 官方博客 - SRP Batcher、Microsoft HLSL 文档
**可信度**：⭐⭐⭐⭐⭐ (官方文档 + 实践验证)

- CBUFFER 是 GPU 侧常量数据块。
- SRP Batcher 通常要求材质参数在约定的 CBUFFER 中组织（例如 `UnityPerMaterial`），以便更稳定地提交。

---

## 精度选择（float/half）

**分类**：HLSL > 性能
**关键词**：#float #half #mobile
**来源**：Unity 官方文档 - Shader data types、ARM Mali GPU 文档
**可信度**：⭐⭐⭐⭐ (官方文档 + 实践验证)

- 移动端常用 `half` 以降低带宽/寄存器压力（但要注意精度问题）。
- 关键计算（深度、世界坐标、矩阵运算等）通常需要 `float` 更安全。

---

## 关键字与变体

**分类**：HLSL > 性能
**关键词**：#keyword #shader-variant #multi_compile #shader_feature
**来源**：Unity 官方文档 - Shader variants and keywords
**可信度**：⭐⭐⭐⭐⭐ (官方文档 + 实践验证)

- 关键字组合会生成多个编译变体，组合数量容易爆炸。
- 通用原则：能少开就少开；用更少组合表达需求。

---

## 关联知识

- 渲染管线基础：../graphics/rendering-pipeline.md

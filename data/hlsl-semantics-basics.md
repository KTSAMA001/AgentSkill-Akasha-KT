# HLSL 语义基础

**标签**：#graphics #shader #knowledge #hlsl
**来源**：Microsoft HLSL 文档、Unity ShaderLab 文档
**收录日期**：2026-02-08
**更新日期**：2026-06-13
**状态**：📘 有效
**可信度**：⭐⭐⭐⭐⭐ (官方文档)
**适用版本**：Unity Shader / HLSL

### 概要

HLSL 语义用于告诉图形管线某个结构体字段的用途，例如顶点位置、法线、UV 或裁剪空间输出位置。

### 内容

常见语义：

| 语义 | 常见用途 |
|---|---|
| `POSITION` | 顶点输入位置，通常是对象空间位置 |
| `NORMAL` | 顶点法线 |
| `TANGENT` | 顶点切线 |
| `TEXCOORD0..n` | UV 或自定义插值通道 |
| `SV_POSITION` | 裁剪空间位置，常用于顶点输出和片元输入 |

`TEXCOORDn` 不只用于纹理坐标，也常被用作自定义 varyings 通道。工程中需要保持顶点输出和片元输入结构体的语义、类型和插值用途一致。

### 关键代码

```hlsl
struct Attributes
{
    float3 positionOS : POSITION;
    float3 normalOS : NORMAL;
    float2 uv : TEXCOORD0;
};
```

### 相关记录

- [HLSL 顶点/片元数据流](./hlsl-vertex-fragment-dataflow.md) - 语义在顶点输出和片元输入中的位置。
- [Shader 法线空间变换](./shader-normal-space-transformation.md) - 法线相关语义与空间变换实践。

### 验证记录

- [2026-04-15] 旧聚合记录结构修复：补齐模板必填章节，未改动原结论。
- [2026-06-13] 结构维护：从旧聚合记录拆分，未重新验证原技术结论。

---

# HLSL 顶点/片元数据流

**标签**：#graphics #shader #knowledge #hlsl
**来源**：Microsoft HLSL 文档、Unity Shader 官方文档
**收录日期**：2026-02-08
**来源日期**：2026-02-08
**更新日期**：2026-06-13
**状态**：📘 有效
**可信度**：⭐⭐⭐⭐⭐ (官方文档)
**适用版本**：Unity Shader / HLSL

### 概要

HLSL 中顶点阶段输出 `SV_POSITION` 和自定义 varyings，片元阶段接收这些 varyings 的插值结果并执行逐片元计算。

### 内容

顶点阶段和片元阶段之间的核心连接是“顶点输出被光栅化插值后成为片元输入”。

- 顶点阶段输出：`SV_POSITION` 和自定义 varyings。
- 片元阶段输入：对 varyings 的插值结果。
- 屏幕覆盖越大，片元阶段执行次数越多。

在 Unity Shader 中，这通常体现为两个结构体：一个用于顶点输入，一个用于顶点到片元的输出/输入桥接。`SV_POSITION` 用于告诉管线顶点最终位于裁剪空间中的位置，自定义 `TEXCOORDn` 则承载 UV、法线、世界坐标等插值数据。

### 关键代码

```hlsl
struct Attributes
{
    float3 positionOS : POSITION;
    float2 uv : TEXCOORD0;
};

struct Varyings
{
    float4 positionCS : SV_POSITION;
    float2 uv : TEXCOORD0;
};
```

### 相关记录

- [Shader 阶段：顶点与片元](./shader-stage-vertex-fragment.md) - 图形管线语境下的顶点/片元阶段职责。
- [HLSL 语义基础](./hlsl-semantics-basics.md) - 结构体字段后的语义解释。

### 验证记录

- [2026-04-15] 旧聚合记录结构修复：补齐模板必填章节，未改动原结论。
- [2026-06-13] 结构维护：从旧聚合记录拆分，未重新验证原技术结论。

---

# HLSL CBUFFER 与 SRP Batcher 基础

**标签**：#unity #shader #knowledge #hlsl #srp-batcher
**来源**：Unity 官方博客 - SRP Batcher、Microsoft HLSL 文档
**收录日期**：2026-02-08
**更新日期**：2026-06-13
**状态**：📘 有效
**可信度**：⭐⭐⭐⭐⭐ (官方文档 + 实践验证)
**适用版本**：Unity SRP / URP / HLSL

### 概要

CBUFFER 是 GPU 侧常量数据块；Unity SRP Batcher 通常要求材质参数按约定的 CBUFFER 组织，以便稳定提交。

### 内容

CBUFFER 用于把一组 uniform 或常量参数组织成 GPU 可高效读取的数据块。旧聚合记录中的核心结论是：

- CBUFFER 是 GPU 侧常量数据块。
- SRP Batcher 通常要求材质参数在约定的 CBUFFER 中组织。
- Unity 常见约定名是 `UnityPerMaterial`。

该记录只保留基础概念；具体布局、版本差异和项目验证仍应以当前 Unity/URP 版本与 Frame Debugger、Profiler 结果为准。

### 关键代码

```hlsl
CBUFFER_START(UnityPerMaterial)
    half4 _BaseColor;
    float _Cutoff;
CBUFFER_END
```

### 相关记录

- [SRP Batcher 与 CBUFFER](./srp-batcher-cbuffer.md) - 从渲染管线聚合记录拆出的更完整说明。
- [SRP Batcher 场景优化要点](./srp-batcher-optimization.md) - 场景优化实践记录。

### 验证记录

- [2026-04-15] 旧聚合记录结构修复：补齐模板必填章节，未改动原结论。
- [2026-06-13] 结构维护：从旧聚合记录拆分，未重新验证原技术结论。

---

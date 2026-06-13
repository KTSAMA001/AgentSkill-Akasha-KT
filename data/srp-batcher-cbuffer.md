# SRP Batcher 与 CBUFFER

**标签**：#unity #shader #knowledge #srp #srp-batcher
**来源**：Unity 官方博客 - SRP Batcher: Speed up your rendering、关于 SRP/URP 的研究
**收录日期**：2026-02-01
**更新日期**：2026-06-13
**状态**：📘 有效
**可信度**：⭐⭐⭐⭐ (官方博客 + 实践验证)
**适用版本**：Unity SRP / URP

### 概要

CBUFFER 是 GPU 侧常量数据块；在 Unity SRP Batcher 语境下，材质参数布局是否稳定会直接影响批处理收益。

### 内容

CBUFFER（Constant Buffer）可以理解为 GPU 侧的“常量数据块”，用于高效地把一组 uniform 或常量参数传给 shader。

在 Unity SRP 语境下，SRP Batcher 会尝试把渲染中可批处理的部分按更稳定的方式提交给 GPU。一个关键前提是 shader 常量数据布局要符合 SRP Batcher 的要求，典型表现为使用 `UnityPerMaterial` 等约定的 CBUFFER 组织材质参数。

#### 工程要点

- 频繁改动经常变化的参数，可能破坏批处理收益；具体影响取决于管线和平台实现。
- 设计材质参数时，尽量区分稳定参数与高频变化参数，例如全局、每相机、每物体、每材质。
- `MaterialPropertyBlock` 常用于 per-renderer 参数覆写，但滥用也可能影响合批与提交效率，需要结合实际渲染路径验证。

### 关键代码

```hlsl
CBUFFER_START(UnityPerMaterial)
    half4 _Color;
    half _Roughness;
CBUFFER_END
```

### 相关记录

- [HLSL CBUFFER 与 SRP Batcher 基础](./hlsl-cbuffer-srp-batcher-basics.md) - HLSL 语境下的 CBUFFER 速记版本。
- [Draw Call、合批与 Instancing](./draw-call-batching-instancing.md) - 批处理优化的上层概念。
- [SRP Batcher 场景优化要点](./srp-batcher-optimization.md) - 场景侧优化经验。

### 验证记录

- [2026-04-15] 旧聚合记录结构修复：补齐模板必填章节，未改动原结论。
- [2026-06-13] 结构维护：从旧聚合记录拆分，未重新验证原技术结论。

---

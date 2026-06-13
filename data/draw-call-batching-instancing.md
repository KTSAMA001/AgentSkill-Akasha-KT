# Draw Call、合批与 Instancing

**标签**：#graphics #knowledge #draw-call #performance
**来源**：Unity 官方文档 - Optimizing draw calls、TA 工程实践经验整理
**收录日期**：2026-02-01
**更新日期**：2026-06-13
**状态**：📘 有效
**可信度**：⭐⭐⭐⭐ (官方文档 + 实践验证)
**适用版本**：Unity / 通用实时渲染优化

### 概要

Draw Call 是 CPU 向 GPU 提交绘制命令的行为；合批和 GPU Instancing 都是在特定约束下减少提交开销的手段。

### 内容

#### 基本概念

- **Draw Call**：CPU 向 GPU 提交一次绘制命令的行为。一次提交不等于一次三角形。
- **Batching（合批）**：把多个对象的绘制合并成更少的 Draw Call，代价通常是需要一致的渲染状态，并受到更多限制。
- **GPU Instancing**：在一次 Draw Call 中绘制同一 mesh/material 的多个实例，通过 per-instance 数据区分实例差异。

#### 性能判断

CPU 侧瓶颈常表现为 Draw Call 过多；GPU 侧瓶颈常表现为 overdraw、shader 太重、像素覆盖太大。优化时需要先判断瓶颈侧，不应只盯着 Draw Call 数量。

#### 合批的副作用

过度合批也可能带来问题：

- 顶点数据变大。
- 剔除粒度变粗。
- 材质灵活性下降。
- 对状态和资源布局有更多约束。

### 相关记录

- [SRP Batcher 与 CBUFFER](./srp-batcher-cbuffer.md) - Unity SRP 中与提交效率相关的常量布局约束。
- [渲染管线三大阶段](./rendering-pipeline-stages.md) - Draw Call 位于应用阶段提交链路。
- [SRP Batcher 场景优化要点](./srp-batcher-optimization.md) - 项目优化经验中的 Batcher 数量控制。

### 验证记录

- [2026-04-15] 旧聚合记录结构修复：补齐模板必填章节，未改动原结论。
- [2026-06-13] 结构维护：从旧聚合记录拆分，未重新验证原技术结论。

---

# URP Renderer Feature 扩展点要点

**标签**：#unity #graphics #knowledge #urp #srp #renderer-feature
**来源**：Unity 官方文档 - Custom Renderer Feature、URP 工程实践
**收录日期**：2026-01-30
**来源日期**：-
**更新日期**：2026-06-13
**状态**：📘 有效
**可信度**：⭐⭐⭐⭐⭐ (官方文档 + 实践验证)
**适用版本**：Unity URP（原记录未限定具体版本）

### 概要

Renderer Feature 是 URP 中注入自定义 Pass 的主要入口。工程上需要重点关注 `RenderPassEvent` 插入时机、RenderTarget 生命周期以及 Pass 之间的排序和依赖。

### 内容

Renderer Feature 的要点：

- 关注 Pass 插入时机（`RenderPassEvent`）：不同时机影响与后处理、透明队列、深度纹理等的交互。
- 关注 RenderTarget 分配/释放：临时 RT、RTHandles、分辨率变化、Camera stacking 等都会影响资源生命周期。
- 关注排序与依赖：Pass 之间的输入输出（深度、颜色、mask RT）要明确，避免隐式依赖。

实践检查项：

- 自定义 Pass 是否明确声明读写的颜色、深度或临时纹理。
- 注入点是否位于所需数据生成之后，例如深度纹理或不透明颜色纹理。
- 是否在相机分辨率、渲染缩放或 Camera stacking 变化时正确处理资源重分配。
- 是否为关键 Pass 添加 profiling，便于定位 CPU/GPU 开销。

### 关键代码

不涉及。

### 相关记录

- [URP 核心 Renderer/Pass/Feature 架构](./urp-core-renderer-pass-feature-architecture.md) - Renderer Feature 所处的结构层级。
- [URP ForwardRenderer Setup 流程](./urp-forward-renderer-setup-flow.md) - RendererFeature 参与 Pass 队列构建的位置。

### 验证记录

- [2026-04-15] 结构修复：补齐模板必填章节，未改动原结论。
- [2026-06-13] 结构维护：从旧聚合记录拆分，未重新验证原技术结论。

---

# CommandBuffer 在 URP 中的角色

**标签**：#unity #graphics #knowledge #urp #srp #rendering-pipeline
**来源**：Unity 官方文档 - CommandBuffer、URP 源码分析
**收录日期**：2026-01-30
**来源日期**：-
**更新日期**：2026-06-13
**状态**：📘 有效
**可信度**：⭐⭐⭐⭐⭐ (官方文档 + 源码验证)
**适用版本**：Unity URP（原记录未限定具体版本）

### 概要

CommandBuffer 是 URP Pass 中录制和提交渲染命令的常见载体。多个绘制或状态设置命令可以进入同一个 CommandBuffer，再由渲染上下文按顺序执行。

### 内容

原记录中的核心结论：

- 每次绘制都是一次命令。
- 多个绘制命令可以 push 到同一个 CommandBuffer。
- 执行 CommandBuffer 时，GPU 按顺序执行命令。
- CommandBuffer 可用于定制想要的渲染效果。

在 URP 工程中，RenderPass 通常会构建命令并提交执行。命令过多会带来 CPU 开销，因此建议在关键 Pass 上加 profiling 点，确认瓶颈位置。

### 关键代码

不涉及。

### 相关记录

- [URP 渲染入口与 RenderSingleCamera 流程](./urp-render-entry-render-single-camera-flow.md) - 相机渲染流程中 CommandBuffer 获取、执行和释放的位置。
- [URP ForwardRenderer Setup 流程](./urp-forward-renderer-setup-flow.md) - CommandBuffer 与 Pass 队列执行之间的关系。

### 验证记录

- [2026-04-15] 结构修复：补齐模板必填章节，未改动原结论。
- [2026-06-13] 结构维护：从旧聚合记录拆分，未重新验证原技术结论。

---

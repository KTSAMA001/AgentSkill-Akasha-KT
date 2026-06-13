# Unity SRP 可编程渲染管线概念概览

**标签**：#unity #graphics #knowledge #srp #rendering-pipeline
**来源**：Unity 官方文档 - Scriptable Render Pipeline
**收录日期**：2026-01-30
**来源日期**：-
**更新日期**：2026-06-13
**状态**：📘 有效
**可信度**：⭐⭐⭐⭐⭐ (官方文档)
**适用版本**：Unity SRP / URP（原记录未限定具体版本）

### 概要

SRP 是 Unity 的可编程渲染管线体系，用 C# 组织渲染循环、渲染状态、目标和执行顺序。本记录只保留 SRP 概念层说明，URP 具体 Renderer/Pass/Feature 结构拆到关联记录。

### 内容

SRP（Scriptable Render Pipeline）的核心价值是把过去内置管线中较封闭的渲染流程，改成可由项目或管线包控制的 render loop。

关键理解点：

- SRP 用 C# 组织“何时画什么、用哪些 render states/targets、执行顺序”。
- 与内置管线相比，SRP 更强调可定制的 render loop。
- 渲染阶段的边界更明确，项目可以围绕渲染目标、Pass 顺序、相机流程和后处理流程做工程化扩展。

### 关键代码

不涉及。

### 相关记录

- [渲染管线基础](./rendering-pipeline-stages.md) - 更基础的渲染管线概念背景。
- [URP 核心 Renderer/Pass/Feature 架构](./urp-core-renderer-pass-feature-architecture.md) - SRP 在 URP 工程结构中的落点。

### 验证记录

- [2026-04-15] 结构修复：补齐模板必填章节，未改动原结论。
- [2026-06-13] 结构维护：从旧聚合记录拆分，未重新验证原技术结论。

---

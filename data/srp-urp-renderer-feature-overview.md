# SRP / URP 与 Renderer Feature 概览

**标签**：#unity #graphics #knowledge #srp #urp #renderer-feature
**来源**：Unity 官方文档 - Universal Render Pipeline、关于 SRP/URP 的研究
**收录日期**：2026-02-01
**更新日期**：2026-06-13
**状态**：📘 有效
**可信度**：⭐⭐⭐⭐⭐ (官方文档 + 实践验证)
**适用版本**：Unity URP / SRP

### 概要

SRP 是 Unity 的可编程渲染管线体系；URP 是官方 SRP 实现之一；Renderer Feature 是 URP 中插入自定义渲染逻辑的重要扩展点。

### 内容

#### 基本概念

- **SRP（Scriptable Render Pipeline）**：Unity 可编程渲染管线体系，允许用 C# 组织渲染流程。
- **URP（Universal Render Pipeline）**：Unity 官方提供的 SRP 之一，目标是跨平台和移动端友好。
- **Renderer Feature**：URP 的扩展点，通常通过 `ScriptableRendererFeature` 注入一个或多个 `ScriptableRenderPass`，从而在指定时机插入自定义渲染逻辑。

#### 工程关注点

Renderer Feature 更像渲染流程插件，需要明确：

- 注入时机，例如 render pass event。
- 资源配置，例如 RT、材质、临时纹理。
- 执行动作，例如绘制、Blit、清理。
- 与后处理、透明队列、深度纹理、相机目标的交互。

设计 Feature 时，应特别关注 RT 分配、清理策略、Pass 执行顺序，以及是否会引入额外全屏拷贝或移动端带宽压力。

### 相关记录

- [CommandBuffer 与渲染命令录制](./command-buffer-render-commands.md) - RenderPass 内部常围绕命令录制与执行组织。
- [URP Renderer Feature 开发要点](./urp-renderer-feature-guide.md) - 已验证的 Renderer Feature 实践记录。
- [URP RenderFeature 自定义后处理完整案例](./urp-renderfeature-postprocess-case-dual-kawase-bloom.md) - 自定义后处理案例。

### 验证记录

- [2026-04-15] 旧聚合记录结构修复：补齐模板必填章节，未改动原结论。
- [2026-06-13] 结构维护：从旧聚合记录拆分，未重新验证原技术结论。

---

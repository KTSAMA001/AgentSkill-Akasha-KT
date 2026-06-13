# URP 核心 Renderer / Pass / Feature 架构

**标签**：#unity #graphics #knowledge #urp #srp #renderer-feature #rendering-pipeline
**来源**：Unity 官方文档 - Universal Render Pipeline、URP 源码分析
**收录日期**：2026-01-30
**来源日期**：-
**更新日期**：2026-06-13
**状态**：📘 有效
**可信度**：⭐⭐⭐⭐⭐ (官方文档 + 源码验证)
**适用版本**：Unity URP（原记录未限定具体版本）

### 概要

URP 的工程结构可以用 `ScriptableRenderer`、`ScriptableRenderPass`、`ScriptableRendererFeature` 三个角色理解：Renderer 负责调度，Pass 负责实际渲染工作，Feature 负责把自定义 Pass 注入 Renderer。

### 内容

常见理解方式：

- `ScriptableRenderer`：一次 Camera 渲染的调度者/编排者，决定 Pass 的队列与执行。
- `ScriptableRenderPass`：真正执行渲染工作的单元，例如绘制、Blit、设置 RenderTarget、清屏等。
- `ScriptableRendererFeature`：把自定义 Pass 注入 Renderer 的扩展点，更像插件入口。

工程上可以把三者分层理解：

| 角色 | 责任 | 常见关注点 |
|------|------|------------|
| `ScriptableRenderer` | 组织相机渲染流程和 Pass 队列 | Pass 顺序、相机数据、RenderTarget 生命周期 |
| `ScriptableRenderPass` | 执行一段具体渲染任务 | 输入输出纹理、命令提交、profiling |
| `ScriptableRendererFeature` | 创建并注入自定义 Pass | 注入时机、可配置参数、资源释放 |

### 关键代码

不涉及。

### 相关记录

- [Unity SRP 可编程渲染管线概念概览](./unity-srp-concept-overview.md) - SRP 概念层背景。
- [URP Renderer Feature 扩展点要点](./urp-renderer-feature-extension-points.md) - Feature 层实践要点。
- [URP ForwardRenderer Setup 流程](./urp-forward-renderer-setup-flow.md) - Renderer 如何组织内置 Pass。

### 验证记录

- [2026-04-15] 结构修复：补齐模板必填章节，未改动原结论。
- [2026-06-13] 结构维护：从旧聚合记录拆分，未重新验证原技术结论。

---

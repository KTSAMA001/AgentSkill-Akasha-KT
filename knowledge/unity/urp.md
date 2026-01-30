# URP / SRP 知识

<!-- 
修改记录：
- [2026-01-31] 从 TA 笔记中抽取 SRP/URP 的核心结构与扩展点（Renderer Feature/RenderPass），用于后续做渲染功能开发与性能排查时快速对照。
-->

本文档记录 Unity SRP/URP 的核心概念与常用扩展点，偏“原理 + 工程要点”。

---

## SRP（Scriptable Render Pipeline）是什么

**关键词**：#SRP #render-loop #ScriptableRenderContext

- SRP 是 Unity 的可编程渲染管线体系：用 C# 组织“何时画什么、用哪些 render states/targets、执行顺序”。
- 与内置管线相比，SRP 更强调“可定制的 render loop”和更明确的渲染阶段划分。

---

## URP 的核心结构（工程视角）

**关键词**：#URP #ScriptableRenderer #ScriptableRenderPass #RendererFeature

常见理解方式：

- `ScriptableRenderer`：一次 Camera 渲染的“调度者/编排者”，决定 Pass 的队列与执行。
- `ScriptableRenderPass`：真正执行渲染工作的单元（绘制、Blit、设置 RT、清屏等）。
- `ScriptableRendererFeature`：把自定义 Pass 注入到 Renderer 的扩展点（更像插件入口）。

---

## Renderer Feature 的要点

**关键词**：#RendererFeature #RenderPassEvent #RT

- 关注 Pass 插入时机（`RenderPassEvent`）：不同时机影响与后处理、透明队列、深度纹理等的交互。
- 关注 RT 分配/释放：临时 RT、RTHandles、分辨率变化、Camera stacking 等都会影响资源生命周期。
- 关注排序与依赖：Pass 之间的输入输出（深度、颜色、mask RT）要明确，避免隐式依赖。

---

## CommandBuffer（命令录制）在 URP 中的角色

**关键词**：#CommandBuffer #profiling

- RenderPass 通常会构建命令并提交执行；命令过多会带来 CPU 开销。
- 建议在关键 Pass 上加 profiling（CPU/GPU）点，确认瓶颈位置。

---

## 关联知识

- 渲染管线基础：../graphics/rendering-pipeline.md

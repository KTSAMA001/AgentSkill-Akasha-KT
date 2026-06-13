# CommandBuffer 与渲染命令录制

**标签**：#unity #graphics #knowledge #srp #rendering
**来源**：Unity 官方文档 - CommandBuffer、关于 SRP/URP 的研究
**收录日期**：2026-02-01
**更新日期**：2026-06-13
**状态**：📘 有效
**可信度**：⭐⭐⭐⭐⭐ (官方文档 + 实践验证)
**适用版本**：Unity SRP / URP

### 概要

CommandBuffer 用于先录制 GPU 绘制和状态切换命令，再在指定时机提交执行；SRP/URP 的 RenderPass 经常围绕它组织渲染逻辑。

### 内容

CommandBuffer 可以理解为“把要做的 GPU 绘制、资源绑定、状态切换等命令先录下来，再在特定时机提交执行”的命令列表。

#### 主要收益

- 将渲染逻辑与执行时机解耦。
- 更容易插入自定义 pass。
- 便于在 SRP/URP 中排序和复用一组渲染命令。

#### 风险点

- 命令录制过多或过重会带来 CPU 侧开销。
- RT 和临时资源生命周期管理不当会造成内存与性能问题。
- 自定义 pass 的执行顺序错误可能影响深度、透明、后处理或相机目标内容。

### 相关记录

- [SRP / URP 与 Renderer Feature 概览](./srp-urp-renderer-feature-overview.md) - CommandBuffer 常用于 Renderer Feature 和 RenderPass 实现。
- [URP Renderer Feature 开发要点](./urp-renderer-feature-guide.md) - CommandBuffer 在 URP Feature 中的实践示例。

### 验证记录

- [2026-04-15] 旧聚合记录结构修复：补齐模板必填章节，未改动原结论。
- [2026-06-13] 结构维护：从旧聚合记录拆分，未重新验证原技术结论。

---

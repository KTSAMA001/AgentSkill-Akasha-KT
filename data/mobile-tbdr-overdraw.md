# 移动端 TBDR 与 Overdraw

**标签**：#graphics #knowledge #performance #rendering
**来源**：ARM/Qualcomm GPU 官方文档、图形学/移动端渲染笔记
**收录日期**：2026-02-01
**更新日期**：2026-06-13
**状态**：📘 有效
**可信度**：⭐⭐⭐⭐ (厂商文档 + 实践验证)
**适用版本**：移动端 Tile-Based GPU / Unity 移动渲染

### 概要

TBDR 通过 tile 化和片上缓存降低移动端带宽压力；Overdraw 则会让同一像素被重复绘制，是移动端透明和粒子效果的常见成本来源。

### 内容

#### TBDR

TBDR（Tile-Based Deferred Rendering）是移动端常见 GPU 架构或渲染策略之一。它将屏幕拆成 tile，在片上缓存中尽量完成一个 tile 的可见性与着色，以减少外部显存带宽。

#### Overdraw

Overdraw 指同一个像素被多次绘制。透明叠加、粒子、大面积特效和全屏后处理都可能导致重复着色与带宽浪费。

#### 工程要点

- TBDR 的收益依赖带宽压力和渲染目标读写模式。
- 过多 RT 切换、过重后处理、过高分辨率都会放大移动端成本。
- 透明和粒子通常是 overdraw 大户，屏幕覆盖面积越大，像素成本越高。

### 相关记录

- [移动 GPU 渲染术语速查](./mobile-gpu-terms-tbr-gmem-backbuffer-glossary.md) - TBR/GMEM/backbuffer/Load-Store 等术语详解。
- [不透明与透明排序](./opaque-transparent-sorting.md) - 透明排序与 overdraw 关系。
- [URP 内置 Bloom vs 自定义 Dual Kawase 性能对比](./urp-builtin-bloom-vs-dual-kawase-renderfeature-performance.md) - 移动 VR 后处理带宽语境。

### 验证记录

- [2026-04-15] 旧聚合记录结构修复：补齐模板必填章节，未改动原结论。
- [2026-06-13] 结构维护：从旧聚合记录拆分，未重新验证原技术结论。

---

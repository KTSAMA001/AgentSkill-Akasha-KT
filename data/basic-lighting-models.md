# 基础光照模型：Lambert / Phong / Blinn-Phong

**标签**：#graphics #shader #knowledge #rendering
**来源**：《Real-Time Rendering》、图形学基础课程
**收录日期**：2026-02-01
**更新日期**：2026-06-13
**状态**：📘 有效
**可信度**：⭐⭐⭐⭐⭐ (权威著作 + 学术标准)
**适用版本**：通用实时渲染

### 概要

Lambert、Phong、Blinn-Phong 是理解实时光照的基础模型，分别覆盖漫反射和经典镜面高光近似。

### 内容

#### Lambert 漫反射

Lambert 的核心是表面越朝向光源越亮。常见形式：

```text
I_d ∝ max(0, N · L)
```

其中 `N` 是表面法线，`L` 是指向光源的方向。

#### Phong 镜面高光

Phong 使用反射向量 `R` 与视线方向 `V` 的夹角决定高光。常见形式：

```text
I_s ∝ max(0, R · V)^n
```

`n` 越大，高光越尖锐。

#### Blinn-Phong 镜面高光

Blinn-Phong 使用半角向量 `H = normalize(L + V)` 替代反射向量，计算更稳定，成本通常更低。常见形式：

```text
I_s ∝ max(0, N · H)^n
```

### 相关记录

- [Shader 阶段：顶点与片元](./shader-stage-vertex-fragment.md) - 光照计算通常在顶点或片元阶段执行。
- [PBR / BRDF 基本要点](./pbr-brdf-basics.md) - 更现代的物理材质与反射模型基础。

### 验证记录

- [2026-04-15] 旧聚合记录结构修复：补齐模板必填章节，未改动原结论。
- [2026-06-13] 结构维护：从旧聚合记录拆分，未重新验证原技术结论。

---

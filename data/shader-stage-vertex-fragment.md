# Shader 阶段：顶点与片元

**标签**：#graphics #shader #knowledge #rendering-pipeline #hlsl
**来源**：《Unity Shader 入门精要》（冯乐乐著）
**收录日期**：2026-02-01
**更新日期**：2026-06-13
**状态**：📘 有效
**可信度**：⭐⭐⭐⭐⭐ (经典著作 + 广泛认可)
**适用版本**：通用实时渲染管线 / Unity Shader

### 概要

顶点着色器负责逐顶点处理和空间变换，片元着色器负责逐片元计算最终颜色；二者之间通过可插值数据连接。

### 内容

#### 顶点着色器

顶点着色器对每个顶点执行一次，核心职责是把顶点从对象空间变换到裁剪空间，并输出后续阶段需要的插值数据。

常见输入：

- position
- normal
- tangent
- uv
- color
- skin weights

常见输出：

- `SV_POSITION`：裁剪空间坐标。
- 自定义 varyings：供光栅化后插值到片元阶段，例如 UV、法线、颜色、世界坐标。

关键点：

- 顶点阶段不直接画出像素，它产出的是后续阶段可插值的属性。
- 常见坐标链路是 Object -> World -> View -> Clip，也常被合并为 MVP 矩阵。

#### 片元着色器

片元着色器对每个片元或像素候选执行一次，负责计算该像素的最终颜色，也可能输出深度或多渲染目标数据。

常见工作：

- 纹理采样，例如 Albedo、Normal、Mask。
- 光照计算，例如 Lambert、Phong、Blinn-Phong、PBR。
- 透明裁剪，例如 `discard` 或 alpha test。
- 输出颜色到 Render Target。

关键点：

- 片元着色器执行次数与屏幕覆盖率强相关，铺满屏幕的对象通常更贵。
- 能利用 Early-Z 时，应避免不必要地写深度或大量 `discard`，因为这些行为可能影响提前深度测试收益。

### 相关记录

- [HLSL 顶点/片元数据流](./hlsl-vertex-fragment-dataflow.md) - Unity/HLSL 语境下的结构体与 varyings 数据流。
- [HLSL 语义基础](./hlsl-semantics-basics.md) - `POSITION`、`TEXCOORD`、`SV_POSITION` 等语义。
- [基础光照模型](./basic-lighting-models.md) - 片元阶段常见光照计算。

### 验证记录

- [2026-04-15] 旧聚合记录结构修复：补齐模板必填章节，未改动原结论。
- [2026-06-13] 结构维护：从旧聚合记录拆分，未重新验证原技术结论。

---

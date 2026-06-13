# GPU 缓冲对象：VBO / EBO / VAO

**标签**：#graphics #knowledge #rendering-pipeline #rendering
**来源**：OpenGL 官方规范、关于 SRP/URP 的研究
**收录日期**：2026-02-01
**更新日期**：2026-06-13
**状态**：📘 有效
**可信度**：⭐⭐⭐⭐⭐ (官方规范 + 实践验证)
**适用版本**：OpenGL 语境；Unity/现代图形 API 可类比理解

### 概要

VBO、EBO、VAO 是 OpenGL 语境下组织顶点数据、索引数据和输入布局的经典术语，本质上描述的是 GPU 如何读取几何数据。

### 内容

#### 核心概念

**VBO（Vertex Buffer Object，顶点缓冲对象）**

VBO 是显存中的一块区域，用于保存模型顶点属性，例如位置、UV、法线、切线等。GPU 可以直接从显存读取这些数据，避免绘制时从 CPU 普通内存逐项读取。

**EBO（Element Buffer Object，索引缓冲对象）**

EBO 保存顶点索引数组，用于指定顶点的绘制顺序。使用索引可以复用顶点数据，减少重复顶点带来的内存占用。

**VAO（Vertex Array Object，顶点数组对象）**

VAO 保存顶点属性如何从 VBO/EBO 中读取的信息，例如属性起始位置、步长、格式和绑定关系。它不是主要数据存储，而是顶点输入布局的组织者。

#### 关系

```text
VAO (输入布局/组织方式)
├── VBO (顶点属性数据)
│   ├── 顶点位置
│   ├── 顶点法线
│   ├── 顶点 UV
│   └── 顶点切线
└── EBO (索引数据)
    └── 顶点索引数组
```

#### Unity 与现代图形 API 中的对应关系

VBO/EBO/VAO 属于 OpenGL 语境的经典说法。在 Unity、D3D12、Vulkan、Metal 等现代图形 API 中，更常见的表达是 Vertex Buffer、Index Buffer、Input Layout 或 Vertex Declaration。名称不同，但核心问题一致：顶点数据存在哪里、索引如何复用、GPU 如何解释每个顶点属性。

### 相关记录

- [渲染管线三大阶段](./rendering-pipeline-stages.md) - 缓冲对象在应用阶段准备，并在几何阶段被读取。
- [Shader 阶段：顶点与片元](./shader-stage-vertex-fragment.md) - 顶点着色器消费顶点缓冲提供的数据。

### 验证记录

- [2026-04-15] 旧聚合记录结构修复：补齐模板必填章节，未改动原结论。
- [2026-06-13] 结构维护：从旧聚合记录拆分，未重新验证原技术结论。

---

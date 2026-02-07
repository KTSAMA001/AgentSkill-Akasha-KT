# 渲染管线知识

<!-- 
修改记录：
- [2026-01-30] 补充来源和可信度标注，确保知识条目符合规范。
- [2026-01-31] 将渲染管线核心概念整理为结构化知识条目，减少碎片化笔记带来的检索成本，方便后续把 SRP/URP、Shader 基础与性能要点继续整合进同一知识体系。
-->

本文档记录图形学渲染管线相关的核心知识点。

---

## 渲染管线三大阶段

**标签**：#graphics #knowledge #rendering-pipeline #draw-call
**来源**：《Unity Shader 入门精要》（冯乐乐著）
**来源日期**：2016 年（书籍出版）
**收录日期**：2026-01-30
**可信度**：⭐⭐⭐⭐⭐ (经典著作 + 广泛认可)

### 定义/概念

渲染管线（Rendering Pipeline）是将 3D 场景转换为 2D 图像的一系列处理步骤，分为三个主要阶段：应用阶段、几何阶段、光栅化阶段。

### 三大阶段

| 阶段 | 主导 | 职责 | 输出 |
|------|------|------|------|
| **应用阶段** | CPU | 处理场景数据 | 渲染图元（点、线、面） |
| **几何阶段** | GPU | 处理几何体 | 屏幕空间顶点坐标、深度、着色信息 |
| **光栅化阶段** | GPU | 逐像素渲染 | 最终屏幕图像 |

### 应用阶段详细流程（CPU 主导）

1. **加载数据**：从硬盘→内存→显存（Mesh、材质、贴图）
2. **设置渲染状态**：指定 Mesh 与材质、贴图的关联关系
3. **Draw Call**：CPU 调用 GPU 开始渲染

**关键点**：
- GPU 不能直接访问内存，需通过显存
- 加速算法和粗粒度剔除在此阶段执行
- 剔除不在视锥体内或被完全遮挡的物体

### 几何阶段详细流程（GPU 主导）

```
DrawCall 图元 → 顶点着色器 → 曲面细分着色器 → 几何着色器 → 裁剪 → 屏幕映射
```

### 光栅化阶段详细流程（GPU 主导）

```
屏幕坐标 → 三角形设置 → 三角形遍历 → 片元着色器 → 逐片元操作 → 目标缓冲区
```

### 记忆技巧

**"355" 记忆法**：
- 应用阶段 **3** 步骤
- 几何阶段 **5** 步骤（顶点着色器 → 屏幕映射）
- 光栅化 **5** 步骤（三角形设置 → 输出）

### 相关知识

- [顶点着色器](#vertex-shader)
- [片元着色器](#fragment-shader)
- [深度测试与模板测试](#depthstencil)
- [逐片元操作（混合等）](#per-fragment-operations)
- [性能关键词：Draw Call / Batching / Instancing](#performance-keywords)
- [CBUFFER 与 SRP Batcher](#cbuffer)
- [Shader 变体与关键字](#shader-variants)
- [SRP/URP 与 Renderer Feature](#srp-urp)
- [CommandBuffer 与渲染命令录制](#command-buffer)
- [光照模型：Lambert / Phong / Blinn-Phong](#lighting-models)
- [PBR / BRDF 基本要点](#pbr-brdf)
- [移动端：TBDR 与 Overdraw](#tbdr-overdraw)
- [不透明/透明：排序与代价](#opaque-transparent)

---

## 渲染管线中的缓冲对象

**标签**：#graphics #knowledge #rendering-pipeline #draw-call
**来源**：OpenGL 官方规范、关于 SRP/URP 的研究
**可信度**：⭐⭐⭐⭐⭐ (官方规范 + 实践验证)

### 定义/概念

渲染管线中的缓冲对象用于在 CPU 和 GPU 之间高效传输和管理渲染数据。

### 核心概念

**VBO (Vertex Buffer Object | 顶点缓冲对象)**

显存中的一块区域，保存模型的顶点信息（位置、UV、法线、切线等）。GPU 可直接从显存读取数据，无需从内存读取。

**EBO (Element Buffer Object | 索引缓冲对象)**

保存顶点索引的数组，用于指定顶点的绘制顺序。通过索引复用顶点数据，减少内存占用。

**VAO (Vertex Array Object | 顶点数组对象)**

VBO 和 EBO 的管理者，保存顶点各属性在 VBO 中的起始位置，用于快速定位某个顶点的某个属性值。

### 关系图

```
VAO (管理者)
├── VBO (数据存储)
│   ├── 顶点位置
│   ├── 顶点法线
│   ├── 顶点 UV
│   └── 顶点切线
└── EBO (索引数据)
    └── 顶点索引数组
```

### 关键点

- VBO 和 EBO 存储实际数据
- VAO 记录数据的组织方式和访问信息
- GPU 通过 VAO 快速访问 VBO 中的顶点属性

> 备注：VBO/EBO/VAO 属于 OpenGL 语境的经典术语。在 Unity/现代图形 API（D3D12/Vulkan/Metal）里对应概念更常见的说法是 Vertex Buffer / Index Buffer / Input Layout（或 Vertex Declaration），本质都是“数据如何在 GPU 侧组织与被读取”。

---

<a id="vertex-shader"></a>
## 顶点着色器（Vertex Shader）

**标签**：#graphics #knowledge #rendering-pipeline #draw-call
**来源**：《Unity Shader 入门精要》（冯乐乐著）
**可信度**：⭐⭐⭐⭐⭐ (经典著作 + 广泛认可)

### 定义/概念

顶点着色器对“每个顶点”执行一次，核心职责是把顶点从对象空间（Object Space）变换到裁剪空间（Clip Space），并输出后续阶段需要的插值数据（如 UV、法线、颜色、世界坐标等）。

### 常见输入/输出

- 输入：position、normal、tangent、uv、color、skin weights（蒙皮）等
- 输出：SV_POSITION（裁剪空间坐标）+ 自定义 varyings（供片元插值使用）

### 关键点

- 顶点阶段不直接“画出像素”，它产出的是可插值的属性。
- 片元阶段拿到的 UV/法线等通常来自顶点输出的插值结果。
- 坐标空间常见链路：Object → World → View → Clip（合并为 MVP 矩阵也很常见）。

---

<a id="fragment-shader"></a>
## 片元着色器（Fragment Shader）

**标签**：#graphics #knowledge #rendering-pipeline #draw-call
**来源**：《Unity Shader 入门精要》（冯乐乐著）
**可信度**：⭐⭐⭐⭐⭐ (经典著作 + 广泛认可)

### 定义/概念

片元着色器对“每个片元/像素候选”执行一次，负责计算该像素的最终颜色（以及可选的深度/多渲染目标输出）。

### 常见工作内容

- 纹理采样（Albedo/Normal/Mask 等）
- 光照计算（Lambert/Phong/Blinn-Phong/PBR 等）
- 透明裁剪（`discard` / alpha test）
- 输出颜色到渲染目标（Render Target）

### 关键点

- 片元着色器执行次数与屏幕覆盖率强相关：越“铺满屏幕”的物体越贵。
- 能利用 Early-Z 的情况下，尽量避免让 shader 破坏 Early-Z（例如写深度、过多 discard 等会影响）。

---

<a id="depthstencil"></a>
## 深度测试与模板测试（Depth/Stencil）

**标签**：#graphics #knowledge #rendering-pipeline #draw-call
**来源**：《Unity Shader 入门精要》（冯乐乐著）、Unity 官方文档
**可信度**：⭐⭐⭐⭐⭐ (经典著作 + 官方文档)

### 定义/概念

- **Depth Test（深度测试）**：比较当前片元深度与深度缓冲中的值，决定该片元是否可见。
- **ZWrite（写深度）**：是否把当前片元深度写入深度缓冲。
- **Stencil Test（模板测试）**：用模板缓冲做更通用的“遮罩/标记/区域控制”。

### 关键点（Unity 常见语境）

- 不透明物体通常：`ZWrite On` + 合理的 `ZTest`，利于遮挡剔除与 Early-Z。
- 透明物体通常：`ZWrite Off`（避免错误遮挡），因此更依赖排序并更容易 overdraw。
- Stencil 常用于：UI Mask、轮廓描边、局部后处理、门户/传送门、角色高亮遮罩等。

---

<a id="per-fragment-operations"></a>
## 逐片元操作（Per-Fragment Operations）

**标签**：#graphics #knowledge #rendering-pipeline #draw-call
**来源**：《Unity Shader 入门精要》（冯乐乐著）
**可信度**：⭐⭐⭐⭐⭐ (经典著作 + 广泛认可)

### 定义/概念

逐片元操作发生在片元着色器之后，典型包括深度/模板相关操作、混合（Blending）、写入颜色缓冲等。

### 关键点

- **Blending（混合）**：透明效果的核心，但会增加 overdraw，且通常无法享受深度写入带来的遮挡收益。
- **Color Mask**：可控是否写入 RGBA 某些通道，常用于特殊效果或调试。

---

<a id="performance-keywords"></a>
## 性能关键词：Draw Call / Batching / Instancing

**标签**：#graphics #knowledge #rendering-pipeline #draw-call
**来源**：Unity 官方文档 - Optimizing draw calls、TA 工程实践经验整理
**可信度**：⭐⭐⭐⭐ (官方文档 + 实践验证)

### 定义/概念

- **Draw Call**：CPU 向 GPU 提交一次绘制命令的行为（一次提交不等于一次三角形）。
- **Batching（合批）**：把多个对象的绘制合并成更少的 Draw Call（代价通常是限制更多、需要一致的渲染状态）。
- **GPU Instancing**：在一次 Draw Call 中绘制同一 mesh/material 的多个实例，并通过 per-instance 数据区分。

### 关键点

- CPU 侧瓶颈常体现为 Draw Call 过多；GPU 侧瓶颈常体现为 overdraw、shader 太重、像素覆盖太大。
- 过度合批也可能带来副作用：更大的顶点数据、剔除粒度变粗、材质灵活性下降。

---

<a id="cbuffer"></a>
## CBUFFER 与 SRP Batcher

**标签**：#graphics #knowledge #rendering-pipeline #draw-call
**来源**：Unity 官方博客 - SRP Batcher: Speed up your rendering、关于 SRP/URP 的研究
**可信度**：⭐⭐⭐⭐ (官方博客 + 实践验证)

### 定义/概念

CBUFFER（Constant Buffer）可以理解为 GPU 侧的“常量数据块”，用于高效地把一组 uniform/常量参数传给 shader。

在 Unity SRP 语境下，**SRP Batcher** 会尝试把渲染中“可批处理的部分”按更稳定的方式提交给 GPU，其中一个关键前提是：shader 的常量数据布局要符合 SRP Batcher 的要求（典型表现为使用 `UnityPerMaterial` 等约定的 CBUFFER 组织材质参数）。

### 关键点

- 把“经常变化”的参数频繁改动，可能会破坏批处理收益（具体取决于管线与平台实现）。
- 设计材质参数时，尽量让“稳定参数”与“高频变化参数”分层组织（例如：全局/每相机/每物体/每材质）。
- `MaterialPropertyBlock` 常用于 per-renderer 参数覆写，但滥用也可能影响合批与提交效率（需要结合实际渲染路径验证）。

---

<a id="shader-variants"></a>
## Shader 变体（Variants）与关键字（Keywords）

**标签**：#graphics #knowledge #rendering-pipeline #draw-call
**来源**：Unity 官方文档 - Shader variants and keywords、TA 工程实践经验整理
**可信度**：⭐⭐⭐⭐⭐ (官方文档 + 实践验证)

### 定义/概念

Shader 变体是“同一个 shader 因关键字组合不同而生成的多份编译结果”。关键字组合越多，变体数量越容易指数级膨胀。

### 关键点

- 变体膨胀会带来：更长的构建时间、更大的包体/缓存、更高的运行时加载与切换成本。
- 通用原则：**能少开关键字就少开**，能用更少的组合表达需求就不要用“全排列”。
- `multi_compile` 倾向于“永远编译所有组合”；`shader_feature` 倾向于“只编译实际使用到的组合”（概念上如此，具体行为与 Unity/管线版本相关）。

---

<a id="srp-urp"></a>
## SRP/URP 与 Renderer Feature

**标签**：#graphics #knowledge #rendering-pipeline #draw-call
**来源**：Unity 官方文档 - Universal Render Pipeline、关于 SRP/URP 的研究
**可信度**：⭐⭐⭐⭐⭐ (官方文档 + 实践验证)

### 定义/概念

- **SRP（Scriptable Render Pipeline）**：Unity 可编程渲染管线体系，允许用 C# 组织渲染流程。
- **URP**：Unity 官方提供的 SRP 之一，偏向跨平台与移动端。
- **Renderer Feature**：URP 的扩展点之一，通常通过 `ScriptableRendererFeature` 注入一个或多个 `ScriptableRenderPass`，从而在指定时机插入自定义渲染逻辑。

### 关键点

- Renderer Feature 更像“渲染流程的插件”：选择注入时机（event）、配置资源（RT/材质）、执行绘制/Blit。
- 设计 Feature 时要特别关注：RT 分配、清理策略、Pass 的执行顺序、与后处理/透明队列的交互。

---

<a id="command-buffer"></a>
## CommandBuffer 与渲染命令录制

**标签**：#graphics #knowledge #rendering-pipeline #draw-call
**来源**：Unity 官方文档 - CommandBuffer、关于 SRP/URP 的研究
**可信度**：⭐⭐⭐⭐⭐ (官方文档 + 实践验证)

### 定义/概念

CommandBuffer（命令缓冲）可以理解为“把要做的 GPU 绘制/状态切换等命令先录下来，再在特定时机提交执行”。在 SRP/URP 中，RenderPass 往往就是围绕“构建并执行命令”来组织。

### 关键点

- 好处：把渲染逻辑与执行时机解耦；更易插入自定义 pass；便于复用与排序。
- 风险点：命令录制过多/过重会带来 CPU 侧开销；RT/资源生命周期管理不当会造成内存与性能问题。

---

<a id="lighting-models"></a>
## 光照模型：Lambert / Phong / Blinn-Phong

**标签**：#graphics #knowledge #rendering-pipeline #draw-call
**来源**：《Real-Time Rendering》、图形学基础课程
**可信度**：⭐⭐⭐⭐⭐ (权威著作 + 学术标准)

### Lambert（漫反射）

- 核心：表面越“朝向光源”，越亮。
- 常见形式：$I_d \propto \max(0, \mathbf{N}\cdot\mathbf{L})$。

### Phong（镜面高光）

- 使用反射向量 $\mathbf{R}$ 与视线 $\mathbf{V}$ 的夹角决定高光。
- 常见形式：$I_s \propto \max(0, \mathbf{R}\cdot\mathbf{V})^n$（$n$ 越大高光越尖锐）。

### Blinn-Phong（镜面高光，半角向量版本）

- 用半角向量 $\mathbf{H}=\text{normalize}(\mathbf{L}+\mathbf{V})$ 替代反射向量，计算更稳定、成本更低。
- 常见形式：$I_s \propto \max(0, \mathbf{N}\cdot\mathbf{H})^n$。

---

<a id="pbr-brdf"></a>
## PBR / BRDF 基本要点

**标签**：#graphics #knowledge #rendering-pipeline #draw-call
**来源**：《Physically Based Rendering》、《Real-Time Rendering》
**可信度**：⭐⭐⭐⭐⭐ (权威著作 + 学术标准)

### 定义/概念

- **BRDF**：描述“光从某方向入射后，向某方向反射的比例”的函数。
- **PBR**：一套更贴近物理规律的材质与光照建模方法，强调能量守恒、菲涅尔效应、粗糙度对高光分布的影响等。

### 关键点（工程侧常用记忆）

- **金属度/粗糙度工作流**：金属更接近“高反射 + 有色反射”，非金属更接近“漫反射为主 + 无色镜面反射”。
- **粗糙度**：越粗糙，高光越宽、越暗；越光滑，高光越尖锐。
- **Fresnel（菲涅尔）**：掠射角更亮（更强反射），正视角更暗（反射更弱）。

---

<a id="tbdr-overdraw"></a>
## 移动端：TBDR 与 Overdraw

**标签**：#graphics #knowledge #rendering-pipeline #draw-call
**来源**：ARM/Qualcomm GPU 官方文档、图形学/移动端渲染笔记
**可信度**：⭐⭐⭐⭐ (厂商文档 + 实践验证)

### 定义/概念

- **TBDR（Tile-Based Deferred Rendering）**：移动端常见 GPU 架构/策略之一，把屏幕分成 tile，在片上缓存中尽量完成一个 tile 的可见性与着色，减少带宽。
- **Overdraw**：同一个像素被多次绘制（尤其透明叠加）导致重复着色与带宽浪费。

### 关键点

- TBDR 的收益非常依赖“带宽压力”和“渲染目标读写”；过多的 RT 切换、过重的后处理、过高的分辨率都会放大成本。
- 透明/粒子是 overdraw 大户：屏幕覆盖面积越大，像素成本越高。

---

<a id="opaque-transparent"></a>
## 不透明/透明：排序与代价

**标签**：#graphics #knowledge #rendering-pipeline #draw-call
**来源**：Unity 官方文档、《Unity Shader 入门精要》
**可信度**：⭐⭐⭐⭐⭐ (官方文档 + 经典著作)

### 不透明（Opaque）

- 通常 `ZWrite On`，更利于遮挡剔除与 Early-Z。
- 一般可以更大胆地依赖深度测试减少过度绘制。

### 透明（Transparent）

- 通常 `ZWrite Off`，需要按距离排序进行正确混合。
- 更容易产生 overdraw；同屏大量透明会显著拉高 GPU 像素成本。

---

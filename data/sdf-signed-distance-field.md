# SDF（有向距离场）知识

<!-- 
修改记录：
- [2026-01-31] 从 TaTa 仓库 (https://github.com/KTSAMA001/TaTa/blob/master/SDF/SDF-8ssedt.md) 整合 SDF 相关知识。
- [2026-01-31] 添加图片引用链接（图片资源保留在 TaTa 仓库）。
-->

本文档记录 SDF（Signed Distance Field，有向距离场）的原理与应用。

> 📷 **图片资源**：本文图片引用自 [TaTa 仓库 SDF/img](https://github.com/KTSAMA001/TaTa/tree/master/SDF/img)

---

## SDF 基本概念

**标签**：#graphics #knowledge #sdf
**来源**：TaTa 仓库 - SDF/SDF-8ssedt.md
**来源日期**：2020-12-18
**收录日期**：2026-01-31
**可信度**：⭐⭐⭐⭐ (技术博客 + 实践验证)

### 定义/概念

Signed Distance Field（有向距离场），中文名为有向距离场。SDF 有 2D 和 3D 的区别，其定义非常简单：**每个像素（体素）记录自己与距离自己最近物体之间的距离，如果在物体内，则距离为负，正好在物体边界上则为 0**。

### 原理/详解

以简单的图像为例：
- 白色表示物体，黑色表示空
- 对于一副中间有一个圆的图像，其对应的 SDF 图中：
  - 圆中心的点最黑（处于物体最内部）
  - 图片四角最白（距离圆最远）
- 通常将有向距离值映射到 [0-1] 范围，0.5 表示物体内外的分界线

**示意图**：

| 原始图像 | 对应 SDF |
|---------|---------|
| ![原始图像](https://raw.githubusercontent.com/KTSAMA001/TaTa/master/SDF/img/example1.png) | ![SDF图像](https://raw.githubusercontent.com/KTSAMA001/TaTa/master/SDF/img/example1_SDF.png) |

### 关键点

- SDF 存储的是距离信息（向量），而非直接的颜色信息（标量）
- 距离为负表示在物体内部
- 距离为正表示在物体外部
- 距离为 0 表示在物体边界上

### 相关知识

- [SDF 生成算法 - 8ssedt](#sdf-生成算法---8ssedt)
- [SDF vs Bitmap](#sdf-vs-bitmap)
- [SDF 图像平滑过渡](#sdf-实现图像平滑过渡)

---

## SDF 生成算法 - 8ssedt

**标签**：#graphics #knowledge #sdf
**来源**：TaTa 仓库 - SDF/SDF-8ssedt.md
**来源日期**：2020-12-18
**收录日期**：2026-01-31
**可信度**：⭐⭐⭐⭐ (技术博客 + 代码验证)

### 定义/概念

8ssedt 是一种能在**线性时间内**计算出 SDF 的算法，相比暴力算法（平方级复杂度）效率大幅提升。

### 原理/详解

算法核心是**动态规划**的递推公式：

对于任意像素点，有以下几种情况：
1. **像素点值为 1（物体内）**：自身就是目标点，距离为 0
2. **像素点值为 0（物体外）**：目标点在四周，需要计算

递推公式：
```
now.sdf = MinimumSDF(near.sdf + distance(now, near))
```

伪代码：
```c
now.sdf = 999999;
if(now in object){
    now.sdf = 0;
}else{
    foreach(near in nearPixel(now)){
        now.sdf = min(now.sdf, near.sdf + distance(now, near));
    }
}
```

### 关键点

- **Pass 0**：从上到下、从左到右遍历，比较左上方四个点
- **Pass 1**：从下到上、从右到左遍历，比较右下方四个点
- 两个 Pass 结合，即可计算出完整的 SDF
- 需要两个 grid 分别计算物体外到物体的距离、物体内到物体外的距离
- 最终 SDF = grid1.sdf - grid2.sdf

### 示例代码

```cpp
struct Point {
    int dx, dy;
    int DistSq() const { return dx*dx + dy*dy; }
};

void Compare(Grid &g, Point &p, int x, int y, int offsetx, int offsety) {
    Point other = Get(g, x+offsetx, y+offsety);
    other.dx += offsetx;
    other.dy += offsety;
    if (other.DistSq() < p.DistSq())
        p = other;
}

void GenerateSDF(Grid &g) {
    // Pass 0: 从上到下，从左到右
    for (int y=0; y<HEIGHT; y++) {
        for (int x=0; x<WIDTH; x++) {
            Point p = Get(g, x, y);
            Compare(g, p, x, y, -1,  0);   // 左
            Compare(g, p, x, y,  0, -1);   // 上
            Compare(g, p, x, y, -1, -1);   // 左上
            Compare(g, p, x, y,  1, -1);   // 右上
            Put(g, x, y, p);
        }
        for (int x=WIDTH-1; x>=0; x--) {
            Point p = Get(g, x, y);
            Compare(g, p, x, y, 1, 0);     // 右
            Put(g, x, y, p);
        }
    }
    
    // Pass 1: 从下到上，从右到左
    for (int y=HEIGHT-1; y>=0; y--) {
        for (int x=WIDTH-1; x>=0; x--) {
            Point p = Get(g, x, y);
            Compare(g, p, x, y,  1,  0);   // 右
            Compare(g, p, x, y,  0,  1);   // 下
            Compare(g, p, x, y, -1,  1);   // 左下
            Compare(g, p, x, y,  1,  1);   // 右下
            Put(g, x, y, p);
        }
        for (int x=0; x<WIDTH; x++) {
            Point p = Get(g, x, y);
            Compare(g, p, x, y, -1, 0);    // 左
            Put(g, x, y, p);
        }
    }
}
```

### 参考链接

- [8ssedt SIMD 优化](https://www.jianshu.com/p/58271568781d) - 从编译角度优化，可减少一半运行时间

---

## SDF vs Bitmap

**标签**：#graphics #knowledge #sdf
**来源**：TaTa 仓库 - SDF/SDF-8ssedt.md
**来源日期**：2020-12-18
**收录日期**：2026-01-31
**可信度**：⭐⭐⭐⭐ (技术博客 + 实践验证)

### 定义/概念

SDF 相比传统 Bitmap 的核心优势：**支持高质量的缩放，放大后边缘依然光滑锐利**。

### 原理/详解

**关键区别**：
- **Bitmap**：每个像素存储 RGB 颜色（标量），插值运算无实际意义
- **SDF**：每个像素存储到边界的距离（向量），插值运算得到的是正确的中间距离值

**放大时的行为**：

将贴图从 256 放大到 1024，每相邻两像素间要插入三个点：
```
A B1 B2 B3 C

// Bitmap 插值（颜色是标量，插值无意义）
A = (0,0,0), C = (1,1,1)
B1 = (0.25, 0.25, 0.25)  // 无实际意义的灰色

// SDF 插值（距离是向量，插值有意义）
A = (0,0), C = (4,0)
B1 = (1,0)  // 正确的中间距离
B2 = (2,0)
B3 = (3,0)
```

**本质**：SDF 利用 GPU 插值器的特性实现了光滑放大效果，类似 PS 中矢量图和位图的区别。

### 关键点

- Bitmap 放大后会出现明显锯齿
- SDF 放大后边缘依然光滑锐利
- SDF 本质上是"信号重建"，通过距离信息恢复原始形状
- 这是 SDF 用于字体渲染的核心原因

**对比效果**：

| 正常大小对比 | 放大后对比 |
|-------------|-----------|
| ![正常对比](https://raw.githubusercontent.com/KTSAMA001/TaTa/master/SDF/img/snowdif1.png) | ![放大对比](https://raw.githubusercontent.com/KTSAMA001/TaTa/master/SDF/img/snowdif2.png) |

左侧 SDF 生成的图像边缘光滑锐利，右侧 Bitmap 放大后出现明显锯齿。

---

## SDF 实现图像平滑过渡

**标签**：#graphics #knowledge #sdf
**来源**：TaTa 仓库 - SDF/SDF-8ssedt.md
**来源日期**：2020-12-18
**收录日期**：2026-01-31
**可信度**：⭐⭐⭐⭐ (技术博客 + 实践验证)

### 定义/概念

SDF 可以实现不同图像之间的平滑过渡，常用于卡通渲染中的脸部阴影过渡。

### 原理/详解

**基本原理**：对不同图像的两张 SDF 进行插值

Shader 代码：
```hlsl
half4 col = half4(1, 1, 1, 1);
half a1 = lerp(color1.r, color2.r, _SDFLerp);
col.a = smoothstep(0.5, 0.5 - _SmoothDelta, a1);
```

**卡通渲染应用**：
- 艺术家绘制特定光线角度的脸部阴影
- 通过 SDF 插值计算中间过程
- 叠加到一张图上，实现平滑过渡

### 关键点

- 每个像素本质上是距离的平滑过渡，转换成 RGB 就是图像间的平滑过渡
- 可以减少贴图数量（多张阴影图合并为一张）

**SDF 插值过渡效果**：

| 图像 1 | 图像 2 |
|-------|-------|
| ![Step1](https://raw.githubusercontent.com/KTSAMA001/TaTa/master/SDF/img/step1.png) | ![Step2](https://raw.githubusercontent.com/KTSAMA001/TaTa/master/SDF/img/step2.png) |

**动态效果演示**：[SDF 过渡 GIF](https://raw.githubusercontent.com/KTSAMA001/TaTa/master/SDF/img/SDF.gif)

### 限制条件

使用 SDF 叠加生成 smooth 图的限制：
1. 生成的 smooth 图由 SDF 退化为位图
2. 原始图像对应像素点之间必须是**单调变化**关系
3. 精度受限于贴图通道（单通道精度 256）

**不适用场景**：如果像素点 y 在图像 ABC 的值分别为 (0, 1, 0)，无法通过阈值描述 (0→1→0) 的变化过程。

### 相关知识

- 卡通渲染
- 脸部阴影技术

---

## 与经验关联

- 相关经验：可在实际项目中验证 SDF 字体、SDF 阴影等效果

---

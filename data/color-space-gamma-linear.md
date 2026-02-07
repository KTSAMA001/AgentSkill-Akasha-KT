# 色彩空间知识

本文档记录 Gamma/Linear 色彩空间的原理与 Unity 中的应用。

---

## Gamma 与 Linear 色彩空间基础

**标签**：#graphics #knowledge #color-space #gamma #linear
**来源**：TaTa 仓库 - ColorSpace/Gamma&Linear.md
**来源日期**：2021-01-06
**收录日期**：2026-01-31
**可信度**：⭐⭐⭐⭐ (技术博客 + 实践验证)

### 定义/概念

- **Gamma 2.2**：显示设备默认进行的操作，`pow(c, 2.2)`，更多的值被压缩在暗部
- **Gamma 0.45 (sRGB)**：用于矫正显示器 2.2 压暗的操作，`pow(c, 0.45)`
- **线性空间**：物理世界真实的光照空间，人眼所见

### 原理/详解

**为什么需要 Gamma？**
1. 人眼对暗部的敏感度更高
2. 早期显示设备存储空间有限
3. 通过 `pow(c, 2.2)` 使用更多比特位存储暗部细节

**完整流程**：
```
物理世界(线性) → Gamma 0.45矫正 → 存储(sRGB) → 显示器 Gamma 2.2 → 人眼看到(线性)
```

### 关键点

- 显示器默认做 Gamma 2.2（压暗）
- sRGB 空间 = Gamma 0.45 空间
- 两次 Gamma 操作（0.45 × 2.2 ≈ 1）还原到线性空间

---

## Unity 色彩空间设置

**标签**：#graphics #knowledge #color-space #gamma #linear
**来源**：TaTa 仓库 - ColorSpace/Gamma&Linear.md
**来源日期**：2021-01-06
**收录日期**：2026-01-31
**可信度**：⭐⭐⭐⭐ (技术博客 + 实践验证)

### Gamma 空间

- Unity **不会**对 shader 输入/输出做任何处理
- 默认 shader 色彩计算在 sRGB（gamma 0.45）空间
- 原始贴图是什么样，输出就是什么样
- 贴图存储的颜色本身就在 sRGB 空间（PS 制作时已经是 sRGB）
- 经过显示器 Gamma 2.2，显示正常

**注意**：如果在 Gamma 空间使用 Linear 贴图，显示结果会**偏暗**

### Linear 空间

- Unity 默认 shader 色彩计算在**线性空间**
- 计算结果会经过一次 `pow(c, 0.45)` 矫正
- 再经过显示器 2.2 操作，回到线性空间

**贴图 sRGB 选项**：
- **勾选 sRGB**：采样时进行 `pow(c, 2.2)`，从 sRGB 转换到线性空间
- **不勾选**：不做任何处理（用于已经是线性的贴图，如法线图、Mask 图等）

### 关键点

| 设置 | Shader 计算空间 | 输出处理 | 贴图处理 |
|------|----------------|---------|---------|
| Gamma | sRGB | 无 | 无 |
| Linear | 线性 | pow(c, 0.45) | sRGB 贴图自动 pow(c, 2.2) |

---

## Linear 空间下的 LUT 处理

**标签**：#graphics #knowledge #color-space #gamma #linear
**来源**：TaTa 仓库 - ColorSpace/Gamma&Linear.md
**来源日期**：2021-01-06
**收录日期**：2026-01-31
**可信度**：⭐⭐⭐⭐ (技术博客 + 实践验证)

### 问题背景

LUT 贴图通常在 PS 中制作，即在 Gamma 空间完成查找操作。在 Linear 空间下使用 LUT 需要特殊处理。

### 解决方案

**方案 1**：勾选 sRGB，对输入 color 做 `pow(c, 0.45)`

**方案 2**：不勾选 sRGB，对输入 color 做 `pow(c, 0.45)`，对输出做 `pow(c, 2.2)`

### 原理解释

1. **输入转换**：输入 color 必须转换到 sRGB 空间才能得到正确的查找坐标
2. **输出转换**：从 LUT 取出的值也是 sRGB 空间的
   - 若不处理，Linear 空间下 Unity 会对输出做 `pow(c, 0.45)`
   - 相当于映射到更亮的空间，显示结果偏亮

### 关键点

- 方案 1：利用 Unity 自动的 sRGB 转换（`pow(c, 2.2)`）
- 方案 2：手动在 shader 中进行转换
- 两种方案显示上有细微差别（精度差异）
- 方案 1 可能有更高精度（管线/硬件支持）

### 相关知识

- [Unity 色彩空间设置](#unity-色彩空间设置)
- 后处理 Color Grading

---

## 与经验关联

- 在实际项目中配置色彩空间时，注意贴图的 sRGB 设置
- 法线图、Mask 图等数据图应**取消勾选** sRGB
- 颜色贴图（Albedo、Diffuse 等）应**勾选** sRGB

---

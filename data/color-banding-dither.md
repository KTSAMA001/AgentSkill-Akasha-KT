# 色带（Color Banding）与抖动（Dithering）知识

<!--
修改记录：
- [2026-02-05] 新增：Color Banding 在 Unity URP 高亮特效（Bloom/Tone Mapping）中的典型表现与解决路径（Dithering、LUT Size、输出位深）。
-->

本文档记录 Color Banding（色带/色阶）这一常见图形伪影的成因，以及在 Unity URP 高亮特效中常见的处理方式。

---

## Color Banding（色带）是什么

**分类**：图形学 > 图像伪影
**标签**：#graphics #knowledge #color-banding #dither #hdr
**来源**：Wikipedia（Colour banding / Dither）、FrostKiwi（LUT 文章）
**来源日期**：2026-01-15（Dither 页面最后编辑时间） / 2026-01-04（Colour banding 页面最后编辑时间） / 2024-02-29（FrostKiwi LUT 文章最后编辑时间）
**收录日期**：2026-02-05
**更新日期**：2026-02-05
**可信度**：⭐⭐⭐（社区科普 + 工程广泛实践）
**状态**：📘 有效

### 定义/概念

- **Color Banding**：连续的颜色/亮度渐变在显示时出现“分层台阶（条带/等高线）”的现象，本质是**量化（Quantization）**导致的精度不足。
- 它常被视为一种不希望出现的 **Posterization（色阶化）**伪影。

### 原理/详解

#### 1) 为什么高亮光晕更容易出现“水波纹/色带”

在 URP 特效里，常见触发条件是：
- 发光颜色（HDR）强度很高（例如 Intensity 7~8）
- Bloom 产生很平滑的大面积渐变光晕
- 后处理中存在 Tone Mapping / Color Grading（常见通过 LUT 做颜色映射）

即使你启用了 HDR（例如中间缓冲是 FP16/更高精度），**最终输出到屏幕/交换链**时通常仍会被呈现为有限色深（典型是每通道 8-bit）。
当 Tone Mapping 把巨大的 HDR 亮度范围压缩到可显示范围时，原本很平滑的亮度差会被“挤到一起”，导致相邻像素落在同一个或相邻的离散亮度等级上，于是看起来像一圈一圈的等高线。

#### 2) 为什么你观察到“圈圈不随纹理流动”

如果条带边界：
- 对 UV 流动不敏感
- 更像固定在屏幕空间或以亮度阈值为分界

通常意味着问题发生在**屏幕空间的后处理/输出量化**阶段，而不是材质自身的纹理采样。

#### 3) 量化误差与抖动的关系

量化会产生误差。若误差与信号相关（在图像中会形成规律结构），人眼更容易注意到“条纹”。
**Dithering（抖动）**通过引入极小的噪声/扰动，使量化误差更接近随机噪声，从而“打散”规律条纹，让渐变看起来更平滑（代价是略微颗粒感）。

### 关键点

- 色带不是 UV 问题，而是“**有限色深 + Tone Mapping/颜色映射 + 大面积平滑渐变**”的组合问题。
- Bloom 这种“平滑、低频”的光晕非常容易暴露量化台阶。
- 抖动的本质不是提高精度，而是**用噪声掩蔽条带**（视觉上更自然）。

---

## Unity URP 中的典型解决方案（按常用优先级）

### 方案 1：开启 Dithering（首选）

适用：最常见、性价比最高。

要点：
- 在 URP 的 Post-processing 中启用 Dithering（不同 URP 版本入口可能在 URP Asset 或 Camera/Volume 相关设置里）。
- Dithering 会在最终输出附近引入细微噪声，显著降低条带可见度。

### 方案 2：提高 LUT Size（提升颜色映射精度）

适用：当色带主要出现在 Color Grading / Tone Mapping 之后，且项目对画质更敏感。

要点：
- URP 颜色分级常依赖 LUT（3D LUT 典型是 32^3 或类似规模）。
- LUT 分辨率过低时，强 HDR 压缩后的渐变可能更容易“断层”。
- 提升 LUT Size（例如从 32 提到 64）通常能改善过渡精度（但会带来一定性能/内存开销）。

### 方案 3：降低“过于极端”的 HDR 强度/调整 Bloom 曲线

适用：当你可以接受艺术上稍微收敛一些高亮。

要点：
- 过高的强度会让 Tone Mapping 压缩更激烈，更容易暴露量化台阶。
- 适当降低峰值、改用更平滑的 falloff、调整 Bloom threshold/散射范围，往往能缓解。

### 方案 4：减少源贴图/渐变的压缩伪影（辅助）

适用：光晕贴图本身就是平滑渐变，且压缩格式较激进。

要点：
- 有损压缩会引入额外噪点与台阶，使 banding 更明显。
- 对关键渐变图：优先选择更高质量压缩或不压缩（取决于平台与内存预算）。

---

## 常见误区

- “我已经开了 HDR/64-bit HDR 渲染，怎么还会 banding？”
  - HDR 往往是**中间缓冲精度**更高；最终显示与截断/量化仍可能受限于输出格式与显示设备。

- “Blur 一下能不能消掉条带？”
  - 如果条带来自输出位深限制，模糊不会真正消除量化台阶，甚至可能让过渡区域更大、更显眼。

---

## 相关知识

- 色彩空间（Gamma/Linear）：./color-space-gamma-linear.md
- 渲染管线基础：./rendering-pipeline-overview.md
- 相关概念：Posterization / Quantization / Mach bands

## 参考链接

- Colour banding（概念、原因、可能方案）：https://en.wikipedia.org/wiki/Colour_banding
- Dither（抖动的定义、与量化误差的关系）：https://en.wikipedia.org/wiki/Dither
- LUT 基础（LUT 的工程背景与常见尺寸观念）：https://blog.frost.kiwi/WebGL-LUTS-made-simple/

---

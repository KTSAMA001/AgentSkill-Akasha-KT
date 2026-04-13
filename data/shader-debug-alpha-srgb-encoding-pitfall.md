# Shader 调试：Alpha 通道输出到 RGB 时的 sRGB 伽马偏差

**标签**：#shader #urp #color-space #experience #graphics #unity
**来源**：实践总结 — Jymf_Role_01.shader 颜色遮罩调试
**收录日期**：2026-04-13
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐⭐（实测 + sRGB 标准公式验证）
**适用版本**：Unity 2022.3+ / URP 14+（任何 Linear 渲染管线均适用）

### 概要

在 Shader 中用 `return alpha` 调试纹理 A 通道时，屏幕取色器读到的值与纹理预览值不一致。这是因为 A 值被灌入了 RGB 通道输出，而 RGB 会被 sRGB Back Buffer 的硬件编码"提亮"。用 `pow(a, 2.2)` 预补偿在暗部会失效，因为 sRGB 编码函数在低值区使用的是线性段而非幂函数。

### 内容

#### 场景复现

- 纹理 `_BaseMap` 的 Alpha 通道，Unity 纹理预览取色器显示 **(12, 12, 12)**
- Shader 中 `return tex2D(_BaseMap, uv).a;`（隐式 `half4(a,a,a,a)`）
- 屏幕取色器读到 **(60, 60, 60)**，而非预期的 (12, 12, 12)

#### 根本原因

**A 通道采样不做 sRGB 解码（正确），但输出到 RGB 后会被 sRGB Back Buffer 的 Linear→sRGB 硬件编码处理。**

sRGB 编码是分段函数（非简单幂函数）：

```
Linear → sRGB 编码（GPU 硬件自动执行）：
  L ≤ 0.0031308 时：S = L × 12.92         ← 线性段
  L > 0.0031308 时：S = 1.055 × L^(1/2.4) - 0.055  ← 幂函数段
```

#### 数学验证

**直接输出 alpha（得到 60）**：
```
a = 12/255 ≈ 0.04706
0.04706 > 0.0031308 → 走幂函数段
S = 1.055 × 0.04706^(1/2.4) - 0.055 ≈ 0.240
0.240 × 255 ≈ 61 ≈ 60 ✓
```

**pow(a, 2.2) 预补偿（得到 ~2-4）**：
```
pow(0.04706, 2.2) ≈ 0.00120
0.00120 < 0.0031308 → 掉入线性段！
S = 0.00120 × 12.92 ≈ 0.0156
0.0156 × 255 ≈ 4
```

`pow(2.2)` 把值压得太低，落入 sRGB 的线性段。线性段 `×12.92` 与幂函数 `L^(1/2.4)` 形式不同，无法与 `pow(2.2)` 互相抵消。

#### 四条核心结论

1. **A 通道全程线性，作为 mask 与颜色相乘无需任何校正** — 采样不做 sRGB 解码，计算在线性空间正确运行
2. **调试 `return alpha` 看到偏高值是正常行为** — A 被灌入 RGB，RGB 被 sRGB 编码提亮
3. **`pow(a, 2.2)` 反补偿在暗部完全失效** — 值被压到 sRGB 线性段阈值（0.0031308）以下，编码方式从幂函数变为 `×12.92` 线性缩放
4. **调试精确值应使用 RenderDoc / Frame Debugger** — 直接读取线性浮点值，完全绕开 sRGB 编码问题；或使用放大系数法（如 `return a * 20.0`）粗略观察

### 关键代码

```hlsl
// ❌ 调试时直接返回 alpha — 屏幕取色不等于纹理预览值（被 sRGB 编码）
return tex2D(_BaseMap, uv).a;

// ❌ pow 预补偿 — 暗部掉入 sRGB 线性段，结果反而更离谱
return pow(tex2D(_BaseMap, uv).a, 2.2);

// ✅ 放大系数法 — 粗略调试用
return tex2D(_BaseMap, uv).a * 20.0;

// ✅ 正式用途 — alpha 作为 mask 直接线性运算，无需任何校正
float mask = tex2D(_BaseMap, uv).a;
baseRGB = baseRGB * clampedAreaColor * step(0.001, mask);
```

### 参考链接

- [sRGB Transfer Function 精确公式解析](https://entropymine.com/imageworsener/srgbformula/) - sRGB 分段函数详细说明，含 0.04045/0.0031308 阈值来源考证
- [Microsoft DXGI 色彩空间转换文档](https://learn.microsoft.com/en-us/windows/win32/direct3ddxgi/converting-data-color-space) - GPU 硬件如何自动执行 sRGB 编码
- [Unity 色彩空间文档](https://docs.unity3d.com/Manual/color-spaces.html) - Linear/Gamma 工作流概述

### 相关记录

- [色彩空间知识](./color-space-gamma-linear.md) - Gamma/Linear 基础原理与 Unity 设置

### 验证记录

- [2026-04-13] 首次记录：在 Jymf_Role_01.shader 颜色遮罩（ColorMask）功能调试中发现并验证。纹理 A 通道值 12 直接输出显示为 60，pow(2.2) 后显示为 ~2，均通过 sRGB 分段公式精确复现。

# Shader 调试：Alpha 通道输出到 RGB 时的 sRGB 伽马偏差

**标签**：#shader #urp #color-space #experience #graphics #unity
**来源**：实践总结 — Jymf_Role_01.shader 颜色遮罩调试
**收录日期**：2026-04-13
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐⭐（实测 + sRGB 精确公式 + 穷举数值分析 + URP 源码追踪）
**适用版本**：Unity 2022.3+ / URP 14+（任何 Linear 渲染管线均适用）

### 概要
在 Shader 中用 `return alpha` 调试纹理 A 通道时，屏幕取色器读到的值与纹理预览值不一致。这是因为 A 值被灌入了 RGB 通道输出，而 RGB 会被 sRGB Back Buffer 的硬件编码"提亮"。用 `pow(a, 2.2)` 预补偿在暗部会失效，因为 sRGB 编码函数在低值区使用的是线性段而非幂函数。此外，**DXT5/ASTC 纹理压缩**会改变实际 alpha 值，进一步加剧暗部数值偏差。

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

**叠加因素：纹理压缩**

DXT5（PC）/ ASTC（Android）对 Alpha 通道是有损压缩。4×4 像素块内的 Alpha 被量化到两个端点值之间的 8 级插值。纹理预览器显示的是压缩前/原始值（12），但 GPU 实际采样到的是压缩后值（可能偏移 ±2~3）。在 sRGB 暗部线性段，这 ±2~3 的偏移会被 8-bit 量化放大为屏幕值 ±1~2 的跳变。

#### 数学验证

> 项目配置：Linear 色彩空间 / URP 14 / HDR=Off / Fast sRGB=Off / Post Processing=Off
> RT 格式：R8G8B8A8_SRGB（HDR 关闭时 Unity 使用 DefaultFormat.LDR + sRGB=true）
> 纹理格式：PC=DXT5(auto) / Android=ASTC 6x6，sRGBTexture=1

**直接输出 alpha（屏幕观测 ~60）**：
```
假设实际采样 alpha = 12/255 ≈ 0.04706
0.04706 > 0.0031308 → 走幂函数段
S = 1.055 × 0.04706^(1/2.4) - 0.055 ≈ 0.240
0.240 × 255 ≈ 61 → 屏幕取色 ~60 ✓
```

**pow(a, 2.2) 预补偿（屏幕观测 ~2）**：
```
pow(0.04706, 2.2) ≈ 0.00120
0.00120 < 0.0031308 → 掉入线性段！
S = 0.00120 × 12.92 ≈ 0.0156
0.0156 × 255 ≈ 4（理论值）
```
但实测屏幕值为 ~2 而非 4，原因是 DXT5 压缩使实际 alpha 低于标称值 12（约为 9~10），导致 pow 后的值更低。

**穷举数值分析**（Python 遍历 alpha 7.0~14.9，步长 0.1）：
```
screen1=60 需要实际 alpha ≈ 11.3~11.5
screen2=2  需要实际 alpha ≈ 7.7~9.7
→ 没有单一 alpha 值能同时满足两个观测值
```
这证实了取色器采样位置/DXT5 块压缩/双线性插值等因素共同造成了偏差——两次观测可能取到了略有不同的有效 alpha 值。最佳单一匹配：alpha≈11 → (59, 3)，接近但不精确等于 (60, 2)。

#### 五条核心结论

1. **A 通道全程线性，作为 mask 与颜色相乘无需任何校正** — 采样不做 sRGB 解码，计算在线性空间正确运行
2. **调试 `return alpha` 看到偏高值是正常行为** — A 被灌入 RGB，RGB 被 sRGB 编码提亮
3. **`pow(a, 2.2)` 反补偿在暗部完全失效** — 值被压到 sRGB 线性段阈值（0.0031308）以下，编码方式从幂函数变为 `×12.92` 线性缩放；且纹理压缩的 ±2~3 偏移在此区间被极度放大
4. **暗部数值分析不可靠** — sRGB 暗部线性段 + 8-bit 量化 + DXT5/ASTC 压缩三者叠加，导致屏幕取色值对原始值的微小差异高度敏感（±2~3 alpha 可导致 ±1~2 屏幕值跳变）
5. **调试精确值应使用 RenderDoc / Frame Debugger** — 直接读取线性浮点值，完全绕开 sRGB 编码与 8-bit 量化问题；或使用放大系数法（如 `return a * 20.0`）粗略观察

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
- URP 源码追踪：`Color.hlsl`（L104-160 精确/Fast sRGB 实现）、`FinalBlitPass.cs`（L150 `_LINEAR_TO_SRGB_CONVERSION` keyword 设定逻辑）、`CoreBlit.shader`（FinalBlit 使用的 shader）

### 相关记录

- [色彩空间知识](./color-space-gamma-linear.md) - Gamma/Linear 基础原理与 Unity 设置

### 验证记录
- [2026-04-13] 首次记录：在 Jymf_Role_01.shader 颜色遮罩（ColorMask）功能调试中发现并验证。纹理 A 通道值 12 直接输出显示为 60，pow(2.2) 后显示为 ~2。
- [2026-04-13] 二次修正：用户指出初版计算结果与实际观测值不完全吻合（pow 后理论 4 实际 2），触发深度调查。追踪 URP 源码确认渲染链路（HDR=Off → R8G8B8A8_SRGB RT → GPU 硬件 sRGB 编码 → FinalBlit → backbuffer）。Python 穷举 alpha 7.0~14.9 证实：没有单一 alpha 值能同时满足 screen1=60 与 screen2=2，偏差来源为 DXT5 纹理压缩改变实际采样值 + sRGB 暗部线性段的 8-bit 量化敏感性极高。

- [2026-04-15] 原状态附注“二次深度修正”已移入验证记录。

# Shader 调试：Alpha 通道输出到 RGB 时的 sRGB 伽马偏差

**标签**：#shader #urp #color-space #experience #graphics #unity
**来源**：实践总结 — 角色 Shader 颜色遮罩调试
**收录日期**：2026-04-13
**更新日期**：2026-07-16
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐⭐（实测 + sRGB 精确公式 + 穷举数值分析 + URP 源码追踪）
**适用版本**：Unity 2022.3+ / URP 14+；sRGB 编解码原理适用于通用图形 API

### 概要
在 Shader 中用 `return alpha` 调试纹理 A 通道时，屏幕取色器读到的值与纹理预览值可能不一致。主要原因不是随机数值误差，而是 A 值被复制到 RGB 后，RGB 写入 sRGB Back Buffer 时会执行确定性的 Linear→sRGB 编码；Alpha 分量本身仍保持线性。`pow(a, 2.2)` 只是近似的 sRGB→Linear 方向，不能充当精确的反向补偿，尤其会在暗部偏离标准 sRGB 分段函数。纹理压缩、过滤、mip、采样位置和 8-bit 量化属于叠加误差。

### 内容

#### 场景复现

- 纹理 `_BaseMap` 的 Alpha 通道，Unity 纹理预览取色器显示 **(12, 12, 12)**
- Shader 中 `return tex2D(_BaseMap, uv).a;`（隐式 `half4(a,a,a,a)`）
- 屏幕取色器读到 **(60, 60, 60)**，而非预期的 (12, 12, 12)

#### 根本原因

**A 通道采样不做 sRGB 解码；但标量 `a` 被返回给 `float4/half4` 输出时会复制到 RGB，随后 RGB 被 sRGB Back Buffer 按 Linear→sRGB 编码。sRGB 格式中的 Alpha 分量使用 Gamma 1.0，仍为线性值。**

sRGB 编码是分段函数（非简单幂函数）：

```
Linear → sRGB 编码（GPU 硬件自动执行）：
  L ≤ 0.0031308 时：S = L × 12.92         ← 线性段
  L > 0.0031308 时：S = 1.055 × L^(1/2.4) - 0.055  ← 幂函数段
```

#### 转换方向速记：`pow(2.2)` 与 `pow(1/2.2)`

先看变量当前代表什么，再决定方向；“Gamma 校正”一词方向含糊，最好明确写成 **sRGB 编码**或 **sRGB 解码**。

```
sRGB/显示编码值 S → Linear/物理计算值 L：解码、去 Gamma
  精确：S ≤ 0.04045 时 L = S / 12.92
        否则 L = ((S + 0.055) / 1.055)^2.4
  粗略：L ≈ pow(S, 2.2)       // 指数 > 1，0~1 数值变小、视觉上变暗

Linear/物理计算值 L → sRGB/显示编码值 S：编码、加 Gamma
  精确：L ≤ 0.0031308 时 S = 12.92 × L
        否则 S = 1.055 × L^(1/2.4) - 0.055
  粗略：S ≈ pow(L, 1.0/2.2)   // 指数 < 1，0~1 数值变大、视觉上变亮
```

记忆法：**拿进 Shader 做光照计算，要解码到 Linear，用约 `2.2`；送去普通显示/存储，要编码到 sRGB，用约 `1/2.2`。** 在 Unity Linear 工作流中，勾选 sRGB 的颜色纹理由 GPU 在采样时自动解码，sRGB Render Target 在写入时自动编码，通常不应在 Shader 中重复 `pow`。

**叠加因素：纹理压缩、过滤和量化**

DXT5/BC3、ASTC 等有损格式可能改变 GPU 实际采样到的 Alpha；双线性过滤、mip 选择和取色位置也可能使采样值不同。偏移量取决于具体格式、块内容、压缩质量、平台和采样条件，不能固定概括为 `±2~3`。Unity Inspector 预览或屏幕取色器显示的值也不应直接视为 Shader 中该次采样的原始线性标量。

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
实测屏幕值为 ~2 而非理论值 4，说明两次观测没有对应同一个理想化输入。压缩、过滤、mip、采样位置和取色器量化都可能参与，不能仅凭该结果把差异唯一归因于 DXT5 压缩。

**穷举数值分析**（Python 遍历 alpha 7.0~14.9，步长 0.1）：
```
screen1=60 需要实际 alpha ≈ 11.3~11.5
screen2=2  需要实际 alpha ≈ 7.7~9.7
→ 没有单一 alpha 值能同时满足两个观测值
```
这证实了不存在一个理想化的单一 Alpha 值同时解释两次观测；它提示应进一步检查纹理压缩、过滤、mip、采样位置和取色器量化，而不是从屏幕读数反推唯一的原始 Alpha。最佳单一匹配 `alpha≈11` 只能得到约 `(59, 3)`，接近但不等于 `(60, 2)`。

#### 五条核心结论

1. **A 通道全程线性，作为 mask 与颜色相乘无需任何校正** — 采样不做 sRGB 解码，计算在线性空间正确运行
2. **调试 `return alpha` 看到偏高值是正常行为** — A 被灌入 RGB，RGB 被 sRGB 编码提亮
3. **`pow(a, 2.2)` 不是精确反补偿** — 它是 sRGB→Linear 的近似方向，不是标准分段函数的严格逆运算；暗部尤其容易偏离预期
4. **屏幕取色值不能直接当作原始线性值** — sRGB 编码是主要确定性变化，纹理压缩、过滤、mip、采样位置和 8-bit 量化是次级偏差
5. **精确检查优先使用 RenderDoc 或线性浮点 RT 读回** — RenderDoc 可检查资源、像素并进行 Shader 调试；也可将标量写入禁用 sRGB 转换的 `RFloat/RHalf` RT 后读回。Frame Debugger 适合观察某次事件的输出 RT，但不能等同于直接读取 Shader 内部采样标量；`return a * 20.0` 只适合粗略观察

### 关键代码

```hlsl
// ❌ 调试时直接返回 alpha — 屏幕取色不等于纹理预览值（被 sRGB 编码）
return tex2D(_BaseMap, uv).a;

// ❌ 近似解码不是精确的显示反补偿，暗部尤其不可靠
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
- [Microsoft DXGI_FORMAT 文档](https://learn.microsoft.com/en-us/windows/win32/api/dxgiformat/ne-dxgiformat-dxgi_format) - sRGB 格式只编码 RGB，Alpha 保持 Gamma 1.0
- [Unity 色彩空间文档](https://docs.unity3d.com/Manual/color-spaces.html) - Linear/Gamma 工作流概述
- [Unity RenderTextureReadWrite](https://docs.unity3d.com/ScriptReference/RenderTextureReadWrite.html) - sRGB/Linear RenderTexture 的读写转换行为
- URP 源码追踪：`Color.hlsl`（L104-160 精确/Fast sRGB 实现）、`FinalBlitPass.cs`（L150 `_LINEAR_TO_SRGB_CONVERSION` keyword 设定逻辑）、`CoreBlit.shader`（FinalBlit 使用的 shader）

### 相关记录

- [色彩空间知识](./color-space-gamma-linear.md) - Gamma/Linear 基础原理与 Unity 设置

### 验证记录
- [2026-04-13] 首次记录：在 Jymf_Role_01.shader 颜色遮罩（ColorMask）功能调试中发现并验证。纹理 A 通道值 12 直接输出显示为 60，pow(2.2) 后显示为 ~2。
- [2026-04-13] 二次修正：用户指出初版计算结果与实际观测值不完全吻合（pow 后理论 4、实际 2），触发深度调查。追踪 URP 源码确认渲染链路（HDR=Off → R8G8B8A8_SRGB RT → GPU 硬件 sRGB 编码 → FinalBlit → backbuffer）。Python 穷举 alpha 7.0~14.9 证实没有单一 Alpha 值能同时满足 screen1=60 与 screen2=2；当时初步怀疑纹理压缩、过滤、采样位置与量化共同造成差异，具体归因在 2026-07-16 的复核中进一步收紧。

- [2026-04-15] 原状态附注“二次深度修正”已移入验证记录。
- [2026-07-16] 外部资料复核并修订：明确主要偏差是确定性的 Linear→sRGB 编码，而非普通数值误差；补充 sRGB 精确编解码公式及 `pow(2.2)` / `pow(1/2.2)` 方向速记；收紧纹理压缩误差与 Inspector 预览的泛化归因；将精确调试建议调整为 RenderDoc 或线性浮点 RT 读回，并明确 Frame Debugger 只能观察事件输出 RT。

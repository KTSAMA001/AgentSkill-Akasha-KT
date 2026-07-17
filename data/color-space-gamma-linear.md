# Unity 中的 Gamma、Linear 与 sRGB 色彩空间

**标签**：#graphics #knowledge #color-space #gamma #linear
**来源**：Unity 官方文档、Unity Graphics ShaderLibrary、Microsoft DXGI 文档与实践复核
**来源日期**：2021-01-06
**收录日期**：2026-01-31
**更新日期**：2026-07-17
**状态**：📘 有效
**可信度**：⭐⭐⭐⭐⭐（官方文档 + 官方源码 + 实践复核）
**适用版本**：Unity 2022.3+ / URP 14+ / Unity 6；sRGB 编解码原理适用于通用图形 API

### 概要

Unity 的 Linear 工作流通常会根据纹理和 RenderTarget 的格式自动完成 sRGB↔Linear 转换，因此普通 URP Shader 不应习惯性手写 `pow(2.2)`。颜色纹理应标记为 sRGB，让 GPU 在采样时自动解码；法线、Mask、Metallic、Roughness 等数据纹理应保持 Linear；Shader 输出到 sRGB RenderTarget 时由 GPU 自动编码。只有数据跨越了一个没有自动转换的边界，且当前编码与目标编码明确不一致时，才需要手动调用 `SRGBToLinear` 或 `LinearToSRGB`。

### 内容

## 1. 先区分三种东西

### Linear 值

Linear 值用于光照、混合、插值和大多数物理意义上的计算。数值翻倍，代表能量或亮度贡献近似翻倍。

### sRGB 编码值

sRGB 是为了存储和显示颜色而使用的非线性编码。它给暗部更多编码精度，但不能直接拿来做物理光照计算。

### “Gamma 校正”

“Gamma 校正”经常被同时用于两个相反方向，容易产生歧义。记录和代码中应优先写清楚：

- **sRGB→Linear**：解码、去 Gamma，用于进入 Shader 计算
- **Linear→sRGB**：编码、加 Gamma，用于显示或存储

## 2. `pow(2.2)` 与 `pow(1/2.2)` 的方向

```
sRGB/显示编码值 S → Linear/物理计算值 L
粗略近似：L ≈ pow(S, 2.2)

Linear/物理计算值 L → sRGB/显示编码值 S
粗略近似：S ≈ pow(L, 1.0 / 2.2)
```

记忆法：

> 进入 Shader 做光照计算，用约 `2.2`；离开 Shader 送去普通显示，用约 `1/2.2`。

对 `0~1` 的数：

```
pow(0.5, 2.2)       ≈ 0.218  // 指数 > 1，数值变小
pow(0.5, 1.0 / 2.2) ≈ 0.730  // 指数 < 1，数值变大
```

但标准 sRGB 是分段函数，不等同于单一的 Gamma 2.2。

### 精确 sRGB→Linear

```
S ≤ 0.04045：L = S / 12.92
S > 0.04045：L = ((S + 0.055) / 1.055)^2.4
```

### 精确 Linear→sRGB

```
L ≤ 0.0031308：S = 12.92 × L
L > 0.0031308：S = 1.055 × L^(1/2.4) - 0.055
```

需要显式转换时，优先使用 Unity ShaderLibrary 中的 `SRGBToLinear`、`LinearToSRGB`，不要自行散落近似 `pow`。

## 3. Unity Linear 工作流的自动转换链路

### 颜色纹理

Albedo、BaseColor、Diffuse、普通 LDR Emission 等颜色纹理通常存储为 sRGB：

```
磁盘/GPU 中的 sRGB 颜色纹理
  → Texture Importer 勾选 sRGB
  → GPU 采样时自动 sRGB→Linear
  → Shader 得到 Linear RGB
```

因此正常采样后不要再手动 `pow(rgb, 2.2)`，否则会重复解码并使颜色过暗。

### 数据纹理

Normal、Mask、Metallic、Roughness、AO、查找索引、噪声参数等不是“颜色”，其数值有明确的数据含义：

```
Texture Importer 关闭 sRGB
  → GPU 不做颜色空间转换
  → Shader 得到纹理中存储的数据值
```

如果把存放在 RGB 中的 Mask 错误标记为 sRGB，`0.5` 可能会被解码成约 `0.214`，阈值、插值和强度都会改变。

### Alpha 通道

sRGB 转换只作用于 RGB，Alpha 保持 Gamma 1.0，也就是线性值。因此颜色纹理勾选 sRGB 时，RGB 会自动解码，Alpha 不会。

### Shader 属性

在 Linear 项目中，ShaderLab 的 `Color` 属性会作为颜色转换后传入 Shader；`Float` 和 `Vector` 默认按原始数据处理。表示颜色时优先使用 `Color` 类型，表示参数或 Mask 时使用 `Float/Vector`，避免靠手写 `pow` 猜测语义。

### RenderTarget

- **sRGB RenderTarget**：Shader 输出视为 Linear RGB，写入时自动 Linear→sRGB；后续采样时自动 sRGB→Linear
- **Linear RenderTarget**：读写均不做 sRGB 转换，适合 Mask、法线、速度、ID 等数据
- **HDR 浮点 RenderTarget**：通常保持 Linear，不在中间 Pass 反复做 sRGB 编解码；最终输出到显示链路时再转换

### Gamma 项目

当项目 `Color Space` 设置为 Gamma 时，Unity 通常不会执行上述自动 sRGB↔Linear 转换，Shader 也会直接用编码后的值参与计算。此时仍不应对某一张普通纹理随意补一个 `pow`：如果某个自定义算法明确要求 Linear 输入，就要统一处理它依赖的全部颜色输入、计算过程和最终输出，而不是只转换局部采样。新项目和常规 PBR/URP 光照优先采用 Linear 工作流。

## 4. Unity Shader 中什么时候需要手动转换

原则只有一条：

> 当前数据的编码与下一步要求的编码不同，并且资源格式、Importer、Sampler 或 RenderTarget 没有替你自动转换时，才手动转换。

### 情况 A：资源标记与真实内容不一致，且暂时无法修正资源

例如一张实际存储 sRGB 颜色的纹理被当作 Linear 数据导入。最佳方案是修正 Texture Importer；只有资源来自外部插件、运行时流或无法改导入设置时，才在 Shader 中手动：

```hlsl
float3 linearColor = SRGBToLinear(sampledSRGB);
```

反过来，如果资源本身已经是 Linear 数据，就不应标记为 sRGB，也不应再次解码。

### 情况 B：颜色通过不支持 sRGB 视图的原始数据通道传入

例如 sRGB 编码颜色被装进：

- `StructuredBuffer` / `ByteAddressBuffer`
- Compute Shader 的 `RWTexture` / UAV 路径，且资源视图没有提供 sRGB 自动转换
- 自定义 packed integer
- 网络、视频插件或原生插件提供的原始缓冲
- CPU 上传的数值数组

这些数据没有纹理 sRGB Sampler 自动解码。如果协议规定其中存的是 sRGB 颜色，需要手动 `SRGBToLinear`。

### 情况 C：要把 Linear 结果写入不自动编码的存储

例如将颜色写进 Linear RT、原始 Buffer、文件或自定义编码协议，而接收方要求 sRGB 编码值：

```hlsl
float3 encodedSRGB = LinearToSRGB(linearColor);
```

如果目标本身是 sRGB RenderTarget，则不要手动编码，否则会重复执行 Linear→sRGB。

### 情况 D：手动渲染路径的 RT 格式或 sRGB Write 状态不明确

使用 `Graphics.SetRenderTarget`、自定义原生渲染、插件纹理或特殊 Blit 链时，要核对：

- 目标 GraphicsFormat 是否为 sRGB
- `RenderTexture.sRGB` 是否符合内容语义
- 当前平台和路径是否自动启用 sRGB Write
- 前一个 Pass 是否改变了相关状态

优先修正 RT 格式和资源声明；`GL.sRGBWrite` 属于特殊兼容手段，不应成为常规 URP Shader 的默认做法。

### 情况 E：自定义 LUT 或外部颜色处理链明确要求不同输入域

LUT 没有统一的固定 `pow` 配方。必须先确认：

- LUT 是以 Linear 还是 sRGB 值作为查询坐标
- LUT 纹理内容以 Linear 还是 sRGB 编码存储
- 输出要求回到 Linear 继续后处理，还是已经是显示编码值

URP 内置 Color Lookup 应交给管线处理。只有自定义 LUT 的制作域、导入设置和 Shader 查询域不一致时，才在明确的边界转换。未经确认不要套用“输入 `pow(1/2.2)`、输出 `pow(2.2)`”之类的固定模板。

### 情况 F：数值调试、截图、读回或外部工具比较

当需要比较“Shader 内的 Linear 浮点值”和“屏幕/PNG 中的 sRGB 8-bit 值”时，必须明确比较的是哪一个域。可选择：

- 写入 Linear 浮点 RT 后读回真实计算值
- 显式 `LinearToSRGB` 后写入不自动编码的输出
- 使用 RenderDoc 查看资源格式、像素值和 Shader 中间结果

这类转换只为调试或数据交换服务，不应反过来污染正式光照计算。

## 5. 通常不需要手动转换的场景

| 场景 | 正确做法 |
|---|---|
| URP 中采样 Albedo/BaseColor | 纹理勾选 sRGB，直接采样 |
| 采样 Normal/Mask/Metallic/Roughness | 关闭 sRGB，直接使用 |
| 使用颜色纹理的 Alpha 作为 Mask | Alpha 直接使用，不做 `pow` |
| Shader 输出普通颜色到相机目标 | 输出 Linear 结果，由管线处理 |
| HDR 中间后处理 | 保持 Linear 浮点链路 |
| ShaderLab `Color` 属性 | 直接使用 Unity 传入值 |
| URP 内置后处理与 Color Lookup | 交给 URP 管线管理转换 |

## 6. 排查清单

看到颜色过亮、过暗或 Mask 数值异常时，按顺序检查：

1. 项目 `Color Space` 是 Linear 还是 Gamma？
2. 数据是颜色，还是有数值意义的 Mask/参数？
3. Texture Importer 的 `sRGB (Color Texture)` 是否与内容一致？
4. 问题通道是 RGB 还是 Alpha？
5. RenderTexture/GraphicsFormat 是 sRGB、Linear 还是 HDR Float？
6. 当前路径是否已经自动转换，是否又手动调用了一次转换？
7. LUT、插件、视频、Buffer 或文件协议规定的输入/输出域是什么？
8. 屏幕取色器看到的是显示编码值，还是 Shader 内的 Linear 值？

### 关键代码

```hlsl
#include "Packages/com.unity.render-pipelines.core/ShaderLibrary/Color.hlsl"

// 仅在输入确实是 sRGB 编码、且采样路径没有自动解码时使用
float3 linearColor = SRGBToLinear(encodedSRGB);

// 仅在目标要求 sRGB 编码、且写入路径没有自动编码时使用
float3 encodedColor = LinearToSRGB(linearColor);
```

### 参考链接

- [Unity TextureImporter.sRGBTexture](https://docs.unity3d.com/ScriptReference/TextureImporter-sRGBTexture.html) - 纹理采样时的自动 sRGB→Linear 转换
- [Unity RenderTextureReadWrite](https://docs.unity3d.com/ScriptReference/RenderTextureReadWrite.html) - RenderTexture 的 sRGB/Linear 读写行为
- [Unity Graphics.SetRenderTarget](https://docs.unity3d.com/ScriptReference/Graphics.SetRenderTarget.html) - 手动渲染路径中的 sRGB Write 状态注意事项
- [Unity Shader 属性与颜色空间](https://docs.unity3d.com/Manual/SL-PropertiesInPrograms.html) - Color 与 Float/Vector 属性的转换差异
- [Unity Graphics Color.hlsl](https://github.com/Unity-Technologies/Graphics/blob/master/Packages/com.unity.render-pipelines.core/ShaderLibrary/Color.hlsl) - `SRGBToLinear`、`LinearToSRGB` 的官方实现
- [Microsoft DXGI_FORMAT](https://learn.microsoft.com/en-us/windows/win32/api/dxgiformat/ne-dxgiformat-dxgi_format) - sRGB 格式对 RGB 与 Alpha 的处理

### 相关记录

- [Shader 调试：Alpha 通道输出到 RGB 时的 sRGB 伽马偏差](./shader-debug-alpha-srgb-encoding-pitfall.md) - Alpha 线性值写入 RGB 后被 sRGB 编码的调试案例
- [ACES Tone Mapping](./aces-tone-mapping.md) - HDR Linear 场景值映射到显示输出的处理

### 验证记录

- [2026-01-31] 初次收录，来源于历史色彩空间学习笔记。
- [2026-04-15] 结构修复：补齐模板必填章节，未改动原结论。
- [2026-07-17] 全面复核并重写：将 Gamma 2.2 明确为 sRGB 的近似而非精确公式；补充标准 sRGB 分段函数、Unity 自动采样/RT 转换链路、RGB 与 Alpha 差异、手动转换的六类边界场景；移除未经输入域约束的 LUT 固定 `pow` 配方，改为按 LUT 制作域、存储域和查询域判断。

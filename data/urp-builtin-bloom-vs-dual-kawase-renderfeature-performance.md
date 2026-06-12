# URP 内置 Volume Bloom 与自定义 Dual Kawase RenderFeature 的性能对比（Quest VR 场景）

**收录日期**：2026-06-12
**标签**：#unity #urp #renderer-feature #performance #experience
**来源**：Quest VR 项目自定义 Bloom RenderFeature 实践，对比结论逐行核查 URP 14.0.12 包源码
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐（源码逐行核查；GPU 帧时间差值未做真机 A/B 实测）
**适用版本**：Unity 2022.3 / URP 14.0.x（PostProcessPass + Volume 体系；Unity 6 的 RenderGraph 路径未核对）

**问题/场景**：

移动 VR（Quest 系）需要 Bloom 时，应该用 URP 内置 Volume Bloom，还是自写 RenderFeature？两者性能差距有多大、差在哪里？

### 概要

URP 14 内置 Bloom 默认配置是 **16 个 Blit、1/2 分辨率起步、每级高斯 2 pass**，且必须附带 UberPost 全分辨率 pass 与 ColorGradingLUT pass；自定义 Dual Kawase RenderFeature（6 Blit、1/4 起步、Blend One One 直接叠加）可把 Bloom 相关 GPU 开销压到内置的约 1/3~1/4。内置的代价换来的是质量功能（scatter/HQ filtering/lens dirt/tonemapping 耦合），不是性能。

### 内容

#### 内置 Bloom 的结构（URP 14.0.12 `Runtime/Passes/PostProcessPass.cs` SetupBloom，1064-1133 行）

- **1/2 分辨率起步**（1066 行 "Start at half-res"，`BloomDownscaleMode.Half` 为默认）。
- 降采样链**每级 2 个 pass**（1115-1119 行注释：两段式高斯——9-tap 降采样 + 5-tap 二次模糊）。
- 默认 `maxIterations = 6` 时共 **1（Prefilter）+ 5×2（Down）+ 5（Up）= 16 个 Blit**。
- mip 链 RT 共 12 张（MipUp/MipDown 各 6）。
- LDR（HDR 关闭）下走 `_USE_RGBM` 编解码路径（1097 行），每次采样附加编解码 ALU。

#### 隐藏成本：开启 Volume 后处理本身的固定开销

内置 Bloom 无法单独启用，必须走完整后处理管线：

1. **UberPost 全分辨率 pass**：Bloom 结果不直接叠加，而是作为纹理在 uber 里采样合成（1144 行 `_Bloom_Texture` 喂给 uber）——整个相机颜色完整读写一遍（VR 双目全分辨率内存往返）。
2. **ColorGradingLUT pass**：只要 post processing 开启就每帧生成，哪怕只想要 Bloom。
3. **VolumeManager 每帧 CPU**：volume 栈混合求值。

#### 自定义 Dual Kawase RenderFeature 的对应设计

- 1/4 分辨率起步、每级 1 pass（Dual Kawase 核），典型档位 6 Blit。
- 合成用 **`Blend One One` 直接叠到相机颜色目标**：TBR GPU 上 dst 读取发生在片上 GMEM，省掉 uber 那次全屏内存往返——这是 Quest 带宽下收益最大的单项。
- 无 LUT、无 volume 求值，CPU 侧实测（Quest2 真机 Profiler）约 0.02ms / 零 GC。

#### 对比表（全分辨率当量带宽为估算值）

| | 内置 Bloom（默认） | Dual Kawase RenderFeature（Lite 档） |
|---|---|---|
| Blit 数 | 16 | 6 |
| 链路起点 | 1/2 res | 1/4 res（顶层像素量为内置的 1/4） |
| 每级模糊 | 高斯 2 pass | Dual Kawase 1 pass |
| 链路带宽（全分辨率当量，估算） | ~0.7 | ~0.16 |
| 附带固定成本 | UberPost 全屏 pass + LUT pass | 无（Blend One One 片上叠加） |
| mip RT 数 | 12 | 7 |

#### 结论与适用判断

- 内置 Volume Bloom **不是性能更优的选项**；它为通用性与质量功能设计（scatter 连续调节、HQ bicubic、lens dirt、tonemapping 正确耦合）。
- 移动 VR 上若只需要 Bloom 且对带宽敏感，自定义 RenderFeature 的结构性优势约 3~4 倍。
- 做内置 vs 自定义的真机 A/B 时，**应给内置开 HDR 才公平**——LDR 下内置走 RGBM 路径表现更差。

### 参考链接

- [URP 14 PostProcessPass.cs（needle-mirror 镜像）](https://github.com/needle-mirror/com.unity.render-pipelines.universal/blob/master/Runtime/Passes/PostProcessPass.cs) - SetupBloom 源码
- [URP Bloom shader 源码注解（Xibanya）](https://xibanya.github.io/URPShaderViewer/Library/URP/Shaders/PostProcessing/Bloom.html) - RGBM 路径与 pass 结构
- 本地核查路径（项目内）：`Library/PackageCache/com.unity.render-pipelines.universal@14.0.12/Runtime/Passes/PostProcessPass.cs`

### 相关记录

- [Godot Bloom：Fast Mipmap Dual Kawase 4K 实践](./godot-bloom-fast-mipmap-dual-kawase-4k-practice.md) - Dual Kawase 算法来源
- [URP RenderFeature 每帧 GC 排查](./urp-renderfeature-per-frame-gc-pitfalls.md) - 同一 RenderFeature 的零 GC 实践
- [后处理模糊算法综述（知乎留档）](./zhihu-postprocessing-blur-algorithms.md) - 高斯/Kawase/Dual Kawase 算法对比背景

### 验证记录

- [2026-06-12] 初次记录。内置 Bloom 的 Blit 数、起步分辨率、两段式高斯结构、RGBM 路径、uber 合成方式均逐行核查 URP 14.0.12 本地包源码（SetupBloom 1064-1144 行）确认；自定义侧 CPU 0.02ms / 零 GC 为 Quest2 真机 Profiler 实测。带宽当量与 1/3~1/4 总开销为结构推算，未做内置 vs 自定义的 GPU 帧时间真机 A/B。

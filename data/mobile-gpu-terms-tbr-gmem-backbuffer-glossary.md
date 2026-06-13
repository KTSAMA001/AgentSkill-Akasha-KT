# 移动 GPU 渲染术语速查：TBR/GMEM/backbuffer/带宽/Load-Store 等

**收录日期**：2026-06-12
**标签**：#graphics #knowledge #performance
**来源**：Quest VR Bloom 优化实践中反复出现的术语，定义经官方文档与硬件厂商资料核对
**状态**：📘 有效
**可信度**：⭐⭐⭐⭐（业界通用概念 + 实践语境核对）
**适用版本**：通用（以移动 TBR GPU / Quest 系 Adreno 为主要语境）

**问题/场景**：

渲染优化记录里高频出现 GMEM、backbuffer、TBR、Load/Store、带宽当量等术语，但没有集中解释，跨记录阅读时容易卡住。本记录是这些术语的速查表，按"定义 → 为什么在移动 VR 优化里重要"组织，并标注它们在相关记录中的出现语境。

### 概要

移动 GPU 优化的核心叙事只有一句话：**显存带宽是最贵的资源，片上内存（GMEM）是免费的**。本表的所有术语几乎都围绕这句话展开：TBR 架构为省带宽而生，GMEM 是它的片上工作区，Load/Store 是数据进出 GMEM 的收费站，backbuffer/中间 RT 是数据的最终去向，而"全屏内存往返"就是优化要消灭的对象。

### 内容

#### TBR / TBDR（Tile-Based Rendering / Tile-Based Deferred Rendering）

移动 GPU（Adreno/Mali/PowerVR，含 Quest 的 Adreno）的基本架构：把屏幕切成小块（tile，如 32×32 像素），**一个 tile 的全部绘制在片上小内存里完成，结束后才把结果一次性写回显存**。与之相对的是桌面 GPU 的 IMR（立即模式渲染，画一笔写一笔显存）。

为什么重要：TBR 把"每像素反复读写显存"变成"每 tile 一次写回"，是移动端在功耗墙内做实时渲染的根基。所有移动端优化建议（少切 RT、少全屏 pass、能混合不拷贝）都是在配合这个架构。

#### GMEM / 片上 tile memory / on-chip

TBR 架构里那块"片上小内存"在 Adreno 的叫法（Mali 叫 tile buffer，概念相同）。容量很小（KB 级），但访问速度极快且**不占外部显存带宽**。

为什么重要：发生在 GMEM 内的操作接近免费——最典型的是**硬件混合（Blending）读取目标颜色**：`Blend One One` 叠加时 dst 读取直接发生在 GMEM，零外部带宽。这就是"用 Blend One One 直接叠到相机颜色目标，省一次全屏 copy"成立的硬件原理。反之，把 RT 当纹理采样则必须走显存。

#### Load Action / Store Action（DontCare / Load / Store / Resolve）

每个渲染 pass 开始时，GMEM 需要决定**是否从显存把已有内容搬进来**（Load）；结束时决定**是否把结果写回显存**（Store）。`DontCare` 表示跳过搬运。

为什么重要：一次 Load + Store 就是一次全分辨率显存往返。优化点：不需要旧内容的 RT（如 bloom 链每级）应 `DontCare` 加载；URP 的 `Blitter.BlitCameraTexture` 重载里显式传 `RenderBufferLoadAction.DontCare` 就是在做这件事。MSAA 下 GMEM 里是多倍采样数据，Store 前在片上做 Resolve（合并采样点）远比写回多倍数据便宜。

#### backbuffer / frontbuffer / swapchain（交换链）

- **frontbuffer**：屏幕当前正在显示的那张图。
- **backbuffer**：GPU 正在绘制的下一帧目标，画完与 frontbuffer 交换（swap），避免撕裂。
- **swapchain**：管理这组缓冲轮换的队列。VR 下 swapchain 由系统合成器（Quest 的 Compositor）持有，App 把眼缓冲（eye buffer）提交给它做畸变合成，而不是直接上屏。

为什么重要：backbuffer/swapchain 图像通常有格式与用法限制（如 Quest 固定 8-bit sRGB、不可随意当纹理采样）。所以管线内部要做后处理时，不能直接在 backbuffer 上操作。

#### 中间 RT（Intermediate Texture）

URP 在"相机颜色"与 backbuffer 之间插入的一张普通 RenderTexture：场景先画到它上面，最后经 FinalBlit 拷到 backbuffer/eye buffer。URP Renderer 上的 `Intermediate Texture` 选项控制是否强制存在。

为什么重要：自定义后处理（采样它、向它叠加）只有在它存在时才合法——这就是 Bloom RenderFeature 依赖 `Intermediate Texture = Always` 的原因。代价是多一次 FinalBlit 全屏拷贝，所以 URP 默认 Auto（不需要时直通 backbuffer 省带宽）。

#### Blit / 全屏 pass / "全屏内存往返"

Blit = 画一个覆盖全屏的三角形，把源纹理经 shader 处理后写到目标 RT，是后处理的基本单元。"全屏内存往返"指一次全分辨率 RT 的完整读出 + 写回（VR 下 ×2 眼）。

为什么重要：移动端后处理成本基本 = Blit 次数 × 各自分辨率的带宽。这就是 bloom 对比记录里用"全分辨率当量带宽"做尺子的原因：1/4 分辨率的 Blit 只算 1/16 张全屏（两个维度各 1/4）。

#### 带宽（Bandwidth）/ bpp（bits per pixel）

带宽 = 单位时间 GPU 与显存间搬运的数据量；bpp = 每像素占用位数，直接决定一张 RT 的搬运成本。常见格式：`RGBA8`=32bpp、`B10G11R11`=32bpp、`FP16(RGBA16F)`=64bpp。

为什么重要：移动 GPU 算力（ALU）相对便宜、带宽相对昂贵且直接转化为发热。"开 HDR 用 B10G11R11 带宽不变"这类结论全部由 bpp 推出。

#### UNorm / 存储钳制

UNorm（Unsigned Normalized）格式（如 RGBA8）把 0~255 整数映射为 0.0~1.0，**写入时硬件强制钳到 [0,1]**，相当于每个 fragment shader 末尾自带 saturate。shader 里算出 >1 没问题（ALU 是 float），存进 UNorm RT 那一刻被砍。

为什么重要：这是"LDR 管线下颜色无法超过 1"的物理原因，与之配套的变通手段（RGBM 编码、曝光缩放）和直接换浮点格式（开 HDR）的取舍见 HDR 相关讨论。

#### sRGB 硬件编解码

UNorm 格式可带 `_SRGB` 后缀（如 `R8G8B8A8_SRGB`）：写入时硬件自动做线性→sRGB 编码、采样时自动解码，**零 ALU 成本**，且 8-bit 存储配合 sRGB 曲线正好把精度分配给人眼敏感的暗部。

为什么重要：浮点格式（B10G11R11/FP16）没有 sRGB 变体，只能线性存储——这是"开 HDR 丢硬件 sRGB 编码 → 暗部 banding 风险"的来源，是 HDR 真实代价里比带宽更需要警惕的一项。

#### texel / texel size

texel = 纹理上的一个像素。texel size = `(1/宽, 1/高)`，即 UV 空间里移动一个 texel 的步长。模糊核的采样偏移都以它为单位（偏移 = texel size × 半径系数）。

为什么重要：多级链路中每级分辨率不同，texel size 必须按**当前 Blit 的源**逐次注入，拿错一级会导致模糊宽度错乱。

#### fireflies（萤火虫噪点）

HDR 场景里孤立的极亮像素（如高光点）经低分辨率降采样链放大后形成的闪烁亮斑，VR 中随头动剧烈跳动，观感极差。

为什么重要：bloom prefilter 里的 clamp（亮度上限钳制）就是专门抑制它的；LDR 管线（上限 1）天然不存在此问题。

### 参考链接

- [Qualcomm Adreno GPU 最佳实践（官方）](https://docs.qualcomm.com/bundle/publicresource/topics/80-78185-2/best_practices.html) - TBR/GMEM/Load-Store 行为
- [ARM Mali GPU 最佳实践（官方）](https://developer.arm.com/documentation/101897/latest/) - tile buffer 与带宽优化通则
- [Unity 官方：URP 移动端优化](https://docs.unity3d.com/Packages/com.unity.render-pipelines.universal@14.0/manual/optimize-for-better-performance.html) - Intermediate Texture / 后处理成本

### 相关记录

- [URP RenderFeature 自定义后处理完整案例](./urp-renderfeature-postprocess-case-dual-kawase-bloom.md) - GMEM/Blend 叠加/中间 RT 等术语的实战语境
- [URP 内置 Bloom vs 自定义 Dual Kawase 性能对比](./urp-builtin-bloom-vs-dual-kawase-renderfeature-performance.md) - "全分辨率当量带宽"的使用语境
- [移动端 TBDR 与 Overdraw](./mobile-tbdr-overdraw.md) - TBDR/Overdraw 在整条管线中的位置
- [Shader 调试：alpha 通道 sRGB 编码陷阱](./shader-debug-alpha-srgb-encoding-pitfall.md) - sRGB 硬件编解码的实际踩坑

### 验证记录

- [2026-06-12] 初次记录。术语定义按 Qualcomm/ARM/Unity 官方文档核对；实战语境引自本库 Bloom 系列记录（Quest2/3S 真机验证过的结论）。

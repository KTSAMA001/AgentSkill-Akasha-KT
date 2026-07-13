# Godot 4 中项目 3-LOD Mipmap Bloom 与改造版 Dual Kawase 的 4K 实践

**标签**：#godot #graphics #shader #experience #post-processing #performance
**来源**：AI 在 Godot 4 Bloom 对比项目中的实现与观察；Godot、Arm、Unity、Unreal 与 Microsoft 官方资料交叉验证
**收录日期**：2026-06-02
**来源日期**：2026-06-02
**更新日期**：2026-07-13
**状态**：⚠️ 待验证
**可信度**：⭐⭐⭐（Godot 屏幕纹理行为与 Dual Filtering 核已由官方资料交叉验证；当前项目的画质归因和 4K 性能只完成 FPS 粗测，尚无同条件 GPU timestamp）
**适用版本**：Godot 4.6.1 stable mono；Forward Plus；HDR 2D；Bloom 对比项目内 3840x2160 渲染预设

### 概要

本记录描述 Godot 4 示例项目中的两条具体 Bloom 实现：项目自定义的单全屏 Pass、3-LOD Mipmap 廉价基线，以及带同分辨率层级混合和额外全分辨率 tent composite 的改造版 Dual Kawase-style Pyramid。Godot 屏幕复制/mipmap 行为、Arm Dual Filtering 的标准 down/up 核和当前 shader 运算结构已经核对；“当前 Dual 画面更好、FPS 与 Fast 接近”只能保留为该项目的观察，不能推广为两类算法的普遍质量或性能排序。

### 内容

#### 实践背景与边界

本记录来自 AI 在 Godot 4 示例项目中实现 Bloom 算法对比的实践，不是用户亲自操作测试。项目目标是比较 Fast Mipmap、Dual Kawase、Wide Glare、自定义方案与 Godot 内置 Glow。

当前实践边界：

- 项目中名为 `RenderViewport` 的独立 `SubViewport` 控制实际后处理尺寸，预设包含 `1280x720`、`1920x1080`、`2560x1440`、`3200x1800`、`3840x2160`。
- 窗口只负责显示缩放，因此可以在小窗口中让 `SubViewport` 按 4K 尺寸渲染。
- 性能显示来自 `Engine.get_frames_per_second()` 的平均 FPS，不是独立 Bloom pass 的 GPU 时间。
- 当前记录没有 GPU timestamp、带宽计数器、关闭 VSync/帧率限制后的受控 benchmark，也没有证明测试始终处于 GPU bound。

#### 术语与结论边界

- “Fast Mipmap”是当前项目给廉价 3-LOD shader 起的模式名，不是行业中定义唯一、实现固定的标准算法。
- 多个 mip LOD 本身已经构成多尺度预过滤与混合。准确限制是“没有自定义显式 down/up 重建链”，而不是“没有多尺度扩散”。
- 当前 Dual 分支使用 Arm Dual Filtering 的 5-tap downsample 与 8-tap upsample 核，但还加入 `base_mix` 同级纹理、三次逐级累加以及最终 5-tap 全分辨率合成，因此应称为“改造版 Dual Kawase-style Pyramid”，不能直接代表 Arm 原始实现。
- Bloom 质量取决于亮部提取、有效点扩散函数（PSF）、半径、层级权重、能量归一化、重建滤波和最终合成，不能只按“Mipmap”或“Dual Kawase”名称排序。

#### 项目 3-LOD Mipmap Bloom

当前路线读取 Godot screen texture 的 mip 链：

```glsl
uniform sampler2D screen_texture : hint_screen_texture, repeat_disable, filter_linear_mipmap;
```

Godot 官方文档确认：

- 2D 中首次遇到使用 `hint_screen_texture` 的节点时，Godot 会把整个屏幕复制到 back buffer；后续节点默认复用这份副本。
- sampler 使用带 mipmap 的 filter 时，Godot 会自动准备可由 `textureLod` 读取的模糊 mip。
- 文档没有承诺屏幕 mip 的精确生成核、内部 Pass 数或跨渲染后端一致的性能成本，因此这些部分不能写成固定事实。

当前实现的逐帧顺序：

1. 场景渲染到 `RenderViewport`。
2. 首个 `hint_screen_texture` 使用者触发 2D 全屏 back-buffer copy。
3. `filter_linear_mipmap` 使 screen texture 具备可读取的 mip 层级。
4. 一个全分辨率 Fragment Pass 读取 `LOD 0` 原图和 3 个较高 LOD。
5. 当前 Pass 直接输出 `base + bloom`，没有项目自定义的逐级 upsample。

当前亮部提取函数：

```glsl
vec3 extract_bloom(vec3 color, float threshold_scale) {
    float brightness = max(max(color.r, color.g), color.b);
    float threshold = bloom_threshold * threshold_scale;
    float knee = max(soft_knee, 0.0001);
    float soft = clamp((brightness - threshold + knee) / (2.0 * knee), 0.0, 1.0);
    float contribution = max(brightness - threshold, 0.0) + soft * soft * knee;
    return color * clamp(contribution / max(brightness, 0.0001), 0.0, 1.0);
}
```

每个全屏像素读取 base color，再读取 3 个 mip LOD：

```glsl
float fast_lod = clamp(bloom_spread, 0.45, 2.25);
bloom += extract_bloom(textureLod(screen_texture, SCREEN_UV, 1.30 + fast_lod * 0.55).rgb, 0.90) * 0.62;
bloom += extract_bloom(textureLod(screen_texture, SCREEN_UV, 2.40 + fast_lod * 0.72).rgb, 0.56) * 0.28;
bloom += extract_bloom(textureLod(screen_texture, SCREEN_UV, 3.55 + fast_lod * 0.90).rgb, 0.34) * 0.10;
```

最终合成：

```glsl
vec3 combined = base + bloom * bloom_tint * bloom_intensity;
```

当前 3-LOD 基线的准确性质：

- shader 主体只有一个全分辨率输出 Pass，但依赖前置屏幕复制和引擎 mip 准备。
- 较高 LOD 的一个同 UV 样本代表原图中更宽的过滤足迹，不能描述为“只读取当前像素附近少量内容”。
- `filter_linear_mipmap` 的一次逻辑采样可在一个 mip 内做双线性过滤，并在相邻 mip 间插值；项目设置也可要求使用最近 mip。逻辑采样指令数不等于物理 texel 读取量或显存事务数。
- `spread` 主要改变 LOD 选择，不是严格卷积半径。
- “宽光晕和层次较弱”只描述当前 3 个 LOD、阈值、权重与合成参数，不是所有 mip/pyramid Bloom 的固有限制。

#### Arm 标准 Dual Filtering 与项目改造

Arm SIGGRAPH 2015 的 Dual Filtering 从 Kawase Blur 衍生而来，使用不同的 downsample 和 upsample 核，并在不同分辨率之间往返。原始示例的标准核为：

- Downsample：中心权重 4，加四个对角样本，总权重 8。
- Upsample：8 个样本，权重序列为 `1, 2, 1, 2, 1, 2, 1, 2`，总权重 12。
- 原始 upsample 示例只读取一个输入纹理，不包含同分辨率 `base_texture`。

当前项目管线：

1. 源场景只渲染一次到 `RenderViewport`。
2. Down chain：`1/2 -> 1/4 -> 1/8 -> 1/16`。
3. Up chain：`1/8 -> 1/4 -> 1/2`。
4. Final composite：全分辨率读取原图与半分辨率 Bloom 纹理。

逐帧读写关系：

| 阶段 | 主要输入 | 输出 | 输出分辨率 |
|---|---|---|---|
| Scene | 场景几何与材质 | `source` | `1x` |
| Down 0 | `source`，同时提取亮部 | `down[0]` | `1/2 x 1/2` |
| Down 1 | `down[0]` | `down[1]` | `1/4 x 1/4` |
| Down 2 | `down[1]` | `down[2]` | `1/8 x 1/8` |
| Down 3 | `down[2]` | `down[3]` | `1/16 x 1/16` |
| Up 2 | `down[3] + down[2]` | `up[2]` | `1/8 x 1/8` |
| Up 1 | `up[2] + down[1]` | `up[1]` | `1/4 x 1/4` |
| Up 0 | `up[1] + down[0]` | `up[0]` | `1/2 x 1/2` |
| Composite | `source + up[0]` | 最终画面 | `1x` |

每一级不会重绘场景，但会产生纹理读取、RT 写入、Render Target 切换和同步成本。

Downsample pass：

```glsl
vec2 offset = source_pixel_size * bloom_spread;
vec3 sum = read_source(UV) * 4.0;
sum += read_source(UV + offset * vec2(1.0, 1.0));
sum += read_source(UV + offset * vec2(-1.0, 1.0));
sum += read_source(UV + offset * vec2(1.0, -1.0));
sum += read_source(UV + offset * vec2(-1.0, -1.0));
COLOR = vec4(sum * 0.125, 1.0);
```

第一层设置 `extract_source = true`，后续层传播已提取的 Bloom 能量。5 个逻辑纹理采样的归一化核与 Arm 原始 downsample 结构一致。

Upsample pass：

```glsl
vec2 o = low_pixel_size * bloom_spread * 1.35;
vec3 up = vec3(0.0);
up += read_low(UV + vec2(-2.0 * o.x, 0.0));
up += read_low(UV + vec2(-o.x, o.y)) * 2.0;
up += read_low(UV + vec2(0.0, 2.0 * o.y));
up += read_low(UV + vec2(o.x, o.y)) * 2.0;
up += read_low(UV + vec2(2.0 * o.x, 0.0));
up += read_low(UV + vec2(o.x, -o.y)) * 2.0;
up += read_low(UV + vec2(0.0, -2.0 * o.y));
up += read_low(UV + vec2(-o.x, -o.y)) * 2.0;
up *= 0.0833333;

vec3 base = texture(base_texture, UV).rgb;
COLOR = vec4(up + base * base_mix, 1.0);
```

8-tap `up` 部分与 Arm 原始 upsample 核一致；`base_texture` 与 `base_mix = 0.55` 是项目扩展。它让每级重建重新注入同分辨率 down 结果，能形成更丰富的多尺度层次，但也改变了标准 Dual Filtering 的能量响应。

以恒定亮部、各 down/up 核均保持常量为前提做简化推导，三次 `up + base * 0.55` 会使单位响应约按 `1.0 -> 1.55 -> 2.10 -> 2.65` 累积。因此当前 Dual 与 Fast 的能量没有归一到相同基准，不能把“看起来更强或更有层次”完全归因于 Dual 核。

Final composite：

```glsl
vec3 base = texture(source_texture, UV).rgb;
vec2 o = bloom_pixel_size * bloom_spread;
vec3 bloom = read_bloom(UV) * 4.0;
bloom += read_bloom(UV + vec2(o.x, 0.0));
bloom += read_bloom(UV + vec2(-o.x, 0.0));
bloom += read_bloom(UV + vec2(0.0, o.y));
bloom += read_bloom(UV + vec2(0.0, -o.y));
bloom *= 0.125;
COLOR = vec4(base + bloom * bloom_tint * bloom_intensity, 1.0);
```

这个全分辨率 Pass 读取一次源图、五次半分辨率 Bloom，并执行最终加法合成。额外 5-tap tent filter 同样属于当前项目设计，不是 Arm 原始 Dual Filtering 必备步骤。

#### 4K 逻辑采样与像素成本

以 `3840x2160` 为例，全分辨率约为 `8.2944M` 像素。以下数字只统计 shader 中可见的逻辑纹理采样指令，不代表物理 texel 读取、缓存 miss 或显存事务。

当前 3-LOD Mipmap 基线：

- 全分辨率主 Pass：`8.2944M` 输出像素。
- 每像素 `base + 3 mip`，共 4 条逻辑纹理采样指令。
- 可见 shader 采样约为 `8.2944M x 4 = 33.1776M`。
- 另外存在 Godot 全屏 back-buffer copy 和 mip 准备成本；当前资料不足以把它们换算成固定采样数或 Pass 数。

当前改造版 Dual：

| 阶段 | 输出像素 | 每像素逻辑采样 | 逻辑采样总量 |
|---|---:|---:|---:|
| Down chain | `2.7540M` | 5 | `13.7700M` |
| Up chain | `2.7216M` | 9（8 个 low + 1 个同级 base） | `24.4944M` |
| Full-res composite | `8.2944M` | 6（1 个 source + 5 个 bloom） | `49.7664M` |
| 合计 | `13.7700M` shaded outputs | - | `88.0308M` |

由此可得：

- `13.77M` shaded outputs 的加总正确，但它只统计输出像素，不包含每像素 tap 数。
- 当前 Dual 的全分辨率 composite 约占可见逻辑采样指令的 56.5%，是主要成本之一。
- “多数中间 Pass 和中间 RT 像素位于低分辨率”成立；“当前 Dual 的大多数整体采样工作都在低分辨率”不成立。
- Fast 的一条 `filter_linear_mipmap` 指令与 Dual 的一条普通双线性采样，在潜在 texel 足迹、缓存行为和硬件代价上不必相同，因此 `33.18M` 与 `88.03M` 也不能直接决定 GPU 时间。

更完整的性能模型至少包括：

```text
输出像素数
x 每像素逻辑采样数
x 采样过滤/格式代价
+ RT 写入
+ back-buffer copy / mip 准备
+ RT 切换、barrier 与同步
+ cache 命中和平台带宽行为
```

#### 为什么当前视觉对比不能代表算法排名

当前两个分支没有控制以下变量：

1. Fast 在三个已经模糊的 LOD 上分别做亮部提取，并使用 `0.90 / 0.56 / 0.34` 三种阈值缩放。
2. Dual 只在第一层 downsample 提取亮部，后续传播同一亮部输入。
3. Fast 的 LOD 权重总和为 `1.0`，Dual 的三次 `base_mix` 会额外累积能量。
4. 两者的扩散半径、有效 PSF、采样形状和最终 composite filter 不同。
5. 当前只比较平均 FPS，不能排除 VSync、帧率上限、CPU bound 或统计分辨率不足。

Arm 原始论文在相同等效 97x97 blur 的静态图上认为各方案输出非常相似，明显问题主要出现在朴素 mipmap 方案的方块伪影和运动稳定性；其性能数据来自特定 Mali-T760 MP8 移动 GPU。Arm 后续案例也显示，当原有 Gaussian 已经先降分辨率时，Dual 的性能差距可能有限，优势表现为同成本下更平滑，而不是无条件大幅更快。

Unity 当前 URP Bloom shader 同时包含普通多级上采样和 Dual down/up 核；普通路径还能选择双三次上采样以换取更平滑、较少闪烁。Unreal 标准 Bloom 则组合多个不同半径、不同分辨率的 Gaussian blur。因此，高质量 Bloom 可以建立在自定义 mip/pyramid 上，Mipmap 与 Dual Kawase 不是天然的低质量/高质量二分。

在亮部提取之后，如果两条链的有效 PSF、半径、能量归一化和合成方式匹配，它们可以得到非常接近的结果。随着 mip/pyramid 路线加入更好的 downsample、显式 upsample 和层级混合，它在结构上也会逐渐接近 mixed-resolution/Dual-style filtering。

#### 当前项目观察

当前 Godot 示例中观察到：

- 现有改造版 Dual 在当前参数下比现有 3-LOD Mipmap 基线呈现更宽、更有层次的光晕。
- 4K 预设下，两者平均 FPS 显示接近。

这些观察可以保留，但目前不能证明：

- Dual Kawase 普遍比所有 mip/pyramid Bloom 画质更好。
- 两者 GPU 成本确实接近。
- 视觉差异主要或仅由 Dual down/up 核造成。

更可信的解释是：当前 Dual 同时拥有显式重建、同级层注入、额外全分辨率 tent filter 和更高的未归一化能量；这些因素共同改变了效果。

#### 后续严格验证方法

1. 先生成同一张 HDR bright-pass mask，让两个 blur 分支读取完全相同的输入。
2. 统一阈值、soft knee、Bloom 强度和输出平均能量。
3. 用单个 HDR 亮点测量并匹配两条链的有效 PSF/扩散半径，再比较静态质量。
4. 增加亚像素移动亮点、旋转高亮边缘和高对比细线，检查方块伪影、闪烁与时序稳定性。
5. 关闭 VSync 与帧率限制，固定场景、分辨率、渲染后端和 GPU 频率条件，预热后采样。
6. 使用 GPU timestamp 或平台 GPU profiler 分别测量 screen copy/mip 准备、down、up、composite，报告 GPU ms、P50/P95 和测试硬件。
7. 只有在以上变量受控后，才能形成可复用的质量与性能排序。

#### 后续优化方向

1. Dual Lite：从 `4 down + 3 up + compose` 降到 `3 down + 2 up + compose`。
2. 合并最后一次 upsample 与 composite，但必须实测其把工作搬到全分辨率后的得失。
3. Hybrid Mip Wide：在 3-LOD 基线上增加少量 offset tap 或自定义 upsample。
4. 将 bright-pass 预提取为共享输入，既能公平比较，也能避免两条分支重复使用不同阈值逻辑。
5. 使用 RenderingDevice/compute/atlas 组织更紧凑的 mip chain，但应按目标 GPU 单独验证 barrier、占用率和带宽。

### 关键代码

以下均是示例项目内的相对资源，不代表 Godot 内置实现：

- `shaders/lightweight_bloom.gdshader`：项目 3-LOD Mipmap 与 Wide Glare shader。
- `shaders/dual_kawase_downsample.gdshader`：改造版 Dual 的降采样与第一层亮部提取。
- `shaders/dual_kawase_upsample.gdshader`：Arm 8-tap 核加项目 `base_mix`。
- `shaders/dual_kawase_composite.gdshader`：额外全分辨率 5-tap 合成。
- `scripts/bloom_controls.gd`：模式切换、共享参数、4K 尺寸预设与 FPS 粗测。

### 参考链接

- [Godot Docs - Screen-reading shaders](https://docs.godotengine.org/en/stable/tutorials/shaders/screen-reading_shaders.html) - 2D back-buffer copy 与自动模糊 mip 行为。
- [Godot Docs - VisualShaderNodeTextureParameter](https://docs.godotengine.org/en/stable/classes/class_visualshadernodetextureparameter.html) - linear/mipmap filter 的 texel 与 mip 层级插值语义。
- [Godot Docs - SubViewport](https://docs.godotengine.org/en/stable/classes/class_subviewport.html) - 示例项目 RT 链使用的视口类型。
- [Arm SIGGRAPH 2015 - Bandwidth-Efficient Graphics](https://developer.arm.com/cfs-file/__key/communityserver-blogs-components-weblogfiles/00-00-00-20-66/siggraph2015_2D00_mmg_2D00_marius_2D00_notes.pdf) - Dual Filtering 原始核、质量/稳定性与特定 Mali 性能对比。
- [Arm - Post-processing effects on mobile](https://developer.arm.com/community/arm-community-blogs/b/mobile-graphics-and-gaming-blog/posts/post-processing-effects-on-mobile-optimization-and-alternatives) - 已降分辨率 Gaussian 与 Dual 的实际案例边界。
- [Arm SIGGRAPH 2024 - HypeHype Render Pipeline](https://developer.arm.com/cfs-file/__key/communityserver-blogs-components-weblogfiles/00-00-00-20-66/siggraph_5F00_mmg_5F00_2024_5F00_HypeHype.pdf) - 现代移动端 Bloom down/up mip chain 与 render-pass 带宽语境。
- [Unity Graphics - URP Bloom.shader](https://github.com/Unity-Technologies/Graphics/blob/master/Packages/com.unity.render-pipelines.universal/Shaders/PostProcessing/Bloom.shader) - 普通 pyramid upsample、Dual down/up 核和过滤实现。
- [Unity URP - highQualityFiltering](https://docs.unity3d.com/kr/Packages/com.unity.render-pipelines.universal%4015.0/api/UnityEngine.Rendering.Universal.Bloom.highQualityFiltering.html) - 双三次与双线性上采样的质量/成本取舍。
- [Unreal Engine - Bloom](https://dev.epicgames.com/documentation/en-us/unreal-engine/bloom-in-unreal-engine) - 多分辨率、多半径 Gaussian Bloom 及卷积 Bloom。
- [Microsoft - D3D10 texture filter semantics](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/d3d10umddi/ne-d3d10umddi-d3d10_ddi_filter) - 双线性和 mip 间线性过滤的采样语义。

### 相关记录

- [高品质后处理：十种图像模糊算法的总结与实现](./zhihu-postprocessing-blur-algorithms.md) - 学习用途本地留档，状态为待验证，仅作为算法背景。
- [URP 内置 Bloom 与自定义 Dual Kawase 性能对比](./urp-builtin-bloom-vs-dual-kawase-renderfeature-performance.md) - 不同平台与实现约束下的性能案例。
- [URP RenderFeature 自定义 Dual Kawase Bloom 案例](./urp-renderfeature-postprocess-case-dual-kawase-bloom.md) - Unity/Quest 场景中的工程实现。
- [色带断层与 Dither 缓解](./color-banding-dither.md) - Bloom 平滑光晕与输出量化台阶的关联。

### 验证记录

- [2026-06-02] 初次记录。来源为 AI 在 Godot 4 Bloom 对比项目中的实现、代码阅读和 4K 预设观察；用户确认实践主体应表述为 AI 实践而非用户亲自操作。已与 Godot screen texture、SubViewport 和 Arm SIGGRAPH 2015 资料交叉核对；性能结论仅为 FPS 粗测。
- [2026-07-13] 修正 4K Dual 总 shaded pixels：从误写的 `12.77M` 更正为约 `13.77M`，并补充屏幕复制、mip 准备、各级 RT 读写关系和成本模型。
- [2026-07-13] 经 Godot、Arm、Unity、Unreal、Microsoft 官方资料再次交叉审计：将“Fast Mipmap”限定为项目 3-LOD 基线，将当前 Dual 标记为带 `base_mix` 与额外 composite 的改造版；撤回“没有多尺度扩散”“Dual 天然明显更好”和“性能接近原因已确定”等过度结论；把 `33M texture reads` 改为逻辑采样指令，并补充 Dual 约 `88.03M` 可见逻辑采样估算。由于仍缺少同输入、同能量和 GPU timestamp 的受控测试，状态调整为待验证。

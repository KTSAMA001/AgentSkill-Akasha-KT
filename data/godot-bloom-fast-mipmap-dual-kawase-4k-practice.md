# Godot 4 中 Fast Mipmap Bloom 与 Dual Kawase 升降采样实践

**标签**：#godot #graphics #shader #experience #post-processing #performance
**来源**：AI 在 Godot 4 Bloom 算法对比项目中的实现与观察；Godot 官方文档与 ARM SIGGRAPH 2015 资料交叉验证
**收录日期**：2026-06-02
**来源日期**：2026-06-02
**更新日期**：2026-06-02
**状态**：✅ 已验证
**可信度**：⭐⭐⭐（AI 实践验证 + 官方文档佐证；4K 性能结论来自项目内 FPS 粗测与视觉观察，未做 GPU timestamp profile）
**适用版本**：Godot 4.6.1 stable mono；Forward Plus；HDR 2D；Bloom 对比项目内 3840x2160 渲染预设

### 概要

在 Godot 4 的燃烧特效 Bloom 对比实践中，Fast Mipmap 方案通过 `hint_screen_texture + filter_linear_mipmap` 在单个全屏 Pass 中读取屏幕 mip 链，成本低但光晕形状和炫光感有限。Dual Kawase 方案使用显式降采样、升采样与最终合成链路，在 4K 对比中观察到性能读数与 Fast Mipmap 接近但视觉效果明显更好；该现象的关键原因是 Dual Kawase 的多数采样发生在低分辨率 RT 上，而 Fast Mipmap 仍需要屏幕纹理拷贝、mip 生成和全屏采样。

### 内容

#### 实践背景

本记录来自 AI 在 Godot 4 示例项目中实现 Bloom 算法对比的实践，不是用户亲自操作测试。项目目标是比较多种 Bloom 路线的效果与性能，包括 Fast Mipmap、Dual Kawase、Wide Glare、自定义与 Godot 内置 Glow。

当前可复用的实践边界：

- 渲染后处理目标通过独立 `RenderViewport` 控制，预设包含 `1280x720`、`1920x1080`、`2560x1440`、`3200x1800`、`3840x2160`。
- `RenderViewport` 是实际渲染尺寸，窗口只是显示缩放，因此可以在小窗口中观察 4K Bloom 成本。
- 性能显示使用 Godot `Engine.get_frames_per_second()` 取平均 FPS，适合快速横向比较，但不是精确 GPU 时间。
- 4K 观察结论应记录为“AI 实践中的 FPS 粗测与视觉观察”，不能等价为严格 GPU profile。

#### Fast Mipmap Bloom 算法

Fast Mipmap 路线的核心是读取 Godot screen texture 的 mip 链：

```glsl
uniform sampler2D screen_texture : hint_screen_texture, repeat_disable, filter_linear_mipmap;
```

Godot 官方文档说明，屏幕纹理读取会使用 back-buffer copy；当 sampler 使用 mipmap filter 时，Godot 会自动计算模糊 mipmap。因此 Fast Mipmap 不是零成本路径，它把一部分模糊成本交给屏幕纹理拷贝和 mip 生成路径。

当前实现的亮部提取函数：

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

当前 Fast Mipmap 模式每个全屏像素读取 base color，再读取 3 个 mip LOD：

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

Fast Mipmap 的性质：

- 优点：Pass 数最低，实现简单，适合作为自定义 Bloom 的廉价基线。
- 局限：只是在当前像素附近读取几个预模糊 LOD，没有显式的多尺度扩散和升采样重建。
- 视觉表现：容易得到“亮部发虚”的近似 Bloom，但宽光晕、层次过渡和镜头炫光感不足。
- 参数含义：`spread` 在这里主要映射到 LOD 选择，而不是严格的卷积半径。

#### Dual Kawase 升降采样算法

Dual Kawase 路线的核心是将亮部能量写入多级低分辨率 RT，再从低分辨率向高分辨率升采样重建。

当前实现的管线：

1. 源场景只渲染一次到 `RenderViewport`。
2. Down chain：`1/2 -> 1/4 -> 1/8 -> 1/16`。
3. Up chain：`1/8 -> 1/4 -> 1/2`。
4. Final compose：全分辨率读取原图与半分辨率 Bloom 纹理，完成最终合成。

关键设计点是：Dual 分支只 blit 当前纹理，不会每一级重复渲染火焰场景。

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

Downsample 的算法含义：

- 第一层 `extract_source = true`，对源场景做亮部提取。
- 后续层只传播和扩大已经隔离出来的 Bloom 能量。
- 权重为 `center * 4 + 4 diagonal taps`，归一化因子为 `0.125`。
- 与简单 mipmap 不同，这里可以显式控制 bright extraction、offset 和各级 RT。

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

Upsample 的算法含义：

- 使用 8 tap 从更低一级 Bloom 纹理重建更宽的 lobe。
- 权重序列为 `1, 2, 1, 2, 1, 2, 1, 2`，总权重 12，归一化约 `1/12 = 0.0833333`。
- `base_mix = 0.55` 用来混合同分辨率 downsample 结果，避免只靠最小 mip 拉伸造成能量断层。
- 这一步是 Dual Kawase 相比 Fast Mipmap 更好看的核心：它不是直接读某个 LOD，而是在逐级升采样时重建 Bloom 形状。

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

Composite 的算法含义：

- 全分辨率读取源图。
- 对半分辨率 Bloom 纹理再做一次 5 tap tent filter。
- 使用 `center * 4 + left/right/up/down`，归一化因子仍为 `0.125`。
- 最后执行加法式 Bloom 合成。

#### 4K 下的近似成本解释

以 `3840x2160` 为例，源分辨率约 `8.29M` 像素。

Fast Mipmap 近似成本：

- 主 pass 覆盖全分辨率 `8.29M` 像素。
- 每像素读取 `base + 3 mip samples`，约 4 次纹理读取。
- 粗略纹理读取量约 `33M` 级别。
- 额外存在 Godot screen texture copy 与 mipmap 生成成本。

Dual Kawase 近似成本：

- Down output pixels：`1920x1080 + 960x540 + 480x270 + 240x135`，约 `2.75M` 像素。
- Up output pixels：`480x270 + 960x540 + 1920x1080`，约 `2.72M` 像素。
- Final compose：`3840x2160`，约 `8.29M` 像素。
- 总 shaded pixels 约 `12.77M`，pass 数更多，但大部分发生在低分辨率。
- 如果按当前 shader tap 粗估，最终 full-res composite 是主要成本之一。

因此，“Pass 更多”不等于一定明显更慢。Dual Kawase 的多数模糊扩散工作发生在低分辨率 RT；Fast Mipmap 虽然 pass 少，但仍是全分辨率 pass，并且依赖屏幕纹理拷贝与 mip 生成。

#### 本次实践观察

AI 在当前 Godot Bloom 对比项目中观察到：

- Fast Mipmap 实现简单、成本低，但画面缺少真正的宽 Bloom 层次，炫光感弱。
- Dual Kawase 在 4K 预设下，FPS 粗测看起来与 Fast Mipmap 接近，但视觉效果明显更好。
- 该现象并不反常，因为 Dual Kawase 的低分辨率 down/up 链路能用较少高分辨率成本获得更稳定的宽光晕。
- 当前项目的 FPS 读数只适合做快速趋势判断；如需严格结论，应使用 GPU timestamp、RenderDoc、系统 GPU profiler 或更长时间、更高压力的 benchmark。

#### 减少 Pass 的后续优化方向

可继续尝试的优化路线：

1. Dual Kawase Lite：从 `4 down + 3 up + compose` 降到 `3 down + 2 up + compose`，减少两个低分辨率 RT pass。
2. 合并最终上采样与 composite：减少一个 pass，但可能把半分辨率工作搬到全分辨率，未必更快。
3. Hybrid Mip Wide：保留单 pass mipmap 路线，但增加少量 offset tap，作为 Fast Mipmap 与 Dual Kawase 之间的折中。
4. Compute/atlas mip chain：用 RenderingDevice 或 compute shader 组织更紧凑的 mip/atlas 管线，复杂度更高，适合后续专项验证。

### 关键代码

完整代码应以项目中的相对资源为准：

- `shaders/lightweight_bloom.gdshader`：Fast Mipmap 与 Wide Glare 单 pass shader。
- `shaders/dual_kawase_downsample.gdshader`：Dual Kawase 降采样与第一层亮部提取。
- `shaders/dual_kawase_upsample.gdshader`：Dual Kawase 升采样重建。
- `shaders/dual_kawase_composite.gdshader`：最终全分辨率合成。
- `scripts/bloom_controls.gd`：模式切换、共享参数同步、4K 渲染尺寸预设、FPS 粗测。

### 参考链接

- [Godot Docs - Screen-reading shaders](https://docs.godotengine.org/en/stable/tutorials/shaders/screen-reading_shaders.html) - Godot screen texture 与 mipmap filter 行为。
- [Godot Docs - SubViewport](https://docs.godotengine.org/en/stable/classes/class_subviewport.html) - 当前项目用于组织 Bloom RT 链。
- [ARM SIGGRAPH 2015 - Bandwidth-Efficient Rendering](https://community.arm.com/cfs-file/__key/communityserver-blogs-components-weblogfiles/00-00-00-20-66/siggraph2015_2D00_mmg_2D00_marius_2D00_notes.pdf) - mixed-resolution filtering 与 Dual filtering 背景资料。

### 相关记录

- [高品质后处理：十种图像模糊算法的总结与实现](./zhihu-postprocessing-blur-algorithms.md) - 浅墨/毛星云文章的本地留档，包含 Dual Blur / Kawase Blur 背景；该记录状态为待验证，因此本文只把它作为算法背景参考。
- [色带断层与 Dither 缓解](./color-banding-dither.md) - Bloom 平滑光晕容易暴露输出量化台阶，可与本次 Bloom 实践关联。

### 验证记录

- [2026-06-02] 初次记录。来源为 AI 在 Godot 4 Bloom 对比项目中的实现、代码阅读和 4K 预设观察；用户确认实践主体应表述为 AI 实践而非用户亲自操作。已与 Godot 官方 screen texture 文档、SubViewport 文档和 ARM SIGGRAPH 2015 mixed-resolution / Dual filtering 资料交叉验证。性能结论限定为 FPS 粗测与视觉观察，未做 GPU timestamp profile。

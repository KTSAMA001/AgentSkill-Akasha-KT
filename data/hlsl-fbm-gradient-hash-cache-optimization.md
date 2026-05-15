# HLSL FBM 解析梯度优化与白边修复

**标签**：#shader #hlsl #performance #experience
**来源**：实践总结 - Unity HLSL 3D Value Noise FBM 优化
**收录日期**：2026-05-15
**来源日期**：2026-05-15
**更新日期**：2026-05-15
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐（本地数值抽样 + 渲染现象回归确认）
**适用版本**：HLSL / Unity Shader，3D value-noise FBM 梯度实现

### 概要

对基于 3D Value Noise 的 `rockFBMGradient`，最终更稳的优化不是减少 octave，也不是只做前向差分 hash 复用，而是把梯度改为同一套 Value Noise 的解析梯度。这样每个 octave 只需要 8 个 corner hash，能把 4 octave 梯度从约 128 次 hash 降到约 32 次，同时避开前向差分在 cell 边界和 Vulkan 精度差异下产生的白边/切割伪影。

### 内容

#### 问题场景

原始梯度实现通常写成：

```hlsl
float val = rockFBM(p, octaves, freq, lacunarity, gain, amplitude);
float dx = rockFBM(p + float3(e, 0.0, 0.0), octaves, freq, lacunarity, gain, amplitude) - val;
float dy = rockFBM(p + float3(0.0, e, 0.0), octaves, freq, lacunarity, gain, amplitude) - val;
float dz = rockFBM(p + float3(0.0, 0.0, e), octaves, freq, lacunarity, gain, amplitude) - val;
return float3(dx, dy, dz) / e;
```

当 `octaves = 4` 时，这相当于每个像素执行 base/x/y/z 四条 FBM 曲线，也就是 16 次 `rockNoise3D`。如果每次 3D Value Noise 需要 8 个 corner hash，总计约 128 次 hash。角色、UI、矿石等像素阶段调用会直接放大成本。

旧前向差分还有一个视觉风险：`p + e` 可能跨过 Value Noise 的 cell 边界，不同图形 API 或不同精度路径下，这类边界差异容易被法线扰动和光照放大成白边、硬切割或局部亮线。

#### 方案演进

第一阶段可以做 hash 生命周期优化：保留前向差分语义，在每个 octave 内缓存 base cell 的 8 个 corner hash，x/y/z 偏移点仍在同 cell 时复用这些 corner，只重复插值；跨 cell 时回退完整采样。这能保持旧算法近似等价，并显著降低 hash 次数。

但如果目标还包括消除 Vulkan 等平台上的边界白线，更推荐最终改成解析梯度：直接对 Value Noise 的 smoothstep 插值求导。这样不会再有 `p + e` 的跨 cell 分支，`e` 参数也不再参与数学结果。

#### 当前结论

- 噪声类型仍是 3D Value Noise + FBM，没有换成 Perlin、Simplex 或 Gradient Noise。
- 梯度从“前向差分近似”变成“Value Noise 解析梯度”，结果不是逐像素严格等价，但整体非常接近。
- 4 octave 下 hash 量从约 `128` 降到约 `32`，并且实现中可以没有 cell 复用判断的 `if`。
- 差异主要集中在旧前向差分容易跨 cell 的边界区域；这些区域正是白边/切割伪影容易出现的位置。
- 如有 ASE 或其他生成代码仍按旧签名调用，可保留带 `e` 的兼容接口，但必须在 HLSL 注释中明确 `e` 仅为旧前向差分接口兼容，解析梯度不依赖它。

#### half 版本注意点

如果同时维护 `half` 版，不要让 float/half 两套算法分叉。历史上若保留前向差分 hash 复用版，`half` 不能简单写成“每层先算 delta，再累加 delta”，因为旧实现的舍入生命周期是：

1. 分别累加 base/x/y/z 四条 FBM 曲线。
2. 最后再执行 `x - base`、`y - base`、`z - base`。

如果 half 新实现改成每个 octave 内先 `(x - base)` 再累加，半精度舍入顺序会变，可能出现可观偏差。若后续只保留 float 解析梯度版，应删除或停用 3D FBM 的 half 接口，避免两套实现长期不同步。

#### 数值对比

以 `octaves=4, e=0.001, freq=1.0, lacunarity=2.0, gain=0.5, amplitude=0.5` 做抽样对比：

| 指标 | 结果 |
|---|---:|
| 旧前向差分梯度长度均值 | `0.528498` |
| 新解析梯度长度均值 | `0.528486` |
| 梯度向量差异均值 | `0.00364` |
| 相对差异中位数 | 约 `0.65%` |
| 相对差异 P95 | 约 `2.3%` |
| 相对差异 P99 | 约 `4.4%` |
| 方向一致性均值 | cosine `0.99993` |

落到最终法线扰动上，差异更小。以常见写法 `normalize(normalWS + grad * (0.016 * noiseScale))` 估算，`noiseScale=10` 时平均法线夹角约 `0.026°`，P95 约 `0.061°`，P99 约 `0.084°`。

### 关键代码

```hlsl
float rockNoise3DInterpolate(
    float n000, float n100, float n010, float n110,
    float n001, float n101, float n011, float n111,
    float3 f)
{
    float nx00 = lerp(n000, n100, f.x);
    float nx10 = lerp(n010, n110, f.x);
    float nx01 = lerp(n001, n101, f.x);
    float nx11 = lerp(n011, n111, f.x);

    return lerp(lerp(nx00, nx10, f.y), lerp(nx01, nx11, f.y), f.z);
}

float3 rockNoise3DGradient(float3 p)
{
    float3 i = floor(p);
    float3 rawF = frac(p);
    float3 f = rawF * rawF * (3.0 - 2.0 * rawF);
    float3 df = 6.0 * rawF * (1.0 - rawF);

    float n000 = rockHash3(i + float3(0, 0, 0));
    float n100 = rockHash3(i + float3(1, 0, 0));
    float n010 = rockHash3(i + float3(0, 1, 0));
    float n110 = rockHash3(i + float3(1, 1, 0));
    float n001 = rockHash3(i + float3(0, 0, 1));
    float n101 = rockHash3(i + float3(1, 0, 1));
    float n011 = rockHash3(i + float3(0, 1, 1));
    float n111 = rockHash3(i + float3(1, 1, 1));

    float nx00 = lerp(n000, n100, f.x);
    float nx10 = lerp(n010, n110, f.x);
    float nx01 = lerp(n001, n101, f.x);
    float nx11 = lerp(n011, n111, f.x);

    float gradX = lerp(lerp(n100 - n000, n110 - n010, f.y),
                       lerp(n101 - n001, n111 - n011, f.y), f.z) * df.x;
    float gradY = lerp(lerp(n010 - n000, n110 - n100, f.x),
                       lerp(n011 - n001, n111 - n101, f.x), f.z) * df.y;
    float gradZ = (lerp(nx01, nx11, f.y) - lerp(nx00, nx10, f.y)) * df.z;

    return float3(gradX, gradY, gradZ);
}

float3 rockFBMGradient(float3 p, int octaves, float e, float freq, float lacunarity, float gain, float amplitude)
{
    // e 是旧前向差分接口的兼容参数；解析梯度不依赖步长。
    float3 gradient = float3(0.0, 0.0, 0.0);

    [loop]
    for (int i = 0; i < octaves; i++)
    {
        gradient += amplitude * freq * rockNoise3DGradient(p * freq);
        freq *= lacunarity;
        amplitude *= gain;
    }

    return gradient;
}
```

### 参考链接

- 暂无外部链接；本记录来自项目实践与本地数值模拟。

### 相关记录

- [Git for Windows 不继承系统代理导致 push/clone 卡死](./git-windows-system-proxy-not-inherited.md) - 阿卡西记录更新时若 Git 直连 GitHub 失败，可用单次代理方式完成同步和推送。

### 验证记录

- [2026-05-15] 初次记录：前向差分 hash 复用方案可在保持旧语义近似等价的前提下降低 hash 调用量，但不能从根因上消除跨 cell 差分带来的白边风险。
- [2026-05-15] 更新验证：解析梯度版在保留 3D Value Noise 类型的前提下，将 4 octave 梯度 hash 量从约 128 降到约 32；本地数值抽样显示梯度相对差异中位数约 0.65%、P95 约 2.3%，最终法线差异在常见强度下约为 0.026° 平均值；渲染观察确认旧白边/切割伪影已消失。
- [2026-05-15] 脱敏检查：记录正文改用泛化项目描述，移除了本机路径、具体项目名和仓库结构细节。

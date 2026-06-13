# ACES Tone Mapping

**标签**：#graphics #knowledge #pbr #hdr #post-processing #color-space
**来源**：Unity_URP_Learning 仓库 / ACES 标准
**来源日期**：2024-08-08
**收录日期**：2026-02-07
**更新日期**：2026-06-13
**状态**：📘 有效
**可信度**：⭐⭐⭐⭐⭐ (工业标准)

### 概要

ACES Tone Mapping 是将 HDR 渲染结果压缩到 LDR 显示范围的色调映射曲线，常用于在保留暗部细节的同时压缩高光。

### 内容

ACES (Academy Color Encoding System) Tone Mapping 是一种将 HDR 渲染结果映射到 LDR 显示范围的色调映射函数。

关键点：

- 拟合曲线近似电影工业中的 ACES RRT+ODT 变换。
- 自带 `saturate` 保证输出在 `[0,1]` 范围。
- 保留暗部细节同时压缩高光区域。
- 已被广泛用于游戏和影视行业。

### 关键代码

```hlsl
float3 ACESToneMapping(float3 x)
{
    float a = 2.51;
    float b = 0.03;
    float c = 2.43;
    float d = 0.59;
    float e = 0.14;
    return saturate((x * (a * x + b)) / (x * (c * x + d) + e));
}
```

### 相关记录

- [色带与抖动](./color-banding-dither.md) - Tone Mapping 后仍可能涉及色带与抖动处理。
- [色彩空间](./color-space-gamma-linear.md) - HDR/LDR 与 Gamma/Linear 转换相关基础。

### 验证记录

- [2026-04-15] 结构修复：补齐模板必填章节，未改动原结论。
- [2026-06-13] 结构维护：从旧聚合记录拆分，未重新验证原技术结论。

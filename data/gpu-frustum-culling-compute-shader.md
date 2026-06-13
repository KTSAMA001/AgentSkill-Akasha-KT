# GPU 视锥剔除 ComputeShader 实现

**标签**：#graphics #shader #knowledge #compute-shader #gpgpu #culling #performance
**来源**：Unity_URP_Learning 仓库实践
**来源日期**：2024-08-08
**收录日期**：2026-02-07
**更新日期**：2026-06-13
**状态**：📘 有效
**可信度**：⭐⭐⭐ (个人实践验证)

### 概要

GPU 视锥剔除在 ComputeShader 中将物体 AABB 顶点变换到裁剪空间，在线程内判断是否完全在视锥外，并把可见结果追加到 GPU Buffer。

### 内容

在 GPU 端执行视锥体剔除时，可将物体的 AABB 包围盒 8 个顶点变换到裁剪空间，判断是否完全在视锥体外部，从而在渲染前剔除不可见物体。

#### AABB 顶点变换

```hlsl
float4 boundVerts[8];
float4x4 mvp = mul(_VPMatrix, mul(_PivotTRS, objectTRS));

// 计算 AABB 8 个顶点的裁剪空间坐标
boundVerts[0] = mul(mvp, float4(boundMin, 1));
boundVerts[1] = mul(mvp, float4(boundMax, 1));
// ... 其余 6 个顶点
```

#### 剔除判断

在齐次裁剪空间中，可见物体的条件为：`-w <= x,y,z <= w`。

```hlsl
for (int i = 0; i < 6; i++)
{
    for (int j = 0; j < 8; j++)
    {
        float4 pos = abs(boundVerts[j]);
        // 只要有一个顶点在视锥体内就保留
        if (pos.z <= pos.w && pos.y <= pos.w * 1.5 && pos.x <= pos.w * 1.1)
            break;
        if (j == 7) return;  // 8个顶点都在外面，剔除
    }
}
```

#### 距离裁剪与噪声扰动

为避免远处草突然消失（硬边界），可用噪声函数添加随机偏移：

```hlsl
float noise = 1 - saturate(snoise(boundPosition.xyz * 0.2));
float smoothstepResult = smoothstep(0, 1, noise) * _MaxDrawDistance / 2;
float mask = boundPosition.w + smoothstepResult;
if (mask <= _MaxDrawDistance)  // 带噪声的软边界距离剔除
```

关键点：

- MVP 矩阵需注意乘法顺序：`VP * PivotTRS * ObjectTRS`。
- y 和 x 方向可适当放宽裁剪范围（如 `* 1.5`、`* 1.1`）防止边缘闪烁。
- Simplex Noise (`snoise`) 可使远处草的剔除边界自然过渡。
- 线程组大小 `[numthreads(640,1,1)]` 需根据硬件调优。

### 相关记录

- [ComputeShader GPGPU 基础概念](./compute-shader-gpgpu-basics.md) - 线程组、Buffer 和调度基础。
- [GPU ComputeShader 草渲染与视锥剔除](./gpu-grass-large-scale-rendering.md#gpu-grass-compute-shader) - 完整的草渲染实践上下文。

### 验证记录

- [2026-04-15] 结构修复：补齐模板必填章节，未改动原结论。
- [2026-06-13] 结构维护：从旧聚合记录拆分，未重新验证原技术结论。

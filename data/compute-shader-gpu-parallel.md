# ComputeShader 与 GPU 并行计算

> GPU 通用计算 (GPGPU) 相关原理与概念

---

## ComputeShader 基础概念 {#compute-shader-basics}

**分类**：图形学 > GPU 计算
**标签**：#graphics #shader #knowledge #compute-shader #gpgpu
**来源**：Unity_URP_Learning 仓库实践 + Unity 官方文档
**来源日期**：2024-08-08
**收录日期**：2026-02-07
**可信度**：⭐⭐⭐⭐ (官方文档 + 实践验证)
**状态**：📘 有效

### 定义/概念

ComputeShader 是运行在 GPU 上的通用计算程序，不属于图形渲染管线，而是利用 GPU 的并行架构执行大规模数据处理任务。

### 原理/详解

#### 线程模型

ComputeShader 使用**三级线程层次**：

```
Dispatch(groupX, groupY, groupZ)           ← CPU 发起调度
  └─ ThreadGroup [numthreads(x, y, z)]     ← 线程组（在一个 SM 上执行）
       └─ Thread (SV_DispatchThreadID)      ← 单个线程
```

```hlsl
// 声明每个线程组包含 640 个线程
[numthreads(640, 1, 1)]
void MyKernel(uint3 id : SV_DispatchThreadID)
{
    // id.x = groupID.x * 640 + threadID.x
    if (id.x >= instanceCount) return;
    // ... 计算逻辑
}
```

#### C# 端调度

```csharp
// 获取线程组大小
cs.GetKernelThreadGroupSizes(0, out uint threadGroupSizeX, out _, out _);

// 计算需要多少线程组
int threadGroupsX = Mathf.CeilToInt((float)totalCount / threadGroupSizeX);

// 发起调度
cs.Dispatch(0, threadGroupsX, 1, 1);
```

#### 数据传递 - StructuredBuffer

CPU 与 GPU 之间通过 `ComputeBuffer` 交换数据：

```csharp
// CPU 端
struct GrassInfo { public Matrix4x4 TRS; }
ComputeBuffer buffer = new ComputeBuffer(count, stride, ComputeBufferType.Default);
buffer.SetData(dataArray);
computeShader.SetBuffer(kernelIndex, "BufferName", buffer);

// GPU 端 (ComputeShader)
StructuredBuffer<GrassInfo> GrassInfos;         // 只读
AppendStructuredBuffer<GrassInfo> CullResult;   // 追加写入
```

#### AppendStructuredBuffer

用于**动态追加结果**的特殊 Buffer 类型（如剔除后的可见列表）：

```hlsl
AppendStructuredBuffer<GrassInfo> CullResult;

[numthreads(640, 1, 1)]
void FrustumCulling(uint3 id : SV_DispatchThreadID)
{
    // ... 剔除判断
    if (isVisible)
    {
        GrassInfo info;
        info.TRS = GrassInfos[id.x].TRS;
        CullResult.Append(info);  // 线程安全的追加
    }
}
```

### 关键点

- `[numthreads(x,y,z)]` 定义线程组大小，总线程数 = x * y * z
- `SV_DispatchThreadID` 为全局线程 ID
- `ComputeBuffer` 的 stride 必须与 GPU 端 struct 大小匹配
- `AppendStructuredBuffer` 适用于输出数量不确定的场景（如剔除结果）
- 使用 `ComputeBuffer.CopyCount` 获取 AppendBuffer 中的实际元素数量
- 记得在不需要时调用 `buffer.Release()` 释放 GPU 内存

### 相关知识

- [PBR 渲染](./pbr-brdf-theory.md) — GPU 草渲染中使用 PBR 光照

### 与经验关联

- 实践验证：[GPU ComputeShader 草渲染与视锥剔除](./experiences/shader/urp.md#gpu-grass-compute-shader) — 完整的 ComputeShader 草渲染实现

---

## GPU 视锥剔除 (Frustum Culling) {#gpu-frustum-culling}

**分类**：图形学 > GPU 计算 > 优化
**标签**：#graphics #shader #knowledge #compute-shader #gpgpu
**来源**：Unity_URP_Learning 仓库实践
**来源日期**：2024-08-08
**收录日期**：2026-02-07
**可信度**：⭐⭐⭐ (个人实践验证)
**状态**：📘 有效

### 定义/概念

在 GPU 端执行视锥体剔除，通过将物体的 AABB 包围盒 8 个顶点变换到裁剪空间，判断是否完全在视锥体外部，从而在渲染前剔除不可见物体。

### 原理/详解

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

在齐次裁剪空间中，可见物体的条件为：`-w ≤ x,y,z ≤ w`

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

### 关键点

- MVP 矩阵需注意乘法顺序：`VP * PivotTRS * ObjectTRS`
- y 和 x 方向可适当放宽裁剪范围（如 `* 1.5`、`* 1.1`）防止边缘闪烁
- Simplex Noise (snoise) 可使远处草的剔除边界自然过渡
- 线程组大小 `[numthreads(640,1,1)]` 需根据硬件调优

### 相关知识

- [ComputeShader 基础概念](#compute-shader-basics)

---

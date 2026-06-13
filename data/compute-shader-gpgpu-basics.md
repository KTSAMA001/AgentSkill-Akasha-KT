# ComputeShader GPGPU 基础概念

**标签**：#graphics #shader #knowledge #compute-shader #gpgpu
**来源**：Unity_URP_Learning 仓库实践 + Unity 官方文档
**来源日期**：2024-08-08
**收录日期**：2026-02-07
**更新日期**：2026-06-13
**状态**：📘 有效
**可信度**：⭐⭐⭐⭐ (官方文档 + 实践验证)

### 概要

ComputeShader 是运行在 GPU 上的通用计算程序，通过线程组、全局线程 ID 和 Buffer 在 CPU/GPU 之间组织大规模并行数据处理。

### 内容

ComputeShader 不属于图形渲染管线，而是利用 GPU 的并行架构执行大规模数据处理任务。

#### 线程模型

ComputeShader 使用**三级线程层次**：

```text
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

关键点：

- `[numthreads(x,y,z)]` 定义线程组大小，总线程数 = `x * y * z`。
- `SV_DispatchThreadID` 为全局线程 ID。
- `ComputeBuffer` 的 stride 必须与 GPU 端 struct 大小匹配。
- `AppendStructuredBuffer` 适用于输出数量不确定的场景（如剔除结果）。
- 使用 `ComputeBuffer.CopyCount` 获取 AppendBuffer 中的实际元素数量。
- 记得在不需要时调用 `buffer.Release()` 释放 GPU 内存。

### 相关记录

- [GPU 视锥剔除 ComputeShader 实现](./gpu-frustum-culling-compute-shader.md) - 使用 ComputeShader 输出可见实例列表的实践。
- [Cook-Torrance BRDF 模型](./pbr-cook-torrance-brdf-theory.md) - GPU 草渲染中使用的 PBR 光照理论。
- [GPU ComputeShader 草渲染与视锥剔除](./gpu-grass-large-scale-rendering.md#gpu-grass-compute-shader) - 完整的 ComputeShader 草渲染实现。

### 验证记录

- [2026-04-15] 结构修复：补齐模板必填章节，未改动原结论。
- [2026-06-13] 结构维护：从旧聚合记录拆分，未重新验证原技术结论。

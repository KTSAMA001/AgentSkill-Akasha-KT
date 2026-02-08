# 大规模渲染 (Large-Scale Rendering) 相关经验

> 大规模渲染 (Large-Scale Rendering) 相关经验
>
> 包含：GPU Instancing、ComputeShader 渲染、视锥剔除、大规模植被等

---

## GPU ComputeShader 草渲染与视锥剔除 {#gpu-grass-compute-shader}

**收录日期**：2026-02-07
**来源日期**：2024-08-08
**标签**：#shader #unity #experience #compute-shader #urp #performance
**状态**：✅ 已验证
**适用版本**：Unity 2022.3+ / URP 14.0+

**问题/场景**：

需要在 URP 中实现大规模草渲染（数万至数十万株），要求高性能、支持 GPU 视锥剔除、支持 PBR 光照。

**解决方案/结论**：

### 1. 整体架构

```
Terrain Mesh 顶点 → 每顶点生成 N 株草数据 → ComputeBuffer
→ ComputeShader 视锥剔除 → AppendBuffer
→ DrawMeshInstancedProcedural 批量渲染
```

### 2. 草数据生成（CPU 端）

```csharp
struct GrassInfo {
    public Vector3 Pos;
    public Matrix4x4 TRS;
    public int id;
}

// 在地形每个顶点周围随机撒草
for (int i = 0; i < vertexCount; i++)
    for (int j = 0; j < grassCountPerFace; j++)
    {
        Vector3 offset = vertices[i] + new Vector3(Random.Range(0, 1f), 0, Random.Range(0, 1f));
        float rot = Random.Range(0, 180);
        grassInfos[idx] = new GrassInfo {
            TRS = Matrix4x4.TRS(offset, Quaternion.Euler(0, rot, 0), Vector3.one),
            Pos = offset, id = idx
        };
    }
```

### 3. GPU 视锥剔除（ComputeShader 端）

```hlsl
[numthreads(640, 1, 1)]
void FrustumCulling(uint3 id : SV_DispatchThreadID)
{
    if (id.x >= instanceCount) return;

    // AABB 8 顶点变换到裁剪空间
    float4x4 mvp = mul(_VPMatrix, mul(_PivotTRS, GrassInfos[id.x].TRS));
    // ... 8 个顶点计算

    // 判断是否在视锥体外
    for (int i = 0; i < 6; i++)
        for (int j = 0; j < 8; j++)
        {
            // 噪声软边界距离剔除
            float noise = 1 - saturate(snoise(boundPosition.xyz * 0.2));
            float mask = boundPosition.w + smoothstep(0, 1, noise) * _MaxDrawDistance / 2;
            if (inFrustum && mask <= _MaxDrawDistance) break;
            if (j == 7) return;  // 完全在外，剔除
        }

    CullResult.Append(grassInfo);  // 通过剔除，追加到结果
}
```

### 4. 批量渲染

```csharp
Graphics.DrawMeshInstancedProcedural(
    grassMesh, 0, grassMaterial,
    new Bounds(Vector3.zero, new Vector3(100f, 100f, 100f)),
    visibleCount, materialPropertyBlock);
```

### 5. 关键踩坑点

- ComputeBuffer stride 必须精确匹配 GPU 端 struct 大小（Matrix4x4=64, Vector3=12, int=4）
- `AppendStructuredBuffer` 需配合 `ComputeBuffer.CopyCount` 获取实际数量
- 视锥剔除的 y/x 方向需适当放宽（`* 1.5`/`* 1.1`）防止边缘闪烁
- 使用 Simplex Noise 使远处草的剔除边界自然过渡，避免硬切割

**参考链接**：

- [Unity_URP_Learning/ComputeShaderGrass](https://github.com/KTSAMA001/Unity_URP_Learning/tree/main/Assets/Products/ComputeShader/ComputeShaderGrass) - 完整源码

**验证记录**：

- [2026-02-07] 从 Unity_URP_Learning 仓库整合，包含多个迭代版本

**理论基础**：

- [ComputeShader 基础概念](./knowledge/graphics/compute-shader.md#compute-shader-basics)
- [GPU 视锥剔除](./knowledge/graphics/compute-shader.md#gpu-frustum-culling)
- [PBR BRDF 模型](./knowledge/graphics/pbr.md#cook-torrance-brdf)

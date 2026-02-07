# URP 渲染管线经验

> Universal Render Pipeline 相关经验
>
> 包含：URP Shader、渲染特性、自定义 Pass、后处理等

---

## ASE Shader 架构与 Bakery 光照集成最佳实践

**日期**：2026-01-29
**标签**：#ASE #ShaderGraph #Bakery #SH光照 #模块化 #变体优化  
**状态**：✅ 已验证

**问题/场景**：

在使用 Amplify Shader Editor (ASE) 开发角色、道具、场景 Shader 时，如何合理组织 Shader 架构，特别是与 Bakery 烘焙光照（SH 球谐）集成时的最佳实践。

**解决方案/结论**：

### 1. ASE 节点架构原则

**核心原则**：ASE Shader 图不应直接引用具体 hlsl 文件，功能细节应封装到各自的节点组中。

- ✅ 将复杂功能（如 SH 光照、RimLight、LatLong 特效）拆分为独立的 ASE 节点组（SubGraph）
- ✅ 每个节点组负责单一功能，对外暴露必要参数
- ✅ 主 Shader 图只负责组合各节点组，而非实现具体逻辑

### 2. SH 光照参数外置

**原因**：让节点可以灵活控制光照来源，提高通用性。

`hlsl
// ❌ 之前：在 shader 内联获取 L0
float3 BakerySH(float3 normalWorld, float2 lightmapUV) {
    BakerySH_float(float3(unity_SHAr.w, unity_SHAg.w, unity_SHAb.w), normalWorld, lightmapUV, sh); 
    return sh;
}

// ✅ 之后：L0 从外部节点传入，更灵活
float3 UnitySHAr() {
    return float3(unity_SHAr.w, unity_SHAg.w, unity_SHAb.w);
}
// 在节点组中调用：BakerySH_float(L0, normalWorld, lightmapUV, sh)
`

### 3. Include 路径使用相对路径

`hlsl
// ❌ 绝对路径：项目迁移后会失效
#include "Assets/CommonFunctionModule/.../BakeryDecodeLightmap.hlsl"

// ✅ 相对路径：更具可移植性
#include "../../../../CommonFunctionModule/.../BakeryDecodeLightmap.hlsl"
`

### 4. 移除不必要的 multi_compile

减少 Shader 变体数量，显著降低编译时间和内存占用：

`hlsl
// ❌ 不必要时移除这些变体声明
#pragma multi_compile _ _ADDITIONAL_LIGHTS_VERTEX _ADDITIONAL_LIGHTS
#pragma multi_compile_fragment _ _ADDITIONAL_LIGHT_SHADOWS
#pragma multi_compile _ _FORWARD_PLUS
#pragma multi_compile _ _LIGHT_LAYERS
`

**影响**：移除不必要宏可以很大程度减少变体数量，提升编译效率。

### 5. 资源清理

定期清理废弃的材质和 Shader 资源，避免：
- 资源引用混乱
- 项目体积膨胀
- 潜在的引用错误

**参考链接**：

- [Bakery GPU Lightmapper 官方文档](https://geom.io/bakery/wiki/)
- [Amplify Shader Editor 官方文档](https://wiki.amplify.pt/index.php)

**验证记录**：

- [2026-01-29] KTSAMA 提交验证，变体优化后编译时间和内存显著下降

**备注**：

此经验来源于项目实际开发中 KTSAMA 的 Shader 重构工作，适用于使用 ASE + Bakery + URP 的项目。

---

## CBUFFER 与 SRP Batcher 合批机制

**日期**：2026-01-31
**标签**：#URP #SRPBatcher #CBUFFER #DrawCall #性能优化
**状态**：✅ 已验证
**来源**：Technical_Artist_Technotes/TA零散知识

**问题/场景**：

在 URP 中，如何让同 Shader 不同材质的物体被 SRP Batcher 合批？为什么 CBUFFER 能避免合批打断？

**核心概念**：

### 1. CBUFFER（Constant Buffer）是什么

CBUFFER 即常量缓冲区，是一段**预先分配的显存（高速）**，用于存储 Shader 中的常量数据（矩阵、向量、颜色等）。

```hlsl
// 常量缓冲区定义
// UnityPerMaterial = 为每个使用该 Shader 的材质分配一块 CBUFFER
CBUFFER_START(UnityPerMaterial)
    half4 _Color;
    half _Width;
    float4 _MainTex_ST;
CBUFFER_END
```

### 2. 合批打断的本质原因

合批被打断的本质是 **DrawCall 之间的渲染状态（Render State）不同**。

渲染状态包括：Shader、纹理、渲染目标、深度测试设置等。如果多个 DrawCall 的渲染状态不完全相同，就无法合批。

**传统流程**：
```
CPU 收集材质属性 → 打包为渲染状态 → 传给 GPU → GPU 执行渲染
```

不同材质的属性值不同 → 渲染状态不同 → 合批被打断

### 3. CBUFFER 为什么能避免合批打断

将属性放入 CBUFFER 后，这些数据**不再通过渲染状态传入 DrawCall**，而是在 GPU 渲染阶段**直接从 CBUFFER 中读取**。

**使用 CBUFFER 后的流程**：
```
CPU 收集材质属性 → 写入 CBUFFER（显存）
CPU 准备渲染状态（不含 CBUFFER 中的属性）→ 传给 GPU
GPU 执行渲染时从 CBUFFER 读取属性
```

由于属性差异被"抽离"出渲染状态，渲染状态趋于一致，合批成功！

### 4. URP 中的 SRP Batcher 条件

- ✅ 使用同一个 Shader
- ✅ 所有材质属性都在 CBUFFER 中声明
- ❌ 多 Pass Shader 无法被 SRP Batcher 合批
- ❌ Texture 类型无法放入 CBUFFER（需使用图集技术）

**关键代码**：

```hlsl
// ✅ 正确：属性在 CBUFFER 中，支持 SRP Batcher
Properties
{
    _Color ("Color", Color) = (1,1,1,1)
    _MainTex ("Texture", 2D) = "white" {}
}

HLSLINCLUDE
CBUFFER_START(UnityPerMaterial)
    half4 _Color;
    float4 _MainTex_ST;  // 纹理的 ST 可以放入
CBUFFER_END

TEXTURE2D(_MainTex);     // 纹理本身单独声明
SAMPLER(sampler_MainTex);
ENDHLSL
```

### 5. CBUFFER 的局限性

| 局限 | 说明 |
|------|------|
| Texture 不可放入 | 纹理需要 GPU 动态加载，无法缓存到 CBUFFER |
| 更新需重新上传 | 修改 CBUFFER 数据需重新上传整个 CBUFFER |
| 大小有限制 | CBUFFER 容量有限，过多参数会超限 |
| 只在 Shader 用的参数 | 放入 CBUFFER 可能浪费显存带宽 |

### 6. Unity 内置 CBUFFER 名称

| 名称 | 用途 |
|------|------|
| UnityPerMaterial | 每个材质的属性（最常用） |
| UnityPerCamera | 相机相关（视图矩阵、投影矩阵等） |
| UnityPerDraw | 当前绘制命令状态（模型矩阵等） |
| UnityGlobalParams | 全局渲染参数（时间、屏幕尺寸等） |

**验证方法**：

在 Frame Debugger 中查看 "SRP Batcher" 标签，确认物体是否被合批。

**验证记录**：

- [2026-01-31] 从 Technical_Artist_Technotes 整理提取


---

## URP Renderer Feature 开发要点

**日期**：2026-01-31
**标签**：#URP #RendererFeature #ScriptableRenderPass #CommandBuffer
**状态**：✅ 已验证
**来源**：Technical_Artist_Technotes/关于SRP、URP

**问题/场景**：

如何在 URP 中自定义 Renderer Feature？有哪些常见的踩坑点？

**核心概念**：

### 1. 什么是 Renderer Feature

Renderer Feature 是一系列对 **CommandBuffer 操作的集合**。它允许向 URP Renderer 添加额外的渲染通道，自定义渲染顺序、渲染对象、材质等。

**本质**：在渲染任务列表中插入、调整渲染任务

### 2. 为什么需要 Renderer Feature

**URP 的限制**：同一个 Shader 中，输出到某一缓冲区的 Pass 只能有一个。

**传统多 Pass 做法**（如描边）在 URP 中无法直接实现：
```
Pass 1: 渲染扩张后的背面 → 颜色缓冲区
Pass 2: 渲染正面 → 颜色缓冲区  // URP 不支持！
```

**解决方案**：使用 Renderer Feature 在指定渲染阶段添加新的 CommandBuffer

### 3. CommandBuffer 基本流程

```csharp
public override void Execute(ScriptableRenderContext context, ref RenderingData renderingData)
{
    // 1. 申请 CommandBuffer（指定名称，对应 Frame Debugger 中的任务名）
    CommandBuffer cmd = CommandBufferPool.Get("MyFeatureName");
    
    // 2. 设置相机、光照等信息
    Camera camera = renderingData.cameraData.camera;
    
    // 3. 添加绘制命令
    cmd.DrawMesh(mesh, matrix, material);
    // 或 cmd.DrawRenderer(renderer, material);
    
    // 4. 执行 CommandBuffer
    context.ExecuteCommandBuffer(cmd);
    
    // 5. 释放 CommandBuffer
    CommandBufferPool.Release(cmd);
}
```

### 4. 常见踩坑点

#### 4.1 部分物体不被渲染

**原因**：Render Layer Mask 设置问题

```csharp
// 在 FilteringSettings 中设置 LayerMask
FilteringSettings filteringSettings = new FilteringSettings(
    RenderQueueRange.opaque,
    layerMask: 1 << targetLayer  // 只渲染指定 Layer
);
```

#### 4.2 批处理失效

**原因1**：Shader 属性未放入 CBUFFER
```hlsl
// 所有属性都要在 CBUFFER 中声明
CBUFFER_START(UnityPerMaterial)
    half4 _Color;
CBUFFER_END
```

**原因2**：未知问题 → 尝试重新烘焙场景光照

#### 4.3 Frame Debugger 中 Pass 名称不对

**原因**：CommandBuffer 申请时的名称就是 Frame Debugger 中显示的任务名

```csharp
// 这个名称会显示在 Frame Debugger 中
CommandBuffer cmd = CommandBufferPool.Get("SurfaceOutline");
```

### 5. 官方 Renderer Feature 参考

| Feature | 功能 |
|---------|------|
| Render Objects | 在指定时机用指定材质渲染指定 Layer 的物体 |
| Decal | 贴花系统 |
| Screen Space Shadows | 屏幕空间阴影映射（需手动添加，非默认） |
| SSAO | 屏幕空间环境光遮蔽 |

### 6. ScriptableRenderPass 关键方法

```csharp
public class MyRenderPass : ScriptableRenderPass
{
    // 配置渲染目标
    public override void OnCameraSetup(CommandBuffer cmd, ref RenderingData renderingData) { }
    
    // 执行渲染（核心方法）
    public override void Execute(ScriptableRenderContext context, ref RenderingData renderingData) { }
    
    // 清理资源
    public override void OnCameraCleanup(CommandBuffer cmd) { }
}
```

### 7. ScriptableRendererFeature 基本结构

```csharp
public class MyRendererFeature : ScriptableRendererFeature
{
    MyRenderPass m_RenderPass;
    
    public override void Create()
    {
        m_RenderPass = new MyRenderPass();
        m_RenderPass.renderPassEvent = RenderPassEvent.AfterRenderingOpaques;
    }
    
    public override void AddRenderPasses(ScriptableRenderer renderer, ref RenderingData renderingData)
    {
        renderer.EnqueuePass(m_RenderPass);
    }
}
```

**验证记录**：

- [2026-01-31] 从 Technical_Artist_Technotes 整理提取

---

## 自定义 PBR Shader 在 URP 中的实现 {#custom-pbr-urp}

**收录日期**：2026-02-07
**来源日期**：2024-08-08
**标签**：#PBR #BRDF #GGX #URP #HLSL #自定义Shader
**状态**：✅ 已验证
**适用版本**：Unity 2022.3+ / URP 14.0+

**问题/场景**：

在 URP 中需要完全自定义 PBR Shader（非使用内置 Lit Shader），手动实现 Cook-Torrance BRDF 模型，包含直接光照和间接光照（IBL），并生成材质属性矩阵展示。

**解决方案/结论**：

### 1. Shader 架构拆分

将 BRDF 函数独立到 `PBR_Func.hlsl` 文件中，主 Shader 文件 `PBR_URP_Shader.shader` 通过 `#include` 引入：

```hlsl
#include "PBR_Func.hlsl"
```

这样实现了功能复用，草渲染等模块也可以引用相同的 PBR 函数库。

### 2. 金属度/粗糙度统一工作流

```hlsl
float3 F0 = lerp(0.04, albedo, metallic);  // 统一金属/非金属
float3 kd = (1 - F) * (1 - metallic);      // 能量守恒
```

### 3. 间接光照 IBL 实现

```hlsl
// 反射探针采样
float mip = roughness * (1.7 - 0.7 * roughness) * UNITY_SPECCUBE_LOD_STEPS;
float4 cubeMapColor = SAMPLE_TEXTURECUBE_LOD(unity_SpecCube0, samplerunity_SpecCube0, reflectDirWS, mip);
float3 envSpecular = DecodeHDREnvironment(cubeMapColor, unity_SpecCube0_HDR);

// 漫反射使用球谐
float3 diffuse_InDirect = SampleSH(N) * albedo * kd;
```

### 4. 材质矩阵展示工具

通过 C# 脚本 `MaterialMatrixShow.cs` 自动生成金属度×粗糙度×亮度的三维球阵列：

```csharp
for (int i = 0; i < _index; i++)       // 亮度轴
    for (int j = 0; j < _index; j++)   // 粗糙度轴
        for (int k = 0; k < _index; k++) // 金属度轴
        {
            temp.material.SetFloat("_Metallic", (float)(k + 0.2f) / _index);
            temp.material.SetFloat("_Roughness", (float)(j + 0.2f) / _index);
            temp.material.color = Color.white * ((float)(i + 0.2f) / _index);
        }
```

**参考链接**：

- [Unity_URP_Learning/PBR](https://github.com/KTSAMA001/Unity_URP_Learning/tree/main/Assets/Products/PBR) - 完整源码
- [LearnOpenGL PBR Theory](https://learnopengl.com/PBR/Theory) - PBR 理论参考

**验证记录**：

- [2026-02-07] 从 Unity_URP_Learning 仓库整合，项目实际运行验证

**理论基础**：

- [PBR BRDF 模型详解](../../knowledge/graphics/pbr.md#cook-torrance-brdf)
- [IBL 间接光照](../../knowledge/graphics/pbr.md#ibl)

---

## GPU ComputeShader 草渲染与视锥剔除 {#gpu-grass-compute-shader}

**收录日期**：2026-02-07
**来源日期**：2024-08-08
**标签**：#ComputeShader #GPU草渲染 #视锥剔除 #DrawMeshInstancedProcedural #URP
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

- [ComputeShader 基础概念](../../knowledge/graphics/compute-shader.md#compute-shader-basics)
- [GPU 视锥剔除](../../knowledge/graphics/compute-shader.md#gpu-frustum-culling)
- [PBR BRDF 模型](../../knowledge/graphics/pbr.md#cook-torrance-brdf)

---

## 屏幕空间描边 SSOutLine RenderFeature 实现 {#ss-outline-renderfeature}

**收录日期**：2026-02-07
**来源日期**：2024-08-08
**标签**：#RenderFeature #描边 #屏幕空间 #后处理 #VolumeComponent #URP
**状态**：✅ 已验证
**适用版本**：Unity 2022.3+ / URP 14.0+

**问题/场景**：

在 URP 中实现全屏屏幕空间描边效果，需要：
1. 基于深度 Mask 的边缘检测
2. 通过 Volume 后处理系统控制参数（描边宽度、颜色）
3. 支持 Scene View 和 Game View 同时工作

**解决方案/结论**：

### 1. 多 RenderFeature 协作

描边需要三个 RenderFeature 协同工作：
1. **SSDepthMaskPassFeature** — 将目标物体的深度写入独立 RT (`_DepthMaskColor`)
2. **GrabColorRenderPassFeature** — 抓取当前帧颜色缓冲到 `_KTGrabTex`
3. **SSOutLinePassFeature** — 读取深度 Mask 和颜色，执行边缘检测并输出

### 2. 自定义 Volume 组件

通过继承 `VolumeComponent` + `IPostProcessComponent` 实现后处理面板控制：

```csharp
[VolumeComponentMenu("KTSAMA_PostProcessing/ScreenSpaceOutLine")]
public class SSOutLineVolume : VolumeComponent, IPostProcessComponent
{
    public BoolParameter isEnabled = new BoolParameter(false);
    public FloatParameter _edgeWidth = new FloatParameter(4, true);
    public ColorParameter _edgeColor = new ColorParameter(Color.white, true);

    public bool IsActive() => isEnabled.value;
    public bool IsTileCompatible() => false;
}
```

### 3. 边缘检测算法（Shader 端）

8 方向深度采样对比，提取边缘：

```hlsl
// 8方向偏移采样深度 Mask
float d1 = SAMPLE_TEXTURE2D(_DepthMaskColor, sampler, uv + _InsiteEdgeWidth * float2( 1,-1) * f).r;
float d2 = SAMPLE_TEXTURE2D(_DepthMaskColor, sampler, uv + _InsiteEdgeWidth * float2(-1, 1) * f).r;
// ... 共 8 个方向 + 原点

float maxDepth = max(d1, max(d2, max(d3, ...)));
float outline = maxDepth - depthOrigin;
float3 result = lerp(screenColor, _EdgeColor, outline);
```

### 4. RenderFeature 中读取 Volume 参数

```csharp
public override void Create()
{
    _volumeStack = VolumeManager.instance.stack;
    ssol = _volumeStack.GetComponent<SSOutLineVolume>();
    setting.ssol = ssol;
}

public override void AddRenderPasses(...)
{
    if (ssol.isEnabled.value)
        renderer.EnqueuePass(m_ScriptablePass);
}
```

### 5. 关键踩坑点

- 使用 `RTHandle` + `RenderingUtils.ReAllocateIfNeeded` 管理临时 RT（而非旧的 `GetTemporaryRT`）
- `Blitter.BlitTexture` 需先 Blit 到临时 RT 再 Blit 回相机颜色，不能直接读写同一 RT
- `renderPassEvent` 时机很重要：描边应在 `AfterRenderingSkybox` 之后执行
- Scene View 兼容需区分处理 `SceneView.currentDrawingSceneView`

**参考链接**：

- [Unity_URP_Learning/RenderFeature](https://github.com/KTSAMA001/Unity_URP_Learning/tree/main/Assets/Products/RenderFeature) - 完整源码
- [可盖大人 Bilibili](https://www.bilibili.com/read/cv29054886/) - RTHandle 用法参考

**验证记录**：

- [2026-02-07] 从 Unity_URP_Learning 仓库整合，实际项目运行验证

**相关经验**：

- [URP Renderer Feature 开发要点](#urp-renderer-feature-开发要点) — 通用 RenderFeature 模式

**理论基础**：

- [Renderer Feature 的要点](../../knowledge/unity/urp.md#renderer-feature-的要点)

---

## 屏幕空间刘海阴影 SSHS RenderFeature {#sshs-renderfeature}

**收录日期**：2026-02-07
**来源日期**：2024-08-08
**标签**：#RenderFeature #刘海阴影 #NPR #屏幕空间 #URP
**状态**：✅ 已验证
**适用版本**：Unity 2022.3+ / URP 14.0+

**问题/场景**：

在 NPR 卡通渲染中，需要实现屏幕空间的刘海在脸上的投影效果（Screen Space Hair Shadow），利用 RenderFeature 将头发的深度信息投射到脸部区域。

**解决方案/结论**：

### 1. 整体思路

利用自定义 RenderFeature 在渲染不透明物体之前：
1. 先将脸部模型的深度写入自定义 RT（`_HairSoildColor`）
2. 再将头发模型的深度/颜色叠加写入同一 RT
3. 后续渲染阶段中，脸部 Shader 采样此 RT 实现阴影效果

### 2. 多 Layer + 多 Pass 分离

```csharp
// 脸部和头发使用不同 Layer
public LayerMask faceLayer;
public LayerMask hairLayer;

// 三次绘制：
// 1. 脸部深度（Pass 0, DepthOnly ShaderTag）
context.DrawRenderers(cullResults, ref draw1, ref faceFiltering);

// 2. 头发深度（Pass 0, UniversalForward ShaderTag）
context.DrawRenderers(cullResults, ref draw2, ref hairFiltering);

// 3. 头发简单颜色（Pass 1）— 用于阴影投射
context.DrawRenderers(cullResults, ref draw3, ref hairFiltering);
```

### 3. 配套 Shader (SSHS.shader)

三个 Pass 分别处理不同功能：
- **FaceDepthOnly**：仅写深度 (`ColorMask 0, ZWrite On`)
- **HairSimpleColor**：输出头发深度到颜色 (`return float4(1, depth, 0, 1)`)
- **DepthMaskColor**：输出纯色遮罩 (`return float4(1, 0, 0, 1)`)

### 4. 关键踩坑点

- 注意 `ConfigureTarget` + `ConfigureClear` 在 `OnCameraSetup` 中设置
- 临时 RT 需在 `OnCameraCleanup` 中释放
- 使用 `ShaderTagId` 匹配 Pass 的 `LightMode` 标签

**参考链接**：

- [Unity_URP_Learning/RenderFeature](https://github.com/KTSAMA001/Unity_URP_Learning/tree/main/Assets/Products/RenderFeature) - 完整源码

**验证记录**：

- [2026-02-07] 从 Unity_URP_Learning 仓库整合

**相关经验**：

- [屏幕空间描边 SSOutLine RenderFeature](#ss-outline-renderfeature) — 类似的 RenderFeature 模式

---

## 遮挡透视效果实现方案 {#occlusion-vision}

**收录日期**：2026-02-07
**来源日期**：2024-08-08
**标签**：#遮挡透视 #RenderFeature #深度测试 #Stencil #URP
**状态**：✅ 已验证
**适用版本**：Unity 2022.3+ / URP 14.0+

**问题/场景**：

在游戏中需要实现被遮挡物体的透视显示效果（如墙后角色轮廓），需要在 URP 中通过自定义 Shader 和 RenderFeature 配合实现。

**解决方案/结论**：

### 1. 核心原理

利用深度测试反转和 Stencil Buffer 实现：
- **CanBeOcclusion Shader**：标记可以被遮挡的物体，写入 Stencil
- **Mask Shader**：遮挡体 Shader，用于生成遮挡区域
- **RenderFeatureUsed Shader**：主物体 Shader，在被遮挡时显示透视颜色

### 2. 配合 SSDepthMaskPassFeature

通过 `SSDepthMaskPassFeature` 将目标物体的深度信息渲染到独立 RT `_DepthMaskColor`：
- 使用 `RTHandle` + `ReAllocateIfNeeded` 分配深度 Mask RT
- 通过全局关键字 `_DEPTH_MASK_COLOR` 控制 Shader 分支
- 在 `OnCameraCleanup` 中关闭关键字，防止影响其他渲染

### 3. 关键踩坑点

- 深度 Mask RT 的 `depthBufferBits` 应设为 0（仅用颜色通道存储信息）
- `RTHandle` 的命名直接对应 Shader 中的全局纹理名
- 注意 `overrideMaterialPassIndex` 选择正确的 Pass

**参考链接**：

- [Unity_URP_Learning/OcclusionVision](https://github.com/KTSAMA001/Unity_URP_Learning/tree/main/Assets/Products/OcclusionVision) - 完整源码（含设计文档 .docx）

**验证记录**：

- [2026-02-07] 从 Unity_URP_Learning 仓库整合，附带设计方案文档

---

## URP 中 GrabPass 替代方案 (GrabColor RenderFeature) {#grab-color-renderfeature}

**收录日期**：2026-02-07
**来源日期**：2024-08-08
**标签**：#GrabPass #RenderFeature #颜色缓冲 #Blit #URP
**状态**：✅ 已验证
**适用版本**：Unity 2022.3+ / URP 14.0+

**问题/场景**：

URP 不支持内置管线的 `GrabPass`，需要在后续 Shader 中读取当前帧的屏幕颜色（如折射、扭曲、描边等效果），需要找到替代方案。

**解决方案/结论**：

### 1. 使用 RenderFeature 抓取颜色缓冲

创建 `GrabColorRenderPassFeature`，在合适时机将相机颜色缓冲 Blit 到全局纹理 `_KTGrabTex`。

### 2. 核心代码

```csharp
public override void OnCameraSetup(CommandBuffer cmd, ref RenderingData renderingData)
{
    RenderTextureDescriptor desc = renderingData.cameraData.cameraTargetDescriptor;
    desc.depthBufferBits = 0;  // 不需要深度
    RenderingUtils.ReAllocateIfNeeded(ref _grabRT, desc);
    cmd.SetGlobalTexture("_KTGrabTex", _grabRT.nameID);
}

public override void Execute(...)
{
    Blitter.BlitCameraTexture(cmd, cameraColorTarget, _grabRT);
}
```

### 3. Scene View 兼容

需要为 Game View 和 Scene View 分别维护独立的 RTHandle，防止互相干扰：

```csharp
#if UNITY_EDITOR
if (SceneView.currentDrawingSceneView)
    Blitter.BlitCameraTexture(cmd, scene_cameraColorTag, _grabRT_SceneView);
else
    Blitter.BlitCameraTexture(cmd, cameraColorTag, _grabRT_GameView);
#else
    Blitter.BlitCameraTexture(cmd, cameraColorTag, _grabRT_GameView);
#endif
```

### 4. 在 Shader 中使用

```hlsl
TEXTURE2D(_KTGrabTex);
SAMPLER(sampler_KTGrabTex);

half4 frag(Varyings i) : SV_Target
{
    float4 screenColor = SAMPLE_TEXTURE2D(_KTGrabTex, sampler_KTGrabTex, i.texcoord);
    // ... 使用屏幕颜色进行后续处理
}
```

### 5. 关键踩坑点

- 抓取的 RT 的 `depthBufferBits` 设为 0，仅需颜色数据
- `SetupRenderPasses` 中获取 `renderer.cameraColorTargetHandle`
- 必须在 `Dispose` 中释放 RTHandle
- `renderPassEvent` 应在 `AfterRenderingSkybox` / `AfterRenderingOpaques`

**参考链接**：

- [Unity_URP_Learning/RenderFeature](https://github.com/KTSAMA001/Unity_URP_Learning/tree/main/Assets/Products/RenderFeature) - 完整源码

**验证记录**：

- [2026-02-07] 从 Unity_URP_Learning 仓库整合

**相关经验**：

- [屏幕空间描边 SSOutLine RenderFeature](#ss-outline-renderfeature) — 依赖此 GrabColor 功能

---

## RenderFeature 运行时开关控制 {#renderfeature-toggler}

**收录日期**：2026-02-07
**来源日期**：2024-08-08
**标签**：#RenderFeature #运行时控制 #ExecuteAlways #URP
**状态**：✅ 已验证
**适用版本**：Unity 2022.3+ / URP 14.0+

**问题/场景**：

在 URP 中需要运行时动态开关 RenderFeature（如调试时禁用某些后处理效果），默认 RenderFeature 只能在 Inspector 中手动勾选。

**解决方案/结论**：

通过 `ScriptableRendererFeature.SetActive()` 方法运行时控制：

```csharp
[System.Serializable]
public struct RenderFeatureToggle
{
    public ScriptableRendererFeature feature;
    public bool isEnabled;
}

[ExecuteAlways]
public class RenderFeatureToggler : MonoBehaviour
{
    [SerializeField] private List<RenderFeatureToggle> renderFeatures;
    [SerializeField] private UniversalRenderPipelineAsset pipelineAsset;

    private void Update()
    {
        foreach (var toggle in renderFeatures)
            toggle.feature.SetActive(toggle.isEnabled);
    }
}
```

**关键代码**：

- `ScriptableRendererFeature.SetActive(bool)` — URP 内置 API
- `[ExecuteAlways]` — 确保在编辑器和运行时都生效

**验证记录**：

- [2026-02-07] 从 Unity_URP_Learning 仓库整合

**相关经验**：

- [URP Renderer Feature 开发要点](#urp-renderer-feature-开发要点) — RenderFeature 基础模式

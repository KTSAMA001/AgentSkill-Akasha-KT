# CBUFFER 与 SRP Batcher 合批机制

**收录日期**：2026-01-31
**标签**：#shader #unity #experience #urp #srp-batcher #renderer-feature
**状态**：✅ 已验证
**来源**：Technical_Artist_Technotes/TA零散知识
**可信度**：⭐⭐⭐⭐ (实践验证)

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

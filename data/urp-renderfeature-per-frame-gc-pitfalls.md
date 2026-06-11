# URP RenderFeature 每帧 GC 排查：OnCameraSetup 字符串插值与 ReAllocateIfNeeded name 比较机制

**收录日期**：2026-06-11
**标签**：#unity #urp #renderer-feature #performance #experience
**来源**：VR 项目自定义 Bloom RenderFeature 实践，结论经 URP 包源码核查验证
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐⭐（直接验证自 URP 14.0.12 包源码）
**适用版本**：Unity 2022.3 / URP 14.0.x（RTHandle + ReAllocateIfNeeded 体系；Unity 6 改用 ReAllocateHandleIfNeeded，机制类似但未逐行核对）

**问题/场景**：

自定义 `ScriptableRendererFeature`（多级 RT 链的后处理，如 Dual Kawase Bloom）在 Profiler 中**每帧产生 GC Alloc**，需要定位分配来源。

### 概要

`OnCameraSetup` 每帧执行，在其中用 `$""` 字符串插值生成 RTHandle 名称是每帧 GC 的典型根因；`ReAllocateIfNeeded` 每帧用 `handle.name != descriptor.name` 做字符串**值比较**，名称内容必须逐帧稳定，否则会触发 RT 反复重建。正确做法是把 RT 名称提为静态常量字符串数组。

### 内容

#### 根因

`ScriptableRenderPass.OnCameraSetup` 每帧、每相机执行。以下写法每帧分配新字符串（链路级数 × 每帧）：

```csharp
// ❌ 每帧 GC：插值每次调用都分配新 string
RenderingUtils.ReAllocateIfNeeded(ref _rt[i], desc, FilterMode.Bilinear,
    TextureWrapMode.Clamp, name: $"_MyFeatureRT{i}");
```

#### URP 源码证据（com.unity.render-pipelines.universal@14.0.12）

`Runtime/RenderingUtils.cs` 中 `RTHandleNeedsReAlloc`（约 525-552 行）每帧比较所有描述符字段，**最后一项是 name**：

```csharp
return
    (DepthBits)handle.rt.descriptor.depthBufferBits != descriptor.depthBufferBits ||
    // ... 其余描述符字段比较 ...
    handle.name != descriptor.name;   // 第 551 行：字符串值比较
```

由此得出两条结论：

1. **C# 字符串 `!=` 是值比较**，内容相同的插值串不会触发 RT 重建——所以插值写法"能用"，但每帧的字符串分配躲不掉。
2. 若名称内容逐帧变化（如把帧号、分辨率拼进名字），会**每帧重建 RT**，这是远比 GC 更严重的隐藏炸弹。

#### 正确写法

```csharp
// ✅ RT 名称预生成为静态常量，OnCameraSetup 内禁止 $"" 插值
static readonly string[] s_RTNames =
    { "_MyFeatureRT0", "_MyFeatureRT1", "_MyFeatureRT2", "_MyFeatureRT3" };

RenderingUtils.ReAllocateIfNeeded(ref _rt[i], desc, FilterMode.Bilinear,
    TextureWrapMode.Clamp, name: s_RTNames[i]);
```

#### 已逐一排除的嫌疑（同版本源码核查）

| 嫌疑 | 结论 |
|------|------|
| `RenderingUtils.ReAllocateIfNeeded` | 未触发重建时无托管分配（`CreateTextureDesc` 返回 struct） |
| `RTHandle.name` | 返回缓存字段 `m_Name`，非原生 `RenderTexture.name` 取值，无分配 |
| `ProfilingScope` / `using (new ProfilingScope(...))` | struct，`using` 对 struct 不装箱，无分配 |
| `CommandBufferPool.Get()` | 对象池，预热后无分配 |
| `Blitter.BlitCameraTexture` | 内部用静态 MaterialPropertyBlock，无每帧分配 |
| `Shader.PropertyToID` | 静态缓存为 `static readonly int` 即无分配 |

#### 验证方式

- Profiler 中对应 ProfilingSampler 条目与 `RenderingUtils` 的 GC Alloc 应为 0 B（首帧的 RT 分配与 CommandBufferPool 预热属正常一次性分配）。
- Editor 下抓帧时 URP 自身与 Profiler 仍可能有少量编辑器专属分配，**以真机 / Development Build 数据为准**。

### 参考链接

- [URP 14 RenderingUtils.cs（needle-mirror 镜像）](https://github.com/needle-mirror/com.unity.render-pipelines.universal/blob/master/Runtime/RenderingUtils.cs) - ReAllocateIfNeeded / RTHandleNeedsReAlloc 源码
- 本地核查路径（项目内）：`Library/PackageCache/com.unity.render-pipelines.universal@14.0.12/Runtime/RenderingUtils.cs`

### 相关记录

- [URP 中 GrabPass 替代方案](./urp-grabpass-alternative.md) - 同为 RTHandle + ReAllocateIfNeeded 用法
- [Godot Bloom：Fast Mipmap Dual Kawase 4K 实践](./godot-bloom-fast-mipmap-dual-kawase-4k-practice.md) - 触发本次排查的 Bloom 算法来源

### 验证记录

- [2026-06-11] 初次记录。VR 项目自定义 Bloom RenderFeature 每帧 GC 排查实录：根因为 OnCameraSetup 内 `$""` 插值；改为静态常量数组后消除。所有"已排除嫌疑"均逐行读 URP 14.0.12 本地包源码确认。

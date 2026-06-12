# URP RenderFeature 自定义后处理完整案例：Quest VR Dual Kawase Bloom

**收录日期**：2026-06-12
**标签**：#unity #urp #renderer-feature #shader #experience
**来源**：Quest VR 项目自定义 Bloom RenderFeature 实践（从零实现到真机验证的完整过程）
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐⭐（Quest2 真机 Profiler 验证 CPU 0.02ms / 零 GC；Frame Debugger 验证链路结构）
**适用版本**：Unity 2022.3 / URP 14.0.x（RTHandle + Blitter 体系）

**问题/场景**：

如何用 ScriptableRendererFeature + RTHandle + Blitter 从零实现一个绕过 Volume/PostProcess 体系的多级 RT 链渲染效果（以 Dual Kawase Bloom 为例），并满足移动 VR（XR Single Pass Instanced）兼容与零 GC 约束。本记录是能力组合的**完整案例**，基础概念见[URP Renderer Feature 开发要点](./urp-renderer-feature-guide.md)。

### 概要

完整展示自定义后处理 RenderFeature 的七项核心能力：Feature/Pass 骨架与相机过滤、RTHandle 链管理（ReAllocateIfNeeded）、XR 兼容 Blit（Blitter + TEXTURE2D_X）、命令流参数注入（cmd.SetGlobalXXX vs material.SetXXX 语义差异）、硬件混合合成省全屏 copy、零 GC 纪律、分设备档位。每项都附踩坑点。

### 内容

#### 1. 总体结构：为什么绕过 Volume 体系

需求是移动 VR 上的低开销 Bloom。内置 Volume Bloom 默认 16 Blit / 1/2 分辨率起步，且强制附带 UberPost 全屏 pass + LUT pass（见[内置 Bloom 性能对比](./urp-builtin-bloom-vs-dual-kawase-renderfeature-performance.md)）。自写 RenderFeature 可压到 6 Blit / 1/4 起步，链路：

```
相机颜色 → Prefilter+Down(1/4) → Down(1/8) → Down(1/16)
        → Up(1/8) → Up(1/4) → Blend One One 叠回相机颜色
```

#### 2. Feature 骨架与相机过滤

```csharp
public override void AddRenderPasses(ScriptableRenderer renderer, ref RenderingData renderingData)
{
    // Preview/Reflection 相机跑后处理纯浪费且会污染资源缩略图
    var camType = renderingData.cameraData.cameraType;
    if (camType == CameraType.Preview || camType == CameraType.Reflection) return;
    // Overlay 相机会对 UI 等内容重复施加效果，只在 Base 相机执行
    if (renderingData.cameraData.renderType != CameraRenderType.Base) return;
    renderer.EnqueuePass(_pass);
}
```

材质在 `Create()` 用 `CoreUtils.CreateEngineMaterial` 创建、`Dispose()` 用 `CoreUtils.Destroy` 释放。Shader 引用留 `Shader.Find` 兜底时，真机包必须在面板显式指定，否则有被裁剪风险。

#### 3. RTHandle 链管理（OnCameraSetup，每帧执行）

```csharp
var desc = renderingData.cameraData.cameraTargetDescriptor; // XR 下自动是 Texture2DArray×2
desc.depthBufferBits = 0;   // 纯颜色链不需要深度
desc.msaaSamples = 1;       // 低分辨率链不需要 MSAA
desc.useMipMap = false;
// 刻意保留相机原始 graphicsFormat：LDR=8bit sRGB，HDR 开启自动 B10G11R11/FP16，双兼容

for (int i = 0; i < iterations; i++)
{
    desc.width  = Mathf.Max(1, baseW >> i);
    desc.height = Mathf.Max(1, baseH >> i);
    RenderingUtils.ReAllocateIfNeeded(ref _down[i], desc, FilterMode.Bilinear,
        TextureWrapMode.Clamp, name: s_DownNames[i]); // 名称必须是静态常量！
}
```

要点：
- 描述符从 `cameraTargetDescriptor` 派生，XR 双眼数组、动态分辨率自动正确；
- `ReAllocateIfNeeded` 在分辨率/档位变化时自动重建，只需 `Dispose` 时 `Release()`；
- **RT 名称必须静态常量数组**——每帧 `$""` 插值是 GC 根因，详见[每帧 GC 排查](./urp-renderfeature-per-frame-gc-pitfalls.md)。

#### 4. XR 兼容 Blit：Blitter API + stereo 宏

C# 侧全部用 `Blitter.BlitCameraTexture(cmd, src, dst, material, passIndex)`，**禁止 `cmd.Blit`**（XR Single Pass Instanced 下不正确）。Shader 侧配套三件套：

```hlsl
#include "Packages/com.unity.render-pipelines.core/Runtime/Utilities/Blit.hlsl" // 提供 Vert/Varyings/_BlitTexture
TEXTURE2D_X(_MyExtraTex);   // 所有屏幕类纹理用 TEXTURE2D_X（XR 下是 Texture2DArray）

half4 Frag(Varyings input) : SV_Target
{
    UNITY_SETUP_STEREO_EYE_INDEX_POST_VERTEX(input); // 漏掉 → 右眼黑屏
    half3 c = SAMPLE_TEXTURE2D_X(_BlitTexture, sampler_LinearClamp, input.texcoord).rgb;
    ...
}
```

另外 Blitter 不提供源纹理 texel size，需要的话由 C# 每次 Blit 前自行注入（见下节）。

#### 5. 参数注入：cmd.SetGlobalXXX 与 material.SetXXX 的语义差异（关键坑）

- `material.SetXXX`：命令缓冲**录制期间 last-value-wins**——录制 6 个 Blit 各 Set 一次，执行时所有 draw 拿到的都是最后一次的值；
- `cmd.SetGlobalXXX`：**按命令流顺序生效**，每个 Blit 能拿到属于自己的值。

结论：整链恒定的参数（强度/阈值/色调）走 material；逐 Blit 变化的值（当前源的 texel size、注入纹理）必须走 `cmd.SetGlobalVector/SetGlobalTexture`。全局量命名加效果前缀（如 `_MyBloomSrcTexel`）避免污染其他 shader。

#### 6. 合成：硬件加法混合省一次全屏 copy（TBR 带宽最大单项优化）

合成 Pass 用 `Blend One One`，以 bloom 链结果为 Blit 源直接画到相机颜色目标：

- 不在 shader 里采样相机颜色 → 规避"源=目标"非法采样，也不需要先把相机颜色 copy 出来；
- TBR GPU 上混合的 dst 读取发生在片上 GMEM，不产生外部带宽；
- 依赖条件：Renderer 的 Intermediate Texture = Always（保证相机颜色是中间 RT 而非 backbuffer）。

#### 7. 零 GC 纪律（每帧路径）

| 项 | 做法 |
|---|---|
| shader 属性 | `static readonly int xxxId = Shader.PropertyToID(...)` |
| RT 名称 | 静态常量字符串数组 |
| 解析/查找逻辑 | for 循环，禁 LINQ |
| CommandBuffer | `CommandBufferPool.Get()/Release()` |
| Profiling | `ProfilingScope`（struct，using 不装箱） |
| 日志 | 仅状态变化时打印，禁每帧拼字符串 |

验证：Profiler 中对应条目 GC Alloc = 0 B（首帧 RT 分配属正常），以真机/Development Build 为准。Quest2 真机实测本案例 CPU 0.02ms。

#### 8. 分设备档位（移动 VR 常见需求）

性能参数（链级数/采样半径等）与美术参数（强度/阈值/色调）**拆成两组**：前者按设备等级独立配置 + 设备级开关（低端机可整档关闭），后者全设备共享避免两端调色不一致。设备检测用 `Unity.XR.Oculus.Utils.GetSystemHeadsetType()`，结果静态缓存（native 调用不可每帧做；XR 初始化前返回 None，此时不固化缓存、下帧重试）。

**重大坑**：AndroidManifest 的 `com.oculus.supportedDevices` 未声明的新设备会触发 Horizon OS **兼容模式**，系统向 App 伪装上报为清单内最近一代设备（如 Quest3S 报成 Quest2），且无 API 可检测兼容模式。Unity 中该清单值由 OVRManager 面板的 Target Devices 勾选项经 `OVRManifestPreprocessor` 生成，勾选后需手动跑 `Meta > Tools > Update AndroidManifest.xml` 重新生成。

#### 9. 验证手段清单

- **链路结构**：Frame Debugger 看 Blit 数与各级 RT 分辨率是否符合预期；
- **CPU/GC**：Profiler（Hierarchy 看条目时长与 GC Alloc；Timeline 看主线程+渲染线程两段）；
- **GPU**：Unity Profiler 连 Quest 通常拿不到 GPU 时间，用 OVR Metrics Tool / `adb shell ovrgpuprofiler` / RenderDoc Meta Fork 做开关 A/B；
- **后处理类效果的特性**：CPU/GPU 成本几乎与场景内容无关（固定结构全屏链），空场景测得的增量≈真实场景增量。

### 参考链接

- [URP 14 RenderingUtils.cs（needle-mirror 镜像）](https://github.com/needle-mirror/com.unity.render-pipelines.universal/blob/master/Runtime/RenderingUtils.cs) - ReAllocateIfNeeded 源码
- [Meta Compatibility Mode 官方文档](https://developers.meta.com/horizon/documentation/unity/os-compatibility-mode/) - supportedDevices 兼容模式行为
- [SimpleURPKawaseBlur（参考实现）](https://github.com/tomc128/urp-kawase-blur) - Dual Kawase 在 URP 的社区实现

### 相关记录

- [URP Renderer Feature 开发要点](./urp-renderer-feature-guide.md) - 基础概念与骨架
- [URP RenderFeature 每帧 GC 排查](./urp-renderfeature-per-frame-gc-pitfalls.md) - 本案例踩到的 GC 坑的深挖
- [URP 内置 Bloom vs 自定义 Dual Kawase 性能对比](./urp-builtin-bloom-vs-dual-kawase-renderfeature-performance.md) - 本案例与内置方案的量化对比
- [URP 中 GrabPass 替代方案](./urp-grabpass-alternative.md) - 同体系的另一个 RTHandle+Blit 案例
- [Godot Bloom：Fast Mipmap Dual Kawase 4K 实践](./godot-bloom-fast-mipmap-dual-kawase-4k-practice.md) - 算法来源

### 验证记录

- [2026-06-12] 初次记录。链路结构经 Frame Debugger 确认（档位切换 Blit 数 4↔6↔8 正确变化）；零 GC 与 CPU 0.02ms 经 Quest2 真机 Profiler 确认；设备伪装坑在 Quest3S 真机复现并经 Meta 官方文档证实；Blend One One 合成与 stereo 宏要求经 Quest 真机双眼显示验证。

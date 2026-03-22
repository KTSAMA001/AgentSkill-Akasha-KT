# Unity 2022.3 → 6.3 LTS 完整迁移指南

**标签**：#unity #urp #shader #knowledge #reference #rendering #dots #migration
**来源**：官方文档 + 社区搜索整理 / 2026-03
**收录日期**：2026-03-23
**来源日期**：2025-2026
**状态**：⚠️待验证
**可信度**：⭐⭐⭐⭐（官方文档 + 社区验证）
**适用版本**：Unity 2022.3 → Unity 6000.3.x LTS

### 概要

从 Unity 2022.3 迁移到 Unity 6.3 LTS (6000.3.x) 的完整参考。Unity 6 经历了 6.0→6.1→6.2→6.3 四个迭代，6.3 是当前推荐 LTS（支持至 2027 年 12 月）。覆盖各版本累计变化、Breaking Changes、新功能速查、TA/客户端影响评估和 5 阶段迁移路线图。

---

### 一、版本现状（2026-03）

| 版本 | 格式 | 状态 | 最新补丁 | 支持期限 |
|------|------|------|---------|---------|
| **Unity 2022.3** | 2022.3.x | 3年 LTS | 2022.3.73f1 | 标准支持已结束，补丁仍发布 |
| Unity 6.0 | 6000.0.x | LTS（即将结束） | 6000.0.71f1 | 至 2026-10 |
| Unity 6.1 | 6000.1.x | **已停止支持** | 6000.1.2f1 | 已结束 |
| Unity 6.2 | 6000.2.x | **已停止支持** | 6000.2.15f1 | 已结束 |
| **Unity 6.3** | 6000.3.x | **当前 LTS ⭐** | 6000.3.11f1 | 至 2027-12 |
| Unity 6.4 | 6000.4.x | Supported | 6000.4.0f1 | 2026 年更新中 |

**选择建议**：新项目 → Unity 6.3 LTS | 老项目维护 → 2022.3 LTS | 追新功能 → Unity 6.4

---

### 二、Unity 6 各版本累计变化

#### 6.0 — 基础架构

| 模块 | 变化 |
|------|------|
| 渲染 | Render Graph 引入（默认开启）、GPU Resident Drawer、WebGPU 实验性 |
| ECS | Entities 1.0 独立包可用（不绑定 6.0，可在旧版使用） |
| 网络 | Multiplayer Play Mode |
| AI | Unity Sentis（Barracuda 继任者） |
| 平台 | WebGPU 实验性、Gradle 8.4、JDK 17 |

#### 6.1 — 图形跃迁

| 模块 | 变化 |
|------|------|
| 渲染 | **URP Forward+**（延迟平铺多光源）、**DX12 成为 Windows 默认**、VRS、双三次 Lightmap 采样 |
| Shader | Shader Variants 精简（减少构建时间） |
| 编辑器 | 菜单结构重组、脚本创建可选保存位置 |
| WebGPU | 计算着色器、间接渲染、GPU Skinning、VFX Graph |
| XR | Meta Quest 构建配置、Mixed Reality 模板 |

#### 6.2 — AI 与工具链

| 模块 | 变化 |
|------|------|
| AI | **Unity AI 套件**（Assistant 项目感知助手、Generators 统一生成器） |
| 图形 | Mesh LOD 自动生成、Shader Graph 动态分支（减少变体）、Render Graph Subpass 合并 |
| 诊断 | Developer Data Framework 默认启用 |
| ECS | Entities 1.4、Unity Vehicles 实验包 |
| UI | World Space UI 支持 |
| 平台 | Android SDK 36 |

#### 6.3 — LTS 稳定化

| 模块 | 变化 |
|------|------|
| 2D | **Box2D v3 集成**（多线程性能提升）、3D 网格渲染为 2D |
| 渲染 | **URP/HDRP 共享 Render Graph 基础**、自定义地形着色器、Per-Renderer User Value、Bloom 过滤选项 |
| 光照 | **GPU Lightmapper 默认启用**、xAtlas Lightmap 打包、反射探针旋转、UnifiedRayTracing API |
| 动画 | Legacy Animation 性能提升 30%、`Animator.ResetControllerState` |
| 音频 | **可脚本化音频管线**（Burst 编译 C# 音频处理单元） |
| UI | UI Test Framework、USS Filter（模糊/灰度）、内置 Vector Graphics（SVG） |
| 无障碍 | 桌面原生屏幕阅读器支持 |
| 编辑器 | 工具栏自定义、新版 Hierarchy（Preview）、Search LMDB 后端、深度链接、Package Manager 签名验证 |
| 平台 | **Android 最低版本提升至 7.1 (API 25)**、UnityWebRequest HTTP/2 默认、Web IL2CPP 优化 |
| XR | On-tile 后处理、自动视口动态分辨率 |

---

### 三、Breaking Changes（2022.3 → 6.3 累计）

#### 已移除

| 功能 | 版本 | 替代方案 |
|------|------|----------|
| Enlighten Baked GI | 6.0 | Progressive Lightmapper |
| Auto Generate Lighting | 6.0 | 手动 Bake / `Lightmapping.BakeAsync()` |
| Ambient Probe 自动烘焙 | 6.0 | 手动 Generate Lighting |
| Cinemachine 2 | 6.5 起 | Cinemachine 3（API 完全重写） |
| Magic Leap XR | 6.3 后 | 仅限现有项目 |
| Android < 7.1 | 6.3 | 最低 API 提升至 25 |

#### 已废弃 API

```csharp
// 查找 API — 性能更好，语义更明确
// ❌ 废弃
Object.FindObjectsOfType<T>()
Object.FindObjectOfType<T>()
// ✅ 替代
Object.FindObjectsByType<T>(FindObjectsSortMode.None)
Object.FindFirstObjectByType<T>()
Object.FindAnyObjectByType<T>()

// 渲染管线属性
// ❌ 废弃
[CustomEditorForRenderPipeline(typeof(MyInspector))]
[VolumeComponentMenuForRenderPipeline("My/Volume", typeof(URP))]
// ✅ 替代
[CustomEditor(typeof(MyInspector)), SupportedOnRenderPipeline(typeof(URP))]
[VolumeComponentMenu("My/Volume"), SupportedOnRenderPipeline(typeof(URP))]

// 渲染纹理格式
// ❌ DepthAuto, ShadowAuto, VideoAuto → ✅ GraphicsFormat.None
```

#### 平台工具版本

| 工具 | 2022.3 | 6.3 |
|------|--------|-----|
| Gradle | 7.x | **8.4** |
| Android Gradle Plugin | 7.x | **8.3.0** |
| SDK Build Tools | 33.x | **34.0.0+** |
| JDK | 11 | **17** |
| .NET | .NET Standard 2.1 (Mono) | .NET 6 Framework (Mono) |
| C# | C# 9 | C# 9 (部分) |

> ⚠️ 6.3 仍是 Mono/.NET 6，**不是 .NET 8**。.NET 8 预计 6.4+。

---

### 四、核心模块详解

#### 4.1 Render Graph — 渲染底层调度

| 版本 | 状态 |
|------|------|
| 6.0 | 默认**开启**，可通过 Compatibility Mode 手动关闭（用于过渡旧代码） |
| 6.1+ | 推荐保持启用，Compatibility Mode 不再是生产路径 |
| 6.3 | URP/HDRP 共享统一 Render Graph 基础，新增 Render Graph Viewer（支持设备连接） |

**升级策略**：6.0 开启 Render Graph 但提供 Compatibility Mode 兼容旧代码。6.1+ Compatibility Mode 不再作为生产路径。6.3 提供 Render Graph Viewer 可在移动端实时调试。

```csharp
// ❌ 旧 — Execute()
public override void Execute(ScriptableRenderContext context,
                              ref RenderingData renderingData)
{
    CommandBuffer cmd = CommandBufferPool.Get("CustomPass");
    cmd.GetTemporaryRT(m_Handle.id, desc);  // 手动管理
    // ...
    cmd.ReleaseTemporaryRT(m_Handle.id);
    context.ExecuteCommandBuffer(cmd);
}

// ✅ 新 — RecordRenderGraph()
public override void RecordRenderGraph(RenderGraph renderGraph,
                                       ContextContainer frameData)
{
    TextureHandle src = renderGraph.ImportTexture(m_Source);
    using (var builder = renderGraph.AddRasterRenderPass<PassData>(
               "CustomPass", out var data))
    {
        builder.SetTextureAccess(src, AccessFlags.Read);
        builder.SetRenderFunc((PassData d, RasterGraphContext ctx) => { });
    }
    // 纹理生命周期由系统自动管理
}
```

| 旧 API | 新 API |
|--------|--------|
| `RenderTargetHandle` | `RTHandle` |
| `RenderTargetIdentifier` | `TextureHandle` |
| `cmd.GetTemporaryRT()` | 系统自动管理 |
| `cmd.ReleaseTemporaryRT()` | 不需要 |
| `cameraColorTarget` | `cameraColorTargetHandle` |

#### 4.2 URP Forward+ — 6.1 新增

| 特性 | Forward（旧） | Forward+（6.1+） |
|------|---------------|------------------|
| 光源数量 | 有限（性能下降） | **大幅提升**（延迟平铺） |
| 透明物体 | 支持 | 支持 |
| 光照贴图 | 支持 | 支持 |
| GPU Resident Drawer | 不支持 | 支持 |
| 适用场景 | 移动端低端 | 移动端中高端、VR、多光源场景 |

**DX12 注意**：6.1 起 DX12 是 Windows 新项目默认图形 API。

#### 4.3 GPU Resident Drawer

**硬件要求**：Forward+ / Deferred+ 渲染路径 + Compute Shader（**不支持 OpenGL ES**）+ SRP Batcher

**最佳场景**：大场景 + 同 Mesh 多实例
**不适用**：每个物体都不同、移动低端设备
**构建影响**：⚠️ 时间显著增长

#### 4.4 Adaptive Probe Volumes

| 对比项 | Light Probe Groups (2022.3) | Adaptive Probe Volumes (6.x) |
|--------|---------------------------|---------------------------|
| 采样精度 | Per-Object | **Per-Pixel** |
| 放置方式 | 手动 | 自动 |
| 流式加载 | 不支持 | 支持 |
| 光照混合 | 不支持 | 支持 |
| 手动微调 | 支持 | 不支持 |
| 转换 | — | ⚠️ 无法从旧探针转换 |

**6.3 补充**：反射探针支持旋转，GPU Lightmapper 默认启用，xAtlas 打包更紧凑。

#### 4.5 Shader Graph 演进

| 版本 | 变化 |
|------|------|
| 6.0 | 基础 Render Graph 支持 |
| 6.1 | Shader Variants 精简（减少构建时间） |
| 6.2 | 动态分支（关键词支持动态分支，减少变体数量） |
| 6.3 | **模板系统**、自定义地形着色器、自定义光照着色器、UI 着色器、Per-Renderer User Value |

**6.3 Per-Renderer User Value**：`unity_RendererUserValue`，单材质实现大量对象差异化，减少材质变体。

#### 4.6 动画系统

| 版本 | 变化 |
|------|------|
| 6.3 | Legacy Animation 性能提升 **30%** |
| 6.3 | `Animator.ResetControllerState` 简化对象池化 |
| 路线图 | 新动画系统计划中（HPC# 底层，预计 6.5-7.0） |

#### 4.7 2D 物理

| 版本 | 变化 |
|------|------|
| 6.3 | **Box2D v3 集成**，`UnityEngine.LowLevelPhysics2D` API，多线程性能提升 |
| 6.3 | 3D Mesh Renderer 可在 2D Renderer 中与 Sprite 混合渲染 |

#### 4.8 Unity AI 套件（6.2+）

| 功能 | 说明 |
|------|------|
| **AI Assistant** | 项目感知助手（/ask、/run、/code 三种模式） |
| **AI Generators** | 统一生成 Sprite、Texture2D、Sound、Animation、Material |
| **Sentis** | 本地 AI 推理引擎（Barracuda 继任者） |

---

### 五、对 TA / 客户端开发者的影响评估

| 变更项 | 影响度 | 紧急度 | 工作量 | 涉及版本 |
|--------|--------|--------|--------|---------|
| Render Graph 迁移 | 🔴 高 | P0 | 大 | 6.0+（默认开启） |
| Shader Graph 升级（模板/动态分支） | 🔴 高 | P0 | 中 | 6.2-6.3 |
| DX12 默认 | 🔴 高 | P0 | 小 | 6.1+ |
| Cinemachine 3 | 🔴 高 | P1 | 中 | 6.5 起 |
| URP Forward+ | 🔴 高 | P1 | 小 | 6.1+ |
| GPU Resident Drawer | 🔴 高 | P1 | 小 | 6.0+ |
| APV 替换探针 | 🔴 高 | P1 | 中 | 6.0+ |
| Enlighten 移除 | 🔴 高 | P0 | 小 | 6.0+ |
| Shader Variants 精简 | 🟡 中 | P1 | 小 | 6.1-6.2 |
| Mesh LOD 自动生成 | 🟡 中 | P2 | 小 | 6.2+ |
| Per-Renderer User Value | 🟡 中 | P2 | 小 | 6.3 |
| 自定义地形着色器 | 🟡 中 | P2 | 小 | 6.3 |
| VFX Graph 兼容性 | 🔴 高 | P1 | 小~中 | 6.x |
| Addressables 2.x | 🟡 中 | P2 | 小 | 6.x |
| Box2D v3 2D 物理 | 🟡 中 | P3 | 中 | 6.3 |
| 可脚本化音频管线 | 🟡 中 | P3 | 中 | 6.3 |
| Legacy Animation 30% 提升 | 🟢 低 | P3 | 无（自动） | 6.3 |
| Sentis 替代 Barracuda | 🟢 低 | P3 | 小 | 6.0+ |

---

### 六、已知问题

#### 🔴 严重

| 问题 | 影响版本 | 说明 |
|------|---------|------|
| 编辑器内存泄漏 | 6000.x 多版本 | Terrain 操作可能冻结 |
| DX12 兼容性 | 6.1+（默认） | 部分项目/插件崩溃 |
| Vulkan + Render Graph 崩溃 | 6000.0.25/.32 | 特定版本组合 |
| 物理性能退化 | 6000.x | Trigger 事件异常频繁 |
| VFX Graph 损坏 | 6.51+ | 旧版 VFX 可能完全损坏 |
| Shader Graph 编译失败 | 6.x | 第三方着色器兼容性差 |

#### 🟡 中等

| 问题 | 说明 |
|------|------|
| Build 后 Shader 失效 | Editor 正常但 Build 异常 |
| GRD 构建时间增长 | 编译所有 BRG shader 变体 |
| Android 兼容性 | GRD 在部分设备不稳定 |
| Developer Data Framework | 6.2+ 新项目默认启用遥测收集 |

---

### 七、迁移路线图（2022.3 → 6.3 LTS）

#### Phase 1：升级准备（1-2 天）
1. 备份项目，创建迁移分支
2. 全局搜索替换废弃 API（`FindObjectsOfType` → `FindObjectsByType`）
3. 检查所有 Asset Store 包的 Unity 6 兼容性声明
4. 替换渲染管线属性标记
5. 评估 Cinemachine 使用情况（6.5 前需迁移到 CM3）

#### Phase 2：基础升级（2-5 天）
1. 升级到 6000.3.x 最新补丁
2. 修复编译错误（重点关注第三方包）
3. 替换 Enlighten → Progressive/GPU Lightmapper
4. 验证渲染管线兼容模式正常工作
5. 验证 Android 最低 API 25（影响目标设备）

#### Phase 3：渲染管线迁移（1-2 周）
1. 启用 Render Graph（关闭 Compatibility Mode）
2. 重写所有自定义 Render Feature / Render Pass
3. 迁移 `RenderTargetHandle` → `RTHandle`
4. 利用 Shader Graph 6.3 新功能（模板、动态分支、Per-Renderer User Value）
5. 使用 Render Graph Viewer 在设备端调试
6. 测试全部后处理效果

#### Phase 4：新功能接入（按需，1-2 周）
1. 评估 URP Forward+（多光源场景）
2. 评估 GRD（Forward+/Deferred+ + Compute Shader）
3. 评估 APV 替换 Light Probes
4. 评估 Mesh LOD 自动生成（减少美术手动 LOD 工作）
5. 迁移 Cinemachine 2 → 3（6.5 截止前）
6. 评估 Per-Renderer User Value 减少材质变体

#### Phase 5：高级优化（按需）
1. Box2D v3 2D 物理评估
2. 可脚本化音频管线评估
3. Legacy Animation 30% 性能提升（自动生效）
4. Unity AI 套件评估
5. DOTS/ECS 评估
6. Multiplayer Play Mode 配置

---

### 八、新功能速查表

| 功能 | 版本 | 说明 |
|------|------|------|
| Render Graph | 6.0+ | 统一渲染图，自动管理纹理 |
| GPU Resident Drawer | 6.0+ | GPU 驱动剔除+绘制 |
| Multiplayer Play Mode | 6.0+ | 编辑器多客户端联机 |
| WebGPU | 6.0+ | 下一代网页图形 API |
| URP Forward+ | 6.1+ | 延迟平铺多光源 |
| Shader Variants 精简 | 6.1+ | 减少构建时间 |
| Unity AI 套件 | 6.2+ | AI 助手 + 生成器 |
| Mesh LOD 自动生成 | 6.2+ | 导入时自动生成 |
| Shader Graph 动态分支 | 6.2+ | 减少变体数量 |
| 自定义地形着色器 | 6.3 | Shader Graph 创建 |
| Per-Renderer User Value | 6.3 | 单材质差异化 |
| GPU Lightmapper 默认 | 6.3 | 更快的光照烘焙 |
| Box2D v3 | 6.3 | 多线程 2D 物理 |
| 可脚本化音频管线 | 6.3 | Burst C# 音频处理 |
| Legacy Animation +30% | 6.3 | 自动生效 |
| UI Test Framework | 6.3 | 自动化 UI 测试 |
| DLSS4 Super Resolution | 6.3 | 最新超分 |
| On-tile XR 后处理 | 6.3 | XR 性能提升 |

---

### 参考链接

- [Unity 6 升级指南](https://docs.unity3d.com/6000.3/Documentation/Manual/UpgradeGuideUnity6.html) — 官方迁移文档
- [Unity 6.3 新功能](https://docs.unity3d.com/6000.3/Documentation/Manual/WhatsNewUnity6.html) — 6.3 更新日志
- [Unity 6.1 新功能](https://docs.unity3d.com/6000.1/Documentation/Manual/WhatsNewUnity6_1.html) — 6.1 更新日志
- [Unity 6.2 新功能](https://docs.unity3d.com/6000.2/Documentation/Manual/WhatsNewUnity6_2.html) — 6.2 更新日志
- [URP 升级指南](https://docs.unity3d.com/6000.0/Documentation/Manual/urp/upgrade-guide-unity-6.html) — URP 迁移
- [Render Graph Viewer](https://docs.unity3d.com/6000.3/Documentation/Manual/render-graph-debugger.html) — 6.3 设备端调试

### 相关记录

- [自定义 PBR BRDF 实现](./pbr-custom-brdf-implementation.md) — 渲染管线相关
- [URP Renderer Feature 开发经验](./urp-renderer-feature-custom.md) — 需迁移的代码模式
- [CBUFFER 与 SRP Batcher 合批机制](./cbuffer-srp-batcher-mechanism.md) — 仍适用
- [Shader 性能优化](./shader-optimization-hlsl.md) — 参考策略

### 验证记录

- [2026-03-23] 初次记录，来源：官方文档 + 搜索引擎收集，未经实践验证
- [2026-03-23] 修正：基于 6.3 LTS（6000.3.x）重写，覆盖 6.0→6.1→6.2→6.3 完整变化历程
- [2026-03-23] 验证修正（交叉验证 22 条事实）：
  - ✅ 修正：Render Graph 在 6.0 默认**开启**（非关闭），Compatibility Mode 是手动关闭选项
  - ✅ 修正：6.1 新增的是 **URP Forward+**（非 Deferred+），延迟平铺多光源
  - ✅ 修正：Entities 1.0 是独立包，不绑定 Unity 6.0 发布
  - ✅ 修正：2022.3 标准支持已于 2025-05 结束，补丁仍发布（非"2026 年结束"）
  - ✅ 确认：6000.4.0f1 于 2026-03-18 发布（版本现状表已包含）

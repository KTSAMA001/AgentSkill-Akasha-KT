# Unity 6 (6000.x) 迁移指南

**标签**：#unity #urp #shader #knowledge #reference #rendering #dots
**来源**：官方文档 + 社区搜索整理 / 2026-03
**收录日期**：2026-03-23
**来源日期**：2025-03
**状态**：⚠️待验证
**可信度**：⭐⭐⭐⭐（官方文档 + 社区验证）
**适用版本**：Unity 6000.x (Unity 6)

### 概要

从 Unity 2022 LTS 升级到 Unity 6 的完整参考，覆盖 TA 和客户端开发者需要关注的所有 Breaking Changes、新功能、已知问题和迁移路线图。数据来源为官方文档与社区反馈，尚未实践验证。

---

### 一、核心架构变化

#### 1. Render Graph — 渲染底层调度

**旧机制**（2022 LTS）：即时执行，按代码顺序提交渲染指令，显存频繁申请释放。

**新机制**（Unity 6）：渲染图引擎，提前收集所有渲染需求，全局统筹合并 Pass，系统自动管理纹理生命周期。

**关键**：升级后 Render Graph **默认关闭**（兼容模式），旧代码可直接跑。但兼容模式不再获得新功能改进。新建项目默认启用。

| 旧 API | 新 API |
|--------|--------|
| `RenderTargetHandle` | `RTHandle` |
| `RenderTargetIdentifier` | `TextureHandle` |
| `cmd.GetTemporaryRT()` | 系统自动管理 |
| `cmd.ReleaseTemporaryRT()` | 不需要（自动回收） |
| `cameraColorTarget` (RenderTexture) | `cameraColorTargetHandle` (RTHandle) |

**代码对比**：

```csharp
// ❌ 旧 — ScriptableRenderPass.Execute()
public override void Execute(ScriptableRenderContext context,
                              ref RenderingData renderingData)
{
    CommandBuffer cmd = CommandBufferPool.Get("CustomPass");
    cmd.GetTemporaryRT(m_Handle.id, desc);
    // ... 渲染逻辑
    cmd.ReleaseTemporaryRT(m_Handle.id);
    context.ExecuteCommandBuffer(cmd);
}

// ✅ 新 — ScriptableRenderPass.RecordRenderGraph()
public override void RecordRenderGraph(RenderGraph renderGraph,
                                       ContextContainer frameData)
{
    TextureHandle source = renderGraph.ImportTexture(m_Source);
    using (var builder = renderGraph.AddRasterRenderPass<PassData>("CustomPass",
               out var passData))
    {
        builder.SetTextureAccess(source, AccessFlags.Read);
        builder.SetRenderFunc((PassData data, RasterGraphContext ctx) => { });
    }
}
```

#### 2. GPU Resident Drawer — 海量物体绘制

将剔除和绘制逻辑移交 GPU，CPU 渲染耗时可降 30%-50%。**硬件要求**：

| 要求 | 说明 |
|------|------|
| 渲染路径 | **必须 Forward+** |
| 图形 API | 必须支持 Compute Shader（**不支持 OpenGL ES**） |
| SRP Batcher | 必须启用 |
| 最佳场景 | 大场景 + 同 Mesh 多实例（植被、建筑群） |
| 构建影响 | ⚠️ 显著增长（编译所有 BRG shader 变体） |

#### 3. Adaptive Probe Volumes — 智能光照探针

替代手工摆放的 Light Probe Groups，基于网格自动生成，支持流式加载和光照混合。

| 对比项 | Light Probe Groups | Adaptive Probe Volumes |
|--------|-------------------|----------------------|
| 采样精度 | Per-Object | **Per-Pixel** |
| 探针放置 | 手动 | 自动 |
| 流式加载 | 不支持 | 支持 |
| 手动微调 | 支持 | 不支持 |
| 转换 | — | ⚠️ 无法从旧探针转换，需重新烘焙 |
| 移动端开销 | 低 | Quest 3 约 5ms，需评估 |

---

### 二、Gemini 未覆盖的重要变更

#### 🔴 Cinemachine 3 — API 完全重写

**6.5 起 Cinemachine 2 停止维护！**

| Cinemachine 2 | Cinemachine 3 |
|---------------|---------------|
| `CinemachineVirtualCamera` | `CinemachineCamera` |
| `CinemachineBrain` | 集成到 Camera |
| `CinemachineImpulse` | 变更 API |

影响：相机切换逻辑、镜头脚本、Timeline Cinemachine Track 全部需重写。

#### 🔴 VFX Graph — 旧版损坏风险

- 旧版 VFX 在 6.51 中**可能完全损坏**
- 新功能：GPU Events Instancing、Read/Write Texture
- 升级后需逐个检查 VFX 效果

#### 🟡 Shader Graph — 兼容性问题

- 第三方着色器包兼容性差（Asset Store）
- Sprite 自定义着色器编译失败报告多
- ⚠️ Editor 正常但 Build 后 Shader 失效
- 6.3 新增：模板系统、8 组纹理坐标、Shader Graph 地形着色器

#### 🟡 .NET / C# 版本限制

| Unity 版本 | .NET 运行时 | C# 版本 |
|-----------|------------|---------|
| 6.0-6.3 | .NET 6 Framework (Mono) | C# 9 (部分) |
| 6.4 Alpha | .NET 8 Runtime | 更多特性 |
| 未来 | CoreCLR | C# 14 (2026-2028) |

**注意**：当前仍是 Mono/.NET 6，**不要用 .NET 8 的 API**。

#### 🟡 Addressables 2.x

- 推荐版本 2.x（最新 2.9.1）
- 升级后 Build Addressables 可能失败
- 自定义 Asset Provider 需重新检查配置

#### 🟢 Profiler 改进

- Highlights 模块：可视化帧时间 vs 目标帧率
- 内存分析工具更新
- 官方发布约 100 页性能优化指南

#### 🟢 Burst 编译器

- Job System 外的 `[BurstCompile]` 支持改进
- 默认接口方法不完全支持
- 10-100x 性能提升（HPC# 子集）

---

### 三、Breaking Changes 完整清单

#### 已移除

| 功能 | 状态 | 替代方案 |
|------|------|----------|
| Enlighten Baked GI | **已移除** | Progressive Lightmapper |
| Auto Generate Lighting | **已移除** | 手动 Bake / `Lightmapping.BakeAsync()` |
| Ambient Probe 自动烘焙 | **已移除** | 手动 Generate Lighting |
| Cinemachine 2 | **6.5 起停维** | Cinemachine 3 |

#### 已废弃 API

```csharp
// 查找 API
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

| 工具 | 2022 LTS | Unity 6 |
|------|----------|---------|
| Gradle | 7.x | **8.4** |
| Android Gradle Plugin | 7.x | **8.3.0** |
| SDK Build Tools | 33.x | **34.0.0** |
| JDK | 11 | **17** |

---

### 四、已知问题与坑点

#### 🔴 严重

| 问题 | 说明 |
|------|------|
| 编辑器内存泄漏 | Terrain 操作可能导致系统冻结 |
| DX12 默认 | 6.1 起成为默认图形 API，部分项目崩溃 |
| Vulkan 不稳定 | + Render Graph 组合时崩溃（6000.0.25/.32） |
| 物理性能退化 | Trigger 事件异常频繁 |
| VFX 损坏 | 旧版 VFX 在 6.51 可能完全损坏 |

#### 🟡 中等

| 问题 | 说明 |
|------|------|
| Shader Graph 编译失败 | 第三方着色器兼容性差 |
| Build 后 Shader 失效 | Editor 正常，Build 异常 |
| GRD 构建时间 | 显著增长 |
| Android 兼容性 | GRD 在部分设备不稳定 |

---

### 五、TA 影响评估

| 变更项 | 影响度 | 紧急度 | 工作量 |
|--------|--------|--------|--------|
| Render Graph 迁移 | 🔴 高 | P0 | 大 |
| Shader Graph 兼容性 | 🔴 高 | P0 | 中 |
| Cinemachine 3 | 🔴 高 | P1 | 中 |
| VFX Graph 检查 | 🔴 高 | P1 | 小~中 |
| GPU Resident Drawer | 🔴 高 | P1 | 小 |
| APV 替换探针 | 🔴 高 | P1 | 中 |
| Enlighten 移除 | 🔴 高 | P0 | 小 |
| Addressables 2.x | 🟡 中 | P2 | 小 |
| Sentis 替代 Barracuda | 🟢 低 | P3 | 小 |

---

### 六、迁移路线图

#### Phase 1：升级准备（1-2 天）
1. 备份项目
2. 扫描废弃 API（`FindObjectsOfType` → `FindObjectsByType`）
3. 检查所有 Asset Store 包的兼容性声明
4. 替换渲染管线属性标记

#### Phase 2：基础升级（1-3 天）
1. 升级到 6000.x 最新补丁
2. 修复编译错误
3. 替换 Enlighten → Progressive Lightmapper
4. 验证渲染管线兼容模式正常

#### Phase 3：渲染管线迁移（1-2 周）
1. 启用 Render Graph（关闭兼容模式）
2. 重写所有自定义 Render Feature
3. 迁移 `RenderTargetHandle` → `RTHandle`
4. 测试全部后处理效果

#### Phase 4：新功能接入（按需）
1. 评估 GRD（Forward+ + Compute Shader）
2. 评估 APV 替换 Light Probes
3. 评估 STP 超分
4. 迁移 Cinemachine 2 → 3（6.5 截止前）

#### Phase 5：高级优化
1. DOTS/ECS 评估
2. Sentis 本地推理
3. Multiplayer Play Mode

---

### 七、新功能速查

| 功能 | 说明 | 适用场景 |
|------|------|----------|
| Fullscreen Pass Renderer Feature | 拖拽 Shader Graph 材质即可实现全屏后处理 | 受击红屏、模糊等视觉特效 |
| STP 时空超分 | 原生集成，低分辨率渲染 + 无损拉伸 | 移动端、VR |
| Multiplayer Play Mode | 编辑器内多客户端联机测试 | 联机游戏开发 |
| Entities 2.0 | 工业级成熟，物理碰撞完善 | 海量物体场景 |
| WebGPU | 下一代网页图形 API，H5/小游戏画质对标原生 | 网页/小游戏端 |
| Unity Sentis | 内置神经网络引擎，本地推理 | 离线智能 NPC |

---

### 参考链接

- [Unity 6 升级指南](https://docs.unity3d.com/6000.3/Documentation/Manual/UpgradeGuideUnity6.html) — 官方迁移文档
- [Unity 6 新功能](https://docs.unity3d.com/6000.3/Documentation/Manual/WhatsNewUnity6.html) — 官方更新日志
- [URP 17 升级指南](https://docs.unity3d.com/6000.0/Documentation/Manual/urp/upgrade-guide-unity-6.html) — URP 迁移
- [GPU Resident Drawer](https://docs.unity3d.com/6000.0/Documentation/Manual/gpu-resident-drawer.html) — GRD 文档
- [Adaptive Probe Volumes](https://docs.unity3d.com/6000.3/Documentation/Manual/urp/probevolumes-concept.html) — APV 文档
- [Render Graph 介绍](https://www.youtube.com/watch?v=U8PygjYAF7A) — 视频教程

### 相关记录

- [自定义 PBR BRDF 实现](./pbr-custom-brdf-implementation.md) — 渲染管线相关
- [URP Renderer Feature 开发经验](./urp-renderer-feature-custom.md) — 需迁移的代码模式

### 验证记录

- [2026-03-23] 初次记录，来源：官方文档 + 搜索引擎收集，未经实践验证

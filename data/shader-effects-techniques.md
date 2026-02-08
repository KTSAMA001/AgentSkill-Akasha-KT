# 具体特效实现相关经验

> 具体特效实现相关经验
> 
> 包含：溶解、描边、扭曲、流光、全息、水面、火焰、遮挡透视等

---

## 遮挡透视效果实现方案 {#occlusion-vision}

**收录日期**：2026-02-07
**来源日期**：2024-08-08
**标签**：#shader #experience #effects
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

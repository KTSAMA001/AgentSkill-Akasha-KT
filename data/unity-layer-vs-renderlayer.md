# Unity 其他无法归类的经验

> Unity 其他无法归类的经验
> 
> 包含：项目配置、构建发布、平台适配、第三方插件等

---
## Layer 与 Render Layer 的区别

**日期**：2026-01-31
**标签**：#unity #experience #rendering
**状态**：✅ 已验证
**来源**：Technical_Artist_Technotes/TA零散知识

**问题/场景**：

Unity 中 Layer 和 Render Layer 有什么区别？在 SRP 中如何正确使用它们进行渲染筛选？

**核心概念**：

### 1. Layer（游戏层）

Layer 是 GameObject 的属性，用于：
- 物理碰撞筛选
- 相机 Culling Mask
- 射线检测筛选
- **渲染时的第一层筛选**

```csharp
// 设置物体 Layer
gameObject.layer = LayerMask.NameToLayer("Characters");

// Layer Mask 用于筛选
LayerMask mask = LayerMask.GetMask("Characters", "Props");
```

### 2. Render Layer（渲染层）

Render Layer 可以粗略理解为 **Pass 的属性**。在通过 Layer 筛选后，还要通过 Render Layer 筛选。

**用途**：在同一 Layer 内，进一步区分哪些物体由哪个 Pass 渲染

### 3. 在 Renderer Feature 中使用

```csharp
// 在 ScriptableRenderPass 的 Execute 中
FilteringSettings filteringSettings = new FilteringSettings(
    RenderQueueRange.opaque,
    layerMask: 1 << targetLayer,     // Layer 筛选
    renderingLayerMask: renderLayer  // Render Layer 筛选
);
```

### 4. 筛选流程

```
场景中所有物体
    ↓ Layer Mask 筛选
符合 Layer 的物体
    ↓ Render Layer Mask 筛选
最终渲染的物体
```

### 5. 常见问题

**问题**：使用 Renderer Feature 后，部分物体不被渲染

**排查**：
1. 检查物体的 Layer 是否在 Feature 的 Layer Mask 中
2. 检查物体 Renderer 组件的 Rendering Layer Mask 设置
3. 检查 Feature 的 Render Layer Mask 设置

**验证记录**：

- [2026-01-31] 从 Technical_Artist_Technotes 整理提取

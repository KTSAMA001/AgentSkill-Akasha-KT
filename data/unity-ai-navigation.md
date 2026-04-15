# Unity AI Navigation 知识

### 概要
Unity AI Navigation 知识


本文档记录 Unity AI Navigation (NavMesh) 系统相关的技术规范、机制和原理。

---

## 多场景独立烘焙与运行时连接机制

**标签**：#unity #knowledge #nav-mesh #ai-navigation
**来源**：Unity 官方文档 / 社区验证
**来源日期**：2026-02-05
**收录日期**：2026-02-05
**可信度**：⭐⭐⭐⭐ (官方文档+实践验证)
**状态**：📘 有效

### 定义/概念

在现代 Unity (AI Navigation 包) 中，支持对多个场景（或 Prefab）分别独立烘焙 NavMesh 数据。当这些场景在运行时以 `LoadSceneMode.Additive` 方式加载到一起时，系统会尝试将它们组合。

即使多个 NavMesh 块在空间上重叠，它们在内存和逻辑上依然是**独立**的网格数据 (`NavMeshData` 实例)，**不会**自动缝合边缘。

### 原理/详解

#### 1. 独立烘焙 (Independent Baking)
- 使用 `NavMeshSurface` 组件替代旧版的 Navigation 窗口。
- 每个场景/Prefab 挂载 `NavMeshSurface`，数据单独存储为 `.asset` 文件。
- 数据加载时通过 `NavMesh.AddNavMeshData()` 注册到全局 NavMesh 系统中。

#### 2. 连接机制 (Link Mechanism)
- **非自动缝合**：Unity 运行时**不会**自动计算两个独立 `NavMeshData` 的边缘并缝合它们，即使它们完美重叠。
- **NavMeshLink**：必须使用连接器（如 `NavMeshLink` 或 `OffMeshLink`）来跨越不同 `NavMeshData` 之间的边界。

#### 3. 对比：运行时烘焙 (Runtime Baking)
- 如果在运行时调用 `NavMeshSurface.BuildNavMesh()` 对整个合并后的场景进行**实时烘焙**，则生成的是**单个**连通的 NavMesh，边缘会自动处理。但这通常开销巨大。

### 关键点

- **独立烘焙 != 自动连通**：分开烘焙的数据块是物理隔离的“孤岛”。
- **必须使用 Link**：跨场景/跨模块寻路必须预置或动态生成 `NavMeshLink`。
- **无缝错觉**：如果两个网格重叠，Agent 有时看起来能过去，可能是因为使用了 `Warp` 或物理推挤，但从寻路图(Graph)层面看是不通的。

### 示例

**错误的做法**：
1. 烘焙场景 A 的地面。
2. 烘焙场景 B 的地面。
3. 运行时加载两者，边缘重叠。
4. 期望 Agent 自动拥有跨场景路径 -> **失败**。

**正确的做法**：
1. 分别烘焙。
2. 在场景 A/B 接缝处放置 `NavMeshLink`。
3. 运行时加载 -> **成功**。

### 参考链接

- [NavMesh Surface - Loading Multiple NavMeshes](https://docs.unity3d.com/Packages/com.unity.ai.navigation@1.1/manual/NavMeshSurface.html#loading-multiple-navmeshes-using-additive-loading) - 官方关于多场景加载的说明
- [Building a NavMesh at Runtime](https://docs.unity3d.com/Manual/nav-BuildingNavMesh.html) - 运行时构建 NavMesh
- [NavMesh Components (GitHub)](https://github.com/Unity-Technologies/NavMeshComponents) - Unity NavMesh Components 官方仓库


### 验证记录
- [2026-04-15] 结构修复：补齐模板必填章节，未改动原结论。

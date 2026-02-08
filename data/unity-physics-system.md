# Unity 物理系统知识
本文档记录 Unity 物理系统的核心概念与原理，偏"知识 + 原理"。

---

## 3D Collider 类型性能消耗对比

**标签**：#unity #knowledge #physics #collider #raycast
**来源**：Unity 2022.3 官方文档 - Collider types and performance  
**收录日期**：2026-02-01  
**来源日期**：2026-01-31  
**状态**：📘 有效
**可信度**：⭐⭐⭐⭐⭐ (官方文档)

### 性能排序（从低到高）

| 碰撞体类型 | 性能消耗 | 说明 |
|-----------|---------|------|
| **SphereCollider** | 🟢 最低 | 最简单高效，适用于圆形物体和通用交互 |
| **CapsuleCollider** | 🟢 较低 | 比 Sphere 稍复杂，但仍高效。适合角色、柱状物体 |
| **BoxCollider** | 🟡 中等偏低 | 高效灵活，适合方形/块状物体。比 Sphere/Capsule 略耗资源 |
| **Convex MeshCollider** | 🟠 较高 | 比 Primitive 碰撞体耗资源多。需凸面网格，可附加到非 Kinematic Rigidbody |
| **Non-Convex MeshCollider** | 🔴 最高 | 最耗资源。仅用于静态、不移动且需精确碰撞面的几何体 |

### 核心要点

1. **Primitive Colliders (Sphere/Capsule/Box)** 是最高效的类型
   - 由简单几何形状定义，多边形数量极少
   - 物理引擎使用数学公式直接计算，而非三角形遍历

2. **Compound Collider（复合碰撞体）**
   - 由多个 Primitive Collider 组合而成
   - 比单个 MeshCollider 更高效
   - 适合复杂动态物体（如车辆、机器人）

3. **MeshCollider 特性**
   - 需要 **mesh cooking** 预处理，将几何体转换为优化的物理格式
   - 运行时 cooking 会造成 CPU 峰值
   - Non-Convex MeshCollider **不能**附加到非 Kinematic Rigidbody
   - 建议启用 **Prebake Collision Meshes**（Player Settings）避免运行时 cooking

### 使用场景建议

| 场景 | 推荐碰撞体 |
|------|-----------|
| 子弹、球体、简单触发器 | SphereCollider |
| 角色控制器、人形 hitbox | CapsuleCollider |
| 箱子、墙壁、平台 | BoxCollider |
| 复杂动态物体（车辆） | Compound Collider（多个 Primitive 组合） |
| 静态环境（地形、建筑） | MeshCollider |

### 参考链接

- [Collider types and performance](https://docs.unity3d.com/2022.3/Documentation/Manual/physics-optimization-cpu-collider-types.html) - 官方性能对比文档
- [Introduction to primitive collider shapes](https://docs.unity3d.com/2022.3/Documentation/Manual/primitive-colliders-introduction.html) - Primitive Collider 说明
- [Optimize physics performance](https://docs.unity3d.com/2022.3/Documentation/Manual/physics-optimization.html) - 物理系统优化总览

---

## 射线检测（Raycast）知识与性能优化

**标签**：#unity #knowledge #physics #collider #raycast
**来源**：Unity 2022.3 官方文档 - Physics.Raycast / Optimize raycasts and other physics queries  
**来源日期**：2026-01-31  
**收录日期**：2026-02-01  
**状态**：📘 有效
**可信度**：⭐⭐⭐⭐⭐ (官方文档)

### 基本概念

`Physics.Raycast` 从指定点向指定方向发射一条射线，检测是否与场景中的 Collider 相交。

**基本用法**：
```csharp
// 简单射线检测
if (Physics.Raycast(origin, direction, out RaycastHit hit, maxDistance, layerMask))
{
    Debug.Log($"Hit: {hit.collider.name}, Distance: {hit.distance}");
}

// 使用 Ray 结构
Ray ray = Camera.main.ScreenPointToRay(Input.mousePosition);
if (Physics.Raycast(ray, out RaycastHit hit, 100f))
{
    Debug.DrawLine(ray.origin, hit.point, Color.red);
}
```

### 关键参数

| 参数 | 说明 |
|------|------|
| `origin` | 射线起点（世界坐标） |
| `direction` | 射线方向（不需要归一化，但建议归一化） |
| `maxDistance` | 最大检测距离，默认 `Mathf.Infinity` |
| `layerMask` | 层级掩码，用于选择性忽略某些 Collider |
| `queryTriggerInteraction` | 是否检测 Trigger Collider |

### 重要注意事项

1. **射线起点在 Collider 内部时不会检测到该 Collider**
2. 建议在 `FixedUpdate` 中执行射线检测（与物理系统同步）
3. 使用 `LayerMask.GetMask("LayerName")` 获取层级掩码

### 射线检测 API 对比

| API | 返回结果 | 内存分配 | 适用场景 |
|-----|---------|---------|---------|
| `Physics.Raycast` | 最近一个命中 | 无 | 只需检测是否命中或最近目标 |
| `Physics.RaycastAll` | 所有命中（数组） | ⚠️ 每次调用分配新数组 | 需要所有命中结果（不频繁调用） |
| `Physics.RaycastNonAlloc` | 所有命中（预分配数组） | ✅ 无 GC | 频繁调用需要多个结果 |
| `RaycastCommand` | 批量处理 | ✅ 使用 NativeArray | 大量射线检测（Job System） |

### 性能优化要点

#### 1. 使用 NonAlloc 版本避免 GC

```csharp
// ❌ 避免：每帧分配新数组
RaycastHit[] hits = Physics.RaycastAll(ray, 100f);

// ✅ 推荐：预分配数组复用
private RaycastHit[] _hitBuffer = new RaycastHit[10];

void FixedUpdate()
{
    int hitCount = Physics.RaycastNonAlloc(ray, _hitBuffer, 100f, layerMask);
    for (int i = 0; i < hitCount; i++)
    {
        // 处理 _hitBuffer[i]
    }
}
```

**缓冲区大小建议**：根据实际需求设置，过大浪费内存，过小会丢失结果。

#### 2. 批量射线检测（Job System）

当需要执行大量射线检测时，使用 `RaycastCommand` 配合 Job System 并行处理：

```csharp
using Unity.Collections;
using Unity.Jobs;

// 1. 创建命令数组
NativeArray<RaycastCommand> commands = new NativeArray<RaycastCommand>(rayCount, Allocator.TempJob);
NativeArray<RaycastHit> results = new NativeArray<RaycastHit>(rayCount, Allocator.TempJob);

// 2. 填充命令
for (int i = 0; i < rayCount; i++)
{
    commands[i] = new RaycastCommand(origins[i], directions[i], QueryParameters.Default, maxDistance);
}

// 3. 调度批处理
JobHandle handle = RaycastCommand.ScheduleBatch(commands, results, 1);

// 4. 等待完成
handle.Complete();

// 5. 处理结果并释放
// ...
commands.Dispose();
results.Dispose();
```

#### 3. 使用 LayerMask 减少检测范围

```csharp
// 只检测 "Enemy" 和 "Obstacle" 层
int layerMask = LayerMask.GetMask("Enemy", "Obstacle");
Physics.Raycast(ray, out hit, 100f, layerMask);

// 忽略 "Player" 层（取反）
int ignorePlayer = ~LayerMask.GetMask("Player");
```

#### 4. 限制 maxDistance

避免使用 `Mathf.Infinity`，设置合理的最大距离减少不必要的计算。

### 其他形状的射线检测

| 方法 | 说明 |
|------|------|
| `Physics.SphereCast` | 球形射线（胖射线） |
| `Physics.BoxCast` | 盒形射线 |
| `Physics.CapsuleCast` | 胶囊形射线 |
| `Physics.OverlapSphere` | 球形范围检测（无方向） |
| `Physics.OverlapBox` | 盒形范围检测 |

同样有 `NonAlloc` 和 `Command` 版本可用。

### 参考链接

- [Physics.Raycast](https://docs.unity3d.com/2022.3/Documentation/ScriptReference/Physics.Raycast.html) - 官方 API 文档
- [Physics.RaycastNonAlloc](https://docs.unity3d.com/2022.3/Documentation/ScriptReference/Physics.RaycastNonAlloc.html) - 无 GC 版本
- [Optimize raycasts and other physics queries](https://docs.unity3d.com/2022.3/Documentation/Manual/physics-optimization-raycasts-queries.html) - 官方优化指南
- [RaycastCommand](https://docs.unity3d.com/2022.3/Documentation/ScriptReference/RaycastCommand.html) - 批量射线检测

---

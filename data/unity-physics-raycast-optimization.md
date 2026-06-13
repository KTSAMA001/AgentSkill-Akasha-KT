# Unity 射线检测 Raycast 性能优化

**标签**：#unity #knowledge #physics #collider #raycast #performance
**来源**：Unity 2022.3 官方文档 - Physics.Raycast / Optimize raycasts and other physics queries
**来源日期**：2026-01-31
**收录日期**：2026-02-01
**更新日期**：2026-06-13
**状态**：📘 有效
**可信度**：⭐⭐⭐⭐⭐ (官方文档)
**适用版本**：Unity 2022.3

### 概要

Unity Raycast 性能优化重点是限制检测范围、使用 LayerMask、避免 `RaycastAll` 频繁分配，并在大量射线时考虑 `RaycastCommand` 批处理。

### 内容

`Physics.Raycast` 从指定点向指定方向发射一条射线，检测是否与场景中的 Collider 相交。

#### 基本用法

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

#### 关键参数

| 参数 | 说明 |
|------|------|
| `origin` | 射线起点（世界坐标） |
| `direction` | 射线方向（不需要归一化，但建议归一化） |
| `maxDistance` | 最大检测距离，默认 `Mathf.Infinity` |
| `layerMask` | 层级掩码，用于选择性忽略某些 Collider |
| `queryTriggerInteraction` | 是否检测 Trigger Collider |

#### 重要注意事项

1. 射线起点在 Collider 内部时不会检测到该 Collider。
2. 建议在 `FixedUpdate` 中执行射线检测（与物理系统同步）。
3. 使用 `LayerMask.GetMask("LayerName")` 获取层级掩码。

#### 射线检测 API 对比

| API | 返回结果 | 内存分配 | 适用场景 |
|-----|---------|---------|---------|
| `Physics.Raycast` | 最近一个命中 | 无 | 只需检测是否命中或最近目标 |
| `Physics.RaycastAll` | 所有命中（数组） | ⚠️ 每次调用分配新数组 | 需要所有命中结果（不频繁调用） |
| `Physics.RaycastNonAlloc` | 所有命中（预分配数组） | ✅ 无 GC | 频繁调用需要多个结果 |
| `RaycastCommand` | 批量处理 | ✅ 使用 NativeArray | 大量射线检测（Job System） |

#### 使用 NonAlloc 版本避免 GC

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

缓冲区大小应根据实际需求设置，过大浪费内存，过小会丢失结果。

#### 批量射线检测（Job System）

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

#### 使用 LayerMask 减少检测范围

```csharp
// 只检测 "Enemy" 和 "Obstacle" 层
int layerMask = LayerMask.GetMask("Enemy", "Obstacle");
Physics.Raycast(ray, out hit, 100f, layerMask);

// 忽略 "Player" 层（取反）
int ignorePlayer = ~LayerMask.GetMask("Player");
```

#### 限制 maxDistance

避免使用 `Mathf.Infinity`，设置合理的最大距离减少不必要的计算。

#### 其他形状的射线检测

| 方法 | 说明 |
|------|------|
| `Physics.SphereCast` | 球形射线（胖射线） |
| `Physics.BoxCast` | 盒形射线 |
| `Physics.CapsuleCast` | 胶囊形射线 |
| `Physics.OverlapSphere` | 球形范围检测（无方向） |
| `Physics.OverlapBox` | 盒形范围检测 |

同样有 `NonAlloc` 和 `Command` 版本可用。

### 参考链接

- [Physics.Raycast](https://docs.unity3d.com/2022.3/Documentation/ScriptReference/Physics.Raycast.html) - 官方 API 文档。
- [Physics.RaycastNonAlloc](https://docs.unity3d.com/2022.3/Documentation/ScriptReference/Physics.RaycastNonAlloc.html) - 无 GC 版本。
- [Optimize raycasts and other physics queries](https://docs.unity3d.com/2022.3/Documentation/Manual/physics-optimization-raycasts-queries.html) - 官方优化指南。
- [RaycastCommand](https://docs.unity3d.com/2022.3/Documentation/ScriptReference/RaycastCommand.html) - 批量射线检测。

### 相关记录

- [Unity 3D Collider 类型性能消耗对比](./unity-collider-types-performance.md) - Collider 类型选择对物理查询成本的影响。

### 验证记录

- [2026-04-15] 结构修复：补齐模板必填章节，未改动原结论。
- [2026-06-13] 结构维护：从旧聚合记录拆分，未重新验证原技术结论。

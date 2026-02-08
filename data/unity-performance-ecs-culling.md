# Unity 性能优化相关经验

> Unity 性能优化相关经验
> 
> 包含：内存管理、GC 优化、Draw Call、批处理、LOD、遮挡剔除、Profiler 等

---

## 草海系统 - ECS 视锥剔除优化

**收录日期**：2026-01-31
**来源日期**：2021-05-19（TaTa 仓库 Git commit 时间）
**标签**：#unity #experience #performance #ecs #culling
**状态**：⚠️ 待验证（需根据 Unity 版本和 DOTS 版本调整）
**适用版本**：Unity 2019.4+, Entities 0.7+

> 📷 **图片/视频资源**：[TaTa 仓库 GrassSystem/Img](https://github.com/KTSAMA001/TaTa/tree/master/GrassSystem/Img)

**问题/场景**：

在移动端实现草海效果，需要处理大量草实例（十万级别）。传统的相机视锥剔除不够用，CPU 提交数据成为性能瓶颈。

**目标效果**：

![草海效果](https://raw.githubusercontent.com/KTSAMA001/TaTa/master/GrassSystem/Img/Grass.jpg)

**解决方案/结论**：

使用 Unity ECS (DOTS) + Hybrid Rendering + Culling Group 实现高效的草海剔除系统。

### 草模型对比

| 模型草 | 面片草 |
|-------|-------|
| ![模型草](https://raw.githubusercontent.com/KTSAMA001/TaTa/master/GrassSystem/Img/GrassModel.png) | ![面片草](https://raw.githubusercontent.com/KTSAMA001/TaTa/master/GrassSystem/Img/GrassPlane.png) |

**结论**：移动端模型草性能优于 Alpha Test 面片草。

### 核心方案对比

| 方案 | 说明 | 优势 | 劣势 |
|------|------|------|------|
| **DrawInstance** | 手动调用 API 合批绘制 | 可充分利用 1024 实例上限 | 需手动管理数据 |
| **Hybrid Rendering** | Unity ECS 提供的批量渲染框架 | 自动处理数据管理，支持单实例剔除 | Draw Call 可能较多 |

### 关键技术点

**1. 使用 JobComponentSystem 实现多线程剔除**

```csharp
public class CullingSystem : JobComponentSystem
{  
    EntityCommandBufferSystem EntityCommandBufferSystem;

    protected override void OnCreate()
    {
        EntityCommandBufferSystem = World.GetExistingSystem<EndSimulationEntityCommandBufferSystem>();
    }

    protected override JobHandle OnUpdate(JobHandle inputDeps)
    {
        if(CullingManager.CullIndexList.Count > 0)
        {
            var EntityCommandBuffer = EntityCommandBufferSystem.CreateCommandBuffer().ToConcurrent();
            NativeArray<int> totalTileID = new NativeArray<int>(totalCount, Allocator.Persistent);
            
            var jobhandle = Entities.ForEach((Entity en, int nativeThreadIndex, ref GeneraGrassTile GrassTile) => {
                for(int i = 0; i < totalCount; i++)
                {
                    if(totalTileID[i] == GrassTile.tile_id)
                    {
                        EntityCommandBuffer.DestroyEntity(nativeThreadIndex, en);
                        return;
                    }
                }
            }).Schedule(inputDeps);
            
            EntityCommandBufferSystem.AddJobHandleForProducer(jobhandle);
            jobhandle.Complete();
            totalTileID.Dispose();
            return jobhandle;
        }
        return inputDeps;
    } 
}
```

**2. 使用 NativeArray.Copy 快速数据拷贝**

```csharp
// 比传统 for 循环快约 2ms（数千个值）
NativeArray<float3>.Copy(posList.ToArray(), 0, totalPos, startOff, InstanceCount);
```

**3. 使用 FrozenRenderSceneTag 优化 Hybrid 性能**

```csharp
EntityArchetype entityArchetype = entityManager.CreateArchetype(
    typeof(LocalToWorld),
    typeof(RenderMesh),
    typeof(RenderBounds),
    typeof(Translation),
    typeof(Rotation),
    typeof(GeneraGrassTile),
    typeof(FrozenRenderSceneTag)  // 关键！
);

entityManager.SetSharedComponentData(grassEntity, new FrozenRenderSceneTag { 
    HasStreamedLOD = 1, 
    SectionIndex = 1 
});
```

**FrozenRenderSceneTag 效果**：
- 挂载后：RenderMeshSystem 开销 < 1ms
- 不挂载：开销 8-10ms（十万实例时）

### 性能对比

**无剔除 vs 有剔除**：

| 无剔除 | 有剔除 |
|-------|-------|
| ![无剔除](https://raw.githubusercontent.com/KTSAMA001/TaTa/master/GrassSystem/Img/GrassNoCulling.png) | ![有剔除](https://raw.githubusercontent.com/KTSAMA001/TaTa/master/GrassSystem/Img/GrassMainCull.png) |
| ![无剔除性能](https://raw.githubusercontent.com/KTSAMA001/TaTa/master/GrassSystem/Img/GrassNoCulling2.png) | ![有剔除性能](https://raw.githubusercontent.com/KTSAMA001/TaTa/master/GrassSystem/Img/GrassMainCull2.png) |

**注意**：简单剔除在相机移动时可能导致 CPU 时间飙高（Entity 动态创建/删除开销）：

![剔除缺陷](https://raw.githubusercontent.com/KTSAMA001/TaTa/master/GrassSystem/Img/GrassMainCull_drawback.png)

**解决方案**：使用 JobComponentSystem 将 Entity 创建/删除从主线程剥离。

**4. 使用 Culling Group 进行 Tile 级别剔除**

```csharp
cullingGroup.SetBoundingSpheres(spheres);
cullingGroup.SetBoundingSphereCount(spheres.Length);
cullingGroup.onStateChanged += OnStateChange;

void OnStateChange(CullingGroupEvent evt)
{
    if (evt.hasBecomeInvisible)
    {
        CullIndexList.Add(evt.index);
    }
    else if (evt.hasBecomeVisible)
    {
        CreateIndexList.Add(evt.index);
    }
}
```

**参考链接**：

- [Unity DOTS 入门](https://www.lfzxb.top/unity-dots-using-ecs-create-gameplay/)
- [ECS System 执行顺序](http://dingxiaowei.cn/2020/02/09/)
- [TaTa 仓库原文](https://github.com/KTSAMA001/TaTa/tree/master/GrassSystem)

**验证记录**：

- [2021-05-19] 初次记录，来源：TaTa 仓库实践总结
- [2026-01-31] 整合到经验库，来源：外部仓库整合

**相关经验**：

- 草海系统还需配合 LOD 混合方案
- 移动端需评估 Culling Group 本身的 CPU 开销（几千个 Group 可能占用 1-2ms）

**备注**：

- 此方案基于 Unity 2019.4 和 Entities 0.7，新版本 API 可能有变化
- Mathematics 库的使用是必须的，提供硬件级性能优化
- 模型草性能优于 Alpha Test 面片草（移动端）
- 完整的草海系统还需要资源生产工具链、LOD 混合方案、玩家/场景交互

---

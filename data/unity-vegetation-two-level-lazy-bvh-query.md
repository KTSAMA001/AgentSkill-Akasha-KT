# Unity 大规模植被解析查询：Heap–Shape 两级懒建 BVH 的设计、复杂度、性能证据与正确性前提

**标签**：#unity #architecture #physics #performance
**来源**：工程实践抽象 - 分区式解析碰撞查询与扁平 BVH 索引设计
**收录日期**：2026-08-26
**更新日期**：2026-08-26
**状态**：⚠️ 待验证
**可信度**：⭐⭐⭐（索引机制、功能回归和单次 Windows Editor 微基准有直接证据；生产数据的外层 Bounds 前提尚未满足，冷建与设备端性能未验证）
**适用版本**：Unity 2022.3 LTS；静态或低频变更的 AABB 宽相位、Sphere/Capsule/Box 解析查询

---

### 概要

当一个 QueryWorld 已经按 Heap 分区、每个 Heap 又包含多个解析碰撞 Shape 时，可以用两级混合 BVH 取代大集合的全量线性宽相位：顶层先筛 Heap，候选 Heap 内再筛 Shape，小集合继续线性扫描；树只在第一次真正需要时构建，增删使顶层索引失效，Floating Origin 则平移已有 Bounds 和节点而不改变拓扑。游戏逻辑显式向 QueryWorld 发起查询；兴趣源只驱动 ColliderStreamer，不参与 BVH 的候选生成或可见性判断。

这套设计的价值不是把所有查询宣布为 `O(log n)`，而是让高频、局部、稀疏查询在良好分布和预热后避开大部分候选。其正确性有一个不可妥协的前提：**外层 Query Heap Bounds 必须完整包含该 Heap 的全部 Query Shape Bounds**。参考实现当前复用了不含碰撞体的视觉 Bounds，因此可能产生确定性假阴性；修复该包含关系并建立门禁之前，不应把它直接作为生产查询方案。

### 内容

#### 一、问题模型

设一个运行时 Cell 独立拥有一份解析查询世界：

- Cell 中有 `H` 个 Heap；
- 第 `i` 个 Heap 有 `S_i` 个 Sphere、Capsule 或 Box；
- 每个 Heap 和 Shape 都有世界空间 AABB；
- 每个 Shape 带 Purpose 位掩码，用于区分交互、武器命中等查询用途；
- `StableGuid` 表示实例在所属场景资产内的稳定身份，供结果去重和确定性收尾使用；
- BVH 只负责产生候选，真正命中仍由解析窄相位决定。

玩法调用 Raycast、Overlap 或 Sweep 时，先选择要查询的运行时 Cell，再把查询几何、Purpose Mask 和距离等条件交给该 Cell 的 QueryWorld。Collider Proxy 是否激活不会改变解析查询可见的数据；需要 PhysX 接触语义时才进入独立的 Collider 流送路径。

若每次查询都枚举所有 Heap，再枚举候选 Heap 的全部 Shape，宽相位成本会随常驻数据规模增长。直接为所有集合立即建树也不理想：小集合可能被建树和遍历固定成本反超，冷建会制造首次查询延迟，频繁变更又会使索引维护成本高于收益。

因此采用混合政策：

```text
Count < 64   → 线性扫描
Count >= 64  → 第一次查询时构建扁平 BVH，此后复用
```

`64` 是参考实现的保守切换点，不是通用最优值；叶容量 `8` 同样是实现参数，不是经过完整参数扫描得到的常数。

#### 二、两级索引的数据结构

顶层和第二层复用同一种扁平 BVH：

```text
运行时 Cell
  └─ Heap Index
       ├─ Heap AABB
       ├─ Heap Purpose OR
       └─ 候选 Heap
            └─ Shape Index
                 ├─ Shape AABB
                 ├─ Shape Purpose
                 └─ 候选 Shape → 解析窄相位
```

每个节点保存：

- 子树所有元素的合并 AABB；
- 子树 Purpose 掩码的按位 OR；
- 在稳定元素数组中的连续区间 `Start + Count`；
- 左右子节点索引；叶节点以无子节点标记。

元素本身不复制进节点。构建先生成稳定的有序索引数组，叶节点引用其中的连续区间；查询用可复用数组栈迭代遍历，避免递归调用和稳态逐查询栈分配。

Purpose OR 是空间之外的第二种剪枝：当节点的用途集合与查询掩码没有交集时，整棵子树都可以跳过。Bounds 查询若完整包含一个节点 AABB，则无需继续访问子节点，只需遍历该节点的连续区间并做 Purpose 过滤。

#### 三、Heap 与 Shape BVH 如何生成

##### 3.1 注册阶段

注册一个 Heap 时先完成以下工作：

1. 保存稳定 Heap 身份、外层 Query Heap Bounds 和 Shape 数组。
2. 一次性计算并缓存每个 Shape 的世界 AABB 与 Purpose Mask。
3. 汇总 Heap 的 Purpose OR。
4. 创建 Shape 索引容器，但不立即构建 Shape 树。
5. 使当前运行时 Cell 的顶层 Heap 索引失效。

Shape AABB 缓存在注册阶段形成，因此单个 Heap 的注册时间与空间为 `O(S_i)`。这一步并不等于建树：少于 64 个 Shape 时会始终线性；大集合也要等该 Heap 第一次成为查询候选才构建 Shape BVH。

除统一的 Floating Origin 刚性平移外，Shape 的位置、尺寸、类型或 Purpose 发生变化时不能原地改写已缓存记录。调用方必须把它作为 Heap 替换：重新校验并生成该 Heap 的 Shape 缓存与懒建 Shape 索引，同时使顶层 Heap 索引失效。移除 Heap 时，其 Shape 缓存与派生索引一并释放。

##### 3.2 顶层 Heap 索引

当运行时 Cell 的 Heap 数达到阈值，第一次查询会：

1. 把 Heap 注册表复制为连续数组；
2. 先按稳定 Heap 身份排序，消除字典枚举顺序对树和命中顺序的影响；
3. 提取 Heap AABB 与 Purpose OR；
4. 为这组元素构建扁平 BVH。

新增、替换或移除 Heap 时，Heap 注册表仍是事实源，顶层派生索引被丢弃；下一次大集合查询根据更新后的注册表重新排序并建树。替换某个 Heap 会同时生成新的 Shape 缓存和新的懒建 Shape 索引，其它 Heap 已有的 Shape 树不必随顶层失效一起重建。

##### 3.3 单棵树的构建

单棵树采用确定性中位数切分：

```text
输入连续区间
  → 合并元素 AABB 与 Purpose OR
  → Count <= 8：形成叶节点
  → 否则计算元素中心的包围盒
  → 选择中心分布最长轴
  → 对当前子区间按该轴中心排序
  → 中心并列时按原始稳定序号收尾
  → 以中位数分成左右子区间
  → 递归构建，最终保存为扁平节点数组
```

因为每个内部节点都会重新排序自己的子区间，构建上界是 `O(n log² n)`，不能按常见的一次预排序 BVH 写成 `O(n log n)`。构建时先创建容量约为 `2n` 的节点列表，再复制为精确数组；这会产生尚未量化的冷查询临时内存峰值。

##### 3.4 生命周期

```text
注册 Heap 并缓存 Shape AABB
  → 首次大查询懒建顶层 Heap 树
  → 候选 Heap 首次含大 Shape 集合时懒建 Shape 树
  → 稳态查询复用节点、索引和遍历栈
  → Heap 增删/替换使顶层失效
  → 下次大查询重建顶层
  → Rebase 平移 Heap、Shape、缓存 AABB 和已建节点
  → Cell 卸载释放整份查询世界
```

#### 四、查询如何穿过两级索引

##### Raycast

1. 顶层以射线、最大距离和 Purpose Mask 筛选 Heap AABB。
2. 对每个候选 Heap，以同一条件筛选 Shape AABB。
3. 对候选 Sphere、Capsule 或 OBB 执行解析射线命中。
4. 以距离和稳定身份等规则选择最终命中。

##### OverlapCapsule

1. 先构造胶囊的包围 AABB。
2. 顶层 BVH 产生候选 Heap，并用线段到 Heap AABB 的距离补充粗筛。
3. Shape BVH 产生候选 Shape。
4. 解析接触测试后按 StableGuid 去重并排序。

Overlap 的宽相位之外还包含最终结果排序；若返回 `R` 个结果，这一部分为 `O(R log R)`。

##### SweepCapsule

1. 对姿态不变的线性平移，合并起点胶囊与终点胶囊的 AABB，形成扫掠宽相位范围；若扫掠过程允许旋转，必须另行构造覆盖中间姿态的保守 Bounds。
2. 依次经过 Heap 和 Shape 索引。
3. 对每个候选执行保守推进，参考实现最多迭代 64 次。
4. 以命中比例、稳定身份等规则选择结果。

BVH 不改变 Sphere/Capsule/OBB 窄相位算法，也不支持 ConvexMesh。需要 PhysX 接触、触发器或 ConvexMesh 的对象仍应走真实 Collider 工作集。

#### 五、复杂度与内存模型

设 `S=ΣS_i` 为全部 Heap 的 Shape 总数，`K_H` 为候选 Heap 数，`K_i` 为第 `i` 个候选 Heap 的 Shape 候选数，`K_S=ΣK_i`。混合索引必须分别写出线性与 BVH 分支，不能只给树路径：

- Shape 缓存注册：每 Heap `O(S_i)`。
- 顶层稳定 Heap 排序：`O(H log H)`。
- 单棵树构建：`O(n log² n)`；常驻节点、索引和遍历栈为 `O(n)`。
- 顶层 Heap 宽相位：

```text
H < 64   → O(H)
H >= 64  → 良好分布、已预热、局部稀疏时 O(log H + K_H)
```

- 对每个候选 Heap `i` 的 Shape 宽相位：

```text
S_i < 64   → O(S_i)
S_i >= 64  → 良好分布、已预热、局部稀疏时 O(log S_i + K_i)
```

- 总查询成本由顶层分支、各候选 Heap 的 Shape 分支和解析窄相位相加：

```text
topLevel(H, K_H) + Σ shapeLevel(S_i, K_i) + narrow(K_S)
```

- 全覆盖、大范围、高重叠、同中心或巨型 AABB、长 Ray/Sweep 的最坏宽相位仍是 `O(H + S)`。
- Overlap 另有 `O(R log R)` 结果排序。
- Sweep 对每个候选最多执行 64 次保守推进。
- Rebase 需要平移 Heap、Shape、缓存 AABB 和已建节点，总体为 `O(H + S)`，不是 `O(1)`。

候选 List、去重 HashSet 和遍历栈会复用并保留历史最大容量。稳态零托管分配只说明已预热的特定路径不会继续扩容，不能推出冷建、重建、多命中或极端查询也零分配。

#### 六、多运行时 Cell 如何运转

每个运行时 Cell 的 QueryWorld 拥有独立的 Heap 注册表、顶层索引、Shape 索引和复用容器。游戏逻辑可以把同一查询显式发送给多个活动 Cell，但它们不会共享一棵世界级 BVH。兴趣源只驱动 ColliderStreamer 的 Proxy 工作集，不驱动 QueryWorld，也不改变 BVH 的候选集合。

这种隔离带来三个结果：

1. 加载、失效、Rebase 和卸载只影响所属 Cell，错误不会直接污染其它 Cell 的索引。
2. 单 Cell 的稀疏查询收益不能自动消除遍历多个 Cell 的调度成本、内存和冷建总量。
3. 若玩法需要“查询整个世界”，外层仍需维护 Active Cell 集合并逐 Cell 发起查询，或另建世界级索引；后者会引入跨 Scene 生命周期和并发所有权问题。

因此不能把单 Cell、单层 AABB 微基准推广为多 Cell 整世界性能。真实评估至少要记录活动 Cell 数、每 Cell Heap/Shape 分布、每帧查询数、命中率、查询范围和冷/热比例。

#### 七、Floating Origin 与索引同步

刚性平移不改变空间邻接和 BVH 拓扑。Rebase 可以把 `-delta` 同步应用到：

- Heap 权威 Bounds；
- Shape 权威记录；
- Shape 缓存 AABB；
- 已构建的 Heap 与 Shape BVH 节点 Bounds。

未构建的树只需平移缓存元素，之后会基于新坐标构建。已构建的树同时平移元素与节点，避免重建。

这个局部能力不等于完整系统已经原子接通 Floating Origin。生产接入仍需用同一世代协调渲染的累计绝对偏移、解析查询的本次 delta 和 PhysX 代理平移；任一子系统漏转发都会造成视觉、查询和碰撞世界分离。

#### 八、正确性前提与已知风险

##### 8.1 外层 Bounds 必须保守包含

两级剪枝正确的必要条件是：

```text
QueryBounds ⊇ actual query path or volume
QueryShapeBounds ⊇ actual Shape
QueryHeapBounds ⊇ union(all QueryShapeBounds in the Heap)
```

三层包含关系必须同时成立：查询自身的宽相位范围要覆盖完整查询轨迹或体积，每个 Shape AABB 要覆盖真实 Shape，外层 Heap Bounds 再覆盖所属全部 Shape AABB。任一层偏小都会在进入解析窄相位前造成假阴性。

参考实现的场景编译器使用 Prototype 的视觉 Bounds 聚合 Heap Bounds，并明确排除碰撞体，以免碰撞外伸扩大渲染激活范围；物理运行时随后把这份视觉 Bounds 直接注册为 Query Heap Bounds。于是视觉几何之外的合法 Shape 可以在顶层被拒绝，形成确定性假阴性。

可选修复有两种：

1. 为渲染和查询分别保存 `VisualHeapBounds` 与 `QueryHeapBounds`；后者聚合全部解析 Shape。
2. 注册查询世界时现场聚合所有 Shape Bounds，完全忽略视觉粗筛 Bounds。

无论选择哪种，都必须建立外伸 Sphere/Capsule/Box 回归，并验证线性与 BVH 两条阈值路径。不要把碰撞 Bounds 合并回渲染 Bounds 后再让同一范围同时承担渲染激活，否则会为了查询正确性扩大渲染工作集。

##### 8.2 Shape 级结果稳定性

同一实例的多个 Shape 共享 StableGuid。Overlap 按 StableGuid 去重时会保留先命中的 Shape；线性和 BVH 的候选顺序不同，跨过阈值后可能改变 ShapeType、接触点或法线，即使实例集合相同。Ray/Sweep 在身份、Heap 和距离完全并列时也需要 Shape 级稳定收尾。若玩法消费接触细节，应引入 ShapeId 或显式优先级，而不是只验证实例身份。

##### 8.3 输入、容差与并发

- 注册、Heap 替换、公共查询与 Rebase 都应拒绝 NaN/Infinity，防止非有限坐标、尺寸、距离或 delta 污染 Bounds、树节点和排序。
- AABB 粗筛容差要与窄相位擦边容差一致，避免在粗筛阶段丢掉临界接触。
- 极大坐标、零距离、重复 Rebase、长射线和高重叠需要专项回归。
- 索引按单运行时线程串行查询与修改设计；查询期间不能并发注册或移除 Heap。

#### 九、实验方法、结果与证据边界

本节沉淀两类证据：功能夹具用于检查索引更新后是否仍命中同一目标；性能夹具只比较单层 AABB 宽相位在理想稀疏条件下是否避开全量扫描。两者都不是完整植被物理系统或目标设备基准。

##### 9.1 功能夹具与稳态分配

在 65 个 Heap、每 Heap 64 个 Sphere 的合成世界中，Raycast、单命中 OverlapCapsule 与 SweepCapsule 能命中唯一目标；Heap 替换、移除和顶层索引平移后仍能保持目标同步；完全并列的不同实例以稳定身份收尾。

同一规模下，预热 16 次后连续执行 256 次单目标 Overlap，当前 Windows Editor 线程记录的托管分配增量为 `0 B`。该结果不覆盖冷建、重建、多命中容器扩容、Ray/Sweep、多个运行时 Cell 或 Quest。

##### 9.2 单层 AABB 性能微基准

当前可复核的单次微基准条件为：

| 项目 | 条件 |
|---|---|
| 数据 | 4096 个边长为 1 的 AABB，沿 X 轴每 4 米排列 |
| 查询 | 只命中一个元素的稀疏 AABB 查询 |
| 冷建树 | 先用一次全覆盖查询完成，不计时 |
| 热身 | BVH 与简化线性扫描各 32 次 |
| 测量 | 固定顺序先 BVH 后线性，各连续 2048 次 |
| 单次聚合结果 | BVH `25,223` ticks；线性 `1,391,980` ticks；线性/BVH = `55.1869` |

精确结果 `55.1869×` 只描述该夹具的一次聚合观测。线性对照只做 AABB 相交计数，不是完整 QueryWorld；测量也不包含两级 Heap→Shape 路径、解析窄相位、首次建树、增删重建或跨 Cell 调度。数据分布是一维、等间距、低重叠，查询只命中一个元素，明显有利于树索引。

实验没有记录 CPU 型号、Stopwatch 频率、独立重复、方差、P50/P95/P99 或随机交错顺序；执行地点是 Windows Unity Editor，不是 Android Player、Quest、ARM 或 IL2CPP。长期门禁只应要求索引路径不劣于等价线性扫描，不能把某个固定倍率设成性能合同。

因此唯一可推广的结论是：**在已预热、局部稀疏且分布理想的合成 AABB 夹具中，树索引显著避开了全量扫描。**

#### 十、适用与不适用条件

适用：

- 静态或低频替换的解析 Sphere、Capsule 与 Box；
- 大量 Heap，或单 Heap 内有大量 Shape；
- 高频、局部、稀疏查询足以摊销冷建；
- 可以预热热点区域；
- 每个运行时 Cell 单线程拥有索引；
- 已验证 Query Heap Bounds 包含全部 Shape。

收益不确定或不适用：

- 少于 64 项的小集合；
- 每帧大量移动、增删或重建；
- 大范围 Overlap、长 Ray、长 Sweep、严重重叠或巨型 Bounds；
- 首次查询延迟不可接受且无法预热；
- ConvexMesh 或必须获得 PhysX 接触语义的玩法；
- 需要并发查询与修改；
- 试图直接推出多 Cell 整世界或 Quest 性能结论。

#### 十一、采用检查清单

- [ ] 查询范围、Shape AABB 与外层 Query Heap Bounds 是否逐层保守包含真实查询轨迹、真实 Shape 和全部所属 Shape？
- [ ] 线性与 BVH 两条阈值路径是否返回相同实例集合与稳定的 Shape 级结果？
- [ ] 阈值和叶容量是否根据目标数据分布做过交叉实验，而不是照抄 64/8？
- [ ] 是否分别测量冷建、增删重建、预热稳态和最坏重叠？
- [ ] 是否记录活动 Cell 数、Heap/Shape 分布、查询范围、命中率和每帧查询数？
- [ ] 是否在目标 Player、CPU 架构和 XR 运行时上采集 P50/P95/P99，而不只看单次 Editor ticks？
- [ ] Rebase 是否以同一世代同步渲染、解析查询和 PhysX 代理？
- [ ] 注册、替换、查询和 Rebase 是否都拒绝非有限输入，并覆盖擦边、极大坐标、长射线和重复 Rebase？
- [ ] 是否接受查询与修改的单线程所有权，或另行实现并验证并发协议？

### 相关记录

- [多运行时 Cell 物理查询与 Collider 流送](./unity-vegetation-multi-cell-physics-streaming.md) - QueryWorld、真实 Collider 工作集、多 Cell 预算和卸载生命周期。
- [统一 BRG 架构](./unity-vegetation-unified-brg-architecture.md) - 运行时 Cell、Heap、兴趣范围与全系统资源所有权。

### 验证记录

- [2026-08-26] 合成夹具表明两级索引能在预热、理想稀疏 AABB 查询中避开大部分全量扫描，并覆盖 Heap 替换、移除与 Rebase 同步；Query Heap Bounds 包含性、冷建、退化分布、多 Cell 和 Quest 性能仍未验证。

---

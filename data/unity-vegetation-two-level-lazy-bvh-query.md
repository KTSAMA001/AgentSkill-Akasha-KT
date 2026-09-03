# Unity 大规模植被解析查询：分组（Heap）–解析碰撞形状（Shape）两级懒建包围体层次结构（BVH）的设计、复杂度、性能证据与正确性前提

**标签**：#unity #architecture #physics #performance
**来源**：工程实践抽象 - 分区式解析碰撞查询与扁平 BVH 索引设计
**收录日期**：2026-08-26
**更新日期**：2026-09-03
**状态**：✅ 已验证
**可信度**：⭐⭐⭐（本文“✅ 已验证”仅指两级懒建 BVH 宽相位、稳定排序、失效重建、Rebase 平移、现有 Sphere 合成世界中的 Raycast/OverlapCapsule/SweepCapsule 夹具、预热后单目标 Overlap 零托管分配，以及一次 Windows Editor 单层 AABB 微基准；它不表示 Capsule/Box 窄相位全组合、生产 QueryWorld 集成、冷建与退化负载、多 Cell 整世界或 Quest 已通过。）
**适用版本**：Unity 2022.3 LTS；静态或低频变更的轴对齐包围盒（Axis-Aligned Bounding Box，AABB）宽相位，以及 Sphere、Capsule、Box 解析查询

---

### 阅读约定：核心术语

- **Heap**：本文特指 QueryWorld 中注册的一组查询数据，是本系统的逻辑分组，不是程序内存中的“堆”。一个 Heap 拥有一个外层查询 Bounds，并包含若干 Shape。
- **Shape**：用于解析查询的碰撞几何元素；本文支持 Sphere（球）、Capsule（胶囊）和 Box（盒）。
- **运行时 Cell**：可独立加载、卸载和 Rebase 的运行时空间分区。每个运行时 Cell 独立拥有一份 QueryWorld。
- **QueryWorld**：所属运行时 Cell 的解析查询数据与入口；它保存 Heap、Shape 和派生索引并接收玩法查询，不等同于 Unity PhysX 世界，也不依赖 Collider Proxy 是否激活。
- **解析查询**：直接用 Sphere、Capsule、Box 的数学表示计算 Raycast、Overlap 或 Sweep，不先创建 Unity Collider GameObject。它负责可重复的玩法命中判断，但不会产生 PhysX 接触或触发器事件。
- **宽相位与窄相位**：宽相位用便宜的包围盒测试排除明显不可能命中的元素，允许保留多余候选；窄相位再对候选执行具体几何求交。宽相位若漏掉真实候选，就会造成后续无法修复的假阴性。
- **AABB**：边与世界坐标轴对齐的保守包围盒。AABB 和 BVH 在本文中只负责宽相位候选筛选；最终是否命中仍由精确的解析窄相位判断。
- **BVH**：把元素包围盒按层次组织起来的空间索引；查询可以通过节点的合并 AABB 跳过整批不相交元素。本文的 BVH 最终保存为扁平节点数组。
- **OBB（Oriented Bounding Box）**：允许旋转的有向盒；本文中的 Box 窄相位按 OBB 处理，其宽相位仍使用能够完整包含它的 AABB。
- **Purpose / Purpose Mask**：Shape 的用途分类位及查询需要的用途位集合，例如交互或武器命中；节点保存子树全部用途的按位 OR，用于整棵子树剪枝。
- **StableGuid**：一株实例在所属 SceneAsset 内的稳定身份；当前编译器和编辑事务会拒绝同一 SceneAsset 内跨 Heap 的空值或重复值。它不保证跨运行时 Cell 全局唯一。
- **Floating Origin**：为控制大世界坐标精度而周期性移动世界原点的机制。**Rebase** 指其中一次坐标重定位操作；本文约定把同一个 `-delta` 同步应用到 Heap、Shape、缓存 AABB 和已构建节点。它不表示完整渲染、查询和 PhysX 协调已经接通。

### 概要

当一个 QueryWorld 已经按 Heap 分区、每个 Heap 又包含多个解析碰撞 Shape 时，可以用两级混合 BVH 取代大集合的全量线性宽相位：顶层先筛 Heap，候选 Heap 内再筛 Shape，小集合继续线性扫描；树只在第一次真正需要时构建，增删使顶层索引失效，Floating Origin 则平移已有 Bounds 和节点而不改变拓扑。游戏逻辑显式向 QueryWorld 发起查询；兴趣源只驱动 ColliderStreamer，不参与 BVH 的候选生成或可见性判断。

这套设计的价值不是把所有查询宣布为 `O(log n)`，而是让高频、局部、稀疏查询在良好分布和预热后避开大部分候选。其正确性有一个不可妥协的前提：**外层 Query Heap Bounds 必须完整包含该 Heap 的全部 Query Shape Bounds**。参考实现当前复用了不含碰撞体的视觉 Bounds，因此可能产生确定性假阴性；修复该包含关系并建立门禁之前，不应把它直接作为生产查询方案。

本文所称“已验证”只覆盖两级 BVH 宽相位及第九节列出的现有合成夹具。现有功能夹具的目标 Shape 均为 Sphere，因此不能据此宣称 Capsule 或 Box 窄相位的全部组合已经验证；它也不表示生产集成、退化负载、多 Cell 整世界或 Quest 性能已经通过。

### 内容

#### 一、问题模型

设一个运行时 Cell 独立拥有一份解析查询世界：

- Cell 中有 `H` 个 Heap；
- 第 `i` 个 Heap 有 `S_i` 个 Sphere、Capsule 或 Box；
- 每个 Heap 和 Shape 都有世界空间 AABB；
- 每个 Shape 带 Purpose 位掩码，用于区分交互、武器命中等查询用途；
- `StableGuid` 在一个 SceneAsset 的全部 Heap 范围内唯一，编译器与编辑事务会拒绝该范围内的空值或重复值。每个 VegetationCellPhysicsRuntime 从自身管理器的一份 SceneAsset 创建一个 QueryWorld，因此该 QueryWorld 内可以按 StableGuid 去重；跨运行时 Cell 汇总时不能假定它全局唯一，调用方必须同时携带运行时 Cell 身份；
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

Shape AABB 缓存在注册阶段形成，因此单个 Heap 的注册时间与空间为 `O(S_i)`。当前实现的 `TreeThreshold = 64`、`LeafSize = 8`：少于 64 个 Shape 时会始终线性；大集合也要等该 Heap 第一次成为查询候选才构建 Shape BVH。顶层 Heap 集合同样在小于阈值时线性扫描，达到阈值后才于首次查询惰性建树。

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

##### 3.5 构建失败与回退

注册表、Shape 记录和缓存 AABB 是权威数据；Heap BVH 与 Shape BVH 都只是可丢弃的派生索引。生产接入时，首次懒建和失效后重建应先在局部临时容器中完成全部排序、节点生成与有限值检查，只有完整成功后才能一次性发布新索引，不能让查询看到半棵树。

若有效输入上的构建因分配、排序或其它运行时异常失败，应丢弃本次临时索引，并对当前权威数据回退到等价线性宽相位：顶层构建失败时线性枚举当前 Heap，某个 Shape BVH 构建失败时只线性枚举该 Heap 的 Shape。注册表已经变化后不得继续使用旧树，因为旧树对应的是上一数据世代。为避免每次查询重复触发同一冷建尖峰，失败世代应保持在线性模式，直到注册表世代再次变化、显式预热或外层明确请求重试。

NaN、Infinity 或不合法尺寸属于输入错误，应按第 8.3 节拒绝对应注册、替换、查询或 Rebase，不能把受污染数据交给线性回退继续运行。上述内容是生产接入建议；现有验证记录没有绑定构建异常注入与回退路径，因此不属于页首已验证范围。

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
4. 解析接触测试后，在当前单 Cell QueryWorld 内按 StableGuid 去重并排序。若玩法把多个 Cell 的结果汇总，必须由外层使用 `(RuntimeCellIdentity, StableGuid)` 作为实例键；当前 `VegetationQueryHit` 不携带 Cell 身份，调用方须在逐 Cell 发起查询时一并保存来源 Cell。

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

同一实例的多个 Shape 共享 StableGuid。在当前单 Cell QueryWorld 内，Overlap 可以按 StableGuid 去重；跨运行时 Cell 汇总时必须按 `(RuntimeCellIdentity, StableGuid)` 去重和排序，不能只比较 StableGuid。这里的 `RuntimeCellIdentity` 是调用方为本次运行时 Cell 分配并保证唯一的身份，不宣称源码已有同名字段；如果同一 SceneAsset 被实例化为多个运行时 Cell，它们也必须使用不同的 RuntimeCellIdentity。

去重会保留先命中的 Shape；线性和 BVH 的候选顺序不同，跨过阈值后可能改变 ShapeType、接触点或法线，即使实例集合相同。Ray/Sweep 在实例键、Heap 和距离完全并列时也需要 Shape 级稳定收尾。若玩法消费接触细节，应引入 ShapeId 或显式优先级；ShapeId 用于区分同一实例内的 Shape，不能替代跨 Cell 实例键。

##### 8.3 输入、容差与并发

- 注册、Heap 替换、公共查询与 Rebase 都应拒绝 NaN/Infinity，防止非有限坐标、尺寸、距离或 delta 污染 Bounds、树节点和排序。
- AABB 粗筛容差要与窄相位擦边容差一致，避免在粗筛阶段丢掉临界接触。
- 极大坐标、零距离、重复 Rebase、长射线和高重叠需要专项回归。
- 索引按单运行时线程串行查询与修改设计；查询期间不能并发注册或移除 Heap。

#### 九、实验方法、结果与证据边界

本节沉淀两类证据：功能夹具用于检查索引更新后是否仍命中同一目标；性能夹具只比较单层 AABB 宽相位在理想稀疏条件下是否避开全量扫描。两者都不是完整植被物理系统或目标设备基准。

##### 9.1 功能夹具与稳态分配

在 65 个 Heap、每 Heap 64 个 Sphere 的合成世界中，Raycast、单命中 OverlapCapsule 与 SweepCapsule 能命中唯一目标；Heap 替换、移除和顶层索引平移后仍能保持目标同步；完全并列的不同实例以稳定身份收尾。该夹具用于验证 Heap/Shape 宽相位索引、三种公共查询入口及索引生命周期；由于目标 Shape 全部是 Sphere，它不构成 Capsule 或 Box 窄相位全组合的直接证据。本文也没有为该夹具提供随机输入下与逐 Shape 线性 oracle 的完整结果对照，相关要求仍保留在工程采用前提中。

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
| 单次聚合结果 | BVH `25,223` ticks；线性 `1,391,980` ticks；本次聚合线性/BVH 约为 `55.2` |

约 `55.2×` 只描述该夹具的一次固定顺序聚合观测。线性对照只做 AABB 相交计数，不是完整 QueryWorld；测量也不包含两级 Heap→Shape 路径、解析窄相位、首次建树、增删重建或跨 Cell 调度。数据分布是一维、等间距、低重叠，查询只命中一个元素，明显有利于树索引。

本实验没有记录 CPU 型号、Stopwatch 频率、独立重复、方差、随机交错顺序，也没有保存逐次的完整 QueryWorld 端到端耗时样本，因此不能从现有聚合 ticks 推导 P50/P95/P99。执行地点是 Windows Unity Editor，不是 Android Player、Quest、ARM 或 IL2CPP。长期门禁只应要求索引路径不劣于等价线性扫描，不能把某个固定倍率设成性能合同。

本文后续所称 **P50/P95/P99**，统一指某一种公共 QueryWorld 查询（Raycast、OverlapCapsule 或 SweepCapsule）从接收输入到生成最终结果的单次端到端耗时样本分布中，第 50、95 和 99 百分位，单位为 `μs/次`；三种查询必须分别统计。每组结果必须声明一个固定负载的测量窗口，并报告该窗口覆盖的连续帧数 `F` 与有效查询次数 `N`，不能只写百分位而不写窗口和样本量。

冷态与热态必须分开：冷态样本是每次重新创建查询世界、首次懒建或失效后重建所触发的首个查询，应通过多个独立冷启动或重建循环采集；热态样本要求相关树已构建、复用容器容量稳定，且窗口内不发生注册、替换、移除或重建。不得把两类样本混入同一百分位。若另行评估“一帧内全部查询的总成本”，应作为独立统计对象以 `ms/帧` 报告，不能与 `μs/次` 混用。本文不预设 `F`、`N` 或通过阈值；具体项目必须随验收结果一并声明。

因此，现有性能证据唯一支持的结论是：**在已预热、局部稀疏且分布理想的这一次合成 AABB 夹具中，观察到树路径使用的聚合 ticks 少于简化线性扫描。** 该结果不表示已经建立统计显著性，也不能推导固定倍率或目标设备收益。

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

#### 十一、工程采用前提

以下项目需要采用方在自己的目标项目、数据分布和设备环境中取得直接证据。`[ ]` 只表示本文没有绑定该目标环境的通过证据，不是当前项目进度，也不表示该项已经执行并失败。

- [ ] 查询范围、Shape AABB 与外层 Query Heap Bounds 是否逐层保守包含真实查询轨迹、真实 Shape 和全部所属 Shape？
- [ ] 线性与 BVH 两条阈值路径是否返回相同实例集合与稳定的 Shape 级结果？
- [ ] 阈值和叶容量是否根据目标数据分布做过交叉实验，而不是照抄 64/8？
- [ ] 是否分别测量冷建、增删重建、预热稳态和最坏重叠？
- [ ] 是否记录活动 Cell 数、Heap/Shape 分布、查询范围、命中率和每帧查询数？
- [ ] 是否在目标 Player、CPU 架构和 XR 运行时上，按第 9.2 节口径分别采集冷态和热态的 QueryWorld 单次端到端耗时 P50/P95/P99（`μs/次`），并报告每个窗口的连续帧数和有效查询次数？如另测每帧总查询成本，是否以 `ms/帧` 独立报告？
- [ ] Rebase 是否以同一世代同步渲染、解析查询和 PhysX 代理？
- [ ] 注册、替换、查询和 Rebase 是否都拒绝非有限输入，并覆盖擦边、极大坐标、长射线和重复 Rebase？
- [ ] 是否接受查询与修改的单线程所有权，或另行实现并验证并发协议？

### 结论

两级懒建 BVH 适合静态或低频替换、预热后高频且局部稀疏的解析查询；它优化的是 Heap 与 Shape 的宽相位候选生成，不改变解析窄相位，也不消除最坏线性退化。现有合成夹具支持索引构建、失效、平移和特定预热路径，但没有证明 Capsule/Box 窄相位全组合、构建失败回退或目标设备性能。

生产采用前必须先保证 Query Heap Bounds 完整包含全部 Query Shape Bounds，再以等价线性结果为 oracle，分别验证目标 Shape、冷建、重建、退化分布、多 Cell 调度和设备端冷/热查询成本。

### 相关记录

- [多运行时 Cell 物理查询与 Collider 流送](./unity-vegetation-multi-cell-physics-streaming.md) - QueryWorld、真实 Collider 工作集、多 Cell 预算和卸载生命周期。
- [统一 BRG 架构](./unity-vegetation-unified-brg-architecture.md) - 运行时 Cell、Heap、兴趣范围与全系统资源所有权。

### 验证记录

- [2026-08-26] Windows Editor 合成夹具覆盖 Heap/Shape 两级惰性索引、Heap 替换与移除后的失效重建、HeapGuid 稳定排序、Rebase 同步，以及预热后单目标 Overlap 路径 `0 B` 托管分配。现有功能夹具的目标 Shape 均为 Sphere；4,096 个稀疏 AABB 的单次 Editor 微基准只表明该次树路径聚合 ticks 少于简化线性扫描，不构成生产性能合同。
- [2026-09-02] 源码复核确认参考实现仍使用 `TreeThreshold = 64`、`LeafSize = 8`：小集合线性扫描，大集合在首次查询时建树。该复核只确认算法选择和参数，不证明这些阈值适合其它数据分布，也不替代第九节未覆盖的集成、退化负载与目标设备验证。
- **未验证边界**：集成层仍把主要来自视觉范围的 `heap.WorldBoundsAtBake` 注册为 Query Heap Bounds，尚未保证包含全部 Query Shape；因此算法夹具通过不等于完整查询链可生产采用。Capsule/Box 窄相位全组合、构建异常回退、冷建、退化分布、多 Cell 世界级负载和 Quest 性能仍未验证。

---

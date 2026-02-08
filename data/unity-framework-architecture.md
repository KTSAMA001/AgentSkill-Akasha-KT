# Unity 中的 C# 脚本编程相关经验

> Unity 中的 C# 脚本编程相关经验
> 
> 包含：MonoBehaviour 生命周期、协程、事件系统、ScriptableObject、序列化等

---

---

## KT_Core 框架架构设计经验总结

**日期**：2026-01-28  
**标签**：#unity #csharp #experience #architecture
**问题/场景**：

审查 ProjectKT 项目的 KT_Core 框架，总结其架构设计模式和最佳实践。

**解决方案/结论**：

### 1. Entity + Feature 组合模式

**核心设计**：
- **Entity** 作为纯容器，只持有 ID、Tags、Faction 等元数据
- **Feature** 作为功能单元，每个负责单一职责（移动、血量、仇恨等）
- Entity 在 Awake 时自动扫描并缓存所有子物体上的 IFeature

**优势**：
- 完全解耦：移动逻辑不需要知道攻击逻辑的存在
- 灵活组合：木箱可以有 HealthFeature 但没有 MovementFeature
- 层级无关：Feature 可挂载在 Entity 或其子节点上

### 2. 状态驱动 vs 阻塞式设计

**问题**：行为树节点如果阻塞等待移动完成，会导致决策无法及时更新

**解决方案**：Feature 内部维护状态机，外部只设置模式立即返回
- MovementFeature 使用 MovementMode 枚举（Idle, Patrol, MoveTo, Follow）
- 行为树调用 StartPatrol() 后立即返回，Feature 在 Update 中持续执行

### 3. NodeCanvas 行为树集成最佳实践

**BTDataCache 缓存机制**：
- 使用 Dictionary 缓存 Transform 到 Entity 映射
- 避免每帧 GetComponentInParent 查找
- 定期清理无效缓存条目

**统一节点设计**：
- 使用枚举参数控制行为变体（如 MovementAction）
- 配合 ShowIf 特性动态显示/隐藏相关参数
- 避免节点爆炸（几十个 MoveTo、Patrol、Flee 节点）

### 4. 仇恨系统设计

**ThreatFeature 职责划分**：
- 仇恨值记录与计算
- 目标排序与选择（切换阈值防抖）
- 战斗状态管理（Enter/Exit Combat 事件）

**策略模式分离检测逻辑**：
- IThreatStrategy 接口定义检测策略
- RangeDetectionStrategy 等具体实现
- Feature 只负责响应检测结果，不关心如何检测

### 5. 技能系统设计

**ScriptableObject 数据驱动**：
- Skill 作为 SO 定义技能数据（冷却、范围、效果列表）
- SkillEffect 作为可序列化效果基类（使用 SerializeReference）
- SkillFeature 管理技能运行时状态

**运行时数据分离**：
- SkillRuntimeData 记录 lastUseTime、冷却计算等
- 与 Skill SO 分离，支持同一技能多实例使用

### 6. 对象池服务化

**静态服务入口 + 可替换实现**：
- PoolService 作为静态入口
- IPoolService 接口支持不同实现
- 无服务时降级为 Instantiate/Destroy

**备注**：

- 2D 游戏使用 A* Pathfinding 时，AIPath 的 Orientation 必须设为 YAxisForward
- Feature 访问 Owner 其他 Feature 时使用 GetFeature<T>()，自动处理缓存
- 使用 Odin Inspector 的 SerializeReference 实现策略模式的序列化
- Entity 标签使用 Flags 枚举支持多选（如同时 Attackable + Boss）


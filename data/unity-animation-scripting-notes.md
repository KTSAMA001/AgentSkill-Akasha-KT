# Unity 动画与脚本开发核心知识清单

**标签**：#unity #animation #csharp #performance #knowledge #root-motion
**来源**：实践总结
**收录日期**：2026-02-09
**更新日期**：2026-02-09
**状态**：✅已验证
**可信度**：⭐⭐⭐⭐
**适用版本**：Unity 2021+

### 概要

一份适合做技术笔记的关联知识点清单，涵盖 Unity 开发中的动画核心机制、API 特性、脚本控制方案以及数学基础。已按核心机制、API特性、替代方案分类整理。

### 内容

#### 1. 核心机制：Root Motion（根运动）
*   **定义**：动画驱动游戏对象的实际位移（`Transform`），而非仅改变骨骼位置（Visual Only）。
*   **关键开关**：Animator 组件下的 `Apply Root Motion`。
*   **脚本控制**：`OnAnimatorMove()` 回调函数。
    *   如果脚本中定义了此函数，Unity 会放弃自动应用根运动。
    *   需开发者手动处理 `animator.deltaPosition` 和 `animator.deltaRotation`。
*   **应用场景**：高精度移动（如攀爬、跑酷、精确攻击），防止滑步（Foot Sliding）。

#### 2. API 深度解析：Animator 状态重置
**Animator.Rebind()**
*   **作用**：强制重置 Animator 到初始状态（Bind Pose/T-Pose），清除所有参数、状态机历史和混合权重。
*   **性能**：**高开销 (Expensive)**。涉及重新分配和计算所有骨骼数据，切勿在 Update 中高频调用。
*   **替代方案**：如果只是想重新播动画，用 `animator.Play(stateName, layer, 0f)` 重置到第 0 帧通常更轻量。

**Play() vs CrossFade()**
*   **Play**：硬切，瞬间跳转，无过渡。
*   **CrossFade**：混合，有过渡时间，平滑切换。

#### 3. 定时与执行：Invoke 与 协程
**Invoke(string methodName, float time)**
*   **原理**：基于反射（Reflection）查找函数名。
*   **缺点**：字符串硬编码（易错，虽可用 `nameof` 缓解）、无法传递参数、受 `Time.timeScale` 影响、对象销毁后可能报错。

**Coroutine (协程)**
*   **代码**：`yield return new WaitForSeconds(time)`。
*   **优势**：更灵活、类型安全、可中断 (`StopCoroutine`)、支持复杂逻辑等待（如等待帧结束 `WaitForEndOfFrame`）。

**Async/Await (UniTask)**
*   **建议**：现代 Unity 开发的更优解，避免协程产生的垃圾回收（GC Alloc），尤其推荐使用 `Cysharp/UniTask` 库。

#### 4. 动画系统架构（发散思考）
**Animation Events（动画事件）**
*   **特点**：比 Invoke 更精准。
*   **用法**：直接在 Animation Clip 的特定帧打点触发函数。
*   **场景**：脚落地时播放音效，动画结束时触发重置、伤害判定框激活。

**Animator State Machine Behaviour**
*   **位置**：挂载在 Animator 状态节点上的脚本（继承 `StateMachineBehaviour`）。
*   **接口**：`OnStateEnter` / `OnStateExit` / `OnStateUpdate`。
*   **优势**：比在 MonoBehaviour 里写计时器更符合“状态驱动”的逻辑，能精准捕捉动画结束时刻。

**Timeline**
*   **定位**：非代码流的动画编排工具。
*   **场景**：适合做过场动画（Cutscenes）、复杂的位移测试、多轨道序列管理，可视化强。

#### 5. 性能优化点
**String Hash**
*   **原理**：`Play("Name")` 内部会进行字符串哈希计算。
*   **优化**：预先缓存 `Animator.StringToHash("Name")` 为 `int`，后续使用 `int` 调用，减少每帧 GC 和 CPU 消耗。

**Culling Mode**
*   **API**：`Animator.cullingMode`。
*   **作用**：决定当角色在屏幕外时是否还计算动画。
*   **建议**：演示代码通常不需要管，但实际项目中为了性能应设为 `CullUpdateTransforms` (仅更新位移) 或 `CullCompletely` (完全停止)。

#### 6. 数学基础
**Transform Reset**
*   **位置重置**：区分 `transform.position` (世界坐标) 与 `transform.localPosition` (父节点相对坐标)。
*   **旋转重置**：使用 `Quaternion.identity` (无旋转) 或恢复保存的 `_defaultRotation`。

### 关键代码

```csharp
// 性能优化：缓存 Hash
private static readonly int AttackStateHash = Animator.StringToHash("Attack");

// 脚本控制 Root Motion 示例
private void OnAnimatorMove()
{
    // 获取动画原本的位移增量
    Vector3 delta = animator.deltaPosition;
    
    // 手动应用（甚至可以修改它，比如放大位移）
    transform.position += delta;
    transform.rotation *= animator.deltaRotation;
}
```

### 验证记录

- [2026-02-09] 初次记录，内容基于用户提供的 Unity 开发经验总结。

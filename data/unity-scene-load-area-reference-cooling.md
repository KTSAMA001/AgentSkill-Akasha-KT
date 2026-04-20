# Unity 区域触发场景加载 — SceneReference 三态状态机 + 卸载冷却

**标签**：#unity #csharp #scene #performance #troubleshooting #experience
**来源**：实践总结
**收录日期**：2026-04-20
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐
**适用版本**：Unity 6+ / UniTask 2.x / Built-in & URP 通用

### 概要

按玩家所在区域（`SceneLoadArea`）按需加载/卸载子场景的引用计数模式中，"边界抖动 / 邻接区域共享同场景路径 / 区域禁用残留计数 / 关卡切换 CTS 孤儿"四类问题用纯计数解决不掉。引入 **NotLoaded / Active / Cooling 三态状态机 + 卸载冷却 CTS** 后，抖动期与邻接切换期对底层零下发，关卡切换由 `ForceUnload` 统一兜底。配套把光照探针重建从"只在 Load 后触发"改为"Load/Unload 任一变更后防抖触发"。

### 内容

#### 1. 调用链定位

```
SceneLoadArea.Update（每帧 isInside 判定）
    └ LoadScenes() / UnloadScenes()                （内部 _isLoaded 幂等守卫）
        └ SceneReference.AddRef / RemoveRef        （三态状态机，本记录核心）
            └ DynamicSceneManager.LoadScene/UnloadScene
                └ SceneSubSceneLoader 单队列
                    ├ DelayFrame(1) 同帧合并
                    ├ OptimizeOperationList         同帧抵消 + 去重
                    ├ ProcessAllOperationsSequentially  顺序 await IO
                    └ ScheduleLightProbeRebuildIfNeeded 防抖重建
```

`SceneReference` 是按 **scenePath 全局唯一** 的引用计数器，所有 `SceneLoadArea` 共享。

#### 2. 三态状态机

| 状态 | 含义 |
|---|---|
| `NotLoaded` | 内存中无该场景，refCount = 0 |
| `Active`    | 场景已加载，refCount ≥ 1 |
| `Cooling`   | 场景仍在内存，refCount = 0，**挂起 CTS 计时中** |

状态转移：

| 当前 | 事件 | 目标 | 副作用 |
|---|---|---|---|
| NotLoaded | AddRef | Active   | 下发 `LoadScene`，++count |
| Active    | AddRef | Active   | 仅 ++count，**零底层操作** |
| Cooling   | AddRef | Active   | **取消 CTS** + ++count，**零底层操作**（救援路径） |
| Active    | RemoveRef → 0 | Cooling  | 启动 CTS 等待 `_unloadDelaySeconds`（默认 2.5s） |
| Cooling   | 到期复检 refCount==0 | NotLoaded | 下发 `UnloadScene` |
| 任意      | ForceUnload | NotLoaded | 取消 CTS + 必要时 Unload + 清零 |

#### 3. 解决问题矩阵

| # | 问题 | 旧实现现象 | 三态方案 |
|---|---|---|---|
| P1 | 边界抖动 0↔1 跨帧 | 同帧抵消失效 → 真实 IO 抖动 | Cooling 期 AddRef 直接救援，跨秒级抖动也零下发 |
| P2 | 邻接 Area 共享同 path（A 出 B 进通常跨帧） | Unload→Load 真实执行 | 同上 |
| P3 | 玩家在区内 Area 被 SetActive(false)，Update 停 | refCount 永不归零 | 恢复 `OnDisable → UnloadScenes()` 主动回收，冷却兜底短禁用不真卸 |
| P4 | 探针重建只在 Load 后触发 | 纯 Unload 批次（含冷却到期）漏重建 | `_hasSceneChangeInSession` Load/Unload 都标脏 |
| P5 | 守卫 `_loadedScenes.Count > 0` | 卸到空永不重建，残留旧探针网格 | 去掉 Count 判定 |
| P6 | `ForceCleanupAllScenes` 不处理挂起 CTS | 加冷却后留孤儿 | `ForceUnload` 内 `CancelPendingUnload + Unload + 置 NotLoaded` |

#### 4. 不变量与契约

- **`IsLoaded` 在 Cooling 期间仍为 true**（场景在内存）。这点对外部代码很重要——卸载冷却对 IsLoaded 透明。
- `ReferenceCount` 公开属性外部读取保持不变。
- `OnDestroy` 故意保持注释 — 关卡切换批量销毁顺序不可控，统一由 `ForceCleanupAllScenes()` 主动清理。
- 冷却期 `RemoveRef` 不允许重启冷却（`if (refCount == 0 && _state == Active)` 守卫），避免覆盖前一个 CTS 形成孤儿。

#### 5. 行为预期（验证场景）

| 场景 | 预期 |
|---|---|
| 边界 200 次/秒抖动 | 实际 Load/Unload 下发 ≤ 2 |
| 相邻 Area 同 path 交替 50 次 | `LoadScene/UnloadScene` 零调用 |
| 进入 → 离开 → 站外 ≥ 2.5s | `冷却到期卸载`，1s 后探针重建 |
| 进入 → 离开 → 1s 内回来 | `取消冷却`，底层零操作 |
| 站内 SetActive(false) | refCount-1，必要时进 Cooling |
| `ForceCleanupAllScenes` 在冷却期 | CTS 取消 + Unload 同步下发，无 OperationCanceledException |

### 关键代码

```csharp
public class SceneReference
{
    private enum SceneRefState { NotLoaded, Active, Cooling }

    private SceneRefState _state = SceneRefState.NotLoaded;
    private CancellationTokenSource _pendingUnloadCts;
    private static float _unloadDelaySeconds = 2.5f;

    public bool IsLoaded => _state != SceneRefState.NotLoaded;  // 含 Cooling

    public void AddReference()
    {
        ReferenceCount++;
        switch (_state)
        {
            case SceneRefState.NotLoaded:
                DynamicSceneManager.LoadScene(ScenePath);
                _state = SceneRefState.Active;
                break;
            case SceneRefState.Active:    /* 仅计数 */          break;
            case SceneRefState.Cooling:   CancelPendingUnload(); break;  // 救援
        }
    }

    public void RemoveReference()
    {
        if (ReferenceCount <= 0) return;
        ReferenceCount--;
        // 注意：仅 Active 才能进入冷却；Cooling 期再 RemoveRef 不允许重启，避免孤儿 CTS
        if (ReferenceCount == 0 && _state == SceneRefState.Active)
            StartCooldown();
    }

    private void StartCooldown()
    {
        if (_pendingUnloadCts != null)
        {
            try { _pendingUnloadCts.Cancel(); } catch { }
            _pendingUnloadCts.Dispose();
        }
        _pendingUnloadCts = new CancellationTokenSource();
        _state = SceneRefState.Cooling;
        RunCooldownAsync(_pendingUnloadCts.Token).Forget();
    }

    private async UniTaskVoid RunCooldownAsync(CancellationToken token)
    {
        try { await UniTask.Delay(TimeSpan.FromSeconds(_unloadDelaySeconds), cancellationToken: token); }
        catch (OperationCanceledException) { return; }

        // 三连复检：任一不通过即放弃
        if (token.IsCancellationRequested) return;
        if (_state != SceneRefState.Cooling) return;
        if (ReferenceCount != 0) return;

        DynamicSceneManager.UnloadScene(ScenePath);
        _state = SceneRefState.NotLoaded;
        _pendingUnloadCts.Dispose();
        _pendingUnloadCts = null;
    }

    public void ForceUnload()
    {
        CancelPendingUnload();
        if (_state != SceneRefState.NotLoaded)
        {
            DynamicSceneManager.UnloadScene(ScenePath);
            _state = SceneRefState.NotLoaded;
        }
        ReferenceCount = 0;
    }
}
```

光照探针卸载也重建（`SceneSubSceneLoader`）：

```csharp
private static bool _rebuildProbesOnUnload = true;
private static bool _hasSceneChangeInSession;   // Load 或 Unload 任一变更都置 true

// 卸载分支末尾追加
if (_rebuildProbesOnUnload) _hasSceneChangeInSession = true;

// 防抖窗口 1000ms（与冷却节奏对齐，吸收同阶段多 Area 触发为一次重建）
// 守卫去掉 _loadedScenes.Count > 0 — 卸到空也允许重建
```

### 设计要点提炼（可复用到其它引用计数场景）

1. **"在内存但 refCount=0" 必须是显式状态**，不能用 `Loaded && Count==0` 隐式表达——隐式表达无法承载"挂起的取消令牌"这种额外语义。
2. **冷却期 AddRef = 救援，不是新加载**：救援路径必须零底层操作，才能消解抖动与邻接共享。
3. **冷却期 RemoveRef 不允许重启冷却**：守卫 `_state == Active` 才启动冷却，避免覆盖前一个 CTS 形成孤儿。
4. **CTS 必须 Dispose**：高频抖动场景如不 Dispose，每次冷却的 CTS 累积会持续吃 GC。
5. **到期前再做一次三连复检**：cancel/state/count 任一不符立即放弃下发，兜底竞态。
6. **关卡级清理走专门的 ForceUnload 分支**，统一处理 CTS + 真实卸载 + 计数清零，不依赖组件销毁顺序。

### 参考链接

- [UniTask GitHub](https://github.com/Cysharp/UniTask) - CTS + Delay + Forget 模式
- [Unity LightProbeGroup.Tetrahedralize/TetrahedralizeAsync 文档](https://docs.unity3d.com/ScriptReference/LightProbes.TetrahedralizeAsync.html)

### 相关记录

- [unity-render-settings-soft-transition.md](./unity-render-settings-soft-transition.md) - 配套的环境（fog/ambient/skybox）软过渡系统，由 SceneLoadArea 在加载完成时驱动
- [scene-asset-loading.md](./scene-asset-loading.md) - 场景资源加载基础概念

### 验证记录

- [2026-04-20] 初次记录，来源：VR 项目实战沉淀

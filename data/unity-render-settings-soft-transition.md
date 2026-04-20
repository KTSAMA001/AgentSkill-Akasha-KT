# Unity RenderSettings 软过渡 — 通道注册式 + 单 CTS 接力 + Fog 等效无雾平滑

**标签**：#unity #csharp #rendering #skybox #experience
**来源**：实践总结
**收录日期**：2026-04-20
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐
**适用版本**：Unity 6+ / UniTask 2.x / Built-in 通用，URP/HDRP 移植仅替换 channel 实现

### 概要

把 `RenderSettings` 的 fog / ambient / skybox 切换从硬切升级为可被打断、可接力、可扩展的软过渡（lerp）。核心设计：**通道注册式（IEnvironmentChannel）+ 单一 CTS 互斥 + 每次 Capture 取实时值起点 + SmoothStep 缓动**。Fog 开关切换通过"等效无雾参数（远距离 / 0 密度）"策略实现 on↔off 全平滑。Skybox 当前在过渡中点（k≥0.5）硬切并 `DynamicGI.UpdateEnvironment`，未来可整体替换为 ShaderSkyboxChannel 不影响其它代码。

### 内容

#### 1. 架构

```
调用方（如 SceneLoadArea）
    ↓ Apply(in EnvironmentSnapshot, float? duration)
EnvironmentTransitionManager（静态调度器）
    ├ List<IEnvironmentChannel> channels
    ├ 单一 CTS + UniTask RunAsync 循环
    └ Init / Reset / Cancel / SnapToTarget / Dump
        ↓ Capture → SetTarget → Tick(k) → Snap
内置通道：
    FogChannel          RenderSettings.fog* 全套（lerp + 等效无雾平滑）
    AmbientChannel      RenderSettings.ambientLight（Color.Lerp）
    SkyboxSwapChannel   RenderSettings.skybox 中点硬切（不 lerp）
未来扩展：
    ShaderSkyboxChannel  blend shader 真正 lerp
    ExposureChannel      后处理曝光 lerp
```

#### 2. IEnvironmentChannel 调用顺序契约

由 Manager 保证：

| # | 时机 | 方法 | 用途 |
|---|---|---|---|
| 1 | 注册时一次 | `Init()` | 缓存原始值，作为无 override 时的回退目标 |
| 2 | 每次 Apply 起始 | `Capture()` | 从当前实时 RenderSettings 取起点（**关键：保证打断时平滑接力**） |
| 3 | 每次 Apply 起始 | `SetTarget(in t)` | 设定终点 |
| 4 | 过渡循环每帧 | `Tick(k)` | k∈[0,1] 缓动后插值 |
| 5 | 过渡正常完成 | `Snap()` | 对齐终点，避免累积误差 |
| 6 | 外部强制复位 | `Reset()` | 回 Init 缓存的原始值 |

#### 3. 关键设计

**3.1 单 CTS 互斥**：每次 `Apply` 都先 `CancelInternal()` 取消旧循环再启新循环。同一时刻最多一个 RunAsync 在跑；旧循环通过 `OperationCanceledException` 立刻退出，**不复位状态**——保留中间值给下一次 `Capture` 接力。

**3.2 finally 标志清理的竞态**：旧循环进入 `finally` 时新循环已把 `_running = true`，无条件 `_running = false` 会破坏新循环状态。修复：`if (!ct.IsCancellationRequested) _running = false`。被取消的旧循环不动 `_running`。

**3.3 起点取实时值**：每次 `Capture` 都从 `RenderSettings.*` 读取。A→B 切到一半时再切 B→C，C 的起点正是当前画面状态，肉眼无跳变。

**3.4 SmoothStep 缓动**：`k = Mathf.SmoothStep(0, 1, t)`，缓入缓出，无需额外 AnimationCurve 资源。

**3.5 FogChannel — fog 开关平滑过渡（核心创新）**

雾效开关切换若直接改 `RenderSettings.fog` 会瞬变。本通道策略：

- **过渡期全程 `RenderSettings.fog = true`**，避免开关引起瞬变。
- "无雾"状态由参数模拟：
  - Linear：`fogStart = fogEnd = NoFogDistance(100000)` → 距离上不可见
  - Exp / ExpSquared：`fogDensity = 0`
- `Capture` 检测当前 `fog=false` 时，把 `_from*` 替换为等效无雾参数。
- `SetTarget` 检测目标 `fog=false` 时，把 `_to*` 替换为等效无雾参数；起点无雾时还需 `_fromColor = _toColor` 避免颜色闪一下。
- `Snap()` 才真正按目标设置 `RenderSettings.fog`（此时画面已无可见雾，开关无视觉差异）。

效果：**fog on↔off 全部 4 种组合（off→off, off→on, on→off, on→on）都平滑**。

**3.6 FogChannel — 多 FogMode**

项目约定整个项目使用同一种 FogMode，但通道实现不限制：4 个数值参数（color/start/end/density）任何模式都做 lerp；`fogMode` 不可 lerp，`SetTarget` 时直接切换（同模式无可见差异）。

**3.7 SkyboxSwapChannel — 中点硬切**

`Tick(k)` 在 `k >= 0.5` 时切换 `RenderSettings.skybox` 并调 `DynamicGI.UpdateEnvironment()`。此时 fog/ambient lerp 已到中间值，能"遮一遮"瞬变，观感最不突兀。

#### 4. EnvironmentSnapshot 字段（值类型，零 GC）

| 字段 | 类型 |
|---|---|
| `FogOverride` | bool |
| `FogColor` | Color |
| `FogMode` | FogMode |
| `FogStart / FogEnd / FogDensity` | float |
| `AmbientOverride` | bool |
| `AmbientColor` | Color |
| `SkyboxOverride` | bool |
| `SkyboxMaterial` | Material |

调用方 `BuildSnapshot()` 配 `_cachedSnapshot + _snapshotDirty + OnValidate` 缓存，避免每次 Apply 重填字段。

### 关键代码

**Manager 主循环**：

```csharp
private static async UniTaskVoid RunAsync(float duration, CancellationToken ct)
{
    _running = true; _currentDuration = duration; _currentElapsed = 0f;
    try
    {
        if (duration <= 0f) { for (int i = 0; i < _channels.Count; i++) _channels[i].Snap(); return; }

        while (_currentElapsed < duration)
        {
            if (ct.IsCancellationRequested) return;
            _currentElapsed += Time.deltaTime;
            float t = Mathf.Clamp01(_currentElapsed / duration);
            float k = Mathf.SmoothStep(0f, 1f, t);
            for (int i = 0; i < _channels.Count; i++) _channels[i].Tick(k);
            await UniTask.NextFrame(ct);
        }
        if (!ct.IsCancellationRequested)
            for (int i = 0; i < _channels.Count; i++) _channels[i].Snap();
    }
    catch (OperationCanceledException) { /* 取消时不复位，保留中间值供下一次 Capture 接力 */ }
    finally
    {
        // 仅本次未被取消时才清标志，避免取消的旧循环误清新循环已置 true 的 _running
        if (!ct.IsCancellationRequested) _running = false;
    }
}
```

**FogChannel 等效无雾平滑**：

```csharp
private const float NoFogDistance = 100000f;

public void Capture()
{
    _fromEnable = RenderSettings.fog;
    _fromColor  = RenderSettings.fogColor;
    if (_fromEnable)
    {
        _fromStart   = RenderSettings.fogStartDistance;
        _fromEnd     = RenderSettings.fogEndDistance;
        _fromDensity = RenderSettings.fogDensity;
    }
    else
    {
        // 当前无雾：用等效无雾作为起点
        _fromStart = NoFogDistance; _fromEnd = NoFogDistance; _fromDensity = 0f;
    }
}

public void SetTarget(in EnvironmentSnapshot t)
{
    if (t.FogOverride)
    {
        _toEnable = true;
        _toColor = t.FogColor; _toMode = t.FogMode;
        _toStart = t.FogStart; _toEnd = t.FogEnd; _toDensity = t.FogDensity;
    }
    else { /* 回退到 _orig* */ }

    if (!_toEnable)
    {
        _toStart = NoFogDistance; _toEnd = NoFogDistance; _toDensity = 0f;
        _toColor = _fromColor;  // 颜色不变，仅靠距离/密度消雾
    }
    if (!_fromEnable) _fromColor = _toColor;  // 起点无雾：颜色对齐目标，避免闪色

    RenderSettings.fogMode = _toMode;
    RenderSettings.fog = true;  // 过渡期统一开启
}

public void Snap()
{
    RenderSettings.fog = _toEnable;  // 此时画面已无可见雾，开关无视觉差异
    // ... 写入最终 mode/color/start/end/density
}
```

**SkyboxSwapChannel 中点切换**：

```csharp
public void Tick(float k)
{
    if (_shouldSwap && !_swapped && k >= 0.5f)
    {
        RenderSettings.skybox = _to;
        DynamicGI.UpdateEnvironment();
        _swapped = true;
    }
}
```

### 设计要点提炼（可复用到其它"实时状态属性 lerp"场景）

1. **Capture/SetTarget 分离 + Capture 取实时值**：是打断接力平滑性的根本，不能用首次起点缓存。
2. **单 CTS 互斥** + **取消时不复位**：保证不会有两个循环同时写同一组 RenderSettings；中间值用于下次 Capture。
3. **finally 写共享标志要看 ct**：取消的旧循环 finally 不能动新循环已经置位的全局标志。
4. **不可插值的二值切换 → 用"等效不可见参数"实现连续过渡**：FogChannel 的 NoFogDistance/density=0 是这一思路的具体应用，可推广到 reflection probe / shadow distance 等开关式属性。
5. **不能 lerp 的资源切换 → 选最不显眼的时机**：SkyboxSwapChannel 选 k≥0.5 中点，让其它正在 lerp 的通道遮蔽瞬变。
6. **快照值类型 + 调用方缓存 + OnValidate 标脏**：Apply 路径零 GC，且 Inspector 修改即时生效。
7. **通道注册式扩展**：新加 ExposureChannel / ShaderSkyboxChannel 只需实现接口 + Register，不动调用方与其它通道。

### 参考链接

- [Unity RenderSettings 文档](https://docs.unity3d.com/ScriptReference/RenderSettings.html)
- [Unity DynamicGI.UpdateEnvironment](https://docs.unity3d.com/ScriptReference/DynamicGI.UpdateEnvironment.html)
- [UniTask GitHub](https://github.com/Cysharp/UniTask)

### 相关记录

- [unity-scene-load-area-reference-cooling.md](./unity-scene-load-area-reference-cooling.md) - 上游驱动方：SceneLoadArea 在加载/卸载完成时调用 `Apply` / `Reset`
- [urp-skybox-notes.md](./urp-skybox-notes.md) - URP Skybox 相关注意事项

### 验证记录

- [2026-04-20] 初次记录，来源：VR 项目实战沉淀

# Unity 材质参数动画代理桥接模式经验

**标签**：#unity #shader #material #animation #srp-batcher #effect-system #experience
**来源**：Unity 实践总结 + Unity 官方文档
**收录日期**：2026-05-29
**来源日期**：2026-05-29
**更新日期**：2026-05-29
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐（匿名实践验证 + Unity 官方资料交叉确认）
**适用版本**：Unity 2022.3 / SRP Batcher / 材质参数动画

### 概要

直接让 `AnimationClip` 录制材质参数会进入 per-renderer 属性覆写语义，工程上可按 `MaterialPropertyBlock (MPB)` 路线理解；`MPB` 不兼容 `SRP Batcher`，大量对象时会造成批次膨胀。代理字段桥接模式的核心收益，是让动画录制落到普通代理组件字段，再由脚本写实例材质，从而保住 `SRP Batcher` 路径。

### 内容

#### 模式存在理由

在需要批量播放材质视觉状态的场景里，最直接的做法是让 `AnimationClip` 录制 Renderer 或 Material 上的 shader property。但这条路的实际问题在于：动画系统会按 Renderer 产生属性覆写，而不是把变化写回共享材质本身。对工程设计来说，这可以直接理解为 `MaterialPropertyBlock` 语义的 per-renderer 覆写路径。

Unity 官方文档明确说明：使用 `MaterialPropertyBlock` 的对象不兼容 `SRP Batcher`。当对象数量、子 Renderer 数量和动画材质参数数量同时上升时，这条路径会把原本可以稳定批处理的渲染提交打散，表现为批次数量膨胀和整体帧率下降。

代理字段桥接模式就是为了避开这条路径：

1. `AnimationClip` 只录普通代理组件字段。
2. `Animator` 继续负责状态切换、采样、融合和过渡。
3. 桥接层在 `LateUpdate` 读取代理输出，并写入实例材质。

这个模式的主要收益不是“脚本写材质天然更快”，而是用可控的脚本成本换回稳定的 `SRP Batcher` 路径。

#### 核心问题与次级问题

核心问题只有一个：解决“直接录制材质参数会走 MPB 语义路径，导致 `SRP Batcher` 失效”。

次级问题包括：

- 录制目标从材质参数转成代理字段，动画绑定更稳定。
- 材质写入回到脚本可控路径，便于缓存、去重和 Profiler 观测。
- 像 UV 偏移速度积分这类运行时语义，可以放在代理层表达，而不是强行录最终材质值。

因此该模式应被理解为“材质参数动画的桥接模式”，而不是旧式一体化材质动画控制器的状态机重写。

#### 推荐结构

一个清晰的桥接结构通常分成三层：

1. **代理字段层**：普通 `MonoBehaviour` 字段承载可录制值，例如 float、color、vector 或 UV 偏移速度。
2. **动画采样层**：`Animator` 和 `AnimationClip` 只负责采样代理字段，不直接动画材质参数。
3. **材质写入层**：桥接脚本把代理输出写入实例材质，并负责缓存、去重、校验和性能标记。

这样做的关键是：动画绑定路径仍然是真实组件字段，材质写入路径则完全由脚本控制。不要为了 Inspector 展示方便，把可录制字段做成只存在于根对象上的镜像字段，否则容易出现“界面可改但动画实际没录到代理字段”的假绑定。

#### 材质实例缓存主线

桥接层应优先写实例材质，而不是写共享材质或 `MPB`。常规主线可以是：

1. 初始化或重绑时，通过 `Renderer.materials` 建立该 Renderer 的实例材质语义。
2. 按 Renderer 分组刷新槽位，避免同一个 Renderer 的多个材质槽重复访问 `renderer.materials`。
3. 高频路径只读取缓存的实例材质引用，再执行必要的 `Material.SetFloat / SetColor / SetVector`。
4. 外部如果直接替换材质引用，需要显式标脏或重绑；桥接层不应每帧扫描所有材质引用来猜测外部变化。

这里的取舍是明确的：`renderer.materials` 的数组分配和实例化成本只放在初始化、重绑、脏刷新等低频路径；热路径只做缓存读取和必要写入。

#### 写入去重

即使写实例材质，`Material.SetX` 仍然是需要控制的热路径成本。一个简单有效的优化是按 route 缓存上次实际写入值：

- 当前值与上次写入值相同：跳过 `SetX`。
- 当前值发生变化：执行 `SetX` 并刷新缓存。
- 浮点、颜色、向量都使用小阈值比较，避免浮点误差造成无意义写入。

这种优化不需要引入“静态参数 / 动态参数”配置，也不需要把 Inspector 复杂化；统一比较数值即可。

#### UV 偏移参数语义

UV 偏移类参数更适合代理字段模式。`AnimationClip` 可以录制偏移速度，而不是直接录制最终 ST 向量；运行时桥接层再按 `deltaTime` 积分：

- X/Y 表示平铺。
- Z/W 表示偏移。
- 代理字段记录偏移速度。
- 桥接层每帧把速度积分到 Z/W，再写完整 ST 向量。

这样可以避免 shader 中 `_Time * speed` 因速度变化影响历史累计时间而产生跳变，也能让播放状态、暂停、重置和循环策略更容易控制。

#### 匿名编辑器实验摘要

一次匿名 Unity 2022.3 Editor PlayMode 对照实验显示，该模式的收益主要来自 `SRP Batcher` 路径稳定，而不是脚本 CPU 自身显著更低。实验边界如下：

- 这是 Editor PlayMode 下的多轮重复测试，不是 Player 构建结果，也不是真机结果。
- 测试规模为百级对象量级，每个对象包含多个子 Renderer，并带有多个代理参数。
- 对照组直接录制材质参数。
- 实验组录制代理字段，再由桥接层写实例材质。
- 多轮观察中，对照组约 60 FPS，桥接组约 100 FPS。
- 桥接组的 SRP 批次数维持在低个位数，脚本桥接成本仍处于亚毫秒级。

这组数据只能证明两条路线在该类规模下的相对趋势，不能替代 Player 或真机验证。更稳妥的结论是：代理字段桥接模式用一笔可控脚本成本，换回了更稳定的渲染批处理路径。

#### 设计边界

代理字段桥接模式不应该承担所有职责：

- 不负责替代 `Animator` 的状态机。
- 不负责每帧自动探测所有外部材质引用替换。
- 不直接写共享材质资产。
- 不把可识别工程上下文写进通用设计文档。

它应该专注于：代理输出读取、实例材质缓存、必要写入、配置校验和性能观测。

### 关键代码

```csharp
// 动画录代理字段；桥接层读取代理输出后，才写入实例材质。
var value = proxy.GetValue();
if (HasValueChanged(route, value))
{
    material.SetVector(route.ShaderPropertyId, value.VectorValue);
    CacheLastAppliedValue(route, value);
}
```

```csharp
// 初始化或脏刷新阶段按 Renderer 分组取实例材质，避免热路径反复访问 renderer.materials。
Material[] materials = renderer.materials;
slot.RuntimeMaterial = materials[slot.MaterialIndex];
slot.Dirty = false;
```

```hlsl
// SRP Batcher 兼容方向：脚本写入的材质参数放入 UnityPerMaterial。
CBUFFER_START(UnityPerMaterial)
    float4 _MainTex_Tiling_Offset;
    float _Dissolve;
    float4 _MainColor;
CBUFFER_END
```

### 参考链接

- [Unity Manual - SRP Batcher](https://docs.unity3d.com/2022.3/Documentation/Manual/SRPBatcher.html) - `SRP Batcher` 兼容条件，包含 `MaterialPropertyBlock` 约束。
- [Unity Scripting API - MaterialPropertyBlock](https://docs.unity3d.com/2022.3/Documentation/ScriptReference/MaterialPropertyBlock.html) - 官方说明 `MPB` 不兼容 `SRP Batcher`。
- [Unity Scripting API - Renderer.materials](https://docs.unity3d.com/2022.3/Documentation/ScriptReference/Renderer-materials.html) - `Renderer.materials` 的实例化材质语义。
- [Unity Issue Tracker - Different phenomenon when SetPropertyBlock is called with and without a materialIndex parameter](https://issuetracker.unity3d.com/issues/different-phenomenon-when-setpropertyblock-is-called-with-and-without-a-materialindex-parameter) - 官方说明动画材质属性写入会落到 per-renderer 属性表；工程设计中可按 MPB 语义理解。

### 相关记录

- [Unity 材质参数动画控制器设计经验](./unity-material-parameter-animation-controller.md) - 旧式一体化控制器路线的曲线采样、CrossFade 和生命周期经验。
- [Unity 渲染相关知识](./unity-material-renderer.md) - `Renderer.materials` 实例化行为与运行时材质替换风险。
- [CBUFFER 与 SRP Batcher 合批机制](./cbuffer-srp-batcher-mechanism.md) - `UnityPerMaterial` 与 `SRP Batcher` 兼容背景。
- [SRP Batcher 参数开销分析](./srp-batcher-parameter-overhead.md) - 材质参数写入与批处理开销背景。

### 验证记录

- [2026-05-29] 初次记录：基于匿名 Unity 2022.3 Editor PlayMode 对照实验、Unity 官方 SRP Batcher / MPB / Renderer.materials 文档，以及 Unity Issue Tracker 中的动画材质属性覆写说明整理。记录已泛化为通用技术结论。


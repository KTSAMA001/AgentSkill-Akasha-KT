# Unity 材质参数动画控制器设计经验

**标签**：#unity #shader #material #animation #srp-batcher #effect-system #experience
**来源**：Unity 项目实践总结 + Unity 官方文档
**收录日期**：2026-05-25
**来源日期**：2026-05-22
**更新日期**：2026-05-25
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐（项目实践 + 官方文档交叉验证）
**适用版本**：Unity 2022.3 / 自定义材质参数动画控制器

### 概要

Unity 材质参数动画控制器应以“脚本驱动材质实例参数 + 曲线按秒采样 + 固定时间追赶式 CrossFade”为主线。需要持续滚动的 Vector 参数不要把速度直接乘到 shader 绝对时间上，而应由脚本把曲线值视为每秒速度源，按真实 `deltaTime` 积分后写入材质参数。

### 内容

#### 适用场景

该经验适用于运行时按曲线驱动 Shader Property 的效果系统，例如溶解、发光、颜色渐变、UV Offset 滚动和可被 Play / Stop 打断的特效表现。控制器可以对外提供统一播放接口，例如 `Play()`、`Stop()`、`Pause()`、`PlayImmediate()` 和 `StopImmediate()`。

#### 核心设计结论

1. 材质参数动画的曲线横轴按秒解释，而不是默认按 0-1 归一化进度解释。
2. 淡入或淡出阶段的实际时长取该阶段所有相关曲线和 Color 渐变时长的最大值；没有曲线就不应强行制造 1 秒阶段。
3. Color 参数由 Gradient 和亮度曲线共同决定，Gradient 需要独立淡入 / 淡出持续时间，否则只有 Gradient 没有亮度曲线时无法稳定决定阶段时长。
4. 普通 Vector 按通道写绝对值；持续叠加 Vector 的曲线值表示“每秒速度源”，脚本每帧执行 `current += velocity * deltaTime` 后写回材质参数。
5. 持续叠加 Vector 的更新阶段应可配置，例如 Idle、Play、Play 完成、Stop、Stop 完成，避免速度保持策略依赖模糊状态。
6. Play / Stop 互相打断时，目标阶段从 0 秒开始正常采样；最终输出在固定时间内从当前输出追赶到目标阶段实时采样值。
7. CrossFade 对持续叠加 Vector 融合的是速度源，不回拉已经累积的 Offset。
8. 为兼容 SRP Batcher，默认通过 `Renderer.materials` 获取并写入材质实例，不使用 `MaterialPropertyBlock`。
9. Shader 中被脚本写入的 Float、Vector、Color 参数应放入 `UnityPerMaterial` CBUFFER。
10. 不建议为明显重复或冲突的配置加入复杂运行时防御；这类问题优先交给编辑器配置规范、校验或人工检查处理。

#### UV 滚动与 `_Time` 的取舍

Shader 内直接使用 `_Time.y * speed` 做 UV 滚动时，`speed` 变化会作用到历史累计时间上，容易造成 offset 瞬间跳变或平滑变速期间异常追赶。项目实践中更简单可控的方案是把 shader 暴露的 Vector 参数作为实际 Offset，由脚本在持续叠加模式下按帧积分。

在该类控制器语义中：

- Vector 曲线记录的是速度源，而不是最终 Offset。
- 启用持续叠加后，脚本每帧读取当前材质参数值并追加增量。
- 曲线仍然可以参与 Play / Stop 阶段和 CrossFade，但持续位移不会因为阶段切换被拉回。

这种方式牺牲了“完全由 shader 自己用 `_Time` 推进”的形式，但换来更清晰的运行时生命周期和更可控的 Play / Stop 打断行为。

#### CrossFade 追赶策略

打断播放时不要用“根据当前值反查目标曲线进度”的方式作为主策略。多条曲线形状差异较大时，按单个参数值反查进度容易导致整体节奏漂移。

更稳定的做法是固定时间追赶：

1. 切换瞬间捕获当前实际输出 `sourceValue`。
2. 目标阶段从 0 秒开始正常推进并实时采样 `targetValue`。
3. 在固定 `crossFadeDurationSeconds` 内输出 `Lerp(sourceValue, liveTargetValue, blendT)`。
4. 融合结束后完全使用目标阶段采样结果。
5. 如果融合中再次切换，重新捕获当前已经融合后的实际输出作为新的 `sourceValue`。

该方案不是 Unity Animator 的 `CrossFadeInFixedTime` 本身，而是在材质参数动画控制器内部采用同类“固定秒数过渡”的语义。Unity 官方 `Animator.CrossFadeInFixedTime` 也以秒为单位定义过渡时长，这与项目的材质参数 CrossFade 配置方向一致。

#### SRP Batcher 与材质写入

Unity 官方文档明确指出，`MaterialPropertyBlock` 不兼容 SRP Batcher；SRP Batcher 兼容对象要求 shader 使用 `UnityPerMaterial` 承载材质属性。因此在需要保持 SRP Batcher 路径的效果系统里，应优先写材质实例参数，而不是用 MPB 做 per-renderer 覆写。

`Renderer.materials` 会返回当前 Renderer 的实例化材质数组，修改其中材质只影响该对象。需要注意：

- `renderer.materials` 返回的是数组副本，但数组内材质引用是实例材质。
- 外部运行时替换 `renderer.materials` 或 `renderer.sharedMaterials` 后，缓存的旧材质引用可能失效。
- 因此材质参数控制器在需要适配运行时材质替换时，更适合按需重新获取目标材质，而不是长期缓存材质数组。

#### 生命周期配置

参数生命周期建议显式拆成以下阶段：

- 初始化默认值：控制器初始化时可选写入。
- Play 开始前设值：可选；未启用时直接进入淡入曲线。
- Play 过程中曲线：按秒采样。
- Play 完成后：可按配置保持持续更新。
- Stop 过程中曲线：如果没有配置曲线，则应按生命周期策略保留当前输出或跳过阶段。
- Stop 完成后设值：可选；未启用时保留淡出最终输出或当前输出。

这种拆分比“Stop 后一律 reset”更清楚，也能覆盖 Play 未完成就 Stop、Stop 未完成又 Play 的打断场景。

### 关键代码

```csharp
// 持续叠加 Vector：曲线值表示每秒速度源，材质参数保存实际 Offset。
Vector4 currentValue = material.GetVector(paramAnim.paramName);
currentValue += velocity * deltaTime;
material.SetVector(paramAnim.paramName, currentValue);
```

```csharp
// 固定时间追赶式 CrossFade：目标阶段持续实时采样，source 只在切换瞬间固定。
float blendT = Mathf.Clamp01(crossFadeElapsed / crossFadeDurationSeconds);
ParameterValue liveTargetValue = SampleTargetValue(paramAnim, targetState, sampleTime);
ParameterValue finalValue = Lerp(sourceValue, liveTargetValue, blendT);
ApplyValue(material, paramAnim, finalValue);
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

- [Unity Manual - SRP Batcher](https://docs.unity3d.com/2022.3/Documentation/Manual/SRPBatcher.html) - SRP Batcher 兼容条件，包含 `UnityPerMaterial` 与 MaterialPropertyBlock 约束。
- [Unity Scripting API - MaterialPropertyBlock](https://docs.unity3d.com/2022.3/Documentation/ScriptReference/MaterialPropertyBlock.html) - 官方说明 MPB 不兼容 SRP Batcher。
- [Unity Scripting API - Renderer.materials](https://docs.unity3d.com/2022.3/Documentation/ScriptReference/Renderer-materials.html) - `Renderer.materials` 的实例化材质语义。
- [Unity Scripting API - AnimationCurve.Evaluate](https://docs.unity3d.com/2022.3/Documentation/ScriptReference/AnimationCurve.Evaluate.html) - 曲线按传入 time 横轴采样。
- [Unity Scripting API - Animator.CrossFadeInFixedTime](https://docs.unity3d.com/2022.3/Documentation/ScriptReference/Animator.CrossFadeInFixedTime.html) - 固定秒数过渡的 Animator API 参考。
- [Unity Manual - Built-in shader variables](https://docs.unity.cn/2023.3/Documentation/Manual/SL-UnityShaderVariables.html) - `_Time` 和 `unity_DeltaTime` 等内置 shader 时间变量。

### 相关记录

- [Unity 渲染相关知识](./unity-material-renderer.md) - `Renderer.materials` 实例化行为与运行时材质替换风险。
- [CBUFFER 与 SRP Batcher 合批机制](./cbuffer-srp-batcher-mechanism.md) - `UnityPerMaterial` 与 SRP Batcher 兼容背景。
- [SRP Batcher 参数开销分析](./srp-batcher-parameter-overhead.md) - 相同 Shader 下 Float / Vector 参数差异的开销经验。
- [Unity 动画与脚本开发核心知识清单](./unity-animation-scripting-notes.md) - Animator Play / CrossFade 基础语义参考。

### 验证记录

- [2026-05-25] 初次记录：基于某 Unity 项目材质参数动画控制器改造过程、运行时与编辑器程序集编译验证，以及 Unity 2022.3 官方文档交叉确认。记录已脱敏，仅保留可复用技术结论；若项目文档与代码语义存在差异，应按当前代码现状另行同步项目文档。

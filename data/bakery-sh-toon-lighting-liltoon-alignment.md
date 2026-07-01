# Bakery SH 对齐 lilToon 的 Toon 化采样与暗部回填实践

**标签**：#unity #shader #graphics #urp #npr #hlsl #experience
**来源**：实践总结（已脱敏）
**收录日期**：2026-07-01
**来源日期**：2026-07-01
**更新日期**：2026-07-01
**状态**：⚠️ 待验证
**可信度**：⭐⭐⭐（已完成源码审查和 ShaderGraph 配置核对，尚未完成 Unity 重新导入/编译验证）
**适用版本**：Unity URP ShaderGraph + Bakery SH/RNM；具体 Unity 与 Bakery 版本未绑定

### 概要

在卡通渲染项目中，直接把 Bakery SH 按表面法线作为间接漫反射使用，容易把角色或场景的暗部推向连续、写实的 PBR 观感。实践方案是在原 `BakerySH_float` 外新增 Toon 包装层：仍复用 Bakery 的 SH 解码、Geomerics 亮度修正、非负 clamp 和抗振铃能力，但把采样方向改成“环境主方向 + 主光方向”的风格化方向，并拆分为亮侧补偿与暗部回填信号。

### 内容

#### 问题背景

- Bakery SH/RNM 提供了有方向性的烘焙环境光，直接用 `normalWorld` 采样会得到较连续的物理漫反射渐变。
- Toon/NPR 目标更重视可控色阶、阴影色板和主光明暗边界；因此 SH 不应直接决定最终颜色。
- 目标不是抛弃 Bakery SH，而是把 Bakery SH 转成 Toon 可用的“亮侧补偿”和“暗侧回填强度”。

#### 脱敏边界

本记录已脱敏处理：

- 不记录真实项目名、内部场景名、完整目录、分支名、截图临时路径、用户本机路径。
- 不记录 ShaderGraph 的 GUID、ObjectId、Slot ObjectId 等内部资产标识。
- 文件名只保留通用实现单元：`BakeryToonDecodeLightmap.hlsl`、`BakeryDecodeLightmap.hlsl`。
- ShaderGraph 只记录节点语义、端口名、默认值和连接关系，不记录资产内部序列化 ID。

#### 设计原则

1. **原 Bakery 解码不重写**：`BakerySH_float` 仍是唯一 SH 采样入口，避免丢失 Bakery 原有抗振铃和非负保护。
2. **不按最终表面法线直接采 SH**：先从 RNM/L1 或 Unity SH L1 估算环境主方向，再和主光方向合成 Toon 采样方向。
3. **对齐 lilToon 的正反方向采样思想**：正向采样作为亮侧环境补偿，反向采样作为暗侧环境回填。
4. **SH 只给强度，不接管色相**：阴影色仍由 Toon 色板或项目已有阴影逻辑决定。
5. **ShaderGraph 输出分级**：`toonLightSH` 和 `toonFillLuma` 是常规输出；`toonFillSH` 与 `toonDirectionWS` 更偏调试或高级接线。

#### 数据流

```text
Bakery L0 + RNM/L1 或 Unity SH L1
→ 估算环境主方向 envDir
→ 与主光方向 mainDir 按权重混合
→ directionScale 削弱方向性
→ BakerySH_float(正向采样) 得到 toonLightSH
→ BakerySH_float(反向采样) 得到 toonFillSH
→ toonFillSH 压成 toonFillLuma，作为暗部回填遮罩
```

#### ShaderGraph 节点配置（脱敏）

| 项 | 配置 |
|---|---|
| Custom Function 文件 | `BakeryToonDecodeLightmap.hlsl` |
| 函数名 | `BakeryToonSH`（ShaderGraph 填无精度后缀；实际 HLSL 函数为 `BakeryToonSH_float`） |
| 输入 | `L0`、`normalWorld`、`lightmapUV`、`mainLightDirWS`、`mainLightColor`、`directionScale`、`envDirectionWeight`、`mainDirectionWeight` |
| 输出 | `toonLightSH`、`toonFillSH`、`toonDirectionWS`、`toonFillLuma` |
| 主光连接 | `mainLightDirWS` 接主光方向，`mainLightColor` 接主光颜色 |
| 默认参数 | `directionScale = 0.666666`，`envDirectionWeight = 1.0`，`mainDirectionWeight = 1.0` |
| 常规接线建议 | `toonLightSH` 少量参与亮面补偿；`toonFillLuma` 接 Lerp/Remap/Smoothstep 做暗部回填遮罩 |
| 不建议直接使用 | `toonFillSH` 不直接当最终颜色；`toonDirectionWS` 是方向向量，通常只用于调试 |

#### 输出端口语义

| 输出 | 语义 | 推荐用法 | 直接接最终颜色的风险 |
|---|---|---|---|
| `toonLightSH` | 正向 Toon 采样得到的亮侧环境信号 | 少量加到亮面或主光强度 | 权重过大会让亮面被烘焙环境染色 |
| `toonFillSH` | 反向 Toon 采样得到的暗侧环境信号 | 可转亮度或做 RGB 回填强度 | 它仍是环境能量，不是美术阴影色 |
| `toonDirectionWS` | 环境方向与主光方向合成出的 Toon 采样方向 | 调试、方向可视化、高级 Rim/Spec 参考 | 它是方向，不是颜色 |
| `toonFillLuma` | `toonFillSH` 的非负亮度 | 作为 Lerp 的 `T` 或 Remap 输入 | 需要限制强度，否则暗部可能过亮 |

#### 逐行实现说明
#### BakeryToonDecodeLightmap.hlsl 逐行说明（脱敏）

| 行 | 脱敏代码 | 逐行说明 |
|---|---|---|
| 1 | <code>#ifndef BAKERY_TOON_DECODE_LIGHTMAP_INCLUDED</code> | 包含保护宏，防止该包装文件在同一 Shader 编译单元里重复展开。 |
| 2 | <code>#define BAKERY_TOON_DECODE_LIGHTMAP_INCLUDED</code> | 包含保护宏，防止该包装文件在同一 Shader 编译单元里重复展开。 |
| 3 | <code></code> | 空行，用于分隔包含保护与 include。 |
| 4 | <code>#include "BakeryDecodeLightmap.hlsl"</code> | 引入原 Bakery 解码文件；设计取舍是复用原 BakerySH_float，不重写 SH 解码和抗振铃逻辑。 |
| 5 | <code></code> | 空行，用于分隔依赖声明与文件级说明。 |
| 6 | <code>// Bakery SH 的卡通化包装层。</code> | 文件级维护说明：强调这是 Toon 包装层，职责是改采样方向和整理输出，不替代 Bakery 原实现。 |
| 7 | <code>// 原始 BakerySH_float 仍然是唯一的 SH 采样入口，这样可以继续复用 Bakery 内部</code> | 文件级维护说明：强调这是 Toon 包装层，职责是改采样方向和整理输出，不替代 Bakery 原实现。 |
| 8 | <code>// Geomerics 亮度修正和非负 clamp，避免把振铃/负光照问题重新引入卡通流程。</code> | 文件级维护说明：强调这是 Toon 包装层，职责是改采样方向和整理输出，不替代 Bakery 原实现。 |
| 9 | <code>// 本文件只负责改造采样方向，并把采样结果整理成 Toon 光照需要的亮侧与暗侧信号。</code> | 文件级维护说明：强调这是 Toon 包装层，职责是改采样方向和整理输出，不替代 Bakery 原实现。 |
| 10 | <code></code> | 空行，用于分隔文件说明与常量定义。 |
| 11 | <code>// 所有归一化保护共用这个阈值，避免无方向环境光或黑光场景产生 NaN。</code> | 说明归一化保护阈值的用途，避免无方向光照时出现 NaN。 |
| 12 | <code>#define BAKERY_TOON_EPSILON 1e-6f</code> | 定义安全阈值；后续 SafeNormalize 使用它判断向量长度是否可靠。 |
| 13 | <code></code> | 空行，用于分隔常量与亮度函数。 |
| 14 | <code>// 保留符号的亮度，用于从 RGB L1 系数中提取“方向性”；符号不能丢，否则环境主方向会被抹平。</code> | 说明保留符号亮度的目的：方向提取不能把正负方向性抹掉。 |
| 15 | <code>float BakeryToonSignedLuminance(float3 color)</code> | 实现带符号亮度：使用 Rec.709 亮度权重从 RGB 中提取标量，同时保留负值方向信息。 |
| 16 | <code>{</code> | 实现带符号亮度：使用 Rec.709 亮度权重从 RGB 中提取标量，同时保留负值方向信息。 |
| 17 | <code>    return dot(color, float3(0.2126729f, 0.7151522f, 0.0721750f));</code> | 实现带符号亮度：使用 Rec.709 亮度权重从 RGB 中提取标量，同时保留负值方向信息。 |
| 18 | <code>}</code> | 实现带符号亮度：使用 Rec.709 亮度权重从 RGB 中提取标量，同时保留负值方向信息。 |
| 19 | <code></code> | 空行，用于分隔两种亮度函数。 |
| 20 | <code>// 非负亮度用于输出给 ShaderGraph 做暗部回填遮罩，避免负值影响 Lerp/Saturate 这类节点。</code> | 说明非负亮度的用途：给 ShaderGraph 做遮罩时避免负数污染插值。 |
| 21 | <code>float BakeryToonPositiveLuminance(float3 color)</code> | 实现非负亮度：先对 RGB 做 max(0)，再复用带符号亮度函数。 |
| 22 | <code>{</code> | 实现非负亮度：先对 RGB 做 max(0)，再复用带符号亮度函数。 |
| 23 | <code>    return BakeryToonSignedLuminance(max(color, float3(0.0f, 0.0f, 0.0f)));</code> | 实现非负亮度：先对 RGB 做 max(0)，再复用带符号亮度函数。 |
| 24 | <code>}</code> | 实现非负亮度：先对 RGB 做 max(0)，再复用带符号亮度函数。 |
| 25 | <code></code> | 空行，用于分隔亮度函数与安全归一化。 |
| 26 | <code>// 带回退值的安全归一化。方向长度过小时回退到法线或默认向上方向，保证预览和极端光照下稳定。</code> | 说明安全归一化的边界条件和回退策略。 |
| 27 | <code>float3 BakeryToonSafeNormalize(float3 value, float3 fallback)</code> | 实现安全归一化：长度足够时用 rsqrt 归一化，长度过小时返回 fallback。 |
| 28 | <code>{</code> | 实现安全归一化：长度足够时用 rsqrt 归一化，长度过小时返回 fallback。 |
| 29 | <code>    float lenSq = dot(value, value);</code> | 实现安全归一化：长度足够时用 rsqrt 归一化，长度过小时返回 fallback。 |
| 30 | <code>    return lenSq &gt; BAKERY_TOON_EPSILON ? value * rsqrt(lenSq) : fallback;</code> | 实现安全归一化：长度足够时用 rsqrt 归一化，长度过小时返回 fallback。 |
| 31 | <code>}</code> | 实现安全归一化：长度足够时用 rsqrt 归一化，长度过小时返回 fallback。 |
| 32 | <code></code> | 空行，用于分隔工具函数与环境方向估算函数。 |
| 33 | <code>// 从 Bakery 的 RNM/L1 或 Unity Light Probe 的 L1 系数估算环境主方向。</code> | 声明环境主方向估算函数；输入是 L0 和 lightmapUV，输出是用于 Toon 采样方向合成的方向提示。 |
| 34 | <code>// 这里不按表面法线直接取 SH，而是先得到一个“环境方向提示”，后续再和主光方向合成 Toon 采样方向。</code> | 声明环境主方向估算函数；输入是 L0 和 lightmapUV，输出是用于 Toon 采样方向合成的方向提示。 |
| 35 | <code>float3 BakeryToonGetSHDirection(float3 L0, float2 lightmapUV)</code> | 声明环境主方向估算函数；输入是 L0 和 lightmapUV，输出是用于 Toon 采样方向合成的方向提示。 |
| 36 | <code>{</code> | 函数体开始。 |
| 37 | <code>#ifdef LIGHTMAP_ON</code> | 编译分支：存在烘焙 lightmap 时优先使用 Bakery RNM/L1 数据。 |
| 38 | <code>    float3 nL1x = SAMPLERNM(_RNM0, lightmapUV).rgb * 2.0f - 1.0f;</code> | 从三张 RNM 纹理读取归一化 L1 方向分量，并从 0..1 还原到 -1..1。 |
| 39 | <code>    float3 nL1y = SAMPLERNM(_RNM1, lightmapUV).rgb * 2.0f - 1.0f;</code> | 从三张 RNM 纹理读取归一化 L1 方向分量，并从 0..1 还原到 -1..1。 |
| 40 | <code>    float3 nL1z = SAMPLERNM(_RNM2, lightmapUV).rgb * 2.0f - 1.0f;</code> | 从三张 RNM 纹理读取归一化 L1 方向分量，并从 0..1 还原到 -1..1。 |
| 41 | <code></code> | 空行，用于分隔 RNM 解包与 L1 重建。 |
| 42 | <code>    float3 L1x = nL1x * L0 * 2.0f;</code> | 按 BakerySH_float 的语义用 L0 放大重建 L1x/L1y/L1z，保留 Bakery 烘焙强度。 |
| 43 | <code>    float3 L1y = nL1y * L0 * 2.0f;</code> | 按 BakerySH_float 的语义用 L0 放大重建 L1x/L1y/L1z，保留 Bakery 烘焙强度。 |
| 44 | <code>    float3 L1z = nL1z * L0 * 2.0f;</code> | 按 BakerySH_float 的语义用 L0 放大重建 L1x/L1y/L1z，保留 Bakery 烘焙强度。 |
| 45 | <code></code> | 空行，用于分隔 L1 重建与方向折叠。 |
| 46 | <code>    // 将彩色 L1 合并成单一方向轴，但保留正负方向性。</code> | 说明为什么把彩色 L1 折叠成单轴：只提取方向提示，不在这里做表面法线物理采样。 |
| 47 | <code>    // 这一步复用 BakerySH_float 的 L1 重建语义，只是不在这里评估最终表面法线；</code> | 说明为什么把彩色 L1 折叠成单轴：只提取方向提示，不在这里做表面法线物理采样。 |
| 48 | <code>    // 卡通渲染会用后面合成出的风格化方向来采样。</code> | 说明为什么把彩色 L1 折叠成单轴：只提取方向提示，不在这里做表面法线物理采样。 |
| 49 | <code>    return float3(</code> | 返回环境方向提示：分别取 L1x/L1y/L1z 的带符号亮度作为方向向量三个分量。 |
| 50 | <code>        BakeryToonSignedLuminance(L1x),</code> | 返回环境方向提示：分别取 L1x/L1y/L1z 的带符号亮度作为方向向量三个分量。 |
| 51 | <code>        BakeryToonSignedLuminance(L1y),</code> | 返回环境方向提示：分别取 L1x/L1y/L1z 的带符号亮度作为方向向量三个分量。 |
| 52 | <code>        BakeryToonSignedLuminance(L1z)</code> | 返回环境方向提示：分别取 L1x/L1y/L1z 的带符号亮度作为方向向量三个分量。 |
| 53 | <code>    );</code> | 返回环境方向提示：分别取 L1x/L1y/L1z 的带符号亮度作为方向向量三个分量。 |
| 54 | <code>#else</code> | 编译分支：没有 lightmap 时进入 Unity Light Probe 回退路径。 |
| 55 | <code>    // Light Probe 回退路径。Unity 将 RGB 三组 L1 分开存储，这里按亮度权重合成一个环境主方向。</code> | 说明 Light Probe 回退的方向合成方式。 |
| 56 | <code>    return unity_SHAr.xyz * 0.2126729f</code> | 用 unity_SHAr/Ag/Ab 三组 L1 按亮度权重合成环境主方向。 |
| 57 | <code>         + unity_SHAg.xyz * 0.7151522f</code> | 用 unity_SHAr/Ag/Ab 三组 L1 按亮度权重合成环境主方向。 |
| 58 | <code>         + unity_SHAb.xyz * 0.0721750f;</code> | 用 unity_SHAr/Ag/Ab 三组 L1 按亮度权重合成环境主方向。 |
| 59 | <code>#endif</code> | 结束 LIGHTMAP_ON 条件编译。 |
| 60 | <code>}</code> | 结束环境方向估算函数。 |
| 61 | <code></code> | 空行，用于分隔环境方向估算与 Toon 方向合成函数。 |
| 62 | <code>// 合成 Toon SH 的采样方向。</code> | 说明 Toon 采样方向的设计：环境方向给场景归属感，主光方向给卡通明暗主导。 |
| 63 | <code>// 环境方向提供场景归属感，主光方向提供卡通明暗的视觉主导；两个权重用于按项目美术需求调节占比。</code> | 说明 Toon 采样方向的设计：环境方向给场景归属感，主光方向给卡通明暗主导。 |
| 64 | <code>void BakeryToonDirection_float(</code> | 声明 ShaderGraph 可调用的 Toon 方向函数；输入包括 Bakery SH、主光和权重，输出合成方向与实际采样方向。 |
| 65 | <code>    float3 L0,</code> | 声明 ShaderGraph 可调用的 Toon 方向函数；输入包括 Bakery SH、主光和权重，输出合成方向与实际采样方向。 |
| 66 | <code>    float3 normalWorld,</code> | 声明 ShaderGraph 可调用的 Toon 方向函数；输入包括 Bakery SH、主光和权重，输出合成方向与实际采样方向。 |
| 67 | <code>    float2 lightmapUV,</code> | 声明 ShaderGraph 可调用的 Toon 方向函数；输入包括 Bakery SH、主光和权重，输出合成方向与实际采样方向。 |
| 68 | <code>    float3 mainLightDirWS,</code> | 声明 ShaderGraph 可调用的 Toon 方向函数；输入包括 Bakery SH、主光和权重，输出合成方向与实际采样方向。 |
| 69 | <code>    float3 mainLightColor,</code> | 声明 ShaderGraph 可调用的 Toon 方向函数；输入包括 Bakery SH、主光和权重，输出合成方向与实际采样方向。 |
| 70 | <code>    float directionScale,</code> | 声明 ShaderGraph 可调用的 Toon 方向函数；输入包括 Bakery SH、主光和权重，输出合成方向与实际采样方向。 |
| 71 | <code>    float envDirectionWeight,</code> | 声明 ShaderGraph 可调用的 Toon 方向函数；输入包括 Bakery SH、主光和权重，输出合成方向与实际采样方向。 |
| 72 | <code>    float mainDirectionWeight,</code> | 声明 ShaderGraph 可调用的 Toon 方向函数；输入包括 Bakery SH、主光和权重，输出合成方向与实际采样方向。 |
| 73 | <code>    out float3 toonDirectionWS,</code> | 声明 ShaderGraph 可调用的 Toon 方向函数；输入包括 Bakery SH、主光和权重，输出合成方向与实际采样方向。 |
| 74 | <code>    out float3 sampleDirectionWS)</code> | 声明 ShaderGraph 可调用的 Toon 方向函数；输入包括 Bakery SH、主光和权重，输出合成方向与实际采样方向。 |
| 75 | <code>{</code> | 函数体开始。 |
| 76 | <code>    float3 fallbackNormal = BakeryToonSafeNormalize(normalWorld, float3(0.0f, 1.0f, 0.0f));</code> | 把 normalWorld 归一化成 fallbackNormal；法线不可用时回退到世界向上。 |
| 77 | <code>    float3 envDir = BakeryToonSafeNormalize(BakeryToonGetSHDirection(L0, lightmapUV), fallbackNormal);</code> | 估算并安全归一化环境方向；环境方向无效时回退到 fallbackNormal。 |
| 78 | <code></code> | 空行，用于分隔环境方向与主光方向处理。 |
| 79 | <code>    // mainLightDirWS 使用 URP 的 surface-to-light 约定，也就是通常用于 dot(normalWS, light.direction) 的方向。</code> | 说明 mainLightDirWS 采用 URP surface-to-light 约定，避免方向符号误接。 |
| 80 | <code>    float3 mainDir = BakeryToonSafeNormalize(mainLightDirWS, fallbackNormal);</code> | 安全归一化主光方向；主光方向无效时回退到 fallbackNormal。 |
| 81 | <code>    float mainLum = max(BakeryToonSignedLuminance(mainLightColor), 0.0f);</code> | 计算主光亮度，并 clamp 到非负，避免负主光影响方向混合权重。 |
| 82 | <code></code> | 空行，用于分隔方向输入与权重处理。 |
| 83 | <code>    float envWeight = max(envDirectionWeight, 0.0f);</code> | 将环境方向权重限制为非负，避免权重反相造成不可控方向。 |
| 84 | <code>    float mainWeight = max(mainDirectionWeight, 0.0f) * mainLum;</code> | 将主光权重限制为非负，并乘主光亮度，使主光越亮方向影响越明显。 |
| 85 | <code></code> | 空行，用于分隔权重计算与方向合成。 |
| 86 | <code>    toonDirectionWS = BakeryToonSafeNormalize(envDir * envWeight + mainDir * mainWeight, envDir);</code> | 合成 Toon 方向：envDir 和 mainDir 按权重混合后安全归一化，失败则回退到 envDir。 |
| 87 | <code></code> | 空行，用于分隔方向合成与方向削弱。 |
| 88 | <code>    // 对齐 lilToon 的思路：采样前削弱方向长度，让结果更像风格化亮侧/暗侧提示，而不是物理漫反射渐变。</code> | 说明 directionScale 对齐 lilToon：削弱 SH 方向性，避免恢复成物理漫反射渐变。 |
| 89 | <code>    sampleDirectionWS = toonDirectionWS * saturate(directionScale);</code> | 输出实际采样方向：对 toonDirectionWS 乘 saturate(directionScale)，默认可取 0.666666。 |
| 90 | <code>}</code> | 结束 Toon 方向函数。 |
| 91 | <code></code> | 空行，用于分隔方向函数与主要 ShaderGraph 入口。 |
| 92 | <code>// 主要入口：输出亮侧 SH、暗侧 SH、调试方向和暗侧亮度遮罩。</code> | 说明主入口输出边界：常规优先用 toonLightSH 和 toonFillLuma，其它输出偏调试/高级接线。 |
| 93 | <code>// 常规材质里优先使用 toonLightSH 和 toonFillLuma；toonFillSH/toonDirectionWS 主要用于调试或高级接线。</code> | 说明主入口输出边界：常规优先用 toonLightSH 和 toonFillLuma，其它输出偏调试/高级接线。 |
| 94 | <code>void BakeryToonSH_float(</code> | 声明 ShaderGraph 主入口；输入与方向函数一致，输出亮侧 SH、暗侧 SH、调试方向和暗侧亮度。 |
| 95 | <code>    float3 L0,</code> | 声明 ShaderGraph 主入口；输入与方向函数一致，输出亮侧 SH、暗侧 SH、调试方向和暗侧亮度。 |
| 96 | <code>    float3 normalWorld,</code> | 声明 ShaderGraph 主入口；输入与方向函数一致，输出亮侧 SH、暗侧 SH、调试方向和暗侧亮度。 |
| 97 | <code>    float2 lightmapUV,</code> | 声明 ShaderGraph 主入口；输入与方向函数一致，输出亮侧 SH、暗侧 SH、调试方向和暗侧亮度。 |
| 98 | <code>    float3 mainLightDirWS,</code> | 声明 ShaderGraph 主入口；输入与方向函数一致，输出亮侧 SH、暗侧 SH、调试方向和暗侧亮度。 |
| 99 | <code>    float3 mainLightColor,</code> | 声明 ShaderGraph 主入口；输入与方向函数一致，输出亮侧 SH、暗侧 SH、调试方向和暗侧亮度。 |
| 100 | <code>    float directionScale,</code> | 声明 ShaderGraph 主入口；输入与方向函数一致，输出亮侧 SH、暗侧 SH、调试方向和暗侧亮度。 |
| 101 | <code>    float envDirectionWeight,</code> | 声明 ShaderGraph 主入口；输入与方向函数一致，输出亮侧 SH、暗侧 SH、调试方向和暗侧亮度。 |
| 102 | <code>    float mainDirectionWeight,</code> | 声明 ShaderGraph 主入口；输入与方向函数一致，输出亮侧 SH、暗侧 SH、调试方向和暗侧亮度。 |
| 103 | <code>    out float3 toonLightSH,</code> | 声明 ShaderGraph 主入口；输入与方向函数一致，输出亮侧 SH、暗侧 SH、调试方向和暗侧亮度。 |
| 104 | <code>    out float3 toonFillSH,</code> | 声明 ShaderGraph 主入口；输入与方向函数一致，输出亮侧 SH、暗侧 SH、调试方向和暗侧亮度。 |
| 105 | <code>    out float3 toonDirectionWS,</code> | 声明 ShaderGraph 主入口；输入与方向函数一致，输出亮侧 SH、暗侧 SH、调试方向和暗侧亮度。 |
| 106 | <code>    out float toonFillLuma)</code> | 声明 ShaderGraph 主入口；输入与方向函数一致，输出亮侧 SH、暗侧 SH、调试方向和暗侧亮度。 |
| 107 | <code>{</code> | 函数体开始。 |
| 108 | <code>    float3 sampleDirectionWS;</code> | 声明内部采样方向变量，不直接暴露给最终颜色。 |
| 109 | <code>    BakeryToonDirection_float(</code> | 调用方向合成函数，把输入参数转换成 toonDirectionWS 和 sampleDirectionWS。 |
| 110 | <code>        L0,</code> | 调用方向合成函数，把输入参数转换成 toonDirectionWS 和 sampleDirectionWS。 |
| 111 | <code>        normalWorld,</code> | 调用方向合成函数，把输入参数转换成 toonDirectionWS 和 sampleDirectionWS。 |
| 112 | <code>        lightmapUV,</code> | 调用方向合成函数，把输入参数转换成 toonDirectionWS 和 sampleDirectionWS。 |
| 113 | <code>        mainLightDirWS,</code> | 调用方向合成函数，把输入参数转换成 toonDirectionWS 和 sampleDirectionWS。 |
| 114 | <code>        mainLightColor,</code> | 调用方向合成函数，把输入参数转换成 toonDirectionWS 和 sampleDirectionWS。 |
| 115 | <code>        directionScale,</code> | 调用方向合成函数，把输入参数转换成 toonDirectionWS 和 sampleDirectionWS。 |
| 116 | <code>        envDirectionWeight,</code> | 调用方向合成函数，把输入参数转换成 toonDirectionWS 和 sampleDirectionWS。 |
| 117 | <code>        mainDirectionWeight,</code> | 调用方向合成函数，把输入参数转换成 toonDirectionWS 和 sampleDirectionWS。 |
| 118 | <code>        toonDirectionWS,</code> | 调用方向合成函数，把输入参数转换成 toonDirectionWS 和 sampleDirectionWS。 |
| 119 | <code>        sampleDirectionWS</code> | 调用方向合成函数，把输入参数转换成 toonDirectionWS 和 sampleDirectionWS。 |
| 120 | <code>    );</code> | 调用方向合成函数，把输入参数转换成 toonDirectionWS 和 sampleDirectionWS。 |
| 121 | <code></code> | 空行，用于分隔方向生成与 SH 双向采样。 |
| 122 | <code>    // 正反两个方向分别模拟 lilToon 的亮侧 SH 和暗侧 SH。</code> | 说明正反方向采样的 lilToon 对齐关系，以及继续复用 Bakery 抗振铃处理。 |
| 123 | <code>    // 两次采样都继续走 BakerySH_float，保证 Bakery 的抗振铃处理仍然生效。</code> | 说明正反方向采样的 lilToon 对齐关系，以及继续复用 Bakery 抗振铃处理。 |
| 124 | <code>    BakerySH_float(L0, sampleDirectionWS, lightmapUV, toonLightSH);</code> | 用正向 sampleDirectionWS 采样 BakerySH_float，得到亮侧环境/补光信号 toonLightSH。 |
| 125 | <code>    BakerySH_float(L0, -sampleDirectionWS, lightmapUV, toonFillSH);</code> | 用反向 sampleDirectionWS 采样 BakerySH_float，得到暗侧环境/回填信号 toonFillSH。 |
| 126 | <code></code> | 空行，用于分隔采样与输出清理。 |
| 127 | <code>    toonLightSH = max(toonLightSH, float3(0.0f, 0.0f, 0.0f));</code> | 对亮侧 SH 做非负保护，避免异常负值传到亮面。 |
| 128 | <code>    toonFillSH = max(toonFillSH, float3(0.0f, 0.0f, 0.0f));</code> | 对暗侧 SH 做非负保护，避免负值污染暗部回填遮罩。 |
| 129 | <code>    toonFillLuma = BakeryToonPositiveLuminance(toonFillSH);</code> | 将暗侧 SH 压成非负亮度，提供 ShaderGraph 中更稳定的单通道回填遮罩。 |
| 130 | <code>}</code> | 结束 ShaderGraph 主入口。 |
| 131 | <code></code> | 空行，用于分隔主入口与可选合成模板。 |
| 132 | <code>// 可选的 lilToon 风格合成模板。</code> | 说明可选合成模板的边界：只给参考，不强制取代项目现有 Toon 色板。 |
| 133 | <code>// 这个函数只演示推荐合成边界：SH 负责亮侧补偿和暗部回填强度，最终阴影色仍由调用方的美术色板决定。</code> | 说明可选合成模板的边界：只给参考，不强制取代项目现有 Toon 色板。 |
| 134 | <code>void BakeryToonLighting_float(</code> | 声明可选的 lilToon 风格合成函数；输入包括 albedo、阴影色、toonBand、主光、SH 与限制参数。 |
| 135 | <code>    float3 albedo,</code> | 声明可选的 lilToon 风格合成函数；输入包括 albedo、阴影色、toonBand、主光、SH 与限制参数。 |
| 136 | <code>    float3 shadowColor,</code> | 声明可选的 lilToon 风格合成函数；输入包括 albedo、阴影色、toonBand、主光、SH 与限制参数。 |
| 137 | <code>    float toonBand,</code> | 声明可选的 lilToon 风格合成函数；输入包括 albedo、阴影色、toonBand、主光、SH 与限制参数。 |
| 138 | <code>    float3 mainLightColor,</code> | 声明可选的 lilToon 风格合成函数；输入包括 albedo、阴影色、toonBand、主光、SH 与限制参数。 |
| 139 | <code>    float3 toonLightSH,</code> | 声明可选的 lilToon 风格合成函数；输入包括 albedo、阴影色、toonBand、主光、SH 与限制参数。 |
| 140 | <code>    float3 toonFillSH,</code> | 声明可选的 lilToon 风格合成函数；输入包括 albedo、阴影色、toonBand、主光、SH 与限制参数。 |
| 141 | <code>    float directSHWeight,</code> | 声明可选的 lilToon 风格合成函数；输入包括 albedo、阴影色、toonBand、主光、SH 与限制参数。 |
| 142 | <code>    float shadowEnvStrength,</code> | 声明可选的 lilToon 风格合成函数；输入包括 albedo、阴影色、toonBand、主光、SH 与限制参数。 |
| 143 | <code>    float lightMinLimit,</code> | 声明可选的 lilToon 风格合成函数；输入包括 albedo、阴影色、toonBand、主光、SH 与限制参数。 |
| 144 | <code>    float lightMaxLimit,</code> | 声明可选的 lilToon 风格合成函数；输入包括 albedo、阴影色、toonBand、主光、SH 与限制参数。 |
| 145 | <code>    out float3 color,</code> | 声明可选的 lilToon 风格合成函数；输入包括 albedo、阴影色、toonBand、主光、SH 与限制参数。 |
| 146 | <code>    out float3 lightColor,</code> | 声明可选的 lilToon 风格合成函数；输入包括 albedo、阴影色、toonBand、主光、SH 与限制参数。 |
| 147 | <code>    out float3 indirectColor)</code> | 声明可选的 lilToon 风格合成函数；输入包括 albedo、阴影色、toonBand、主光、SH 与限制参数。 |
| 148 | <code>{</code> | 函数体开始。 |
| 149 | <code>    // 亮侧：主光颜色叠加少量 Toon SH，再做上下限约束，避免烘焙环境把卡通亮面打爆。</code> | 说明亮侧合成：主光加少量 Toon SH，并用上下限防止过曝。 |
| 150 | <code>    lightColor = mainLightColor + toonLightSH * max(directSHWeight, 0.0f);</code> | 计算 lightColor：主光颜色叠加 toonLightSH * directSHWeight。 |
| 151 | <code>    lightColor = clamp(</code> | 对 lightColor 做 clamp，避免烘焙环境把卡通亮面打爆或压得过低。 |
| 152 | <code>        lightColor,</code> | 对 lightColor 做 clamp，避免烘焙环境把卡通亮面打爆或压得过低。 |
| 153 | <code>        float3(lightMinLimit, lightMinLimit, lightMinLimit),</code> | 对 lightColor 做 clamp，避免烘焙环境把卡通亮面打爆或压得过低。 |
| 154 | <code>        float3(lightMaxLimit, lightMaxLimit, lightMaxLimit)</code> | 对 lightColor 做 clamp，避免烘焙环境把卡通亮面打爆或压得过低。 |
| 155 | <code>    );</code> | 对 lightColor 做 clamp，避免烘焙环境把卡通亮面打爆或压得过低。 |
| 156 | <code></code> | 空行，用于分隔亮侧光色与明暗颜色合成。 |
| 157 | <code>    float3 directColor = albedo * lightColor;</code> | 计算亮侧颜色：albedo 乘受限后的 lightColor。 |
| 158 | <code>    float3 shadowBase = shadowColor * lightColor;</code> | 计算阴影基底：由调用方的 shadowColor 乘 lightColor，保持阴影色板主导权。 |
| 159 | <code>    float3 fillMask = saturate(toonFillSH * max(shadowEnvStrength, 0.0f));</code> | 计算回填遮罩：toonFillSH 乘 shadowEnvStrength 后 saturate。 |
| 160 | <code></code> | 空行，用于分隔遮罩计算与最终合成。 |
| 161 | <code>    // 暗侧：SH 只作为回填强度，把阴影色轻微推回固有色；最后限制暗侧不超过亮侧，维持卡通层级。</code> | 说明暗侧合成边界：SH 只做回填强度，暗侧不能超过亮侧。 |
| 162 | <code>    indirectColor = lerp(shadowBase, albedo, fillMask);</code> | 把 shadowBase 按 fillMask 往 albedo 回填，模拟暗部环境提亮。 |
| 163 | <code>    indirectColor = min(indirectColor, directColor);</code> | 用 min 限制 indirectColor 不超过 directColor，维持卡通亮暗层级。 |
| 164 | <code>    color = lerp(indirectColor, directColor, saturate(toonBand));</code> | 用 toonBand 在暗侧与亮侧之间插值，得到最终合成颜色。 |
| 165 | <code>}</code> | 结束可选合成函数。 |
| 166 | <code></code> | 空行，用于分隔函数与包含保护结束。 |
| 167 | <code>#endif</code> | 结束包装文件包含保护。 |

#### BakeryDecodeLightmap.hlsl 顶部 include guard 逐行说明（脱敏）

| 行 | 脱敏代码 | 逐行说明 |
|---|---|---|
| 1 | <code>// 为 Bakery ShaderGraph 工具函数补充包含保护。</code> | 中文维护备注：说明为什么给原 Bakery 解码文件补 include guard。 |
| 2 | <code>// Toon 包装层会 include 本文件，而旧 Bakery Custom Function 节点也可能继续直接引用它；</code> | 中文维护备注：说明为什么给原 Bakery 解码文件补 include guard。 |
| 3 | <code>// 这个守卫用于支持新旧节点短期并存，避免同一编译单元里重复定义函数。</code> | 中文维护备注：说明为什么给原 Bakery 解码文件补 include guard。 |
| 4 | <code>#ifndef BAKERY_DECODE_LIGHTMAP_INCLUDED</code> | include guard 开始，避免重复包含原 Bakery 解码文件。 |
| 5 | <code>#define BAKERY_DECODE_LIGHTMAP_INCLUDED</code> | 定义 include guard 宏。 |
| 6 | <code></code> | 空行，用于分隔守卫与原 Bakery 编译开关。 |
| 7 | <code>//#define NOURP</code> | 保留原 Bakery 的 NOURP 可选编译开关注释，不改变原逻辑。 |
| 8 | <code>//#define SURFACE</code> | 保留原 Bakery 的 SURFACE 可选编译开关注释，不改变原逻辑。 |
| 9 | <code></code> | 原 Bakery 文件头部保留内容。 |
| 10 | <code>#if defined(SURFACE) &amp;&amp; defined(SHADER_TARGET_SURFACE_ANALYSIS)</code> | 原 Bakery 的 SURFACEANALYSIS 条件编译逻辑，记录中仅说明其仍保持原样。 |
| 11 | <code>#define SURFACEANALYSIS</code> | 原 Bakery 的 SURFACEANALYSIS 条件编译逻辑，记录中仅说明其仍保持原样。 |
| 12 | <code>#endif</code> | 原 Bakery 的 SURFACEANALYSIS 条件编译逻辑，记录中仅说明其仍保持原样。 |
### 关键代码

核心不是重写 SH，而是改采样方向后继续走 Bakery：

```hlsl
BakerySH_float(L0,  sampleDirectionWS, lightmapUV, toonLightSH);
BakerySH_float(L0, -sampleDirectionWS, lightmapUV, toonFillSH);
```

方向合成的关键是把环境方向与主光方向合成，再按 lilToon 思路削弱方向性：

```hlsl
toonDirectionWS = BakeryToonSafeNormalize(envDir * envWeight + mainDir * mainWeight, envDir);
sampleDirectionWS = toonDirectionWS * saturate(directionScale);
```

暗部回填的推荐边界是“强度来自 SH，色相来自项目色板”：

```hlsl
float3 fillMask = saturate(toonFillSH * max(shadowEnvStrength, 0.0f));
indirectColor = lerp(shadowBase, albedo, fillMask);
indirectColor = min(indirectColor, directColor);
```

### 参考链接

- [Bakery GPU Lightmapper 官方文档](https://geom.io/bakery/wiki/) - Bakery 光照烘焙与 SH/RNM 背景。
- [lilToon 官方仓库](https://github.com/lilxyzw/lilToon) - Toon SH 正反方向采样与暗部环境回填思路的参考来源。

### 相关记录

- [ASE Shader 架构与 Bakery 光照集成最佳实践](./ase-shader-bakery-integration.md) - 记录 Bakery SH 参数外置、ShaderGraph 封装与 Include 路径实践，本记录在此基础上补充 NPR/Toon 化处理。
- [基于图像的间接光照 IBL](./pbr-image-based-lighting-ibl.md) - 说明 PBR 中 `SampleSH(N) * albedo` 的间接漫反射定位，本记录强调该做法在 Toon 中需要再处理。

### 验证记录

- [2026-07-01] 初次记录。来源为一次 Unity URP + Bakery + ShaderGraph 的实践实现整理；已执行阿卡西 `git pull origin main`、重复检测和写入前结构校验。
- [2026-07-01] 脱敏审查：原始上下文包含真实工程名、本机绝对路径、内部场景资源路径、ShaderGraph 序列化 ID 和截图临时路径；正式记录已统一移除或泛化，仅保留通用文件名、函数名、端口语义和可复用 HLSL 逻辑。
- [2026-07-01] 正确性边界：已基于当前 HLSL 源码逐行读取并记录实现意图，已核对 ShaderGraph 节点语义配置；尚未在 Unity 编辑器中完成重新导入、ShaderGraph 编译或画面对比，因此状态标记为“⚠️ 待验证”。

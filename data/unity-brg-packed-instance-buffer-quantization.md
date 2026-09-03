# Unity BatchRendererGroup（BRG）逐株 Buffer 的 32 字节压缩与量化应用二进制接口（ABI）

**标签**：#unity #experience #rendering #performance #memory #hlsl #culling
**来源**：工程实践抽象 - Unity BRG 实例数据压缩与 CPU/GPU 协议设计
**收录日期**：2026-08-26
**更新日期**：2026-09-03
**状态**：📘 有效
**可信度**：⭐⭐⭐⭐（32 B 位级 ABI，以及本文列明的 Editor D3D11 Buffer 回读、非法输入与失败原子性、Forward 前景 Mask 正向对照已有直接运行证据；历史 Bounds 高 16 位错误解包实验只保留结果摘要而没有保存注入代码差异，不作为可公开复核证据或本可信度的依据；冻结源码显示最终 Packed Record 入口尚未独立拒绝负最大风摆，因此不把生产入口整体称为已验证；ShadowCaster、DepthOnly、DepthNormals 仅确认静态共用解码与世界形变代码链）
**适用版本**：Unity 2022.3.62f3、Windows Editor Direct3D11、Unity.Mathematics 1.3.2、BatchRendererGroup 与 DOTS Instancing；其它 Unity 版本、图形后端或 Half 转换实现需重新验证寻址和位级兼容性

---

### 概要

BatchRendererGroup（BRG）是 Unity 提供的低层批量渲染接口；本文讨论它所消费的逐实例数据。这里的应用二进制接口（ABI）不是操作系统 ABI，而是 C# 生产者与 HLSL 消费者之间必须逐字一致的 32 字节 Buffer 契约。TRS 指 Translation、Rotation、Scale，即位移、旋转和缩放。

当实例系统已把变换约束为有限、无剪切、非镜像、正数统一缩放时，不必为每株保存 `ObjectToWorld`、`WorldToObject` 和两组 `float4` 参数。本文用三个 IEEE 754 binary32（普通 32 位浮点数）保存世界坐标；用 smallest-three 方法省略单位四元数绝对值最大的分量，把其余三项与省略项索引压入 `10:10:10:2`；把部分连续标量存为 IEEE 754 binary16（16 位半精度浮点数）；再把 `[0,1]` 随机相位线性映射为 UNorm16（16 位无符号归一化整数）。身份和地址继续使用整数位段，最终使固定逐株区从 `128 B` 收敛到 `32 B`。

这项优化的难点不是位运算本身，而是建立完整协议：C# 写入与 HLSL 读取必须共享同一 ABI；CPU 剔除必须使用 GPU 实际恢复后的量化 TRS；影响剔除半径的量化值必须保守包络；批量预览、Cell 变换和 Floating Origin 更新必须先验证完整候选再触碰已发布状态；不可表达输入必须明确失败。

本文将这项知识标为“📘 有效”：位级 ABI 与下文列出的 Editor D3D11 路径有直接运行证据，冻结源码也足以复核字段和寻址链；但生产入口仍有明确边界，尤其是最终 Packed Record 生产者尚未独立拒绝负最大风摆。Forward 正向对照只证明单株合成夹具的 BRG 与普通 GameObject 前景轮廓在当前门限内一致；它不证明 RGB 光照等价，也不能替代缺少可复核代码差异的历史故障注入。当前证据支持“逻辑 GraphicsBuffer 请求大小、完整回读长度和全量上传载荷下降”，不支持“Quest 帧时间、GPU 时间、功耗或物理显存一定下降”。新 Shader 用额外的 Half 解码、四元数恢复和向量旋转换取更小记录，带宽与 ALU 的净收益必须在目标设备上另做 A/B。

## 一、问题与证据边界

旧布局为每株保存两张 `float3x4` 矩阵、实例参数和光照寻址参数：

```text
48 B ObjectToWorld
+ 48 B WorldToObject
+ 16 B Instance Parameters
+ 16 B Lighting Address Parameters
= 128 B / instance
```

这条表达能覆盖一般矩阵，但在数据模型已经只允许“旋转 + 正数统一缩放 + 位移”时存在重复信息：逆矩阵可以从同一 TRS 推导，法线只需要旋转，模式和索引也不需要使用浮点向量保存。

本文的直接验证绑定到 Unity `2022.3.62f3`、Windows Editor Direct3D11 和 Unity.Mathematics `1.3.2`，项目 Build Target 为 Android。32 B 布局、GraphicsBuffer 完整回读和 Forward 前景 Mask 正向对照已有直接证据；历史故障注入没有保留代码差异，只能作为不可公开复核的归档工程观察。ShadowCaster、DepthOnly 与 DepthNormals 只完成了共用解码和世界形变入口的静态核对。Quest Vulkan、设备帧时、带宽、功耗和物理显存变化尚未验证。

本文中的**运行时 Cell**是一份场景植被资产及其独立运行资源的所有权边界，**Heap** 是 Cell 内的空间分块，**StableGuid** 是实例在所属场景资产内的持久身份；它们只用于解释记录地址与发布边界，不是 32 B 位布局本身的一部分。

本文中的 **BRG Metadata** 是 C# 为某个 Shader 属性登记的 32 位寻址描述：低 31 位保存该属性在共享 GPU Buffer 中的基址，最高位表示 Unity 是否还要自动追加当前可见实例索引对应的逐株偏移。它不是材质说明文本；一旦最高位、基址、记录步长或 Shader 侧二次偏移约定不一致，Shader 就会读到另一株或另一段数据。

本文的参考实现绑定到匿名工程快照：Git 提交 `f0fef16849cfb8945e9928e5219a140ee250fcf4`，植被模块 Git tree `4700f76e0b087fe3935c06e660ee732bbf55c87a`。持有该快照的读者可按下表复核；没有源码访问权的读者只能把它视为具名工程案例，不能独立重跑实现观察。

| 核心主张 | 模块内相对入口 | 证据类型 |
|---|---|---|
| 32 B 布局、偏移、smallest-three 与 Half 编码 | `Runtime/Rendering/VegetationRenderDataLayout.cs`：`PackedVegetationInstanceData`、`PackRotation`、`QuantizeHalfValue` | 冻结源码与位级测试定义 |
| 全量上传、单株覆写和光照段地址 | `Runtime/Rendering/VegetationSceneBatch.cs`：`UploadInstanceData`、`BuildPackedInstanceData`、`UploadPackedInstanceData` | 冻结源码静态核对 |
| HLSL 以 32 B 步长解码并区分逐株/共享 Metadata | `Shaders/MiniatureWorldVegetationInput.hlsl`：`VegetationLoadInstanceData`、`VegetationLoadStaticLightColor`、`VegetationEvaluateStoredBakerySh` | 冻结源码静态核对 |
| CPU 使用量化后 TRS 构建剔除数组 | `Runtime/Rendering/VegetationSceneBatch.cs`：CPU 剔除数组构建路径与 `QuantizeWorldMatrix` 调用 | 冻结源码静态核对 |
| 金样、布局与 Shader 合同 | `Tests/EditMode/Rendering/VegetationRenderDataLayoutTests.cs`、`VegetationShaderTests.cs` | 测试定义存在；具体运行结果按第九节和验证记录的证据边界理解 |
| 两组 D3D11 Buffer 分配与完整回读 | `Generated/Reports/BufferCompression/Current/IndependentRuntimeEvidence_Current.json` | 归档的直接运行记录；包含 Unity 版本、图形 API、实例/Heap 计数、布局字节、底层分配字节与回读长度 |
| ABI、非法输入与失败原子性用例 | `Generated/Reports/EditorClosure/FullTestRunner_EditMode_Current.xml` 中 `PackedMatrix_RoundTripsUnity2022DotsOrdering`、`SceneBatch_EditModeSupportsSceneMaskAndManualTransformPreview` | 归档的直接运行结果；测试行为仍需结合对应测试源码理解 |
| Forward 前景 Mask 正向对照 | `Tests/PlayMode/VegetationBrgSmokeTests.cs`、`Generated/Reports/EditorClosure/FullTestRunner_PlayMode_Current.xml`、`Generated/Reports/BufferCompression/Current/BufferCompressionComparison.md` | 冻结测试定义与归档的 D3D11 正向运行结果；历史故障注入只在报告中留下摘要，未保留注入代码差异，不属于可公开复核证据 |

## 二、压缩成立的前置契约

### 2.1 可表达变换

32 B 方案只接受：

- 世界位置三个分量均为有限 `float32`。
- 三个矩阵轴长度近似相等：`maxScale - minScale <= maxScale × 0.001`。
- 缩放大于零，编码为 Half 后仍不能下溢为零。
- 三个归一化轴的两两点积绝对值最大不超过 `0.001`，不含剪切。
- `dot(cross(x,y),z) >= 0.999`，保持正手性且不含镜像。
- 旋转可以恢复为有限单位四元数。

非统一缩放、镜像和剪切不是“压缩误差”，而是格式无法表达的输入。正确处理方式是在 CPU 写入前拒绝，而不是让 Shader 静默近似。

这里的相对轴长差 `0.001`、轴点积绝对值 `0.001` 和手性点积 `0.999` 都是当前工程用来识别“足够接近统一、正交、正手”的验收阈值，不是 32 B ABI 的数学定律。数学前提分别是三轴等长、两两正交和正手；浮点生产者必须自行选择并冻结识别容差。调整这些阈值会改变合法输入域，采用者应把变更纳入版本与回归测试。第四节的旋转误差 `< 0.25°` 同样只是当前工程门禁，不是 smallest-three 编码的解析最坏误差上界。

### 2.2 字段选择原则

| 数据 | 表达 | 原因 |
|---|---|---|
| 世界位置 | `float3` | 大世界坐标对绝对误差敏感；不纳入该 ABI 的量化字段 |
| 世界旋转 | smallest-three `10:10:10:2` | 单个 `uint` 可恢复单位四元数 |
| 正统一缩放 | IEEE 754 binary16 位布局；编码固定为 Unity.Mathematics 1.3.2 `math.f32tof16` | 动态范围足够时以显式上下界换容量 |
| 随机相位 | UNorm16 | 语义天然位于 `[0,1]` |
| 最大风摆幅值与局部 Bounds 连续量 | IEEE 754 binary16 位布局；编码固定为 Unity.Mathematics 1.3.2 `math.f32tof16` | 风摆字段是非负世界空间位移幅值；有符号 Bounds 参数另按各自语义校验 |
| Heap 索引 | UInt16 | 保持整数精确；超出格式或当前逻辑 Heap 数量时失败 |
| 光照模式与记录索引 | 1 bit + 31 bit | 不用浮点表达地址；越界明确失败 |

“位置保留 float32”只表示该 ABI 没有新增位置量化误差，不表示突破了 float32 或 Floating Origin 本身的精度上限。

## 三、32 字节 ABI

一株固定为 8 个 `uint`：

| 字节范围 | uint | 内容 |
|---|---:|---|
| 0–11 | 0–2 | 世界位置 `float3`，按位解释为三个 float32 |
| 12–15 | 3 | smallest-three 旋转：三个 10 位分量 + 2 位省略分量索引 |
| 16–19 | 4 | 低 16 位正统一缩放 Half；高 16 位随机相位 UNorm16 |
| 20–23 | 5 | 低 16 位最大风摆 Half，单位为世界空间长度；高 16 位对象空间 Bounds 最低 Y 的 Half |
| 24–27 | 6 | 低 16 位对象空间 Bounds 高度倒数 Half，单位为对象空间长度的倒数；高 16 位 HeapIndex |
| 28–31 | 7 | 最高位光照模式；低 31 位对应稀疏光照表的记录索引 |

旋转字的规范位序为：`a = bits[0..9]`、`b = bits[10..19]`、`c = bits[20..29]`、`omitted = bits[30..31]`。`a/b/c` 始终按四元数 `x,y,z,w` 的原顺序保存，跳过 `omitted` 指定的一个分量。

光照模式位的规范映射是 `0 = StaticLightColor`、`1 = StaticBakerySh`。低 31 位索引总是解释为当前模式对应稀疏表中的记录号，不能跨表复用。

下面的固定输入与 8 个期望 uint 是当前 ABI 的最小金样；其它语言或工具链只有逐字得到同一输出，才算字节兼容：

```text
position              = (1, -2, 3.5)
rotation              = identity
uniformScale          = 1
random/maxWind/minY/invHeight = (0.5, 0.25, -1, 2)
lightingMode          = StaticBakerySh
heapIndex             = 7
lightingRecordIndex   = 9

expected uint[8] =
  3F800000 C0000000 40600000 E0080200
  80003C00 BC003400 00074000 80000009
```

ABI 不能只靠注释维持。最低门禁应同时冻结：

1. C# 结构尺寸必须为 32 B。
2. 每个字段偏移和位段必须有固定输入的 8 个 `uint` 金样。
3. C# 编码后必须能在 CPU 参考解码中恢复。
4. HLSL 必须用相同的 32 B stride、Half 位序、旋转分量顺序和索引掩码。
5. 至少一个真实 SRP/BRG 像素门禁必须记录渲染目标、比较区域、前景判定和差异指标；若用故障注入证明门禁灵敏度，还必须保存可复算的代码差异。当前归档只满足正向对照，历史负向注入因缺少代码差异而不计入该门禁。

若格式继续演进，应增加显式 ABI 版本或由同一 schema 生成 C#/HLSL 常量，避免两端靠人工同步。

## 四、旋转、Half 与索引如何编码

### 4.1 Smallest-three 旋转

对归一化四元数：

1. 从 `x` 开始，用严格 `>` 依次比较 `|y|、|z|、|w|`，找出绝对值最大的分量并用 2 bit 保存其索引；相等时保留较早的 `x→y→z→w` 分量。
2. 若该分量为负，则整体取反。四元数 `q` 与 `-q` 表示同一旋转，因此不改变语义。
3. 省略最大分量；其余三个分量必定位于 `[-1/√2, +1/√2]`。
4. 其余分量按 `x,y,z,w` 原顺序跳过省略项，依次成为 `a/b/c`。令 `R=1/√2`，每个分量按 `Mathf.RoundToInt(clamp01((v/R × 0.5)+0.5) × 1023)` 映射到 10 位；跨语言编码器必须复现该舍入语义。
5. 解码时恢复三个分量，并计算：

```text
missing = sqrt(max(0, 1 - a² - b² - c²))
```

6. 单个 10 位值按 `v = (((q/1023)×2)-1)×R` 恢复。按 2 bit 索引把非负 `missing` 放回原位置，最后再次归一化。

这里的字节兼容输入从“已经提取并归一化的有限四元数”开始；Unity 世界矩阵如何经 `LookRotation` 得到该四元数属于生产者的变换提取协议，不属于 32 B 字段本身。需要在非 Unity 工具中从矩阵直接生成完全相同字节时，必须同时复刻生产者的矩阵容差、轴归一化和四元数提取，不能只实现上述位打包。

为冻结合法输入的数值口径，`R` 使用 binary32 位型 `0x3F3504F3`（显示值约 `0.70710677`）；归一化后的分量、除法、乘法和加法都按 binary32、按上述书写顺序求值。`Mathf.RoundToInt` 的 midpoint 规则是 round-to-nearest、ties-to-even。兼容编码器不能把它替换成 ties-away-from-zero、十进制舍入或更高精度计算后只在末尾转 float32。

旋转样本由冻结测试中的 `System.Random(0x51A7C0DE)` 产生。每株依次调用三次 `NextDouble()`，立即转为 binary32 的 `u1/u2/u3`，再按下式构造单位四元数：

```text
x = sqrt(1-u1) × sin(2πu2)
y = sqrt(1-u1) × cos(2πu2)
z = sqrt(u1)   × sin(2πu3)
w = sqrt(u1)   × cos(2πu3)
```

这是用三个 `[0,1)` 均匀变量生成 SO(3) 均匀旋转的四元数方法；测试按随机序列连续生成 10,000 株，没有筛选或重采样。角误差的操作定义是 Unity 2022.3 的 `Quaternion.Angle(source, decoded)`，单位为度：它把 `q` 与 `-q` 视为同一姿态，测量两姿态之间的最短夹角，概念上等价于 `2×acos(clamp(|dot(q,decoded)|,0,1))` 再转换为度。

归档输出记录的样本最大角误差为 `0.197823°`，低于当前工程验收门限 `< 0.25°`。这只是上述固定 PRNG、binary32 数学路径和 10,000 株样本的观测最大值，不是数学最坏误差证明；跨运行时复现实验还必须保持 Unity 版本及其 `System.Random`、`Mathf` 和 `Quaternion.Angle` 行为一致，或直接冻结生成后的样本语料。

### 4.2 IEEE 754 binary16 存储、规范编码与 UNorm16

本文把 16 位连续标量存入 IEEE 754 binary16 的符号位、指数位和尾数字段；文中的 “Half” 仅是这一 16 位存储布局的简称。binary16 规定结果如何解释，但不单独规定本 ABI 从 binary32 产生这些位的全部转换步骤。字节兼容的规范编码器固定为 Unity.Mathematics 1.3.2 的 `math.f32tof16`；不能用平台自带 `half` 转换或泛称的“IEEE 默认转换”替代。

- Half 合法输入必须是 binary32 有限值且绝对值不超过 `65504`；NaN、Infinity 和超界值在转换前失败。
- 语义上必须大于零的缩放和 Bounds 高度倒数先拒绝 `value <= 0`；转换后若 binary16 位模式表示零，也必须失败。
- 最大风摆字段表示非负世界空间位移幅值：零合法，负值不属于 ABI 输入域。ABI 规范要求最终 Packed Record 生产者在打包前拒绝负值；当前通用生产入口尚未形成这一独立硬门禁，因此“规范已定义”不等于“该入口已闭环”。
- Bounds 最低点允许有限负值；有符号字段保留 binary16 符号位，包括 `-0 → 0x8000`。
- 随机相位接受有限 binary32，先钳制到 `[0,1]`，再以 binary32 计算 `value × 65535`，最后用 round-to-nearest、ties-to-even 编为 UNorm16；解码为 `q / 65535.0f`。有限超界值饱和是此字段的专门规则，不适用于其它字段。当前内部调用会产生有限 `[0,1]` 值，但打包帮助函数本身没有独立的非有限门禁；抽取为公共入口前仍需补齐。
- GPU 解码一个 `uint` 中的两个 binary16 值时，分别读取低 16 位和右移后的高 16 位；不能假设一次转换会自动返回两个值。

对合法有限输入，Unity.Mathematics 1.3.2 `math.f32tof16` 按以下 binary32/uint 位算法产生低 16 位：

```text
ux  = asuint(x)
mag = ux & 0x7FFFF000
h   = (asuint(min(asfloat(mag) * asfloat(0x07800000),
                      asfloat(0x4D77FF00))) + 0x1000) >> 13
halfBits = (h | ((ux & 0x80000FFF) >> 16)) & 0xFFFF
```

这条算法是本 ABI 的编码规范源。它输出可按 binary16 解释的位模式，并保留 signed zero 与 binary16 次正规数。兼容向量包括 `+0 → 0000`、`-0 → 8000`、`5.96046448e-08f → 0001`、最大次正规数 `0.000060975552f → 03FF`、最小正常数 `0.00006103515625f → 0400`、`123.4f → 57B6` 和 `65504f → 7BFF`。

在 `1.0` 与下一 binary16 值 `1.0009765625` 的精确 binary32 中点，规范编码结果是 `1.00048828125f → 3C01`，不能擅自替换为 ties-to-even 会得到的 `3C00`。CPU 参考解码固定使用同版本 `math.f16tof32`，HLSL 使用 `f16tof32` 解释低 16 位。移动 GPU 是否把次正规数 flush-to-zero 尚需真机验证；工程采用时可以把合法下界提高到最小正常 binary16，或增加目标设备边界测试。

### 4.3 整数索引

HeapIndex 与稀疏光照记录索引必须保持整数语义：

- 格式容量只是 HeapIndex `0..65535` 和 31 位光照记录索引；运行时还必须满足 `HeapIndex < logicalHeapCount`，以及 `LightingRecordIndex < 当前模式对应稀疏表的 logicalCount`。
- 最高位只表示两种静态光照模式。
- 任一越界都在 Buffer 写入前失败，禁止浮点取整、Infinity 或回绕污染 GPU 地址。

参考实现不是只检查位宽：布局从 SceneAsset 的实际 Heap/两种模式计数生成；上传前逐 Heap 验证每种 payload 的精确字节数和内容摘要；记录索引由对应全局稀疏表的递增游标产生。因此可绘制记录不会指向哨兵或另一张表。所有 Offset、乘法、加法和 16 B 对齐使用 checked Int32；`TotalBytes < 2^31` 同时保证 Metadata 低 31 位可保存基址，并使 `base + index×stride + loadWidth` 保持在已分配 Buffer 内。超过这一单 Buffer 上限时应分页，不能依赖 uint 回绕；ConstantBuffer 路径还必须额外满足设备窗口上限。

## 五、C# 到 HLSL 的端到端数据流

```text
SceneAsset 中的高精度局部 TRS
  → 与运行时 Cell Transform 和 Floating Origin 组合成最终世界矩阵
  → CPU 验证有限、正统一缩放、无剪切、非镜像
  → 编码为 8 uint / 32 B
  → 按全局 GPU Slot 写入共享 GraphicsBuffer
  → BRG Metadata 保留 PerInstanceDataBit，并声明逐株数据基址
  → HLSL 按 32 B stride 做两次 uint4 读取
  → 恢复 position / rotation / scale / wind / Bounds / Heap / lighting index
  → 直接由压缩 TRS 构造世界顶点；法线只应用单位四元数旋转
  → Forward 使用该链生成已通过单株前景 Mask 正向对照的结果；Depth、DepthNormals 与 Shadow 共用相同解码和世界形变代码入口
```

证据类型必须分开理解：Forward 已在固定相机和冻结非零风下完成正常解码的前景 Mask 正向对照；ShadowCaster、DepthOnly 和 DepthNormals 只确认静态调用到同一 Packed Record 解码与世界形变链。静态共链可以降低实现漂移风险，但不等于这三个 Pass 已完成像素等价或故障注入验证。历史 Forward 故障注入只剩结果摘要而没有代码差异，因此也不能被提升为当前可复核的负向门禁。

Shader 不再先把顶点变到世界空间、完成风动后再依赖 `WorldToObject` 返回对象空间。它直接输出形变后的世界位置，从而让删除逆矩阵成为真正的数据流简化，而不只是压缩存储。

普通 GameObject 回退路径仍可使用 Unity 对象矩阵和经典实例化属性。BRG 与普通 GO 的代码分支必须保持清晰，不能让 32 B 自定义 stride 被 Unity 的默认 `float4` 或矩阵步长解释。

当前 DOTS Metadata 的逐株寻址契约为：

```text
metadata = 0x80000000 | PackedInstanceBase
instanceIndex = visibleInstances 当前元素 = GlobalSlot
address = (metadata & 0x7FFFFFFF) + instanceIndex × 32
```

C# 只为 Packed Instance Metadata 设置 `PerInstanceDataBit`。HLSL 取得原始 Metadata 后调用 Unity 的 `ComputeDOTSInstanceDataAddress(metadata, 32)`；该帮助函数清除最高位，并且只在最高位存在时追加一次 `GetDOTSInstanceIndex() × 32`。剔除 Scatter 写入 `visibleInstances` 的正是与上传展开顺序相同的全局实例数组下标，因此它与 GlobalSlot 数值一致，Shader 不再手动追加第二次 Slot 偏移。

例如 PackedInstanceBase 为 `96`、GlobalSlot 为 `5` 时，Metadata 为 `0x80000060`，Unity 帮助函数得到的记录地址为 `96 + 5×32 = 256`；随后两次读取覆盖 `[256,271]` 与 `[272,287]`。若再手工追加 Slot，会错误跳到 `416`。

风场、每 Heap 量化表和两张稀疏光照表的 Metadata 都不设置最高位；HLSL 以 stride `0` 取得共享基址，再分别追加 `HeapIndex×128`、`LightingRecordIndex×8` 或 `LightingRecordIndex×20`。这同时冻结了“哪些地址由 Unity 自动按实例偏移、哪些地址由 Shader 按记录索引偏移”的边界。

ABI 的规范单位是上述顺序的 8 个 32 位字；导出连续原始字节时约定 little-endian。当前字节回读只在 Windows Editor 验证；目标 Android/Quest 架构同为 little-endian，但本文没有完成其运行时闭环。Big-endian CPU/GPU 后端不属于当前适用范围。

## 六、多 Heap 与稀疏光照如何寻址

一个已加载运行时 Cell 仍使用单 Batch、单 Buffer。布局顺序为：

```text
64 B 合法零地址哨兵
16 B Cell Wind
16 B Cell Wind Spatial
32 B × allocatedInstanceCount Packed Instance Records
128 B × allocatedHeapCount Lighting Quantization
8 B × allocatedStaticColorCount
16 B 对齐
20 B × allocatedBakeryShCount
16 B 总对齐
```

其中 `allocatedX = max(1, logicalX)`。即使场景或某张稀疏表为空，也为 Metadata 保留一个合法哨兵记录；逻辑计数仍为零，哨兵不会生成 DrawCommand。

每 Heap 的 `128 B Lighting Quantization` 不是逐株光照，也不是第二份实例记录。它由八个 `float4` 组成：`StaticLightColor` 的最小值/步长一对，以及 Bakery SH 的 `Ar`、`Ag`、`Ab` 三组最小值/步长，共四对、每对 `32 B`。同一 Heap 内的逐株压缩光照记录用这些参数恢复到浮点值；因此它是 Heap 级解码字典，开销随 Heap 数量增长。

两种逐株光照模式只保存其一，并通过 32 B 实例记录末尾的模式位和记录索引寻址：

- `StaticLightColor` 在烘焙阶段把采样到的 L2 探针评估成最终 RGB 辐照度，每株压缩为 `8 B`；运行时不再按顶点法线求 SH，代价较低，但失去法线方向变化。
- `StaticBakerySh` 每株保存项目 Bakery Probe 路径使用的 `unity_SHAr/Ag/Ab` 压缩表达，共 `20 B`；运行时再结合顶点法线做 Geomerics 方向评估。它保留方向响应，但不是保存完整九系数 L2。

两张表是按实际模式计数的稀疏表：一株不会同时占用 `8 B + 20 B`。某种模式没有逻辑记录时，布局仍因 `max(1,S)` 或 `max(1,C)` 保留一个不可绘制的哨兵槽。

令 `A16(x)` 表示向上对齐到 16 字节，`N/H/C/S` 分别为实例、Heap、StaticLightColor 与 StaticBakerySh 记录数，则：

```text
bytes = A16(
          A16(96 + 32×max(1,N) + 128×max(1,H) + 8×max(1,C))
          + 20×max(1,S))
```

旧布局只把 `32×max(1,N)` 换成 `128×max(1,N)`。由于差值本身是 16 字节整数倍，在其它数量相同的情况下，总逻辑分配精确减少：

```text
96 × max(1,N) bytes
```

总降幅通常小于 75%，因为 96 B 头部、每 Heap 128 B 量化表和 8 B/20 B 稀疏光照表没有缩小。Heap 越多，每 Heap 固定开销占比越高。

归档的两组 8,192 株 D3D11 回读都只有静态颜色记录，因此 `N=8192、C=8192、S=0`；区别是 `H=50` 与 `H=1024`。冻结 SceneAsset 中的静态颜色 payload 也分别合计为 `65,536 B = 8192×8 B`，Bakery SH payload 为零。由此可以完整复算绝对字节数：

```text
样本 A：N=8192, H=50, C=8192, S=0
32 B 布局 = A16(96 + 262144 + 6400 + 65536 + 20) = 334208 B
128 B 旧布局 = A16(96 + 1048576 + 6400 + 65536 + 20) = 1120640 B

样本 B：N=8192, H=1024, C=8192, S=0
32 B 布局 = A16(96 + 262144 + 131072 + 65536 + 20) = 458880 B
128 B 旧布局 = A16(96 + 1048576 + 131072 + 65536 + 20) = 1245312 B
```

末尾的 `20 B` 是 `S=0` 时仍保留的单个 Bakery SH 哨兵槽；最终 `A16` 分别加入 `12 B` 对齐填充。两组实例段都从 `1,048,576 B` 降到 `262,144 B`，所以在其它段不变时精确减少 `786,432 B`。压缩后的 `334,208 B` 与 `458,880 B` 同时匹配布局计算、底层 `GraphicsBuffer.count×stride` 和完整回读长度；压缩前总量来自相同计数和冻结的 128 B 旧布局，不是同一会话中的帧性能 A/B。

### 多 Heap 地址链

```text
按 SceneAsset 当前 Heap 顺序扫描
  → 前序 Heap 实例总数形成当前 HeapBase
  → GlobalSlot = HeapBase + Heap 内 RuntimeIndex
  → PackedRecordAddress = PackedBase + GlobalSlot × 32
  → 记录中的 HeapIndex 定位该 Heap 的 128 B 量化表
  → LightingMode + LightingRecordIndex 定位两张全局稀疏光照表之一
```

HeapBase 不需要序列化；它是当前加载快照的派生量。`StableGuid` 才是持久实例身份，GlobalSlot、HeapBase 和 RuntimeIndex 都不能跨重编译或重装载保存为外部引用。

## 七、CPU 剔除必须使用量化后的真值

若 GPU 使用量化后旋转和缩放，而 CPU 仍用原始矩阵计算包围球与 LOD，实例在视锥或阈值边缘可能出现单帧消失。参考策略是：

1. 每次都从权威高精度矩阵重新编码，禁止对已经量化的结果反复往返。
2. CPU 立即用同一编码规则恢复旋转和缩放。
3. 剔除中心、半径、LOD 中心和 LOD 尺寸都使用恢复后的 TRS。
4. 对合法的非负最大风摆幅值，剔除余量取 `max(source, decoded)`；该公式不能套用于允许负值的 Bounds 参数。
5. Heap Bounds 保留编译结果，并把量化后实例球并入，只允许保守扩展，不允许缩小工作集。

风摆余量成立还依赖 Shader 形变契约。风向必须归一化，`heightMask` 必须限制在 `[0,1]`，Cell 请求幅值也只能与实例上限取最小值；于是每个顶点的风摆满足：

```text
|deltaWorld(vertex)|
  = |sin(phase)| × min(max(cellAmplitude, 0), decodedMaxWind) × heightMask
  <= decodedMaxWind
```

`BoundsMinimumY` 与 `BoundsInverseHeight` 只负责产生高度权重，不能让权重超过 1。若 Shader 新增其它顶点位移，它必须获得独立保守余量，不能借用 `maximumWindDisplacement` 的结论。

这套做法会在全量上传与剔除快照构建时重复提取和量化 TRS，换来两端一致和失败事务。它属于加载/Rebase 的低频 CPU 成本；当前没有 Profile 数据证明其尖峰可以忽略。

## 八、ABI 规范与尚未闭环的生产入口

32 B ABI 不规定编辑器预览、Cell 管理或资源卸载的完整生命周期。以下四条是任何生产者采用该 ABI 时必须满足的规范，不是对当前所有入口已经完成验证的陈述。当前实现已覆盖完整记录覆写和候选发布流程，但最大风摆的最终通用 Packed Record 生产入口仍缺少独立的非负校验；因此字段语义已经规范化，这个入口的失败闭环尚未完成。

1. 始终从权威高精度 TRS 构建完整候选，禁止读取旧 GPU 记录后二次量化。
2. 单株更新覆写完整 32 B；批量更新先验证全部记录和对应 CPU 剔除数据，任一记录失败时不触碰已发布 Buffer。
3. Cell Transform 或 Floating Origin 改变时，先完成量化候选 CPU Snapshot 和完整候选 Buffer，二者成功后再切换公开状态。
4. 原地 Patch 需要额外处理在途 GPU 工作；严格一致性场景使用 GPU Fence、双 Buffer/世代切换或独立预览 Batch。

StableGuid 是持久身份，GPU Slot 只是当前加载快照中的地址。Heap 失活也不代表其记录已经紧凑或释放，因此本文的字节收益只描述已分配 Cell Buffer 和全量上传载荷。运行时 Cell/Heap 的完整生命周期见[统一 BRG 架构](./unity-vegetation-unified-brg-architecture.md)，编辑预览和作者提交事务见[植被 Painter 作者工作流与事务设计](./unity-vegetation-painter-authoring-transaction-workflow.md)。

## 九、实验方法、观察与边界

本节把证据分为四类：**直接运行**表示归档结果记录了测试或 GPU 操作实际执行；**冻结源码静态观察**表示结论来自前述提交中的代码与资产，未在本文重新运行；**派生计算**表示输入计数、公式和对齐规则可从直接运行记录与冻结源码复算，但对应结果不是一次独立运行观察；**生产规范**表示采用该 ABI 必须满足的要求，不能当作当前入口已经实现的事实。只剩结果摘要、缺少输入或代码差异的历史实验另标为“归档工程观察”，不属于上述可复核证据，也不参与可信度判断。

| 主张 | 证据类型 | 方法与可追溯入口 | 结果 | 边界 |
|---|---|---|---|---|
| 固定逐株记录从 128 B 降为 32 B | 直接运行 + 冻结源码静态观察 | `PackedMatrix_RoundTripsUnity2022DotsOrdering` 执行结构尺寸与 8 个 `uint` 金样断言；冻结布局定义给出新旧字段宽度 | 归档用例通过；固定逐株区减少 `96 B`，金样逐字匹配 | 只证明 ABI 与逻辑字节，不证明设备帧耗 |
| 总 Buffer 字节随实例段缩小 | 直接运行 + 派生计算 | D3D11 运行记录直接创建两份 SceneBatch，比较 `Layout.TotalBytes`、`count×stride` 和完整回读长度；压缩前值按冻结 128 B 布局与同一 `N/H/C/S` 派生复算 | 样本 A 的压缩后布局、分配与回读均为 `334,208 B`；样本 B 三者均为 `458,880 B`。同计数下压缩前分别为 `1,120,640 B`、`1,245,312 B`；两组实例段均减少 `786,432 B` | 第六节已展开全部计数和对齐。压缩前值不是同会话运行观察；回读长度不等于驱动物理显存、分配器保留或整进程 PSS（Proportional Set Size，按共享页比例分摊后的进程内存） |
| 旋转量化误差低于当前样本门限 | 直接运行 | `PackedMatrix_RoundTripsUnity2022DotsOrdering` 使用 `System.Random(0x51A7C0DE)`，按第四节公式生成 10,000 个 SO(3) 均匀样本；编码后解码，并以 `Quaternion.Angle` 的最短姿态夹角统计最大值 | 归档输出的观测最大角误差为 `0.197823°`，低于当前工程验收门限 `0.25°` | 样本最大值不是数学最坏误差证明；门限不是 ABI 数学定律；跨运行时复现需冻结 PRNG 与 Unity 数学行为 |
| 已覆盖的非法输入会失败；指定失败事务不产生半更新 | 直接运行 | 同一 Packed Matrix 用例覆盖 Half 上溢、正值字段 Half 下溢、非统一缩放、镜像、等长剪切与超出 UInt16 的 HeapIndex；`SceneBatch_EditModeSupportsSceneMaskAndManualTransformPreview` 覆盖批量预览第二株非法、过大/过小 Cell 缩放与 NaN Origin | 两个归档用例均通过；前一组输入抛出预期异常，后一组失败后完整 GPU Buffer、预览 Heap、Cell/Origin 字段及 SceneAsset 的测试快照保持调用前值 | 没有覆盖负最大风摆，也没有证明所有生产入口、所有索引边界和并发 GPU 时序都具有相同失败原子性；这里不使用笼统的“已发布候选不变”外推 |
| 最大风摆应保持非负幅值语义 | 冻结源码静态观察 + 生产规范 | 静态对照作者输入、Prototype 初始化、Packed Record 构造器和 Shader 使用点 | 上游作者输入与 Prototype 初始化会钳制为非负；Shader 读取后再次 `max(...,0)`；最终通用 Half 打包入口只检查有限值与可表示范围，没有独立拒绝负数 | 没有可追溯运行证据证明迁移或损坏的负值在最终入口被拒绝；补齐该门禁前，本项不是生产闭环 |
| Forward 正向对照约束单株几何轮廓 | 直接运行 + 冻结源码静态观察 | 启用相机把正常 SRP 帧写入 `192×192` 的线性 ARGB32 RenderTexture；比较区域是整张颜色缓冲。先关闭 BRG 取得同机位空背景，再以同一 Mesh、Material、相机和实例变换渲染普通 MeshRenderer。每条路径的像素若 `max(|ΔR|,|ΔG|,|ΔB|) > 8`（Color32 通道单位）就记为前景；差异是两个二值前景 Mask 异或后的像素总数 | 正确解码时 BRG 与 GO 各有 `192` 个前景像素，Mask 差异为 `2` 个像素；允许差异为 `max(8, ceil(BRG前景数×5%))`，本样本即 `10` 个像素 | 只证明该单株三角形夹具、冻结非零风和 Forward Pass 下，两条顶点变换产生的前景覆盖在当前工程门限内一致；不比较 RGB 光照，不证明一般 Mesh、多 Heap、地址位段或其它 Pass 正确 |
| 历史 Forward 负向注入 | 归档工程观察 | 归档摘要称曾临时让 Bounds 最低 Y 所在的打包字高 16 位发生错误解包，再运行同一前景 Mask 门禁；这只说明注入属于字内位段选择/解码错误，不足以把它称为 Metadata、stride 或 Slot 的寻址错误。现存白名单证据没有保存当时的 HLSL/C# 代码差异，无法判断高 16 位具体被读成哪个位段 | 摘要记载 Mask 差异从 `2` 增至 `22` 并触发失败 | 因注入实现不可复算，本项不属于直接证据、不参与可信度，也不能证明门禁对任意 ABI 位段或寻址错误都敏感 |

未冻结动态输入的同机位截图只能发现明显外观回归，不能证明像素等价。正向对照要升级为具有灵敏度证据的视觉门禁，不仅要固定动态输入，还必须保存受控错误及其代码差异，证明错误确实能被观察到；当前历史负向注入不满足后一项。

## 十、不能从当前证据推出什么

- 未做压缩前后同协议的 CPU 上传、首帧、稳定帧、GC Alloc 或 GPU 帧时间 A/B。
- 未在 Quest Vulkan 或 Android Player 上验证 Shader、Half 次正规数、带宽、ALU、功耗和热降频。
- 更小的 `buffer.count × stride` 不等于驱动物理显存一定按相同比例下降。
- Shader 每顶点增加 smallest-three 解码、`sqrt/rsqrt`、cross 和分支，不能只看读字节就断言 GPU 更快。
- 现有机器像素门禁是单 Heap 合成夹具；多 Heap、两种光照模式交错的真实 GPU 寻址仍缺同等级自动断言。
- ConstantBuffer 后端没有独立设备闭环。
- 高频 Rebase/Cell Transform 的重复编码、托管 Dictionary 和全量上传峰值尚未测量。
- 位置仍是 float32，大世界精度问题仍需 Floating Origin。
- 最大风摆的非负语义目前依赖上游作者/资产钳制；最终 Packed Record 入口尚未形成独立硬门禁。

## 十一、工程采用前提

以下复选项是其它团队采用这一协议前应逐项确认的工程条件，不是当前项目待办、完成率或开发进度；未勾选只表示采用者尚未提供对应证据。

- [ ] 数据模型是否真的只允许有限、无剪切、非镜像、正数统一缩放？
- [ ] 最大风摆是否在最终 ABI 生产者入口按非负幅值校验，而不是只依赖 Inspector 或上游钳制？
- [ ] 是否共同冻结字段表、8 个 `uint` 金样、C#/HLSL stride、位序、舍入和 Metadata 寻址？
- [ ] CPU 剔除是否使用解码后的 TRS，并对量化位移保守扩展 Bounds？
- [ ] 空表哨兵、HeapIndex、光照索引和总地址计算是否在上传前完成整数门禁？
- [ ] 批量更新和 Rebase 是否先构建完整 CPU/GPU 候选再发布，且不从旧量化结果反复往返？
- [ ] 是否分别验证逻辑分配、实际回读、上传耗时、GPU 时间和物理显存，而不混成一个“性能提升”？
- [ ] 是否在目标图形 API 和移动设备上验证 Half 边界、四个 Pass 和带宽/ALU取舍？
- [ ] ABI 变化时是否有版本、重建和旧候选拒绝策略？

## 十二、结论

在有限、无剪切、非镜像、正数统一缩放的输入域内，逐株固定记录可以从 `128 B` 收敛到 `32 B`；当前直接证据证明了字段布局、位级金样、逻辑分配、D3D11 完整回读，以及单株 Forward 前景 Mask 的正向一致性。实现这一结果的必要条件，是同时冻结字节布局、数值编码和 GPU 寻址，并让 CPU 剔除、LOD、Bounds 与事务发布使用 GPU 解码后的同一量化真值。历史负向注入因没有保存具体代码差异，只能提示这类门禁可能发现明显的顶点形变错误，不能作为可复核证明。

这项结果是存储与协议结论，不是设备性能结论。当前可以确认的是：32 B 位级契约和列出的 Editor D3D11 路径有效；不能把它概括为整条生产运行链已经闭环。最大风摆最终生产入口的非负门禁、其它三个 Pass 的像素验证、Quest Vulkan、同协议帧时 A/B、物理显存、功耗和热稳定性仍需各自的直接证据。

### 相关记录

- [统一 BRG 架构](./unity-vegetation-unified-brg-architecture.md) - 数据权威、运行时 Cell/Heap、单 Buffer、剔除和卸载的大结构。
- [Bakery L2 静态光照与投影代理](./unity-vegetation-bakery-static-lighting-pipeline.md) - 每 Heap 量化表与 8 B/20 B 稀疏光照记录的生成和消费。
- [历史 Quest 3S BRG 与普通 GO 系统观察](./quest-vegetation-brg-performance-lighting-validation.md) - 历史真机 A/B/A；不等于本文 32 B ABI 的设备验证。
- [植被 Painter 作者工作流与事务设计](./unity-vegetation-painter-authoring-transaction-workflow.md) - StableGuid、变换预览和正式提交如何进入运行时 Patch。

### 验证记录

- [2026-08-26] 直接运行：在 Unity 2022.3.62f3、Windows Editor Direct3D11 与 Unity.Mathematics 1.3.2 下，执行固定 8 uint 金样、CPU 参考解码、采用 `System.Random(0x51A7C0DE)` 的 10,000 个旋转样本、指定非法输入与失败原子性用例，以及 Forward 前景 Mask 正向对照。另直接创建并完整回读两份 `N=8192、C=8192、S=0` 的 GraphicsBuffer；`H=50` 时布局/分配/回读均为 `334,208 B`，`H=1024` 时三者均为 `458,880 B`。压缩前绝对值属于按冻结 128 B 布局与同一组计数得到的派生计算，详见第六节。归档还记载一次 Bounds 高 16 位错误解包令 Mask 差异升至 `22`，但未保存注入代码差异，本文只把它列为不可公开复核的工程观察。
- [2026-09-02] 冻结源码静态复核：参考实现仍使用每株 `32 B / 8 uint`，四个 Pass 仍共用 Packed Record 解码与世界形变入口；最终 Packed Record 生产者仍没有负最大风摆的独立拒绝门禁。这次复核没有重新执行 Quest 或其它三个 Shader Pass 的像素 A/B。
- **未验证边界**：最大风摆最终通用生产入口的独立非负门禁、Quest Vulkan、ShadowCaster/DepthOnly/DepthNormals 像素等价、同协议帧时 A/B、物理显存和目标设备性能。

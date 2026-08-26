# Unity BRG 逐株 Buffer 的 32 字节压缩与量化 ABI

**标签**：#unity #experience #rendering #performance #memory #hlsl #culling
**来源**：工程实践抽象 - Unity BRG 逐株数据压缩、运行时回读与回归门禁
**收录日期**：2026-08-26
**更新日期**：2026-08-26
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐（32 B ABI、逻辑分配、实际 Buffer 回读和 Editor 渲染闭环已有证据；Quest Vulkan、帧耗与带宽收益尚未验证）
**适用版本**：Unity 2022.3 LTS、BatchRendererGroup 与 DOTS Instancing；其它 Unity 或图形后端需复核 Raw/Constant Buffer 寻址和 Half 行为

---

### 概要

当实例系统已经把变换约束为有限、无剪切、非镜像、正数统一缩放时，BRG 不必为每株保存 `ObjectToWorld`、`WorldToObject` 和两组 `float4` 参数。可以把世界位置保留为 `float32`，把旋转编码为 smallest-three `10:10:10:2`，把连续标量编码为 IEEE Half 或 UNorm16，把身份和地址继续保存为整数位段，从而把固定逐株区从 `128 B` 收敛到 `32 B`。

这项优化的难点不是位运算本身，而是建立完整协议：C# 写入与 HLSL 读取必须共享同一 ABI；CPU 剔除必须使用 GPU 实际恢复后的量化 TRS；影响剔除半径的量化值必须保守包络；批量预览、Cell 变换和 Floating Origin 更新必须先验证完整候选再触碰已发布状态；不可表达输入必须明确失败。

当前证据支持“逻辑 GraphicsBuffer 请求大小、完整回读长度和全量上传载荷下降”，不支持“Quest 帧时间、GPU 时间、功耗或物理显存一定下降”。新 Shader 用额外的 Half 解码、四元数恢复和向量旋转换取更小记录，带宽与 ALU 的净收益必须在目标设备上另做 A/B。

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

本文的参考证据固定为一份 2026-08-26 匿名工程候选：Unity `2022.3.62f3`、Android Build Target、Windows Editor Direct3D11。证据包括源码静态复核、严格 Test Runner 报告、实际 SceneBatch 创建和整段 GraphicsBuffer 回读，以及真实 SRP 前景 Mask 门禁。报告摘要与权威状态文件的长度和 SHA-256 相符，相关源码时间也早于最终测试；但候选当时尚未绑定不可变 VCS 源码摘要，因此它仍是版本受限的工程快照，不是公开可复跑基准。

阿卡西正文不保留原始工程路径、资源名、本地快照号、RunId、程序集 MVID 或私有内容 Hash。下文数字只在匿名规模和验证协议层面使用。

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

### 2.2 字段选择原则

| 数据 | 表达 | 原因 |
|---|---|---|
| 世界位置 | `float3` | 大世界坐标对绝对误差敏感；不在本轮量化 |
| 世界旋转 | smallest-three `10:10:10:2` | 单个 `uint` 可恢复单位四元数 |
| 正统一缩放 | IEEE Half | 动态范围足够时以显式上下界换容量 |
| 随机相位 | UNorm16 | 语义天然位于 `[0,1]` |
| 风摆与局部 Bounds 连续量 | IEEE Half | 允许有限量化误差，并可对剔除做保守补偿 |
| Heap 索引 | UInt16 | 保持整数精确；超出范围时拆分资产 |
| 光照模式与记录索引 | 1 bit + 31 bit | 不用浮点表达地址；越界明确失败 |

“位置保留 float32”只表示本轮没有新增位置量化误差，不表示突破了 float32 或 Floating Origin 本身的精度上限。

## 三、32 字节 ABI

一株固定为 8 个 `uint`：

| 字节范围 | uint | 内容 |
|---|---:|---|
| 0–11 | 0–2 | 世界位置 `float3`，按位解释为三个 float32 |
| 12–15 | 3 | smallest-three 旋转：三个 10 位分量 + 2 位省略分量索引 |
| 16–19 | 4 | 低 16 位正统一缩放 Half；高 16 位随机相位 UNorm16 |
| 20–23 | 5 | 低 16 位最大风摆 Half；高 16 位 Bounds 最低点 Half |
| 24–27 | 6 | 低 16 位 Bounds 高度倒数 Half；高 16 位 HeapIndex |
| 28–31 | 7 | 最高位光照模式；低 31 位对应稀疏光照表的记录索引 |

旋转字的规范位序为：`a = bits[0..9]`、`b = bits[10..19]`、`c = bits[20..29]`、`omitted = bits[30..31]`。`a/b/c` 始终按四元数 `x,y,z,w` 的原顺序保存，跳过 `omitted` 指定的一个分量。

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
5. 至少一个真实 SRP/BRG 像素门禁必须能对故障注入变红。

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

固定种子均匀覆盖 SO(3) 的 10,000 个样本中，观测最大角误差为 `0.197823°`，门限为 `< 0.25°`。这是该样本集的观测最大值，不是数学最坏误差证明。

### 4.2 Half 与 UNorm16

- Half 合法输入必须是 binary32 有限值且绝对值不超过 `65504`；NaN、Infinity 和超界值在转换前失败。
- 语义上必须大于零的缩放和 Bounds 高度倒数会先拒绝 `value <= 0`，因此正负零都不合法；在 Half 舍入后若变成零也必须失败。
- 最大风摆和 Bounds 最低点允许零与负值；一般 Half 字段保留 binary16 符号位，包括 `-0 → 0x8000`。
- 随机相位的合法输入域是有限 binary32。先钳制到 `[0,1]`，再以 binary32 计算 `value × 65535`，最后用 round-to-nearest、ties-to-even 编为 UNorm16；解码为 `q / 65535.0f`。NaN/Infinity 不属于 ABI 合法输入，必须由调用方拒绝。当前内部调用由稳定身份生成有限 `[0,1]` 值，但打包帮助函数本身没有独立非有限门禁，抽取为公共库时应补上。
- GPU 解码一个 `uint` 中的两个 Half 时，必须分别读取低 16 位和右移后的高 16 位；不能假设一次转换会自动得到两个值。

Half 转换固定使用 Unity.Mathematics 1.3.2 `math.f32tof16` 的位算法，而不是泛指任意“IEEE Half 转换”。对上述合法有限输入，兼容实现按以下 binary32/uint 步骤产生低 16 位：

```text
ux  = asuint(x)
mag = ux & 0x7FFFF000
h   = (asuint(min(asfloat(mag) * asfloat(0x07800000),
                      asfloat(0x4D77FF00))) + 0x1000) >> 13
halfBits = (h | ((ux & 0x80000FFF) >> 16)) & 0xFFFF
```

这条规则保留 signed zero 与 binary16 次正规数；例如 `+0 → 0000`、`-0 → 8000`、`5.96046448e-08f → 0001`、`123.4f → 57B6`、`65504f → 7BFF`。CPU 参考解码固定使用同版本 `math.f16tof32`；HLSL 使用 `f16tof32` 解释低 16 位。不同移动 GPU 是否把次正规数 flush-to-zero 仍需真机验证；生产采用可以把允许下界提高到最小正常 Half，或为目标设备增加边界测试。

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
  → Forward、Depth、DepthNormals 与 Shadow 共用同一取数和世界形变链
```

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

Heap 量化表和两张光照表的 Metadata 不带 PerInstanceDataBit。Shader 从共享基址显式追加 HeapIndex 或 LightingRecordIndex；否则 BRG 会自动按实例步长偏移，共享数据会错误退化为逐株寻址。

## 七、CPU 剔除必须使用量化后的真值

若 GPU 使用量化后旋转和缩放，而 CPU 仍用原始矩阵计算包围球与 LOD，实例在视锥或阈值边缘可能出现单帧消失。参考策略是：

1. 每次都从权威高精度矩阵重新编码，禁止对已经量化的结果反复往返。
2. CPU 立即用同一编码规则恢复旋转和缩放。
3. 剔除中心、半径、LOD 中心和 LOD 尺寸都使用恢复后的 TRS。
4. 对影响顶点最大位移的 Half 字段，剔除余量取 `max(source, decoded)`。
5. Heap Bounds 保留编译结果，并把量化后实例球并入，只允许保守扩展，不允许缩小工作集。

这套做法会在全量上传与剔除快照构建时重复提取和量化 TRS，换来两端一致和失败事务。它属于加载/Rebase 的低频 CPU 成本；当前没有 Profile 数据证明其尖峰可以忽略。

## 八、预览、Rebase 与卸载事务

### 8.1 初次加载

```text
验证 SceneAsset / Prototype 版本与内容摘要
  → 统计两张稀疏光照表的实际记录数
  → 计算唯一 Layout
  → 分配临时清零 uint 数组和 GraphicsBuffer
  → 按 Heap 顺序写风场、32 B 记录、量化表和光照表
  → 一次 SetData 上传完整候选
  → 注册 Metadata 与 Batch
  → 构建 CPU 剔除快照和 StableGuid→当前 Slot 反查
```

完整候选在一次上传前位于临时数组中，因此编码失败不会把半条记录发布到 GPU。

### 8.2 编辑预览

- 单株预览始终覆写该株完整的 32 B，避免字段级撕裂。
- 批量预览先为全部目标构建紧凑记录和剔除数据；任一目标失败时不开始 GPU 写入。
- 取消预览时从权威 SceneAsset 的高精度数据重新编码，而不是读取并二次量化 GPU 结果。
- 反查表以 StableGuid 找到当前 Slot；Slot 仍只是当前会话地址。

CPU Job 完成和原地 Buffer Patch 不自动证明先前提交的 GPU 工作已经退役。高风险编辑器或运行时热更新若需要严格在途一致性，仍应使用 GPU Fence、双 Buffer/世代切换或独立预览 Batch。

### 8.3 Cell Transform 与 Floating Origin

候选更新顺序应为：

```text
构建量化后的候选 CPU Snapshot
  → 构建并上传完整候选 Buffer
  → 两者成功后才提交 CellTransform / Origin
  → 替换 StableGuid→Slot 反查和公开 Snapshot
  → 清理旧预览
```

这样 Half 上溢、最终缩放下溢或 NaN Origin 被拒绝时，管理字段、GPU Buffer、预览 Bounds 和作者资产仍保持调用前状态。

### 8.4 HeapMask 与卸载

HeapMask 只门控剔除。Heap 失活不会重传、缩容或释放该 Heap 的 32 B 记录和光照表；Count/Scatter 仍可能按运行时 Cell 总实例长度调度。只有整个运行时 Cell 卸载时，系统才等待最后的 CPU 剔除 Job、移除 Batch、释放 GraphicsBuffer 与 NativeArray，并释放 Prototype 注册引用。

因此，32 B 压缩减少的是常驻 Cell Buffer 与全量上传载荷，不会自动把失活 Heap 变成紧凑运行工作集。

## 九、已验证结果

### 9.1 布局与实际回读

| 匿名场景规模 | 旧布局 | 新布局 | 降幅 | 证据强度 |
|---|---:|---:|---:|---|
| 288 实例 / 40 Heap / 两种光照各 144 | 46,112 B | 18,464 B | 59.958% | 精确公式与布局门禁；无独立结构化整段回读 |
| 8,192 实例 / 50 Heap / 8,192 静态颜色 / 0 Bakery SH | 1,120,640 B | 334,208 B | 70.177% | 实际 SceneBatch、逻辑分配、底层 count×stride 与整段回读长度一致 |
| 8,192 实例 / 1,024 Heap / 8,192 静态颜色 / 0 Bakery SH | 1,245,312 B | 458,880 B | 63.151% | 实际 SceneBatch、逻辑分配、底层 count×stride 与整段回读长度一致 |

两个回读样本在释放后均确认 GraphicsBuffer 不再有效。这里证明的是 Unity 逻辑分配请求和可回读长度，不等于驱动最终物理显存、分配器保留或整进程 PSS。

### 9.2 正确性与失败门禁

- 结构尺寸、字段位序和 8 个 `uint` 金样通过。
- 世界位置编解码逐位一致。
- 10,000 个固定种子 SO(3) 样本的观测最大旋转误差为 `0.197823°`。
- Half 上溢、正值下溢、非统一缩放、镜像、剪切和 Heap 索引越界会显式失败。
- GPU 整段回读证明单株预览只改变目标 32 B，取消后全 Buffer 逐字恢复。
- 批量预览第二个候选失败时，完整 Buffer、预览 Heap 和作者资产保持不变。
- Cell 或 Origin 候选失败时，公开字段、完整 Buffer 与已有预览保持不变。
- 真实 SRP Forward 门禁在冻结非零风时记录 BRG/普通 GO 前景均为 192 像素、差异 2，门限为 10；一次受控错误解码故障注入曾把差异扩大到 22 并让门禁失败。
- 同轮严格结果为 EditMode `244/244`、PlayMode `11/11`，失败、跳过和不确定均为 0。

Test Runner 总数是带日期的候选快照，不是长期必须维持的用例数量合同。Shader Importer 和文本关系门禁支持四个 Pass 复用同一解码链，但 Forward 之外的 Shadow、Depth 与 DepthNormals 尚没有同等级视觉等价 A/B。

### 9.3 有限视觉观察

一组同机位前后截图未见明显实例位置、光照分区或阴影外观回归；但截图时非零风没有冻结，不能把逐像素差异全部归因于量化，也不能把它升级为像素等价证明。正式可信视觉门禁以上述冻结风的合成 SRP Mask 测试为准。

## 十、不能从当前证据推出什么

- 未做压缩前后同协议的 CPU 上传、首帧、稳定帧、GC Alloc 或 GPU 帧时间 A/B。
- 未在 Quest Vulkan 或 Android Player 上验证 Shader、Half 次正规数、带宽、ALU、功耗和热降频。
- 更小的 `buffer.count × stride` 不等于驱动物理显存一定按相同比例下降。
- Shader 每顶点增加 smallest-three 解码、`sqrt/rsqrt`、cross 和分支，不能只看读字节就断言 GPU 更快。
- 现有机器像素门禁是单 Heap 合成夹具；多 Heap、两种光照模式交错的真实 GPU 寻址仍缺同等级自动断言。
- ConstantBuffer 后端没有独立设备闭环。
- 高频 Rebase/Cell Transform 的重复编码、托管 Dictionary 和全量上传峰值尚未测量。
- 位置仍是 float32，大世界精度问题仍需 Floating Origin。

## 十一、采用检查清单

- [ ] 数据模型是否真的只允许有限、无剪切、非镜像、正数统一缩放？
- [ ] 是否先冻结字段表、尺寸、字节偏移、位段和 HLSL stride？
- [ ] 是否为固定输入保存 8 个 `uint` 金样，而不只测试 round-trip？
- [ ] CPU 剔除是否使用 GPU 实际恢复后的 TRS？
- [ ] 影响最大位移的量化值是否保守扩展 Bounds？
- [ ] 空实例、空 Heap 和空稀疏表的 Metadata 是否仍指向合法哨兵？
- [ ] HeapIndex 与记录索引是否在写入前做整数范围门禁？
- [ ] 批量预览和全量重建是否先验证完整候选再发布？
- [ ] 是否把 StableGuid 与当前 GPU Slot 分开建模？
- [ ] 是否分别验证逻辑分配、实际回读、上传耗时、GPU 时间和物理显存，而不混成一个“性能提升”？
- [ ] 是否在目标图形 API 和移动设备上验证 Half 边界、四个 Pass 和带宽/ALU取舍？
- [ ] ABI 变化时是否有版本、重建和旧候选拒绝策略？

## 十二、可复用结论

1. 先收紧可表达语义，再压缩数据；任意矩阵不能靠 Shader 静默近似成紧凑 TRS。
2. 高动态范围位置、连续标量和离散身份应使用不同表达：float32、Half/UNorm 与整数位段各司其职。
3. GPU 数据量化会改变运行时真值；CPU 剔除、LOD 和 Bounds 必须消费同一真值或使用保守上界。
4. ABI 验证要同时覆盖尺寸、金样位序、范围失败、实际 Buffer 回读、真实 Shader 像素和故障注入。
5. 记录压缩、全量上传、稳定帧带宽和最终帧耗是四个不同结论；当前证据只支持前两项中的字节规模。
6. 多 Heap 共享 Buffer 时，HeapBase 是加载快照派生地址，StableGuid 才是持久身份；HeapMask 不等于数据卸载。
7. 事务性发布与压缩同等重要。缩小记录不能以半应用预览、CPU/GPU 剔除漂移或失败后状态污染为代价。

### 相关记录

- [统一 BRG 架构](./unity-vegetation-unified-brg-architecture.md) - 数据权威、运行时 Cell/Heap、单 Buffer、剔除和卸载的大结构。
- [Bakery L2 静态光照与投影代理](./unity-vegetation-bakery-static-lighting-pipeline.md) - 每 Heap 量化表与 8 B/20 B 稀疏光照记录的生成和消费。
- [Quest 3S BRG 与普通 GO 性能基线](./quest-vegetation-brg-performance-lighting-validation.md) - 历史真机 A/B/A；不等于本文 32 B ABI 的设备验证。
- [植被 Painter 作者工作流与事务设计](./unity-vegetation-painter-authoring-transaction-workflow.md) - StableGuid、变换预览和正式提交如何进入运行时 Patch。

### 验证记录

- [2026-08-26] 审查 128 B 到 32 B 的逐株 ABI、C#/HLSL 位序、CPU 同量化剔除、多 Heap/稀疏光照寻址、预览/Rebase 事务和卸载链；未发现阻断实现问题。
- [2026-08-26] 复核两个匿名 8,192 实例 SceneBatch 的完整 GraphicsBuffer 回读，以及 EditMode `244/244`、PlayMode `11/11`、旋转误差和真实 SRP Mask 门禁；明确这些证据不包含 Quest Vulkan 或帧耗 A/B。
- [2026-08-26] 完成语义脱敏：删除本机路径、真实资源名、本地快照号、RunId、程序集 MVID 和私有内容 Hash，只保留可复用机制、匿名规模与验证边界。

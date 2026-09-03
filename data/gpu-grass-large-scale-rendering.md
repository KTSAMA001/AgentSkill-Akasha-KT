# Unity Compute Shader 草渲染：间接绘制链与视锥剔除边界

**标签**：#unity #graphics #experience #compute-shader #urp #performance #culling
**来源**：[KTSAMA001/Unity_URP_Learning - ComputeShaderGrass](https://github.com/KTSAMA001/Unity_URP_Learning/tree/5b9852d71e53527526c695e9c25e72739bfa7eb6/Assets/Products/ComputeShader/ComputeShaderGrass)
**收录日期**：2026-02-07
**来源日期**：2024-03-28
**更新日期**：2026-09-03
**状态**：📘 有效
**可信度**：⭐⭐⭐（公开源码与 Unity 2022.3 官方图形约定已静态核对；本文未运行来源工程，也没有设备性能数据）
**适用版本**：来源快照使用 Unity 2022.3.17f1c1、Universal Render Pipeline（URP）14.0.9；其它版本需要重新编译和验证

---

### 概要

这个公开案例展示了一条完整的 GPU 草渲染教学链：CPU 把若干地形 Mesh 合并为采样表面，按三角形面积随机生成草的变换矩阵；Compute Shader 每帧把通过筛选的矩阵追加到结果 Buffer；CPU 将追加计数复制到间接绘制参数；最后用 `Graphics.DrawMeshInstancedIndirect` 提交草 Mesh。

它能说明 Append Buffer、间接参数和 GPU 实例数据如何串起来，但不能直接当作生产级视锥剔除方案。冻结源码中的所谓“六面剔除”循环没有使用平面索引，六次重复的是同一组裁剪空间条件；判定只接受“至少一个包围盒角点落入放宽后的裁剪盒”，因此可能漏掉与视锥相交、但八个角点都在视锥外的实例。噪声项又基于裁剪坐标，并与绘制距离混入同一阈值，结果会随相机投影变化。

深度条件需要单独辨析。源码直接上传 `Camera.projectionMatrix`，没有调用 `GL.GetGPUProjectionMatrix`。Unity 2022.3 官方文档说明，脚本侧投影矩阵遵循 OpenGL 约定；对普通透视投影的前方点，源码中的 `abs(z) <= abs(w)` 等价于 `-w <= z <= w`，同时包含近、远深度边界。若把矩阵换成 Direct3D 11（D3D11）等平台调整后的 GPU 投影矩阵，合法区间则是 `0 <= z <= w`，此时取绝对值会错误接受一部分 `z < 0` 的点。也就是说，这个 z 条件不能脱离“上传的究竟是哪一种矩阵”而单独判定。

本文结论来自源码与官方约定的静态审计，不是运行时性能实测：这是一份适合理解数据流的案例，也是一份说明“能够间接绘制”不等于“剔除已经正确”的反例。

### 一、术语与问题模型

- **TRS（Translation、Rotation、Scale）矩阵**：把平移、旋转和缩放合并到一个 `4 × 4` 变换矩阵中。源码为每株草保存一个 `float4x4` TRS。
- **AABB（Axis-Aligned Bounding Box，轴对齐包围盒）**：六个面与其定义空间的 X、Y、Z 轴平行的长方体。每个坐标轴各取最小值或最大值，共有 `2 × 2 × 2 = 8` 种组合，因此有八个角点。源码先定义一个局部空间 AABB，再把八个角点分别乘到裁剪空间；经过实例旋转后，它在世界空间不再是轴对齐盒。
- **VP（View–Projection）矩阵**：视图矩阵与投影矩阵的乘积，把世界空间位置变换到裁剪空间。源码上传的是 `Camera.projectionMatrix × Camera.worldToCameraMatrix`。
- **裁剪空间**：透视除法前的齐次坐标空间。一个点写作 `(x, y, z, w)`，可见区间必须结合生成它的投影矩阵约定判断。
- **间接绘制参数**：GPU 绘制所需的索引数、实例数、索引起点、顶点基址和起始实例。实例数可以由 GPU 计算结果产生，而不必由 CPU 逐株统计。
- **Append Buffer**：GPU 线程可以把通过筛选的记录追加到末尾的缓冲区；其内部计数器表示结果数量。
- **保守粗筛**：用便宜的包围体测试排除明确不可见的实例。它可以多留下候选，但不能丢掉真正可见的实例，否则会出现错误消失。
- **绘制总 Bounds**：Unity 在提交整条间接绘制前使用的 CPU 侧包围盒。它决定整批是否可能进入相机，但不会替代每株剔除。
- **真值 oracle**：为了验证另一实现而建立的参考实现。它必须直接表达预先定义的正确性契约、结果可重复，并尽量与被测实现采用不同的代码路径；这里指 CPU 上的六平面包围体相交实现。

审计这类案例至少要分别回答四个问题：草实例如何生成；可见列表和实例计数如何传到 Draw；粗筛是否保守；裁剪条件是否与实际上传的投影矩阵采用同一约定。

### 二、冻结来源与证据范围

本文绑定到公开提交 [`5b9852d71e53527526c695e9c25e72739bfa7eb6`](https://github.com/KTSAMA001/Unity_URP_Learning/commit/5b9852d71e53527526c695e9c25e72739bfa7eb6)。关键证据如下：

| 主张 | 冻结源码或官方入口 | 本文证据 |
|---|---|---|
| 按地形三角形面积生成草 | [`GPUGrassTest.Start`](https://github.com/KTSAMA001/Unity_URP_Learning/blob/5b9852d71e53527526c695e9c25e72739bfa7eb6/Assets/Products/ComputeShader/ComputeShaderGrass/GPUGrassTest.cs) | 源码静态核对 |
| Compute Shader 生成可见矩阵列表 | [`FrustumCulling.compute`](https://github.com/KTSAMA001/Unity_URP_Learning/blob/5b9852d71e53527526c695e9c25e72739bfa7eb6/Assets/Products/ComputeShader/ComputeShaderGrass/FrustumCulling.compute) | 源码静态核对 |
| 追加计数成为间接实例数 | `GPUGrassTest.Update` 中的 `ComputeBuffer.CopyCount` | 源码静态核对 |
| 最终提交方式和固定总 Bounds | `GPUGrassTest.Update` 中的 `Graphics.DrawMeshInstancedIndirect` | 源码静态核对 |
| Windows Standalone 显式选择 D3D11 | [`ProjectSettings.asset`](https://github.com/KTSAMA001/Unity_URP_Learning/blob/5b9852d71e53527526c695e9c25e72739bfa7eb6/ProjectSettings/ProjectSettings.asset) | 冻结项目配置静态核对 |
| 脚本投影矩阵与 GPU 投影矩阵的区别 | [Unity 2022.3 `GL.GetGPUProjectionMatrix`](https://docs.unity3d.com/2022.3/Documentation/ScriptReference/GL.GetGPUProjectionMatrix.html) | Unity 官方文档 |
| OpenGL-like 与 Direct3D-like 的裁剪深度约定 | [Unity 2022.3 平台图形差异](https://docs.unity3d.com/2022.3/Documentation/Manual/SL-PlatformDifferences.html) | Unity 官方文档 |

冻结配置证明 Windows Standalone 图形 API 被设为 D3D11，却不能证明作者只在该平台运行过这个场景；本文也没有运行它。没有直接证据证明：特定实例规模的 CPU/GPU 时间、基于物理的渲染画面正确性、各种相机投影下无闪烁、移动设备收益，或代码在来源版本之外仍兼容。来源目录包含多个迭代资产；本文只描述上表所指的 `GPUGrassTest` 与 `FrustumCulling` 主链。

### 三、端到端运行链

#### 3.1 CPU 生成实例

启动时，脚本先把 `_terrianMeshGroup` 中的 Mesh 合并到一个临时 Mesh，再遍历索引缓冲中的每个三角形。每个三角形的草数为：

```text
ceil(max(1, densityPerArea × triangleArea))
```

这不只是面积密度公式，还施加了“每个三角形至少一株”的下限。总实例数因此至少等于三角形数；当许多三角形满足 `densityPerArea × area < 1` 时，把同一表面细分成更多三角形会增加草数。换言之，生成密度受三角化粒度影响，不是只由表面面积决定；极小乃至零面积三角形也会进入“一株”分支。

每株草在三角形内均匀取一点，用三角面法线决定朝向，再叠加随机 Y 轴旋转和随机高度缩放。最终上传记录只有一个 `float4x4` TRS，即每株 `64 B`。这条主链没有额外上传位置或实例 ID。

这一生成方法的成本与地形三角形数和生成实例数线性相关，而且全部发生在 CPU。脚本没有保存稳定实例身份，也没有把数据分区流送；适合一次性教学场景，不等于开放世界作者数据结构。

#### 3.2 GPU 追加可见记录

每帧流程按下列顺序执行：

```text
清零 Append 计数
→ 设置相机 VP、最大距离和实例 Buffer
→ 按每组 640 个线程 Dispatch
→ 每个线程读取一株 TRS 并执行筛选
→ 通过者把完整 64 B TRS 追加到结果 Buffer
```

线程组大小由 `[numthreads(640, 1, 1)]` 固定为每组 640 个线程；CPU 提交的组数是 `1 + floor(instanceCount / 640)`，并不是“640 个线程组”。当实例数不是 640 的整数倍时，这个值等于向上取整 `ceil(instanceCount / 640)`；当实例数恰好是整数倍时会多提交一组。线程入口的 `id.x >= instanceCount` 检查会让多余线程返回，因此不会越界写入。严格的正整数向上取整写法是 `(instanceCount + 639) / 640`。

结果 Buffer 复制的是完整矩阵，不是原实例索引。实例较多时，这会增加筛选阶段的写带宽；是否应改为追加索引，需要根据后续 Shader 寻址和目标 GPU 测量决定。

#### 3.3 间接参数与绘制

参数 Buffer 含 5 个 `uint`：

```text
indexCountPerInstance
instanceCount
startIndex
baseVertex
startInstance
```

`ComputeBuffer.CopyCount(result, args, sizeof(uint))` 把 Append 计数写入第二个字段，也就是实际绘制实例数。材质读取筛选后的矩阵 Buffer，`DrawMeshInstancedIndirect` 再提交一条间接绘制。

这条调用还传入一个以脚本 Transform 为中心、尺寸 `1000 × 1000 × 1000` 的固定总 Bounds。它是整批提交的 CPU 侧可见性入口：

- Bounds 过大时，整批更难被提前拒绝，CPU 粗粒度剔除收益下降。
- Bounds 过小、中心错误，或者没有覆盖筛选后实例的真实范围时，Unity 可能在任何逐株结果参与绘制之前拒绝整条 Draw；视锥内的草也会以整批为单位突然消失。
- Compute Dispatch 已经在 Draw 调用前执行，因此总 Bounds 拒绝 Draw 并不会追回本帧已经发生的筛选计算。

总 Bounds 既不是草地实际范围的自动计算，也不能证明逐株筛选正确。正式方案应从全部实例与最大顶点动画位移推导它，或者把大范围拆成多个空间批次。

### 四、裁剪条件究竟在哪些约定下成立

源码构造的矩阵是：

```text
clip = Camera.projectionMatrix × Camera.worldToCameraMatrix
       × PivotTRS × InstanceTRS × localPosition
```

`Camera.projectionMatrix` 被原样写入 Compute Shader。代码没有调用 `GL.GetGPUProjectionMatrix`，Compute Shader 的普通矩阵参数也不会因为运行在 D3D11 后端就自动改写其数值。Unity 2022.3 官方文档给出的边界是：

- 脚本侧 Unity 投影矩阵遵循 OpenGL-like 约定。普通透视投影的合法归一化深度是近面 `-1`、远面 `+1`，齐次形式为 `-w <= z <= w`。
- 经 `GL.GetGPUProjectionMatrix` 转换后的 Direct3D-like 矩阵采用 `[0, 1]` 深度区间。Unity 在 D3D11 上通常使用反向 Z，近面为 `+1`、远面为 `0`，但合法齐次区间仍是 `0 <= z <= w`。

源码先对整个裁剪坐标执行 `abs`，随后检查 `boundPosition.z <= boundPosition.w`，实际表达式是：

```text
abs(z) <= abs(w)
```

因此可以得到三个不同层次的结论：

1. **对源码实际上传的普通 Unity 透视矩阵**：相机前方点有 `w > 0`，`abs(z) <= abs(w)` 等价于 `-w <= z <= w`。它同时测试 OpenGL-like 的近、远深度边界，不能描述成“只测了远面”或“完全没有近面判断”。
2. **如果改为平台调整后的 D3D11 GPU 投影矩阵**：正确区间是 `0 <= z <= w`。取绝对值只保留了幅值上界，丢失 `z >= 0`；一部分越过深度区间下界的点会被折回并错误接受。此时 `abs(z) <= abs(w)` 不成立。
3. **对自定义、斜截面、扩展现实（XR）或其它非普通投影**：仅凭当前源码和官方通用约定不能证明上述等价关系。必须固定真实矩阵，逐点或逐包围体与 CPU 参考结果对照；本文不把普通透视结论外推到这些情况。

这段深度判断在当前普通透视矩阵下可以自洽，不代表整套视锥剔除正确。主要错误位于下一节的“六次重复”和“角点必须进入裁剪盒”两处。

### 五、为什么当前“视锥剔除”仍不具备生产正确性

标准包围盒–视锥保守粗筛的拒绝条件是：只有当包围盒的全部可能点都位于同一个视锥平面外时，才能确认它不可见。冻结 Compute Shader 没有实现这个条件。

源码先用局部最小点 `(-1.5, 0, -1.5)` 与最大点 `(1.5, 7, 1.5)` 枚举八种 min/max 组合，再把八个角点乘到裁剪空间。外层循环执行六次，但循环变量 `i` 没有参与任何计算；每一次都对八个角点重复同一组条件：

```text
abs(z) <= abs(w)
abs(y) <= 1.5 × abs(w)
abs(x) <= 1.1 × abs(w)
abs(w) + noise(abs(clipPosition)) × maxDistance / 2 <= maxDistance
```

只要找到一个同时满足所有条件的角点，就结束当前内层循环；六轮检查完全相同。因此最终结果等价于把同一个“至少一个角点在放宽裁剪盒内”的测试重复六次，而不是分别测试左、右、下、上、近、远六个平面。

它会产生以下问题：

1. **不是六个平面测试。** 外层循环没有读取平面方程或使用平面索引。
2. **不是保守相交测试。** 一个大包围盒可以横跨视锥，但八个角点全部位于视锥外；源码会把这种仍与视锥相交的实例错误剔除。
3. **放宽系数没有几何依据。** `1.5` 与 `1.1` 只能扩大近似裁剪盒，不能修复相交算法。
4. **距离与噪声没有统一空间。** 噪声输入来自裁剪坐标，距离阈值却混用 `w`；相机位置、FOV 或投影改变时，图案和剔除边界也会改变。
5. **包围体不是从真实几何推导。** 固定局部范围没有读取草 Mesh Bounds，也没有纳入顶点动画最大位移；过小会造成误剔除，过大则增加无效候选。

所以，把这段实现描述为“AABB 八角点对六个视锥面进行判断”是不准确的。更准确的名称是“对局部 AABB 的八个变换后角点执行重复的裁剪空间近似筛选”。

### 六、如何用 CPU 真值 oracle 做可执行验证

参考实现之所以能作为真值 oracle，不是因为“CPU 天然比 GPU 正确”，而是因为它可以独立、直接地表达预定契约：对同一相机、同一实例包围体和同一距离规则，计算六个世界空间平面；若某个平面的外侧包含全部八个角点，则拒绝实例，否则保留。该算法可读、确定，且没有复用被测 Compute Shader 的循环和裁剪表达式，适合为 GPU 结果提供可复核的期望集合。

验证前必须固定随机种子或保存实例 TRS，避免 CPU 与 GPU 比较期间输入变化。设 CPU oracle 判定可见的原始实例索引集合为 `T`，GPU 粗筛输出集合为 `G`：

```text
正确性底线：T ⊆ G
等价检查：T - G 必须为空
```

GPU 粗筛不能比 CPU 真值少，否则代表可见实例被错误丢弃。额外候选 `G - T` 若仍由光栅化裁剪或后续精筛排除，主要代价是效率；但这个案例把 `G` 直接交给 Draw，超出自定义距离规则却仍在相机视锥内的额外实例可能真正显示出来。若目标是完整复现包含距离规则在内的 CPU 谓词，而不只是证明视锥粗筛无漏项，就必须进一步要求 `G = T`。

当前输出只有 TRS，没有稳定 ID。直接用浮点矩阵做集合键会受重复变换、浮点序列化和容差影响，不能形成可靠的逐实例证明。可执行的调试方法是：

1. 将输入数组下标 `id.x` 作为本次固定输入的原始索引。
2. 在验证构建中增加一个调试用 `AppendStructuredBuffer<uint>`，通过筛选时追加 `id.x`；正式 64 B TRS ABI 可以保持不变。
3. 用 `AsyncGPUReadback` 读取计数与索引集合，不依赖 Append 的输出顺序。
4. CPU 对同一批 TRS 生成集合 `T`，比较 `T - G`、`G - T`，并单列擦边、大包围盒、相机位于包围盒内、不同相机视野角（FOV）和近远裁剪面用例。
5. 记录误剔除数量必须为零，再统计额外候选率与性能；不能用“一条 Draw”替代正确性验证。

这个方法使用的是单次验证输入内稳定的原始索引，不要求先为教学案例设计持久化的全局唯一标识。若不能增加调试索引，当前仅含 TRS 的输出最多支持有歧义的近似匹配，不能证明没有误剔除。

### 七、把案例改造成可靠方案需要什么

最小改造顺序如下：

1. 明确选择一种坐标约定：要么继续使用 Unity 脚本侧 OpenGL-like 投影矩阵并按 `-w <= z <= w` 测试，要么上传 `GL.GetGPUProjectionMatrix` 的结果并按目标平台约定测试；不要混用。
2. CPU 每帧计算六个世界空间视锥平面并上传平面方程，或者实现经过独立验证的齐次裁剪空间保守测试。
3. 对每个实例构建包含缩放、旋转和顶点动画最大位移的世界空间包围体。
4. 每个平面只在整个包围体都位于外侧时拒绝实例；擦边应保留。
5. 将距离剔除与视锥剔除分开，距离使用明确的世界空间定义；若要噪声过渡，应只影响远距离淡出或概率选择，不破坏视锥保守性。
6. 根据全部实例的真实范围计算整批 Draw Bounds，或把大世界拆成多个空间批次。
7. 用上一节的 CPU/GPU 索引集合对照验证无误剔除，再分别测量实例 Buffer 读取、结果写入、Dispatch、CopyCount、Draw、顶点和片元成本。

如果目标还包括作者编辑、细节层级（LOD）、多场景加载、静态光照、稳定身份或物理碰撞，就需要在这条渲染演示之外增加相应的数据权威和生命周期层，而不是继续向单个脚本堆状态。

### 八、适用与不适用范围

适合：

- 学习 Append Buffer、CopyCount 和间接绘制如何连接；
- 验证“CPU 生成静态实例、GPU 每帧压缩可见列表”的基本架构；
- 作为错误剔除算法与投影矩阵约定的审计练习。

不适合直接采用：

- 不能容忍视锥边缘错误消失的正式画面；
- 需要多个运行时 Cell、动态加载或精确 LOD 的大世界；
- 需要持久编辑、撤销、稳定实例身份或场景资产闭环；
- 需要用现有资料证明移动设备性能收益。

### 结论

冻结案例的主链是“CPU 按三角形面积生成 64 B TRS → Compute Shader 追加筛选后的 TRS → CopyCount 写实例数 → DrawMeshInstancedIndirect 绘制”。其中“每个三角形至少一株”使实例数依赖三角化粒度；固定总 Bounds 若过小，还会在逐株结果之外造成整批错误消失。

对源码实际上传的普通 `Camera.projectionMatrix`，`abs(z) <= abs(w)` 与 OpenGL-like 的 `-w <= z <= w` 深度区间相容；对经过平台转换的 D3D11 GPU 投影矩阵，同一写法则会丢失 `z >= 0` 下界。当前剔除不正确的确定性证据，是外层六次循环没有使用平面索引，以及“至少一个角点在盒内”不等价于包围体与视锥相交。

采用这类方案时，应先用调试原始索引建立 CPU 真值集合，并证明 GPU 候选集合没有漏掉任何真值实例，再讨论单次 Draw、噪声边界或性能。本文没有运行来源工程、没有 GPU 读回对照、没有目标设备帧时间和画面证据，因此只能把它评价为教学案例，不能称为已验证的大规模植被解决方案。

### 相关记录

- [GPU 视锥剔除](./gpu-frustum-culling-compute-shader.md) - 正确剔除所需的基础概念。
- [Compute Shader 基础](./compute-shader-gpgpu-basics.md) - Dispatch、线程组和 Buffer 基础。
- [Unity 大规模植被统一 BRG 架构](./unity-vegetation-unified-brg-architecture.md) - 另一条面向持久作者数据、多空间分区（Cell）和 BatchRendererGroup（BRG）生命周期的架构；不是本案例的同一实现。

### 参考链接

- [冻结提交](https://github.com/KTSAMA001/Unity_URP_Learning/commit/5b9852d71e53527526c695e9c25e72739bfa7eb6) - 本文核对的公开源码版本。
- [GPUGrassTest.cs](https://github.com/KTSAMA001/Unity_URP_Learning/blob/5b9852d71e53527526c695e9c25e72739bfa7eb6/Assets/Products/ComputeShader/ComputeShaderGrass/GPUGrassTest.cs) - CPU 生成、Dispatch、CopyCount 与 Draw 主链。
- [FrustumCulling.compute](https://github.com/KTSAMA001/Unity_URP_Learning/blob/5b9852d71e53527526c695e9c25e72739bfa7eb6/Assets/Products/ComputeShader/ComputeShaderGrass/FrustumCulling.compute) - 当前近似筛选实现。
- [ProjectSettings.asset](https://github.com/KTSAMA001/Unity_URP_Learning/blob/5b9852d71e53527526c695e9c25e72739bfa7eb6/ProjectSettings/ProjectSettings.asset) - 冻结项目的图形 API 配置。
- [Unity 2022.3 `GL.GetGPUProjectionMatrix`](https://docs.unity3d.com/2022.3/Documentation/ScriptReference/GL.GetGPUProjectionMatrix.html) - 脚本投影矩阵到当前图形 API 投影矩阵的转换说明。
- [Unity 2022.3 Shader 平台差异](https://docs.unity3d.com/2022.3/Documentation/Manual/SL-PlatformDifferences.html) - Direct3D-like 与 OpenGL-like 裁剪深度区间及反向 Z 说明。
- [Unity 2022.3 `Graphics.DrawMeshInstancedIndirect`](https://docs.unity3d.com/2022.3/Documentation/ScriptReference/Graphics.DrawMeshInstancedIndirect.html) - 间接绘制参数与总 Bounds API。

### 验证记录

- [2026-09-03] 静态审计：绑定公开提交，核对 `GPUGrassTest.cs`、`FrustumCulling.compute`、项目图形 API 配置与 Unity 2022.3 官方投影矩阵约定。验证范围不包含运行来源工程、GPU 读回集合对照、性能采样或画面测试。

---

# Unity 2022.3 GPU 虫群网格塑形与 VAT 动画 MVP 实践

**标签**：#unity #graphics #shader #experience #compute-shader #gpgpu #hlsl #animation #draw-call
**来源**：本地 Unity 3D GPU 虫群原型源码、自动化测试与 Editor 视觉验证（脱敏原创整理）
**收录日期**：2026-09-03
**来源日期**：2026-09-03
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐ (本地 Editor 实践、自动化测试与直接视觉验证)
**适用版本**：Unity 2022.3.62f3 / URP 14.0.12；其他版本与目标平台需复验

### 概要

面向“数千只飞虫先环绕物体飞行，再聚合成锤子、弓箭、斧头等预制 Mesh，并能连续换形”的 3D 游戏需求，一条可控且较小的实现路径是：在 Editor 中把目标 Mesh 烘焙为确定性的局部空间表面点云，用 ComputeShader 持久维护实例的位置、速度与动画相位，再通过 `Graphics.DrawMeshInstancedIndirect` 批量绘制，顶点阶段从位置 VAT（Vertex Animation Texture）读取每只虫子的形变。

本次 MVP 在 Unity 2022.3 中以 8,192 个永久实例完成了环绕、组装、保持形状、无缝换形、散开与返回环绕的闭环。Visual Effect Graph（VFX Graph）包虽然可用，但没有参与运行时；BatchRendererGroup（BRG）也未采用。这个结果证明的是 ComputeShader、间接实例化和 VAT 的组合路线，而不是对 VFX Graph 或 BRG 的否定性结论。

### 内容

#### 一、场景、目标与最小闭环

这个问题不是普通的“播放一个粒子特效”，而是同时包含四个需要保持一致的数据约束：

1. 每只虫子要有稳定身份，才能保留位置、速度和动画相位；
2. 任意预选 Mesh 要先转换成数量固定、位于 Mesh 局部空间的目标点；
3. 换形时不能销毁并重新生成整群虫子，也不能把位置瞬间覆盖为新目标；
4. 单只虫子的顶点动画要在大量 GPU 实例上独立播放，不能让 CPU 为每只虫子更新骨骼或矩阵。

本次 MVP 固定使用 8,192 个槽位。可观察状态序列为：

```text
Orbit
  -> Assemble
  -> HoldShape
  -> Retarget
  -> HoldShape
  -> Disperse
  -> Orbit
```

端到端数据路径如下：

```text
目标 Mesh
  -> Editor 面积加权采样
  -> 固定数量的局部空间点
  -> Morton 排序
  -> ShapeAsset
  -> Target A / Target B ComputeBuffer

稳定实例 ID + 状态机参数
  -> ComputeShader 更新 Persistent Agent Buffer
  -> 间接实例化绘制
  -> 顶点着色器按 Instance ID 读取虫子状态
  -> 按 Vertex ID 和实例相位采样 VAT
  -> 屏幕上可见的虫群与形状过渡
```

这条路径把“形状数据”“群体运动”和“单体动画”拆成三个独立层次，因此可以分别替换目标 Mesh、运动模型或昆虫资产，而不必重做整个系统。

#### 二、为什么 MVP 选择 ComputeShader 加间接实例化

候选技术并不是简单的互斥关系，它们解决问题的侧重点不同。

| 路线 | 更擅长的场景 | 对本 MVP 的判断 |
|---|---|---|
| VFX Graph | 快速制作粒子外观、事件和特效图逻辑 | Unity 2022.3 对应包已能解析，但稳定槽位、外部目标 Buffer、速度连续换形和自定义 VAT 的组合没有单独实测；因此本次既不采用，也不声称它不可行 |
| BatchRendererGroup | 大量渲染批次、异构实例数据、可见性与 LOD 管理 | 对固定容量、单 Mesh、单材质、单场景验证来说引入的管理复杂度较高，适合作为后续生产优化，而不是最小闭环起点 |
| 普通 `DrawMeshInstanced` | 少量实例、CPU 已有矩阵 | 单批数量有限，而且要求 CPU 组织矩阵，不符合让 GPU 持久维护数千个运动实例的目标 |
| ComputeShader + `DrawMeshInstancedIndirect` | 固定容量、单 Mesh/材质、GPU 端模拟、按实例 ID 取数据 | 能直接表达稳定 ID、持久速度、双目标 Buffer 和 VAT 相位，依赖少，适合作为 Unity 2022.3 的 MVP |

因此，选择 Compute/Indirect 是“按当前约束取最短可验证路径”，不是先证明其他路线失败后的被迫回退。

#### 三、把任意 Mesh 烘焙为局部空间表面点云

##### 1. 为什么必须是局部空间

ShapeAsset 保存的是源 Mesh 顶点坐标系中的点，而不是某个场景对象变换后的世界坐标。运行时统一用虫群控制器的 `localToWorld` 矩阵把模拟结果送到世界空间。

这样做有三个好处：

- 同一个点云可以跟随控制器整体平移、旋转和缩放；
- 烘焙结果不依赖临时摆放在场景里的 Transform；
- 形状资产可以跨场景复用，测试也能直接证明移动源对象不会改变采样结果。

如果把世界坐标误烘进资产，虫群一旦移动到另一个位置，目标点就会产生重复变换或仍粘在原场景位置。

##### 2. 面积加权的三角形选择

逐三角形平均分配点会使小三角形过密、大三角形过稀。正确做法是先计算所有非退化三角形的面积，构建累计分布，再让随机数落到累计面积区间中。某个三角形被选择的概率因此与它的表面积成正比。

在选中的三角形内，用两个均匀随机数 `u`、`v` 和平方根重心坐标进行均匀表面采样：

```text
r  = sqrt(u)
b0 = 1 - r
b1 = r * (1 - v)
b2 = r * v
p  = b0 * p0 + b1 * p1 + b2 * p2
```

直接用三个独立权重再归一化，或者直接线性使用 `u`、`v`，都会在三角形内部产生偏置。

实现还需要：

- 忽略零面积或数值退化三角形；
- 检查所有输出位置和法线是否为有限数；
- 有顶点法线时按相同重心坐标插值，没有时使用三角形面法线；
- 对空 Mesh、零点数和全退化 Mesh 明确报错，不生成半成品资产；
- Editor 烘焙时读取只读 Mesh 数据，不为了采样而永久打开导入资源的 Read/Write 开关。

##### 3. 固定 Seed 与 Morton 排序

固定随机种子保证同一个 Mesh、点数和 Seed 能产生逐元素一致的点云。确定性既方便测试，也避免重新烘焙后虫群映射无故变化。

每种形状独立采样后，可把局部包围盒归一化到统一坐标范围，为每个点计算 Morton Code，再按 Morton Code 稳定排序。Morton Code 把三维坐标的各轴比特交错到一个整数中，使空间上相近的点在一维序列里通常也较接近。

当 Target A 的第 `i` 个点与 Target B 的第 `i` 个点互相映射时，这种排序通常比完全随机的索引配对减少大范围交叉飞行。它的代价小、实现确定，但不是最优传输算法：

- 不保证总移动距离最短；
- 两个形状朝向、长宽比或拓扑差异很大时仍可能出现交叉；
- 对视觉要求更高时，可在离线阶段换成匈牙利算法、近似最优传输、分块最近邻或带语义区域的匹配。

##### 4. 表面点云不等于体积点云

面积加权采样只覆盖 Mesh 表面。它适合从自由视角辨认轮廓，但不会自动填充实体内部。若需求是有明显厚度的“虫群实体”，应另做体素化、内部拒绝采样、四面体采样或 SDF 体积采样；不能把表面采样结果描述成体数据。

#### 四、持久 Agent Buffer 与连续状态切换

每个实例在 GPU 中至少保存：

```hlsl
struct AgentData
{
    float3 position;
    float  phase;
    float3 velocity;
    float  padding;
};
```

8,192 个槽位只在初始化时创建一次。实例 ID 既是 Agent Buffer 的索引，也是目标点 Buffer 的索引和 VAT 相位的稳定来源。

##### 1. 环绕、塑形和散开的目标不同，积分器相同

- `Orbit`：根据稳定 ID、时间、半径和高度在 GPU 中生成程序化环绕目标；
- `Assemble` / `HoldShape`：读取 Target A 中对应索引的局部点；
- `Retarget`：在 Target A 与 Target B 的对应点之间使用平滑插值；
- `Disperse`：根据当前位置相对中心的方向施加向外加速度。

除散开状态外，核心运动可以概括为阻尼弹簧：

```text
acceleration = (target - position) * springStrength
             - velocity * damping
             + perAgentBuzz
```

随后限制最大加速度和最大速度，再积分速度与位置。单帧 `deltaTime` 还应设上限，以免 Editor 卡顿或断点恢复后产生爆炸速度。

##### 2. 双目标 Buffer 是无缝换形的关键

运行时预先分配两个等容量目标 Buffer：Active 和 Incoming。切换形状时只把新点云上传到 Incoming，并重置换形进度；不重新创建 Agent Buffer，也不把当前速度清零。

```csharp
// 开始换形：只更新新目标
incomingTargetBuffer.SetData(nextShapePoints);
transitionProgress = 0f;

// GPU 每帧读取平滑后的目标
target = lerp(targetA[id], targetB[id], SmoothStep01(transitionProgress));

// 换形完成：交换引用，不搬运整个 Agent Buffer
(activeTargetBuffer, incomingTargetBuffer) =
    (incomingTargetBuffer, activeTargetBuffer);
```

速度连续性来自同一个 `AgentData.velocity` 在全过程中持续积分。若换形时直接覆盖 `position`，即使最终轮廓正确，也会出现整群瞬移；若销毁并重建特效，实例相位、速度和稳定身份都会丢失。

#### 五、间接实例化绘制与 VAT 单体动画

##### 1. 一次提交固定容量实例

间接参数 Buffer 保存 Mesh 的索引数量、实例数量、索引起点、基础顶点和起始实例。C# 每帧对单一 Mesh、材质和 SubMesh 调用一次 `Graphics.DrawMeshInstancedIndirect`，由 GPU 根据参数绘制全部 8,192 个实例。

这里的“一次”指 C# 侧的一次间接绘制提交，不等于已经用帧调试器证明整个渲染管线只有一个 Draw Call；阴影、多 Pass、编辑器叠加和管线行为仍应在目标场景单独测量。

材质通过 `SV_InstanceID` 读取对应的 Agent 数据，按速度构建朝向基向量，再将实例局部顶点放到 Agent 位置。绘制时必须提供足够保守的世界空间 Bounds；Bounds 太小会导致整群虫子被 CPU 视锥剔除而突然消失。

##### 2. 用球体正弦形变验证 VAT 数据通路

为了先验证技术闭环而不等待正式昆虫资产，本次生成了一个拓扑固定的低模椭球，并把 16 帧正弦顶点位移烘焙进 `RGBAHalf` 纹理：

```text
纹理宽度 = Mesh 顶点数
纹理高度 = 动画帧数
像素 RGB  = 对应顶点在该帧的位置偏移
```

顶点着色器按 `SV_VertexID` 选择纹理列，按时间和 Agent 的稳定相位选择纹理行：

```hlsl
AgentData agent = agents[input.instanceID];
float normalized = frac(globalTime * vatFps / frameCount + agent.phase);
uint frame = min((uint)floor(normalized * frameCount), (uint)frameCount - 1u);
float3 offset = vatTexture.Load(int3(input.vertexID, frame, 0)).xyz;
float3 animatedPosition = input.positionOS.xyz + offset * vatAmplitude;
```

初始化时由实例 ID 哈希得到 `phase`，可以避免所有虫子同一时刻以相同姿态扭动。相位保存在持久 Agent Buffer 中，因此换形不会重置动画。

这个球体 VAT 与正式昆虫 VAT 在“每实例选择动画相位、每顶点读取逐帧位移、保持拓扑不变”的数据通路上等价，但不证明真实虫子的以下内容已经解决：

- 翅膀与身体的剪影质量；
- DCC 导出、法线或切线 VAT；
- 材质、透明翅膀、光照和阴影；
- 动画压缩、插值、LOD 和远距离替代表示。

#### 六、实现顺序与验收过程

这类实验应先锁定可观察验收条件，再按依赖关系建立最小闭环，而不是先堆视觉效果。

##### 1. 先建立可测试的数据层

第一阶段只处理点云和状态语义：

- 单三角形采样点必须在三角形内；
- 不同面积三角形的采样比例应近似面积比；
- 相同 Seed 必须得到相同结果；
- 场景 Transform 变化不能影响局部空间点；
- Read/Write 关闭的导入 Mesh 仍可在 Editor 烘焙；
- 空输入、错误点数、非有限值和退化 Mesh 必须被拒绝；
- Morton 排序不能丢点或产生非有限键；
- 非法状态跳转必须失败；
- 提交 Retarget 后只交换目标槽位，实例代数不变。

##### 2. 再生成最小验证资产

用程序化低模几何生成锤子、弓箭和斧头，然后用相同点数与 Seed 烘焙三个 ShapeAsset。这样可以先验证算法、资源持久化和自由视角轮廓，不依赖外部美术资产。

视觉检查不是一次通过：斧头初版刀刃辨识度不足，扩大刀刃后重新烘焙点云并重新检查正面与斜视角。这说明测试通过只能证明数据约束，不能替代轮廓可读性审查。

##### 3. 最后接入 GPU 模拟、渲染与交互

运行场景提供自由旋转、平移、缩放，相应按键或按钮触发环绕、组装、前后换形、散开和自动演示。诊断面板显示状态、形状、后端、存活数、容量、代数与帧时间，使测试期间可以直接发现重新生成、容量变化或状态错误。

#### 七、验证结果与证据边界

在 Unity 2022.3.62f3、URP 14.0.12、Apple M5 / Metal 的真实 Editor 场景中，本次实验得到以下结果：

- 8,192 个持久实例在完整状态序列中保持存活，代数保持为 1；
- 锤子、弓箭和加宽刀刃后的斧头从多个自由相机角度可辨认；
- 换形 25%、50%、75% 中间帧都保持有虫群可见，没有整群单帧消失；
- 两个不同时刻的近景显示实例间存在不同形变，VAT 数据通路同时由 Shader 索引逻辑佐证；
- EditMode 测试 19/19 通过，PlayMode 测试 2/2 通过；
- 正式验证结束后的 Console 为 0 error、0 warning；
- 共检查 15 张正式截图，覆盖 Orbit、三种形状、多角度、Retarget 中间帧、Disperse、VAT 时刻和诊断界面。

证据强度必须分层理解：

| 证据 | 能证明 | 不能单独证明 |
|---|---|---|
| EditMode 测试 | 采样、确定性、局部空间、排序和状态机不变量 | 形状是否肉眼可辨、换形是否自然 |
| PlayMode 测试 | 同一控制器、代数和容量在状态序列中保持 | 所有帧都没有视觉瑕疵 |
| 静态截图 | 某些时刻真实渲染且轮廓可读 | 连续运动、稳定帧率 |
| 两个 VAT 时刻与 Shader 代码 | VAT 形变和错相数据路径工作 | 正式昆虫美术质量 |
| 本地 Editor 时间样本 | 当前机器、当前场景下的局部观察 | 前台 FPS、Standalone 或目标平台性能 |

曾记录到一次后台、锁屏状态的时间样本：GPU 约 9.13 ms、主线程约 3.55 ms、渲染线程约 1.81 ms；但整帧间隔约 100.97 ms，明显受 Editor 失焦和系统限速影响。因此这些分项只能保留为本地观察，不能换算成正式 FPS，也不能作为任何发布平台认证。

此外，下列内容没有在本次 MVP 中验证：

- VFX Graph 的外部 StructuredBuffer、稳定槽位与自定义 VAT 组合；
- BRG、逐实例视锥/遮挡剔除、LOD、流式加载；
- 邻域 Boids、碰撞、避障和导航；
- Standalone Player、Windows、主机、移动端或 XR；
- 真实昆虫 Mesh、生产级 VAT、材质与灯光。

#### 八、可复用落地步骤

要把这条路线迁移到另一个 Unity 3D 项目，可以按以下顺序实施：

1. 先固定最大实例容量 `N`，所有 ShapeAsset 都必须恰好包含 `N` 个有效点；
2. 在 Editor 中对目标 Mesh 做局部空间面积加权采样，并以固定 Seed 保存结果；
3. 对每个点云使用一致的空间排序策略，先获得足够可用的跨形状索引对应；
4. 一次性分配 Agent、Target A、Target B 和 Indirect Args Buffer；
5. 初始化 Agent 的位置、速度和稳定动画相位，运行期间不要因换形重建；
6. 用明确状态机驱动 Orbit、Shape、Retarget 和 Disperse 目标；
7. 用阻尼弹簧追踪目标，保留速度并限制 `deltaTime`、加速度和最大速度；
8. Retarget 时只上传 Incoming 点云，过渡完成后交换目标 Buffer 引用；
9. 在顶点 Shader 中用 Instance ID 读取 Agent，用 Vertex ID 和相位读取 VAT；
10. 为整个可能运动范围设置正确绘制 Bounds，并加入资源释放与非法配置报错；
11. 分别验证数据不变量、PlayMode 生命周期、连续视觉帧和目标平台性能。

#### 九、常见失败方式

- **直接把目标点写入当前位置**：轮廓会立刻出现，但没有飞行过程，速度也失去意义。
- **每次换形重建粒子系统或 Agent Buffer**：会重置速度、VAT 相位和稳定身份，容易产生闪烁。
- **所有点随机配对**：大量路径横穿整个形状；可先用 Morton 排序降低混乱，再按需求升级匹配算法。
- **把场景 Transform 烘进 ShapeAsset**：资产无法在新的位置与朝向下可靠复用。
- **把表面采样称为体积采样**：自由视角下会暴露内部空洞，方案边界也被误判。
- **所有实例使用同一 VAT 时间**：群体会像一个同步抖动的物体，应从稳定 ID 派生相位。
- **绘制 Bounds 太小**：Unity 会把整次间接绘制剔除，表现为某些视角或移动位置突然消失。
- **把包安装当成路线验证**：VFX Graph 能被 UPM 解析，不代表外部 Buffer、状态连续性和 VAT 已经跑通。
- **把后台 Editor 样本当成发布性能**：需要前台预热、稳定采样、Standalone 和目标设备证据。

#### 十、结论

对于“固定数量、单一昆虫 Mesh、多个预烘焙目标形状、要求平滑切换”的实验，`Editor 点云烘焙 + Persistent ComputeShader 模拟 + 双目标 Buffer + DrawMeshInstancedIndirect + VAT` 是一条职责清楚、依赖较少、容易直接验证的 Unity 2022.3 MVP 路线。

它最重要的设计原则不是某个 API，而是保持三种连续性：实例身份连续、速度连续、动画相位连续。只要这三者不因状态或目标变化而重建，Orbit、Assemble、Retarget 和 Disperse 就能共享同一批 GPU 实例。进入生产阶段后，再依据真实瓶颈决定是否增加 GPU 剔除和 LOD、迁移 BRG，或单独验证 VFX Graph 后端；不应在最小闭环阶段预先承担所有复杂度。

### 相关记录

- [ComputeShader GPGPU 基础概念](./compute-shader-gpgpu-basics.md) - 补充线程组、StructuredBuffer 和 Dispatch 的基础概念。
- [GPU ComputeShader 草渲染与视锥剔除](./gpu-grass-large-scale-rendering.md#gpu-grass-compute-shader) - 对照另一种 ComputeShader 驱动的大规模实例渲染实践。
- [GPU 视锥剔除 ComputeShader 实现](./gpu-frustum-culling-compute-shader.md) - 后续加入 GPU 可见性筛选时的扩展阅读；本次虫群 MVP 尚未实现逐实例 GPU 剔除。

### 验证记录

- [2026-09-03] 初次记录。基于 Unity 2022.3.62f3 / URP 14.0.12 本地原型源码、19 项 EditMode 测试、2 项 PlayMode 测试、15 张正式 Editor 截图和一次受后台限速影响的时间样本整理；项目名称、绝对路径和内部任务标识已脱敏。
- [2026-09-03] 已明确区分当前验证的 ComputeShader + DrawMeshInstancedIndirect 路线，以及仅安装但未验证的 VFX Graph、未采用的 BRG 和未验证的生产平台范围。

---

# 3ds Max 到 Unity 的平滑组与 BlendShape 法线异常排查

**标签**：#unity #3dsmax #fbx #experience #troubleshooting
**来源**：实践总结 - 3ds Max、FBX 与 Unity 对照实验
**收录日期**：2026-07-17
**来源日期**：2026-07-17
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐（本地对照实验验证）
**适用版本**：3ds Max 2020、FBX Exporter 2019.2、Unity 2022.3 LTS

### 概要

当带有 Morph/BlendShape 的低多边形模型导入 Unity 时，可能出现两种看似矛盾的结果：启用 `Legacy Blend Shape Normals` 后造型符合预期但提示“mesh has no smoothing groups”，关闭 Legacy 后警告消失，表情变形时部分硬面却看起来被平滑。本次实测确认，根因是源网格没有有效平滑组数据，导致 Unity 无法稳定地为基础网格与 BlendShape 使用同一套硬边边界；正确做法是在 3ds Max 中实际编码平滑组，并让 FBX 导出和 Unity 导入设置保持一致。

### 内容

#### 问题表现

测试对象是一个使用 Skin 与 Morph 的低多边形头部网格。基础姿态外观正常，但将某个表情 BlendShape 从 0 调到 100 后，额头、嘴角等区域的硬面明暗发生变化，看起来像被平滑。

Unity 中观察到两组现象：

- 启用 `Legacy Blend Shape Normals`：低多边形外观符合预期，但每个 BlendShape 都可能出现 `Can't generate normals ... mesh has no smoothing groups` 警告。
- 关闭 Legacy：可以不出现上述旧版警告，但在缺少有效平滑组时，Unity 可能按夹角或回退规则重新计算变形法线，使原本需要断开的硬边发生平均。
- 将基础网格法线设为 `Calculate`、BlendShape 法线设为 `Import` 时，两种策略不一致，Unity 会提示它将改为重新计算 BlendShape 法线。

#### 平滑组实际控制什么

平滑组不是增加几何面数，也不会直接改变顶点位置。它描述相邻多边形之间是否共享平滑法线：

- 相邻面的平滑组位掩码有交集时，公共边可以参与法线平均，视觉上形成连续曲面。
- 相邻面的平滑组位掩码没有交集时，公共边保持硬边，视觉上保留折面。
- 所有面都为平滑组 0，表示 DCC 没有提供可供下游重建硬边关系的有效平滑组集合。FBX 导出窗口即使勾选“平滑组”，也不能凭空补出源模型中不存在的数据。

对于需要保持全硬边的 Low Poly 模型，不必为每个面分配全局唯一的编号；只需保证共享边且需要保持硬边的相邻面使用互不相交的平滑组。互不相邻的面可以复用编号。

#### 根因定位过程

1. 固定 Unity Scene View 的观察角度、材质、灯光和 BlendShape 权重，对比 Legacy 开关前后的表现，排除 Game View 与 Scene View 视角不同造成的误判。
2. 在 3ds Max 中检查基础 Editable Poly 的多边形平滑组，确认测试网格所有面均为平滑组 0。
3. 对比静态网格、Skin 网格、显式法线网格及弯曲姿态，确认“添加 Skin 就必然丢失平滑组”不是本例的直接根因。
4. 复制源场景，仅对测试头部写入有效平滑组；先以 1° 阈值执行 Auto Smooth，再检查并处理仍为 0 的面，使需要保持硬边的相邻面不共享平滑组。
5. 重新保存场景并在新的 3ds Max 进程中加载，复核拓扑、Skin、Morph 和平滑组均未丢失。
6. 导出新的 FBX，确认文件包含 Smoothing Layer 数据，同时保留 Skin、骨骼层级和 BlendShape。
7. 在 Unity 中关闭 Legacy，使用一致的 Calculate/Calculate 策略重新导入。警告消失，BlendShape 保留，低多边形硬边在变形前后维持预期表现。

#### 3ds Max 处理要点

在基础网格层处理，而不是只在导出窗口中改设置：

1. 选中目标网格，进入 Editable Poly 的“多边形”子对象级别。
2. 全选多边形，在“多边形：平滑组”区域检查当前编号。
3. 使用较小阈值的 Auto Smooth 作为起点；Low Poly 全硬边测试可从 1° 开始。
4. 检查是否仍有未编码的平滑组 0 面。对于需要保持硬边的相邻面，分配互不相交的平滑组；非相邻面可以复用组号。
5. 保持 Morpher 与 Skin 修改器及其依赖层级，不要为了处理平滑组而破坏顶点顺序或 BlendShape 拓扑一致性。
6. 保存到新文件，避免覆盖源资产，并重新打开一次验证持久化结果。

Auto Smooth 不是“执行后必然全部正确”的保证。最终判断依据是面上的实际平滑组数据和硬边关系，而不是按钮是否点击过。

#### 已验证的 FBX 导出配置

使用“导出选定对象”，包含目标网格及 Skin 所需的骨骼父级。关键配置如下：

| 配置 | 值 |
|---|---|
| 格式 | Binary FBX |
| 单位 | m |
| Up Axis | Y |
| Smoothing Groups | 开启 |
| Tangents and Binormals | 关闭 |
| Triangulate | 开启 |
| Skin | 开启 |
| Shape/Morph | 开启 |
| Bake Animation | 关闭 |
| Smooth Mesh/Subdivision | 关闭 |
| Cameras / Lights / Embed Media | 关闭 |

`Smoothing Groups` 是写出已有数据的开关，不是生成器。如果源网格仍全部为平滑组 0，仅开启该项无法解决问题。

#### 已验证的 Unity 导入配置

| 配置 | 值 |
|---|---|
| Legacy Blend Shape Normals | 关闭 |
| Normals | Calculate |
| Blend Shape Normals | Calculate |
| Normals Mode | Unweighted |
| Smoothness Source | From Smoothing Groups |
| Smoothing Angle | 1 |
| Tangents | None |

基础网格法线与 BlendShape 法线应采用配套策略。若一个设为 `Calculate`、另一个设为 `Import`，Unity 会回退到重新计算并产生额外警告，不能作为稳定的最终配置。

#### 为什么 Legacy 表现正常却仍有警告

警告表示旧版 BlendShape 法线生成流程需要平滑组，但 FBX 没有提供有效数据。在本次版本和资源组合中，失败后的回退结果恰好没有把 Low Poly 硬边重新平均，因此视觉上更接近预期；这只是失败路径的副作用，不代表输入数据完整，也不是可依赖的资产规范。

因此不能把“看起来正常”当成“导入正确”。应同时满足：

- Console 没有相关 FBX/BlendShape 法线警告。
- BlendShape 从 0 到 100 的过程中，预期硬边没有发生异常明暗连续化。
- 骨骼、Skin、BlendShape 数量和名称完整。
- 相同视角、材质和光照条件下，对比原始姿态与极限表情。

#### 可复用排查清单

1. 先区分位置变形异常和法线明暗异常，不要仅凭轮廓判断。
2. 固定 Scene View 视角和光照，并分别检查 BlendShape 0、50、100。
3. 检查源网格是否真的含有非零平滑组，而不是只看 FBX 导出勾选项。
4. 检查 FBX 是否写出了 Smoothing Layer、Skin 和 BlendShape 数据。
5. 保证 Unity 的基础法线与 BlendShape 法线策略一致。
6. 清空 Console 后重新导入，避免旧警告干扰判断。
7. 将静态、Skin、Morph、显式法线作为独立变量做对照，不要一次改变多个条件。
8. 对修复后的 Max 文件重新打开验证，再导出 FBX，防止只在当前编辑器会话中暂时生效。

#### 结论边界

本记录确认的是“源网格缺少有效平滑组时，Unity 的 BlendShape 法线计算无法稳定保持 Low Poly 硬边”这一具体链路。它不能推出所有蒙皮后法线异常都由平滑组造成；修改器顺序、显式法线、负缩放、镜像、拓扑变化和不同 FBX 插件版本仍需单独排查。

### 相关记录

- [3ds Max 蒙皮后法线异常问题调查](./3dsmax-skin-normal-fbx-export.md) - 相邻问题记录；该记录侧重 Skin 与导出法线，本记录侧重平滑组和 BlendShape 法线。

### 验证记录

- [2026-07-17] 初次记录。通过源场景、补齐平滑组的场景副本、对应 FBX 以及 Unity 导入设置进行对照验证；在关闭 Legacy 的情况下消除相关警告，并保持 BlendShape 变形时的 Low Poly 硬边表现。
- [2026-07-17] 完成脱敏：删除真实项目名、内部目录、本机绝对路径、用户名、角色与资源标识；未保存含项目层级和资产名称的截图，仅保留可复用参数与技术结论。

---

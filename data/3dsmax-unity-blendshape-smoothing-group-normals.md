# 3ds Max 到 Unity 的平滑组与 BlendShape 法线异常排查

**标签**：#unity #3dsmax #fbx #experience #troubleshooting
**来源**：实践总结 - 3ds Max、FBX 二进制数据与 Unity Mesh 对照实验，并结合 Unity / Autodesk 官方资料复核
**收录日期**：2026-07-17
**来源日期**：2026-07-17
**更新日期**：2026-07-20
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐（本地文件与下游 Mesh 交叉验证，并由官方资料佐证）
**适用版本**：3ds Max 2020、FBX Exporter 2019.2 / 2020.x、Unity 2022.3 LTS

### 概要

带 Morph/BlendShape 的低多边形模型导入 Unity 后，可能出现“基础姿态正常、变形时硬面明暗异常”，或“Legacy 模式视觉正常但提示缺少平滑组”。直接审计源 MAX、FBX 二进制数组和 Unity 最终 Mesh 后确认：基础法线、BlendShape 法线差量和平滑边界是三类独立数据；当 FBX 只有可用的基础法线，却没有与之匹配的 Shape 法线时，`Import / Import` 会触发 FBX SDK 回退并产生错误法线差量。稳定方案是让基础网格与 BlendShape 使用同一套计算规则，或保证 DCC 真正导出了匹配的基础/Shape 法线和有效平滑组。

### 内容

#### 问题表现

测试对象是使用 Skin 与 Morph 的低多边形测试网格。基础姿态外观正常，但某些变形通道权重从 0 调到 100 后，局部折面明暗发生异常变化，看起来像被平滑或法线方向呆滞。

常见现象包括：

- `Legacy Blend Shape Normals` 开启时，Low Poly 外观符合预期，但 Console 报告 `mesh has no smoothing groups`。
- Legacy 关闭且基础/BlendShape 法线都设为 `Import` 时，警告消失，但变形后的法线严重偏离几何。
- 基础法线设为 `Calculate`、BlendShape 法线设为 `Import` 时，Unity 为每个 Shape 警告并改为重新计算。
- `Normals=Import + Blend Shape Normals=Calculate` 在极限权重可能看起来正确，但中间权重仍可能因两套基准不一致而出现插值伪影。

#### BlendShape 法线的数据原理

BlendShape 不只保存位置变化，也可以保存法线变化。简化表达为：

```text
位置：P(w) = P0 + w × ΔP
法线：N(w) = normalize(N0 + w × ΔN)
```

- `P0` / `N0`：基础姿态的位置和法线。
- `ΔP`：形态键位置差量。
- `ΔN`：形态键法线差量。
- `w`：形态键权重。

Unity 运行时通常使用导入阶段生成的 `ΔN`，不会因为顶点位置变化而自动按所有三角形重新计算法线。因此：

- `ΔP` 正确、`ΔN` 错误：轮廓和变形动作正常，但明暗、高光或 Low Poly 折面异常。
- `ΔN = 0`：法线停留在基础姿态；可能仍显得“很 Low Poly”，但并未严格跟随变形几何。
- `N0` 与 `ΔN` 由不同算法生成：权重 0 或 100 可能看似正常，中间权重仍可能错误。

#### 直接文件审计确认的根因

本次对源场景、原始 FBX、补平滑组后的场景副本和对应 FBX 分层审计，得到以下事实：

1. 源 MAX 的测试网格包含 Skin、Morph 和多个变形通道；所有面平滑组均为 0。
2. 在 3ds Max 中把 Morph 权重调到 100 后，几何位置和视口计算出的面角法线都会变化，说明 Morph 本身没有锁死法线。
3. 原始 FBX 有基础网格法线，但完全没有 Smoothing Layer。
4. 原始 FBX 的多个 Shape 节点虽然包含 Normal 数组，但所有 Shape Normal 数值均为 0，即不存在可直接使用的法线差量。
5. 给源网格写入有效平滑组并重新导出后，FBX 出现 Smoothing Layer，Shape 中也出现非零法线差量。
6. 仅“补平滑组并导出”仍不能保证 Unity 2022.3 的现代 `Import / Import` 路径正确；测试中的修复 FBX 在该组合下仍出现错误，而一致的 `Calculate / Calculate` 路径稳定。

因此，不能把问题简单归因于 Skin 或 Morpher。直接根因是：原始 FBX 没有可用的 Shape 法线，也没有供下游重建硬边关系的平滑组；Unity 的 Import 路径只能调用 FBX SDK 回退计算，而回退算法与基础网格法线不一致。

#### 为什么 Import / Import 无警告却会异常

`Normals=Import` 使用 FBX 中的基础法线；`Blend Shape Normals=Import` 希望使用 FBX 中的 Shape 法线。如果 Shape 没有可用法线，Unity 2022.3 会让 FBX SDK 自行生成。

FBX SDK 生成 Shape 法线的方法可能与基础法线来源不同，于是导入后得到错误的非零 `ΔN`。这条现代 Import 路径可能不报告警告，所以“没有警告”不能证明法线数据正确。

官方 Issue 也确认过：当 BlendShape 没有有效法线时，FBX SDK 生成的结果可能与基础网格计算方式不同，形成非零差量和可见伪影；另有 Issue 记录部分 FBX 的 BlendShape 法线在 Import 模式下会损坏。

#### 为什么 Legacy 表现正常却仍有警告

Legacy 打开后，Inspector 会隐藏 `Blend Shape Normals`。隔离测试确认，被隐藏的旧值不会影响结果，真正起作用的是基础 `Normals`：

- `Legacy + Normals=Calculate`：旧路径会因缺少平滑组报告警告，但最终法线数据与现代 `Calculate / Calculate` 基本一致，因此可以出现“视觉正确但有警告”。
- `Legacy + Normals=Import`：缺少平滑组时可能生成 `ΔN=0`，让形态键继续使用基础姿态法线；这可能保持硬朗的 Low Poly 明暗，但法线并未正确跟随几何。
- 补齐有效平滑组后，Legacy 可完成旧式重建并消除对应警告，但它仍是兼容路径，不应作为新资产规范的首选。

警告描述的是 Legacy 尝试使用缺失平滑组的分支失败，不等于最终 Mesh 一定没有可用法线。反过来，没有警告也不等于 Import 出来的 `ΔN` 正确。

#### Unity 法线配置组合的实际作用

| Normals | Blend Shape Normals | 实际作用 | 风险与适用性 |
|---|---|---|---|
| Import | Import | 基础法线和 Shape 法线都取自 FBX；Shape 法线缺失时由 FBX SDK 回退生成 | 只有 FBX 同时包含匹配的基础/Shape 法线且下游验证通过时才可靠；本例异常 |
| Import | Calculate | 基础法线来自 DCC，Shape 法线由 Unity 计算 | 两套基准可能不一致；Unity 2022.3 的中间权重存在已知风险，不作为稳定规范 |
| Calculate | Import | 基础法线由 Unity 计算，却要求导入 Shape 法线 | Unity 会逐 Shape 警告并强制改为重新计算；结果近似 Calculate/Calculate，但不应保留这种配置 |
| Calculate | Calculate | 基础与 Shape 使用相同 Unity 算法 | 本例最稳定，推荐 |
| Import | None | 导入基础法线，Shape `ΔN=0` | 形变时法线冻结 |
| Calculate | None | 计算基础法线，Shape `ΔN=0` | 形变时法线冻结 |
| None | — | Mesh 不保存法线 | 仅适合不受实时光照影响的渲染路径 |

基础姿态下，`Import` 与 `Calculate + From Angle 0°` 可能看起来非常接近，因为 FBX 基础法线本身就可能是逐面硬法线。但这不能推出 Shape 法线也可导入；基础 `N0` 正常与 `ΔN` 正常是两件事。

#### Smoothness Source 和 Smoothing Angle

Smoothness Source 决定“哪些边可以共享平滑法线”：

| 设置 | 实际作用 |
|---|---|
| Prefer Smoothing Groups | FBX 有平滑组时使用平滑组，没有时回退到角度规则 |
| From Smoothing Groups | 只使用 FBX 平滑组；文件没有平滑组时会警告或回退 |
| From Angle | 忽略平滑组，按相邻面夹角决定硬边 |
| None | 不根据硬边拆分法线，容易得到连续平滑结果 |

`Smoothing Angle` 主要在 `From Angle` 下决定边界：

- 0°：几乎所有非共面的边都保持硬边，适合全硬边 Low Poly 测试。
- 角度升高：更多相邻面参与平滑，硬边拆分减少，外观趋向连续。
- 180°：接近全部可连接面参与平滑，不适合需要明显折面的 Low Poly 资产。

Unity 的 `Mesh.vertexCount` 可能明显高于 DCC 控制点数。法线硬边、UV 缝、材质、顶点色、蒙皮数据等都可能导致顶点拆分；不能只凭 Unity 顶点数判断源拓扑是否改变。

#### Normals Mode

Normals Mode 决定已经允许平滑的多个面如何平均法线，不负责定义硬边边界：

- `Unweighted`：每个相邻面权重相同。
- `Area Weighted`：面积大的面影响更大。
- `Angle Weighted`：顶点角度大的面影响更大。
- `Area and Angle Weighted`：同时考虑面积和角度。
- `Unweighted Legacy`：旧算法，仅用于兼容旧资产。

如果一条边已经是完全硬边，每个面使用独立法线，权重模式几乎不起作用。它主要改变平滑区域的高光与明暗过渡。

#### 平滑组实际控制什么

平滑组不增加几何面数，也不直接改变顶点位置。它描述相邻多边形之间是否共享平滑法线：

- 相邻面的平滑组位掩码有交集时，公共边可以参与法线平均。
- 位掩码没有交集时，公共边保持硬边。
- 所有面都为平滑组 0，表示没有向下游提供可用于重建硬/软边关系的有效平滑组集合。

Low Poly 全硬边不需要给每个面分配全局唯一编号；只需保证共享边且需要断开的相邻面没有共同平滑组。互不相邻的面可以复用编号。

FBX 导出窗口中的 `Smoothing Groups` 只是写出已有数据的开关，不会为平滑组 0 的源模型凭空生成正确分组。

#### 推荐方案 A：现有全硬边 Low Poly 资源

当现有 FBX 的基础逐面法线正常，但 Shape 法线不可用，且目标就是近似全硬边效果时：

| 配置 | 值 |
|---|---|
| Legacy Blend Shape Normals | 关闭 |
| Normals | Calculate |
| Blend Shape Normals | Calculate |
| Normals Mode | Unweighted |
| Smoothness Source | From Angle |
| Smoothing Angle | 0° |
| Tangents | None（没有法线贴图时） |

该配置让基础姿态和 Shape 使用同一套 Unity 算法，并通过 0° 规则维持 Low Poly 硬边。它是现有错误 FBX 的稳定修复方案，但没有补齐 DCC 层的硬/软边语义。

#### 推荐方案 B：正式修复资产

在 3ds Max 中：

1. 在基础 Editable Poly 层为目标网格写入真实平滑组。
2. 检查不应平滑的相邻面没有共同平滑组，且不存在遗漏的平滑组 0 面。
3. 保持 Morph、Skin 及其拓扑依赖，不改变顶点顺序。
4. 保存到新文件并重新打开验证持久化结果。
5. 导出 FBX 时开启 Smoothing Groups、Skin 和 Shape/Morph。

在 Unity 中：

| 配置 | 值 |
|---|---|
| Legacy Blend Shape Normals | 关闭 |
| Normals | Calculate |
| Blend Shape Normals | Calculate |
| Normals Mode | Unweighted |
| Smoothness Source | From Smoothing Groups 或 Prefer Smoothing Groups |
| Tangents | None（无切线空间法线贴图时） |

这种方案把硬/软边边界作为美术资产的一部分写入 FBX，再由 Unity 用同一算法计算基础与 Shape 法线，适合长期资产规范。

#### Import / Import 何时才适用

只有同时满足以下条件时，才考虑 `Import / Import`：

1. FBX 中基础网格和每个 Shape 都存在非零、语义正确的法线数据。
2. 基础与 Shape 法线由同一 DCC 算法和同一硬/软边规则生成。
3. Unity 导入后检查实际 `deltaNormals`，而不是只看 Inspector 无警告。
4. 固定视角、材质与灯光，验证权重 0、50、100，而不是只看极限权重。
5. 多个 BlendShape 同时叠加时也没有累计伪影。

只补平滑组、只消除警告、或只验证基础姿态，都不足以证明 Import 路径正确。

#### 已验证的 FBX 导出要点

使用“导出选定对象”，包含目标网格及 Skin 所需骨骼父级。关键配置：

| 配置 | 值 |
|---|---|
| 格式 | Binary FBX |
| 单位 | 与项目约定一致 |
| Up Axis | Y |
| Smoothing Groups | 开启 |
| Split Per-Vertex Normals | 关闭（除非面对旧 MotionBuilder 工作流） |
| Tangents and Binormals | 无法线贴图时关闭 |
| Triangulate | 开启或在 DCC 中固定三角化结果 |
| Skin | 开启 |
| Shape/Morph | 开启 |
| Bake Animation | 无需动画时关闭 |
| Smooth Mesh/Subdivision | 关闭 |
| Cameras / Lights / Embed Media | 无需时关闭 |

`Split Per-Vertex Normals` 会复制顶点并转换几何，Autodesk 将其定位为旧 MotionBuilder 硬边兼容流程，不应当作本问题的通用修复开关。

#### 可复用排查清单

1. 区分位置变形异常和法线明暗异常，不要只看轮廓。
2. 固定 Unity Scene View 视角、材质和光照，分别检查权重 0、50、100。
3. 在 3ds Max 中检查源面是否真的含有非零平滑组，而不是只看导出勾选项。
4. 检查 Max 视口法线是即时计算结果，还是存在可导出的显式法线/Shape 法线。
5. 直接检查 FBX 是否含 Smoothing Layer、基础 Normal 与 Shape Normal，并确认 Shape Normal 不是全零。
6. 在 Unity 中读取 `Mesh.GetBlendShapeFrameVertices` 返回的 `deltaVertices` 和 `deltaNormals`，确认法线差量是否实际存在且方向合理。
7. 保证基础法线与 BlendShape 法线使用一致策略。
8. 清空 Console 后重新导入，避免旧警告干扰。
9. 对修复后的 Max 文件重新打开验证，再导出 FBX，防止结果只存在于当前编辑器会话。
10. 把静态、Skin、Morph、平滑组、显式法线和导入算法作为独立变量做对照。

#### 结论边界

本记录确认的是一条具体数据链：源网格缺少有效平滑组，FBX 又没有可用 Shape 法线时，Unity 的 BlendShape Import 路径可能生成与基础法线不一致的 `ΔN`；一致的 Calculate 路径可以稳定规避。

它不能推出所有蒙皮或变形法线异常都由平滑组造成。修改器顺序、显式法线、负缩放、镜像、切线空间、拓扑变化、不同 FBX 插件版本和不同 Unity 版本仍需单独排查。FBX 文件也无法完整还原当时所有导出窗口选择，资产来源版本必须另行追溯。

### 参考链接

- [Unity 2022.3 Model Import Settings](https://docs.unity3d.com/2022.3/Documentation/Manual/FBXImporter-Model.html) - Normals、Blend Shape Normals、Smoothness Source 和 Tangents 的官方定义。
- [Unity Issue 1160752](https://issuetracker.unity3d.com/issues/blenshape-normals-are-not-being-imported-correctly) - FBX SDK 在部分 BlendShape Normal Import 场景产生伪影，Legacy 可作为兼容回避路径。
- [Unity Issue UUM-122300](https://issuetracker.unity3d.com/issues/blend-shape-normals-are-incorrect-for-fbx-files-when-normals-are-set-to-import-and-blend-shape-normals-are-set-to-calculate) - `Normals=Import + Blend Shape Normals=Calculate` 使用不一致基准生成差量的问题。
- [Autodesk 3ds Max FBX Geometry](https://help.autodesk.com/cloudhelp/2024/ENU/3DSMax-Interoperability/files/GUID-249100FE-67BE-43B8-AF12-D20703CDF8D1.htm) - Smoothing Groups、Split Per-Vertex Normals、Tangents 和 Triangulate 的官方说明。

### 相关记录

- [3ds Max 蒙皮后法线异常问题调查](./3dsmax-skin-normal-fbx-export.md) - 相邻问题记录；该记录侧重 Skin、显式法线与导出条件，本记录侧重平滑组和 BlendShape 法线差量。

### 验证记录

- [2026-07-17] 初次记录。通过源场景、补齐平滑组的场景副本、对应 FBX 以及 Unity 导入设置进行对照验证；在关闭 Legacy 的情况下消除相关警告，并保持 BlendShape 变形时的 Low Poly 硬边表现。
- [2026-07-20] 深化验证：使用独立 3ds Max 批处理检查基础网格、Morph 通道、平滑组和变形前后法线；直接解析原始/修复 FBX 的 Mesh、Shape、Normal 与 Smoothing 数组；在 Unity 2022.3 隔离项目中测试多组 Normals、Blend Shape Normals、Legacy、Smoothness Source、Smoothing Angle 和 Normals Mode 组合，并检查权重 0、50、100 下的 `deltaNormals` 与几何法线。确认原始 Shape Normal 全零、Import 回退可产生错误非零差量、Legacy 隐藏设置不生效，以及一致 Calculate 策略的稳定性。

---

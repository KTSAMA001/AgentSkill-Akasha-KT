# 把 MeshRenderer 渲染进 UGUI Canvas（CanvasRenderer.SetMesh 路线）

**标签**：#unity #ui #ugui #urp #rendering #experience #troubleshooting
**来源**：项目实践总结 + 外部调研（Unity 官方文档、开源库 LuisDevYT/UIMeshRenderer）
**收录日期**：2026-06-25
**状态**：✅ 已验证
**可信度**：⭐⭐⭐（实践验证 + 官方文档佐证）
**适用版本**：Unity 2022.3 / URP 14

### 概要

把普通 3D 模型（MeshRenderer）直接渲染到 UGUI Canvas 上、作为 UI 元素参与界面，本质就是 `CanvasRenderer.SetMesh` + 关闭原 MeshRenderer + 设置材质；但**真正的坑在"模型单位→UI像素的尺度转换"**——少了它模型会被缩成亚像素而"看不见"。本记录沉淀可行路线、关键坑、踩过的反面教训与路线边界。

### 内容

#### 一、本质：三步 + 一个必须的额外步骤

朴素三步（用户直觉，基本正确）：
1. 拿到模型的 `Mesh`（`MeshFilter.sharedMesh`）。
2. 关闭模型原来的 `MeshRenderer`（否则它还在 3D 世界里画一份）。
3. 把 `Mesh` 喂给 `CanvasRenderer.SetMesh`，并 `SetMaterial`。

**但必须补一个不显眼却致命的步骤——坐标尺度转换**：
- 模型 `Mesh` 顶点是**模型单位**（一个球包围盒可能才 0.89）。
- `CanvasRenderer` 把顶点当作 **UI 像素坐标**（rect 动辄 100px）。
- 所以原封不动 `SetMesh(sharedMesh)`，模型只有约 0.89 像素 → **一个看不见的点**。

放大有两种做法：
- **A. 读顶点 × 固定倍数 k 再 SetMesh**（k = sourceUnitsToUiUnits × fitScale，如 100 → 球 89px）。代价：mesh 需勾 **Read/Write**（`GetVertices/GetTriangles` 才能调用）。
- **B. 直接 SetMesh 原 mesh，但把该 UI 元素的 `RectTransform.localScale` 设成 100**。不用读顶点、不需要 Read/Write，最省。

> `CanvasRenderer.SetMesh` 本身不要求 mesh 可读；只有在 C# 里 `GetVertices` 读顶点才要 Read/Write。

#### 二、必须 vs 可选（容易过度设计）

| 处理 | 必须？ | 说明 |
|---|---|---|
| 取 mesh + 关 MeshRenderer + SetMesh + SetMaterial | ✅ | 基本闭环 |
| 模型单位 → UI 像素 放大 | ✅ | 唯一致命坑，缺了看不见 |
| SetMaterial（源材质）+ 保持不被覆盖 | ✅ | 见下"材质坑" |
| normals / tangents / uv1 顶点流 | ⬜ | 只有带光照/法线贴图/用第二套UV的 shader 才需要 |
| 居中 mesh.bounds | ⬜ | 不做也能显示，只是偏 |
| submesh 合并 / 多材质 | ⬜ | 单材质用不上 |
| 每帧重建 / skinned bake | ⬜ | 仅动画/蒙皮需要 |

#### 三、材质坑：override `UpdateMaterial`（否则丢 shader）

把源模型材质喂给 `canvasRenderer.SetMaterial(...)` 后，若组件是 `Graphic`（`m_Material` 为空），**基类 `Graphic.UpdateMaterial` 会在 mask/canvas 状态变化时用 `materialForRendering`（退化为 UI/Default）把材质覆盖掉** → 表现为"勾每帧重建才正常，否则模型变回灰白 UI 材质"。

解决：**override `UpdateMaterial()`**，用源材质（经 `GetModifiedMaterial` 以保留 Mask/RectMask2D stencil）设给 CanvasRenderer。`mainTexture` 从材质的 `_MainTex` 或 URP 的 `_BaseMap` 解析。

#### 四、`Canvas.additionalShaderChannels`：法线/切线/UV1 默认会被丢

UGUI 合批时把 Canvas 下所有 UI 合并成一个大网格，每顶点默认只带 **Position/Color/UV0**；**Normal/Tangent/TexCoord1/2/3 默认被丢弃**（省带宽）。

所以即便你给 CanvasMesh 写了法线/切线/UV1，**若没开对应 `additionalShaderChannels`，合并阶段会被剥掉，到不了 shader**。带光照/法线贴图/菲涅尔（Fresnel = 法线·视线）类 shader 必须显式开：
```csharp
canvas.additionalShaderChannels |= AdditionalCanvasShaderChannels.Normal | Tangent | TexCoord1;
```
注意它是 **Canvas 级**设置：开了会让该 Canvas 下**所有 UI** 顶点变大（内存/带宽涨），移动端敏感，故应做成开关，按 shader 需要决定开关。

#### 五、Prefab 实例的 Transform 替换限制

UGUI Graphic 带 `[RequireComponent(typeof(RectTransform))]`，`AddComponent` 时会把物体的 `Transform` 替换为 `RectTransform`。**但 Unity 禁止在"已连接的 Prefab 实例"上替换 Transform 类型，会抛 `ArgumentException`**。

- 规避：在 **Prefab 编辑/隔离模式**下处理（该模式下物体不是"实例"，可正常替换）。
- 批量加组件时务必**逐物体 try/catch**——否则一个失败抛异常会中断整个处理循环，表现为"似乎不自动处理"。
- 显式转换普通 Transform → RectTransform：`go.AddComponent<RectTransform>()`（在普通 Transform 上即替换语义）。

#### 六、踩过的反面教训（避免回退）

- ❌ 用 `fit = rect / 合并bounds` 的"自适应填充" + 跨多物体的"共享/合并包围盒"：多个相距较远的小模型，合并 bounds 被**间距**撑大，fit≈1，每个模型本体被缩成**亚像素**而看不见；移动一个子物体会改变合并重心，导致"动一个、另一个反向运动"。→ 正解：**每个物体独立 + 固定倍数缩放**，不跨物体共享 bounds。
- ❌ 生成一堆代理子节点（generated root + 每 submesh 一个代理）：与源物体分离，移动不跟手；且违背"不新增节点"诉求。→ 正解：把渲染组件**就地加在源物体本身**上，每个物体即一个独立 UI 元素（可独立移动/材质/显隐）。

#### 七、开源现状与路线边界

- 开源 `LuisDevYT/UIMeshRenderer`（MIT）：**仅单个手动 Mesh + Built-in 专用 shader**，**不支持自动收集子树、不支持 URP**。只能参考"`Graphic` + `SetMesh` + 专用 shader 参数化定位"的最小骨架，不能直接满足"URP + 多子物体"。
- **CanvasRenderer 路线（路线 A）固有边界**：一个 CanvasRenderer 一个材质（多材质/多 submesh 需合并或多元素）；3D/VFX shader 不一定兼容 UGUI 管线（可能依赖世界坐标/深度/相机等 UI 不提供的输入，或不写 Mask stencil）；正交呈现、无透视。
- **兜底**：若需任意 shader / 透视 / 阴影 / 多材质精确还原，改用 **相机 + RenderTexture + RawImage** 路线（对任意 shader 都通，代价是额外相机+RT 开销，移动端需控制数量）。

### 关键代码

固定比例映射（每个元素把自己的 mesh 映射进自己的 rect，无跨物体依赖）：
```csharp
// k = sourceUnitsToUiUnits * fitScale; center = centerOnBounds ? mesh.bounds.center : 0
// rectCenter = 本元素 rect 中心; rot = Quaternion.Euler(meshEulerAngles)
for (int i = 0; i < srcVerts.Count; i++)
{
    Vector3 local = (srcVerts[i] - center) * k;          // 模型单位 -> UI 像素，固定放大
    outVerts.Add(rot * local + rectCenter + uiOffset);   // 落在本元素 rect 内
}
canvasRenderer.SetMesh(canvasMesh);
```

材质不被覆盖：
```csharp
protected override void UpdateMaterial()
{
    canvasRenderer.materialCount = 1;
    canvasRenderer.SetMaterial(GetModifiedMaterial(sourceMaterial), 0); // 用源材质而非 UI/Default
    canvasRenderer.SetTexture(mainTexture);
}
```

### 参考链接

- [LuisDevYT/UIMeshRenderer (GitHub, MIT)](https://github.com/LuisDevYT/UIMeshRenderer) - 单 mesh / Built-in 的最小实现，仅供思路参考
- [Unity - CanvasRenderer.SetMesh](https://docs.unity3d.com/ScriptReference/CanvasRenderer.SetMesh.html)
- [Unity - RequireComponent / RectTransform 替换行为](https://docs.unity3d.com/ScriptReference/RequireComponent.html)

### 相关记录

- [unity-ugui-sprite-atlas-batching-z-depth.md](./unity-ugui-sprite-atlas-batching-z-depth.md) - UGUI 合批与 z-depth

### 验证记录

- [2026-06-25] 初次记录，来源：项目实践（CanvasRenderer.SetMesh 路线，已实测基础可见性与子物体独立性）+ 外部调研（Unity 文档、开源库 README）。

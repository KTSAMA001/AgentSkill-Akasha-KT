# Unity 2022.3 UGUI Sprite Atlas 与 Canvas 合批排查

**标签**：#unity #graphics #ui #performance #knowledge #draw-call #texture
**来源**：实践总结 + Unity 官方文档 / Unity Learn / Issue Tracker
**收录日期**：2026-05-08
**来源日期**：2026-05-08
**更新日期**：2026-05-08
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐（官方文档、官方 Issue 与实测现象交叉验证）
**适用版本**：Unity 2022.3 LTS / UGUI / Sprite Atlas V1 & V2

### 概要

Unity 2022.3 中，Editor/Play Mode 的 Frame Debugger 是否显示 Sprite Atlas 取决于 Sprite Atlas Mode；UGUI 合批也不能只按“同图集/同材质”判断，还要同时看 Canvas depth、重叠关系、intermediate layer、TMP/Mask 的实际材质，以及 local Z / 非共面对 depth 排序的影响。

### 内容

#### Sprite Atlas 在 Editor/Play Mode 下看到散图的原因

Frame Debugger 中看到某个 UI draw 使用单张源图，不必然说明 Sprite 没有被图集资源收录。Unity 2022.3 的关键前提是 `Project Settings > Editor > Sprite Atlas > Mode`：

| Sprite Atlas Mode | Edit Mode | Play Mode | Player / AssetBundle / Addressables Build |
|---|---|---|---|
| Disabled | 使用原图 | 使用原图 | 不构建图集 |
| Sprite Atlas V1 - Enabled For Builds | 使用原图 | 使用原图 | 构建图集 |
| Sprite Atlas V1 - Always Enabled | 使用原图 | 运行时使用图集 | 构建图集 |
| Sprite Atlas V2 - Enabled | 使用图集 | 使用图集 | 构建图集 |
| Sprite Atlas V2 - Enabled For Builds | 使用原图 | 使用原图 | 构建图集 |

因此，如果要在 Editor/Play Mode 的 Frame Debugger 中验证 atlas texture，优先确认模式是 `Sprite Atlas V2 - Enabled`。如果模式是 `V2 - Enabled For Builds`，Editor/Play 仍看到源图是符合官方语义的正常表现。

另一个常见前提是图集是否能被运行时自动加载。`Include in Build` 关闭或图集需要按需分发时，Unity 可能需要通过 `SpriteAtlasManager.atlasRequested` 做 late binding；这类场景下，图集资源存在不等于当前帧已经绑定到渲染纹理。

#### Sprite Atlas V1 与 V2 的差异

V1 是旧 Sprite Atlas 系统，Unity 在 Play Mode、Player build 或 AssetBundle build 等阶段使用自定义机制打包，缓存输出位于 `Library/AtlasCache`。

V2 使用 AssetDatabase V2 导入路径，Unity 2022.2 起默认推荐 `Sprite Atlas V2 - Enabled`。V2 的主要收益是与 AssetDatabase V2、Cache Server / Accelerator、import artifact 流程对齐，使构建和缓存更一致。Inspector 上多数图集设置与 V1 相似，但底层导入和缓存路径不同。

启用 V2 会迁移现有 V1 图集；官方文档说明迁移后的资产与 V1 不兼容，Unity 不能把它们自动恢复为原始 V1 状态。需要回退时，应从启用 V2 前的版本控制或备份恢复。

#### UGUI 合批不能只看同图集或同材质

UGUI Canvas batch build 会收集 CanvasRenderer 的几何，按 depth / 层级绘制顺序排序，并检查重叠、共享材质、纹理等条件。两个 Graphic 使用同一图集和同一材质，也可能因为中间插入了不能合批的 Graphic 而拆批。

最容易忽略的是 intermediate layer：两个本来可合批的元素之间，如果在绘制顺序上夹着另一个不同材质或不同纹理的元素，并且它们的包围盒发生重叠，Canvas 为保证透明队列的 back-to-front 结果，必须把批次拆开。

TMP/Text 也常导致误判。文字字形 quad 的透明区域可能比可见文字大，透明包围盒与周围图片重叠时，会形成意料之外的 intermediate layer。TMP 的不同 Font Asset、fallback atlas、material preset 也会改变实际纹理或材质，从而影响合批。

Mask / RectMask2D 相关对象也不能简单写成“一定拆批”或“一定不拆批”。关键是它们可能通过 stencil 或 material modifier 改变 `Graphic.materialForRendering`，导致实际送入 CanvasRenderer 的材质状态不同。

#### local Z / 非共面与 Canvas depth

同一 Canvas 内，常规 UI 覆盖顺序主要由 Hierarchy / sibling order 控制，后绘制的元素覆盖先绘制的元素。不要把 UGUI 的常规显示顺序简单理解成由 local Z 控制。

但 local Z / 是否共面确实会影响合批。Unity Issue Tracker 对相关问题的官方说明是：Canvas 元素 local Z 非 0 或处于非共面状态时，可能被赋予更高 depth，以保证渲染顺序；当这些非共面元素与不同材质或不同纹理交错出现时，depth 优先级会压过 material batching，从而导致预期合批被拆开。

需要注意，非共面本身不是独立的“必拆批”条件。如果其他合批条件仍满足，非共面元素仍可能合批。更准确的判断是：local Z / 非共面会参与或改变 depth 排序；它与材质、纹理、层级交错、重叠关系共同决定最终是否拆批。

#### 排查顺序

1. 确认 Sprite Atlas Mode，明确当前 Editor/Play 是否应该使用 atlas texture。
2. 在 Frame Debugger 中看 draw event 的实际 `_MainTex` / texture 绑定，而不是只看 Output/Mesh 预览图。
3. 用 UI Profiler 的 Batch Breaking Reason 判断拆批原因；Frame Debugger 能证明 draw event 数量，但不能直接给出根因。
4. 检查同 Canvas 内是否存在不同材质/纹理的 intermediate layer，尤其是 TMP/Text、Mask/stencil 和透明包围盒重叠。
5. 检查 UI 子节点 local Z 是否混杂；需要合批的 UI 尽量保持共面，前后关系优先用 sibling order 或 Canvas sorting 管理。
6. World Space UI 还要额外考虑多 Canvas sorting、相机透明排序、渲染队列和空间遮挡；这类 UI 更容易因为空间层次接受更多 draw call。

### 关键代码（如有）

无。

### 参考链接

- [Unity Manual - Sprite Packer Modes](https://docs.unity.cn/Manual/SpritePackerModes.html) - Sprite Atlas V1/V2 各模式在 Edit Mode、Play Mode 和构建阶段的行为。
- [Unity Manual - Sprite Atlas V2](https://docs.unity3d.com/cn/2022.3/Manual/SpriteAtlasV2.html) - V2 图集系统、ADBV2、迁移和兼容性说明。
- [Unity Manual - Sprite Atlas properties](https://docs.unity3d.com/cn/2022.3/Manual/class-SpriteAtlas.html) - Include in Build 等图集属性。
- [Unity Scripting API - SpriteAtlasManager.atlasRequested](https://docs.unity3d.com/cn/2022.3/ScriptReference/U2D.SpriteAtlasManager-atlasRequested.html) - 图集 late binding 入口。
- [Unity Learn - Optimizing Unity UI](https://learn.unity.com/topics/best-practices/optimizing-ui-controls) - Canvas batch build、depth、overlap、shared material、intermediate layer 与 Batch Breaking Reason。
- [Unity Manual - Canvas draw order](https://docs.unity3d.com/cn/2018.3/Manual/UICanvas.html) - Canvas 内 UI 元素的绘制顺序。
- [Unity Issue Tracker - UUM-87152](https://issuetracker.unity3d.com/issues/ui-image-batching-breaks-when-interleaving-elements-with-mixed-z-positions-and-materials) - mixed Z positions and materials 导致 UI Image batching break 的官方说明。
- [Unity Issue Tracker - UUM-98769](https://issuetracker.unity3d.com/issues/ui-image-batching-breaks-when-the-image-is-nested-in-a-prefab-and-is-offset-on-the-z-axis) - Z-axis offset 导致 batching break 的复现记录，关联 UUM-87152。
- [Unity Issue Tracker - UUM-96842](https://issuetracker.unity3d.com/issues/sprite-atlas-inspector-preview-disappears-when-entering-play-mode-unless-spriteatlasmode-is-set-to-sprite-atlas-v2-enabled) - Sprite Atlas V2 与 AssetDatabase / AtlasCache 差异的官方说明补充。

### 相关记录

- [渲染管线知识](./rendering-pipeline-overview.md) - Draw Call、渲染状态与合批的基础概念。
- [CBUFFER 与 SRP Batcher 合批机制](./cbuffer-srp-batcher-mechanism.md) - SRP Batcher 方向的合批机制，与 UGUI Canvas batching 区分参考。

### 验证记录

- [2026-05-08] 初次记录。来源为一次 Unity 2022.3 UGUI 图集与 Canvas 合批问题调查；已按脱敏要求移除原始上下文中的路径、资源名、标识符、截图和工程代码细节，仅保留通用 Unity 结论。
- [2026-05-08] 使用四路交叉验证：Sprite Atlas V1/V2 官方文档核对、UGUI batching 官方 Learn 核对、local Z / 非共面官方 Issue Tracker 核对、原始问题现场仅作为调查触发来源且未写入正文。

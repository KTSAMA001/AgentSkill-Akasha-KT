# 3ds Max 蒙皮后法线异常问题调查

**标签**：#unity #3dsmax #fbx #experience #troubleshooting
**来源**：智谱 MCP 搜索 + 社区讨论（Autodesk Forum / Unity Discussion）
**收录日期**：2026-03-12
**来源日期**：2026-03-12
**状态**：⚠️ 待验证
**可信度**：⭐⭐⭐（网络资料汇总，未亲自验证）
**适用版本**：3ds Max 2015+, Unity 2020+

### 概要
美术在做模型资产时法线正常（硬边效果），但动画绑定后法线被打乱。通过网络搜索汇总了可能的原因和解决方案，**待美术验证后更新状态**。

### 问题原因

| 原因 | 说明 |
|------|------|
| **Skin 修改器位置** | Skin 必须是修改器堆栈的**最顶层**，如果 TurboSmooth 等在它上面会导致法线计算错误 |
| **网格类型** | Editable Poly 导出可能有问题，Editable Mesh 更兼容 FBX |
| **FBX 导出设置** | Normals 选项未选择 "From DCC"，导致导出时法线被重算 |

### 解决方案

#### 方案 1：调整修改器顺序（推荐）

修改器堆栈顺序（从下到上）：
1. Editable Mesh / Editable Poly（基础网格）
2. 其他修改器（UVW Map、TurboSmooth 等）
3. **Skin（必须是最顶层！）**

#### 方案 2：转换为 Editable Mesh

导出前：
1. 右键模型 → Convert to → Editable Mesh
2. 再添加 Skin 修改器
3. 导出 FBX

#### 方案 3：检查 FBX 导出设置

- **Skins** → 确保勾选
- **Normals** → 选择 "From DCC" 或 "In DCC"
- **Tangents & Binormals** → 关闭或选择 "In DCC"

#### 方案 4：锁定法线

在添加 Skin 之前：
1. 添加 Edit Normals 修改器
2. 选择所有法线 → Lock Selected
3. 再添加 Skin 修改器

### 验证步骤

1. 导出**不带绑定**的模型到 Unity → 看法线是否正常
2. 如果正常 → 问题在绑定环节（Skin 修改器）
3. 如果也异常 → 问题在 FBX 导出设置

### 参考链接

- [Autodesk Forum: Skin Modifier breaks export normals](https://forums.autodesk.com/t5/3ds-max-animation-and-rigging/skin-modifier-breaks-export-normals-on-object-max-2015-student/td-p/7960385)
- [Unity Discussion: 3ds max .fbx messed up normals](https://discussions.unity.com/t/solution-to-3ds-max-fbx-messed-up-flipped-normals/664472)
- [Unity Discussion: 3DS Skin modifier + FBX files](https://discussions.unity.com/t/3ds-skin-modifier-fbx-files/396193)
- [中文博客: FBX从3ds Max到Unity](https://blog.wallenwang.com/2017/02/fbx-from-3dsmax-to-unity/)

### 相关记录

- [animation-retarget-technology-unity.md](./animation-retarget-technology-unity.md) - 动画重定向技术

### 验证记录
- [2026-03-12] 初次记录，来源：智谱 MCP 搜索结果，待实际验证

- [2026-04-15] 原状态备注“待美术实际测试”已移入验证记录，等待美术实测。

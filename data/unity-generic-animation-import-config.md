# Unity Generic 动画导入配置完整流程：解决滑步、UI 消失与双重位移

**标签**：#unity #animation #root-motion #experience
**来源**：实践总结 + Unity 官方文档验证
**收录日期**：2026-02-10
**更新日期**：2026-02-10
**状态**：⚠️待验证
**可信度**：⭐⭐⭐⭐
**适用版本**：Unity 2020.3+

### 概要

针对 Unity Generic（非人形）动画导入时常见的滑步（Foot Sliding）、Inspector UI 选项消失（Bake Into Pose 等不显示）、以及双重位移问题的完整四步修复流程。核心记忆口诀：**Rig → Motion(None) → Bake → Mask(Uncheck Root)**。

### 内容

#### 第一步：Rig（身份定义）

这一步是基础，决定了 Unity 如何识别骨骼层级。

1. **选中 FBX 母文件**。
2. 在 **Rig** 标签页：
   - **Animation Type**：必须选 **Generic**。
   - **Avatar Definition**：
     - 若是独立模型 → 选 **Create From This Model**。
     - 若是独立动画文件 → 选 **Copy From Other Avatar** 并指向该角色的 Avatar。
   - **Root Node**：选择根骨骼（如 `root`）。
     - ⚠️ 注意：如果选了之后 Animation 页报错或选项不出来，可以暂时设为 **None**。
3. 点击 **Apply**。

#### 第二步：Motion（解锁 UI 面板）—— 最关键的一步

如果发现 Animation 页没有 `Bake Into Pose` 等选项，必须先做这一步。

1. 切换到 **Animation** 标签页。
2. 向下滚动到最底部，找到 **Motion** 区域。
3. **Root Motion Node**：将其下拉菜单设为 **`<None>`**。
   - **原理**：设为 None 后，Unity 会基于整体质心（Center of Mass）计算运动，从而解除对特定骨骼的"死锁"，让上方隐藏的 `Root Transform` 选项瞬间出现。
4. 点击 **Apply**。

#### 第三步：Root Transform（位移烘焙设置）

选项显示出来后，开始处理滑步的核心逻辑。

1. **Root Transform Position (XZ)**：
   - **Bake Into Pose**：
     - 想要**原地踏步**（代码控制位移）→ **勾选**。
     - 想要**动画驱动位移**（Apply Root Motion）→ **不勾选**。
   - **Based Upon**：建议选 **Root Node Position**（如果 Rig 已设根节点）或 **Center of Mass**（最稳，基于质心）。

2. **Root Transform Rotation**（旋转）：
   - 通常建议**勾选** Bake Into Pose，防止播放动画时角色方向发生莫名偏转。

3. **Root Transform Position (Y)**（高度）：
   - **Bake Into Pose**：必须**勾选**。防止角色在播放动画时高度上下乱跳。

4. 点击 **Apply**。

#### 第四步：Mask（消除双重位移）—— 终极清理

即使做了前三步，可能仍有微小滑步（因为骨骼肉体在动），这一步是终极解决。

1. 在 Animation 标签页中找到 **Mask** 区域。
2. **Definition**：选 **Create From This Model**（或 Copy 自你的 Avatar）。
3. 展开 **Transform** 骨骼列表。
4. 找到根骨骼（如 `root`），**取消勾选**它。
   - **原理**：告诉 Unity"使用 Root Motion 驱动游戏对象，但在播放动画时，不要让 `root` 骨骼相对于父级发生任何位移"，从而消除双重位移。
5. 点击 **Apply**。

#### 深度避坑总结表

| 遇到问题 | 检查细节 | 解决方案 |
|---------|---------|---------|
| Bake 选项不出来 | Root Motion Node 被报错卡死 | Motion → Root Motion Node 设为 `<None>` |
| 勾了位移还是滑步 | 存在双重位移 | Mask → 取消勾选根骨骼 (root) |
| Loop Match 亮红灯 | 首尾速度不一致 | Animation 窗口中将 Z 轴位移曲线设为 Linear（线性） |
| 角色越走越歪 | 旋转没烘焙 | Root Transform Rotation → 勾选 Bake Into Pose |

### 参考链接

- [导入带有非人形（通用）动画的模型 - Unity 官方文档](https://docs.unity.cn/cn/2021.1/Manual/GenericAnimations.html) - Generic 动画导入官方指南
- [Rig 选项卡 - Unity 手册](https://docs.unity3d.com/cn/current/Manual/FBXImporter-Rig.html) - FBX 导入器 Rig 设置说明
- [模型导入工作流程 - Unity 手册](https://docs.unity.cn/cn/2020.3/Manual/ImportingModelFiles.html) - 完整模型导入流程

### 相关记录

- [Unity 动画与脚本开发核心知识清单](./unity-animation-scripting-notes.md) - Root Motion API 与 Animator 脚本控制
- [Unity BlendTree 下动画驱动音效同步](./unity-blendtree-audio-sync.md) - BlendTree 动画音效同步方案

### 验证记录

- [2026-02-10] 初次记录。来源：用户实践经验总结。经网络调查与 Unity 官方文档交叉验证，四步流程中的各项设置（Rig/Generic、Root Motion Node/None、Bake Into Pose、Mask/Transform）均与官方文档吻合。整体流程为实践总结的最佳实践组合，非单一官方出处，标记为待验证（待实际项目验证完整流程的连贯有效性）。

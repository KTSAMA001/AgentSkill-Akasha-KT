# KINEMATION Retarget Pro 插件全面分析

**标签**：#unity #animation #knowledge #retarget-pro #animation-retarget #ik #scriptable-object
**来源**：实践分析 + 官方文档 (https://kinemation.gitbook.io/retarget-pro) + 源码阅读
**收录日期**：2026-02-10
**更新日期**：2026-02-10
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐（官方文档 + 源码实证）
**适用版本**：Retarget Pro 4.2.1 / Unity 2021.3.24f1+

### 概要

KINEMATION Retarget Pro 是 Unity 高级动画重定向插件，可将一个角色（Source）的动画无缝迁移到另一个角色（Target），质量高于 Unity 内置 Humanoid 系统。支持编辑器离线烘焙和运行时实时重定向两种模式。仅支持将 Humanoid/Generic 动画重定向到 **Generic** 角色，暂不支持烘焙 Humanoid 格式输出。

### 内容

#### 一、基本信息

| 项目 | 信息 |
|------|------|
| 插件名称 | Retarget Pro |
| 开发者 | KINEMATION |
| 当前版本 | **4.2.1** |
| 最低 Unity 版本 | 2021.3.24f1 |
| 兼容渲染管线 | Built-in / URP / HDRP |
| 官方文档 | https://kinemation.gitbook.io/retarget-pro |
| GitHub | https://github.com/kinemation/retarget-pro |
| Asset Store | https://u3d.as/2YfD |
| Discord | https://discord.gg/kinemation-1027338787958816860 |

#### 二、目录结构

```
KINEMATION/
├── Plugins/FuzzySharp/           # 第三方模糊字符串匹配库（骨骼名自动映射）
├── RetargetPro/
│   ├── Editor/                   # 编辑器工具
│   │   ├── RetargetProWindow.cs        # 主窗口（Window > KINEMATION > Retarget Pro）
│   │   ├── RetargetAnimBaker.cs        # 动画烘焙器
│   │   ├── GenericAnimationBaker.cs    # Generic 格式动画曲线记录
│   │   ├── PreviewerWindow.cs          # 动画预览窗口
│   │   ├── RetargetContextWindow.cs    # 右键批量重定向窗口
│   │   ├── ProfileContextMenu.cs       # 右键创建 Profile / 自动映射
│   │   └── RetargetProfileWidget.cs    # Profile Inspector 内 Feature 列表 UI
│   ├── Runtime/
│   │   ├── RetargetProfile.cs          # 重定向配置（ScriptableObject）
│   │   ├── RetargetProComponent.cs     # 离线重定向核心逻辑
│   │   ├── DynamicRetargeter.cs        # 实时重定向组件（MonoBehaviour）
│   │   └── Features/
│   │       ├── RetargetFeature.cs          # Feature 基类
│   │       ├── RetargetFeatureState.cs     # Feature 运行时状态基类
│   │       ├── RetargetJobUtility.cs       # Animation Job 工具（含 FABRIK 算法）
│   │       ├── RetargetUtility.cs          # 骨骼名匹配工具
│   │       ├── BasicRetargeting/           # 基础旋转+位移重定向
│   │       ├── IKRetargeting/              # IK 增强重定向
│   │       ├── FPSRetargeting/             # FPS 武器动画专用
│   │       ├── BonePoser/                  # 骨骼姿态覆盖
│   │       └── CopyBone/                   # 骨骼直接复制
│   └── Presets/                  # 预设（Mixamo/Synty/UnityRobot Rig + Profile）
└── Shared/KAnimationCore/
    ├── Runtime/
    │   ├── Core/                 # 数学工具（KTwoBoneIK、KChainIK/FABRIK、KTransform 等）
    │   ├── Rig/                  # 骨骼系统（KRig、KRigComponent、KRigElement 等）
    │   └── Input/                # 输入系统
    └── Editor/
        └── Rig/                  # Rig 编辑器（KRigEditor、RigMappingMenu 等）
```

#### 三、工作模式

| 模式 | 说明 | 核心类 |
|------|------|--------|
| **编辑器离线烘焙** | 采样重定向后生成新 AnimationClip | `RetargetAnimBaker` + `RetargetProComponent` |
| **运行时实时重定向** | Animation Jobs 多线程并行计算 | `DynamicRetargeter` (Playable API) |

#### 四、完整工作流 — 逐步创建指南

##### 步骤 1：添加 Rig Component

1. 将角色模型拖入场景
2. 展开骨骼层级，找到**骨骼根节点**（Root / Hips / Armature）
3. 选中根骨骼 → Inspector → Add Component → 搜索 **KRigComponent**
4. 点击 **"Refresh Hierarchy"** 按钮扫描所有子骨骼
5. **Apply changes to prefab** 保存
6. 源角色和目标角色**各做一次**

**快捷方式**：右键骨骼根节点 → `GameObject > Auto Rig Mapping` 可一步到位创建 Rig Component + Rig Asset + Element Chains。

##### 步骤 2：创建 Rig Asset

**手动方式**：
1. Project 窗口右键 → **Create > KINEMATION > Rig**
2. 命名为 `Rig_角色名.asset`
3. 选中 Rig Asset → Inspector 中将场景中的 KRigComponent 拖入 "Rig Component" 字段
4. 点击 **"Import Rig"** 按钮
5. Ctrl+S 保存

**自动方式（推荐）**：
1. 右键骨骼根节点 → `GameObject > Auto Rig Mapping`
2. Rig Mapping Window 中 Rig Asset 留空、Root Bone 选择骨骼根
3. "Bone Names to Avoid" 默认过滤 `twist` 和 `correct`（辅助骨骼）
4. 点击 **"Create Rig Mapping"** → 自动生成资产 + 骨骼链

源角色和目标角色**各做一次**。

##### 步骤 3：配置 Element Chains（骨骼链）

在 Rig Asset → "Element Chains" 标签页中配置。标准人形角色建议：

| 链名 | 包含骨骼 |
|------|----------|
| Pelvis | Hips |
| Spine | Spine, Spine1, Spine2, Chest |
| Neck | Neck, Head |
| RightArm | RightShoulder, RightUpperArm, RightLowerArm, RightHand |
| LeftArm | LeftShoulder, LeftUpperArm, LeftLowerArm, LeftHand |
| RightLeg | RightUpperLeg, RightLowerLeg, RightFoot |
| LeftLeg | LeftUpperLeg, LeftLowerLeg, LeftFoot |
| Fingers | 可选，按需 |
| Weapon | FPS 专用，可选 |

> **重要**：命名需一致，系统依靠名称自动匹配。按住 Shift+LMB 可多选骨骼。

##### 步骤 4：创建 Retarget Profile

**手动方式**：
1. Project 右键 → **Create > KINEMATION > Retarget Profile**
2. 配置字段：
   - Source/Target Character → 带 KRigComponent 的角色 Prefab
   - Source/Target Pose → T-Pose 或 A-Pose AnimationClip
   - Source/Target Rig → 对应 Rig Asset
   - Elements To Exclude → 可选排除骨骼

**自动方式（推荐）**：
1. 在 Project 中同时选中两个 Rig Asset（Ctrl+点击）
2. 右键 → **Create Retarget Profile**
3. 自动使用 FuzzySharp 模糊匹配映射骨骼链，为每个目标链创建 IKRetargetFeature
4. 第一个选中 = Source，第二个 = Target

##### 步骤 5：添加 Retarget Features

在 Retarget Pro 窗口或 Profile Inspector 中点击 **"Add Retarget Feature"**，可选类型：

| Feature 类型 | 适用场景 | 关键参数 |
|-------------|----------|----------|
| **BasicRetargetFeature** | 脊椎/手指/脖子等一般链 | scaleWeight, translationWeight, offset |
| **IKRetargetFeature** | 手臂/腿部需要精确位置 | ikWeight, effectorOffset, poleOffset |
| **FPSRetargetFeature** | 第一人称换弹/武器动画 | rightHandOffset, leftHandOffset, weaponOffset |
| **BonePoserFeature** | 强制固定姿态 | rotationPose, isAdditive |
| **CopyBoneFeatureSettings** | 直接复制骨骼 | copyFrom, copyTo |

##### 步骤 6A：编辑器预览与烘焙

1. 打开 **Window > KINEMATION > Retarget Pro**
2. 填写 Source/Target Character、Profile、Animation
3. 配置 Frame Rate (24~240)、Copy Clip Settings、Use Root Motion、Keyframe All
4. 设置 Save Folder（默认 `Assets/RetargetedAnimations`）
5. Play / Loop 预览 → **Bake Animation** 输出 `.anim` 文件
6. 预览结果：**Window > KINEMATION > Animation Previewer**

**批量重定向**：选中 AnimationClip / FBX / Animator Controller → 右键 → **Animation Retargeting**

##### 步骤 6B：实时重定向

1. 目标角色添加 **Animator** 组件（Controller 留空）
2. 确保源/目标角色骨骼根节点都有 KRigComponent 并已 Refresh
3. 目标角色添加 **DynamicRetargeter** 组件
4. 设置 Animation Source（源角色 GameObject）和 Retarget Profile
5. 运行游戏即可

##### 步骤 7：FBX 导出（可选）

需安装 Unity FBX Exporter 包。将烘焙后的动画放入 Animator Controller，挂到角色上，右键 → Export to FBX。

#### 五、核心实现原理

##### 基础重定向（Basic Retarget）

```csharp
// 核心公式：旋转差值映射
Quaternion orientationDelta = Quaternion.Inverse(cachedSourcePose.rotation) * cachedTargetPose.rotation;
Quaternion targetRotation = sourceBone.rotation * orientationDelta;
```

1. 缓存源/目标参考姿态（T-Pose/A-Pose）的旋转
2. 计算旋转差值 delta
3. 每帧将源骨骼旋转乘以 delta 得到目标旋转
4. 体型缩放：`chainScale = targetChainLength / sourceChainLength`
5. featureWeight 控制与原始姿态的 Slerp 混合

骨骼链数量不匹配时使用分布式映射：
```csharp
int targetIndex = Mathf.FloorToInt((targetCount - 1) * ((float)i / (sourceCount - 1)));
```

##### IK 重定向

- **3 骨骼链**：Two-Bone IK（`KTwoBoneIK.Solve()`），基于三角形余弦定理
- **4+ 骨骼链**：FABRIK 算法（Forward And Backward Reaching IK），迭代求解

Effector 计算：
```csharp
Vector3 effector = sourceTip - sourceRoot.TransformPoint(sourcePose);
effector = effector * scale + targetRoot.TransformPoint(targetPose);
```

##### 实时重定向（Animation Jobs）

- 使用 Playable API + `AnimationScriptPlayable`
- `BasicRetargetJob` / `IKRetargetJob` 实现 `IAnimationJob`
- 多线程并行运行，使用 `NativeArray` 避免 GC
- `TransformStreamHandle` / `TransformSceneHandle` 直接操作 Animator 流

##### FPS 重定向

在武器局部空间中计算手部位置，然后在目标角色武器空间还原 + Two-Bone IK 解算手臂。

##### 骨骼自动映射

`RetargetUtility.IsNameMatching()` 通过关键词匹配（pelvis/hip/spine/arm/leg 等），支持左右侧检测（_l/_r/left/right）。配合 FuzzySharp 库做模糊字符串匹配。

#### 六、架构设计亮点

1. **Feature 模式**：`RetargetFeature`（SO 配置）+ `RetargetFeatureState`（运行时状态）分离，支持任意组合
2. **双模式统一**：离线/实时共享同一套 Profile 和 Feature 配置
3. **观察者模式**：KRig 通过 `IRigObserver` 通知 Profile 自动更新
4. **Job 化并行**：Animation Jobs 充分利用多线程
5. **NativeArray**：避免 GC，适合实时场景

#### 七、适用与限制

**适用**：不同体型角色共享动画、FPS 武器动画迁移、Generic rig 间重定向、批量动画转换、运行时换装换角色

**不适用**：目标角色为 Humanoid Rig 的烘焙导出、面部表情重定向、BlendShape/Morph Target 动画

### 参考链接

- [官方文档](https://kinemation.gitbook.io/retarget-pro) - 完整工作流指南
- [GitHub 仓库](https://github.com/kinemation/retarget-pro) - 示例项目
- [Asset Store](https://u3d.as/2YfD) - 购买页面
- [Discord](https://discord.gg/kinemation-1027338787958816860) - 社区支持

### 相关记录

- [Unity 动画与脚本开发核心知识](./unity-animation-scripting-notes.md) - Animation 系统基础

### 验证记录

- [2026-02-10] 初次记录。通过完整源码阅读（17 个 C# 文件）+ 官方文档交叉验证。版本号 4.2.1 由用户确认。

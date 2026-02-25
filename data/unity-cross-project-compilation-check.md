# Unity 跨项目功能迁移的编译验证经验

标签 | 收录日期 | 状态 | 可信度 | 适用版本
---|---|---|---|---
#unity #editor #csharp #experience | 2026-02-25 | ✅ 已验证 | 📘 有效 | Unity 2021+

## 概要
在进行 Unity 跨项目功能迁移（特别是涉及 Editor 工具和运行时逻辑混合的迁移）时，可以直接在当前项目的终端中使用 `dotnet build` 命令编译目标项目的 `.csproj` 文件来验证迁移代码的正确性。**关键点在于必须同时编译运行时程序集和 Editor 程序集**，否则容易遗漏 Editor 目录下的编译错误。

## 内容

### 场景描述
当我们需要将 A 项目的某些功能（如 GM 工具、网络数据控制类）迁移到 B 项目时，通常会直接修改 B 项目的源码文件。为了不频繁切换 Unity 编辑器窗口，我们可以在 A 项目的 VS Code 终端中直接使用 `dotnet build` 检查 B 项目的编译状态。

### 核心踩坑点：程序集隔离
Unity 会将代码拆分到不同的程序集中：
1. `Assembly-CSharp.csproj`：包含游戏运行时的核心逻辑代码（如 `Assets/Script/Logic/`）。
2. `Assembly-CSharp-Editor.csproj`：包含所有位于 `Editor` 文件夹下的工具代码（如 `Assets/Script/Editor/`）。

如果只执行 `dotnet build <B项目路径>\Assembly-CSharp.csproj`，编译器**只会检查运行时代码**。如果迁移的 Editor 工具代码中存在错误（例如引用了新项目中不存在的命名空间或类），这个错误会被完全隐藏，导致误以为迁移成功。

### 正确的验证流程

在终端中执行以下两条命令，并过滤错误信息：

**1. 验证运行时代码：**
```powershell
dotnet build <B项目路径>\Assembly-CSharp.csproj | Select-String -Pattern "错误|Error|Failed"
```

**2. 验证 Editor 工具代码（关键）：**
```powershell
dotnet build <B项目路径>\Assembly-CSharp-Editor.csproj | Select-String -Pattern "错误|Error|Failed"
```

只有当这两个程序集都编译通过（无 Error 输出）时，才能确认跨项目代码迁移在语法和依赖层面是完全正确的。

## 关键代码/命令

```powershell
# 示例：在 drjd_vr 项目中验证 dlxb_vr 项目的编译状态
$targetProject = "D:\UnityProject_Work\dlxb_vr\Unity\Proj_dlxb_vr"

# 检查运行时
dotnet build "$targetProject\Assembly-CSharp.csproj" | Select-String -Pattern "错误|Error|Failed"

# 检查 Editor
dotnet build "$targetProject\Assembly-CSharp-Editor.csproj" | Select-String -Pattern "错误|Error|Failed"
```

## 相关记录
- [unity-editor-api.md](./unity-editor-api.md) - Unity Editor 开发知识

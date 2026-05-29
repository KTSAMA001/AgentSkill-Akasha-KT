# Unity Custom Inspector 中 Foldout / 数组列表折叠箭头缩进错位与 Header 组合陷阱

**标签**：#unity #editor #custom-editor #experience #bug
**来源**：实践排查 + Unity Issue Tracker + Unity Scripting API
**收录日期**：2026-05-29
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐（实践验证 + 官方 Issue Tracker 交叉验证）
**适用版本**：Unity 2022.3+（重点关注 IMGUI `OnInspectorGUI` 路径）

### 概要

在 Unity `CustomEditor.OnInspectorGUI` 中混用 `Foldout`、`foldoutHeader`、`BeginFoldoutHeaderGroup` 和数组/列表 `PropertyField` 时，常见问题不是单一控件“画歪了”，而是 Unity IMGUI 已知问题族叠加导致的：折叠箭头缩进错位、点击区与图标不一致、以及 `FoldoutHeaderGroup` 内首个列表直接报错。更稳的规避思路是：顶层分区避免依赖 `BeginFoldoutHeaderGroup` 承载列表，手工 Header 走显式 `Rect`，数组/列表单独做安全缩进兜底。

### 内容

#### 问题现象

在自定义 Inspector 中，以下现象容易同时出现：

- 顶层分区或参数卡片的折叠三角箭头左偏，视觉上越过容器边界
- `foldoutHeader` 与右侧按钮拼接时，背景、箭头和按钮边界错位
- 数组/列表字段的第一个折叠入口在 Header 容器内报错：

```text
You can't nest Foldout Headers, end it with EndFoldoutHeaderGroup.
```

#### 根因不是一个点，而是三个因素叠加

1. Unity IMGUI 自身存在已知问题  
   Unity Issue Tracker 已有公开记录：
   - 数组/列表的 Foldout 箭头缩进会错位
   - `FoldoutHeaderGroup` 对 `indentLevel` 的处理不稳定
   - `FoldoutHeaderGroup` 内首个列表会触发错误

2. `foldoutHeader` 的用途和普通 `Foldout` 不同  
   `foldoutHeader` 更接近“整条 Header”的视觉样式，不适合直接拿来当普通折叠控件，再外挂同层按钮。否则会出现：
   - 背景矩形按整条 Header 画
   - 按钮按独立控件画
   - 箭头和点击区却仍按 Foldout 逻辑计算

3. 自定义 Inspector 混绘会放大偏差  
   当同一 Inspector 中同时存在：
   - Unity 默认 `PropertyField`
   - 手工 `EditorGUI.Foldout`
   - Odin `PropertyTree`
   - `helpBox` / `toolbar` 等容器样式  
   各层 margin / padding / indent 会叠加，最终把本来就不稳定的箭头缩进问题放大成明显越界。

#### 不推荐的组合

```csharp
expanded = EditorGUILayout.BeginFoldoutHeaderGroup(expanded, title);
EditorGUILayout.PropertyField(arrayProperty, true);
EditorGUILayout.EndFoldoutHeaderGroup();
```

以及：

```csharp
EditorGUILayout.BeginHorizontal();
expanded = EditorGUILayout.Foldout(expanded, title, true, EditorStyles.foldoutHeader);
GUILayout.Button("删除");
EditorGUILayout.EndHorizontal();
```

这两类写法都容易踩中 Unity Inspector 的边界问题。

#### 更稳的规避方案

##### 1. 顶层分区只保留 Header 外观，不依赖 FoldoutHeaderGroup 语义

```csharp
Rect headerRect = EditorGUILayout.GetControlRect(false, EditorGUIUtility.singleLineHeight + 3f);
headerRect.xMin += 10f;
expanded = EditorGUI.Foldout(headerRect, expanded, title, true, EditorStyles.foldoutHeader);
```

适用场景：
- 顶层分区里还要继续画数组、列表、复杂自定义布局

##### 2. 自绘卡片 Header，折叠区和右侧按钮共享同一条背景

```csharp
Rect headerRect = EditorGUILayout.GetControlRect(false, EditorGUIUtility.singleLineHeight + 6f);
Rect foldoutRect = new Rect(headerRect.x + 12f, headerRect.y + 1f, headerRect.width - 64f, headerRect.height - 2f);
Rect buttonRect = new Rect(headerRect.xMax - 58f, headerRect.y + 1f, 56f, headerRect.height - 2f);

GUI.Box(headerRect, GUIContent.none, EditorStyles.toolbar);
expanded = EditorGUI.Foldout(foldoutRect, expanded, title, true);
GUI.Button(buttonRect, "删除", EditorStyles.toolbarButton);
```

这样做的目的不是“更好看”，而是把：
- 背景
- 折叠箭头
- 按钮点击区  
统一到同一个显式坐标系里，避免各画各的。

##### 3. 数组/列表字段单独做安全缩进兜底

```csharp
using (new EditorGUI.IndentLevelScope(1))
{
    EditorGUILayout.PropertyField(arrayProperty, new GUIContent(label), true);
}
```

这不能从根上修 Unity，但对“箭头左偏到容器外”这类问题足够实用。

#### 实战判断准则

- 如果分区内部会画数组/列表，优先不要让它直接挂在 `BeginFoldoutHeaderGroup` 下面
- 如果一个折叠标题右边还要塞按钮，优先自己画 `Rect`
- 如果只是普通字段折叠且没有复杂布局，默认 `PropertyField` / `Foldout` 仍然够用，不要过度自绘

### 关键代码

```csharp
private const float FoldoutArrowSafePadding = 10f;

private static void DrawListPropertyWithSafeIndent(SerializedProperty property, string label)
{
    if (property == null)
    {
        return;
    }

    using (new EditorGUI.IndentLevelScope(1))
    {
        EditorGUILayout.PropertyField(property, new GUIContent(label), true);
    }
}
```

### 参考链接

- [Unity Issue Tracker - Foldout arrow indent is misaligned in the Inspector when used for Arrays or Lists](https://issuetracker.unity3d.com/issues/foldout-arrow-indent-is-misaligned-in-the-inspector-when-used-for-arrays-or-lists) - 数组/列表折叠箭头缩进错位
- [Unity Issue Tracker - EditorGUILayout Foldout Header Group does not respect EditorGUI.indentLevel value](https://issuetracker.unity3d.com/issues/editorguilayout-foldout-header-group-does-not-respect-editorgui-dot-indentlevel-value) - FoldoutHeaderGroup 与缩进行为不一致
- [Unity Issue Tracker - First List in a FoldoutHeaderGroup errors](https://issuetracker.unity3d.com/issues/first-list-in-a-foldoutheadergroup-errors) - FoldoutHeaderGroup 内首个列表报错
- [Unity Scripting API - EditorGUILayout.BeginFoldoutHeaderGroup](https://docs.unity3d.com/ScriptReference/EditorGUILayout.BeginFoldoutHeaderGroup.html) - 官方 API 说明
- [Unity Scripting API - EditorGUILayout.Foldout](https://docs.unity3d.com/ScriptReference/EditorGUILayout.Foldout.html) - 普通 Foldout API

### 相关记录

- [Unity Editor 开发知识](./unity-editor-api.md) - `CustomEditor` 与 Inspector 绘制基础
- [基于 ScriptableObject 配置驱动 + AssetPostprocessor 自动执行的资源批量导入管理框架](./unity-asset-import-tool-architecture.md) - `finishedDefaultHeaderGUI` 等低侵入 Inspector 增强思路
- [BD 节点条件显示的替代方案](./bd-showif-workaround.md) - 宿主自带 Inspector 会影响 Odin/Unity 绘制策略

### 验证记录

- [2026-05-29] 初次记录，来源：Unity 2022.3 项目中的自定义 Inspector 实修 + Unity Issue Tracker / Scripting API 交叉核对


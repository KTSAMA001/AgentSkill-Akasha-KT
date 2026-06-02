# Unity Color 属性在 HSV V=0 时丢失色相与饱和度

**标签**：#unity #editor #material #shader #serialization #experience #bug
**来源**：实践排查 + LWGUI 源码检查 + Unity Issue Tracker + Unity Scripting API
**收录日期**：2026-06-02
**来源日期**：2026-06-02（本次实践排查）；2024-01-03（Unity Issue Tracker UUM-59751）
**更新日期**：2026-06-02
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐（项目实测 + Unity 官方 Issue Tracker + 本地源码检查；未覆盖 Unity 版本需重新确认）
**适用版本**：本地复现版本为 Unity 2022.3.62f3 / URP 14；Unity Issue Tracker UUM-59751 标注 2021.3.34f1、2022.3.17f1、2023.2.4f1、2023.3.0b1 可复现。其他 Unity 版本需以实际 `Color`/Color Picker 序列化行为为准重新验证。

### 概要

在已验证版本范围内，Unity 材质 `Color` 属性只按 RGB/RGBA 保存颜色，颜色面板中的 HSV 只是编辑交互模式。若在 HSV 模式下把 `V` 设为 0，写入材质的 RGB 会变成纯黑，关闭并重新打开颜色面板后无法恢复原来的 H/S；shader 侧再做最小亮度补偿，也只能得到灰色或默认色，而不能还原原始色相。

### 内容

#### 问题场景

某 Unity 材质调色 shader 使用一个 `Color` 属性作为 tint 乘色：

```shader
_TintColor("Tint Color", Color) = (1,1,1,1)
```

材质面板由 LWGUI 绘制，用户在 Unity Color Picker 中切换到 HSV 模式后，将 `S` 设为 100、`V` 设为 0。表现为：

- 当次颜色面板中还能看到用户选择过的色相和饱和度。
- 关闭颜色面板后，材质属性实际保存为 `RGB(0, 0, 0)`。
- 再次打开颜色面板时，Unity 只能从纯黑 RGB 反推 HSV，`S` 会变成 0。
- shader 中即使有“最小亮度”参数，也只是把 `HSV(0,0,0)` 抬成 `HSV(0,0,minV)`，结果是无彩色灰度，而不是用户原先选择的红、蓝或其他色相。

#### 根因

HSV 到 RGB 在 `V=0` 时是多对一映射：

```text
HSV(0.0, 1.0, 0.0) -> RGB(0, 0, 0)
HSV(0.3, 1.0, 0.0) -> RGB(0, 0, 0)
HSV(0.7, 0.5, 0.0) -> RGB(0, 0, 0)
```

一旦材质只保存了 `RGB(0,0,0)`，原始 H/S 信息已经不可逆丢失。shader 或 C# 后续只能知道“这是黑色”，不能知道它曾经是“亮度为 0 的红色”还是“亮度为 0 的蓝色”。

Unity 官方 Issue Tracker `UUM-59751` 对同类问题的处理意见也是：Color 值按 RGB 序列化，因此精确 HSV 值可能不会在转换中保留；若自定义系统需要保留 HSV，必须单独存储 HSV，再转换成 Unity Color。

#### 版本边界

本记录不是永久性 Unity API 断言，而是基于以下 Unity 版本范围的排查结论：

- 本地复现环境为 Unity 2022.3.62f3 / URP 14，使用 Unity 默认 `Color` 材质属性绘制路径。
- Unity Issue Tracker UUM-59751 在 2024-01-03 标注的可复现版本包括 2021.3.34f1、2022.3.17f1、2023.2.4f1、2023.3.0b1。
- 如果目标 Unity 版本修改了 `Color` 序列化方式、Color Picker 行为，或提供单独持久化 HSV 的材质属性支持，本记录需要重新验证并更新状态。
- 在未完成目标版本验证前，只能把本结论用于“Unity 默认 `Color`/`EditorGUI.ColorField` 仍按 RGB 持久化”的场景。

#### LWGUI 不是根因

本次检查的 LWGUI 材质面板中，普通属性绘制路径最终仍调用 Unity 默认材质属性绘制：

```csharp
materialEditor.ShaderProperty(rect, prop, label);
```

`[Sub]` drawer 的默认路径也只是委托给 Unity 的默认 shader property GUI：

```csharp
editor.DefaultShaderPropertyInternal(position, prop, label);
```

LWGUI 的 `ColorDrawer` 只是把多个 `Color` 属性压缩到同一行显示，核心仍是：

```csharp
var src = cProp.colorValue;
var dst = EditorGUI.ColorField(r, GUIContent.none, src, true, true, isHdr);
cProp.colorValue = dst;
```

因此该现象不是 LWGUI 特有 bug，而是 Unity 默认 `Color` / `ColorField` 只持久化 RGB 的设计限制。

#### 不推荐的 shader 侧补偿

不要在 shader 中对 `Color` 属性做类似下面的最小亮度补偿来“修复”HSV 黑色：

```hlsl
float3 hsv = RgbToHsv(_TintColor.rgb);
hsv.z = max(hsv.z, _MinBrightness);
float3 color = HsvToRgb(hsv);
```

当该 `Color` 属性的 RGB 为 0 时，`RgbToHsv` 已经无法恢复 H/S。这个补偿看似让亮度限制生效，实际会把颜色变成灰色或默认 H/S 颜色，容易误导使用者。

#### 推荐处理策略

1. 如果材质协议继续使用 Unity `Color` 属性，就不要允许业务入口写入 `V=0` 的颜色。
2. 在 C#、UI 或数据配置入口限制 HSV 的 `V` 下限，例如 `0.01` 或按视觉效果确定的更高阈值。
3. shader 侧直接使用传入的 RGB，不再试图从纯黑 RGB 中恢复色相和饱和度。
4. 只有当业务确实需要支持“亮度为 0 但仍保留 H/S”时，才设计独立 HSV 参数或自定义 Inspector 序列化，例如 `_Hue`、`_Saturation`、`_Value`。

#### 判断准则

- **低亮但非黑 RGB**：可以通过更小 epsilon 的 RGB→HSV 函数改善低亮区域饱和度被压低的问题。
- **精确 RGB 黑色**：无解，除非有额外的 H/S 存储来源。
- **材质调色工具**：若最终只写 Unity `Color`，必须在写入前限制最小 V，不能依赖 shader 后处理补救。

### 关键代码

```csharp
// 推荐：在写入 Unity Color 前限制 HSV 的 V 下限。
const float MinColorValue = 0.01f;

Color ClampHsvValueBeforeWritingColor(float h, float s, float v, float a)
{
    v = Mathf.Max(v, MinColorValue);
    Color color = Color.HSVToRGB(h, s, v, hdr: true);
    color.a = a;
    return color;
}
```

```hlsl
// 推荐：shader 侧只消费最终 RGB，不做“从黑色恢复 HSV”的补偿。
baseRGB = lerp(baseRGB, baseRGB * _TintColor.rgb, mask);
```

### 参考链接

- [Unity Issue Tracker UUM-59751 - HSV color doesn't stay the same when it's changed](https://issuetracker.unity3d.com/issues/hsv-color-doesnt-stay-the-same-when-its-changed) - Unity 官方说明 Color 按 RGB 序列化，HSV 需要额外存储。
- [Unity Scripting API - Color.RGBToHSV](https://docs.unity3d.com/ScriptReference/Color.RGBToHSV.html) - Unity 从 RGB 重新计算 HSV 的官方 API。

### 相关记录

- [Shader 调试：Alpha 通道输出到 RGB 时的 sRGB 伽马偏差](./shader-debug-alpha-srgb-encoding-pitfall.md) - 同一类材质/颜色调试问题，涉及颜色与通道解释差异。
- [色彩空间知识](./color-space-gamma-linear.md) - Unity 颜色空间与 sRGB/Linear 基础背景。

### 验证记录

- [2026-06-02] 初次记录。基于某 Unity 材质调色 shader 的 `Color` 属性调试、LWGUI 普通 `Color` 属性绘制路径检查、Unity Issue Tracker UUM-59751 与 Unity `Color.RGBToHSV` 文档交叉验证。结论：`Color` 属性在 `V=0` 时只能保存为 RGB 纯黑，H/S 信息丢失后不可恢复；工程上应在写入端限制 HSV V 下限，或改用独立 HSV 参数。
- [2026-06-02] 修正：补充版本边界，将适用版本从泛化的 Unity 2021.3+/2022.3+/2023.2+ 收窄为“本地复现版本与官方 Issue Tracker 标注版本”，并明确其他 Unity 版本需要重新验证。
- [2026-06-02] 修正：执行记录脱敏补强，移除示例参数中的业务语义前缀，统一改为 `_TintColor`、`_Hue`、`_Saturation`、`_Value` 等通用技术命名。
- [2026-06-02] 修正：将日期式边界表述调整为版本边界，本地复现版本精确为 Unity 2022.3.62f3 / URP 14；其他 Unity 版本以实际 `Color`/Color Picker 序列化行为重新验证。

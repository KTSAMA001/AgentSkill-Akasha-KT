# ASE Meta Pass 与自发光烘焙完整链路

**标签**：#shader #unity #urp #material #experience #troubleshooting
**来源**：项目实践验证 + 本地 ASE/URP 源码验证
**收录日期**：2026-05-12
**来源日期**：2026-05-12
**更新日期**：2026-05-12
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐ (项目实测 + 源码验证)
**适用版本**：Unity URP 14.0.12；Amplify Shader Editor 1.9.8.1；Bakery/Unity Lightmap 烘焙流程

### 概要

Unity/URP 的 `Meta` Pass 是给 lightmap/GI 烘焙器读取材质 `Albedo` 与 `Emission` 的特殊 Pass，不参与运行时相机渲染。ASE 自定义 Shader 想让纹理和自发光正确参与烘焙，需要同时接好 `Baked Albedo` / `Baked Emission`，并让 Shader 的 SubShader Tags 带上 `"IsEmissive"="true"`，最终验证材质 `.mat` 中 `m_LightmapFlags` 为 `2`。

### 内容

#### Meta Pass 是什么

`Meta` Pass 是 Unity 烘焙流程使用的特殊 Shader Pass，典型标记为：

```shader
Pass
{
    Name "Meta"
    Tags { "LightMode"="Meta" }
}
```

它的核心用途不是把物体画到主相机画面，而是在烘焙 lightmap/GI 时告诉烘焙器这个材质的两个关键输入：

- `Albedo`：材质本身的反照率，即基础颜色/纹理贡献。
- `Emission`：材质自身发出的光，即自发光颜色/贴图贡献。

URP/ASE 生成的 Meta Pass 顶点阶段通常会调用 `MetaVertexPosition(...)`，把几何按 lightmap UV 空间展开给烘焙器采样。这解释了为什么 Meta Pass 里通常只关心材质输入，而不应该混入运行时相机、雾效、屏幕空间或已采样 lightmap 的结果。

如果 Shader 没有有效的 Meta Pass，或者 Meta Pass 中 `metaInput.Albedo` / `metaInput.Emission` 仍为 `0`，烘焙器就无法从这个 Shader 得到正确的材质反照率或自发光贡献。

#### 问题场景

在 URP + ASE 的场景 Shader 中，为了让纹理和自发光参与 lightmap/GI 烘焙，需要处理两层问题：

1. `Meta` Pass 必须给烘焙器输出正确的 `Albedo` 和 `Emission`。
2. ASE Master 节点上的 `Baked Albedo` 和 `Baked Emission` 必须接到适合烘焙的材质数据，而不是运行时最终色。
3. 材质资产本身的 GI flag 必须是干净的 `BakedEmissive`，不能同时带 `EmissiveIsBlack`。

只完成第一步并不够。实测中 ASE 材质 Inspector 的 `Global Illumination = Baked` 看起来和 URP SimpleLit 一样，但落盘后的 `.mat` 可能是：

```yaml
m_LightmapFlags: 6
```

`6 = BakedEmissive(2) + EmissiveIsBlack(4)`。这会导致自发光在烘焙阶段被当作黑色，Bakery 的 emissive pass 尤其容易直接忽略它。

#### Meta Pass 正确接法

在 ASE Master 节点上：

- `Baked Albedo` 接基础材质颜色，即主纹理/程序纹理结果，但不要包含 lightmap、fog、相机相关效果或 emission。
- `Baked Emission` 接自发光结果，例如 `EmissionColor * EmissionMap`。
- 运行时 `Color` 可以继续接 `基础颜色 * Lightmap + Emission`。

关键原则：`Baked Albedo` 表示材质反照率，不是最终屏幕颜色。不要把已经采样过的 lightmap 再接进 `Baked Albedo`，否则会形成双重烘焙或错误变暗。

以自采 lightmap 的 ASE 场景 Shader 为例，推荐链路是：

```text
BaseMap * PixelMap
    -> Baked Albedo

EmissionColor * EmissionMap
    -> Baked Emission

BaseMap * PixelMap * LightMap_ON_Switch + EmissionColor * EmissionMap
    -> Color
```

这样烘焙器看到的是材质本体，运行时看到的是已经乘过 lightmap 的最终显示效果。

#### ASE Inspector 为什么会把 Baked 写成 6

ASE 的材质 Inspector 会先调用 Unity 的 lightmap emission UI，再根据 Shader Tag 二次修正材质 flag。逻辑等价于：

```csharp
materialEditor.LightmapEmissionProperty();

string isEmissive = mat.GetTag("IsEmissive", false, "false");
if (isEmissive.Equals("true"))
{
    mat.globalIlluminationFlags &= (MaterialGlobalIlluminationFlags)3;
}
else
{
    mat.globalIlluminationFlags |= MaterialGlobalIlluminationFlags.EmissiveIsBlack;
}
```

因此如果 Shader 没有 `"IsEmissive"="true"`，即使 Inspector 下拉选了 `Baked`，ASE 仍会把 `EmissiveIsBlack` 加回去，最终变成 `6`。

#### SimpleLit 为什么可以

URP SimpleLit 使用自己的 `SimpleLitShader`/`BaseShaderGUI` Inspector。它会绘制 Emission 勾选与 Global Illumination 下拉，并通过 Unity 的 emissive flag 修正逻辑同步 `_EMISSION` keyword 与材质 GI flag。

SimpleLit 的 Meta Pass 也明确输出：

```hlsl
metaInput.Albedo = _BaseColor.rgb * SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, uv).rgb;
metaInput.Emission = SampleEmission(uv, _EmissionColor.rgb, TEXTURE2D_ARGS(_EmissionMap, sampler_EmissionMap));
```

ASE 自定义 Shader 要达到同等效果，需要同时满足：

- Meta Pass 输出正确的 `Albedo`。
- Meta Pass 输出正确的 `Emission`。
- 材质 `globalIlluminationFlags` 是干净的 `BakedEmissive`。
- Shader 带有让 ASE Inspector 正确处理 emissive flag 的 `IsEmissive` tag。

#### ASE 中添加方式

不要手改生成后的 `.shader`，因为下次保存 ASE 图会覆盖。推荐在 ASE Master/Output 节点中添加自定义 SubShader Tag：

1. 选中最终 Master/Output 节点。
2. 找到 `Custom SubShader Tags` 或 `Tags` 区域。
3. 点 `+` 新增一项。
4. 填入：

```text
Name  = IsEmissive
Value = true
```

保存后，生成的 SubShader Tags 应包含：

```shader
Tags
{
    "RenderPipeline"="UniversalPipeline"
    "RenderType"="Opaque"
    "Queue"="Geometry"
    "UniversalMaterialType"="Unlit"
    "IsEmissive"="true"
}
```

然后回到材质 Inspector，把 `Global Illumination` 再选为 `Baked`，确认 `.mat` 落盘为：

```yaml
m_LightmapFlags: 2
```

这才是干净的 `MaterialGlobalIlluminationFlags.BakedEmissive`。

#### 验证清单

- Shader 的 `Meta` Pass 存在 `Tags { "LightMode"="Meta" }`。
- Meta Pass 顶点阶段使用 lightmap UV 空间，例如调用 `MetaVertexPosition(...)`。
- `metaInput.Albedo` 来源是基础纹理/材质色，不含 lightmap。
- `metaInput.Emission` 来源是发光颜色/贴图，且材质发光颜色非黑。
- ASE Master 节点中 `Baked Albedo` 不接运行时最终 `Color`。
- ASE Master 节点中 `Baked Emission` 不为 `0`，且确实进入 `metaInput.Emission`。
- SubShader Tags 包含 `"IsEmissive"="true"`。
- 材质 `.mat` 中 `m_LightmapFlags: 2`，不是 `4` 或 `6`。
- 参与烘焙的 Renderer/物体启用 `Contribute GI` 或等价静态 GI 设置。
- 若使用 Bakery，尤其要确认材质 flag 精确为 `BakedEmissive`，因为部分 Bakery 流程会把非 `2` 的 emissive 材质按黑色处理。

### 关键代码（如有）

```shader
// Meta Pass 是烘焙入口，不参与运行时主相机渲染
Pass
{
    Name "Meta"
    Tags { "LightMode"="Meta" }
}

// Meta Pass 最终应把材质输入写给烘焙器
metaInput.Albedo = bakedAlbedo;
metaInput.Emission = bakedEmission;
```

```shader
// ASE 生成 Shader 中需要出现的 SubShader Tag
Tags { "RenderPipeline"="UniversalPipeline" "RenderType"="Opaque" "Queue"="Geometry" "IsEmissive"="true" }
```

```yaml
# 正确：BakedEmissive
m_LightmapFlags: 2

# 错误：BakedEmissive + EmissiveIsBlack
m_LightmapFlags: 6
```

### 参考链接（如有）

- [Unity Scripting API - MaterialGlobalIlluminationFlags](https://docs.unity3d.com/ScriptReference/MaterialGlobalIlluminationFlags.html) - 材质 GI flag 枚举说明
- [Unity Manual - Meta Pass](https://docs.unity.cn/Manual/MetaPass.html) - Meta Pass 用于 lightmap/GI 烘焙输入

### 相关记录（如有）

- [ASE Shader 架构与 Bakery 光照集成最佳实践](./ase-shader-bakery-integration.md) - ASE 与 Bakery 项目集成经验
- [Amplify Shader Editor 架构与实现机制解析](./amplify-shader-editor-architecture.md) - ASE 模板、图数据和代码生成机制

### 验证记录

- [2026-05-12] 基于项目内自定义 ASE 场景 Shader、ASE 1.9.8.1 源码、URP 14.0.12 SimpleLit 源码和材质 `.mat` 序列化结果验证。确认 Meta Pass 用于烘焙器读取 `Albedo`/`Emission`，不是运行时主相机渲染；实测发现未添加 `IsEmissive` tag 时 ASE 的 `Global Illumination = Baked` 会落为 `m_LightmapFlags: 6`；添加 tag 后重新设置 Baked 可落为 `m_LightmapFlags: 2`，自发光烘焙恢复正常。

---

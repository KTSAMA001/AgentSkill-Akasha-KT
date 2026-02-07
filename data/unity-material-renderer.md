# Unity 渲染相关知识

## Renderer.material 与 Renderer.materials 的实例化行为

**分类**：Unity > Rendering > Material
**标签**：#unity #knowledge #rendering #material
**来源**：Unity 官方文档
**来源日期**：2026-01-31
**收录日期**：2026-02-02
**可信度**：⭐⭐⭐⭐⭐(官方)
**状态**：📘 有效

### 定义/概念

Unity 中 `Renderer.material` 和 `Renderer.materials` 属性用于访问渲染器的材质实例。首次访问时会自动从 SharedMaterial 克隆一份独立实例，后续访问返回同一实例。

### 原理/详解

#### `renderer.material`

> 官方文档原文：
> "Returns the first **instantiated** Material assigned to the renderer."
> "Modifying `material` will change the material for this object only. **If the material is used by any other renderers, this will clone the shared material and start using it from now on.**"

#### `renderer.materials`

> 官方文档原文：
> "Returns all the **instantiated** materials of this object."
> "Note that like all arrays returned by Unity, **this returns a copy of materials array**."

#### 内存管理注意

> "This function automatically instantiates the materials and makes them unique to this renderer. **It is your responsibility to destroy the materials when the game object is being destroyed.** Resources.UnloadUnusedAssets also destroys the materials but it is usually only called when loading a new level."

### 关键点

- **首次访问**：`renderer.material` / `renderer.materials` 首次访问时，如果材质是 SharedMaterial，Unity 会自动克隆一份独立实例
- **后续访问**：返回已创建的实例，**不会重新克隆**
- **数组行为**：`renderer.materials` 每次调用都返回**新的数组副本**，但数组内的 Material 引用是**相同的实例**
- **外部替换**：如果通过 `renderer.materials = newMats` 或 `renderer.sharedMaterials = ...` 整体替换材质，旧的实例引用失效
- **内存责任**：开发者需要在对象销毁时手动 Destroy 实例化的材质，否则会内存泄漏

### 示例

```csharp
void TestMaterialBehavior()
{
    var renderer = GetComponent<Renderer>();
    
    // 测试数组副本行为
    Material[] mats1 = renderer.materials;  // 触发实例化（如果是首次）
    Material[] mats2 = renderer.materials;  // 返回新数组副本
    
    Debug.Log($"数组相同? {mats1 == mats2}");           // False - 不同的数组对象
    Debug.Log($"材质相同? {mats1[0] == mats2[0]}");     // True - 同一个材质实例
    Debug.Log($"材质ID: {mats1[0].GetInstanceID()} vs {mats2[0].GetInstanceID()}"); // 相同
    
    // 修改材质属性
    mats1[0].color = Color.red;  // 会影响渲染，因为是同一个实例
}

void OnDestroy()
{
    // 需要手动销毁实例化的材质
    var renderer = GetComponent<Renderer>();
    foreach (var mat in renderer.materials)
    {
        Destroy(mat);
    }
}
```

### 对比表

| 属性 | 首次访问 | 后续访问 | 返回值特性 |
|------|---------|---------|-----------|
| `renderer.material` | 克隆实例 | 返回已有实例 | 单个 Material |
| `renderer.materials` | 克隆所有材质 | 返回已有实例 | **每次返回新数组副本**，但内部 Material 引用相同 |
| `renderer.sharedMaterial` | 不克隆 | 不克隆 | 原始 SharedMaterial |
| `renderer.sharedMaterials` | 不克隆 | 不克隆 | 每次返回新数组副本 |

### 常见陷阱

1. **误以为每次访问都创建新实例** - 实际上只有首次访问创建，后续返回同一实例
2. **误以为数组引用相同** - `renderer.materials` 每次返回新数组，但这不意味着材质被重新克隆
3. **忘记销毁实例化材质** - 导致内存泄漏
4. **外部替换材质后缓存失效** - 如果其他代码替换了 `renderer.materials`，之前保存的材质引用就失效了

### 相关知识

- [Unity 官方文档 - Renderer.material](https://docs.unity3d.com/ScriptReference/Renderer-material.html)
- [Unity 官方文档 - Renderer.materials](https://docs.unity3d.com/ScriptReference/Renderer-materials.html)

### 与经验关联

- 实践验证：LogicMatAnimCtrl 材质动画控制器中，需要实时获取材质以支持运行时替换场景

---

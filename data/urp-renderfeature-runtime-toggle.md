# RenderFeature 运行时开关控制 {#renderfeature-toggler}

**收录日期**：2026-02-07
**来源日期**：2024-08-08
**标签**：#shader #unity #experience #urp #srp-batcher #renderer-feature
**来源**：Unity_URP_Learning
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐ (代码验证)
**适用版本**：Unity 2022.3+ / URP 14.0+

**问题/场景**：

在 URP 中需要运行时动态开关 RenderFeature（如调试时禁用某些后处理效果），默认 RenderFeature 只能在 Inspector 中手动勾选。

**解决方案/结论**：

通过 `ScriptableRendererFeature.SetActive()` 方法运行时控制：

```csharp
[System.Serializable]
public struct RenderFeatureToggle
{
    public ScriptableRendererFeature feature;
    public bool isEnabled;
}

[ExecuteAlways]
public class RenderFeatureToggler : MonoBehaviour
{
    [SerializeField] private List<RenderFeatureToggle> renderFeatures;
    [SerializeField] private UniversalRenderPipelineAsset pipelineAsset;

    private void Update()
    {
        foreach (var toggle in renderFeatures)
            toggle.feature.SetActive(toggle.isEnabled);
    }
}
```

**关键代码**：

- `ScriptableRendererFeature.SetActive(bool)` — URP 内置 API
- `[ExecuteAlways]` — 确保在编辑器和运行时都生效

**验证记录**：

- [2026-02-07] 从 Unity_URP_Learning 仓库整合

**相关经验**：

- [URP Renderer Feature 开发要点](./urp-renderer-feature-guide.md) — RenderFeature 基础模式

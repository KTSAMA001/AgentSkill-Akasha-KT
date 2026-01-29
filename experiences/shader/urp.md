# URP 渲染管线经验

> Universal Render Pipeline 相关经验
>
> 包含：URP Shader、渲染特性、自定义 Pass、后处理等

---

## ASE Shader 架构与 Bakery 光照集成最佳实践

**日期**：2026-01-29
**标签**：#ASE #ShaderGraph #Bakery #SH光照 #模块化 #变体优化  
**状态**：✅ 已验证

**问题/场景**：

在使用 Amplify Shader Editor (ASE) 开发角色、道具、场景 Shader 时，如何合理组织 Shader 架构，特别是与 Bakery 烘焙光照（SH 球谐）集成时的最佳实践。

**解决方案/结论**：

### 1. ASE 节点架构原则

**核心原则**：ASE Shader 图不应直接引用具体 hlsl 文件，功能细节应封装到各自的节点组中。

- ✅ 将复杂功能（如 SH 光照、RimLight、LatLong 特效）拆分为独立的 ASE 节点组（SubGraph）
- ✅ 每个节点组负责单一功能，对外暴露必要参数
- ✅ 主 Shader 图只负责组合各节点组，而非实现具体逻辑

### 2. SH 光照参数外置

**原因**：让节点可以灵活控制光照来源，提高通用性。

`hlsl
// ❌ 之前：在 shader 内联获取 L0
float3 BakerySH(float3 normalWorld, float2 lightmapUV) {
    BakerySH_float(float3(unity_SHAr.w, unity_SHAg.w, unity_SHAb.w), normalWorld, lightmapUV, sh); 
    return sh;
}

// ✅ 之后：L0 从外部节点传入，更灵活
float3 UnitySHAr() {
    return float3(unity_SHAr.w, unity_SHAg.w, unity_SHAb.w);
}
// 在节点组中调用：BakerySH_float(L0, normalWorld, lightmapUV, sh)
`

### 3. Include 路径使用相对路径

`hlsl
// ❌ 绝对路径：项目迁移后会失效
#include "Assets/CommonFunctionModule/.../BakeryDecodeLightmap.hlsl"

// ✅ 相对路径：更具可移植性
#include "../../../../CommonFunctionModule/.../BakeryDecodeLightmap.hlsl"
`

### 4. 移除不必要的 multi_compile

减少 Shader 变体数量，显著降低编译时间和内存占用：

`hlsl
// ❌ 不必要时移除这些变体声明
#pragma multi_compile _ _ADDITIONAL_LIGHTS_VERTEX _ADDITIONAL_LIGHTS
#pragma multi_compile_fragment _ _ADDITIONAL_LIGHT_SHADOWS
#pragma multi_compile _ _FORWARD_PLUS
#pragma multi_compile _ _LIGHT_LAYERS
`

**影响**：移除不必要宏可以很大程度减少变体数量，提升编译效率。

### 5. 资源清理

定期清理废弃的材质和 Shader 资源，避免：
- 资源引用混乱
- 项目体积膨胀
- 潜在的引用错误

**参考链接**：

- [Bakery GPU Lightmapper 官方文档](https://geom.io/bakery/wiki/)
- [Amplify Shader Editor 官方文档](https://wiki.amplify.pt/index.php)

**验证记录**：

- [2026-01-29] KTSAMA 提交验证，变体优化后编译时间和内存显著下降

**备注**：

此经验来源于项目实际开发中 KTSAMA 的 Shader 重构工作，适用于使用 ASE + Bakery + URP 的项目。

# Unity 中 Shader 相关经验

> Unity 中 Shader 相关经验
>
> 包含：ShaderLab、Shader Graph、材质属性、渲染队列、多 Pass 等

---

## VR Shader 变体收集器开发复盘

**日期**：2026-01-29
**标签**：#unity #shader #experience #shader-variants #editor
**状态**：✅ 已验证

**背景**：
为了解决 VR 项目中 Shader 变体丢失、预热时间过长以及打包剔除问题，开发了一套自动化变体收集工具。在此过程中积累了大量关于 Unity Shader 编译机制和变体管理的深度经验。

**关键经验总结**：

### 1. 编译机制与变体丢失
- **必须禁用异步编译**：EditorSettings.asyncShaderCompilation = false。异步编译会产生"中间变体"（包含不存在的宏组合），导致运行时报错。
- **预热阶段**：首次收集前必须先跑一遍渲染流程并清空缓存，消除冷启动产生的临时变体。

### 2. 双文件策略解决打包剔除
- **NonVR SVC**：包含完整变体（含非 VR 宏），用于打包引用，防止 Shader 被引擎剔除。
- **VR SVC**：仅包含 STEREO_MULTIVIEW_ON 等 VR 宏变体，仅用于运行时预热，节省 50% 时间。
- **注意**：如果 SVC 只含 VR 变体，Unity 打包时会认为"当前平台未启用 VR"而剔除这些变体，导致 AB 包中丢失变体。

### 3. URP 与宏的坑点
- **_ADDITIONAL_LIGHTS**：URP 管线开启额外光后，即使场景无光，收集结果也会强制带此宏。需后处理移除，否则全烘焙场景无法匹配。
- **multi_compile** 声明：避免使用 multi_compile_local_fragment，在同步编译下会导致产生无宏变体，应使用 multi_compile_local。
- **shader_feature** 丢失：若 SVC 只有 VR 变体，shader_feature_local 宏会全部丢失，需配合双文件策略解决。

### 4. 编辑器环境隔离
- **环境污染**：Inspector、Project 预览窗口会在后台渲染材质，产生干扰变体。
- **解决方案**：收集时必须强制关闭除 Game View 外的所有窗口。

**详细文档**：
- [VR变体收集器完整架构文档](./vr-variant-collector-architecture.md)

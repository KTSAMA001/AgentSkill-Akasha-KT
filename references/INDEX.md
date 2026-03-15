# 索引

## 参考文档

| 文档 | 路径 | 用途 |
|------|------|------|
| **查找流程** | [workflows/search.md](./workflows/search.md) | 检索记录、网络搜索 |
| **记录流程** | [workflows/record.md](./workflows/record.md) | 记录经验/知识 |
| **验证流程** | [workflows/validate.md](./workflows/validate.md) | 修正、废弃记录 |
| 使用示例 | [EXAMPLES.md](./EXAMPLES.md) | 参考用法 |
| 记录模板 | [templates/record-template.md](./templates/record-template.md) | 通用记录模板 |
| **标签注册表** | [tag-registry.md](./tag-registry.md) | 标签元数据（显示名、图标） |

---

## 标签概览

> 完整元数据（显示名、图标）见 [tag-registry.md](./tag-registry.md)。新增标签时需同时注册。

`#agent-skills` `#ai` `#ai-navigation` `#akasha` `#animation` `#animation-retarget` `#anti-bot` `#architecture` `#arknights` `#astrbot` `#astc` `#audio` `#behavior-designer` `#bilibili` `#blend-tree` `#brdf` `#bug` `#cicd` `#claude-code` `#collider` `#color-banding` `#color-space` `#compute-shader` `#conventional-commits` `#cook-torrance` `#copilot` `#credential` `#cross-platform` `#csharp` `#culling` `#custom-editor` `#cyberpunk` `#deployment` `#design` `#dither` `#docker` `#docx` `#dotnet` `#draw-call` `#ecs` `#editor` `#effect-system` `#effects` `#excel` `#experience` `#fbx` `#feishu` `#font` `#gamma` `#git` `#github-actions` `#gpgpu` `#graphics` `#hdr` `#hlsl` `#idea` `#identity` `#ik` `#knowledge` `#ktsama` `#linear` `#markdown` `#material` `#math` `#mcp` `#meilisearch` `#memory` `#mvvm` `#nav-mesh` `#npr` `#openclaw` `#pat` `#pbr` `#performance` `#physics` `#playwright` `#post-processing` `#python` `#raycast` `#react` `#reference` `#renderer-feature` `#rendering` `#rendering-pipeline` `#retarget-pro` `#root-motion` `#scene` `#scriptable-object` `#sdf` `#search-api` `#search-engine` `#searxng` `#selenium` `#serialization` `#serp` `#shader` `#shader-variants` `#skybox` `#smart-furniture` `#social` `#srp` `#srp-batcher` `#texture` `#tools` `#troubleshooting` `#ui` `#unicode` `#unity` `#urp` `#vera` `#vitepress` `#vr` `#vscode` `#web` `#windows` `#3dsmax` `#配置管理` `#持久化` `#测试` `#workflow`

---

## 文件清单

| 文件 | 标签 | 状态 | 简述 |
|------|------|------|------|
| [agent-skills-spec.md](../data/agent-skills-spec.md) | #ai #knowledge #agent-skills | 📘 有效 | Agent Skills 规范 |
| [akasha-semantic-search-architecture.md](../data/akasha-semantic-search-architecture.md) | #architecture #ai #mcp #akasha #search-engine #python | 💡 构想中 | 阿卡西记录语义搜索架构设计 |
| [astc-compression-formula.md](../data/astc-compression-formula.md) | #unity #texture #memory #astc #experience | ✅ 已验证 | ASTC 纹理压缩内存估算公式 |
| [akasha-visualization-web.md](../data/akasha-visualization-web.md) | #tools #web #reference #akasha | 📘 有效 | 阿卡西记录可视化网站 |
| [animation-retarget-root-motion-algorithm.md](../data/animation-retarget-root-motion-algorithm.md) | #unity #animation #math #root-motion #animation-retarget #knowledge | 📘 有效 | 3D 动画重定向与根运动算法解析 (Animation Retargeting & Root Motion) |
| [animation-retarget-technology-unity.md](../data/animation-retarget-technology-unity.md) | #unity #animation #animation-retarget #knowledge #ik | 📘 有效 | 动画重定向技术分析和 Unity 中的应用 |
| [arknights-ui-industrial-style.md](../data/arknights-ui-industrial-style.md) | #design #knowledge #arknights #ui | 📘 有效 | 明日方舟工业风 UI：网点、网格、切角、噪点等视觉元素总结 |
| [ase-shader-bakery-integration.md](../data/ase-shader-bakery-integration.md) | #shader #unity #experience #urp #srp-batcher #renderer-feature | ✅ 已验证 | ASE Shader 架构与 Bakery 光照集成最佳实践 |
| [astrbot-mcp-service-config.md](../data/astrbot-mcp-service-config.md) | #ai #experience #mcp #astrbot | ✅ 已验证 | AstrBot 集成 MCP 服务经验 |
| [astrbot-messages-param-error.md](../data/astrbot-messages-param-error.md) | #ai #experience #astrbot #bug | ⚠️ 部分解决（v4.13.2 仍有报告） | AstrBot "messages 参数非法" 错误 |
| [astrbot-plugin-file-upload-onebot.md](../data/astrbot-plugin-file-upload-onebot.md) | #ai #experience #mcp #astrbot | ✅ 已验证 | AstrBot 插件文件上传到QQ实现 |
| [astrbot-plugin-llm-request-interceptor.md](../data/astrbot-plugin-llm-request-interceptor.md) | #ai #experience #mcp #astrbot | ✅ 已验证 | AstrBot 插件自动触发函数（LLM 请求拦截） |
| [bd-log-throttle.md](../data/bd-log-throttle.md) | #unity #experience #editor #behavior-designer | ✅ 已验证 | BD 节点日志频率控制 {#bd-log-throttle} |
| [bd-showif-workaround.md](../data/bd-showif-workaround.md) | #unity #experience #editor #behavior-designer | ✅ 已验证 | BD 节点条件显示的替代方案 {#bd-showif-workaround} |
| [bd-tooltip-namespace-conflict.md](../data/bd-tooltip-namespace-conflict.md) | #unity #experience #editor #behavior-designer | ✅ 已验证 | BD 节点 Tooltip 命名空间冲突解决 {#bd-tooltip-namespace-conflict} |
| [behavior-designer-api.md](../data/behavior-designer-api.md) | #unity #knowledge #behavior-designer #ai | 📘 有效 | Behavior Designer 行为树插件的技术规范、API 和原理 |
| [browser-automation-search-mcp-dev.md](../data/browser-automation-search-mcp-dev.md) | #python #playwright #mcp #experience #web #tools | ⚠️ 待验证（MCP部分未完成） | 浏览器自动化搜索 MCP 开发记录 |
| [cbuffer-srp-batcher-mechanism.md](../data/cbuffer-srp-batcher-mechanism.md) | #shader #unity #experience #urp #srp-batcher #renderer-feature | ✅ 已验证 | CBUFFER 与 SRP Batcher 合批机制 |
| [cicd-vitepress-deploy.md](../data/cicd-vitepress-deploy.md) | #tools #experience #cicd #vitepress #github-actions | ✅ 已验证 | 持续集成/持续部署相关经验 |
| [claude-code-backend-models.md](../data/claude-code-backend-models.md) | #ai #tools #reference #claude-code | ✅ 已验证 | Claude Code 作为 Agent 框架接入多种模型 (LLM Gateway) |
| [claude-code-comprehensive-guide.md](../data/claude-code-comprehensive-guide.md) | #ai #tools #reference #claude-code | ✅ 已验证 | Claude Code 完整指南 |
| [claude-code-fork-session.md](../data/claude-code-fork-session.md) | #ai #tools #reference #claude-code | ✅ 已验证 | Claude Code Fork 会话功能 (Branching Conversation) |
| [claude-code-slash-commands.md](../data/claude-code-slash-commands.md) | #ai #tools #reference #claude-code | ✅ 已验证 | Claude Code 完整斜杠命令列表 (Slash Commands) |
| [claude-code-latest-features-2026.md](../data/claude-code-latest-features-2026.md) | #ai #tools #reference #claude-code | ✅ 已验证 | Claude Code 最新功能 (2026-03)：Plugin System、Agent Teams、1M Context、Adaptive Thinking |
| [color-banding-dither.md](../data/color-banding-dither.md) | #graphics #knowledge #color-banding #dither #hdr | 📘 有效 | 色带（Color Banding）与抖动（Dithering）知识 |
| [color-space-gamma-linear.md](../data/color-space-gamma-linear.md) | #graphics #knowledge #color-space #gamma #linear | 📘 有效 | 色彩空间知识 |
| [compute-shader-gpu-parallel.md](../data/compute-shader-gpu-parallel.md) | #graphics #shader #knowledge #compute-shader #gpgpu | 📘 有效 | GPU 通用计算 (GPGPU) 相关原理与概念 |
| [docker-container-git-auth-persist.md](../data/docker-container-git-auth-persist.md) | #git #experience #docker #credential #troubleshooting | ✅ 已验证 | Docker 容器重建后 Git 认证持久化配置 {#docker-git-auth-persist} |
| [docker-git-credential-persist.md](../data/docker-git-credential-persist.md) | #git #experience #pat #docker #credential | ✅ 已验证 | Docker 容器内 Git PAT 凭据持久化配置 {#docker-git-credential} |
| [docker-vs-native-deployment-file-access.md](../data/docker-vs-native-deployment-file-access.md) | #docker #deployment #tools #experience #ai | ✅ 已验证 | Docker 与原生部署：文件操作需求下的选择 |
| [dotnet-cross-platform-compile-verify.md](../data/dotnet-cross-platform-compile-verify.md) | #csharp #dotnet #tools #experience | ✅ 已验证 | .NET 跨平台编译环境验证 |
| [effect-system-code-review.md](../data/effect-system-code-review.md) | #unity #architecture #scriptable-object #effect-system | ✅ 已验证 | EffectSystem 效果系统 - 代码审查与架构分析 |
| [excel-id-enum-generator.md](../data/excel-id-enum-generator.md) | #unity #tools #excel #experience | ✅ 已验证 | Excel ID 一键导出枚举 |
| [git-commit-conventions.md](../data/git-commit-conventions.md) | #git #reference #conventional-commits | ✅ 已验证 | Git 团队协作工作流相关经验 |
| [git-filter-repo-rewrite-history.md](../data/git-filter-repo-rewrite-history.md) | #git #experience #pat #docker #credential | ✅ 已验证 | 使用 git-filter-repo 重写提交历史（清除敏感信息） |
| [git-config-in-repo.md](../data/git-config-in-repo.md) | #git #docker #配置管理 #持久化 | ✅ 已验证 | Git 配置跟随仓库持久化 |
| [git-https-fail-switch-ssh.md](../data/git-https-fail-switch-ssh.md) | #git #experience #pat #docker #credential | ✅ 已验证 | Git HTTPS 拉取失败，改用 SSH 协议解决 |
| [git-object-corrupt-repair.md](../data/git-object-corrupt-repair.md) | #git #experience #pat #docker #credential | ⚠️ 解决方案已验证，根因待查 | Git 对象损坏（loose object corrupt）修复 {#git-object-corrupt} |
| [gpu-grass-large-scale-rendering.md](../data/gpu-grass-large-scale-rendering.md) | #shader #unity #experience #compute-shader #urp #performance | ✅ 已验证 | 大规模渲染 (Large-Scale Rendering) 相关经验 |
| [hlsl-syntax-semantics.md](../data/hlsl-syntax-semantics.md) | #graphics #shader #knowledge #hlsl | 📘 有效 | Unity Shader / HLSL 基础知识 |
| [idea-3d-girl-smart-furniture.md](../data/idea-3d-girl-smart-furniture.md) | #idea #smart-furniture | 💡 灵感记录 | 3D智能家具创意 |
| [img-svg-css-color-filter.md](../data/img-svg-css-color-filter.md) | #tools #web #experience #vitepress | ✅ 已验证 | img 标签的 SVG 无法继承 CSS color，需用 filter 着色 {#img-svg-color-filter} |
| [kinemation-retarget-pro-plugin.md](../data/kinemation-retarget-pro-plugin.md) | #unity #animation #knowledge #retarget-pro #animation-retarget #ik #scriptable-object | ✅ 已验证 | KINEMATION Retarget Pro 插件全面分析 |
| [kira-framework-analysis.md](../data/kira-framework-analysis.md) | #unity #csharp #architecture #ui #mvvm #knowledge | 📘 有效 | KiraFramework Unity 游戏开发框架分析 |
| [ktsama-bilibili-profile.md](../data/ktsama-bilibili-profile.md) | #social #reference #ktsama #bilibili | 📘 有效 | [KTSAMA的B站主页] |
| [llm-api-image-url-deserialize-error.md](../data/llm-api-image-url-deserialize-error.md) | #ai #experience #astrbot #bug | ✅ 已解决 | LLM API image_url 字段反序列化错误 - "unknown variant `image_url`, expected `text`" |
| [macos-git-osxkeychain-path.md](../data/macos-git-osxkeychain-path.md) | #git #experience #pat #docker #credential | ✅ 已验证 | macOS Git osxkeychain Credential Helper 路径问题 {#osxkeychain-path} |
| [md-to-word-converter-implementation.md](../data/md-to-word-converter-implementation.md) | #python #tools #experience #docx #markdown | ✅ 已验证 | Markdown to Word 转换器实现详解（python-docx + Pygments + Mermaid/PlantUML） |
| [material-unified-management.md](../data/material-unified-management.md) | #unity #shader #material #experience | ✅ 已验证 | 角色/怪物材质统一管理 |
| [mcp-protocol-agent-dev.md](../data/mcp-protocol-agent-dev.md) | #ai #experience #mcp | ✅ 已验证 | MCP 协议与 Agent 服务开发经验 |
| [monster-siren-web-analysis.md](../data/monster-siren-web-analysis.md) | #web #design #knowledge #arknights #react #cyberpunk | 📘 有效 | 塞壬唱片官网 (Monster Siren) 深度技术与设计分析 |
| [npr-rendering-outline.md](../data/npr-rendering-outline.md) | #shader #unity #experience #npr #renderer-feature #post-processing | ✅ 已验证 | 非真实感渲染 (Non-Photorealistic Rendering) 相关经验 |
| [pbr-brdf-theory.md](../data/pbr-brdf-theory.md) | #graphics #knowledge #pbr #brdf #cook-torrance | 📘 有效 | 基于物理的渲染（Physically Based Rendering）相关原理与概念 |
| [pbr-custom-shader-urp.md](../data/pbr-custom-shader-urp.md) | #shader #unity #experience #pbr #urp #hlsl | ✅ 已验证 | 基于物理的渲染 (Physically Based Rendering) 相关经验 |
| [physics-update-timing.md](../data/physics-update-timing.md) | #unity #physics #experience | ✅ 已验证 | 物理碰撞更新时机 |
| [prefab-variant-generator-v4-toolkit.md](../data/prefab-variant-generator-v4-toolkit.md) | #unity #tools #architecture #custom-editor #reference | ✅ 已验证 | PrefabVariantGeneratorV4 工具本体说明（定位、执行模型、端口机制、扩展规范） |
| [python-web-scraping-antibot.md](../data/python-web-scraping-antibot.md) | #python #experience #playwright #selenium #anti-bot | ✅ 已验证 | 网页抓取与反爬虫绕过 |
| [render-queue-design.md](../data/render-queue-design.md) | #unity #rendering #performance #experience | ✅ 已验证 | 渲染队列设计策略 |
| [rendering-pipeline-overview.md](../data/rendering-pipeline-overview.md) | #graphics #knowledge #rendering-pipeline #draw-call | 📘 有效 | 渲染管线知识 |
| [safari-svg-favicon-compat.md](../data/safari-svg-favicon-compat.md) | #tools #web #experience #vitepress | ⚠️ 待验证 | Safari SVG Favicon 兼容性 |
| [scene-asset-loading.md](../data/scene-asset-loading.md) | #unity #performance #scene #experience | ✅ 已验证 | 场景引用资源加载机制 |
| [serialize-reference-usage.md](../data/serialize-reference-usage.md) | #unity #csharp #serialization #experience | ✅ 已验证 | SerializeReference 多态序列化 |
| [sdf-signed-distance-field.md](../data/sdf-signed-distance-field.md) | #graphics #knowledge #sdf | 📘 有效 | SDF（有向距离场）知识 |
| [search-api-services.md](../data/search-api-services.md) | #tools #knowledge #search-api #serp | ✅ 已验证 | 搜索 API 服务对比 |
| [self-hosted-search-engines.md](../data/self-hosted-search-engines.md) | #tools #knowledge #search-engine #meilisearch #searxng | ✅ 已验证 | 自搭建搜索引擎技术 |
| [shader-effects-techniques.md](../data/shader-effects-techniques.md) | #shader #experience #effects | ✅ 已验证 | 具体特效实现相关经验 |
| [shader-optimization-hlsl.md](../data/shader-optimization-hlsl.md) | #shader #experience #hlsl #performance | ✅ 已验证 | Shader 性能优化相关经验 |
| [shader-variants-compile.md](../data/shader-variants-compile.md) | #shader #experience #hlsl #shader-variants | ✅ 已验证 | HLSL 着色器语言相关经验 |
| [srp-batcher-optimization.md](../data/srp-batcher-optimization.md) | #unity #srp-batcher #performance #experience | ✅ 已验证 | SRP Batcher 场景优化要点 |
| [srp-batcher-parameter-overhead.md](../data/srp-batcher-parameter-overhead.md) | #unity #srp-batcher #performance #experience | ✅ 已验证 | SRP Batcher 参数开销分析 |
| [unity-ai-navigation.md](../data/unity-ai-navigation.md) | #unity #knowledge #nav-mesh #ai-navigation | 📘 有效 | Unity AI Navigation 知识 |
| [unity-animation-scripting-notes.md](../data/unity-animation-scripting-notes.md) | #unity #animation #csharp #performance #knowledge #root-motion | ✅ 已验证 | Unity 动画与脚本开发核心知识清单 |
| [unity-blendtree-audio-sync.md](../data/unity-blendtree-audio-sync.md) | #unity #knowledge #experience #animation #blend-tree #audio | ✅ 已验证 | Unity BlendTree 下动画驱动音效同步（脚步声等）常见方案汇总 |
| [unity-cross-project-compilation-check.md](../data/unity-cross-project-compilation-check.md) | #unity #editor #csharp #experience | ✅ 已验证 | Unity 跨项目功能迁移的编译验证经验 |
| [unity-dynamicres-foveated-conflict.md](../data/unity-dynamicres-foveated-conflict.md) | #unity #vr #bug #experience | ⚠️ 待验证 | Unity 动态分辨率与注视点渲染冲突 |
| [unity-editor-api.md](../data/unity-editor-api.md) | #unity #knowledge #editor #custom-editor | 📘 有效 | Unity Editor 开发知识 |
| [unity-framework-architecture.md](../data/unity-framework-architecture.md) | #unity #csharp #experience #architecture | ⚠️ 待验证 | Unity 中的 C# 脚本编程相关经验 |
| [unity-generic-animation-import-config.md](../data/unity-generic-animation-import-config.md) | #unity #animation #root-motion #experience | ⚠️ 待验证 | Unity Generic 动画导入配置完整流程：解决滑步、UI 消失与双重位移 |
| [unity-layer-vs-renderlayer.md](../data/unity-layer-vs-renderlayer.md) | #unity #experience #rendering | ✅ 已验证 | Unity 中 Layer 与 Render Layer 的核心区别与使用场景 |
| [unity-material-renderer.md](../data/unity-material-renderer.md) | #unity #knowledge #rendering #material | 📘 有效 | Unity 渲染相关知识 |
| [unity-performance-ecs-culling.md](../data/unity-performance-ecs-culling.md) | #unity #experience #performance #ecs #culling | ⚠️ 待验证（需根据 Unity 版本和 DOTS 版本调整） | Unity 性能优化相关经验 |
| [unity-physics-system.md](../data/unity-physics-system.md) | #unity #knowledge #physics #collider #raycast | 📘 有效 | Unity 物理系统知识 |
| [unity-shader-variants-tool.md](../data/unity-shader-variants-tool.md) | #unity #shader #experience #shader-variants #editor | ✅ 已验证 | Unity 中 Shader 相关经验 |
| [urp-grabpass-alternative.md](../data/urp-grabpass-alternative.md) | #shader #unity #experience #urp #srp-batcher #renderer-feature | ✅ 已验证 | URP 中 GrabPass 替代方案 (GrabColor RenderFeature) {#grab-color-renderfeature} |
| [urp-skybox-notes.md](../data/urp-skybox-notes.md) | #unity #urp #shader #skybox #experience | ✅ 已验证 | URP SkyBox 注意事项 |
| [urp-renderer-feature-guide.md](../data/urp-renderer-feature-guide.md) | #shader #unity #experience #urp #srp-batcher #renderer-feature | ✅ 已验证 | URP Renderer Feature 开发要点 |
| [urp-renderfeature-runtime-toggle.md](../data/urp-renderfeature-runtime-toggle.md) | #shader #unity #experience #urp #srp-batcher #renderer-feature | ✅ 已验证 | RenderFeature 运行时开关控制 {#renderfeature-toggler} |
| [urp-srp-architecture.md](../data/urp-srp-architecture.md) | #unity #graphics #knowledge #urp #srp | 📘 有效 | URP / SRP 知识 |
| [vera-kt-dog-identity.md](../data/vera-kt-dog-identity.md) | #social #reference #vera #identity | 📘 有效 | 薇拉的身份设定 |
| [vitepress-architecture-deep-dive.md](../data/vitepress-architecture-deep-dive.md) | #web #vitepress #architecture #reference | 📘 有效 | 阿卡西记录 Web 项目架构深度解析 |
| [vitepress-dynamic-sidebar-index.md](../data/vitepress-dynamic-sidebar-index.md) | #tools #web #experience #vitepress | ✅ 已验证 | VitePress 动态侧边栏标签 + 分类索引页自动生成 |
| [vitepress-emoji-to-svg-icon.md](../data/vitepress-emoji-to-svg-icon.md) | #tools #web #experience #vitepress | ✅ 已验证 | 全站 Emoji 替换为 SVG 图标的完整流程 {#emoji-to-svg} |
| [vitepress-frontmatter-attrs-crash.md](../data/vitepress-frontmatter-attrs-crash.md) | #vitepress #bug #experience #web | ✅ 已验证 | VitePress 构建失败：markdown-it-attrs 与 Frontmatter 冲突 |
| [vitepress-sidebar-highlight-padding.md](../data/vitepress-sidebar-highlight-padding.md) | #tools #web #experience #vitepress | ✅ 已验证 | 侧边栏自定义高亮竖条与文字间距 {#sidebar-padding-left} |
| [vitepress-spa-fixed-pseudo-leak.md](../data/vitepress-spa-fixed-pseudo-leak.md) | #tools #web #experience #vitepress | ⚠️ 待验证 | VitePress SPA 路由中 position:fixed 伪元素泄漏 |
| [vitepress-vpfeature-icon-structure.md](../data/vitepress-vpfeature-icon-structure.md) | #tools #web #experience #vitepress | ✅ 已验证 | VitePress VPFeature 图标 HTML 结构（无 .icon 包裹层） {#vpfeature-icon-structure} |
| [vr-variant-collector-architecture.md](../data/vr-variant-collector-architecture.md) | #unity #shader #architecture #shader-variants | 📘 有效 | VR 变体收集器 - 架构与流程图解 |
| [vscode-copilot-skills-config.md](../data/vscode-copilot-skills-config.md) | #vscode #tools #experience #copilot | ✅ 已验证 | GitHub Copilot 使用相关经验 |
| [web-archive-mcp-blueprint.md](../data/web-archive-mcp-blueprint.md) | #mcp #python #playwright #architecture #web #tools | ✅ 已验证 | Web Archive MCP — 实现蓝图 |
| [windows-system-path-missing-app-detection-failure.md](../data/windows-system-path-missing-app-detection-failure.md) | #vscode #tools #experience #claude-code #git #bug | ✅ 已验证 | Windows 系统 PATH 缺失关键目录导致工具检测失败（以 Claude Code 为案例） |
| [pyinstaller-windows-exe-packaging.md](../data/pyinstaller-windows-exe-packaging.md) | #python #tools #experience #cross-platform | ✅ 已验证 | PyInstaller 打包 Python 为 Windows EXE 完整指南 |
| [python-docx-emoji-font-solution.md](../data/python-docx-emoji-font-solution.md) | #python #docx #experience #font #unicode | ✅ 已验证 | python-docx Emoji 显示问题解决方案（w:hAnsi 字体属性） |
| [3dsmax-skin-normal-fbx-export.md](../data/3dsmax-skin-normal-fbx-export.md) | #unity #3dsmax #fbx #experience #troubleshooting | ⚠️ 待验证 | 3ds Max 蒙皮后法线异常问题调查（待美术验证） |
| [claude-mem-smart-tools-windows-fix.md](../data/claude-mem-smart-tools-windows-fix.md) | #tools #windows #mcp #experience #bug | ✅ 已验证 | ClaudeMem MCP 工具修复（Smart工具 + Memory工具 inputSchema） |
| [test-workflow-verification.md](../data/test-workflow-verification.md) | #测试 #workflow | ✅ 已验证 | 阿卡西记录工作流测试（git push 验证） |

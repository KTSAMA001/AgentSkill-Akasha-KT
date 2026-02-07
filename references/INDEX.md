# 索引

## 参考文档

| 文档 | 路径 | 用途 |
|------|------|------|
| **查找流程** | [workflows/search.md](./workflows/search.md) | 检索记录、网络搜索 |
| **记录流程** | [workflows/record.md](./workflows/record.md) | 记录经验/知识 |
| **验证流程** | [workflows/validate.md](./workflows/validate.md) | 修正、废弃记录 |
| 使用示例 | [EXAMPLES.md](./EXAMPLES.md) | 参考用法 |
| 经验模板 | [templates/experience-template.md](./templates/experience-template.md) | 记录经验 |
| 知识模板 | [templates/knowledge-template.md](./templates/knowledge-template.md) | 记录知识 |
| 验证报告 | [reports/validation-report-20260205.md](./reports/validation-report-20260205.md) | 内容审计记录 |

---

## 标签概览

> 新增记录时优先复用已有标签，保持一致性。

`#3d` `#agent-skills` `#ai` `#ai-navigation` `#akasha` `#animation` `#anti-bot` `#architecture` `#arknights` `#astrbot` `#audio` `#behavior-designer` `#bilibili` `#blend-tree` `#brdf` `#bug` `#cicd` `#claude-code` `#collider` `#color-banding` `#color-space` `#compute-shader` `#conventional-commits` `#cook-torrance` `#copilot` `#credential` `#csharp` `#culling` `#custom-editor` `#cyberpunk` `#design` `#dither` `#docker` `#draw-call` `#ecs` `#editor` `#effect-system` `#effects` `#experience` `#gamma` `#git` `#github-actions` `#gpgpu` `#graphics` `#hdr` `#hlsl` `#idea` `#identity` `#knowledge` `#ktsama` `#linear` `#material` `#mcp` `#meilisearch` `#nav-mesh` `#npr` `#pat` `#pbr` `#performance` `#physics` `#playwright` `#post-processing` `#python` `#raycast` `#react` `#reference` `#renderer-feature` `#rendering` `#rendering-pipeline` `#scriptable-object` `#sdf` `#search-api` `#search-engine` `#searxng` `#selenium` `#serp` `#shader` `#shader-variants` `#smart-furniture` `#social` `#srp` `#srp-batcher` `#tools` `#ui` `#unity` `#urp` `#vera` `#vitepress` `#vscode` `#web`

---

## 文件清单

| 文件 | 标签 | 状态 | 简述 |
|------|------|------|------|
| [agent-skills-spec.md](../data/agent-skills-spec.md) | ：#ai #knowledge #agent-skills |  | Agent Skills 规范 |
| [akasha-visualization-web.md](../data/akasha-visualization-web.md) | ：#tools #web #reference #akasha | ：📘 有效 | 阿卡西记录可视化网站 |
| [arknights-ui-industrial-style.md](../data/arknights-ui-industrial-style.md) | ：#design #knowledge #arknights #ui | ：📘 有效 | 明日方舟工业风 UI：网点、网格、切角、噪点等视觉元素总结 |
| [astrbot-mcp-integration.md](../data/astrbot-mcp-integration.md) | ：#ai #experience #mcp #astrbot | ：✅ 已验证 | AstrBot 集成 MCP 服务经验 |
| [astrbot-messages-param-error.md](../data/astrbot-messages-param-error.md) | ：#ai #experience #astrbot #bug | ：⚠️ 部分解决（v4.13.2 仍有报告） | AstrBot "messages 参数非法" 错误 |
| [behavior-designer-api.md](../data/behavior-designer-api.md) | ：#unity #knowledge #behavior-designer #ai | ：📘 有效 | Behavior Designer 行为树插件的技术规范、API 和原理 |
| [cicd-vitepress-deploy.md](../data/cicd-vitepress-deploy.md) | ：#tools #experience #cicd #vitepress #github-actions | ：✅ 已验证 | 持续集成/持续部署相关经验 |
| [claude-code-guide.md](../data/claude-code-guide.md) | ：#ai #tools #reference #claude-code | ：✅ 已验证 | Anthropic Claude Code AI 编程助手相关经验 |
| [color-banding-dither.md](../data/color-banding-dither.md) | ：#graphics #knowledge #color-banding #dither #hdr | ：📘 有效 | 色带（Color Banding）与抖动（Dithering）知识 |
| [color-space-gamma-linear.md](../data/color-space-gamma-linear.md) | ：#graphics #knowledge #color-space #gamma #linear |  | 色彩空间知识 |
| [compute-shader-gpu-parallel.md](../data/compute-shader-gpu-parallel.md) | ：#graphics #shader #knowledge #compute-shader #gpgpu | ：📘 有效 | GPU 通用计算 (GPGPU) 相关原理与概念 |
| [effect-system-code-review.md](../data/effect-system-code-review.md) | ：#unity #architecture #scriptable-object #effect-system | ：✅ 已验证 | EffectSystem 效果系统 - 代码审查与架构分析 |
| [git-commit-conventions.md](../data/git-commit-conventions.md) | ：#git #reference #conventional-commits | ：✅ 已验证 | Git 团队协作工作流相关经验 |
| [git-troubleshooting.md](../data/git-troubleshooting.md) | ：#git #experience #pat #docker #credential | ：⚠️ 解决方案已验证，根因待查 | Git 常见问题解决相关经验 |
| [gpu-grass-large-scale-rendering.md](../data/gpu-grass-large-scale-rendering.md) | ：#shader #unity #experience #compute-shader #urp #performance | ：✅ 已验证 | 大规模渲染 (Large-Scale Rendering) 相关经验 |
| [hlsl-syntax-semantics.md](../data/hlsl-syntax-semantics.md) | ：#graphics #shader #knowledge #hlsl |  | Unity Shader / HLSL 基础知识 |
| [idea-3d-girl-smart-furniture.md](../data/idea-3d-girl-smart-furniture.md) | ：#idea #smart-furniture #3d | ：💡 灵感记录 | 3D美少女智能家具创业想法 |
| [ktsama-bilibili-profile.md](../data/ktsama-bilibili-profile.md) | ：#social #reference #ktsama #bilibili | ：📚 有效 | [KTSAMA的B站主页] |
| [mcp-protocol-agent-dev.md](../data/mcp-protocol-agent-dev.md) | ：#ai #experience #mcp | ：✅ 已验证 | MCP 协议与 Agent 服务开发经验 |
| [monster-siren-web-analysis.md](../data/monster-siren-web-analysis.md) | ：#web #design #knowledge #arknights #react #cyberpunk | ：📘 有效 | 塞壬唱片官网 (Monster Siren) 深度技术与设计分析 |
| [npr-rendering-outline.md](../data/npr-rendering-outline.md) | ：#shader #unity #experience #npr #renderer-feature #post-processing | ：✅ 已验证 | 非真实感渲染 (Non-Photorealistic Rendering) 相关经验 |
| [pbr-brdf-theory.md](../data/pbr-brdf-theory.md) | ：#graphics #knowledge #pbr #brdf #cook-torrance | ：📘 有效 | 基于物理的渲染（Physically Based Rendering）相关原理与概念 |
| [pbr-custom-shader-urp.md](../data/pbr-custom-shader-urp.md) | ：#shader #unity #experience #pbr #urp #hlsl | ：✅ 已验证 | 基于物理的渲染 (Physically Based Rendering) 相关经验 |
| [python-web-scraping-antibot.md](../data/python-web-scraping-antibot.md) | ：#python #experience #playwright #selenium #anti-bot | ：✅ 已验证 | 网页抓取与反爬虫绕过 |
| [rendering-pipeline-overview.md](../data/rendering-pipeline-overview.md) | ：#graphics #knowledge #rendering-pipeline #draw-call |  | 渲染管线知识 |
| [sdf-signed-distance-field.md](../data/sdf-signed-distance-field.md) | ：#graphics #knowledge #sdf |  | 📷 **图片资源**：本文图片引用自 [TaTa 仓库 SDF/img](https://github.com/KTSAMA001/TaTa/tree/master/SDF/img) |
| [search-api-services.md](../data/search-api-services.md) | ：#tools #knowledge #search-api #serp | ：✅ 已验证 | 搜索 API 服务对比 |
| [self-hosted-search-engines.md](../data/self-hosted-search-engines.md) | ：#tools #knowledge #search-engine #meilisearch #searxng | ：✅ 已验证 | 自搭建搜索引擎技术 |
| [shader-effects-techniques.md](../data/shader-effects-techniques.md) | ：#shader #experience #effects | ：✅ 已验证 | 具体特效实现相关经验 |
| [shader-optimization-hlsl.md](../data/shader-optimization-hlsl.md) | ：#shader #experience #hlsl #performance | ：✅ 已验证 | Shader 性能优化相关经验 |
| [shader-variants-compile.md](../data/shader-variants-compile.md) | ：#shader #experience #hlsl #shader-variants | ：✅ 已验证 | HLSL 着色器语言相关经验 |
| [unity-ai-navigation.md](../data/unity-ai-navigation.md) | ：#unity #knowledge #nav-mesh #ai-navigation | ：📘 有效 | Unity AI Navigation 知识 |
| [unity-blendtree-audio-sync.md](../data/unity-blendtree-audio-sync.md) | ：#unity #knowledge #animation #blend-tree #audio | ：📘 有效 | Unity BlendTree 下动画驱动音效同步（脚步声等）常见方案汇总 |
| [unity-editor-api.md](../data/unity-editor-api.md) | ：#unity #knowledge #editor #custom-editor | ：📘 有效 | Unity Editor 开发知识 |
| [unity-editor-extension.md](../data/unity-editor-extension.md) | ：#unity #experience #editor #behavior-designer | ：✅ 已验证 | Unity Editor 扩展开发相关经验 |
| [unity-framework-architecture.md](../data/unity-framework-architecture.md) | ：#unity #csharp #experience #architecture |  | Unity 中的 C# 脚本编程相关经验 |
| [unity-layer-vs-renderlayer.md](../data/unity-layer-vs-renderlayer.md) | ：#unity #experience #rendering | ：✅ 已验证 | Unity 其他无法归类的经验 |
| [unity-material-renderer.md](../data/unity-material-renderer.md) | ：#unity #knowledge #rendering #material | ：📘 有效 | Unity 渲染相关知识 |
| [unity-performance-ecs-culling.md](../data/unity-performance-ecs-culling.md) | ：#unity #experience #performance #ecs #culling | ：⚠️ 待验证（需根据 Unity 版本和 DOTS 版本调整） | Unity 性能优化相关经验 |
| [unity-physics-system.md](../data/unity-physics-system.md) | ：#unity #knowledge #physics #collider #raycast |  | Unity 物理系统知识 |
| [unity-shader-variants-tool.md](../data/unity-shader-variants-tool.md) | ：#unity #shader #experience #shader-variants #editor | ：✅ 已验证 | Unity 中 Shader 相关经验 |
| [urp-shader-practices.md](../data/urp-shader-practices.md) | ：#shader #unity #experience #urp #srp-batcher #renderer-feature | ：✅ 已验证 | Universal Render Pipeline 相关经验 |
| [urp-srp-architecture.md](../data/urp-srp-architecture.md) | ：#unity #graphics #knowledge #urp #srp |  | URP / SRP 知识 |
| [vera-kt-dog-identity.md](../data/vera-kt-dog-identity.md) | ：#social #reference #vera #identity | ：📚 有效 | 薇拉的身份设定 |
| [vitepress-site-dev.md](../data/vitepress-site-dev.md) | ：#tools #web #experience #vitepress | ：✅ 已验证 | VitePress 静态站点生成器相关经验 |
| [vr-variant-collector-architecture.md](../data/vr-variant-collector-architecture.md) | ：#unity #shader #architecture #shader-variants |  | 请在 VS Code 中点击右上角的 **"Open Preview to the Side"** (快捷键 `Ctrl+K V`) 查看图形化渲染效果。 |
| [vscode-copilot-skills-config.md](../data/vscode-copilot-skills-config.md) | ：#vscode #tools #experience #copilot | ：✅ 已验证 | GitHub Copilot 使用相关经验 |


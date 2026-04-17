# 索引

## 参考文档

| 文档 | 路径 | 用途 |
|------|------|------|
| **查找流程** | [workflows/search.md](./workflows/search.md) | 检索记录、网络搜索 |
| **记录流程** | [workflows/record.md](./workflows/record.md) | 记录经验/知识 |
| **验证流程** | [workflows/validate.md](./workflows/validate.md) | 修正、废弃记录 |
| **治理流程** | [workflows/governance.md](./workflows/governance.md) | 修改模板、workflow、schema 与 Web 契约 |
| 使用示例 | [EXAMPLES.md](./EXAMPLES.md) | 参考用法 |
| 记录模板 | [templates/record-template.md](./templates/record-template.md) | 通用记录模板 |
| 脚本说明 | [scripts/README.md](./scripts/README.md) | 校验脚本与索引脚本使用说明 |
| **标签注册表** | [tag-registry.md](./tag-registry.md) | 标签元数据（显示名、图标） |

---

## 标签概览

> 完整元数据（显示名、图标）见 [tag-registry.md](./tag-registry.md)。新增标签时需同时注册。

`#3dsmax` `#agent-skills` `#ai` `#ai-navigation` `#akasha` `#animation` `#animation-retarget` `#anti-bot` `#architecture` `#arknights` `#astc` `#astrbot` `#audio` `#behavior-designer` `#bilibili` `#blend-tree` `#brdf` `#bug` `#cicd` `#claude-code` `#collider` `#color-banding` `#color-space` `#compute-shader` `#conventional-commits` `#cook-torrance` `#copilot` `#credential` `#cross-platform` `#csharp` `#culling` `#custom-editor` `#cyberpunk` `#deployment` `#design` `#dither` `#docker` `#docx` `#dotnet` `#draw-call` `#ecs` `#editor` `#effect-system` `#effects` `#excel` `#experience` `#fbx` `#font` `#gamma` `#git` `#github-actions` `#gpgpu` `#graphics` `#hdr` `#hlsl` `#hook` `#idea` `#identity` `#ik` `#knowledge` `#ktsama` `#linear` `#macos` `#markdown` `#material` `#math` `#mcp` `#meilisearch` `#memory` `#mvvm` `#nav-mesh` `#npr` `#openclaw` `#pat` `#pbr` `#performance` `#physics` `#playwright` `#post-processing` `#python` `#raycast` `#react` `#reference` `#renderdoc` `#renderer-feature` `#rendering` `#rendering-pipeline` `#retarget-pro` `#root-motion` `#scene` `#scriptable-object` `#sdf` `#search-api` `#search-engine` `#searxng` `#selenium` `#serialization` `#serp` `#shader` `#shader-variants` `#skybox` `#smart-furniture` `#social` `#srp` `#srp-batcher` `#texture` `#tools` `#troubleshooting` `#ui` `#unicode` `#unity` `#urp` `#vera` `#vitepress` `#vr` `#vscode` `#web` `#windows` `#yaml` `#zhihu`

---

## 文件清单

| 文件 | 标签 | 状态 | 简述 |
|------|------|------|------|
| [3dsmax-skin-normal-fbx-export.md](../data/3dsmax-skin-normal-fbx-export.md) | #unity #3dsmax #fbx #experience #troubleshooting | ⚠️ 待验证 | 美术在做模型资产时法线正常（硬边效果），但动画绑定后法线被打乱。通过网络搜索汇总了可能的原因和解决方案，**待美术验证后更新状态**。 |
| [agent-skill-record-test.md](../data/agent-skill-record-test.md) | #agent-skills #experience #akasha | ⚠️ 待验证 | 本记录仅用于验证子 Agent 是否会按阿卡西 record 流程完成写入、索引同步与脚本校验，不可作为正式知识引用。 |
| [agent-skills-spec.md](../data/agent-skills-spec.md) | #ai #knowledge #agent-skills | 📘 有效 | Agent Skills 规范 |
| [akasha-semantic-search-architecture.md](../data/akasha-semantic-search-architecture.md) | #architecture #ai #mcp #akasha #search-engine #python | 💡 构想中 | 为阿卡西记录（Akasha-KT）设计基于向量模型的语义搜索架构，提升自然语言查询体验，实现从关键词匹配到语义理解的升级。 |
| [akasha-visualization-web.md](../data/akasha-visualization-web.md) | #tools #web #reference #akasha | 📘 有效 | 阿卡西记录可视化网站 |
| [amplify-shader-editor-architecture.md](../data/amplify-shader-editor-architecture.md) | #unity #shader #graphics #architecture #urp | ✅ 已验证 | Amplify Shader Editor 的核心不是单纯的节点编辑器，而是一套 `图模型 + 文本模板 + 代码片段收集器 + Shader 内嵌序列化协议`。它把节点图直接嵌入 `.shader` 文件尾部的 `/*ASEBEGIN ... ASEEND*/` 区块中，使 Shader 文件同时成为运行产物和可编辑源；生成阶段则由主节点发起，沿输入端口反向递归收集代码片段，再通过模板标签系统组装为完整 Shader。 |
| [animation-retarget-root-motion-algorithm.md](../data/animation-retarget-root-motion-algorithm.md) | #unity #animation #math #root-motion #animation-retarget #knowledge | 📘 有效 | 系统解析了不同比例模型复用同一套动画且不产生滑步（Foot Sliding）的核心算法与数学原理，涵盖从资源分发机制到根运动（Root Motion）的缩放计算，以及四足动物的 Stride Warping 适配方案和 Unity 底层实现机制。 |
| [animation-retarget-technology-unity.md](../data/animation-retarget-technology-unity.md) | #unity #animation #animation-retarget #knowledge #ik | 📘 有效 | 系统分析了 Animation Retargeting（动画重定向）技术的基本原理、骨骼映射方案以及在 Unity 引擎中的实际应用经验，包括遇到的问题和解决方法。作者有 Havok 引擎源码阅读和自研引擎实现经验。 |
| [arknights-ui-industrial-style.md](../data/arknights-ui-industrial-style.md) | #design #knowledge #arknights #ui | 📘 有效 | 明日方舟工业风 UI：网点、网格、切角、噪点等视觉元素总结 |
| [ase-shader-bakery-integration.md](../data/ase-shader-bakery-integration.md) | #shader #unity #experience #urp #srp-batcher #renderer-feature | ✅ 已验证 | ASE Shader 架构与 Bakery 光照集成最佳实践 |
| [astc-compression-formula.md](../data/astc-compression-formula.md) | #unity #texture #memory #astc #experience | ✅ 已验证 | ASTC 压缩格式的内存估算公式，用于快速计算纹理占用内存。 |
| [astrbot-mcp-service-config.md](../data/astrbot-mcp-service-config.md) | #ai #experience #mcp #astrbot | ✅ 已验证 | AstrBot 集成 MCP 服务经验 |
| [astrbot-messages-param-error.md](../data/astrbot-messages-param-error.md) | #ai #experience #astrbot #bug | 🔄 待更新 | AstrBot "messages 参数非法" 错误 |
| [astrbot-plugin-file-upload-onebot.md](../data/astrbot-plugin-file-upload-onebot.md) | #ai #experience #mcp #astrbot | ✅ 已验证 | AstrBot 插件文件上传到QQ实现 |
| [astrbot-plugin-llm-request-interceptor.md](../data/astrbot-plugin-llm-request-interceptor.md) | #ai #experience #mcp #astrbot | ✅ 已验证 | AstrBot 插件自动触发函数（LLM 请求拦截） |
| [bd-log-throttle.md](../data/bd-log-throttle.md) | #unity #experience #editor #behavior-designer | ✅ 已验证 | BD 节点日志频率控制 {#bd-log-throttle} |
| [bd-showif-workaround.md](../data/bd-showif-workaround.md) | #unity #experience #editor #behavior-designer | ✅ 已验证 | BD 节点条件显示的替代方案 {#bd-showif-workaround} |
| [bd-tooltip-namespace-conflict.md](../data/bd-tooltip-namespace-conflict.md) | #unity #experience #editor #behavior-designer | ✅ 已验证 | BD 节点 Tooltip 命名空间冲突解决 {#bd-tooltip-namespace-conflict} |
| [behavior-designer-api.md](../data/behavior-designer-api.md) | #unity #knowledge #behavior-designer #ai | 📘 有效 | Behavior Designer 行为树插件的技术规范、API 和原理 |
| [browser-automation-search-mcp-dev.md](../data/browser-automation-search-mcp-dev.md) | #python #playwright #mcp #experience #web #tools | ⚠️ 待验证 | 开发浏览器自动化搜索工具，目标是替代智谱MCP的搜索功能。实现了基于 Playwright 的搜索功能，可打开浏览器、执行搜索并获取结果。MCP封装部分因Python版本问题暂停。 |
| [cbuffer-srp-batcher-mechanism.md](../data/cbuffer-srp-batcher-mechanism.md) | #shader #unity #experience #urp #srp-batcher #renderer-feature | ✅ 已验证 | CBUFFER 与 SRP Batcher 合批机制 |
| [cicd-vitepress-deploy.md](../data/cicd-vitepress-deploy.md) | #tools #experience #cicd #vitepress #github-actions | ✅ 已验证 | 持续集成/持续部署相关经验 |
| [claude-code-2-1-feature-inventory.md](../data/claude-code-2-1-feature-inventory.md) | #claude-code #reference #tools #ai | ✅ 已验证 | Claude Code 2.1.81 完整功能清单，涵盖 15 大能力域：交互模式、内置工具、多代理、会话管理、非交互/SDK 模式、Git 集成、MCP、Hooks、Plugin、Skill、IDE 集成、Memory、Chrome 集成、结构化输出、CLI 标志与环境变量。 |
| [claude-code-backend-models.md](../data/claude-code-backend-models.md) | #ai #tools #reference #claude-code | ✅ 已验证 | Claude Code 作为 Agent 框架接入多种模型 (LLM Gateway) |
| [claude-code-comprehensive-guide.md](../data/claude-code-comprehensive-guide.md) | #claude-code #tools #reference | ✅ 已验证 | Claude Code 是 Anthropic 推出的 AI 编程助手，支持终端 CLI、桌面应用、Web 浏览器、VS Code 和 JetBrains IDE 五大平台，提供 1M token 上下文窗口、多代理协调、插件系统、Hook 自动化等能力。 |
| [claude-code-config-dialog-settings.md](../data/claude-code-config-dialog-settings.md) | #claude-code #reference #tools | ✅ 已验证 | `/config` 命令打开的设置界面（存储于 `~/.claude.json`，**非** `settings.json`）中各配置项的作用说明。与 `settings.json`（权限、hooks、环境变量等）是两套独立的配置系统。 |
| [claude-code-fork-session.md](../data/claude-code-fork-session.md) | #ai #tools #reference #claude-code | ✅ 已验证 | Claude Code Fork 会话功能 (Branching Conversation) |
| [claude-code-latest-features-2026.md](../data/claude-code-latest-features-2026.md) | #ai #tools #reference #claude-code | ✅ 已验证 | Claude Code 最新功能 (2026-03) |
| [claude-code-skill-hook-trigger-boost.md](../data/claude-code-skill-hook-trigger-boost.md) | #claude-code #agent-skills #hook #experience | ✅ 已验证 | Claude Code Skill 的主动式/被动式触发模式由 frontmatter 控制，但主动式 skill 自动触发率仅 ~20%。通过 `UserPromptSubmit` hook 注入 forced eval 指令可提升至 ~84%。操作级别的行为区分（如查询自动/记录询问）需通过 SKILL.md 内部规则实现，frontmatter 无法做到。 |
| [claude-code-slash-commands.md](../data/claude-code-slash-commands.md) | #ai #tools #reference #claude-code | ✅ 已验证 | Claude Code 完整斜杠命令列表 (Slash Commands) |
| [claude-code-source-architecture.md](../data/claude-code-source-architecture.md) | #claude-code #mcp #architecture #agent-skills | ✅ 已验证 | 对 Claude Code 官方 CLI 工具的完整源码进行逆向分析，揭示其系统提示词设计、Agent 子系统、Tool 工具框架、查询循环与上下文管理、权限管线等核心架构。 |
| [claude-mem-smart-tools-windows-fix.md](../data/claude-mem-smart-tools-windows-fix.md) | #tools #windows #mcp #experience #bug #cross-platform | ✅ 已验证 | ClaudeMem 插件 v12.1.5 的 MCP server 在 Windows 上存在两个 Bug：语法错误导致整个 MCP server 无法启动，以及 Smart 工具的 tree-sitter 调用方式与 CLI 0.26.7 不兼容。两者均需手动修复，且 `claude plugins update` 后会被覆盖。 |
| [color-banding-dither.md](../data/color-banding-dither.md) | #graphics #knowledge #color-banding #dither #hdr | 📘 有效 | 色带（Color Banding）与抖动（Dithering）知识 |
| [color-space-gamma-linear.md](../data/color-space-gamma-linear.md) | #graphics #knowledge #color-space #gamma #linear | 📘 有效 | 色彩空间知识 |
| [compute-shader-gpu-parallel.md](../data/compute-shader-gpu-parallel.md) | #graphics #shader #knowledge #compute-shader #gpgpu | 📘 有效 | GPU 通用计算 (GPGPU) 相关原理与概念 |
| [copilot-claude-code-mcp-setup.md](../data/copilot-claude-code-mcp-setup.md) | #copilot #claude-code #mcp #vscode #ai #experience | ⚠️ 待验证 | 通过 `@steipete/claude-code-mcp` 将 Claude Code CLI 包装为 MCP server，注册到 VS Code 用户级 `mcp.json`，使 GitHub Copilot（Agent 模式）在执行任务时可直接调用 `claude_code` 工具，将复杂子任务委派给 Claude Code 完成。 |
| [docker-container-git-auth-persist.md](../data/docker-container-git-auth-persist.md) | #git #experience #docker #credential #troubleshooting | ✅ 已验证 | Docker 容器重建后 Git 认证持久化配置 {#docker-git-auth-persist} |
| [docker-git-credential-persist.md](../data/docker-git-credential-persist.md) | #git #experience #pat #docker #credential | ✅ 已验证 | Docker 容器内 Git PAT 凭据持久化配置 {#docker-git-credential} |
| [docker-vs-native-deployment-file-access.md](../data/docker-vs-native-deployment-file-access.md) | #docker #deployment #tools #experience #ai | ✅ 已验证 | 针对"让 bot 操作电脑文件"这一需求，原生部署是明显更优的选择。Docker 的容器隔离在这一场景下是累赘而非优势。 |
| [dotnet-cross-platform-compile-verify.md](../data/dotnet-cross-platform-compile-verify.md) | #csharp #dotnet #tools #experience | ✅ 已验证 | 验证在 Linux arm64 容器中部署的 .NET SDK 能否成功编译 macOS arm64 跨平台应用。 |
| [effect-system-code-review.md](../data/effect-system-code-review.md) | #unity #architecture #scriptable-object #effect-system | ✅ 已验证 | EffectSystem 效果系统 - 代码审查与架构分析 |
| [endfield-rendering-study.md](../data/endfield-rendering-study.md) | #rendering #shader #pbr #knowledge #zhihu | 📘 有效 | 系统分析了《终末地》项目的角色渲染流程，以脸部渲染为核心深入解读 shader 效果实现，涵盖渲染管线整体梳理、角色渲染细节、特殊效果说明等。附有大量渲染对比图和 AI 绘制的流程图，原图在 GitHub 上可查。 |
| [excel-id-enum-generator.md](../data/excel-id-enum-generator.md) | #unity #tools #excel #experience | ✅ 已验证 | 将 Excel 表格中的数据 ID 一键导出为 C# 枚举，避免在预制体上手动填写 ID 导致的资源冗余和查找困难。 |
| [git-commit-conventions.md](../data/git-commit-conventions.md) | #git #reference #conventional-commits | ✅ 已验证 | Git 团队协作工作流相关经验 |
| [git-config-in-repo.md](../data/git-config-in-repo.md) | #git #docker #experience #credential | ✅ 已验证 | Docker 容器重建后，如果 Git 配置只写在 `~/.gitconfig`，会随容器销毁丢失。将配置写入仓库内 `.git/config` 可以让配置和挂载卷一起持久化。 |
| [git-filter-repo-rewrite-history.md](../data/git-filter-repo-rewrite-history.md) | #git #experience #pat #docker #credential | ✅ 已验证 | 使用 git-filter-repo 重写提交历史（清除敏感信息） |
| [git-https-fail-switch-ssh.md](../data/git-https-fail-switch-ssh.md) | #git #experience #pat #docker #credential | ✅ 已验证 | 已存在仓库通过 HTTPS 拉取持续失败，但改为 SSH 远程地址后可立即恢复。该类问题通常与网络链路、代理干扰或认证通道稳定性有关，而不是仓库内容本身损坏。 |
| [git-merge-3way-file-not-in-base.md](../data/git-merge-3way-file-not-in-base.md) | #git #experience | ⚠️ 待验证 | 当一个文件在合并基点（merge base）上**不存在**时，即使当前分支曾经添加后又 `git rm` 删除了该文件，合并到目标分支时 **不会** 导致目标分支的同名文件被删除。Git 三方合并只比较最终快照与合并基点的差异，不追踪中间历史。 |
| [git-object-corrupt-repair.md](../data/git-object-corrupt-repair.md) | #git #docker #experience #troubleshooting #credential | 🔄 待更新 | 当 Git loose object 损坏时，可以从正常仓库重新写回缺失对象完成修复；但本案例的真实触发根因尚未确认，因此该记录仍需继续更新。 |
| [gpu-grass-large-scale-rendering.md](../data/gpu-grass-large-scale-rendering.md) | #shader #unity #experience #compute-shader #urp #performance | ✅ 已验证 | 大规模渲染 (Large-Scale Rendering) 相关经验 |
| [hlsl-syntax-semantics.md](../data/hlsl-syntax-semantics.md) | #graphics #shader #knowledge #hlsl | 📘 有效 | Unity Shader / HLSL 基础知识 |
| [idea-3d-girl-smart-furniture.md](../data/idea-3d-girl-smart-furniture.md) | #design #idea #smart-furniture | 💡 构想中 | 3D智能家具创意 |
| [img-svg-css-color-filter.md](../data/img-svg-css-color-filter.md) | #tools #web #experience #vitepress | ✅ 已验证 | img 标签的 SVG 无法继承 CSS color，需用 filter 着色 {#img-svg-color-filter} |
| [kinemation-retarget-pro-plugin.md](../data/kinemation-retarget-pro-plugin.md) | #unity #animation #knowledge #retarget-pro #animation-retarget #ik #scriptable-object | ✅ 已验证 | KINEMATION Retarget Pro 是 Unity 高级动画重定向插件，可将一个角色（Source）的动画无缝迁移到另一个角色（Target），质量高于 Unity 内置 Humanoid 系统。支持编辑器离线烘焙和运行时实时重定向两种模式。仅支持将 Humanoid/Generic 动画重定向到 **Generic** 角色，暂不支持烘焙 Humanoid 格式输出。 |
| [kira-framework-analysis.md](../data/kira-framework-analysis.md) | #unity #csharp #architecture #ui #mvvm | 📘 有效 | KiraFramework 是一个以 UI 管理为核心的 Unity 游戏开发框架，采用配置驱动的代码生成系统，提供类型安全的事件通信和层级化 UI 管理。适合中小型 RPG/卡牌/策略类游戏，但 MVVM View 层尚未完成。 |
| [ktsama-bilibili-profile.md](../data/ktsama-bilibili-profile.md) | #design #reference #social #ktsama #bilibili | 📘 有效 | [KTSAMA的B站主页] |
| [li-comm-polling-to-event-driven.md](../data/li-comm-polling-to-event-driven.md) | #docker #architecture #astrbot #openclaw | ✅ 已验证 | OpenClaw（璃）与 AstrBot（星璃）之间的双璃通信经过三次架构迭代：v3.2 高频轮询 → v3.3 事件驱动 → v4.0 纯 API 直连。最终方案零文件队列、零 cron 轮询、零 watchdog，双向通过 HTTP API 实时投递。 |
| [llm-api-image-url-deserialize-error.md](../data/llm-api-image-url-deserialize-error.md) | #ai #experience #astrbot #bug | ✅ 已验证 | 在 AstrBot 中使用某些 LLM 模型时，触发 `All chat models failed: BadRequestError: Error code: 400`，错误信息显示在 `messages[11]` 位置遇到 `image_url` 字段，但 API 期望的是 `text` 字段。 |
| [macos-git-osxkeychain-path.md](../data/macos-git-osxkeychain-path.md) | #macos #git #experience #pat #credential | ✅ 已验证 | Homebrew 安装的 Git 在 macOS 上可能找不到 `git-credential-osxkeychain`，原因不是功能缺失，而是 helper 不在 PATH。将 `credential.helper` 配置为完整可执行路径即可恢复认证。 |
| [material-unified-management.md](../data/material-unified-management.md) | #unity #shader #material #experience | ✅ 已验证 | 多种 Shader 之间的宏开关和参数切换需要统一管理，否则会导致配置混乱。 |
| [mcp-protocol-agent-dev.md](../data/mcp-protocol-agent-dev.md) | #ai #experience #mcp | ✅ 已验证 | MCP 协议与 Agent 服务开发经验 |
| [md-to-word-converter-implementation.md](../data/md-to-word-converter-implementation.md) | #python #tools #experience #docx #markdown | ✅ 已验证 | 基于 Python 的 Markdown 转 Word (.docx) 文档转换器，支持代码语法高亮、Mermaid/PlantUML 图表渲染、表格转换、图片嵌入等功能。核心使用 `python-docx` + `markdown` + `Pygments` + `BeautifulSoup4` 技术栈。 |
| [modified-renderdoc-wuwa-capture.md](../data/modified-renderdoc-wuwa-capture.md) | #graphics #windows #reference #renderdoc #anti-bot #hook #rendering #zhihu | ⚠️ 待验证 | 通过修改 RenderDoc 源码中的所有特征字符串（`renderdoc` → `rendertest`），绕过《鸣潮》对 RenderDoc 的检测（包括文件特征码扫描和 CrashSight 检测），实现在 PC 端使用 RenderDoc 进行截帧和 Shader 分析。 |
| [monster-siren-web-analysis.md](../data/monster-siren-web-analysis.md) | #web #design #knowledge #arknights #react #cyberpunk | 📘 有效 | 塞壬唱片官网 (Monster Siren) 深度技术与设计分析 |
| [msaa-texture-display-optimization.md](../data/msaa-texture-display-optimization.md) | #unity #graphics #rendering #texture #performance #knowledge | ✅ 已验证 | MSAA（多重采样抗锯齿）只对**多边形（Mesh）边缘**产生抗锯齿效果，**不会**对纹理（Texture）的 Alpha 镂空边缘生效。因此，纹理应尽量与网格边界对齐以获得 MSAA 的抗锯齿效果；若无法对齐，只能通过 MipMap 来缓解锯齿（代价是增加内存占用）。 |
| [npr-rendering-outline.md](../data/npr-rendering-outline.md) | #shader #unity #experience #npr #renderer-feature #post-processing | ✅ 已验证 | 非真实感渲染 (Non-Photorealistic Rendering) 相关经验 |
| [pbr-brdf-theory.md](../data/pbr-brdf-theory.md) | #graphics #knowledge #pbr #brdf #cook-torrance | 📘 有效 | 基于物理的渲染（Physically Based Rendering）相关原理与概念 |
| [pbr-custom-shader-urp.md](../data/pbr-custom-shader-urp.md) | #shader #unity #experience #pbr #urp #hlsl | ✅ 已验证 | 基于物理的渲染 (Physically Based Rendering) 相关经验 |
| [physics-update-timing.md](../data/physics-update-timing.md) | #unity #physics #experience | ✅ 已验证 | 需要物理碰撞/触发检测的物体，应在 FixedUpdate 而非 LateUpdate 中更新位置，否则检测位置是上一帧的位置。 |
| [prefab-variant-generator-v4-toolkit.md](../data/prefab-variant-generator-v4-toolkit.md) | #unity #tools #architecture #custom-editor | ✅ 已验证 | `PrefabVariantGeneratorV4` 是 Unity Editor 下的 DAG 节点式 Prefab 批处理工具。它以 `PipelineGraphData` 作为配置资产，按拓扑顺序执行各 Stage，支持分支派生、路径注入与多终端批量产物生成。 |
| [pyinstaller-windows-exe-packaging.md](../data/pyinstaller-windows-exe-packaging.md) | #python #tools #experience #cross-platform | ✅ 已验证 | 在 Linux 环境下为 Windows 打包 Python 程序的踩坑记录，包含 bat 脚本生成、资源文件打包、路径兼容等关键问题。 |
| [python-docx-emoji-font-solution.md](../data/python-docx-emoji-font-solution.md) | #python #docx #experience #font #unicode | ✅ 已验证 | 解决 python-docx 生成的 Word 文档中 emoji 显示为方框或方框带问号的问题。根因是 `run.font.name` 只设置 Word XML 的 `w:ascii` 属性，而 emoji 字符（Unicode 补充平面，code point > 0xFFFF）需要通过 `w:hAnsi` 属性指定字体才能正确渲染。 |
| [python-web-scraping-antibot.md](../data/python-web-scraping-antibot.md) | #python #experience #playwright #selenium #anti-bot | ✅ 已验证 | 网页抓取与反爬虫绕过 |
| [render-queue-design.md](../data/render-queue-design.md) | #unity #rendering #performance #experience | ✅ 已验证 | 多特效叠加时，固定渲染队列比动态距离排序更稳定可控，且能保证批次数量。 |
| [rendering-pipeline-overview.md](../data/rendering-pipeline-overview.md) | #graphics #knowledge #rendering-pipeline #draw-call | 📘 有效 | 渲染管线知识 |
| [safari-svg-favicon-compat.md](../data/safari-svg-favicon-compat.md) | #tools #web #experience #vitepress | ⚠️ 待验证 | Safari SVG Favicon 兼容性 |
| [scene-asset-loading.md](../data/scene-asset-loading.md) | #unity #performance #scene #experience | ✅ 已验证 | 不要在场景中提前引用后续游戏过程中才需要的资源，Unity 场景加载机制会在运行时加载场景中引用的全部资源。 |
| [sdf-signed-distance-field.md](../data/sdf-signed-distance-field.md) | #graphics #knowledge #sdf | 📘 有效 | SDF（有向距离场）知识 |
| [search-api-services.md](../data/search-api-services.md) | #tools #knowledge #search-api #serp | ✅ 已验证 | 搜索 API 服务对比 |
| [self-hosted-search-engines.md](../data/self-hosted-search-engines.md) | #tools #knowledge #search-engine #meilisearch #searxng | ✅ 已验证 | 自搭建搜索引擎技术 |
| [serialize-reference-usage.md](../data/serialize-reference-usage.md) | #unity #csharp #serialization #experience | ✅ 已验证 | 使用 `[SerializeReference]` 特性实现接口或抽象类的多态序列化，支持在 Inspector 中配置不同类型的实现。 |
| [shader-debug-alpha-srgb-encoding-pitfall.md](../data/shader-debug-alpha-srgb-encoding-pitfall.md) | #shader #urp #color-space #experience #graphics #unity | ✅ 已验证 | 在 Shader 中用 `return alpha` 调试纹理 A 通道时，屏幕取色器读到的值与纹理预览值不一致。这是因为 A 值被灌入了 RGB 通道输出，而 RGB 会被 sRGB Back Buffer 的硬件编码"提亮"。用 `pow(a, 2.2)` 预补偿在暗部会失效，因为 sRGB 编码函数在低值区使用的是线性段而非幂函数。此外，**DXT5/ASTC 纹理压缩**会改变实际 alpha 值，进一步加剧暗部数值偏差。 |
| [shader-effects-techniques.md](../data/shader-effects-techniques.md) | #shader #experience #effects | ✅ 已验证 | 具体特效实现相关经验 |
| [shader-normal-space-transformation.md](../data/shader-normal-space-transformation.md) | #graphics #shader #math #knowledge | 📘 有效 | 法线（Normal）是方向向量（co-vector），不能直接用模型矩阵变换，必须使用**逆转置矩阵**（inverse transpose）。位置和方向向量则直接使用模型矩阵或其逆矩阵。 |
| [shader-optimization-hlsl.md](../data/shader-optimization-hlsl.md) | #shader #experience #hlsl #performance | ✅ 已验证 | Shader 性能优化相关经验 |
| [shader-variants-compile.md](../data/shader-variants-compile.md) | #shader #experience #hlsl #shader-variants | ✅ 已验证 | HLSL 着色器语言相关经验 |
| [srp-batcher-optimization.md](../data/srp-batcher-optimization.md) | #unity #srp-batcher #performance #experience | ✅ 已验证 | SRP 管线下的场景优化建议，减少 DrawCall 和批次开销。 |
| [srp-batcher-parameter-overhead.md](../data/srp-batcher-parameter-overhead.md) | #unity #srp-batcher #performance #experience | ✅ 已验证 | 相同 Shader 不同材质的参数绑定开销分析，基于 RenderDoc 抓帧验证。 |
| [unity-ai-navigation.md](../data/unity-ai-navigation.md) | #unity #knowledge #nav-mesh #ai-navigation | 📘 有效 | Unity AI Navigation 知识 |
| [unity-animation-curve-filter-motionnodename-pitfall.md](../data/unity-animation-curve-filter-motionnodename-pitfall.md) | #unity #animation #fbx #experience #bug #custom-editor | ✅ 已验证 | 在 `AssetPostprocessor.OnPostprocessAnimation` 中实现动画曲线过滤时，**不能把** `ModelImporter.motionNodeName` **当成** Inspector `Rig` 页签里 Generic 动画的 `Root node`。`motionNodeName` 对应的是 `Animation` 页签 `Motion` 区域的 `Root Motion Node`，不是同一个设置。当前已验证可用的做法，是通过 `SerializedObject` 读取内部属性 `m_HumanDescription.m_RootMotionBoneName`，再按 `EditorCurveBinding.path` 的 Transform 路径字符串做匹配。 |
| [unity-animation-scripting-notes.md](../data/unity-animation-scripting-notes.md) | #unity #animation #csharp #performance #knowledge #root-motion | ✅ 已验证 | 一份适合做技术笔记的关联知识点清单，涵盖 Unity 开发中的动画核心机制、API 特性、脚本控制方案以及数学基础。已按核心机制、API特性、替代方案分类整理。 |
| [unity-asset-import-tool-architecture.md](../data/unity-asset-import-tool-architecture.md) | #unity #custom-editor #tools #architecture #scriptable-object #fbx #texture | ✅ 已验证 | 基于 ScriptableObject 配置驱动 + AssetPostprocessor 自动执行的资源批量导入管理框架，分为模型处理和纹理处理两大平行子系统。支持文件夹级别的规则配置、单资源豁免机制、资源移动自动重新导入、模块化后处理扩展，以及 Project 窗口/Inspector 的可视化增强。 |
| [unity-blendtree-audio-sync.md](../data/unity-blendtree-audio-sync.md) | #unity #experience #animation #blend-tree #audio | ✅ 已验证 | Unity BlendTree 下动画驱动音效同步（脚步声等）常见方案汇总 |
| [unity-cross-project-compilation-check.md](../data/unity-cross-project-compilation-check.md) | #unity #editor #csharp #experience | ✅ 已验证 | 在进行 Unity 跨项目功能迁移（特别是涉及 Editor 工具和运行时逻辑混合的迁移）时，可以直接在当前项目的终端中使用 `dotnet build` 命令编译目标项目的 `.csproj` 文件来验证迁移代码的正确性。**关键点在于必须同时编译运行时程序集和 Editor 程序集**，否则容易遗漏 Editor 目录下的编译错误。 |
| [unity-dynamicres-foveated-conflict.md](../data/unity-dynamicres-foveated-conflict.md) | #unity #vr #bug #experience | ⚠️ 待验证 | 在 Unity 2022.3.39f1 版本中，动态分辨率（Dynamic Resolution）不能与注视点渲染（Foveated Rendering）同时启用。 |
| [unity-editor-api.md](../data/unity-editor-api.md) | #unity #knowledge #editor #custom-editor | 📘 有效 | Unity Editor 开发知识 |
| [unity-framework-architecture.md](../data/unity-framework-architecture.md) | #unity #csharp #architecture | ⚠️ 待验证 | Unity 中的 C# 脚本编程相关经验 |
| [unity-generic-animation-import-config.md](../data/unity-generic-animation-import-config.md) | #unity #animation #root-motion #experience | ⚠️ 待验证 | 针对 Unity Generic（非人形）动画导入时常见的滑步（Foot Sliding）、Inspector UI 选项消失（Bake Into Pose 等不显示）、以及双重位移问题的完整四步修复流程。核心记忆口诀：**Rig → Motion(None) → Bake → Mask(Uncheck Root)**。 |
| [unity-layer-vs-renderlayer.md](../data/unity-layer-vs-renderlayer.md) | #unity #experience #rendering | ✅ 已验证 | Unity 中 Layer 与 Render Layer 的核心区别与使用场景 |
| [unity-material-renderer.md](../data/unity-material-renderer.md) | #unity #knowledge #rendering #material | 📘 有效 | Unity 渲染相关知识 |
| [unity-mcp-ai-editor-bridge.md](../data/unity-mcp-ai-editor-bridge.md) | #unity #mcp #tools #claude-code #ai #knowledge | ⚠️ 待验证 | 让 LLM（Claude、Cursor、VS Code Copilot 等）通过 MCP 协议直接操控 Unity Editor，实现自然语言创建 GameObject、编辑材质、管理场景、编写脚本等操作。 |
| [unity-meta-touch-via-userdata.md](../data/unity-meta-touch-via-userdata.md) | #unity #editor #tools #experience #serialization | ✅ 已验证 | 如果目标只是让 Unity 资源对应的 `.meta` 文件稳定产生变化，优先使用 `AssetImporter.userData` 写入自定义标记，而不是依赖 `timeCreated` 这类未明确公开承诺的内部字段。 |
| [unity-performance-ecs-culling.md](../data/unity-performance-ecs-culling.md) | #unity #experience #performance #ecs #culling | ⚠️ 待验证 | Unity 性能优化相关经验 |
| [unity-physics-system.md](../data/unity-physics-system.md) | #unity #knowledge #physics #collider #raycast | 📘 有效 | Unity 物理系统知识 |
| [unity-shader-variants-tool.md](../data/unity-shader-variants-tool.md) | #unity #shader #experience #shader-variants #editor | ✅ 已验证 | Unity 中 Shader 相关经验 |
| [unity-strict-variant-matching-enum-keyword.md](../data/unity-strict-variant-matching-enum-keyword.md) | #unity #shader #shader-variants #urp #experience #bug #vr | ✅ 已验证 | 在 Unity 2022.3.x（Meta Quest / Android / Vulkan）平台，开启 `PlayerSettings.strictShaderVariantMatching` 后，Shader Graph 中使用 `multi_compile_local` 的 Enum 关键字（如 `_DISPLAYMODE_NORMAL _DISPLAYMODE_SP1`）会持续报 `variant not found` 错误。画面显示正常，但控制台不断刷错。关闭严格匹配后错误消失。 本记录已按官方帖子与 Issue Tracker 对齐到版本维度：**“strict 下报 variant not found”是一个问题族，不同版本修复的是不同子问题。你在 2022.3.39f1 遇到的这类，并不被已修复的 Deferred 子问题覆盖。** |
| [unity6-migration-guide.md](../data/unity6-migration-guide.md) | #unity #shader #reference #urp #rendering #ecs | ⚠️ 待验证 | 从 Unity 2022.3 迁移到 Unity 6.3 LTS (6000.3.x) 的完整参考。Unity 6 经历了 6.0→6.1→6.2→6.3 四个迭代，6.3 是当前推荐 LTS（支持至 2027 年 12 月）。覆盖各版本累计变化、Breaking Changes、新功能速查、TA/客户端影响评估和 5 阶段迁移路线图。 |
| [urp-grabpass-alternative.md](../data/urp-grabpass-alternative.md) | #shader #unity #experience #urp #srp-batcher #renderer-feature | ✅ 已验证 | URP 中 GrabPass 替代方案 (GrabColor RenderFeature) {#grab-color-renderfeature} |
| [urp-renderer-feature-guide.md](../data/urp-renderer-feature-guide.md) | #shader #unity #experience #urp #srp-batcher #renderer-feature | ✅ 已验证 | URP Renderer Feature 开发要点 |
| [urp-renderfeature-runtime-toggle.md](../data/urp-renderfeature-runtime-toggle.md) | #shader #unity #experience #urp #srp-batcher #renderer-feature | ✅ 已验证 | RenderFeature 运行时开关控制 {#renderfeature-toggler} |
| [urp-skybox-notes.md](../data/urp-skybox-notes.md) | #unity #urp #shader #skybox #experience | ✅ 已验证 | URP 天空盒不能使用 URP 格式 Shader，必须使用 Built-in 管线写法。 |
| [urp-srp-architecture.md](../data/urp-srp-architecture.md) | #unity #graphics #knowledge #urp #srp | 📘 有效 | URP / SRP 知识 |
| [vera-kt-dog-identity.md](../data/vera-kt-dog-identity.md) | #design #reference #social #vera #identity | 📘 有效 | 薇拉的身份设定 |
| [vitepress-architecture-deep-dive.md](../data/vitepress-architecture-deep-dive.md) | #web #vitepress #architecture | 📘 有效 | AkashaRecord-Web 是阿卡西记录知识库的 Web 前端展示平台，采用 VitePress 构建静态站点，辅以 Express Webhook 服务实现自动构建。本文档提供了完整的技术架构、核心流程、组件系统、数据流与部署方案解析。 |
| [vitepress-dynamic-sidebar-index.md](../data/vitepress-dynamic-sidebar-index.md) | #tools #web #experience #vitepress | ✅ 已验证 | VitePress 动态侧边栏标签 + 分类索引页自动生成 |
| [vitepress-emoji-to-svg-icon.md](../data/vitepress-emoji-to-svg-icon.md) | #tools #web #experience #vitepress | ✅ 已验证 | 全站 Emoji 替换为 SVG 图标的完整流程 {#emoji-to-svg} |
| [vitepress-frontmatter-attrs-crash.md](../data/vitepress-frontmatter-attrs-crash.md) | #vitepress #bug #experience #web | ✅ 已验证 | 在 VitePress 构建过程中（`npm run docs:build`），如果文档包含自定义 ID 语法（如 `{#id}`）且该语法被意外写入 Frontmatter（如 title 字段），会导致 `markdown-it-attrs` 插件抛出 `Error in pattern 'end of block'` 错误，造成构建失败。 |
| [vitepress-sidebar-highlight-padding.md](../data/vitepress-sidebar-highlight-padding.md) | #tools #web #experience #vitepress | ✅ 已验证 | 侧边栏自定义高亮竖条与文字间距 {#sidebar-padding-left} |
| [vitepress-spa-fixed-pseudo-leak.md](../data/vitepress-spa-fixed-pseudo-leak.md) | #tools #web #experience #vitepress | ⚠️ 待验证 | VitePress SPA 路由中 position:fixed 伪元素泄漏 |
| [vitepress-vpfeature-icon-structure.md](../data/vitepress-vpfeature-icon-structure.md) | #tools #web #experience #vitepress | ✅ 已验证 | VitePress VPFeature 图标 HTML 结构（无 .icon 包裹层） {#vpfeature-icon-structure} |
| [vr-variant-collector-architecture.md](../data/vr-variant-collector-architecture.md) | #unity #shader #architecture #shader-variants | 📘 有效 | VR 变体收集器 - 架构与流程图解 |
| [vscode-copilot-skills-config.md](../data/vscode-copilot-skills-config.md) | #vscode #tools #experience #copilot | ✅ 已验证 | GitHub Copilot 使用相关经验 |
| [web-archive-mcp-blueprint.md](../data/web-archive-mcp-blueprint.md) | #mcp #python #playwright #architecture #web #tools | ✅ 已验证 | 基于 FastMCP + Playwright (Edge) 的网页归档 MCP 服务，提供 4 个工具：`save_as_markdown`、`archive_web_page`（兼容别名）、`save_as_mhtml`、`save_as_zip`。支持反爬（stealth 模式）、站点弹窗处理、CDP 协议抓取 MHTML，输出 HTML 源码 / Markdown / MHTML / 全页截图 / ZIP 打包。 |
| [windows-system-path-missing-app-detection-failure.md](../data/windows-system-path-missing-app-detection-failure.md) | #vscode #tools #experience #claude-code #git #bug | ✅ 已验证 | 当应用或扩展通过进程调用系统命令（如 `where.exe`）探测依赖时，若系统 `PATH` 缺失 `C:\Windows\System32` 等关键目录，会出现“明明已安装依赖却被判定缺失”的假故障。本记录沉淀一套可复用的定位与修复流程。 |
| [windows-winget-msstore-app-install.md](../data/windows-winget-msstore-app-install.md) | #windows #tools #experience #troubleshooting | ✅ 已验证 | 当目标应用只有 Microsoft Store 分发渠道时，仍可通过 `winget` 直接从 `msstore` 源安装，而不需要打开 Microsoft Store 图形界面。本记录验证了这一做法对 `Microsoft To Do` 可行，并总结了更可靠的安装后校验方式。 |

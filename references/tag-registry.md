# 标签注册表

> **SSOT**：所有标签的元数据定义。前端同步脚本自动解析此表生成 `tag-meta.json`。
>
> - **标签**：唯一标识，小写英文 + 连字符
> - **显示名**：前端展示用的中文/人类可读名称
> - **图标**：对应 `public/icons/{icon}.svg`，未注册则 fallback 到 `doc`
> - **维度**：分类层级 - domain(领域) / type(类型) / specialty(专项) / custom(自定义)
> - **说明**：标签用途的简要描述
>
> 新增标签时请在此注册，并同步更新 INDEX.md 标签概览。

| 标签 | 显示名 | 图标 | 维度 | 说明 |
|------|--------|------|------|------|
| #agent-skills | Agent Skills | chip | domain | Agent 技能开发相关 |
| #ai | AI | chip | domain | 人工智能领域 |
| #ai-navigation | AI 寻路 | unity | specialty | Unity AI 导航系统 |
| #akasha | 阿卡西记录 | book | custom | 知识库系统本身 |
| #animation | 动画 | unity | specialty | 动画系统相关 |
| #animation-retarget | 动画重定向 | unity | specialty | 动画重定向技术 |
| #anti-bot | 反爬虫 | network | specialty | 反爬虫/反机器人 |
| #architecture | 架构设计 | code | type | 架构设计类记录 |
| #arknights | 明日方舟 | monitor | specialty | 明日方舟游戏相关 |
| #astrbot | AstrBot | chip | specialty | AstrBot 机器人框架 |
| #audio | 音频 | unity | specialty | 音频系统 |
| #behavior-designer | 行为树 | unity | specialty | Behavior Designer 插件 |
| #bilibili | B站 | network | specialty | B站相关开发 |
| #blend-tree | BlendTree | unity | specialty | Unity BlendTree 动画 |
| #brdf | BRDF | shader | specialty | 双向反射分布函数 |
| #bug | Bug | spark | specialty | Bug 记录与修复 |
| #cicd | CI/CD | network | specialty | 持续集成/持续部署 |
| #claude-code | Claude Code | chip | specialty | Claude Code CLI 工具 |
| #collider | 碰撞体 | unity | specialty | Unity 碰撞系统 |
| #color-banding | 色带 | shader | specialty | 色带问题与修复 |
| #color-space | 色彩空间 | shader | specialty | Gamma/Linear 色彩空间 |
| #compute-shader | 计算着色器 | shader | specialty | GPU 计算着色器 |
| #conventional-commits | 提交规范 | code | specialty | Git 提交信息规范 |
| #cook-torrance | Cook-Torrance | shader | specialty | Cook-Torrance BRDF 模型 |
| #copilot | Copilot | wrench | specialty | GitHub Copilot |
| #credential | 凭证管理 | wrench | specialty | 凭证/密钥管理 |
| #csharp | C# | code | domain | C# 编程语言 |
| #culling | 剔除 | unity | specialty | 视锥/遮挡剔除 |
| #custom-editor | 自定义编辑器 | unity | specialty | Unity 编辑器扩展 |
| #cyberpunk | 赛博朋克 | monitor | specialty | 赛博朋克项目 |
| #design | 设计 | monitor | domain | 设计相关 |
| #deployment | 部署 | network | specialty | 部署相关 |
| #dither | 抖动 | shader | specialty | 抖动算法 |
| #docker | Docker | network | domain | Docker 容器技术 |
| #dotnet | .NET | code | domain | .NET 平台 |
| #draw-call | Draw Call | shader | specialty | Draw Call 优化 |
| #ecs | ECS | unity | specialty | Entity Component System |
| #editor | 编辑器 | unity | specialty | Unity 编辑器 |
| #effect-system | 效果系统 | unity | specialty | 特效系统 |
| #effects | 特效 | shader | specialty | 视觉特效 |
| #experience | 经验 | book | type | 实践经验类记录 |
| #gamma | Gamma | shader | specialty | Gamma 校正 |
| #git | Git | code | domain | Git 版本控制 |
| #hook | Hook | wrench | specialty | Claude Code Hooks 机制 |
| #github-actions | GitHub Actions | network | specialty | GitHub CI/CD |
| #gpgpu | GPGPU | shader | specialty | GPU 通用计算 |
| #graphics | 图形学 | shader | domain | 计算机图形学 |
| #hdr | HDR | shader | specialty | 高动态范围 |
| #hlsl | HLSL | shader | specialty | HLSL 着色器语言 |
| #idea | 灵感 | spark | type | 创意灵感类记录 |
| #identity | 身份设定 | doc | specialty | 身份/人设相关 |
| #ik | 逆向运动学 | unity | specialty | Inverse Kinematics |
| #knowledge | 知识 | book | type | 知识学习类记录 |
| #ktsama | KTSAMA | doc | specialty | KTSAMA 个人相关 |
| #linear | 线性空间 | shader | specialty | 线性颜色空间 |
| #material | 材质 | unity | specialty | Unity 材质系统 |
| #math | 数学 | code | specialty | 数学相关 |
| #mcp | MCP 协议 | chip | domain | Model Context Protocol |
| #meilisearch | Meilisearch | wrench | specialty | Meilisearch 搜索引擎 |
| #mvvm | MVVM 架构 | code | specialty | MVVM 设计模式 |
| #nav-mesh | NavMesh | unity | specialty | Unity 导航网格 |
| #npr | NPR 渲染 | shader | specialty | 非真实感渲染 |
| #pat | PAT 令牌 | code | specialty | Personal Access Token |
| #pbr | PBR 渲染 | shader | specialty | 基于物理的渲染 |
| #performance | 性能优化 | spark | specialty | 性能优化 |
| #physics | 物理系统 | unity | specialty | Unity 物理引擎 |
| #playwright | Playwright | network | specialty | Playwright 测试框架 |
| #post-processing | 后处理 | shader | specialty | 后处理效果 |
| #python | Python | code | domain | Python 编程语言 |
| #raycast | 射线检测 | unity | specialty | 射线检测 |
| #react | React | network | domain | React 框架 |
| #reference | 参考 | book | type | 参考资料/文档 |
| #renderer-feature | Renderer Feature | shader | specialty | URP Renderer Feature |
| #rendering | 渲染 | shader | specialty | 渲染技术 |
| #rendering-pipeline | 渲染管线 | shader | specialty | 渲染管线 |
| #retarget-pro | Retarget Pro | unity | specialty | Retarget Pro 插件 |
| #root-motion | Root Motion | unity | specialty | Root Motion 动画 |
| #scriptable-object | ScriptableObject | unity | specialty | Unity ScriptableObject |
| #sdf | SDF 距离场 | shader | specialty | 有符号距离场 |
| #search-api | 搜索 API | wrench | specialty | 搜索 API 接口 |
| #search-engine | 搜索引擎 | wrench | specialty | 搜索引擎开发 |
| #searxng | SearXNG | wrench | specialty | SearXNG 元搜索引擎 |
| #selenium | Selenium | network | specialty | Selenium 自动化 |
| #serp | SERP | wrench | specialty | 搜索结果页 |
| #shader | 着色器 | shader | domain | 着色器编程 |
| #shader-variants | Shader 变体 | shader | specialty | Shader 变体管理 |
| #smart-furniture | 智能家具 | spark | specialty | 智能家具项目 |
| #social | 社交 | network | specialty | 社交平台相关 |
| #srp | SRP | shader | specialty | Scriptable Render Pipeline |
| #srp-batcher | SRP Batcher | shader | specialty | SRP Batcher 优化 |
| #tools | 工具 | wrench | domain | 开发工具 |
| #troubleshooting | 故障排查 | wrench | specialty | 问题排查 |
| #ui | UI | monitor | specialty | 用户界面 |
| #unity | Unity 引擎 | unity | domain | Unity 游戏引擎 |
| #urp | URP | shader | specialty | Universal Render Pipeline |
| #vera | 薇拉 | doc | specialty | 薇拉项目 |
| #vitepress | VitePress | network | domain | VitePress 静态站点 |
| #vscode | VS Code | monitor | specialty | VS Code 编辑器 |
| #web | Web 开发 | network | domain | Web 前端开发 |
| #macos | macOS | monitor | domain | macOS 系统与工具链 |

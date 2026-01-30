# 分类体系索引

> 经验记录系统的完整分类结构和文件说明

---

## 目录结构

```
~/.copilot/experiences/
├── anthropic/          # Anthropic 产品（Claude Code、Claude API）
│   └── README.md       # 目录索引
├── csharp/             # C# 语言
├── git/                # Git 版本控制
├── python/             # Python
├── shader/             # Shader 开发
├── tools/              # 开发工具
├── unity/              # Unity 引擎
├── vscode/             # VS Code 编辑器
└── general/            # 通用内容
```

## 分类详情

### anthropic/ - Anthropic 产品

| 文件 | 说明 |
|------|------|
| `claude-code.md` | Claude Code AI 编程助手完整指南 |
| `README.md` | 本索引 |

### csharp/ - C# 语言

| 文件 | 说明 |
|------|------|
| `syntax.md` | 语法特性：泛型、委托、事件、反射 |
| `async.md` | 异步编程：async/await、Task、并发控制 |
| `linq.md` | LINQ 查询：表达式、方法语法、性能 |
| `patterns.md` | 设计模式：单例、工厂、观察者、SOLID |
| `collections.md` | 集合数据结构：List、Dictionary、Span |
| `dotnet.md` | .NET API：IO、网络、JSON、正则 |
| `misc.md` | 其他 C# 相关 |

### git/ - 版本控制

| 文件 | 说明 |
|------|------|
| `commands.md` | 常用命令：基础、高级、组合技巧 |
| `workflow.md` | 工作流：分支策略、PR、代码审查 |
| `troubleshooting.md` | 问题解决：冲突、回滚、恢复 |
| `lfs.md` | LFS 大文件：配置、迁移 |
| `misc.md` | 其他 Git 相关 |

### python/ - Python

| 文件 | 说明 |
|------|------|
| `syntax.md` | 语法：类型提示、装饰器、上下文 |
| `libraries.md` | 常用库：requests、pandas、numpy |
| `automation.md` | 自动化：文件处理、批量操作 |
| `environment.md` | 环境管理：venv、conda、pip |
| `misc.md` | 其他 Python 相关 |

### shader/ - Shader 开发

| 文件 | 说明 |
|------|------|
| `hlsl.md` | HLSL 语法：数据类型、函数、语义 |
| `urp.md` | URP 管线：URP Shader、渲染特性 |
| `hdrp.md` | HDRP 管线：光照、体积效果 |
| `techniques.md` | 渲染技术：光照模型、阴影、PBR |
| `optimization.md` | 性能优化：指令、采样、变体 |
| `effects.md` | 特效实现：溶解、描边、扭曲、水面 |
| `misc.md` | 其他 Shader 相关 |

### tools/ - 开发工具

| 文件 | 说明 |
|------|------|
| `terminal.md` | 终端命令：Shell、脚本、别名 |
| `build.md` | 构建工具：npm、webpack、vite |
| `debug.md` | 调试工具：日志、性能、内存分析 |
| `cicd.md` | CI/CD：GitHub Actions、自动化 |
| `misc.md` | 其他工具相关 |

### unity/ - Unity 引擎

| 文件 | 说明 |
|------|------|
| `csharp.md` | Unity C# 脚本：MonoBehaviour、协程、事件、ScriptableObject |
| `physics.md` | 物理系统：Rigidbody、Collider、碰撞检测、射线、关节 |
| `shader.md` | Unity Shader：ShaderLab、Shader Graph、材质 |
| `vfx.md` | 特效技法：粒子系统、VFX Graph、后处理 |
| `ui.md` | UI 系统：UGUI、UI Toolkit、Canvas 优化 |
| `animation.md` | 动画系统：Animator、状态机、IK、Timeline |
| `performance.md` | 性能优化：内存、GC、Draw Call、批处理、Profiler |
| `editor.md` | 编辑器扩展：Inspector、EditorWindow、工具开发 |
| `networking.md` | 网络开发：Netcode、Mirror、同步 |
| `asset.md` | 资源管理：AssetBundle、Addressables、热更新 |
| `misc.md` | 其他 Unity 相关 |

### vscode/ - VS Code 编辑器

| 文件 | 说明 |
|------|------|
| `shortcuts.md` | 快捷键：常用、自定义、多光标 |
| `extensions.md` | 扩展：推荐、配置、开发 |
| `settings.md` | 配置：settings.json、工作区 |
| `copilot.md` | Copilot：Chat、Agent、Skills、MCP |
| `debugging.md` | 调试：launch.json、断点 |
| `misc.md` | 其他 VS Code 相关 |

### general/ - 通用

| 文件 | 说明 |
|------|------|
| `misc.md` | 无法归类的其他有价值内容 |

## 新建分类

需要新增分类时：

1. 在 `experiences/` 下创建新目录
2. 添加目录到 SKILL.md 的分类体系中
3. 在本 INDEX.md 中添加该分类的文件说明
4. 创建该分类的 README.md 或第一个文件

## 文件命名规范

- 使用小写字母和连字符：`csharp.md`、`shader.md`
- 同一分类内文件命名保持一致风格
- 避免使用特殊字符和空格

# Amplify Shader Editor 架构与实现机制解析

**标签**：#unity #shader #graphics #knowledge #architecture #urp
**来源**：[项目源码分析 + Amplify 官方文档 + 官方论坛/公开资料交叉验证]
**收录日期**：2026-03-24
**来源日期**：2026-03-24
**更新日期**：2026-03-24
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐⭐(项目源码 + 项目样本 + 官方资料交叉验证)
**适用版本**：Amplify Shader Editor 1.9.8.1；Unity URP 项目

### 概要

Amplify Shader Editor 的核心不是单纯的节点编辑器，而是一套 `图模型 + 文本模板 + 代码片段收集器 + Shader 内嵌序列化协议`。它把节点图直接嵌入 `.shader` 文件尾部的 `/*ASEBEGIN ... ASEEND*/` 区块中，使 Shader 文件同时成为运行产物和可编辑源；生成阶段则由主节点发起，沿输入端口反向递归收集代码片段，再通过模板标签系统组装为完整 Shader。

### 内容

#### 1. 本地源码验证出的核心结论

基于项目内 `Assets/CommonFunctionModule/CommonScript/Plugin/AmplifyShaderEditor` 的源码分析，可以确认以下实现结构：

- `AmplifyShaderEditorWindow` 是总控入口，负责窗口生命周期、图加载/保存、模板管理与编译触发
- `ParentGraph` 是整张图的文档模型，负责节点容器、连接管理、节点排序、序列化和触发主节点编译
- `ParentNode` 是大多数节点的共同基类，节点同时具备 UI、可序列化数据和代码生成三重职责
- `InputPort` / `OutputPort` / `WireReference` 负责端口与连线；生成代码时由输入端口沿连线反向回溯上游节点
- `MasterNodeDataCollector` 负责把各节点产出的属性、uniform、pragma、函数、局部变量、插值器等片段集中登记和去重
- `TemplatesManager` / `TemplateIdManager` / `TemplateMultiPassMasterNode` 负责模板识别、标签替换、多 Pass 组织和最终 Shader 拼装

#### 2. ASE 的真正设计理念

ASE 最关键的设计不是“节点可视化”，而是以下四点：

- **Shader 即源文件**：图信息直接附着在 `.shader` 末尾，而不是分离到独立 `.graph`
- **图即依赖图**：编译时从主节点输入端口回溯上游节点，连线关系天然就是代码依赖关系
- **片段式代码生成**：节点只负责声明自己需要哪些代码片段，不直接拼完整 Shader
- **模板决定结构**：节点图决定“算什么”，模板决定“这些代码放在哪些 Pass、哪些段落、以什么渲染管线结构输出”

#### 3. 持久化与反序列化机制

本地源码 `IOUtils.cs` 明确使用以下标记：

- `/*ASEBEGIN`
- `ASEEND*/`
- `//CHKSM=...`

这表示 ASE 使用“Shader 文件尾部嵌入 DSL 文本”的方式保存图数据。图内通常包含：

- 版本号
- 相机/缩放信息
- `Node;...` 节点行
- `WireConnection;...` 连线行
- 校验和

加载流程由 `AmplifyShaderEditorWindow.LoadFromDisk(...)` 驱动，大致是：

1. 读取 shader 文本
2. 检查是否存在有效 ASE body
3. 按行解析指令
4. 通过类型名和反射创建节点
5. 先恢复节点，再恢复连线
6. 处理旧版本/废弃节点兼容

这说明 ASE 实际上维护了一套专门面向 Shader 资产的文本序列化协议。

#### 4. 代码生成链路

本地源码验证出的生成链路如下：

1. 主节点 `MasterNode.Execute(...)` 或 `TemplateMultiPassMasterNode.Execute(...)` 发起编译
2. 初始化 `MasterNodeDataCollector`
3. 主节点从输入端口请求数据
4. `InputPort.GenerateShaderForOutput(...)` 顺着连线找到上游节点
5. 上游节点返回表达式/变量名，并把函数、局部变量、pragma、uniform 等信息写入 DataCollector
6. 模板系统读取这些收集结果并填充到模板标签
7. 最终 `UpdateShaderAsset(...)` 将生成后的 Shader 正文与 `GenerateGraphInfo()` 生成的图数据一起写回文件

因此 ASE 的图并不是运行时执行图，而是“Shader 代码依赖图”。

#### 5. 模板与多 Pass 的实现意义

项目源码和官方资料都指向同一个结论：ASE 的模板系统不是附加功能，而是它适配 SRP/URP、多 Pass、Render State 的核心机制。

在项目源码 `TemplatesManager.cs` 中能看到大量模板标签常量，例如：

- `/*ase_name*/`
- `/*ase_props*/`
- `/*ase_pragma*/`
- `/*ase_globals*/`
- `/*ase_vert_code:...*/`
- `/*ase_frag_code:...*/`
- `/*ase_pass*/`
- `/*ase_pass_end*/`
- `/*ase_lod*/`

这证明模板本质是“带约定标签的 Shader 文本”，而不是黑盒编译器输出。

`TemplateIdManager.BuildShader()` 的设计重点是：

- 按记录好的起始位置排序替换点
- 逐个替换模板 ID
- 按 pass 使用状态裁剪不需要的段落
- 最后再做 tag 级别替换

这是一种典型的“文本模板 + 位置替换”策略，避免了完整 AST 编译器的高复杂度，同时保留了很强的结构控制力。

#### 6. 多 Pass 组织方式

项目里的 `TemplateMultiPassMasterNode` 显示，ASE 的多 Pass 不是简单复制代码，而是：

- 同一 Shader 内部可以有多个 pass 对应的 master node
- 每个 pass 有独立输入与收集上下文
- 但属性、subshader 和全局 uniform 又能汇总到同一最终结果
- 某些 pass 可以被包含、排除、隐藏或由模板选项动态控制

项目样本 `boli_3.shader` 与 `UVTitleSplit_ASE.shader` 的 `ASEBEGIN` 区块都能看到多个 `TemplateMultiPassMasterNode` 实例，这与本地源码结构完全吻合。

#### 7. Shader Function 与复用机制

`AmplifyShaderFunction.cs` 中最重要的字段是 `FunctionInfo`，说明 Shader Function 本身也是一等资产，其内部同样保存图定义信息。

这意味着 ASE 的可复用能力不是简单“复制节点组”，而是：

- 将一个函数图保存为独立资产
- 在其他 Shader 图中作为 Function 节点引用
- 输入输出通过 `Function Input` / `Function Output` 节点定义

项目额外定制的 `ASEFunctionWatcher.cs` 进一步补强了这一体系：

- 监听 ASE Function 资产变化
- 递归查找所有引用链
- 自动回刷受影响的 ASE Shader

这是把“函数资产化”真正纳入工程工作流的关键增强。

#### 8. Custom Expression 的最佳定位

项目样本 `UVTitleSplit_ASE.shader` 中使用了 `CustomExpressionNode` 处理核心 UV 逻辑，这与官方文档描述一致：

- 检测到 `return` 时，会生成函数模式
- 没有 `return` 时，会以内联表达式方式写入顶点/片元代码段
- 支持 Create / Call / File 等模式

这说明 ASE 的最佳实践不是“完全拒绝手写代码”，而是：

- 常规组合逻辑交给节点
- 复杂局部算法交给 Custom Expression
- 更大粒度复用交给 Shader Function
- 整体结构问题交给模板

#### 9. 外部资料交叉验证结果

通过官方文档和公开资料可交叉验证以下事实：

- **官方 Templates 文档**：模板是普通 Unity Shader，在关键位置通过 ASE 注释标签标识替换点；支持从模板创建 Shader、切换模板和多 Pass 模式
- **官方 Custom Expression 文档**：存在 `return` 会进入函数模式；无 `return` 则按表达式模式生成；支持 Create / Call / File 模式
- **官方 Function Input 文档**：Function Input 只用于 Shader Function，本质是为函数图定义输入端口，最终会在使用函数时映射成画布上的输入端口
- **官方 API 文档**：支持继承父节点类编写自定义节点，节点结构由主体、输入端口、输出端口和代码生成逻辑组成
- **官方/社区 Multi-Pass Switch 文档**：多 Pass 下会根据当前分析的 subshader/pass，在编译时路由到对应输入

这些公开信息与本地源码分析结论一致，没有出现明显冲突。

#### 10. 对工程实践最值得记住的结论

- ASE 最强的不是节点数量，而是“图、模板、资产协议”三者耦合得非常成熟
- 它特别适合 TA / 图形程序混合协作，因为模板文本可控，节点图可视化，必要时还能手写局部 HLSL
- 如果项目要长期深用 ASE，优先投入方向应该是：
  - 设计统一模板
  - 抽取 Shader Function
  - 补齐函数依赖回刷
  - 避免单图过大

### 关键代码（如有）

```text
/*ASEBEGIN
Version=19801
Node;AmplifyShaderEditor.CustomExpressionNode;...
Node;AmplifyShaderEditor.TemplateMultiPassMasterNode;...
WireConnection;...
ASEEND*/
```

上面的结构来自项目内实际 ASE Shader 样本，证明 ASE 使用“尾部嵌入图数据”的资产协议。

### 参考链接（如有）

- [Amplify Shader Editor Manual](https://wiki.amplify.pt/index.php?title=Unity_Products%3AAmplify_Shader_Editor%2FManual) - 官方手册总入口
- [Amplify Shader Editor Templates](https://wiki.amplify.pt/index.php?title=Unity_Products%3AAmplify_Shader_Editor%2FTemplates) - 官方模板系统说明
- [Amplify Shader Editor Custom Expression](https://wiki.amplify.pt/index.php?title=Unity_Products%3AAmplify_Shader_Editor%2FCustom_Expression) - 官方自定义表达式说明
- [Amplify Shader Editor Function Input](https://wiki.amplify.pt/index.php?title=Unity_Products%3AAmplify_Shader_Editor%2FFunction_Input) - 官方 Shader Function 输入节点说明
- [Amplify Shader Editor API](https://wiki.amplify.pt/index.php?title=Unity_Products%3AAmplify_Shader_Editor%2FAPI) - 官方自定义节点 API
- [Amplify Shader Editor Template Multi-Pass Switch](https://wiki.amplify.pt/index.php?title=Unity_Products%3AAmplify_Shader_Editor%2FTemplate_Multi-Pass_Switch) - 官方多 Pass 路由节点说明
- [Amplify Forum - Multi-Pass Questions](https://forum.amplify.pt/viewtopic.php?t=586) - 社区对多 Pass 能力的讨论

### 相关记录（如有）

- [ASE Shader 架构与 Bakery 光照集成最佳实践](./ase-shader-bakery-integration.md) - 项目内 ASE 实践经验，偏工程使用层
- [HLSL 着色器语言相关经验](./shader-variants-compile.md) - 涉及 ASE 中 Static Switch/变体使用

### 验证记录

- [2026-03-24] 初次记录。基于项目内 ASE 插件源码、项目样本 Shader、官方文档搜索结果和官方论坛公开说明交叉验证整理。
- [2026-03-24] 本地源码验证重点包括：`AmplifyShaderEditorWindow`、`ParentGraph`、`ParentNode`、`InputPort`、`MasterNodeDataCollector`、`TemplatesManager`、`TemplateIdManager`、`TemplateMultiPassMasterNode`。
- [2026-03-24] 项目样本验证包括 `boli_3.shader`、`UVTitleSplit_ASE.shader`，均确认存在 `ASEBEGIN` 图数据与多 Pass 主节点信息。

---

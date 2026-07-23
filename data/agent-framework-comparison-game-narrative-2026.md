# Agent 框架对比 - 游戏叙事生成场景 (2026)

**标签**：#ai #llm #agent-workflow #game-design #architecture #comparison #structured-output
**来源**：开源框架调研 + GitHub 官方文档
**收录日期**：2026-07-23
**来源日期**：2026-07-23
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐（基于官方文档和 GitHub 仓库最新信息）

### 概要

针对游戏动态叙事生成需求,调研主流开源 Agent 框架的适用性。重点评估结构化输出、多 Agent 协作、错误处理、编程语言支持等核心能力。结论:Unity/C# 项目推荐 Microsoft Agent Framework,Python 后端推荐 LangGraph,快速原型推荐 CrewAI。

### 内容

#### 一、调研背景

基于 [llm-structured-event-generation-game-narrative.md](./llm-structured-event-generation-game-narrative.md) 的架构设计,需要找到支持以下能力的开源框架:

**核心需求**:
- ✅ 结构化输出(JSON Schema 强制约束)
- ✅ 多 Agent 协作(主控 → 生成 → 校验)
- ✅ 错误处理机制(Hints-based 自纠错)
- ✅ 向量检索集成(世界书查询)
- ✅ 编程语言支持(C# for Unity / Python for backend)

#### 二、框架对比

##### 1. Microsoft Agent Framework (MAF)

**GitHub**: https://github.com/microsoft/agent-framework  
**前身**: Semantic Kernel (已迁移到 MAF,Semantic Kernel 进入维护模式)  
**最新版本**: Python/C# 双语言支持,2026年7月持续更新

**核心特性**:
- ✅ **C# 原生支持**:完整的 .NET 10.0+ 支持,适合 Unity
- ✅ **多 Agent 编排**:基于图的工作流,支持顺序/并发/交接/群组协作
- ✅ **生产级特性**:checkpointing、streaming、human-in-the-loop、time-travel
- ✅ **中间件系统**:灵活的请求/响应处理和异常处理
- ✅ **多 LLM 支持**:Azure OpenAI、OpenAI、GitHub Copilot SDK
- ⚠️ **结构化输出**:文档未明确提及,需进一步验证

**安装**:
```bash
# .NET
dotnet add package Microsoft.Agents.AI
dotnet add package Microsoft.Agents.AI.Foundry

# Python
pip install agent-framework
```

**C# 示例**:
```csharp
AIAgent agent = new AIProjectClient(new Uri(endpoint), new DefaultAzureCredential())
    .AsAIAgent(model: deploymentName, instructions: "...", name: "EventGenerator");
    
var result = await agent.RunAsync("生成主题为商人公会报复的事件...");
```

**适用场景**:
- ✅ Unity C# 项目
- ✅ 需要云部署和分布式追踪
- ✅ 企业级生产环境

**缺点**:
- ❌ 较重量级,云优先设计
- ❌ 游戏开发案例较少
- ❌ 结构化输出支持不明确

**推荐指数**: ⭐⭐⭐⭐ (Unity 项目首选)

---

##### 2. LangGraph

**GitHub**: https://github.com/langchain-ai/langgraph  
**最新版本**: 1.2.9 (2026-07-10)  
**语言**: Python 99.6%, JavaScript/TypeScript 版本独立维护

**核心特性**:
- ✅ **图状态机**:支持循环/分支,非 DAG 限制
- ✅ **持久化执行**:从失败中自动恢复,支持长时间运行
- ✅ **Human-in-the-loop**:可暂停/审核/修改执行
- ✅ **结构化输出**:与 Pydantic 深度集成
- ✅ **多 Agent**:SupervisorAgent 模式,子图支持
- ✅ **流式处理**:token-by-token streaming
- ✅ **全面的记忆系统**:短期工作记忆 + 长期持久化

**安装**:
```bash
pip install -U langgraph
```

**Python 示例**:
```python
from langgraph.graph import StateGraph, END
from pydantic import BaseModel

class EventDraft(BaseModel):
    title: str
    choices: List[Choice]

workflow = StateGraph(GameState)
workflow.add_node("world_master", world_master_agent)
workflow.add_node("event_generator", event_generator_with_schema)
workflow.add_node("validator", validate_event)

workflow.add_edge("world_master", "event_generator")
workflow.add_conditional_edges(
    "event_generator",
    lambda x: "validator" if x["draft"] else "world_master"
)
```

**适用场景**:
- ✅ Python 后端 + 游戏客户端 HTTP 调用
- ✅ 复杂状态机和循环流程
- ✅ 需要持久化和恢复能力

**缺点**:
- ❌ 不支持 C#(只有 Python 和 JS/TS)
- ❌ 与 LangChain 生态耦合(虽然可独立使用)

**推荐指数**: ⭐⭐⭐⭐⭐ (Python 后端首选)

---

##### 3. CrewAI

**GitHub**: https://github.com/joaomdmoura/crewai  
**最新版本**: 1.15.5 (2026-07-20)  
**语言**: Python (3.10-3.13)

**核心特性**:
- ✅ **角色驱动**:YAML 定义 Agent 的 role/goal/backstory
- ✅ **双模式**:Crews(自主协作) + Flows(事件驱动控制)
- ✅ **结构化输出**:Pydantic 模型强制约束
- ✅ **异步执行**:原生 async 支持
- ✅ **Human-in-the-loop**:明确的审核点
- ✅ **工具生态**:MCP/A2A 支持,丰富的预置工具
- ✅ **代码简洁**:上手快,适合快速原型

**安装**:
```bash
uv pip install 'crewai[tools]'
crewai create crew game_narrative_system
```

**YAML 定义 Agent**:
```yaml
world_master:
  role: >
    World Master - 剧情规划专家
  goal: >
    分析玩家行为并规划符合世界观的事件主题
  backstory: >
    你掌握完整的世界书和剧本大纲,负责确保叙事连贯性
  tools:
    - query_world_book
    - check_plot_dag

event_generator:
  role: >
    Event Generator - 内容创作专家
  goal: >
    生成符合 schema 的结构化事件草稿
  output_pydantic: EventDraft
```

**适用场景**:
- ✅ 快速原型验证
- ✅ 需要声明式配置
- ✅ 社区活跃(10万+认证开发者)

**缺点**:
- ❌ 不支持 C#(Python only)
- ❌ 生产环境案例相对较少

**推荐指数**: ⭐⭐⭐⭐ (快速验证首选)

---

##### 4. Haystack

**GitHub**: https://github.com/deepset-ai/haystack  
**最新版本**: 3.0.0 (2026-07-20)  
**语言**: Python

**核心特性**:
- ✅ **RAG 专长**:为检索增强生成优化
- ✅ **Pipeline 架构**:模块化组件,显式数据流
- ✅ **向量数据库**:丰富的集成(通过 haystack-core-integrations)
- ✅ **异步支持**:原生 async + token streaming
- ✅ **多模态**:文本/图像/音频

**安装**:
```bash
pip install haystack-ai
```

**适用场景**:
- ✅ 世界书向量检索
- ✅ 语义搜索
- ✅ 知识库问答

**缺点**:
- ❌ 多 Agent 协作支持较弱
- ❌ 面向企业 RAG,非游戏 AI
- ❌ 不支持 C#

**推荐指数**: ⭐⭐⭐ (作为世界书检索组件)

---

##### 5. AutoGen (Microsoft Research)

**GitHub**: https://github.com/microsoft/autogen  
**状态**: ⚠️ **维护模式**(不再新增功能,社区维护)  
**继任者**: Microsoft Agent Framework

**核心特性**:
- ✅ 对话式多 Agent(Agent 之间消息协作)
- ✅ Group Chat(动态决定谁发言)
- ✅ 跨语言支持(.NET + Python)

**迁移建议**:
Microsoft 官方推荐新项目使用 Microsoft Agent Framework。

**推荐指数**: ⭐⭐ (已被 MAF 取代)

---

#### 三、核心功能支持对比表

| 框架 | 结构化输出 | 多Agent协作 | 错误处理 | 向量检索 | C#支持 | 游戏适用性 | 社区活跃度 |
|---|---|---|---|---|---|---|---|
| **Microsoft Agent Framework** | ⚠️ 未明确 | ✅✅✅ | ✅✅✅ | ⚠️ | ✅✅✅ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **LangGraph** | ✅✅✅ | ✅✅✅ | ✅✅✅ | ✅✅ | ❌ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **CrewAI** | ✅✅ | ✅✅ | ✅ | ⚠️ | ❌ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Haystack** | ⚠️ | ⚠️ | ✅ | ✅✅✅ | ❌ | ⭐⭐ | ⭐⭐⭐⭐ |
| **AutoGen** | ❌ | ✅✅ | ✅ | ❌ | ✅ | ⭐⭐ | ⭐⭐ (维护模式) |

---

#### 四、推荐方案

##### 方案 A: Unity C# 项目

**推荐**: **Microsoft Agent Framework**

**原因**:
- ✅ C# 原生支持,直接在 Unity 中使用
- ✅ 微软官方维护,稳定性好
- ✅ 多 Agent 编排能力完整
- ⚠️ 需验证结构化输出支持(可能需要自己封装)

**快速验证代码**:
```csharp
// Unity MonoBehaviour
using Microsoft.Agents.AI;

public class EventSystem : MonoBehaviour {
    private AIAgent worldMaster;
    private AIAgent eventGenerator;
    
    async void Start() {
        var client = new AIProjectClient(
            new Uri(endpoint), 
            new DefaultAzureCredential()
        );
        
        worldMaster = client.AsAIAgent(
            model: "gpt-4",
            instructions: "你是World Master,负责规划事件主题...",
            name: "WorldMaster"
        );
        
        eventGenerator = client.AsAIAgent(
            model: "gpt-4",
            instructions: "你是Event Generator,生成结构化事件...",
            name: "EventGenerator"
        );
    }
    
    public async Task<string> GenerateEvent(string playerAction) {
        var theme = await worldMaster.RunAsync($"玩家行为: {playerAction}");
        var eventJson = await eventGenerator.RunAsync($"主题: {theme}");
        return eventJson;
    }
}
```

**潜在问题**:
- 结构化输出需要自己用 `System.Text.Json` 或 `Newtonsoft.Json` 解析和校验
- 云优先设计可能增加延迟(可考虑本地模型)

---

##### 方案 B: Godot/其他引擎 + Python 后端

**推荐**: **LangGraph**

**原因**:
- ✅ 结构化输出支持最完善(Pydantic 集成)
- ✅ 图状态机适合复杂事件生成流程
- ✅ 持久化能力强,支持存档/读档
- ✅ 生态最成熟

**架构**:
```
Godot Client (GDScript)
    ↓ HTTP POST /api/generate_event
FastAPI Backend (Python + LangGraph)
    ├─ WorldMaster Agent (规划主题)
    ├─ EventGenerator Agent (生成草稿)
    └─ Validator (校验入库)
    ↓ 返回 JSON
Godot Client 渲染事件
```

**后端示例**:
```python
from fastapi import FastAPI
from langgraph.graph import StateGraph
from pydantic import BaseModel

app = FastAPI()

class EventRequest(BaseModel):
    player_action: str
    world_state: dict

class EventDraft(BaseModel):
    title: str
    description: str
    choices: List[Choice]

@app.post("/api/generate_event")
async def generate_event(req: EventRequest):
    workflow = create_event_workflow()  # LangGraph workflow
    result = await workflow.ainvoke({
        "player_action": req.player_action,
        "world_state": req.world_state
    })
    return result["event_draft"]
```

---

##### 方案 C: 快速原型验证

**推荐**: **CrewAI**

**原因**:
- ✅ YAML 配置,无需大量代码
- ✅ 结构化输出简单(Pydantic)
- ✅ 上手最快

**示例**:
```python
from crewai import Agent, Task, Crew, Process
from pydantic import BaseModel

class EventDraft(BaseModel):
    title: str
    choices: List[Choice]

world_master = Agent(
    role="World Master",
    goal="规划符合剧情的事件主题",
    backstory="掌握世界书和剧本大纲...",
    tools=[query_world_book]
)

event_generator = Agent(
    role="Event Generator",
    goal="生成结构化事件",
    output_pydantic=EventDraft
)

plan_task = Task(
    description="分析玩家行为: {player_action}",
    agent=world_master,
    expected_output="事件主题和目标checkpoint"
)

generate_task = Task(
    description="生成事件: {theme}",
    agent=event_generator,
    expected_output="符合schema的事件JSON"
)

crew = Crew(
    agents=[world_master, event_generator],
    tasks=[plan_task, generate_task],
    process=Process.sequential
)

result = crew.kickoff(inputs={"player_action": "拒绝贿赂"})
```

---

#### 五、关键决策因素

##### 1. 如果必须用 C# (Unity/Godot C#)
→ **Microsoft Agent Framework** (唯一成熟的 C# Agent 框架)

##### 2. 如果可以用 Python 后端
→ **LangGraph** (功能最完整,生态最好)

##### 3. 如果需要快速验证想法
→ **CrewAI** (代码最少,配置最简单)

##### 4. 如果只需要世界书检索
→ **Haystack** (作为 RAG 组件集成到主框架)

##### 5. 如果需要本地运行(无云依赖)
→ **LangGraph** 或 **CrewAI** + Ollama/LMStudio

---

#### 六、实施建议

##### 阶段 1: 原型验证 (1-2周)

**工具**: CrewAI + Claude/GPT-4

**目标**:
- 验证三层架构可行性
- 测试结构化输出质量
- 评估 LLM 生成的叙事连贯性

**输出**:
- Python 脚本原型
- 10-20 个测试事件
- 性能和成本数据

---

##### 阶段 2: 技术选型 (根据原型结果)

**如果原型成功** → 选择生产框架:
- Unity C# → Microsoft Agent Framework
- Python 后端 → LangGraph
- 混合方案 → FastAPI + LangGraph 后端 + 游戏客户端 HTTP 调用

**如果原型失败** → 诊断瓶颈:
- LLM 质量问题 → 换模型或调整 prompt
- 结构化输出不稳定 → 加强 schema 约束或后处理
- 性能问题 → 考虑缓存/预生成

---

##### 阶段 3: 生产集成 (4-6周)

**关键任务**:
1. 世界书向量化(embedding + 向量数据库)
2. 事件模板库(不同危险等级的 schema)
3. 校验层实现(白名单/一致性检查)
4. 错误处理(Hints-based 重试)
5. 持久化(玩家触发的事件记录)

---

### 相关记录

- [llm-structured-event-generation-game-narrative.md](./llm-structured-event-generation-game-narrative.md) - 游戏动态事件生成架构设计
- [agent-skills-spec.md](./agent-skills-spec.md) - Agent Skills 开放标准
- [claude-code-2-1-feature-inventory.md](./claude-code-2-1-feature-inventory.md) - Claude Code 的结构化输出实现

---

### 验证记录

- [2026-07-23] 基于各框架 GitHub 官方文档和最新版本(2026年7月)的调研
- [2026-07-23] Microsoft Agent Framework 和 LangGraph 的特性已通过官方文档验证
- [2026-07-23] CrewAI 1.15.5 的结构化输出和 Flows 特性已确认

# Claude Code 作为 Agent 框架接入多种模型 (LLM Gateway)

**收录日期**：2026-01-31
**标签**：#ai #tools #reference #claude-code
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐ (实践验证)

**问题/场景**：

想了解 Claude Code 是否可以作为"中转层"，连接 IDE 后使用 GLM 或其他非 Anthropic 模型，以及具体支持哪些模型提供商。

**解决方案/结论**：

**Claude Code 本质上是一个 Agent 框架**，不绑定特定模型，通过配置 `ANTHROPIC_BASE_URL` 等环境变量可接入不同的后端 API。

### 官方支持的提供商

| 提供商 | 环境变量 | 说明 |
|--------|----------|------|
| **Anthropic API** | `ANTHROPIC_BASE_URL` | 默认，直连 Anthropic |
| **Amazon Bedrock** | `CLAUDE_CODE_USE_BEDROCK=1` | 通过 AWS 调用 Claude |
| **Google Vertex AI** | `CLAUDE_CODE_USE_VERTEX=1` | 通过 GCP 调用 Claude |
| **Microsoft Foundry** | `CLAUDE_CODE_USE_FOUNDRY=1` | 通过 Azure 调用 Claude |

### 通过 LLM Gateway 扩展更多模型

使用 **LiteLLM** 或类似代理可接入几乎任何兼容 Anthropic/OpenAI API 格式的模型。

理论上可接入的模型：

| 模型系列 | 提供商 |
|----------|--------|
| **GLM-4.7 / GLM-4.5** | 智谱 AI (bigmodel.cn) |
| **GPT-4 / GPT-4o** | OpenAI |
| **Gemini Pro / Ultra** | Google |
| **DeepSeek** | DeepSeek |
| **Qwen (通义千问)** | 阿里云 |
| **Moonshot (Kimi)** | 月之暗面 |
| **本地模型** | Ollama、vLLM、LocalAI 等 |

### 智谱 GLM 配置示例

智谱提供了 **Anthropic 兼容 API 端点**，在 `~/.claude/settings.json` 中配置：

```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "https://open.bigmodel.cn/api/anthropic",
    "ANTHROPIC_AUTH_TOKEN": "your-api-key",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "glm-4.5-air",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "glm-4.7",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "glm-4.7"
  }
}
```

### 关键要点

- Claude Code **界面显示的仍是 Anthropic 模型名**，但实际调用的是配置的后端模型
- 后端 API 需**兼容 Anthropic Messages 格式**（或通过网关转换）
- 使用 `/model` 命令可查看/切换可用模型

**参考链接**：

- [Claude Code Model Configuration](https://code.claude.com/docs/en/model-config) - 模型配置官方文档
- [Claude Code LLM Gateway](https://code.claude.com/docs/en/llm-gateway) - LiteLLM 等网关配置
- [Claude Code on Amazon Bedrock](https://code.claude.com/docs/en/amazon-bedrock) - AWS Bedrock 配置
- [智谱 GLM Coding Plan](https://docs.bigmodel.cn/cn/guide/develop/claude) - 智谱 AI Claude 兼容 API

**验证记录**：

- [2026-01-31] 初次记录，来源：官方文档 + 实践验证。已成功通过智谱 API 使用 GLM-4.7 模型。

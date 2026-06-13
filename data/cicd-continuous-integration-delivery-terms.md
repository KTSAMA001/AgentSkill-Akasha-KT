# CI/CD 持续集成与持续交付术语

**标签**：#tools #web #knowledge #cicd #github-actions #deployment
**来源**：实践总结 + 官方文档核对
**收录日期**：2026-05-25
**来源日期**：2026-05-25
**更新日期**：2026-06-13
**状态**：📘 有效
**可信度**：⭐⭐⭐⭐（官方文档 + 实践语境核对）
**适用版本**：通用 CI/CD / GitHub Actions / GitLab CI/CD / Jenkins / Buildkite

### 概要

CI/CD 是自动化构建、测试、打包、发布或部署的工程实践集合；CI 强调持续集成，CD 可指持续交付或持续部署，区别主要在最后一步是否自动上线。

### 内容

CI/CD 是一组自动化工程实践，常见展开如下：

| 缩写 | 全称 | 人话解释 |
|------|------|----------|
| CI | Continuous Integration，持续集成 | 代码频繁合入后，自动构建、自动测试，尽早发现集成问题。 |
| CD | Continuous Delivery，持续交付 | 自动把通过测试的代码准备成可发布状态，例如生成安装包、镜像或发布候选版本。 |
| CD | Continuous Deployment，持续部署 | 更进一步，代码通过测试后自动部署到目标环境，人工介入更少。 |

持续交付和持续部署的区别在于最后一步是否自动上线：

- 持续交付：系统自动准备好可发布产物，是否发布通常由人确认。
- 持续部署：通过测试后自动发布或部署到目标环境。

在实际项目里，CI/CD 可能由 GitHub Actions、GitLab CI/CD、Jenkins、Buildkite 等工具完成。典型流程是：push 代码后自动拉取依赖、编译、跑测试、打包、上传产物，必要时再部署到服务器。

#### 实践语境

在阿卡西 Web 和 Git Commit AI 工具里的语境：

- 阿卡西 Web 的 CI/CD 更偏“文档站构建和部署”：Git 变更触发构建，再通过服务器、Nginx 或 Webhook 更新站点。
- Git Commit AI 当前本地工具没有完整 CI/CD，只做了本地验证和打包；如果未来自动化，可让 CI 在提交后跑单元测试、构建 exe、生成桌面包并上传产物。

#### 与 Qt 和冒烟测试的关系

| 术语 | 所属范围 | 关注点 |
|------|----------|--------|
| Qt | GUI 开发框架 | 怎么做桌面界面。 |
| 冒烟测试 | 测试方法 | 先确认核心流程没明显坏。 |
| CI/CD | 工程自动化流程 | 自动构建、测试、打包、发布或部署。 |

三者可以组合使用：例如一个 Qt 桌面工具提交代码后，由 CI 自动构建 exe，并先跑冒烟测试确认 GUI 主路径能启动，再决定是否发布打包产物。

### 关键代码

不涉及。

### 参考链接

- [GitLab Docs: Get started with GitLab CI/CD](https://docs.gitlab.com/ci/) - CI/CD 持续构建、测试、部署与监控的工程流程说明。
- [GitLab: What is CI/CD?](https://about.gitlab.com/topics/ci-cd/) - CI/CD、持续交付与持续部署的概念解释。

### 相关记录

- [Akasha Webhook PM2 守护与 HTTPS 反向代理](./akasha-webhook-pm2-https-proxy.md) - CI/CD 在阿卡西 Web 文档站部署中的实践语境。
- [冒烟测试术语与 Qt offscreen GUI 检查](./smoke-test-term-and-offscreen-gui-check.md) - CI 中常见的快速健康检查。

### 验证记录

- [2026-05-25] 初次记录，来源为 Git Commit AI 工具讨论中对 Qt、冒烟测试、CI/CD 的术语解释需求；已与 Qt、Qt for Python、ISTQB、GitLab CI/CD 官方资料核对。
- [2026-05-25] 本地查重：阿卡西中已有 CI/CD 部署实践、Git Commit AI 工具实践、RenderDoc Qt UI 字符串记录，但没有面向术语解释的独立词条，因此新增原聚合记录并反向更新相关记录引用。
- [2026-06-13] 结构维护：从旧聚合记录拆分，未重新验证原技术结论。
---

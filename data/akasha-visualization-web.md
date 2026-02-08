# 阿卡西记录可视化网站

**标签**：#tools #web #reference #akasha
**来源**：用户 KTSAMA 提供
**来源日期**：2026-02-07
**收录日期**：2026-02-07
**更新日期**：2026-02-08
**可信度**：⭐⭐⭐⭐⭐（官方）
**状态**：📘 有效

### 定义/概念

这是阿卡西记录（Akasha-KT）技能的可视化网站，用于浏览和查询已记录的经验与知识。

### 关键点

- **网站地址**：https://akasha.ktsama.top
- **架构设计**：基于 VitePress SSG，采用 Schema 驱动的数据架构，彻底消除硬编码业务逻辑
- **视觉风格**：明日方舟（Arknights）工业风 UI，包含网点/网格背景、切角设计、SVG 图标系统
- **主要功能**：
    - **可视化浏览**：卡片式记录展示，支持按标签筛选和多维度搜索
    - **自动化部署**：通过 Webhook 实现根据 Git 变更智能触发构建（内容更新 vs 全量构建）
    - **双向同步**：前端展示与后端 Agent 技能仓库（AgentSkill-Akasha-KT）保持结构与数据的一致性
- **关联技能**：该网站是 `skill_akasha-kt` 技能的配套可视化工具

### 架构演进记录

#### 2026-02-08 UI 重构与体验优化
- **Schema 驱动**：建立 `record-template.md` 为单一信源（SSOT），驱动前端的状态颜色、图标映射和元数据解析
- **UI 规范化**：标签栏改为多行折叠式，卡片高度统一，标题/路径文字截断优化
- **视觉升级**：全面移除 Emoji，改用工业风 SVG 图标；优化全局网点背景，去除重复叠加层
- **路由修复**：Nginx 配置 `try_files` 支持 cleanUrls 模式下的页面刷新（404 修复）

### 相关知识与经验

- [Agent Skills 规范](./agent-skills-spec.md) - 阿卡西记录技能基于 Agent Skills 标准构建
- [Git 仓库管理经验](./git-commit-conventions.md) - 记录技能的版本控制与同步流程
- [持续集成/持续部署相关经验](./cicd-vitepress-deploy.md) - 网站的自动化构建与部署踩坑记录
- [明日方舟工业风 UI 分析](./arknights-ui-industrial-style.md) - 视觉设计的灵感来源与规范



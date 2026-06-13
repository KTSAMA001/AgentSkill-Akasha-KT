# 冒烟测试术语与 Qt offscreen GUI 检查

**标签**：#tools #python #knowledge #ui #troubleshooting
**来源**：实践总结 + 官方文档核对
**收录日期**：2026-05-25
**来源日期**：2026-05-25
**更新日期**：2026-06-13
**状态**：📘 有效
**可信度**：⭐⭐⭐⭐（官方文档 + 实践语境核对）
**适用版本**：通用软件测试 / Qt 6 / PySide6

### 概要

冒烟测试是软件测试里的快速健康检查，用一组最小核心路径判断程序是否值得继续测试；Qt offscreen 冒烟测试是在不真正弹出窗口的情况下检查 GUI 主路径是否能创建并运行。

### 内容

冒烟测试不追求覆盖所有功能，而是挑一组最关键路径先跑，确认程序没有“一启动就坏、核心流程走不通、构建产物不能运行”这类明显问题。

可以把它理解成：

- 完整测试之前的门槛检查。
- 新构建、新打包、新改动后的第一轮快速确认。
- 失败后通常先修基础问题，不继续投入更细的回归测试。

它不是：

- 不是完整测试。
- 不是性能测试。
- 不是“看一眼界面能打开”就结束。

#### Qt offscreen 冒烟测试语境

在 Git Commit AI 工具里，Qt offscreen 冒烟测试指不真正弹出窗口，但让 Qt 创建 GUI、切换测试项目、新建连接档案、刷新下拉框、触发重复名称提示。

这类测试验证的是 GUI 主路径没有明显崩溃或状态错乱，而不是证明所有界面细节都正确。

### 关键代码

不涉及。

### 参考链接

- [ISTQB Smoke Test Glossary](https://istqb-glossary.page/smoke-test/) - 冒烟测试术语定义。

### 相关记录

- [Qt / PySide6 GUI 框架术语](./qt-pyside6-gui-framework-terms.md) - Qt/PySide6 GUI 框架概念。
- [Git Commit AI：commit-msg Hook 日志优化工具设计与实现实践](./git-commit-ai-hook-tool-implementation.md) - Qt offscreen 冒烟测试的实践语境。

### 验证记录

- [2026-05-25] 初次记录，来源为 Git Commit AI 工具讨论中对 Qt、冒烟测试、CI/CD 的术语解释需求；已与 Qt、Qt for Python、ISTQB、GitLab CI/CD 官方资料核对。
- [2026-05-25] 本地查重：阿卡西中已有 CI/CD 部署实践、Git Commit AI 工具实践、RenderDoc Qt UI 字符串记录，但没有面向术语解释的独立词条，因此新增原聚合记录并反向更新相关记录引用。
- [2026-06-13] 结构维护：从旧聚合记录拆分，未重新验证原技术结论。
---

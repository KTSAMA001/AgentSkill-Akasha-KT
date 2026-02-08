# Git 团队协作工作流相关经验

> Git 团队协作工作流相关经验
>
> 包含：分支策略、PR 流程、代码审查、发布流程等

---

## Git 提交消息规范 - Conventional Commits

**日期**：2026-01-30
**标签**：#git #reference #conventional-commits
**状态**：✅ 已验证
**参考**：[conventionalcommits.org](https://www.conventionalcommits.org/)

**问题/场景**：

需要统一 Git 提交消息的风格，使 commit 历史清晰易读，并支持自动化工具（如自动生成 CHANGELOG、语义化版本）。

**解决方案/结论**：

### 基本格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type 类型（必需）

| Type | 含义 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat: 添加用户登录功能` |
| `fix` | 修复 bug | `fix: 修复对象池内存泄漏` |
| `docs` | 文档修改 | `docs: 更新 README 说明` |
| `style` | 代码格式（不影响功能） | `style: 统一代码缩进` |
| `refactor` | 重构 | `refactor: 重构 Entity 获取方式` |
| `perf` | 性能优化 | `perf: 优化寻路算法` |
| `test` | 测试相关 | `test: 添加单元测试` |
| `chore` | 构建/工具相关 | `chore: 升级依赖包` |
| `revert` | 回退提交 | `revert: feat: xxx` |

### Scope（可选）

说明提交影响的模块，例如：

```
feat(core): 添加实体系统
fix(pool): 修复对象池回收问题
docs(api): 更新 API 文档
```

### Subject（必需）

- 使用现在时态（如 "add" 而非 "added"）
- 首字母小写
- 结尾不加句号

### Body（可选）

详细说明本次提交的内容，可分多行：

```
feat(skills): 添加投射物自动回收逻辑

解决了对象池生成的投射物可能未被正确回收的问题，
添加了生命周期监听机制，确保超时后自动调用 Despawn。
```

### Footer（可选）

用于关联 Issue 或 BREAKING CHANGE：

```
feat(api): 移除已废弃的 API

BREAKING CHANGE: 移除了 Entity.GetFeature() 方法，
请改用 Entity.FindFeature<T>()

Closes #123
```

### 完整示例

```
feat(skills): 添加投射物自动回收逻辑

解决了对象池生成的投射物可能未被正确回收的问题，
添加了生命周期监听机制。

- 实现 SkillEffect 生命周期监听
- 超时自动调用 PoolService.Despawn()
- 添加单元测试

Closes #123
```

### 版本影响

| Type | 版本变化 |
|------|---------|
| `feat` | MINOR 版本升级 (0.1.0 → 0.2.0) |
| `fix` | PATCH 版本升级 (0.1.0 → 0.1.1) |
| 带有 `BREAKING CHANGE` | MAJOR 版本升级 (0.1.0 → 1.0.0) |

### 常用命令

```bash
# 只看新功能
git log --oneline --grep="feat"

# 只看修复
git log --oneline --grep="fix"

# 查看特定模块
git log --oneline --grep="core"

# 使用工具自动生成 CHANGELOG
npm install -g conventional-changelog-cli
conventional-changelog -p angular -i CHANGELOG.md -s
```

**参考链接**：

- [Conventional Commits 官方规范](https://www.conventionalcommits.org/)
- [Angular 提交规范](https://github.com/angular/angular/blob/main/CONTRIBUTING.md#commit)

**验证记录**：

- [2026-01-30] 初次记录，来源：[Conventional Commits 官方文档](https://www.conventionalcommits.org/)

**备注**：

此规范广泛应用于开源项目（Angular、React、Vue 等），适合团队协作项目。对于个人项目，也可以采用简化版，只保留 `<type>: <subject>` 格式。

---

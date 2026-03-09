# Git 配置跟随仓库持久化

> 创建时间：2026-03-09
> 标签：#git #docker #配置管理 #持久化

## 问题场景

Docker 容器重建后，`~/.gitconfig` 丢失，需要重新配置 `credential.helper` 等设置。

## 解决方案

**将 Git 配置写入仓库内的 `.git/config`**，而非全局 `~/.gitconfig`：

```bash
# 在仓库目录下执行
cd /path/to/repo
git config credential.helper "store --file /path/to/credentials/.git-credentials"
```

## 原理

| 配置位置 | 作用域 | 持久化 |
|----------|--------|--------|
| `~/.gitconfig` | 全局（所有仓库） | ❌ 容器重建丢失 |
| `.git/config` | 当前仓库 | ✅ 随仓库持久化 |

## 适用条件

1. 仓库本身在持久化目录（挂载卷）
2. 凭证文件也在持久化位置

## 配置示例

```ini
# .git/config
[credential]
    helper = store --file /astrbot_data/.git-credentials
```

## 优缺点

**优点**：
- 无需额外脚本或软链接
- 容器重建后直接可用
- 配置与仓库绑定，便于迁移

**缺点**：
- 每个仓库需要单独配置
- 凭证路径硬编码在仓库配置中

## 替代方案

- **全局配置 + 软链接**：将 `~/.gitconfig` 放到挂载卷，用脚本重建软链接
- **环境变量**：`GIT_CONFIG_GLOBAL` 指向挂载卷中的配置文件
- **Git Credential Manager**：使用外部凭证管理器

---

_来源：2026-03-09 OpenClaw 容器环境实践_

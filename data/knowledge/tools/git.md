# Git 知识

> Git 相关知识：凭据管理、协议、配置等
>
> 修改记录：
> - [2026-02-05] 初始记录，Docker 容器内 Git 凭据持久化配置
> - [2026-02-05] 新增 macOS osxkeychain credential helper 配置

---

## Docker 内 Git PAT 凭据隐藏且持久化 {#docker-git-credential}

**分类**：tools > git
**关键词**：#git #pat #credential-helper #docker #https
**来源**：实践记录
**收录日期**：2026-02-05
**可信度**：⭐⭐⭐（个人实践验证）
**状态**：📘 有效

### 定义/概念

在 Docker 容器中使用 Git over HTTPS 时，通过 `credential.helper store` 将 PAT 凭据写入宿主机挂载文件，实现"远程地址不含明文 token，且容器重启后仍可推送"。

### 原理/详解

`credential.helper store` 会把凭据写入指定文件。将该文件放在容器挂载卷（如 `/AstrBot/data/.git-credentials`）即可持久化。Git 远程 URL 使用无 token 的 HTTPS 地址，凭据由 helper 提供，避免 URL 明文泄露。

### 关键点

- 远程地址应为无 token 的 HTTPS：`https://github.com/<user>/<repo>.git`
- 将凭据文件放在挂载卷（宿主机持久化）
- 凭据文件权限建议 `600`
- 已暴露的 PAT 应立即撤销，重新生成

### 示例

```bash
# 宿主机创建凭据文件并限制权限
touch /path/to/mounted/.git-credentials
chmod 600 /path/to/mounted/.git-credentials

# 容器内配置凭据存储到挂载文件
git config --global credential.helper "store --file /container/path/.git-credentials"

# 远程地址保持干净（无 token）
git remote set-url origin https://github.com/<user>/<repo>.git

# 第一次 push 时按提示输入用户名与 PAT，凭据会写入挂载文件
git push origin main
```

### 相关知识

- [macOS osxkeychain 配置](#macos-osxkeychain)

---

## macOS Git Credential Helper 配置 {#macos-osxkeychain}

**分类**：tools > git
**关键词**：#git #credential-helper #macos #osxkeychain #homebrew
**来源**：实践记录
**收录日期**：2026-02-05
**可信度**：⭐⭐⭐（个人实践验证）
**状态**：📘 有效

### 定义/概念

macOS 上 Git 可通过 `git-credential-osxkeychain` 将凭据安全存储在系统钥匙串中，避免明文存储或反复输入。

### 原理/详解

Homebrew 安装的 Git，其 credential helper 位于 `$(git --exec-path)/git-credential-osxkeychain`。若简写 `osxkeychain` 无法识别（报 `not a git command`），需使用完整路径配置。

### 关键点

- **Homebrew Git 路径**：`/opt/homebrew/opt/git/libexec/git-core/git-credential-osxkeychain`
- 若 `git credential-osxkeychain` 报错，检查是否在 PATH 或使用完整路径
- 凭据存储在 macOS 钥匙串，可通过"钥匙串访问"应用查看/删除
- 清除 Keychain 中的 GitHub 凭据会导致所有仓库认证失败

### 示例

```bash
# 检查 credential helper 是否可用
which git-credential-osxkeychain

# 查找实际位置
ls -la "$(git --exec-path)" | grep credential

# 使用完整路径配置（Homebrew Git）
git config --global credential.helper /opt/homebrew/opt/git/libexec/git-core/git-credential-osxkeychain

# 或简写（如果 PATH 正确）
git config --global credential.helper osxkeychain

# 清除缓存的凭据（需重新输入 PAT）
printf "protocol=https\nhost=github.com\n\n" | git credential-osxkeychain erase
```

### 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| `git: 'credential-osxkeychain' is not a git command` | helper 不在 PATH | 使用完整路径配置 |
| `Authentication failed` | PAT 过期或无效 | 重新生成 PAT，删除钥匙串中旧条目 |
| 多仓库认证失败 | 清除了 Keychain 凭据 | 重新配置 helper 并输入有效 PAT |

### 相关知识

- [Docker 内 Git 凭据配置](#docker-git-credential)
- 另见：[Git 问题解决经验](../../experiences/git/troubleshooting.md)

---

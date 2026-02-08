# macOS Git osxkeychain Credential Helper 路径问题 {#osxkeychain-path}

**来源**：KTSAMA 实践经验
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐ (实践验证)6-02-05
**标签**：#git #experience #pat #docker #credential
**状态**：✅ 已验证
**适用版本**：Git 2.x+ (Homebrew)

**问题/场景**：

在 macOS 上使用 Homebrew 安装的 Git，配置 `credential.helper osxkeychain` 后执行 git 操作报错：
- `git: 'credential-osxkeychain' is not a git command`
- `fatal: Authentication failed`

同时清除 Keychain 凭据后，多个仓库同时失去认证能力。

**解决方案/结论**：

问题根源是 `git-credential-osxkeychain` 可执行文件不在系统 PATH 中，但存在于 Git 的 exec-path 目录。需使用完整路径配置。

### 1. 确认 credential helper 位置

```bash
# 查找 Git 的 exec-path
git --exec-path
# 输出示例：/opt/homebrew/opt/git/libexec/git-core

# 确认 credential helper 存在
ls -la "$(git --exec-path)" | grep credential
# 应看到 git-credential-osxkeychain 文件
```

### 2. 使用完整路径配置

```bash
# 配置完整路径（Homebrew Git on Apple Silicon）
git config --global credential.helper /opt/homebrew/opt/git/libexec/git-core/git-credential-osxkeychain
```

> 📌 Intel Mac 路径可能是 `/usr/local/opt/git/libexec/git-core/git-credential-osxkeychain`

### 3. 验证配置

```bash
# 测试 push（第一次会提示输入用户名和 PAT）
git push origin main
```

**⚠️ 注意事项**：

- **不要随意清除 Keychain 凭据**：会导致所有使用该凭据的仓库认证失败
- PAT 需要 `repo` 权限才能 push
- GitHub 已禁用密码认证（2021年起），必须使用 PAT

**验证记录**：

- [2026-02-05] 通过完整路径配置解决了多仓库认证问题

**相关经验**：

- [Docker 容器内 Git 凭据配置](./docker-git-credential-persist.md)

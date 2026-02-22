# Docker 容器重建后 Git 认证持久化配置 {#docker-git-auth-persist}

**标签**：#git #experience #docker #credential #troubleshooting
**来源**：KTSAMA & 璃 实践总结
**收录日期**：2026-02-22
**来源日期**：2026-02-22
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐⭐ (实践验证)
**适用版本**：Git 2.x+, Docker 容器环境

**问题/场景**：

在 Docker 容器中运行 Git 操作时，容器重建后出现认证失败：
- `fatal: could not read Username for 'https://github.com': No such device or address`
- `fatal: Authentication failed`

**根本原因**：
1. Docker 容器重建后，`~/.gitconfig`（Git 全局配置）丢失
2. 凭证文件若保存在挂载卷中（如 `/AstrBot/data/.git-credentials`）会幸存
3. 但 Git 没有配置指向该凭证文件，导致无法找到认证信息

**解决方案/结论**：

### 核心步骤

```bash
# 配置 Git 使用挂载卷中的凭证文件
git config --global credential.helper "store --file /AstrBot/data/.git-credentials"
```

### 完整排查流程

```bash
# 1. 确认容器环境
cat /proc/1/cgroup | head -1
ls -la /.dockerenv

# 2. 检查 Git 配置状态
git config --global --list
git config --global credential.helper

# 3. 检查凭证文件是否存在
ls -la /AstrBot/data/.git-credentials
cat /AstrBot/data/.git-credentials

# 4. 配置凭证 helper
git config --global credential.helper "store --file /AstrBot/data/.git-credentials"

# 5. 验证配置
git config --global --list | grep credential

# 6. 测试 Git 操作
cd /path/to/repo
git pull origin main
git push origin main
```

### 自动化方案（推荐）

将配置命令添加到容器启动脚本中，实现自动配置：

```bash
# 在容器启动脚本（如 entrypoint.sh）中添加
if [ -f /AstrBot/data/.git-credentials ]; then
    git config --global credential.helper "store --file /AstrBot/data/.git-credentials"
    echo "✅ Git 凭证配置完成"
fi
```

**关键点**：

- ✅ 凭证文件必须保存在**挂载卷**中（容器外持久化）
- ✅ 凭证文件权限建议 `600`（仅所有者可读写）
- ✅ 远程 URL 应为干净的 HTTPS 格式（不含 token）
- ⚠️ 容器重建后需重新配置 `credential.helper`
- ⚠️ 若凭证文件也不存在，需重新执行一次 `git push` 生成

**验证记录**：

- [2026-02-22] AstrBot Docker 容器内实践验证成功
  - Pull 测试：✅ 正常
  - Push 测试：✅ 正常
  - 警告：`unable to get credential storage lock` 不影响功能

**相关经验**：

- [Docker 容器内 Git PAT 凭证持久化配置](./docker-git-credential-persist.md)
- [macOS Git osxkeychain 路径问题](./macos-git-osxkeychain-path.md)
- [Git HTTPS 失败改用 SSH](./git-https-fail-switch-ssh.md)

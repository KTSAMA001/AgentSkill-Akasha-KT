# Docker 容器内 Git PAT 凭据持久化配置 {#docker-git-credential}

**标签**：#git #experience #pat #docker #credential
**来源**：KTSAMA 实践经验
**收录日期**：2026-02-05
**来源日期**：2026-02-05
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐ (实践验证)
**适用版本**：Git 2.x+

**问题/场景**：

在 Docker 容器中使用 Git over HTTPS 时，需要实现：
- 远程地址不含明文 token（安全）
- 容器重启后凭据仍然有效（持久化）

**解决方案/结论**：

使用 `credential.helper store` 将 PAT 凭据写入宿主机挂载文件。

### 1. 宿主机创建凭据文件

```bash
# 创建凭据文件并限制权限
touch /path/to/mounted/.git-credentials
chmod 600 /path/to/mounted/.git-credentials
```

### 2. 容器内配置凭据存储

```bash
# 配置 credential helper 指向挂载文件
git config --global credential.helper "store --file /container/path/.git-credentials"

# 确保远程地址干净（无 token）
git remote set-url origin https://github.com/<user>/<repo>.git
```

### 3. 首次推送

```bash
# 第一次 push 时按提示输入用户名与 PAT
# 凭据会自动写入挂载文件，后续无需再输入
git push origin main
```

**关键点**：

- 远程地址应为无 token 的 HTTPS：`https://github.com/<user>/<repo>.git`
- 凭据文件放在挂载卷（宿主机持久化）
- 凭据文件权限建议 `600`
- 已暴露的 PAT 应立即撤销，重新生成

**验证记录**：

- [2026-02-05] AstrBot 容器内实践验证成功

**相关经验**：

- [macOS osxkeychain 路径问题](./macos-git-osxkeychain-path.md)

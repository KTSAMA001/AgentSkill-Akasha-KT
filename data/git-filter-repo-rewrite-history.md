# 使用 git-filter-repo 重写提交历史（清除敏感信息）

**收录日期**：2026-01-29
**标签**：#git #experience #pat #docker #credential
**来源**：KTSAMA 实践经验
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐ (实践验证)

**问题/场景**：

需要从 Git 历史中批量替换作者名称/邮箱，清除敏感信息（如真实姓名、公司邮箱），并将所有历史提交的作者统一替换为新的身份信息。

**解决方案/结论**：

推荐使用官方推荐的 `git-filter-repo` 工具，比 `git filter-branch` 更快更安全。

### 1. 安装 git-filter-repo

```powershell
pip install git-filter-repo
```

### 2. 创建邮箱映射文件（mailmap）

创建 `mailmap.txt`，格式为：`新名称 <新邮箱> 旧名称 <旧邮箱>`

```text
<新用户名> <新邮箱@example.com> <旧用户名> <旧邮箱@company.com>
```

> 📌 **格式要点**：新信息在前，旧信息在后（与 `.mailmap` 文件格式一致）

### 3. 执行历史重写

```powershell
git filter-repo --mailmap mailmap.txt --force
```

**命令说明**：
- `--mailmap`：指定映射文件
- `--force`：强制执行（跳过"仓库不是全新克隆"的警告）

### 4. 重新添加远程仓库

> ⚠️ `git-filter-repo` 会自动移除 `origin` 远程，防止误推送

```powershell
git remote add origin https://github.com/<用户名>/<仓库名>.git
```

### 5. 强制推送到远程

```powershell
git push origin main --force
```

> ⚠️ **警告**：强制推送会覆盖远程历史，协作仓库需提前通知所有成员！

### 完整脚本示例

```powershell
cd "目标仓库目录"

# 1. 创建映射文件
@"
KTSAMA <ktsama@example.com> KTSAMA_Old <old@company.com>
"@ | Out-File -Encoding utf8NoBOM mailmap.txt

# 2. 执行重写
git filter-repo --mailmap mailmap.txt --force

# 3. 重新添加远程
git remote add origin https://github.com/KTSAMA001/Repo.git

# 4. 强制推送
git push origin main --force

# 5. 清理与配置
Remove-Item mailmap.txt
git config user.name "KTSAMA"
git config user.email "ktsama@example.com"
```

**验证记录**：

- [2026-01-29] 实践验证成功。

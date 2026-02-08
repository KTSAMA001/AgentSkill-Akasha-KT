# Git 常见问题解决相关经验

> Git 常见问题解决相关经验
>
> 包含：冲突解决、回滚操作、历史修改、误操作恢复、凭据配置等

---

## Docker 容器内 Git PAT 凭据持久化配置 {#docker-git-credential}

**日期**：2026-02-05
**标签**：#git #experience #pat #docker #credential
**状态**：✅ 已验证
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

- [macOS osxkeychain 路径问题](#osxkeychain-path)

---

## 使用 git-filter-repo 重写提交历史（清除敏感信息）

**日期**：2026-01-29
**标签**：#git #experience #pat #docker #credential
**状态**：✅ 已验证

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

---

## Git HTTPS 拉取失败，改用 SSH 协议解决

**日期**：2026-01-30  
**标签**：#git #experience #pat #docker #credential
**状态**：✅ 已验证  
**适用版本**：Git 2.x+

**问题/场景**：

在已存在的 Git 仓库执行 `git pull` 或 `git fetch` 时报错：
- `fatal: unable to access 'https://xxx.git/': Recv failure: Connection was aborted`
- `fatal: unable to access 'https://xxx.git/': Recv failure: Connection was reset`

但将仓库**克隆到新位置却可以成功**，通常是因为 HTTPS 连接不稳定或被拦截。

**解决方案/结论**：

最有效的方案是将远程 URL 从 HTTPS 改为 SSH。

### 1. 将 HTTPS URL 改为 SSH URL

```powershell
# 查看当前远程配置
git remote -v

# 将 HTTPS URL 改为 SSH URL
git remote set-url origin git@你的gitlab地址:命名空间/仓库名.git
```

**URL 格式对照**：
- HTTPS: `https://gitlab.com/group/repo.git`
- SSH: `git@gitlab.com:group/repo.git`

### 2. 验证与拉取

```powershell
# 再次尝试拉取
git fetch origin
git pull
```

### 处理本地修改冲突

切换协议后，如果 `git pull` 报本地修改冲突：

```powershell
# 方案：暂存本地修改
git stash
git pull
git stash pop
```

**验证记录**：

- [2026-01-30] 初次记录，来源：实践总结。在公司内网 GitLab 仓库遇到此问题，HTTPS 持续失败，改 SSH 后立即解决。
- [2026-01-30] 再次验证：如果不处理本地修改直接 Pull 可能会失败，建议配合 Stash 使用。

---

## macOS Git osxkeychain Credential Helper 路径问题 {#osxkeychain-path}

**日期**：2026-02-05
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

- [Docker 容器内 Git 凭据配置](#docker-git-credential)

---

## Git 对象损坏（loose object corrupt）修复 {#git-object-corrupt}

**日期**：2026-02-05
**标签**：#git #experience #pat #docker #credential
**状态**：⚠️ 解决方案已验证，根因待查
**适用版本**：Git 2.x+

**问题/场景**：

Git 操作时报错：
```
error: inflate: data stream error (incorrect header check)
error: unable to unpack f91781d579577a6c5a9fd52b01e3799ba3f755ea header
fatal: loose object f91781d579577a6c5a9fd52b01e3799ba3f755ea is corrupt
```

删除 `.git/objects/` 下的损坏文件后，错误变为：
```
error: unable to read sha1 file of Unity/Proj.../NC_PolygonClub_01.png (f91781d...)
```

**根因分析**：

`.git/objects/` 目录存储的是 Git 对象（blob/tree/commit），格式为：
```
zlib压缩( "blob " + 文件大小 + "\0" + 文件原始内容 )
```

**可能的损坏原因**（未确认）：
- 磁盘 I/O 错误、坏道
- 网络传输中断（clone/fetch 过程中断电、断网）
- 杀毒软件误操作或实时扫描干扰
- 文件系统损坏
- Git 进程异常终止

> ⚠️ **待查**：本次案例的实际触发原因未能确定，仅验证了修复方法有效。

**解决方案**：

### 方案一：从其他正常仓库恢复（推荐）

如果团队其他成员有正常的仓库：

```bash
# 1. 从正常仓库导出原始文件
git show f91781d579577a6c5a9fd52b01e3799ba3f755ea > NC_PolygonClub_01.png

# 2. 把文件发给损坏方
```

损坏方收到文件后：

```bash
# 1. 删除损坏的对象（如果还在）
rm -f .git/objects/f9/1781d579577a6c5a9fd52b01e3799ba3f755ea

# 2. 用 hash-object 重建对象（关键步骤）
git hash-object -w NC_PolygonClub_01.png
# 输出：f91781d579577a6c5a9fd52b01e3799ba3f755ea

# 3. 验证
git cat-file -t f91781d579577a6c5a9fd52b01e3799ba3f755ea
# 输出：blob

# 4. 继续正常操作
git pull
```

### 方案二：从远程强制恢复（通常无效）

```bash
# 尝试从远程获取缺失对象
git fetch origin
git reset --hard origin/dev
```

⚠️ **实测结论**：此方案在对象已损坏/删除的情况下**通常无效**。
- `git fetch` 和 `git reset` 都需要读取本地对象来计算差异
- 损坏的对象会导致这些命令本身报错终止
- 只有在损坏对象恰好不在当前操作路径上时才可能成功

### 方案三：重新克隆（终极方案）

```bash
# 1. 备份当前修改
mv repo repo_broken

# 2. 重新克隆
git clone <仓库地址> repo

# 3. 手动复制备份中的修改
```

**关键知识点**：

| 要点 | 说明 |
|------|------|
| Git 对象哈希 | 只取决于**文件内容**，与路径/文件名无关 |
| 不能直接覆盖 | `.git/objects/` 文件是压缩格式，不能用原文件覆盖 |
| `hash-object -w` | 正确方式：读取文件 → 加头 → 压缩 → 写入对象库 |
| 同内容同哈希 | 相同内容的文件在任何位置执行 `hash-object` 结果一致 |

**验证记录**：

- [2026-02-05] 同事仓库损坏，通过 `git hash-object -w` 从正常仓库导出文件重建对象，成功修复

**相关经验**：

- [git-filter-repo 重写历史](#git-filter-repo-rewrite)

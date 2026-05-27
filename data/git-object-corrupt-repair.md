# Git 对象损坏（loose object corrupt）修复 {#git-object-corrupt}

**标签**：#git #windows #tools #experience #troubleshooting
**来源**：KTSAMA 实践经验
**收录日期**：2026-02-05
**来源日期**：2026-02-05
**更新日期**：2026-05-27
**状态**：🔄 待更新
**可信度**：⭐⭐⭐⭐ (修复流程已多轮验证，根因仍需现场确认)
**适用版本**：Git 2.x+

### 概要
当 Git loose object 损坏时，可以隔离损坏对象后从远端重新补拉，或从正常仓库重新写回缺失对象完成修复；但真实触发根因通常仍需结合现场磁盘、杀软、网络中断等因素继续确认。

**问题/场景**：
Git 操作时报错：
```
error: inflate: data stream error (incorrect header check)
error: unable to unpack f91781d579577a6c5a9fd52b01e3799ba3f755ea header
fatal: loose object f91781d579577a6c5a9fd52b01e3799ba3f755ea is corrupt
```

Fork / GUI Git 客户端在拉取时也可能表现为：
```
Resolving deltas: ...
error: inflate: data stream error (incorrect header check)
error: unable to unpack <object-id> header
fatal: cannot read existing object info <object-id>
fatal: fetch-pack: invalid index-pack output
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

### 方案一：隔离损坏 loose object 后重新补拉（推荐优先尝试）

适用条件：
- `git fsck --full --no-progress --no-dangling` 能定位到损坏对象哈希。
- 损坏对象在 `.git/objects/<前两位>/<后38位>` 中以 loose object 形式存在。
- 远端仓库正常，且当前账号可以正常 fetch。

处理流程：
```bash
# 1. 全仓检查并记录损坏对象
git fsck --full --no-progress --no-dangling

# 2. 不直接删除，先移动到隔离目录
mkdir -p .git/repair-quarantine/<timestamp>/objects/<前两位>
mv .git/objects/<前两位>/<后38位> .git/repair-quarantine/<timestamp>/objects/<前两位>/<后38位>.corrupt

# 3. 从远端补拉对象；支持 --refetch 的 Git 版本优先使用
git fetch --all --tags --force --refetch --no-auto-maintenance

# 4. 再次验证
git fsck --full --no-progress --no-dangling
```

注意：
- 只移动明确定位到的 loose object，不主动搬移 pack 文件。
- 若 Git 版本不支持 `--refetch`，可退回普通 `git fetch --all --tags --force --no-auto-maintenance`，但对已缺失对象的补拉能力较弱。
- 若最终 fsck 仍失败，优先保留损坏仓库作为备份，再重新克隆。

### 方案二：从其他正常仓库恢复单个 blob

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

### 方案三：普通 fetch/reset 强制恢复（通常无效）

```bash
# 尝试从远程获取缺失对象
git fetch origin
git reset --hard origin/dev
```

⚠️ **实测结论**：此方案在对象已损坏/删除的情况下**通常无效**。
- `git fetch` 和 `git reset` 都需要读取本地对象来计算差异
- 损坏的对象会导致这些命令本身报错终止
- 只有在损坏对象恰好不在当前操作路径上时才可能成功

### 方案四：重新克隆（终极方案）

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
| `git fsck` | 用于定位对象库损坏、缺失和连通性问题 |
| `--refetch` | 在支持的 Git 版本中可按 fresh clone 方式重新获取对象，适合补拉被隔离的对象 |

### 验证记录
- [2026-02-05] 同事仓库损坏，通过 `git hash-object -w` 从正常仓库导出文件重建对象，成功修复
- [2026-05-09] Codex 在隔离 Git 仓库中人为破坏 loose blob object，复现 `inflate: data stream error`、`unable to unpack ... header`、`loose object ... is corrupt` 同类报错，并验证本地 bat 工具的 `find`/`write` 流程可将对象写回，修复后 `git show <objectId>` 与 `git fsck --full` 均通过。该验证仅覆盖隔离测试环境，尚未代表真实项目仓库或用户现场已验证。
- [2026-05-27] 在项目现场截图中复现 Fork 拉取时报 `inflate: data stream error`、`cannot read existing object info`、`fetch-pack: invalid index-pack output` 的诊断路径；正常仓库中对应对象可被 `git cat-file -t` 解析为 tree，`git fsck --full --no-progress` 退出码为 0，仅有 dangling 对象，支持“同事本地对象库损坏而非远端整体损坏”的判断。
- [2026-05-27] Codex 在隔离 Git 仓库中构造损坏 loose blob object，验证自动化流程：`git fsck` 定位对象 → 移动到 `.git/repair-quarantine/<timestamp>/` → `git fetch --all --tags --force --refetch --no-auto-maintenance` 补拉 → 再次 `git fsck` 退出码为 0。该验证覆盖 loose object 损坏自动修复路径，不覆盖 pack 内部严重损坏。
- [2026-05-27] 将自动修复流程整理为 Windows 双击工具：普通用户选择项目文件夹后自动检查、隔离、补拉、复验；用户反馈工具可用。工具提示语调整为“修复完成，可以回到 Fork 再次拉取更新”，避免误导用户认为需要直接打开 Unity 项目。

**相关经验**：

- [git-filter-repo 重写历史](./git-filter-repo-rewrite-history.md)

### 参考链接

- [git-fsck 官方文档](https://git-scm.com/docs/git-fsck) - 对对象数据库执行连通性与有效性检查
- [git-fetch 官方文档](https://git-scm.com/docs/git-fetch) - 从远端下载对象与引用，包含 `--refetch` 选项说明

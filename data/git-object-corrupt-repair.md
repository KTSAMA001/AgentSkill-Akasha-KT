# Git 对象损坏（loose object corrupt）修复 {#git-object-corrupt}

**来源**：KTSAMA 实践经验
**状态**：⚠️ 解决方案已验证，根因待查
**可信度**：⭐⭐⭐ (解决方案有效)
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

- [git-filter-repo 重写历史](./git-filter-repo-rewrite-history.md)

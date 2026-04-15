# Git 三方合并：合并基点不存在的文件不会被误删

**标签**：#git #experience
**来源**：实践分析 + StackOverflow 验证
**收录日期**：2026-04-08
**更新日期**：2026-04-08
**状态**：⚠️ 待验证
**可信度**：⭐⭐⭐（社区公认原理，但具体场景尚未实际合并验证）
**适用版本**：Git 2.x+

### 概要
当一个文件在合并基点（merge base）上**不存在**时，即使当前分支曾经添加后又 `git rm` 删除了该文件，合并到目标分支时 **不会** 导致目标分支的同名文件被删除。Git 三方合并只比较最终快照与合并基点的差异，不追踪中间历史。

### 内容

#### 背景场景

项目中 `v_2.06/release/release-candidate` 分支从 dev 拉取时，dev 上不存在某批 `.prefab.meta` 文件。后来一次批量处理提交（`6e15cac07`）错误地将这些 `.meta` 文件新增到了当前分支。而 dev 分支后来独立地添加了这些美术资源（含 `.prefab` 和对应 `.meta`）。

需要在当前分支上 `git rm` 这些错误引入的 `.meta` 文件，但担心合并回 dev 时会把 dev 上的文件也删掉。

#### 核心原理：Git 三方合并只看快照

Git merge 使用**三方合并**（3-way merge），比较三棵树：

```
                   合并基点（merge base）
                  /                     \
        当前分支 tip                    目标分支 tip
```

对每个文件路径，Git 只对比**三个点的最终状态**，不看中间经过了什么：

| | 合并基点 | 当前分支 tip | 目标分支 tip | 合并结果 |
|---|---|---|---|---|
| 场景 A | 不存在 | 不存在（git rm 后） | 存在（独立添加） | ✅ 采纳目标分支版本 |
| 场景 B | 不存在 | 不存在 | 不存在 | 无变化 |
| 场景 C | 存在 | 删除 | 存在（未修改） | ⚠️ 自动删除（危险） |
| 场景 D | 存在 | 删除 | 存在（有修改） | ⚠️ 冲突（delete/modify） |

**关键区分**：
- **场景 A**（本次情况）：合并基点没有文件 → 当前分支状态和基点一样（都没有）→ Git 认为当前分支"没动过" → 只有目标分支新增了 → **采纳目标分支，零冲突**
- **场景 C/D**（需要警惕）：合并基点有文件 → 当前分支删了 → Git 认为当前分支"主动删除" → 可能删除目标分支的文件或产生冲突

#### 判断关键：合并基点上文件是否存在

```bash
# 找到合并基点
git merge-base <当前分支> <目标分支>

# 检查文件在合并基点上是否存在
git show <merge-base-hash>:<文件路径>
# 如果报 "does not exist"，说明是场景 A → git rm 安全
# 如果正常输出文件内容，说明是场景 C/D → git rm 有风险
```

#### 常见误解

> ❌ "git rm 会在历史里留下一条删除记录，合并时会以最新的为准把对方也删了"

这是错误的。Git merge **不比较时间戳**，不看"谁的提交更新"。它只做两组对比：
1. 合并基点 vs 当前分支 tip → 得出"当前分支改了什么"
2. 合并基点 vs 目标分支 tip → 得出"目标分支改了什么"
3. 合并两组变更 → 只有一方改了就采纳该方，双方都改了才冲突

### 关键代码

```bash
# 验证合并基点上文件是否存在
git merge-base HEAD origin/dev
# 假设输出 abc123

git show abc123:"path/to/file.meta"
# fatal: path 'path/to/file.meta' does not exist in 'abc123'
# → 合并基点不存在 → git rm 安全

# 执行 git rm
git rm "path/to/file.meta"
git commit -m "Fixed: 移除被错误引入的 .meta 文件"

# 合并前可做模拟验证（不实际合并）
git merge --no-commit --no-ff origin/dev
# 确认目标分支的文件被保留
git merge --abort
```

### 参考链接

- [What happens in git merge if one file does not exist in merged branch - StackOverflow](https://stackoverflow.com/questions/76105594/what-happens-in-git-merge-if-one-file-does-not-exist-in-merged-branch) - 核心原理："if A added some files that were not in the merge base and B didn't, the result will be that the files exist in the result"
- [Merging two branches A and B where A contains files that were deleted from B - StackOverflow](https://stackoverflow.com/questions/37151268/merging-two-branches-a-and-b-where-a-contains-files-that-were-deleted-from-b) - 文件删除在合并中的行为
- [Files getting deleted in GIT while merging - StackOverflow](https://stackoverflow.com/questions/60219219/files-getting-deleted-in-git-while-merging) - 合并时文件被删除的原因分析

### 相关记录

- [Git 团队协作工作流相关经验](./git-commit-conventions.md) - Git 工作流规范

### 验证记录
- [2026-04-08] 初次记录。通过 StackOverflow 多个问答交叉验证了三方合并原理，确认合并基点不存在的文件执行 `git rm` 后合并安全。**但尚未执行实际的 `git merge` 操作验证**，标记为 ⚠️ 待验证，需在后续实际合并分支时确认结果。

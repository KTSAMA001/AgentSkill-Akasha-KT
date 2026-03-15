# 阿卡西记录工作流测试

**标签**：#akasha #tools #测试 #experience
**来源**：实践总结
**收录日期**：2026-03-15
**来源日期**：2026-03-15
**更新日期**：2026-03-15
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐⭐ (官方流程)

### 概要

验证阿卡西记录的完整记录流程是否正常工作，包括 git pull → 验证检查 → 写入 data/ → 更新 INDEX.md → git commit & push。

### 内容

#### 测试目的

验证阿卡西记录 skill 的记录流程（workflows/record.md）是否能正确执行。

#### 流程步骤

| 步骤 | 操作 | 状态 |
|------|------|------|
| 1 | git pull origin main | ✅ |
| 2 | 读取 workflows/validate.md | ✅ |
| 3 | 读取 templates/record-template.md | ✅ |
| 4 | 执行重复检测 | ✅ |
| 5 | 按模板格式写入 data/ | ✅ |
| 6 | 更新 references/INDEX.md | ✅ |
| 7 | git commit | ✅ |
| 8 | git push origin main | ✅ |

#### 验证结果

- ✅ git pull 正常同步
- ✅ data/ 目录写入成功
- ✅ INDEX.md 更新成功
- ✅ git push 推送成功

### 关键代码

```bash
# 完整流程命令
cd /path/to/akasha-kt
git pull origin main
# ... 验证和写入 ...
git add data/xxx.md references/INDEX.md
git commit -m "docs: add [文件名]"
git push origin main
```

### 参考链接

- [记录流程](../references/workflows/record.md)
- [验证流程](../references/workflows/validate.md)
- [记录模板](../references/templates/record-template.md)

### 相关记录

无

### 验证记录

- [2026-03-15] 初次记录，来源：实践验证
- [2026-03-15] 流程验证通过，git push 成功

---

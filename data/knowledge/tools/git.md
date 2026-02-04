# Git 知识
<!-- 
修改记录：
- [2026-02-05] 记录 Docker 容器内 Git 凭据持久化与隐藏配置要点，便于后续推送测试与复用。
---

```markdown
## Docker 内 Git PAT 凭据隐藏且持久化

**分类**：tools > git
**关键词**：#git #pat #credential-helper #docker #https
**来源**：实践记录（容器内 Git 推送与凭据存储）
**来源日期**：2026-02-05
**收录日期**：2026-02-05
**更新日期**：2026-02-05
**可信度**：⭐⭐（个人实践）
**状态**：📘 有效

### 定义/概念

在 Docker 容器中使用 Git over HTTPS 时，通过 `credential.helper store` 将 PAT 凭据写入宿主机挂载文件，实现“远程地址不含明文 token，且容器重启后仍可推送”。

### 原理/详解

`credential.helper store` 会把凭据写入指定文件。将该文件放在容器挂载卷（如 `/AstrBot/data/.git-credentials`）即可持久化。Git 远程 URL 使用无 token 的 HTTPS 地址，凭据由 helper 提供，避免 URL 明文泄露。

### 关键点

- 远程地址应为无 token 的 HTTPS：`https://github.com/<user>/<repo>.git`
- 将凭据文件放在挂载卷（宿主机持久化）
- 凭据文件权限建议 `600`
- 已暴露的 PAT 应立即撤销，重新生成

### 示例（可选）

```bash
# 宿主机创建凭据文件并限制权限
touch /Users/ktsama/docker/astrbot/data/.git-credentials
chmod 600 /Users/ktsama/docker/astrbot/data/.git-credentials

# 容器内配置凭据存储到挂载文件
git config --global credential.helper "store --file /AstrBot/data/.git-credentials"

# 远程地址保持干净（无 token）
git -C /AstrBot/data/skills/skill_akasha-kt remote set-url origin https://github.com/KTSAMA001/AgentSkill-Akasha-KT.git

# 第一次 push 时按提示输入用户名与 PAT，凭据会写入挂载文件
git -C /AstrBot/data/skills/skill_akasha-kt push origin main
```

### 相关知识

- Git credential helper（HTTPS 凭据存储机制）

---
```

---
